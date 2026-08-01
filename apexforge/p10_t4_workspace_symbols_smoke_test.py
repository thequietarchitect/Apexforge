"""AFP-P10-T4.9 workspace-symbol smoke and adversarial contract test."""

from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from language_server.protocol import INVALID_PARAMS, METHOD_NOT_FOUND, encode_message, read_message
from language_server.server import (
    EXIT_SUCCESS,
    LanguageServerSession,
    active_server_capabilities,
    main as server_main,
    run_language_server,
    server_capabilities,
)
from language_server.workspace_symbols import (
    CANONICAL_WORKSPACE_SYMBOLS_SHA256,
    MAX_SYMBOL_RESULTS,
    MAX_WORKSPACE_FILES,
    P10_T4_WORKSPACE_SYMBOL_VERSION,
    WORKSPACE_SYMBOL_KIND,
    WORKSPACE_SYMBOL_METHOD,
    WORKSPACE_SYMBOL_SCHEMA,
    workspace_symbols,
    workspace_symbols_fingerprint,
)
from tooling.vscode_references_rename import (
    CANONICAL_VSCODE_REFERENCES_RENAME_SHA256,
    audit_vscode_references_rename,
)
from tooling.vscode_workspace_symbols import (
    CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256,
    P10_T4_VSCODE_WORKSPACE_SYMBOLS_VERSION,
    VSCODE_WORKSPACE_SYMBOLS_KIND,
    VSCODE_WORKSPACE_SYMBOLS_SCHEMA,
    audit_vscode_workspace_symbols,
    audit_vscode_workspace_symbols_vsix,
    workspace_symbols_fingerprint as vscode_fingerprint,
)


EXPECTED_SERVER = "b163f9c607f9c592d3e1371788f99fc0ebaa1f271bc6e17ae183149de82ccf85"
EXPECTED_VSCODE = "ddf809a166f95fed8215a2a6cbcf11f0f318199d5dfb8f719fa09ec49e60c9aa"
EXPECTED_T48 = "8dcb0b5ca57e2a8a507d16513fcb75d96e7f15d72db3d768afdcb8161d7d6119"

ALPHA = """function Alpha(value : int) : int {
    return value
}
"""
COUNTER = """module demo.counter

directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            emit changed
        }
    }
}
"""
COUNTER_OVERLAY = COUNTER.replace("state count", "state total").replace("add count", "add total")
AUTHORITY = """authority Operator {
    capability Execute
}
"""
ROLE = """role Maintainer {
    authority Operator
}
"""
PRINCIPAL = """principal DeMarcus {
    role Maintainer
}
"""
INVALID = "function Broken(value : int) : int { return }\n"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def request(message_id: int, method: str, params: object = None) -> dict[str, object]:
    value: dict[str, object] = {"jsonrpc": "2.0", "id": message_id, "method": method}
    if params is not None:
        value["params"] = params
    return value


def notification(method: str, params: object = None) -> dict[str, object]:
    value: dict[str, object] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        value["params"] = params
    return value


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


def initialize_params(root_uri: object, *, enabled: bool = True) -> dict[str, object]:
    capabilities: dict[str, object] = {}
    if enabled:
        capabilities["workspace"] = {
            "symbol": {
                "dynamicRegistration": False,
                "symbolKind": {"valueSet": list(range(1, 27))},
            }
        }
    return {
        "processId": None,
        "rootUri": root_uri,
        "capabilities": capabilities,
    }


def symbol_names(values: object) -> list[str]:
    require(type(values) in (list, tuple), "expected symbol sequence")
    return [str(item["name"]) for item in values if type(item) is dict]


def node_harness(client_path: Path, server_path: Path, repository_root: Path, workspace_root: Path) -> str:
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
        rootUri: __WORKSPACE_URI__,
        capabilities: {workspace: {symbol: {dynamicRegistration: false}}},
    });
    assert.strictEqual(initialized.capabilities.workspaceSymbolProvider, true);
    const alpha = await client.sendRequest('workspace/symbol', {query: 'Alpha'});
    assert.strictEqual(alpha.length, 1);
    assert.strictEqual(alpha[0].name, 'Alpha');
    assert.strictEqual(alpha[0].kind, 12);
    const counter = await client.sendRequest('workspace/symbol', {query: 'Counter changed'});
    assert.strictEqual(counter.length, 1);
    assert.strictEqual(counter[0].name, 'changed');
    await client.stop();
    process.stdout.write('node-workspace-symbol-lifecycle: PASS\n');
})().catch((error) => { console.error(error && error.stack ? error.stack : error); process.exitCode = 1; });
"""
    return (
        template.replace("__CLIENT_PATH__", json.dumps(str(client_path)))
        .replace("__PYTHON_COMMAND__", json.dumps(sys.executable))
        .replace("__SERVER_PATH__", json.dumps(str(server_path)))
        .replace("__REPOSITORY_ROOT__", json.dumps(str(repository_root)))
        .replace("__WORKSPACE_URI__", json.dumps(workspace_root.as_uri()))
    )


def main() -> None:
    require(P10_T4_WORKSPACE_SYMBOL_VERSION == "10-T4.9", "server version changed")
    require(WORKSPACE_SYMBOL_SCHEMA == 1, "server schema changed")
    require(WORKSPACE_SYMBOL_KIND == "apexforge.language-server-workspace-symbols", "server kind changed")
    require(WORKSPACE_SYMBOL_METHOD == "workspace/symbol", "server method changed")
    require(MAX_WORKSPACE_FILES == 4096, "workspace file limit changed")
    require(MAX_SYMBOL_RESULTS == 256, "workspace result limit changed")
    require(workspace_symbols_fingerprint() == EXPECTED_SERVER, "server fingerprint changed")
    require(CANONICAL_WORKSPACE_SYMBOLS_SHA256 == EXPECTED_SERVER, "server constant changed")

    base = server_capabilities()
    require("workspaceSymbolProvider" not in base, "frozen T4.1 capabilities changed")
    active = active_server_capabilities(workspace_symbols_enabled=True)
    require(active["workspaceSymbolProvider"] is True, "workspace capability omitted")

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        nested = root / "nested"
        nested.mkdir()
        (root / "alpha.apex").write_text(ALPHA, encoding="utf-8")
        counter_path = nested / "counter.apex"
        counter_path.write_text(COUNTER, encoding="utf-8")
        (root / "authority.apex").write_text(AUTHORITY, encoding="utf-8")
        (root / "role.apex").write_text(ROLE, encoding="utf-8")
        (root / "principal.apex").write_text(PRINCIPAL, encoding="utf-8")
        (root / "broken.apex").write_text(INVALID, encoding="utf-8")
        ignored = root / "dist"
        ignored.mkdir()
        (ignored / "hidden.apex").write_text(
            "function Hidden(value : int) : int {\n    return value\n}\n",
            encoding="utf-8",
        )

        all_symbols = workspace_symbols(root.as_uri(), "")
        names = symbol_names(all_symbols)
        for expected in (
            "Alpha", "demo.counter", "Counter", "count", "changed", "run",
            "primary", "Operator", "Execute", "Maintainer", "DeMarcus",
        ):
            require(expected in names, f"workspace omitted {expected!r}")
        require("Hidden" not in names, "ignored directory was indexed")
        require("Broken" not in names, "invalid source produced a symbol")
        require("value" not in names, "function parameter polluted workspace search")
        require(names.index("Alpha") < names.index("changed"), "empty-query ordering changed")

        exact = workspace_symbols(root.as_uri(), "Alpha")
        require(symbol_names(exact) == ["Alpha"], "exact query changed")
        prefix = workspace_symbols(root.as_uri(), "Counte")
        require(symbol_names(prefix)[0] == "Counter", "prefix ranking changed")
        container = workspace_symbols(root.as_uri(), "Counter changed")
        require(symbol_names(container) == ["changed"], "container token matching changed")
        authority = workspace_symbols(root.as_uri(), "Operator")
        require("Operator" in symbol_names(authority), "authority declaration missing")
        require(
            symbol_names(authority).count("Operator") == 1,
            "authority references leaked into workspace symbols",
        )

        overlay = {counter_path.as_uri(): COUNTER_OVERLAY}
        require(symbol_names(workspace_symbols(root.as_uri(), "total", overlay)) == ["total"], "open overlay omitted")
        require("count" not in symbol_names(workspace_symbols(root.as_uri(), "count", overlay)), "disk text overrode open document")
        require(workspace_symbols(root.as_uri(), "Hidden", {str(root): ALPHA}) == (), "malformed overlay key changed scan")

        disabled = LanguageServerSession()
        response = disabled.process(request(1, "initialize", initialize_params(root.as_uri(), enabled=False)))
        require(type(response) is dict, "disabled initialize failed")
        blocked = disabled.process(request(2, WORKSPACE_SYMBOL_METHOD, {"query": "Alpha"}))
        require(error_code(blocked) == METHOD_NOT_FOUND, "unnegotiated workspace symbols passed")

        session = LanguageServerSession()
        response = session.process(request(1, "initialize", initialize_params(root.as_uri())))
        require(type(response) is dict, "initialize failed")
        result = response["result"]
        require(type(result) is dict, "initialize result changed")
        capabilities = result["capabilities"]
        require(type(capabilities) is dict and capabilities.get("workspaceSymbolProvider") is True, "server did not advertise workspace symbols")
        query_response = session.process(request(2, WORKSPACE_SYMBOL_METHOD, {"query": "Alpha"}))
        require(type(query_response) is dict and symbol_names(query_response["result"]) == ["Alpha"], "server query changed")

        overlay_uri = counter_path.as_uri()
        session.process(notification("textDocument/didOpen", {"textDocument": {"uri": overlay_uri, "languageId": "apexforge", "version": 1, "text": COUNTER_OVERLAY}}))
        overlay_response = session.process(request(3, WORKSPACE_SYMBOL_METHOD, {"query": "total"}))
        require(type(overlay_response) is dict and symbol_names(overlay_response["result"]) == ["total"], "session overlay changed")
        bad_query = session.process(request(4, WORKSPACE_SYMBOL_METHOD, {"query": 7}))
        require(error_code(bad_query) == INVALID_PARAMS, "non-string query passed")

        no_root = LanguageServerSession()
        no_root.process(request(1, "initialize", initialize_params(None)))
        missing_root = no_root.process(request(2, WORKSPACE_SYMBOL_METHOD, {"query": "Alpha"}))
        require(error_code(missing_root) == INVALID_PARAMS, "missing root URI passed")

        input_stream = BytesIO(
            b"".join(
                (
                    encode_message(request(1, "initialize", initialize_params(root.as_uri()))),
                    encode_message(request(2, WORKSPACE_SYMBOL_METHOD, {"query": "Alpha"})),
                    encode_message(request(3, "shutdown")),
                    encode_message(notification("exit")),
                )
            )
        )
        output_stream = BytesIO()
        error_stream = StringIO()
        code = run_language_server(input_stream, output_stream, error_stream=error_stream)
        require(code == EXIT_SUCCESS, "stdio lifecycle failed")
        require(error_stream.getvalue() == "", "stdio lifecycle wrote stderr")
        framed = decode_all(output_stream.getvalue())
        require(len(framed) == 3, "stdio response count changed")
        require(symbol_names(framed[1]["result"]) == ["Alpha"], "stdio workspace result changed")

        stdout = StringIO()
        stderr = StringIO()
        code = server_main(("--workspace-symbols-contract",), stdout=stdout, stderr=stderr)
        require(code == EXIT_SUCCESS, "workspace contract CLI failed")
        require(stdout.getvalue() == EXPECTED_SERVER + "\n", "workspace contract CLI output changed")
        require(stderr.getvalue() == "", "workspace contract CLI wrote stderr")

        repository_root = Path(__file__).resolve().parent
        extension_root = repository_root.parent / "editors" / "vscode-apexforge"
        previous = audit_vscode_references_rename(extension_root)
        require(previous.references_rename_sha256 == EXPECTED_T48, "T4.8 compatibility changed")
        require(CANONICAL_VSCODE_REFERENCES_RENAME_SHA256 == EXPECTED_T48, "T4.8 constant changed")
        audit = audit_vscode_workspace_symbols(extension_root)
        require(audit.workspace_symbols_sha256 == EXPECTED_VSCODE, "VS Code audit changed")
        require(P10_T4_VSCODE_WORKSPACE_SYMBOLS_VERSION == "10-T4.9", "VS Code version changed")
        require(VSCODE_WORKSPACE_SYMBOLS_SCHEMA == 1, "VS Code schema changed")
        require(VSCODE_WORKSPACE_SYMBOLS_KIND == "apexforge.vscode-workspace-symbols", "VS Code kind changed")
        runtime_hashes = {
            "extension.js": __import__("hashlib").sha256((extension_root / "extension.js").read_bytes()).hexdigest(),
            "runtime/lsp-client.js": __import__("hashlib").sha256((extension_root / "runtime" / "lsp-client.js").read_bytes()).hexdigest(),
            "LANGUAGE_SERVER.md": __import__("hashlib").sha256((extension_root / "LANGUAGE_SERVER.md").read_bytes()).hexdigest(),
        }
        require(vscode_fingerprint(runtime_hashes) == EXPECTED_VSCODE, "VS Code projection changed")
        require(CANONICAL_VSCODE_WORKSPACE_SYMBOLS_SHA256 == EXPECTED_VSCODE, "VS Code constant changed")

        vsix_path = root / "t49-runtime-test.vsix"
        with ZipFile(vsix_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(extension_root / "extension.js", "extension/extension.js")
            archive.write(extension_root / "runtime" / "lsp-client.js", "extension/runtime/lsp-client.js")
            archive.write(extension_root / "LANGUAGE_SERVER.md", "extension/LANGUAGE_SERVER.md")
        vsix = audit_vscode_workspace_symbols_vsix(extension_root, vsix_path)
        require(vsix.workspace_symbols_sha256 == EXPECTED_VSCODE, "VSIX audit fingerprint changed")

        client_path = extension_root / "runtime" / "lsp-client.js"
        server_path = repository_root / "apexforge_lsp.py"
        script = node_harness(client_path, server_path, repository_root, root)
        completed = subprocess.run(
            ("node", "-e", script),
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, "Node lifecycle failed: " + (completed.stderr or completed.stdout))
        require("node-workspace-symbol-lifecycle: PASS" in completed.stdout, "Node lifecycle output changed")

    print("AFP-P10-T4.9 Workspace Symbols: PASS")
    print("Multi-file declaration indexing: PASS")
    print("Query ranking and container filtering: PASS")
    print("Ignored-directory and invalid-source containment: PASS")
    print("Open-document overlay semantics: PASS")
    print("LSP capability, request, and stdio lifecycle: PASS")
    print("VS Code provider, VSIX, and Node lifecycle: PASS")
    print("Frozen T4.8 references/rename compatibility: PASS")
    print("Deterministic T4.9 fingerprints: PASS")


if __name__ == "__main__":
    main()
