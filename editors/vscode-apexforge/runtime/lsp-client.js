/* AFP-P10-T4.11 dependency-free JSON-RPC/LSP process client hardening. */
'use strict';

const childProcess = require('child_process');

const JSONRPC_VERSION = '2.0';
const HEADER_DELIMITER = Buffer.from('\r\n\r\n', 'ascii');
const MAX_HEADER_BYTES = 64 * 1024;
const MAX_CONTENT_BYTES = 16 * 1024 * 1024;
const DEFAULT_REQUEST_TIMEOUT_MS = 10000;
const DEFAULT_STOP_TIMEOUT_MS = 3000;
const REQUEST_CANCELLED = -32800;
const CANCEL_REQUEST_METHOD = '$/cancelRequest';

function requireNonEmptyString(value, owner) {
    if (typeof value !== 'string' || value.length === 0) {
        throw new TypeError(`${owner} must be a non-empty string.`);
    }
    return value;
}

function encodeMessage(message) {
    if (message === null || typeof message !== 'object' || Array.isArray(message)) {
        throw new TypeError('LSP message must be an object.');
    }
    const body = Buffer.from(JSON.stringify(message), 'utf8');
    if (body.length > MAX_CONTENT_BYTES) {
        throw new RangeError(`LSP message exceeds ${MAX_CONTENT_BYTES} bytes.`);
    }
    const header = Buffer.from(`Content-Length: ${body.length}\r\n\r\n`, 'ascii');
    return Buffer.concat([header, body]);
}

class CancellationError extends Error {
    constructor(message = 'Language-server request was cancelled.') {
        super(message);
        this.name = 'CancellationError';
        this.code = REQUEST_CANCELLED;
    }
}

class LspMessageReader {
    constructor() {
        this.buffer = Buffer.alloc(0);
    }

    push(chunk) {
        if (!Buffer.isBuffer(chunk)) {
            chunk = Buffer.from(chunk);
        }
        this.buffer = this.buffer.length === 0 ? chunk : Buffer.concat([this.buffer, chunk]);
        const messages = [];
        while (this.buffer.length > 0) {
            const headerEnd = this.buffer.indexOf(HEADER_DELIMITER);
            if (headerEnd < 0) {
                if (this.buffer.length > MAX_HEADER_BYTES) {
                    throw new Error('LSP header exceeds the size limit.');
                }
                break;
            }
            if (headerEnd > MAX_HEADER_BYTES) {
                throw new Error('LSP header exceeds the size limit.');
            }
            const headerBytes = this.buffer.subarray(0, headerEnd);
            for (const byte of headerBytes) {
                if (byte > 0x7f) {
                    throw new Error('LSP headers must be ASCII.');
                }
            }
            const headers = new Map();
            for (const line of headerBytes.toString('ascii').split('\r\n')) {
                if (!line) {
                    continue;
                }
                const separator = line.indexOf(':');
                if (separator <= 0) {
                    throw new Error(`Malformed LSP header line: ${line}`);
                }
                const name = line.slice(0, separator).trim().toLowerCase();
                const value = line.slice(separator + 1).trim();
                if (!name || !value || headers.has(name)) {
                    throw new Error(`Malformed or duplicate LSP header: ${line}`);
                }
                headers.set(name, value);
            }
            const lengthText = headers.get('content-length');
            if (!lengthText || !/^\d+$/.test(lengthText)) {
                throw new Error('LSP message requires a decimal Content-Length header.');
            }
            const contentLength = Number.parseInt(lengthText, 10);
            if (!Number.isSafeInteger(contentLength) || contentLength > MAX_CONTENT_BYTES) {
                throw new Error('LSP Content-Length is outside the supported range.');
            }
            const bodyStart = headerEnd + HEADER_DELIMITER.length;
            const totalLength = bodyStart + contentLength;
            if (this.buffer.length < totalLength) {
                break;
            }
            const body = this.buffer.subarray(bodyStart, totalLength);
            this.buffer = this.buffer.subarray(totalLength);
            let value;
            try {
                value = JSON.parse(body.toString('utf8'));
            } catch (error) {
                throw new Error(`Invalid JSON-RPC payload: ${error.message}`);
            }
            if (value === null || typeof value !== 'object' || Array.isArray(value)) {
                throw new Error('JSON-RPC payload must be an object.');
            }
            messages.push(value);
        }
        return messages;
    }
}

class LspProcessClient {
    constructor(options) {
        if (options === null || typeof options !== 'object') {
            throw new TypeError('LspProcessClient options must be an object.');
        }
        this.command = requireNonEmptyString(options.command, 'command');
        this.args = Array.isArray(options.args) ? options.args.map((item) => String(item)) : [];
        this.cwd = options.cwd ? String(options.cwd) : undefined;
        this.env = options.env || process.env;
        this.requestTimeoutMs = Number.isInteger(options.requestTimeoutMs)
            ? options.requestTimeoutMs : DEFAULT_REQUEST_TIMEOUT_MS;
        this.stopTimeoutMs = Number.isInteger(options.stopTimeoutMs)
            ? options.stopTimeoutMs : DEFAULT_STOP_TIMEOUT_MS;
        this.onNotification = typeof options.onNotification === 'function'
            ? options.onNotification : () => {};
        this.onStderr = typeof options.onStderr === 'function' ? options.onStderr : () => {};
        this.onStateChange = typeof options.onStateChange === 'function'
            ? options.onStateChange : () => {};
        this.onLog = typeof options.onLog === 'function' ? options.onLog : () => {};
        this.onExit = typeof options.onExit === 'function' ? options.onExit : () => {};

        this.state = 'stopped';
        this.child = null;
        this.reader = new LspMessageReader();
        this.nextRequestId = 1;
        this.pending = new Map();
        this.closePromise = null;
        this._resolveClose = null;
        this.stopPromise = null;
        this.stopRequested = false;
        this.lastExitCode = null;
        this.lastExitSignal = null;
    }

    _setState(value) {
        if (this.state !== value) {
            this.state = value;
            this.onStateChange(value);
        }
    }

    _log(message) {
        this.onLog(String(message));
    }

    _cleanupPending(pending) {
        clearTimeout(pending.timer);
        if (pending.cancellationDisposable
                && typeof pending.cancellationDisposable.dispose === 'function') {
            try {
                pending.cancellationDisposable.dispose();
            } catch (error) {
                this._log(`Cancellation subscription disposal failed: ${error.message}`);
            }
        }
    }

    _rejectPending(error) {
        for (const pending of this.pending.values()) {
            this._cleanupPending(pending);
            pending.reject(error);
        }
        this.pending.clear();
    }

    _handleMessage(message) {
        if (message.jsonrpc !== JSONRPC_VERSION) {
            throw new Error('Received a message without jsonrpc="2.0".');
        }
        if (Object.prototype.hasOwnProperty.call(message, 'id')
                && !Object.prototype.hasOwnProperty.call(message, 'method')) {
            const pending = this.pending.get(message.id);
            if (!pending) {
                this._log(`Ignored response for unknown request id ${String(message.id)}.`);
                return;
            }
            this.pending.delete(message.id);
            this._cleanupPending(pending);
            if (Object.prototype.hasOwnProperty.call(message, 'error')) {
                const rpcError = message.error || {};
                const error = new Error(
                    `JSON-RPC ${String(rpcError.code)}: ${String(rpcError.message || 'Error')}`
                );
                error.code = rpcError.code;
                error.data = rpcError.data;
                pending.reject(error);
                return;
            }
            if (!Object.prototype.hasOwnProperty.call(message, 'result')) {
                pending.reject(new Error('JSON-RPC response omitted both result and error.'));
                return;
            }
            pending.resolve(message.result);
            return;
        }
        if (typeof message.method === 'string') {
            if (Object.prototype.hasOwnProperty.call(message, 'id')) {
                this._log(`Ignored unsupported server request ${message.method}.`);
                return;
            }
            try {
                this.onNotification(message.method, message.params);
            } catch (error) {
                this._log(`Notification handler failed: ${error.message}`);
            }
        }
    }

    _write(message) {
        if (!this.child || !this.child.stdin || this.child.stdin.destroyed) {
            throw new Error('Language-server stdin is not available.');
        }
        this.child.stdin.write(encodeMessage(message));
    }

    sendNotification(method, params) {
        requireNonEmptyString(method, 'method');
        const message = {jsonrpc: JSONRPC_VERSION, method};
        if (params !== undefined) {
            message.params = params;
        }
        this._write(message);
    }

    _cancelPending(id, method, reason) {
        const pending = this.pending.get(id);
        if (!pending) {
            return false;
        }
        this.pending.delete(id);
        this._cleanupPending(pending);
        try {
            this.sendNotification(CANCEL_REQUEST_METHOD, {id});
        } catch (error) {
            this._log(`Cancellation notification failed for ${method}: ${error.message}`);
        }
        pending.reject(reason instanceof Error ? reason : new CancellationError());
        return true;
    }

    sendRequest(method, params, timeoutOrToken, cancellationToken) {
        requireNonEmptyString(method, 'method');
        if (!this.child) {
            return Promise.reject(new Error('Language-server process is not running.'));
        }
        let selectedTimeout = this.requestTimeoutMs;
        let token = cancellationToken;
        if (Number.isInteger(timeoutOrToken)) {
            selectedTimeout = timeoutOrToken;
        } else if (timeoutOrToken && typeof timeoutOrToken === 'object') {
            token = timeoutOrToken;
        }
        if (token && token.isCancellationRequested === true) {
            return Promise.reject(new CancellationError(`Language-server request cancelled: ${method}`));
        }

        const id = this.nextRequestId++;
        const message = {jsonrpc: JSONRPC_VERSION, id, method};
        if (params !== undefined) {
            message.params = params;
        }

        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this._cancelPending(
                    id,
                    method,
                    new Error(`Language-server request timed out: ${method}`)
                );
            }, selectedTimeout);
            if (typeof timer.unref === 'function') {
                timer.unref();
            }
            const pending = {
                resolve,
                reject,
                timer,
                method,
                cancellationDisposable: null,
            };
            this.pending.set(id, pending);
            if (token && typeof token.onCancellationRequested === 'function') {
                pending.cancellationDisposable = token.onCancellationRequested(() => {
                    this._cancelPending(
                        id,
                        method,
                        new CancellationError(`Language-server request cancelled: ${method}`)
                    );
                });
                if (token.isCancellationRequested === true) {
                    this._cancelPending(
                        id,
                        method,
                        new CancellationError(`Language-server request cancelled: ${method}`)
                    );
                    return;
                }
            }
            try {
                this._write(message);
            } catch (error) {
                this.pending.delete(id);
                this._cleanupPending(pending);
                reject(error);
            }
        });
    }

    async start(initializeParams) {
        if (this.state !== 'stopped') {
            throw new Error(`Cannot start language server from state ${this.state}.`);
        }
        this.reader = new LspMessageReader();
        this.lastExitCode = null;
        this.lastExitSignal = null;
        this.stopRequested = false;
        this._setState('starting');
        this.closePromise = new Promise((resolve) => {
            this._resolveClose = resolve;
        });
        const child = childProcess.spawn(this.command, this.args, {
            cwd: this.cwd,
            env: this.env,
            stdio: ['pipe', 'pipe', 'pipe'],
            windowsHide: true,
        });
        this.child = child;
        child.stdout.on('data', (chunk) => {
            try {
                for (const message of this.reader.push(chunk)) {
                    this._handleMessage(message);
                }
            } catch (error) {
                this._log(`Language-server protocol failure: ${error.message}`);
                this._rejectPending(error);
                child.kill();
            }
        });
        child.stderr.on('data', (chunk) => this.onStderr(chunk.toString('utf8')));
        child.on('error', (error) => {
            this._log(`Language-server process error: ${error.message}`);
            this._rejectPending(error);
            this._setState('failed');
            if (this._resolveClose) {
                this._resolveClose({code: null, signal: null, error});
                this._resolveClose = null;
            }
        });
        child.on('close', (code, signal) => {
            const expected = this.stopRequested || this.state === 'stopping';
            this.lastExitCode = code;
            this.lastExitSignal = signal;
            if (this.child === child) {
                this.child = null;
            }
            this._rejectPending(
                new Error(`Language-server process exited (code=${String(code)}, signal=${String(signal)}).`)
            );
            this._setState('stopped');
            if (this._resolveClose) {
                this._resolveClose({code, signal, expected});
                this._resolveClose = null;
            }
            try {
                this.onExit({code, signal, expected});
            } catch (error) {
                this._log(`Exit handler failed: ${error.message}`);
            }
        });

        try {
            const result = await this.sendRequest('initialize', initializeParams);
            this.sendNotification('initialized', {});
            this._setState('running');
            return result;
        } catch (error) {
            this._setState('failed');
            if (this.child) {
                this.child.kill();
            }
            throw error;
        }
    }

    async stop() {
        if (this.stopPromise) {
            return this.stopPromise;
        }
        this.stopPromise = this._stopCore();
        try {
            await this.stopPromise;
        } finally {
            this.stopPromise = null;
        }
    }

    async _stopCore() {
        const child = this.child;
        this.stopRequested = true;
        if (!child) {
            this._setState('stopped');
            return;
        }
        this._setState('stopping');
        try {
            await this.sendRequest('shutdown', undefined, this.stopTimeoutMs);
        } catch (error) {
            this._log(`Language-server shutdown request failed: ${error.message}`);
        }
        if (this.child) {
            try {
                this.sendNotification('exit');
            } catch (error) {
                this._log(`Language-server exit notification failed: ${error.message}`);
            }
        }
        const closePromise = this.closePromise || Promise.resolve();
        let timedOut = false;
        await Promise.race([
            closePromise,
            new Promise((resolve) => {
                const timer = setTimeout(() => {
                    timedOut = true;
                    resolve();
                }, this.stopTimeoutMs);
                if (typeof timer.unref === 'function') {
                    timer.unref();
                }
            }),
        ]);
        if (timedOut && this.child) {
            this._log('Language-server process did not stop in time; terminating it.');
            this.child.kill();
            await closePromise;
        }
    }
}

module.exports = {
    CANCEL_REQUEST_METHOD,
    CancellationError,
    DEFAULT_REQUEST_TIMEOUT_MS,
    DEFAULT_STOP_TIMEOUT_MS,
    JSONRPC_VERSION,
    LspMessageReader,
    LspProcessClient,
    MAX_CONTENT_BYTES,
    REQUEST_CANCELLED,
    encodeMessage,
};
