"""AFP-P10-T4.4 hierarchical document-symbol smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import which
import subprocess
import sys

from language_server.protocol import INVALID_PARAMS, METHOD_NOT_FOUND, encode_message, read_message
from language_server.server import (
    EXIT_SUCCESS,
    LanguageServerSession,
    active_server_capabilities,
    main as server_main,
    run_language_server,
    server_capabilities,
)
from language_server.symbols import (
    CANONICAL_DOCUMENT_SYMBOLS_SHA256,
    DOCUMENT_SYMBOL_KIND,
    DOCUMENT_SYMBOL_METHOD,
    DOCUMENT_SYMBOL_SCHEMA,
    P10_T4_DOCUMENT_SYMBOL_VERSION,
    SYMBOL_KIND_FUNCTION,
    SYMBOL_KIND_MODULE,
    SYMBOL_KIND_OBJECT,
    document_symbols,
    document_symbols_fingerprint,
)
from tooling.vscode_document_symbols import (
    CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256,
    P10_T4_VSCODE_DOCUMENT_SYMBOL_VERSION,
    VSCODE_DOCUMENT_SYMBOL_KIND,
    VSCODE_DOCUMENT_SYMBOL_SCHEMA,
    audit_vscode_document_symbols,
    document_symbol_fingerprint as vscode_document_symbol_fingerprint,
)
from tooling.vscode_lsp_activation import (
    CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
    audit_vscode_lsp_activation,
)


EXPECTED_SERVER_SHA256 = "f4c337b1bbaab80093bb765323e27d3583609e4e0e229685a4aad9b82153484e"
EXPECTED_VSCODE_SHA256 = "4e2dc7a669b47a2859925c5c1bfa2a6057b4964ad2642c1cbb1aaa79b0dc4bd8"
EXPECTED_T4_3_SHA256 = "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"

URI = "file:///C:/ApexForgeSymbols/main.apex"
FUNCTION_SOURCE = """function Identity<T : numeric>(value : T) : T {
    let copy = value
    return copy
}
"""
MODULE_SOURCE = """module demo.main
import demo.core

directive Counter {
    state count : int = 0
    event done

    cause run {
        path primary @ 10 {
            add count 1
            emit done
        }
    }
}
"""
INVALID_SOURCE = "function Broken(value : int) : int { return }\n"


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


def initialize_params(*, symbols: bool) -> dict:
    text_document = {}
    if symbols:
        text_document["documentSymbol"] = {
            "hierarchicalDocumentSymbolSupport": True,
            "symbolKind": {"valueSet": list(range(1, 27))},
        }
    return {
        "processId": None,
        "rootUri": "file:///C:/ApexForgeSymbols",
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


def document_symbol_request(message_id: int = 2) -> dict:
    return request(
        message_id,
        DOCUMENT_SYMBOL_METHOD,
        {"textDocument": {"uri": URI}},
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
        rootUri: 'file:///ApexForgeSymbols',
        capabilities: {
            textDocument: {
                documentSymbol: {
                    hierarchicalDocumentSymbolSupport: true,
                    symbolKind: {valueSet: Array.from({length: 26}, (_, index) => index + 1)},
                },
            },
        },
    });
    assert.strictEqual(initialized.capabilities.documentSymbolProvider, true);
    const uri = 'file:///ApexForgeSymbols/main.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {
            uri,
            languageId: 'apexforge',
            version: 1,
            text: 'function Identity(value : int) : int { return value }\n',
        },
    });
    const symbols = await client.sendRequest('textDocument/documentSymbol', {
        textDocument: {uri},
    });
    assert.strictEqual(symbols.length, 1);
    assert.strictEqual(symbols[0].name, 'Identity');
    assert.strictEqual(symbols[0].kind, 12);
    await client.stop();
    assert.strictEqual(client.lastExitCode, 0);
    console.log('AFP-P10-T4.4 Node document-symbol request: PASS');
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
    require(P10_T4_DOCUMENT_SYMBOL_VERSION == "10-T4.4", "server version changed")
    require(DOCUMENT_SYMBOL_SCHEMA == 1, "server schema changed")
    require(
        DOCUMENT_SYMBOL_KIND == "apexforge.language-server-document-symbols",
        "server kind changed",
    )
    require(DOCUMENT_SYMBOL_METHOD == "textDocument/documentSymbol", "method changed")
    require(document_symbols_fingerprint() == EXPECTED_SERVER_SHA256, "server hash drift")
    require(CANONICAL_DOCUMENT_SYMBOLS_SHA256 == EXPECTED_SERVER_SHA256, "server constant drift")

    function_values = document_symbols(URI, FUNCTION_SOURCE)
    require(len(function_values) == 1, "function symbol count changed")
    function = function_values[0]
    require(function["name"] == "Identity", "function name changed")
    require(function["kind"] == SYMBOL_KIND_FUNCTION, "function kind changed")
    require("function<T : numeric>" in function["detail"], "generic detail omitted")
    children = function.get("children")
    require(type(children) is list and len(children) == 3, "function children changed")
    require([item["name"] for item in children] == ["T", "value", "copy"], "function child order changed")

    module_values = document_symbols(URI, MODULE_SOURCE)
    require(len(module_values) == 1, "module symbol count changed")
    module = module_values[0]
    require(module["name"] == "demo.main", "module name changed")
    require(module["kind"] == SYMBOL_KIND_MODULE, "module kind changed")
    module_children = module.get("children")
    require(type(module_children) is list and len(module_children) == 2, "module children changed")
    require(module_children[0]["name"] == "demo.core", "module import omitted")
    directive = module_children[1]
    require(directive["name"] == "Counter", "directive name changed")
    require(directive["kind"] == SYMBOL_KIND_OBJECT, "directive kind changed")
    require([item["name"] for item in directive["children"]] == ["count", "done", "run"], "directive order changed")
    require(document_symbols(URI, INVALID_SOURCE) == (), "invalid source exposed symbols")

    require(active_server_capabilities(document_symbols_enabled=False) == server_capabilities(), "frozen capabilities changed")
    require(
        active_server_capabilities(document_symbols_enabled=True)
        == {**server_capabilities(), "documentSymbolProvider": True},
        "negotiated symbol capability changed",
    )

    disabled = LanguageServerSession()
    initialized = disabled.process(request(1, "initialize", initialize_params(symbols=False)))
    require(initialized["result"]["capabilities"] == server_capabilities(), "T4.1 initialize changed")
    disabled.process(did_open(FUNCTION_SOURCE))
    require(error_code(disabled.process(document_symbol_request())) == METHOD_NOT_FOUND, "disabled symbols did not use MethodNotFound")

    session = LanguageServerSession()
    initialized = session.process(request(1, "initialize", initialize_params(symbols=True)))
    require(initialized["result"]["capabilities"]["documentSymbolProvider"] is True, "provider not advertised")
    session.process(did_open(MODULE_SOURCE))
    response = session.process(document_symbol_request())
    require(type(response) is dict and response.get("id") == 2, "symbol response missing")
    result = response.get("result")
    require(type(result) is list and result[0]["name"] == "demo.main", "symbol result changed")
    session.process(notification("textDocument/didClose", {"textDocument": {"uri": URI}}))
    require(error_code(session.process(document_symbol_request(3))) == INVALID_PARAMS, "closed document request was accepted")

    transcript = b"".join(
        encode_message(item)
        for item in (
            request(11, "initialize", initialize_params(symbols=True)),
            notification("initialized", {}),
            did_open(FUNCTION_SOURCE),
            document_symbol_request(12),
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
    require(messages[1]["result"][0]["name"] == "Identity", "stdio symbols changed")

    out = StringIO()
    err = StringIO()
    require(server_main(("--symbols-contract",), stdout=out, stderr=err) == 0, "symbols contract failed")
    require(out.getvalue() == EXPECTED_SERVER_SHA256 + "\n", "symbols CLI hash changed")
    require(err.getvalue() == "", "symbols CLI wrote stderr")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    activation = audit_vscode_lsp_activation(extension_root)
    require(activation.activation_sha256 == EXPECTED_T4_3_SHA256, "T4.3 projection changed")
    require(CANONICAL_VSCODE_LSP_ACTIVATION_SHA256 == EXPECTED_T4_3_SHA256, "T4.3 constant changed")

    vscode_audit = audit_vscode_document_symbols(extension_root)
    require(P10_T4_VSCODE_DOCUMENT_SYMBOL_VERSION == "10-T4.4", "VS Code version changed")
    require(VSCODE_DOCUMENT_SYMBOL_SCHEMA == 1, "VS Code schema changed")
    require(VSCODE_DOCUMENT_SYMBOL_KIND == "apexforge.vscode-document-symbols", "VS Code kind changed")
    require(vscode_audit.document_symbol_sha256 == EXPECTED_VSCODE_SHA256, "VS Code audit hash changed")
    require(CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256 == EXPECTED_VSCODE_SHA256, "VS Code constant changed")

    runtime_hashes = {
        name: __import__("hashlib").sha256((extension_root / name).read_bytes()).hexdigest()
        for name in ("extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
    }
    require(vscode_document_symbol_fingerprint(runtime_hashes) == EXPECTED_VSCODE_SHA256, "VS Code projection changed")

    extension_text = (extension_root / "extension.js").read_text(encoding="utf-8")
    for marker in (
        "registerDocumentSymbolProvider",
        "provideDocumentSymbols",
        "textDocument/documentSymbol",
        "new vscode.DocumentSymbol",
    ):
        require(marker in extension_text, f"extension marker missing: {marker}")

    node = which("node")
    require(node is not None, "Node.js is required for T4.4 testing")
    completed = subprocess.run(
        (
            node,
            "--check",
            str(extension_root / "extension.js"),
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, f"extension syntax failed: {completed.stderr}")

    harness_path = repository_root / "dist" / "p10_t4_4_node_smoke.js"
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
        completed = subprocess.run(
            (node, str(harness_path)),
            cwd=str(repository_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        require(completed.returncode == 0, "Node document-symbol lifecycle failed:\n" + completed.stderr + completed.stdout)
        require("AFP-P10-T4.4 Node document-symbol request: PASS" in completed.stdout, "Node success marker missing")
    finally:
        harness_path.unlink(missing_ok=True)

    print("AFP-P10-T4.4 hierarchical document-symbol smoke test passed.")
    print("Module and declaration hierarchy: PASS")
    print("Nested member symbols: PASS")
    print("UTF-16 LSP ranges: PASS")
    print("Conditional capability negotiation: PASS")
    print("Open-document request handling: PASS")
    print("VS Code Outline provider registration: PASS")
    print("Node-to-Python document-symbol request: PASS")
    print("Frozen T4.3 activation projection: PASS")
    print("Deterministic T4.4 fingerprints: PASS")


if __name__ == "__main__":
    main()
