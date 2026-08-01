"""AFP-P10-T4.11 final language-server integration hardening smoke test."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from language_server.integration import (
    CANONICAL_INTEGRATION_SHA256,
    CANCEL_REQUEST_METHOD,
    P10_T4_INTEGRATION_VERSION,
    REQUEST_CANCELLED,
    SET_TRACE_METHOD,
    integrated_capabilities,
    integration_fingerprint,
    verify_frozen_feature_hashes,
)
from language_server.protocol import encode_message, read_message
from language_server.server import (
    LanguageServerSession,
    active_server_capabilities,
    run_language_server,
    server_capabilities,
)
from tooling.vscode_formatting import CANONICAL_VSCODE_FORMATTING_SHA256
from tooling.vscode_integration import (
    CANONICAL_VSCODE_INTEGRATION_SHA256,
    audit_vscode_integration,
    audit_vscode_integration_vsix,
    integration_fingerprint as vscode_integration_fingerprint,
)

EXPECTED_SERVER = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"
EXPECTED_VSCODE = "b901ace810dece5e59840148263a893ea6920424ca7d0b7a2dfd594bb9b20e0b"
SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            message count
            emit changed
        }
    }
}
"""


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def request(message_id: object, method: str, params: object = None) -> dict[str, object]:
    value: dict[str, object] = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        value["params"] = params
    return value


def notification(method: str, params: object = None) -> dict[str, object]:
    value: dict[str, object] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        value["params"] = params
    return value


def all_capabilities() -> dict[str, object]:
    return {
        "textDocument": {
            "publishDiagnostics": {"relatedInformation": True, "versionSupport": True},
            "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
            "hover": {"contentFormat": ["markdown", "plaintext"]},
            "completion": {"completionItem": {"snippetSupport": False}},
            "definition": {"linkSupport": False},
            "references": {},
            "rename": {"prepareSupport": True},
            "formatting": {"dynamicRegistration": False},
        },
        "workspace": {"symbol": {"dynamicRegistration": False}},
    }


def build_vsix(extension_root: Path, path: Path) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for source_name, archive_name in (
            ("extension.js", "extension/extension.js"),
            ("runtime/lsp-client.js", "extension/runtime/lsp-client.js"),
            ("LANGUAGE_SERVER.md", "extension/LANGUAGE_SERVER.md"),
            ("package.json", "extension/package.json"),
        ):
            archive.writestr(archive_name, (extension_root / source_name).read_bytes())


def slow_server_source() -> str:
    return r"""import json, os, sys, time

def read_message():
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line == b"\r\n":
            break
        name, value = line.decode("ascii").split(":", 1)
        headers[name.lower()] = value.strip()
    body = sys.stdin.buffer.read(int(headers["content-length"]))
    return json.loads(body.decode("utf-8"))

def write(value):
    body = json.dumps(value, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    sys.stdout.buffer.flush()

while True:
    message = read_message()
    if message is None:
        break
    method = message.get("method")
    if method == "initialize":
        write({"jsonrpc":"2.0","id":message["id"],"result":{"capabilities":{}}})
    elif method == "test/slow":
        time.sleep(0.35)
        write({"jsonrpc":"2.0","id":message["id"],"result":"late"})
    elif method == "test/crash":
        os._exit(7)
    elif method == "shutdown":
        write({"jsonrpc":"2.0","id":message["id"],"result":None})
    elif method == "exit":
        break
"""


def node_harness(client_path: Path, server_path: Path, repository_root: Path, slow_path: Path) -> str:
    template = r"""
'use strict';
const assert = require('assert');
const path = require('path');
const {pathToFileURL} = require('url');
const {
    CancellationError, LspMessageReader, LspProcessClient,
    REQUEST_CANCELLED, encodeMessage,
} = require(__CLIENT_PATH__);

class Token {
    constructor() { this.isCancellationRequested = false; this.listeners = new Set(); }
    onCancellationRequested(listener) {
        this.listeners.add(listener);
        return {dispose: () => this.listeners.delete(listener)};
    }
    cancel() {
        this.isCancellationRequested = true;
        for (const listener of [...this.listeners]) listener();
    }
}

(async () => {
    const reader = new LspMessageReader();
    const framed = Buffer.concat([
        encodeMessage({jsonrpc:'2.0', id:1, result:'a'}),
        encodeMessage({jsonrpc:'2.0', method:'x'}),
    ]);
    assert.deepStrictEqual(reader.push(framed.subarray(0, 7)), []);
    assert.strictEqual(reader.push(framed.subarray(7)).length, 2);
    assert.throws(() => new LspMessageReader().push(Buffer.from(
        'Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}', 'ascii'
    )), /duplicate/i);

    const rootUri = pathToFileURL(__REPOSITORY_ROOT__).toString();
    const client = new LspProcessClient({
        command: __PYTHON_COMMAND__, args: [__SERVER_PATH__, '--stdio'],
        cwd: __REPOSITORY_ROOT__, onStderr(text) { process.stderr.write(text); },
    });
    const initialized = await client.start({
        processId: process.pid, rootUri, capabilities: __CAPABILITIES__,
    });
    assert.strictEqual(initialized.capabilities.documentFormattingProvider, true);
    assert.strictEqual(initialized.capabilities.workspaceSymbolProvider, true);
    const uri = 'file:///T411Counter.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {uri, languageId:'apexforge', version:1, text:__SOURCE__},
    });
    const symbols = await client.sendRequest('textDocument/documentSymbol', {textDocument:{uri}});
    assert.ok(Array.isArray(symbols) && symbols.length === 1);
    const hover = await client.sendRequest('textDocument/hover', {textDocument:{uri}, position:{line:1,character:10}});
    assert.ok(hover && hover.contents);
    const definition = await client.sendRequest('textDocument/definition', {textDocument:{uri}, position:{line:5,character:17}});
    assert.ok(definition && definition.range);
    const references = await client.sendRequest('textDocument/references', {textDocument:{uri}, position:{line:5,character:17}, context:{includeDeclaration:true}});
    assert.ok(Array.isArray(references) && references.length >= 2);
    const edits = await client.sendRequest('textDocument/formatting', {textDocument:{uri}, options:{tabSize:4,insertSpaces:true}});
    assert.deepStrictEqual(edits, []);
    await Promise.all([client.stop(), client.stop()]);
    assert.strictEqual(client.pending.size, 0);

    let unexpectedExit = null;
    const slow = new LspProcessClient({
        command: __PYTHON_COMMAND__, args: [__SLOW_SERVER__], cwd: __REPOSITORY_ROOT__,
        requestTimeoutMs: 2000, onExit(details) { unexpectedExit = details; },
    });
    await slow.start({processId:process.pid, rootUri, capabilities:{}});
    const token = new Token();
    const pending = slow.sendRequest('test/slow', {}, token);
    setTimeout(() => token.cancel(), 25);
    await assert.rejects(pending, (error) => error instanceof CancellationError && error.code === REQUEST_CANCELLED);
    assert.strictEqual(slow.pending.size, 0);
    await slow.stop();

    const crash = new LspProcessClient({
        command: __PYTHON_COMMAND__, args: [__SLOW_SERVER__], cwd: __REPOSITORY_ROOT__,
        onExit(details) { unexpectedExit = details; },
    });
    await crash.start({processId:process.pid, rootUri, capabilities:{}});
    await assert.rejects(crash.sendRequest('test/crash', {}), /exited/i);
    await new Promise((resolve) => setTimeout(resolve, 50));
    assert.ok(unexpectedExit && unexpectedExit.expected === false && unexpectedExit.code === 7);
    process.stdout.write('node-t4.11-integration: PASS\n');
})().catch((error) => {
    console.error(error && error.stack ? error.stack : error);
    process.exitCode = 1;
});
"""
    return (
        template.replace('__CLIENT_PATH__', json.dumps(str(client_path)))
        .replace('__PYTHON_COMMAND__', json.dumps(sys.executable))
        .replace('__SERVER_PATH__', json.dumps(str(server_path)))
        .replace('__REPOSITORY_ROOT__', json.dumps(str(repository_root)))
        .replace('__SLOW_SERVER__', json.dumps(str(slow_path)))
        .replace('__CAPABILITIES__', json.dumps(all_capabilities()))
        .replace('__SOURCE__', json.dumps(SOURCE))
    )


def main() -> None:
    require(P10_T4_INTEGRATION_VERSION == "10-T4.11", "integration version changed")
    require(integration_fingerprint() == EXPECTED_SERVER, "server integration fingerprint changed")
    require(CANONICAL_INTEGRATION_SHA256 == EXPECTED_SERVER, "server integration constant changed")
    require(verify_frozen_feature_hashes(), "a frozen feature fingerprint changed")
    require(CANONICAL_VSCODE_FORMATTING_SHA256 == "46a4267481b3f4fabd250c7324cc3b4f7be98bb6d5b2b7a52ef05bb6fc27c6ff", "T4.10 VS Code fingerprint changed")

    expected_capabilities = integrated_capabilities()
    actual_capabilities = active_server_capabilities(
        document_symbols_enabled=True,
        hover_enabled=True,
        completion_enabled=True,
        definition_enabled=True,
        references_enabled=True,
        rename_enabled=True,
        workspace_symbols_enabled=True,
        formatting_enabled=True,
    )
    require(actual_capabilities == expected_capabilities, "integrated capability projection changed")
    require("documentFormattingProvider" not in server_capabilities(), "frozen T4.1 capabilities changed")

    session = LanguageServerSession()
    preinit = session.process(request(1, "textDocument/hover", {}))
    require(preinit["error"]["code"] == -32002, "pre-initialize containment changed")
    session.process(notification(CANCEL_REQUEST_METHOD, {"id": 2}))
    cancelled = session.process(request(2, "initialize", {"processId": None, "rootUri": "file:///workspace", "capabilities": all_capabilities()}))
    require(cancelled["error"]["code"] == REQUEST_CANCELLED, "pre-dispatch cancellation changed")
    initialized = session.process(request(3, "initialize", {"processId": None, "rootUri": "file:///workspace", "capabilities": all_capabilities()}))
    require(initialized["result"]["capabilities"] == expected_capabilities, "initialize capability negotiation changed")
    session.process(notification("initialized", {}))
    session.process(notification(SET_TRACE_METHOD, {"value": "verbose"}))
    uri = "file:///Counter.apex"
    session.process(notification("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "apexforge", "version": 1, "text": SOURCE}}))
    require(session.health_snapshot()["open_document_count"] == 1, "document open state changed")
    prior_errors = session.notification_error_count
    session.process(notification("textDocument/didChange", {"textDocument": {"uri": uri, "version": 1}, "contentChanges": [{"text": SOURCE}]}))
    require(session.notification_error_count == prior_errors + 1, "stale version notification was not isolated")
    require(session.health_snapshot()["open_document_count"] == 1, "notification failure poisoned document state")
    malformed_cancel_errors = session.notification_error_count
    session.process(notification(CANCEL_REQUEST_METHOD, {"id": None}))
    require(session.notification_error_count == malformed_cancel_errors + 1, "malformed cancellation was not isolated")
    session.process(notification("unknown/notification", {"value": 1}))
    unknown = session.process(request(4, "unknown/request", {}))
    require(unknown["error"]["code"] == -32601, "unknown request containment changed")
    session.process(notification("textDocument/didClose", {"textDocument": {"uri": uri}}))
    closed_notifications = session.drain_outgoing_notifications()
    require(any(item.get("params", {}).get("diagnostics") == [] for item in closed_notifications), "didClose did not clear diagnostics")
    require(session.health_snapshot()["trace"] == "verbose", "trace state changed")
    shutdown = session.process(request(5, "shutdown"))
    require(shutdown["result"] is None, "shutdown result changed")
    session.process(notification("exit"))
    require(session.health_snapshot()["exit_code"] == 0, "clean exit changed")
    post_exit = session.process(request(6, "shutdown"))
    require(post_exit["error"]["code"] == -32600, "post-exit request containment changed")

    stream_session = LanguageServerSession()
    messages = (
        request(10, "initialize", {"processId": None, "rootUri": "file:///workspace", "capabilities": {}}),
        notification("initialized", {}),
        request(11, "shutdown"),
        notification("exit"),
    )
    input_stream = BytesIO(b"".join(encode_message(item) for item in messages))
    output_stream = BytesIO()
    require(run_language_server(input_stream, output_stream, session=stream_session) == 0, "stdio lifecycle exit changed")
    output_stream.seek(0)
    first = read_message(output_stream)
    second = read_message(output_stream)
    require(first["id"] == 10 and second["id"] == 11, "stdio response order changed")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    audit = audit_vscode_integration(extension_root)
    require(audit.integration_sha256 == EXPECTED_VSCODE, "VS Code integration audit changed")
    runtime_hashes = {
        "extension.js": hashlib.sha256((extension_root / "extension.js").read_bytes()).hexdigest(),
        "runtime/lsp-client.js": hashlib.sha256((extension_root / "runtime" / "lsp-client.js").read_bytes()).hexdigest(),
        "LANGUAGE_SERVER.md": hashlib.sha256((extension_root / "LANGUAGE_SERVER.md").read_bytes()).hexdigest(),
    }
    require(vscode_integration_fingerprint(runtime_hashes) == EXPECTED_VSCODE, "VS Code integration projection changed")

    with tempfile.TemporaryDirectory(prefix="apexforge-t411-") as temp_text:
        temp = Path(temp_text)
        vsix = temp / "apexforge-t411.vsix"
        build_vsix(extension_root, vsix)
        vsix_audit = audit_vscode_integration_vsix(extension_root, vsix)
        require(vsix_audit.integration_sha256 == EXPECTED_VSCODE, "VSIX audit changed")
        slow_path = temp / "slow_lsp.py"
        with slow_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(slow_server_source())
        script = node_harness(
            extension_root / "runtime" / "lsp-client.js",
            repository_root / "apexforge" / "apexforge_lsp.py",
            repository_root,
            slow_path,
        )
        completed = subprocess.run(
            ("node", "-e", script),
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, f"Node integration lifecycle failed: {completed.stderr or completed.stdout}")
        require("node-t4.11-integration: PASS" in completed.stdout, "Node integration output changed")

    print("AFP-P10-T4.11 full language-server integration smoke test passed.")
    print("Frozen T4.1-T4.10 feature contracts: PASS")
    print("Integrated capability negotiation: PASS")
    print("Cancellation and trace notifications: PASS")
    print("Malformed-request and notification containment: PASS")
    print("Document version and diagnostic lifecycle: PASS")
    print("Bounded stdio framing and shutdown lifecycle: PASS")
    print("Serialized client stop and cancellation cleanup: PASS")
    print("Unexpected process-exit reporting: PASS")
    print("VSIX payload integrity and forbidden-file audit: PASS")
    print("Deterministic T4.11 fingerprints: PASS")


if __name__ == "__main__":
    main()
