/* AFP-P10-T4.3 ApexForge VS Code language-server activation. */
'use strict';

const fs = require('fs');
const path = require('path');
const vscode = require('vscode');
const { LspProcessClient } = require('./runtime/lsp-client');

const LANGUAGE_ID = 'apexforge';
const OUTPUT_CHANNEL_NAME = 'ApexForge Language Server';
const DIAGNOSTIC_COLLECTION_NAME = 'apexforge';
const CONFIGURATION_SECTION = 'apexforge.languageServer';
const DEFAULT_SERVER_PATH = 'apexforge/apexforge_lsp.py';
const CLIENT_NAME = 'ApexForge VS Code';
const CLIENT_VERSION = '10-T4.3';

let activeRuntime = null;

function folderKey(folder) {
    return folder.uri.toString();
}

function sameFolder(left, right) {
    return Boolean(left && right && folderKey(left) === folderKey(right));
}

function defaultPythonCommand() {
    return process.platform === 'win32' ? 'py' : 'python3';
}

function selectPythonCommand(folder) {
    const configuration = vscode.workspace.getConfiguration(
        CONFIGURATION_SECTION,
        folder.uri
    );
    const configured = configuration.get('pythonCommand', '');
    if (typeof configured === 'string' && configured.trim()) {
        return configured.trim();
    }
    return defaultPythonCommand();
}

function resolveServerPath(folder) {
    const configuration = vscode.workspace.getConfiguration(
        CONFIGURATION_SECTION,
        folder.uri
    );
    const configured = configuration.get('serverPath', DEFAULT_SERVER_PATH);
    const value = typeof configured === 'string' && configured.trim()
        ? configured.trim()
        : DEFAULT_SERVER_PATH;
    return path.isAbsolute(value)
        ? path.normalize(value)
        : path.join(folder.uri.fsPath, value);
}

function traceEnabled(folder) {
    return vscode.workspace
        .getConfiguration(CONFIGURATION_SECTION, folder.uri)
        .get('trace', false) === true;
}

function documentBelongsToFolder(document, folder) {
    if (!document || document.languageId !== LANGUAGE_ID) {
        return false;
    }
    const documentFolder = vscode.workspace.getWorkspaceFolder(document.uri);
    return sameFolder(documentFolder, folder);
}

function lspRange(rawRange) {
    const value = rawRange || {};
    const rawStart = value.start || {};
    const rawEnd = value.end || rawStart;
    const start = new vscode.Position(
        Number.isInteger(rawStart.line) ? rawStart.line : 0,
        Number.isInteger(rawStart.character) ? rawStart.character : 0
    );
    const end = new vscode.Position(
        Number.isInteger(rawEnd.line) ? rawEnd.line : start.line,
        Number.isInteger(rawEnd.character) ? rawEnd.character : start.character
    );
    return new vscode.Range(start, end);
}

function diagnosticSeverity(value) {
    switch (value) {
        case 2:
            return vscode.DiagnosticSeverity.Warning;
        case 3:
            return vscode.DiagnosticSeverity.Information;
        case 4:
            return vscode.DiagnosticSeverity.Hint;
        case 1:
        default:
            return vscode.DiagnosticSeverity.Error;
    }
}

function convertDiagnostic(raw) {
    const diagnostic = new vscode.Diagnostic(
        lspRange(raw.range),
        typeof raw.message === 'string' ? raw.message : 'ApexForge diagnostic',
        diagnosticSeverity(raw.severity)
    );
    if (typeof raw.code === 'string' || Number.isInteger(raw.code)) {
        diagnostic.code = raw.code;
    }
    diagnostic.source = typeof raw.source === 'string'
        ? raw.source
        : DIAGNOSTIC_COLLECTION_NAME;

    if (Array.isArray(raw.relatedInformation)) {
        diagnostic.relatedInformation = raw.relatedInformation
            .filter((item) => (
                item
                && item.location
                && typeof item.location.uri === 'string'
                && typeof item.message === 'string'
            ))
            .map((item) => new vscode.DiagnosticRelatedInformation(
                new vscode.Location(
                    vscode.Uri.parse(item.location.uri),
                    lspRange(item.location.range)
                ),
                item.message
            ));
    }

    return diagnostic;
}

class WorkspaceLanguageServer {
    constructor(folder, shared) {
        this.folder = folder;
        this.output = shared.output;
        this.diagnostics = shared.diagnostics;
        this.client = null;
        this.startPromise = null;
        this.openVersions = new Map();
        this.disposed = false;
    }

    log(message) {
        this.output.appendLine(`[${this.folder.name}] ${String(message)}`);
    }

    trace(message) {
        if (traceEnabled(this.folder)) {
            this.log(message);
        }
    }

    async start() {
        if (this.disposed) {
            return;
        }
        if (this.client && this.client.state === 'running') {
            return;
        }
        if (this.startPromise) {
            return this.startPromise;
        }

        this.startPromise = this._startCore();
        try {
            await this.startPromise;
        } finally {
            this.startPromise = null;
        }
    }

    async _startCore() {
        if (this.folder.uri.scheme !== 'file') {
            this.log('Skipped: language-server activation requires a file-system workspace.');
            return;
        }

        const serverPath = resolveServerPath(this.folder);
        if (!fs.existsSync(serverPath)) {
            this.log(`Skipped: server entry point was not found at ${serverPath}.`);
            return;
        }

        const command = selectPythonCommand(this.folder);
        this.log(`Starting ${command} "${serverPath}" --stdio`);

        const client = new LspProcessClient({
            command,
            args: [serverPath, '--stdio'],
            cwd: this.folder.uri.fsPath,
            onNotification: (method, params) => this.handleNotification(method, params),
            onStderr: (text) => {
                for (const line of String(text).split(/\r?\n/)) {
                    if (line) {
                        this.log(`stderr: ${line}`);
                    }
                }
            },
            onStateChange: (state) => this.trace(`State: ${state}`),
            onLog: (message) => this.log(message),
        });
        this.client = client;

        try {
            const initializeResult = await client.start({
                processId: process.pid,
                clientInfo: {
                    name: CLIENT_NAME,
                    version: CLIENT_VERSION,
                },
                rootUri: this.folder.uri.toString(),
                workspaceFolders: [
                    {
                        uri: this.folder.uri.toString(),
                        name: this.folder.name,
                    },
                ],
                capabilities: {
                    textDocument: {
                        publishDiagnostics: {
                            relatedInformation: true,
                            versionSupport: true,
                        },
                    },
                },
            });

            const serverInfo = initializeResult && initializeResult.serverInfo;
            const serverLabel = serverInfo && serverInfo.name
                ? `${serverInfo.name}@${serverInfo.version || 'unknown'}`
                : 'ApexForge language server';
            this.log(`Started ${serverLabel}.`);

            for (const document of vscode.workspace.textDocuments) {
                if (documentBelongsToFolder(document, this.folder)) {
                    this.didOpen(document);
                }
            }
        } catch (error) {
            this.log(`Start failed: ${error.message}`);
            if (this.client === client) {
                this.client = null;
            }
            try {
                await client.stop();
            } catch (stopError) {
                this.log(`Cleanup failed: ${stopError.message}`);
            }
            vscode.window.showErrorMessage(
                `ApexForge language server failed for ${this.folder.name}. `
                + `See "${OUTPUT_CHANNEL_NAME}" for details.`
            );
        }
    }

    handleNotification(method, params) {
        if (method !== 'textDocument/publishDiagnostics') {
            this.trace(`Notification: ${method}`);
            return;
        }
        if (!params || typeof params.uri !== 'string') {
            this.log('Ignored malformed publishDiagnostics notification.');
            return;
        }

        const uri = vscode.Uri.parse(params.uri);
        const openDocument = vscode.workspace.textDocuments.find(
            (document) => document.uri.toString() === params.uri
        );
        if (
            openDocument
            && Number.isInteger(params.version)
            && params.version < openDocument.version
        ) {
            this.trace(
                `Ignored stale diagnostics for ${params.uri} `
                + `(server=${params.version}, editor=${openDocument.version}).`
            );
            return;
        }

        const values = Array.isArray(params.diagnostics)
            ? params.diagnostics.map(convertDiagnostic)
            : [];
        this.diagnostics.set(uri, values);
        this.trace(`Published ${values.length} diagnostic(s) for ${params.uri}.`);
    }

    didOpen(document) {
        const client = this.client;
        if (!client || client.state !== 'running') {
            return;
        }

        const uri = document.uri.toString();
        const previous = this.openVersions.get(uri);
        if (previous !== undefined) {
            if (previous !== document.version) {
                this.didChange(document);
            }
            return;
        }

        client.sendNotification('textDocument/didOpen', {
            textDocument: {
                uri,
                languageId: LANGUAGE_ID,
                version: document.version,
                text: document.getText(),
            },
        });
        this.openVersions.set(uri, document.version);
        this.trace(`didOpen ${uri}@${document.version}`);
    }

    didChange(document) {
        const client = this.client;
        if (!client || client.state !== 'running') {
            return;
        }

        const uri = document.uri.toString();
        if (!this.openVersions.has(uri)) {
            this.didOpen(document);
            return;
        }

        const previous = this.openVersions.get(uri);
        if (Number.isInteger(previous) && document.version <= previous) {
            return;
        }

        client.sendNotification('textDocument/didChange', {
            textDocument: {
                uri,
                version: document.version,
            },
            contentChanges: [
                {
                    text: document.getText(),
                },
            ],
        });
        this.openVersions.set(uri, document.version);
        this.trace(`didChange ${uri}@${document.version}`);
    }

    didClose(document) {
        const uri = document.uri.toString();
        const client = this.client;
        if (client && client.state === 'running' && this.openVersions.has(uri)) {
            client.sendNotification('textDocument/didClose', {
                textDocument: {
                    uri,
                },
            });
            this.trace(`didClose ${uri}`);
        }
        this.openVersions.delete(uri);
        this.diagnostics.delete(document.uri);
    }

    async restart() {
        this.log('Restart requested.');
        await this.stop();
        this.disposed = false;
        await this.start();
    }

    async stop() {
        const client = this.client;
        this.client = null;
        for (const uri of this.openVersions.keys()) {
            this.diagnostics.delete(vscode.Uri.parse(uri));
        }
        this.openVersions.clear();

        if (!client) {
            return;
        }

        try {
            await client.stop();
            this.log('Stopped.');
        } catch (error) {
            this.log(`Stop failed: ${error.message}`);
        }
    }

    async dispose() {
        this.disposed = true;
        await this.stop();
    }
}

class ApexForgeExtensionRuntime {
    constructor(context) {
        this.context = context;
        this.output = vscode.window.createOutputChannel(OUTPUT_CHANNEL_NAME);
        this.diagnostics = vscode.languages.createDiagnosticCollection(
            DIAGNOSTIC_COLLECTION_NAME
        );
        this.controllers = new Map();
        this.disposables = [];
    }

    controllerForFolder(folder) {
        return folder ? this.controllers.get(folderKey(folder)) : undefined;
    }

    async addFolder(folder) {
        if (!folder) {
            return undefined;
        }
        const key = folderKey(folder);
        if (this.controllers.has(key)) {
            const existing = this.controllers.get(key);
            await existing.start();
            return existing;
        }

        const controller = new WorkspaceLanguageServer(folder, {
            output: this.output,
            diagnostics: this.diagnostics,
        });
        this.controllers.set(key, controller);
        await controller.start();
        return controller;
    }

    async removeFolder(folder) {
        const key = folderKey(folder);
        const controller = this.controllers.get(key);
        if (!controller) {
            return;
        }
        this.controllers.delete(key);
        await controller.dispose();
    }

    controllerForDocument(document) {
        if (!document || document.languageId !== LANGUAGE_ID) {
            return undefined;
        }
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        return this.controllerForFolder(folder);
    }

    async activate() {
        this.output.appendLine('AFP-P10-T4.3 extension activation started.');

        const folders = vscode.workspace.workspaceFolders || [];
        for (const folder of folders) {
            await this.addFolder(folder);
        }

        this.disposables.push(
            vscode.workspace.onDidChangeWorkspaceFolders(async (event) => {
                for (const folder of event.removed) {
                    await this.removeFolder(folder);
                }
                for (const folder of event.added) {
                    await this.addFolder(folder);
                }
            }),
            vscode.workspace.onDidOpenTextDocument(async (document) => {
                if (document.languageId !== LANGUAGE_ID) {
                    return;
                }
                const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                const controller = await this.addFolder(folder);
                if (controller) {
                    controller.didOpen(document);
                }
            }),
            vscode.workspace.onDidChangeTextDocument((event) => {
                const controller = this.controllerForDocument(event.document);
                if (controller) {
                    controller.didChange(event.document);
                }
            }),
            vscode.workspace.onDidCloseTextDocument((document) => {
                const controller = this.controllerForDocument(document);
                if (controller) {
                    controller.didClose(document);
                } else {
                    this.diagnostics.delete(document.uri);
                }
            }),
            vscode.workspace.onDidChangeConfiguration(async (event) => {
                const affected = [...this.controllers.values()].filter(
                    (controller) => event.affectsConfiguration(
                        CONFIGURATION_SECTION,
                        controller.folder.uri
                    )
                );
                for (const controller of affected) {
                    await controller.restart();
                }
            }),
            vscode.commands.registerCommand(
                'apexforge.showLanguageServerOutput',
                () => this.output.show(true)
            ),
            vscode.commands.registerCommand(
                'apexforge.restartLanguageServer',
                async () => {
                    for (const controller of this.controllers.values()) {
                        await controller.restart();
                    }
                }
            )
        );

        this.context.subscriptions.push(
            this.output,
            this.diagnostics,
            ...this.disposables
        );

        this.output.appendLine('AFP-P10-T4.3 extension activation completed.');
    }

    async dispose() {
        const controllers = [...this.controllers.values()];
        this.controllers.clear();
        await Promise.allSettled(
            controllers.map((controller) => controller.dispose())
        );
        this.diagnostics.clear();
    }
}

async function activate(context) {
    const runtime = new ApexForgeExtensionRuntime(context);
    activeRuntime = runtime;
    await runtime.activate();
}

async function deactivate() {
    const runtime = activeRuntime;
    activeRuntime = null;
    if (runtime) {
        await runtime.dispose();
    }
}

exports.activate = activate;
exports.deactivate = deactivate;
