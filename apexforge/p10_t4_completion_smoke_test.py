"""AFP-P10-T4.6 context-aware completion smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
import hashlib
import json
from pathlib import Path
from shutil import which
import subprocess
import sys
from typing import Optional

from language_server.completion import (
    CANONICAL_COMPLETION_SHA256,
    COMPLETION_KIND,
    COMPLETION_METHOD,
    COMPLETION_SCHEMA,
    COMPLETION_TRIGGER_CHARACTERS,
    P10_T4_COMPLETION_VERSION,
    completion,
    completion_fingerprint,
)
from language_server.protocol import (
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    encode_message,
    read_message,
)
from language_server.server import (
    EXIT_SUCCESS,
    LanguageServerSession,
    active_server_capabilities,
    main as server_main,
    run_language_server,
    server_capabilities,
)
from tooling.vscode_completion import (
    CANONICAL_VSCODE_COMPLETION_SHA256,
    P10_T4_VSCODE_COMPLETION_VERSION,
    VSCODE_COMPLETION_KIND,
    VSCODE_COMPLETION_SCHEMA,
    audit_vscode_completion,
    completion_fingerprint as vscode_completion_fingerprint,
)
from tooling.vscode_document_symbols import (
    CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256,
    audit_vscode_document_symbols,
)
from tooling.vscode_hover import (
    CANONICAL_VSCODE_HOVER_SHA256,
    audit_vscode_hover,
)
from tooling.vscode_lsp_activation import (
    CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
    audit_vscode_lsp_activation,
)


EXPECTED_SERVER_SHA256 = "8a6054d257a8b98c1a64584c7c8b9f9a5416a62769c11a500ab34afd333f21c5"
EXPECTED_VSCODE_SHA256 = "a583db79bf020cad7c96d9696814e151cf26e471f61bb7097617747c0434127a"
EXPECTED_T4_5_SHA256 = "f8367f64fae736a53cb2c3faf855314aa4e4958d99728332cbab28fa2aa5db56"
EXPECTED_T4_4_SHA256 = "4e2dc7a669b47a2859925c5c1bfa2a6057b4964ad2642c1cbb1aaa79b0dc4bd8"
EXPECTED_T4_3_SHA256 = "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"

URI = "file:///C:/ApexForgeCompletion/main.apex"
FUNCTION_SOURCE = """function Identity<T : numeric>(value : T) : T {
    let copy = value
    return c"""
DIRECTIVE_SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            emit
        }
    }
}"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def request(message_id: object, method: str, params: object = None) -> dict:
    value = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        value["params"] = params
    return value


def notification(method: str, params: object = None) -> dict:
    value = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        value["params"] = params
    return value


def initialize_params(*, completion_enabled: bool, hover: bool = False, symbols: bool = False) -> dict:
    text_document = {}
    if completion_enabled:
        text_document["completion"] = {
            "completionItem": {
                "documentationFormat": ["markdown", "plaintext"],
                "snippetSupport": False,
            }
        }
    if hover:
        text_document["hover"] = {
            "contentFormat": ["markdown", "plaintext"],
        }
    if symbols:
        text_document["documentSymbol"] = {
            "hierarchicalDocumentSymbolSupport": True,
            "symbolKind": {"valueSet": list(range(1, 27))},
        }
    return {
        "processId": None,
        "rootUri": "file:///C:/ApexForgeCompletion",
        "capabilities": {"textDocument": text_document},
    }


def did_open(text: str, *, version: int = 1) -> dict:
    return notification(
        "textDocument/didOpen",
        {
            "textDocument": {
                "uri": URI,
                "languageId": "apexforge",
                "version": version,
                "text": text,
            }
        },
    )


def lsp_position(text: str, offset: int) -> dict[str, int]:
    line = text.count("\n", 0, offset)
    start = text.rfind("\n", 0, offset) + 1
    character = len(text[start:offset].encode("utf-16-le")) // 2
    return {"line": line, "character": character}


def completion_at(text: str, offset: Optional[int] = None) -> dict[str, object]:
    selected = len(text) if offset is None else offset
    return completion(URI, text, lsp_position(text, selected))


def labels(result: object) -> tuple[str, ...]:
    require(type(result) is dict, "completion result must be an object")
    require(result.get("isIncomplete") is False, "completion list became incomplete")
    items = result.get("items")
    require(type(items) is list, "completion items must be an array")
    return tuple(item["label"] for item in items)


def completion_request(text: str, *, message_id: int = 2) -> dict:
    return request(
        message_id,
        COMPLETION_METHOD,
        {
            "textDocument": {"uri": URI},
            "position": lsp_position(text, len(text)),
            "context": {"triggerKind": 1},
        },
    )


def error_code(response: object) -> int:
    require(type(response) is dict, "expected response object")
    error = response.get("error")
    require(type(error) is dict, "expected JSON-RPC error")
    code = error.get("code")
    require(type(code) is int, "expected integer error code")
    return code


def decode_all(data: bytes) -> tuple[dict, ...]:
    stream = BytesIO(data)
    values = []
    while stream.tell() < len(data):
        value = read_message(stream)
        require(type(value) is dict, "framed value was not an object")
        values.append(dict(value))
    return tuple(values)


def node_harness(client_path: Path, server_path: Path, repository_root: Path) -> str:
    template = r"""
'use strict';
const assert = require('assert');
const {LspProcessClient} = require(__CLIENT_PATH__);

(async () => {
    const client = new LspProcessClient({
        command: __PYTHON_COMMAND__,
        args: [__SERVER_PATH__, '--stdio'],
        cwd: __REPOSITORY_ROOT__,
        onStderr(text) { process.stderr.write(text); },
    });
    const initialized = await client.start({
        processId: process.pid,
        rootUri: 'file:///ApexForgeCompletion',
        capabilities: {
            textDocument: {
                completion: {
                    completionItem: {
                        documentationFormat: ['markdown', 'plaintext'],
                        snippetSupport: false,
                    },
                },
            },
        },
    });
    assert.strictEqual(initialized.capabilities.completionProvider.resolveProvider, false);
    assert.deepStrictEqual(initialized.capabilities.completionProvider.triggerCharacters, ['@', ':']);
    const uri = 'file:///ApexForgeCompletion/main.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {
            uri,
            languageId: 'apexforge',
            version: 1,
            text: 'function Identity<T : numeric>(value : T) : T {\n    let copy = value\n    return c',
        },
    });
    const result = await client.sendRequest('textDocument/completion', {
        textDocument: {uri},
        position: {line: 2, character: 12},
        context: {triggerKind: 1},
    });
    assert.strictEqual(result.isIncomplete, false);
    const labels = result.items.map((item) => item.label);
    assert.ok(labels.includes('copy'));
    assert.ok(labels.includes('collection'));
    await client.stop();
    assert.strictEqual(client.lastExitCode, 0);
    console.log('AFP-P10-T4.6 Node completion request: PASS');
})().catch((error) => {
    console.error(error && error.stack ? error.stack : String(error));
    process.exitCode = 1;
});
"""
    return (
        template
        .replace("__CLIENT_PATH__", json.dumps(str(client_path)))
        .replace("__PYTHON_COMMAND__", json.dumps(sys.executable))
        .replace("__SERVER_PATH__", json.dumps(str(server_path)))
        .replace("__REPOSITORY_ROOT__", json.dumps(str(repository_root)))
    )


def main() -> None:
    require(P10_T4_COMPLETION_VERSION == "10-T4.6", "server version changed")
    require(COMPLETION_SCHEMA == 1, "server schema changed")
    require(COMPLETION_KIND == "apexforge.language-server-completion", "server kind changed")
    require(COMPLETION_METHOD == "textDocument/completion", "completion method changed")
    require(COMPLETION_TRIGGER_CHARACTERS == ("@", ":"), "trigger characters changed")
    require(completion_fingerprint() == EXPECTED_SERVER_SHA256, "server completion hash drift")
    require(CANONICAL_COMPLETION_SHA256 == EXPECTED_SERVER_SHA256, "server constant drift")

    require(labels(completion_at("")) == ("authority", "directive", "function", "import", "module", "principal", "role", "workflow"), "top-level completion changed")
    require(labels(completion_at("dir")) == ("directive",), "prefix filtering changed")
    directive_items = labels(completion_at("directive Demo {\n    "))
    require(directive_items == ("authority", "cause", "event", "requires", "state"), "directive context changed")

    state_source = "directive Counter {\n    state count : int = 0\n    cause run {\n        path primary @ 10 {\n            add "
    require(labels(completion_at(state_source)) == ("count",), "state target completion changed")
    event_source = "directive Counter {\n    event changed\n    cause run {\n        path primary @ 10 {\n            emit "
    require(labels(completion_at(event_source)) == ("changed",), "event target completion changed")

    type_items = labels(completion_at("function Identity<T : numeric>(value : "))
    require("T" in type_items and "int" in type_items and "string" in type_items, "type completion changed")
    require(labels(completion_at("function Identity<T : ")) == ("numeric",), "constraint completion changed")

    function_items = labels(completion_at(FUNCTION_SOURCE))
    require("copy" in function_items, "local binding completion missing")
    require("collection" in function_items, "built-in type prefix completion missing")
    require(labels(completion_at('function X() : string {\n    return "abc')) == (), "string completion leaked")

    unicode_result = completion_at("😀 dir")
    unicode_item = unicode_result["items"][0]
    require(unicode_item["label"] == "directive", "UTF-16 prefix label changed")
    require(unicode_item["textEdit"]["range"] == {"start": {"line": 0, "character": 3}, "end": {"line": 0, "character": 6}}, "UTF-16 replacement range changed")

    require(active_server_capabilities() == server_capabilities(), "frozen T4.1 capabilities changed")
    expected_provider = {
        "resolveProvider": False,
        "triggerCharacters": ["@", ":"],
    }
    require(active_server_capabilities(completion_enabled=True) == {**server_capabilities(), "completionProvider": expected_provider}, "completion capability changed")
    combined = active_server_capabilities(document_symbols_enabled=True, hover_enabled=True, completion_enabled=True)
    require(combined["documentSymbolProvider"] is True, "T4.4 capability missing")
    require(combined["hoverProvider"] is True, "T4.5 capability missing")
    require(combined["completionProvider"] == expected_provider, "combined completion capability changed")

    disabled = LanguageServerSession()
    initialized = disabled.process(request(1, "initialize", initialize_params(completion_enabled=False)))
    require(initialized["result"]["capabilities"] == server_capabilities(), "disabled initialize changed")
    disabled.process(did_open(FUNCTION_SOURCE))
    require(error_code(disabled.process(completion_request(FUNCTION_SOURCE))) == METHOD_NOT_FOUND, "disabled completion did not use MethodNotFound")

    session = LanguageServerSession()
    initialized = session.process(request(1, "initialize", initialize_params(completion_enabled=True, hover=True, symbols=True)))
    capabilities = initialized["result"]["capabilities"]
    require(capabilities["completionProvider"] == expected_provider, "completion provider not advertised")
    require(capabilities["hoverProvider"] is True, "T4.5 provider not preserved")
    require(capabilities["documentSymbolProvider"] is True, "T4.4 provider not preserved")
    session.process(did_open(FUNCTION_SOURCE))
    response = session.process(completion_request(FUNCTION_SOURCE))
    require(type(response) is dict and response.get("id") == 2, "completion response missing")
    require("copy" in labels(response.get("result")), "session completion changed")
    session.process(notification("textDocument/didClose", {"textDocument": {"uri": URI}}))
    require(error_code(session.process(completion_request(FUNCTION_SOURCE, message_id=3))) == INVALID_PARAMS, "closed document completion was accepted")

    transcript = b"".join(
        encode_message(item)
        for item in (
            request(11, "initialize", initialize_params(completion_enabled=True)),
            notification("initialized", {}),
            did_open(FUNCTION_SOURCE),
            completion_request(FUNCTION_SOURCE, message_id=12),
            request(13, "shutdown"),
            notification("exit"),
        )
    )
    output = BytesIO()
    errors = StringIO()
    code = run_language_server(BytesIO(transcript), output, error_stream=errors)
    require(code == EXIT_SUCCESS, "stdio transcript failed")
    require(errors.getvalue() == "", "stdio transcript wrote stderr")
    messages = decode_all(output.getvalue())
    require([item.get("id") for item in messages] == [11, 12, 13], "response order changed")
    require("copy" in labels(messages[1]["result"]), "stdio completion changed")

    out = StringIO()
    err = StringIO()
    require(server_main(("--completion-contract",), stdout=out, stderr=err) == 0, "completion contract failed")
    require(out.getvalue() == EXPECTED_SERVER_SHA256 + "\n", "completion CLI hash changed")
    require(err.getvalue() == "", "completion CLI wrote stderr")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    activation = audit_vscode_lsp_activation(extension_root)
    require(activation.activation_sha256 == EXPECTED_T4_3_SHA256, "T4.3 projection changed")
    require(CANONICAL_VSCODE_LSP_ACTIVATION_SHA256 == EXPECTED_T4_3_SHA256, "T4.3 constant changed")

    symbols = audit_vscode_document_symbols(extension_root)
    require(symbols.document_symbol_sha256 == EXPECTED_T4_4_SHA256, "T4.4 projection changed")
    require(CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256 == EXPECTED_T4_4_SHA256, "T4.4 constant changed")

    hover = audit_vscode_hover(extension_root)
    require(hover.hover_sha256 == EXPECTED_T4_5_SHA256, "T4.5 projection changed")
    require(CANONICAL_VSCODE_HOVER_SHA256 == EXPECTED_T4_5_SHA256, "T4.5 constant changed")

    vscode_audit = audit_vscode_completion(extension_root)
    require(P10_T4_VSCODE_COMPLETION_VERSION == "10-T4.6", "VS Code version changed")
    require(VSCODE_COMPLETION_SCHEMA == 1, "VS Code schema changed")
    require(VSCODE_COMPLETION_KIND == "apexforge.vscode-completion", "VS Code kind changed")
    require(vscode_audit.completion_sha256 == EXPECTED_VSCODE_SHA256, "VS Code audit hash changed")
    require(CANONICAL_VSCODE_COMPLETION_SHA256 == EXPECTED_VSCODE_SHA256, "VS Code constant changed")

    runtime_hashes = {
        name: hashlib.sha256((extension_root / name).read_bytes()).hexdigest()
        for name in ("extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
    }
    require(vscode_completion_fingerprint(runtime_hashes) == EXPECTED_VSCODE_SHA256, "VS Code completion projection changed")

    extension_text = (extension_root / "extension.js").read_text(encoding="utf-8")
    for marker in (
        "registerCompletionItemProvider",
        "provideCompletionItems",
        "textDocument/completion",
        "new vscode.CompletionItem",
        "CompletionItemKind.TypeParameter",
    ):
        require(marker in extension_text, f"extension marker missing: {marker}")

    node = which("node")
    require(node is not None, "Node.js is required for T4.6 testing")
    completed = subprocess.run((node, "--check", str(extension_root / "extension.js")), check=False, capture_output=True, text=True)
    require(completed.returncode == 0, f"extension syntax failed: {completed.stderr}")

    harness_path = repository_root / "dist" / "p10_t4_6_node_smoke.js"
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(
        node_harness(
            extension_root / "runtime" / "lsp-client.js",
            repository_root / "apexforge" / "apexforge_lsp.py",
            repository_root,
        ),
        encoding="utf-8",
    )
    try:
        completed = subprocess.run((node, str(harness_path)), cwd=str(repository_root), check=False, capture_output=True, text=True, timeout=30)
        require(completed.returncode == 0, "Node completion lifecycle failed:\n" + completed.stderr + completed.stdout)
        require("AFP-P10-T4.6 Node completion request: PASS" in completed.stdout, "Node success marker missing")
    finally:
        harness_path.unlink(missing_ok=True)

    print("AFP-P10-T4.6 context-aware completion smoke test passed.")
    print("Tolerant incomplete-source completion: PASS")
    print("Block and declaration context selection: PASS")
    print("Type, constraint, state, event, and lexical-scope items: PASS")
    print("UTF-16 identifier replacement ranges: PASS")
    print("Conditional capability negotiation: PASS")
    print("Open-document request handling: PASS")
    print("VS Code CompletionItem provider registration: PASS")
    print("Node-to-Python completion request: PASS")
    print("Frozen T4.3 activation projection: PASS")
    print("Frozen T4.4 document-symbol projection: PASS")
    print("Frozen T4.5 hover projection: PASS")
    print("Deterministic T4.6 fingerprints: PASS")


if __name__ == "__main__":
    main()
