/* AFP-P10-T4.11 ApexForge VS Code integration hardening. */
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
const CLIENT_VERSION = '10-T4.11';

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

const LSP_SYMBOL_KIND_TO_VSCODE = [
    undefined,
    vscode.SymbolKind.File,
    vscode.SymbolKind.Module,
    vscode.SymbolKind.Namespace,
    vscode.SymbolKind.Package,
    vscode.SymbolKind.Class,
    vscode.SymbolKind.Method,
    vscode.SymbolKind.Property,
    vscode.SymbolKind.Field,
    vscode.SymbolKind.Constructor,
    vscode.SymbolKind.Enum,
    vscode.SymbolKind.Interface,
    vscode.SymbolKind.Function,
    vscode.SymbolKind.Variable,
    vscode.SymbolKind.Constant,
    vscode.SymbolKind.String,
    vscode.SymbolKind.Number,
    vscode.SymbolKind.Boolean,
    vscode.SymbolKind.Array,
    vscode.SymbolKind.Object,
    vscode.SymbolKind.Key,
    vscode.SymbolKind.Null,
    vscode.SymbolKind.EnumMember,
    vscode.SymbolKind.Struct,
    vscode.SymbolKind.Event,
    vscode.SymbolKind.Operator,
    vscode.SymbolKind.TypeParameter,
];

function convertDocumentSymbol(raw) {
    if (!raw || typeof raw.name !== 'string') {
        return undefined;
    }
    const range = lspRange(raw.range);
    const selectionRange = lspRange(raw.selectionRange || raw.range);
    const kind = LSP_SYMBOL_KIND_TO_VSCODE[raw.kind]
        ?? vscode.SymbolKind.Object;
    const symbol = new vscode.DocumentSymbol(
        raw.name,
        typeof raw.detail === 'string' ? raw.detail : '',
        kind,
        range,
        selectionRange
    );
    if (Array.isArray(raw.children)) {
        symbol.children = raw.children
            .map(convertDocumentSymbol)
            .filter((item) => item !== undefined);
    }
    return symbol;
}

function convertDefinition(raw) {
    const values = Array.isArray(raw) ? raw : (raw ? [raw] : []);
    const locations = values
        .filter((item) => (
            item
            && typeof item.uri === 'string'
            && item.range
        ))
        .map((item) => new vscode.Location(
            vscode.Uri.parse(item.uri),
            lspRange(item.range)
        ));
    if (locations.length === 0) {
        return undefined;
    }
    return locations.length === 1 ? locations[0] : locations;
}

function convertReferences(raw) {
    if (!Array.isArray(raw)) {
        return [];
    }
    return raw
        .filter((item) => (
            item
            && typeof item.uri === 'string'
            && item.range
        ))
        .map((item) => new vscode.Location(
            vscode.Uri.parse(item.uri),
            lspRange(item.range)
        ));
}

function convertWorkspaceSymbol(raw) {
    if (
        !raw
        || typeof raw.name !== 'string'
        || !raw.name
        || !raw.location
        || typeof raw.location.uri !== 'string'
        || !raw.location.range
    ) {
        return undefined;
    }
    const kind = LSP_SYMBOL_KIND_TO_VSCODE[raw.kind]
        ?? vscode.SymbolKind.Object;
    return new vscode.SymbolInformation(
        raw.name,
        kind,
        typeof raw.containerName === 'string' ? raw.containerName : '',
        new vscode.Location(
            vscode.Uri.parse(raw.location.uri),
            lspRange(raw.location.range)
        )
    );
}

function convertTextEdits(raw) {
    if (!Array.isArray(raw)) {
        return [];
    }
    return raw
        .filter((item) => item && item.range && typeof item.newText === 'string')
        .map((item) => new vscode.TextEdit(lspRange(item.range), item.newText));
}

function convertPrepareRename(raw) {
    if (!raw || !raw.range) {
        return undefined;
    }
    const range = lspRange(raw.range);
    if (typeof raw.placeholder === 'string' && raw.placeholder) {
        return {range, placeholder: raw.placeholder};
    }
    return range;
}

function convertWorkspaceEdit(raw) {
    if (!raw || typeof raw !== 'object' || !raw.changes) {
        return undefined;
    }
    const edit = new vscode.WorkspaceEdit();
    for (const [uriText, rawEdits] of Object.entries(raw.changes)) {
        if (!Array.isArray(rawEdits)) {
            continue;
        }
        const uri = vscode.Uri.parse(uriText);
        for (const rawEdit of rawEdits) {
            if (
                rawEdit
                && rawEdit.range
                && typeof rawEdit.newText === 'string'
            ) {
                edit.replace(uri, lspRange(rawEdit.range), rawEdit.newText);
            }
        }
    }
    return edit;
}

function convertHover(raw) {
    if (!raw || !raw.contents) {
        return undefined;
    }

    const contents = raw.contents;
    let rendered;
    if (
        contents
        && typeof contents === 'object'
        && contents.kind === 'markdown'
        && typeof contents.value === 'string'
    ) {
        rendered = new vscode.MarkdownString(contents.value);
        rendered.isTrusted = false;
        rendered.supportHtml = false;
    } else if (
        contents
        && typeof contents === 'object'
        && typeof contents.value === 'string'
    ) {
        rendered = contents.value;
    } else if (typeof contents === 'string') {
        rendered = contents;
    } else {
        return undefined;
    }

    const range = raw.range ? lspRange(raw.range) : undefined;
    return new vscode.Hover(rendered, range);
}

const LSP_COMPLETION_KIND_TO_VSCODE = [
    undefined,
    vscode.CompletionItemKind.Text,
    vscode.CompletionItemKind.Method,
    vscode.CompletionItemKind.Function,
    vscode.CompletionItemKind.Constructor,
    vscode.CompletionItemKind.Field,
    vscode.CompletionItemKind.Variable,
    vscode.CompletionItemKind.Class,
    vscode.CompletionItemKind.Interface,
    vscode.CompletionItemKind.Module,
    vscode.CompletionItemKind.Property,
    vscode.CompletionItemKind.Unit,
    vscode.CompletionItemKind.Value,
    vscode.CompletionItemKind.Enum,
    vscode.CompletionItemKind.Keyword,
    vscode.CompletionItemKind.Snippet,
    vscode.CompletionItemKind.Color,
    vscode.CompletionItemKind.File,
    vscode.CompletionItemKind.Reference,
    vscode.CompletionItemKind.Folder,
    vscode.CompletionItemKind.EnumMember,
    vscode.CompletionItemKind.Constant,
    vscode.CompletionItemKind.Struct,
    vscode.CompletionItemKind.Event,
    vscode.CompletionItemKind.Operator,
    vscode.CompletionItemKind.TypeParameter,
];

function convertCompletionDocumentation(raw) {
    if (typeof raw === 'string') {
        return raw;
    }
    if (
        raw
        && typeof raw === 'object'
        && raw.kind === 'markdown'
        && typeof raw.value === 'string'
    ) {
        const value = new vscode.MarkdownString(raw.value);
        value.isTrusted = false;
        value.supportHtml = false;
        return value;
    }
    if (raw && typeof raw === 'object' && typeof raw.value === 'string') {
        return raw.value;
    }
    return undefined;
}

function convertCompletionItem(raw) {
    if (!raw || typeof raw.label !== 'string' || !raw.label) {
        return undefined;
    }
    const kind = LSP_COMPLETION_KIND_TO_VSCODE[raw.kind]
        ?? vscode.CompletionItemKind.Text;
    const item = new vscode.CompletionItem(raw.label, kind);
    if (typeof raw.detail === 'string') {
        item.detail = raw.detail;
    }
    item.documentation = convertCompletionDocumentation(raw.documentation);
    if (typeof raw.sortText === 'string') {
        item.sortText = raw.sortText;
    }
    if (typeof raw.filterText === 'string') {
        item.filterText = raw.filterText;
    }
    if (raw.preselect === true) {
        item.preselect = true;
    }

    if (
        raw.textEdit
        && typeof raw.textEdit === 'object'
        && typeof raw.textEdit.newText === 'string'
        && raw.textEdit.range
    ) {
        item.insertText = raw.textEdit.newText;
        item.range = lspRange(raw.textEdit.range);
    } else if (typeof raw.insertText === 'string') {
        item.insertText = raw.insertText;
    }
    return item;
}

class WorkspaceLanguageServer {
    constructor(folder, shared) {
        this.folder = folder;
        this.output = shared.output;
        this.diagnostics = shared.diagnostics;
        this.client = null;
        this.startPromise = null;
        this.restartPromise = null;
        this.generation = 0;
        this.unexpectedExitCount = 0;
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
        const generation = this.generation;
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
            onStateChange: (state) => this.handleStateChange(client, state),
            onExit: (details) => this.handleClientExit(client, details),
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
                        documentSymbol: {
                            hierarchicalDocumentSymbolSupport: true,
                            symbolKind: {
                                valueSet: Array.from({length: 26}, (_, index) => index + 1),
                            },
                        },
                        hover: {
                            contentFormat: ['markdown', 'plaintext'],
                        },
                        completion: {
                            completionItem: {
                                documentationFormat: ['markdown', 'plaintext'],
                                snippetSupport: false,
                            },
                        },
                        definition: {
                            linkSupport: false,
                        },
                        references: {},
                        rename: {
                            prepareSupport: true,
                        },
                        formatting: {
                            dynamicRegistration: false,
                        },
                    },
                    workspace: {
                        symbol: {
                            dynamicRegistration: false,
                            symbolKind: {
                                valueSet: Array.from({length: 26}, (_, index) => index + 1),
                            },
                        },
                    },
                },
            });

            if (this.disposed || generation !== this.generation || this.client !== client) {
                this.log('Discarded stale language-server startup.');
                await client.stop();
                return;
            }

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

    handleStateChange(client, state) {
        this.trace(`State: ${state}`);
        if (this.client !== client) {
            return;
        }
        if (state === 'failed') {
            this.log('Language-server client entered the failed state.');
        }
    }

    handleClientExit(client, details) {
        if (this.client !== client) {
            return;
        }
        const expected = Boolean(details && details.expected);
        if (!expected && !this.disposed) {
            this.unexpectedExitCount += 1;
            this.log(
                `Language server exited unexpectedly `
                + `(code=${String(details && details.code)}, `
                + `signal=${String(details && details.signal)}).`
            );
        }
        this.client = null;
        for (const uri of this.openVersions.keys()) {
            this.diagnostics.delete(vscode.Uri.parse(uri));
        }
        this.openVersions.clear();
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

    async documentSymbols(document, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return [];
        }
        if (token && token.isCancellationRequested) {
            return [];
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/documentSymbol',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return [];
            }
            return Array.isArray(result)
                ? result.map(convertDocumentSymbol).filter((item) => item !== undefined)
                : [];
        } catch (error) {
            this.log(`Document symbols failed: ${error.message}`);
            return [];
        }
    }

    async hover(document, position, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return undefined;
        }
        if (token && token.isCancellationRequested) {
            return undefined;
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/hover',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                    position: {
                        line: position.line,
                        character: position.character,
                    },
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return undefined;
            }
            return convertHover(result);
        } catch (error) {
            this.log(`Hover failed: ${error.message}`);
            return undefined;
        }
    }

    async definitions(document, position, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return undefined;
        }
        if (token && token.isCancellationRequested) {
            return undefined;
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/definition',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                    position: {
                        line: position.line,
                        character: position.character,
                    },
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return undefined;
            }
            return convertDefinition(result);
        } catch (error) {
            this.log(`Definition failed: ${error.message}`);
            return undefined;
        }
    }

    async references(document, position, context, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return [];
        }
        if (token && token.isCancellationRequested) {
            return [];
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/references',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                    position: {
                        line: position.line,
                        character: position.character,
                    },
                    context: {
                        includeDeclaration: context.includeDeclaration === true,
                    },
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return [];
            }
            return convertReferences(result);
        } catch (error) {
            this.log(`References failed: ${error.message}`);
            return [];
        }
    }

    async prepareRename(document, position, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return undefined;
        }
        if (token && token.isCancellationRequested) {
            return undefined;
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/prepareRename',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                    position: {
                        line: position.line,
                        character: position.character,
                    },
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return undefined;
            }
            return convertPrepareRename(result);
        } catch (error) {
            this.log(`Prepare rename failed: ${error.message}`);
            return undefined;
        }
    }

    async rename(document, position, newName, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return undefined;
        }
        if (token && token.isCancellationRequested) {
            return undefined;
        }

        this.didOpen(document);
        try {
            const result = await client.sendRequest(
                'textDocument/rename',
                {
                    textDocument: {
                        uri: document.uri.toString(),
                    },
                    position: {
                        line: position.line,
                        character: position.character,
                    },
                    newName,
                },
                token
            );
            if (token && token.isCancellationRequested) {
                return undefined;
            }
            return convertWorkspaceEdit(result);
        } catch (error) {
            this.log(`Rename failed: ${error.message}`);
            throw error;
        }
    }

    async completions(document, position, token, context) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return [];
        }
        if (token && token.isCancellationRequested) {
            return [];
        }

        this.didOpen(document);
        try {
            const params = {
                textDocument: {
                    uri: document.uri.toString(),
                },
                position: {
                    line: position.line,
                    character: position.character,
                },
            };
            if (context) {
                params.context = {
                    triggerKind: context.triggerKind,
                    triggerCharacter: context.triggerCharacter,
                };
            }
            const result = await client.sendRequest(
                'textDocument/completion',
                params,
                token
            );
            if (token && token.isCancellationRequested) {
                return [];
            }
            const rawItems = Array.isArray(result)
                ? result
                : (result && Array.isArray(result.items) ? result.items : []);
            return rawItems
                .map(convertCompletionItem)
                .filter((item) => item !== undefined);
        } catch (error) {
            this.log(`Completion failed: ${error.message}`);
            return [];
        }
    }

    async formatDocument(document, options, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return [];
        }
        if (token && token.isCancellationRequested) {
            return [];
        }
        this.didOpen(document);
        try {
            const result = await client.sendRequest('textDocument/formatting', {
                textDocument: {uri: document.uri.toString()},
                options: {
                    tabSize: Number.isInteger(options && options.tabSize) ? options.tabSize : 4,
                    insertSpaces: !options || options.insertSpaces !== false,
                },
            }, token);
            if (token && token.isCancellationRequested) {
                return [];
            }
            return convertTextEdits(result);
        } catch (error) {
            this.log(`Formatting failed: ${error.message}`);
            return [];
        }
    }

    async workspaceSymbols(query, token) {
        await this.start();
        const client = this.client;
        if (!client || client.state !== 'running') {
            return [];
        }
        if (token && token.isCancellationRequested) {
            return [];
        }

        try {
            const result = await client.sendRequest(
                'workspace/symbol',
                {query: typeof query === 'string' ? query : ''},
                token
            );
            if (token && token.isCancellationRequested) {
                return [];
            }
            return Array.isArray(result)
                ? result.map(convertWorkspaceSymbol).filter((item) => item !== undefined)
                : [];
        } catch (error) {
            this.log(`Workspace symbols failed: ${error.message}`);
            return [];
        }
    }

    async restart() {
        if (this.restartPromise) {
            return this.restartPromise;
        }
        this.restartPromise = (async () => {
            this.log('Restart requested.');
            await this.stop();
            if (!this.disposed) {
                await this.start();
            }
        })();
        try {
            await this.restartPromise;
        } finally {
            this.restartPromise = null;
        }
    }

    async stop() {
        this.generation += 1;
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
        this.output.appendLine('AFP-P10-T4.11 extension activation started.');

        const folders = vscode.workspace.workspaceFolders || [];
        await Promise.allSettled(folders.map((folder) => this.addFolder(folder)));

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
                await Promise.allSettled(
                    affected.map((controller) => controller.restart())
                );
            }),
            vscode.languages.registerDocumentSymbolProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideDocumentSymbols: async (document, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.documentSymbols(document, token)
                            : [];
                    },
                },
                {label: 'ApexForge'}
            ),
            vscode.languages.registerHoverProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideHover: async (document, position, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.hover(document, position, token)
                            : undefined;
                    },
                }
            ),
            vscode.languages.registerDefinitionProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideDefinition: async (document, position, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.definitions(document, position, token)
                            : undefined;
                    },
                }
            ),
            vscode.languages.registerReferenceProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideReferences: async (document, position, context, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.references(document, position, context, token)
                            : [];
                    },
                }
            ),
            vscode.languages.registerRenameProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    prepareRename: async (document, position, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.prepareRename(document, position, token)
                            : undefined;
                    },
                    provideRenameEdits: async (document, position, newName, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.rename(document, position, newName, token)
                            : undefined;
                    },
                }
            ),
            vscode.languages.registerDocumentFormattingEditProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideDocumentFormattingEdits: async (document, options, token) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller ? controller.formatDocument(document, options, token) : [];
                    },
                }
            ),
            vscode.languages.registerWorkspaceSymbolProvider(
                {
                    provideWorkspaceSymbols: async (query, token) => {
                        const controllers = [...this.controllers.values()].sort(
                            (left, right) => folderKey(left.folder).localeCompare(folderKey(right.folder))
                        );
                        const groups = await Promise.all(
                            controllers.map((controller) => controller.workspaceSymbols(query, token))
                        );
                        return groups.flat();
                    },
                }
            ),
            vscode.languages.registerCompletionItemProvider(
                {language: LANGUAGE_ID, scheme: 'file'},
                {
                    provideCompletionItems: async (document, position, token, context) => {
                        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
                        const controller = await this.addFolder(folder);
                        return controller
                            ? controller.completions(document, position, token, context)
                            : [];
                    },
                },
                '@',
                ':'
            ),
            vscode.commands.registerCommand(
                'apexforge.showLanguageServerOutput',
                () => this.output.show(true)
            ),
            vscode.commands.registerCommand(
                'apexforge.restartLanguageServer',
                async () => {
                    await Promise.allSettled(
                        [...this.controllers.values()].map(
                            (controller) => controller.restart()
                        )
                    );
                }
            )
        );

        this.context.subscriptions.push(
            this.output,
            this.diagnostics,
            ...this.disposables
        );

        this.output.appendLine('AFP-P10-T4.11 extension activation completed.');
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
