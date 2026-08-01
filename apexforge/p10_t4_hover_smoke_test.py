"""AFP-P10-T4.5 syntax-level hover smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import which
import subprocess
import sys

from language_server.hover import (
    CANONICAL_HOVER_SHA256,
    HOVER_KIND,
    HOVER_MARKUP_KIND,
    HOVER_METHOD,
    HOVER_SCHEMA,
    P10_T4_HOVER_VERSION,
    hover,
    hover_fingerprint,
    lsp_position_to_offset,
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
from tooling.vscode_document_symbols import (
    CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256,
    audit_vscode_document_symbols,
)
from tooling.vscode_hover import (
    CANONICAL_VSCODE_HOVER_SHA256,
    P10_T4_VSCODE_HOVER_VERSION,
    VSCODE_HOVER_KIND,
    VSCODE_HOVER_SCHEMA,
    audit_vscode_hover,
    hover_fingerprint as vscode_hover_fingerprint,
)
from tooling.vscode_lsp_activation import (
    CANONICAL_VSCODE_LSP_ACTIVATION_SHA256,
    audit_vscode_lsp_activation,
)


EXPECTED_SERVER_SHA256 = "c3038a06ccd7edc573571df165063d7d2eefb471748f23c40e80b4bc7b6a6e94"
EXPECTED_VSCODE_SHA256 = "f8367f64fae736a53cb2c3faf855314aa4e4958d99728332cbab28fa2aa5db56"
EXPECTED_T4_4_SHA256 = "4e2dc7a669b47a2859925c5c1bfa2a6057b4964ad2642c1cbb1aaa79b0dc4bd8"
EXPECTED_T4_3_SHA256 = "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"

URI = "file:///C:/ApexForgeHover/main.apex"
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


def initialize_params(*, hover_enabled: bool, symbols: bool = False) -> dict:
    text_document = {}
    if hover_enabled:
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
        "rootUri": "file:///C:/ApexForgeHover",
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


def position_of(text: str, token: str) -> dict[str, int]:
    offset = text.index(token)
    return lsp_position(text, offset)


def hover_request(
    text: str,
    token: str,
    *,
    message_id: int = 2,
) -> dict:
    return request(
        message_id,
        HOVER_METHOD,
        {
            "textDocument": {"uri": URI},
            "position": position_of(text, token),
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
        rootUri: 'file:///ApexForgeHover',
        capabilities: {
            textDocument: {
                hover: {contentFormat: ['markdown', 'plaintext']},
            },
        },
    });
    assert.strictEqual(initialized.capabilities.hoverProvider, true);
    const uri = 'file:///ApexForgeHover/main.apex';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {
            uri,
            languageId: 'apexforge',
            version: 1,
            text: 'function Identity(value : int) : int { return value }\n',
        },
    });
    const result = await client.sendRequest('textDocument/hover', {
        textDocument: {uri},
        position: {line: 0, character: 9},
    });
    assert.ok(result);
    assert.strictEqual(result.contents.kind, 'markdown');
    assert.ok(result.contents.value.includes('function Identity'));
    await client.stop();
    assert.strictEqual(client.lastExitCode, 0);
    console.log('AFP-P10-T4.5 Node hover request: PASS');
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


def markdown_value(result: object) -> str:
    require(type(result) is dict, "hover result must be an object")
    contents = result.get("contents")
    require(type(contents) is dict, "hover contents must be MarkupContent")
    require(contents.get("kind") == HOVER_MARKUP_KIND, "hover markup kind changed")
    value = contents.get("value")
    require(type(value) is str, "hover markdown must be text")
    return value


def main() -> None:
    require(P10_T4_HOVER_VERSION == "10-T4.5", "server version changed")
    require(HOVER_SCHEMA == 1, "server schema changed")
    require(HOVER_KIND == "apexforge.language-server-hover", "server kind changed")
    require(HOVER_METHOD == "textDocument/hover", "hover method changed")
    require(hover_fingerprint() == EXPECTED_SERVER_SHA256, "server hover hash drift")
    require(CANONICAL_HOVER_SHA256 == EXPECTED_SERVER_SHA256, "server constant drift")

    require(lsp_position_to_offset("😀x", {"line": 0, "character": 2}) == 1, "UTF-16 astral conversion changed")
    try:
        lsp_position_to_offset("😀x", {"line": 0, "character": 1})
    except ValueError:
        pass
    else:
        raise AssertionError("surrogate-pair split was accepted")

    function_hover = hover(URI, FUNCTION_SOURCE, position_of(FUNCTION_SOURCE, "Identity"))
    require("function Identity<T : numeric>" in markdown_value(function_hover), "function hover changed")
    parameter_hover = hover(URI, FUNCTION_SOURCE, position_of(FUNCTION_SOURCE, "value"))
    require("parameter value : T" in markdown_value(parameter_hover), "parameter hover changed")
    binding_hover = hover(URI, FUNCTION_SOURCE, position_of(FUNCTION_SOURCE, "copy"))
    require("let copy" in markdown_value(binding_hover), "binding hover changed")

    module_hover = hover(URI, MODULE_SOURCE, position_of(MODULE_SOURCE, "demo.main"))
    require("module demo.main" in markdown_value(module_hover), "module hover changed")
    import_hover = hover(URI, MODULE_SOURCE, position_of(MODULE_SOURCE, "demo.core"))
    require("import demo.core" in markdown_value(import_hover), "import hover changed")
    state_hover = hover(URI, MODULE_SOURCE, position_of(MODULE_SOURCE, "count"))
    require("state count : int" in markdown_value(state_hover), "state hover changed")
    path_hover = hover(URI, MODULE_SOURCE, position_of(MODULE_SOURCE, "primary"))
    require("path primary @ 10" in markdown_value(path_hover), "path hover changed")
    require(hover(URI, MODULE_SOURCE, {"line": 2, "character": 0}) is None, "whitespace exposed hover")
    require(hover(URI, INVALID_SOURCE, {"line": 0, "character": 9}) is None, "invalid source exposed hover")

    require(active_server_capabilities() == server_capabilities(), "frozen T4.1 capabilities changed")
    require(
        active_server_capabilities(hover_enabled=True)
        == {**server_capabilities(), "hoverProvider": True},
        "negotiated hover capability changed",
    )
    require(
        active_server_capabilities(document_symbols_enabled=True, hover_enabled=True)
        == {
            **server_capabilities(),
            "documentSymbolProvider": True,
            "hoverProvider": True,
        },
        "combined capability negotiation changed",
    )

    disabled = LanguageServerSession()
    initialized = disabled.process(request(1, "initialize", initialize_params(hover_enabled=False)))
    require(initialized["result"]["capabilities"] == server_capabilities(), "disabled initialize changed")
    disabled.process(did_open(FUNCTION_SOURCE))
    require(error_code(disabled.process(hover_request(FUNCTION_SOURCE, "Identity"))) == METHOD_NOT_FOUND, "disabled hover did not use MethodNotFound")

    session = LanguageServerSession()
    initialized = session.process(request(1, "initialize", initialize_params(hover_enabled=True, symbols=True)))
    capabilities = initialized["result"]["capabilities"]
    require(capabilities["hoverProvider"] is True, "hover provider not advertised")
    require(capabilities["documentSymbolProvider"] is True, "T4.4 provider not preserved")
    session.process(did_open(FUNCTION_SOURCE))
    response = session.process(hover_request(FUNCTION_SOURCE, "Identity"))
    require(type(response) is dict and response.get("id") == 2, "hover response missing")
    require("function Identity" in markdown_value(response.get("result")), "session hover changed")
    session.process(notification("textDocument/didClose", {"textDocument": {"uri": URI}}))
    require(error_code(session.process(hover_request(FUNCTION_SOURCE, "Identity", message_id=3))) == INVALID_PARAMS, "closed document hover was accepted")

    transcript = b"".join(
        encode_message(item)
        for item in (
            request(11, "initialize", initialize_params(hover_enabled=True)),
            notification("initialized", {}),
            did_open(FUNCTION_SOURCE),
            hover_request(FUNCTION_SOURCE, "Identity", message_id=12),
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
    require("function Identity" in markdown_value(messages[1]["result"]), "stdio hover changed")

    out = StringIO()
    err = StringIO()
    require(server_main(("--hover-contract",), stdout=out, stderr=err) == 0, "hover contract failed")
    require(out.getvalue() == EXPECTED_SERVER_SHA256 + "\n", "hover CLI hash changed")
    require(err.getvalue() == "", "hover CLI wrote stderr")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    activation = audit_vscode_lsp_activation(extension_root)
    require(activation.activation_sha256 == EXPECTED_T4_3_SHA256, "T4.3 projection changed")
    require(CANONICAL_VSCODE_LSP_ACTIVATION_SHA256 == EXPECTED_T4_3_SHA256, "T4.3 constant changed")

    symbols = audit_vscode_document_symbols(extension_root)
    require(symbols.document_symbol_sha256 == EXPECTED_T4_4_SHA256, "T4.4 projection changed")
    require(CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256 == EXPECTED_T4_4_SHA256, "T4.4 constant changed")

    vscode_audit = audit_vscode_hover(extension_root)
    require(P10_T4_VSCODE_HOVER_VERSION == "10-T4.5", "VS Code version changed")
    require(VSCODE_HOVER_SCHEMA == 1, "VS Code schema changed")
    require(VSCODE_HOVER_KIND == "apexforge.vscode-hover", "VS Code kind changed")
    require(vscode_audit.hover_sha256 == EXPECTED_VSCODE_SHA256, "VS Code audit hash changed")
    require(CANONICAL_VSCODE_HOVER_SHA256 == EXPECTED_VSCODE_SHA256, "VS Code constant changed")

    runtime_hashes = {
        name: __import__("hashlib").sha256((extension_root / name).read_bytes()).hexdigest()
        for name in ("extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
    }
    require(vscode_hover_fingerprint(runtime_hashes) == EXPECTED_VSCODE_SHA256, "VS Code hover projection changed")

    extension_text = (extension_root / "extension.js").read_text(encoding="utf-8")
    for marker in (
        "registerHoverProvider",
        "provideHover",
        "textDocument/hover",
        "new vscode.Hover",
        "new vscode.MarkdownString",
    ):
        require(marker in extension_text, f"extension marker missing: {marker}")

    node = which("node")
    require(node is not None, "Node.js is required for T4.5 testing")
    completed = subprocess.run((node, "--check", str(extension_root / "extension.js")), check=False, capture_output=True, text=True)
    require(completed.returncode == 0, f"extension syntax failed: {completed.stderr}")

    harness_path = repository_root / "dist" / "p10_t4_5_node_smoke.js"
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
        require(completed.returncode == 0, "Node hover lifecycle failed:\n" + completed.stderr + completed.stdout)
        require("AFP-P10-T4.5 Node hover request: PASS" in completed.stdout, "Node success marker missing")
    finally:
        harness_path.unlink(missing_ok=True)

    print("AFP-P10-T4.5 syntax-level hover smoke test passed.")
    print("Declaration and nested-member hover: PASS")
    print("Markdown Hover projection: PASS")
    print("UTF-16 request positions and ranges: PASS")
    print("Conditional capability negotiation: PASS")
    print("Open-document request handling: PASS")
    print("VS Code Hover provider registration: PASS")
    print("Node-to-Python hover request: PASS")
    print("Frozen T4.3 activation projection: PASS")
    print("Frozen T4.4 document-symbol projection: PASS")
    print("Deterministic T4.5 fingerprints: PASS")


if __name__ == "__main__":
    main()
