"""AFP-P10-T4.7 same-document definition navigation smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import which
import subprocess
import sys
from typing import Optional

from language_server.completion import CANONICAL_COMPLETION_SHA256
from language_server.definition import (
    CANONICAL_DEFINITION_SHA256,
    DEFINITION_KIND,
    DEFINITION_METHOD,
    DEFINITION_SCHEMA,
    P10_T4_DEFINITION_VERSION,
    definition,
    definition_fingerprint,
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
    audit_vscode_completion,
)
from tooling.vscode_definition import (
    CANONICAL_VSCODE_DEFINITION_SHA256,
    P10_T4_VSCODE_DEFINITION_VERSION,
    VSCODE_DEFINITION_KIND,
    VSCODE_DEFINITION_SCHEMA,
    audit_vscode_definition,
    definition_fingerprint as vscode_definition_fingerprint,
)
from tooling.vscode_document_symbols import CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256
from tooling.vscode_hover import CANONICAL_VSCODE_HOVER_SHA256
from tooling.vscode_lsp_activation import CANONICAL_VSCODE_LSP_ACTIVATION_SHA256


EXPECTED_SERVER_SHA256 = "6a8c78f39e5f265bc2f8c1c9b1085834570712f4607cf09ce95d6464b1b647cd"
EXPECTED_VSCODE_SHA256 = "939e9649c7c44d7b5a7cce0ac9eaa7ab900b12a49df1b7dab7d55500b8996e1a"
EXPECTED_T4_6_SHA256 = "a583db79bf020cad7c96d9696814e151cf26e471f61bb7097617747c0434127a"
EXPECTED_T4_5_SHA256 = "f8367f64fae736a53cb2c3faf855314aa4e4958d99728332cbab28fa2aa5db56"
EXPECTED_T4_4_SHA256 = "4e2dc7a669b47a2859925c5c1bfa2a6057b4964ad2642c1cbb1aaa79b0dc4bd8"
EXPECTED_T4_3_SHA256 = "b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6"

URI = "file:///C:/ApexForgeDefinition/main.apex"
FUNCTION_SOURCE = """function Identity<T : numeric>(value : T) : T {
    let copy = value
    when copy > 0 {
        return Identity<T>(copy)
    } otherwise {
        return value
    }
}
"""
DIRECTIVE_SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            set count = count + 1
            emit changed
            message \"😀\" + count
            when count > 0 {
                emit changed
            }
        }
    }
}
"""


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


def lsp_position(text: str, offset: int) -> dict[str, int]:
    line = text.count("\n", 0, offset)
    line_start = text.rfind("\n", 0, offset) + 1
    character = len(text[line_start:offset].encode("utf-16-le")) // 2
    return {"line": line, "character": character}


def occurrence_offset(text: str, needle: str, occurrence: int = 1) -> int:
    require(occurrence > 0, "occurrence must be positive")
    start = -1
    for _ in range(occurrence):
        start = text.find(needle, start + 1)
        require(start >= 0, f"missing occurrence {occurrence} of {needle!r}")
    return start


def definition_at(text: str, needle: str, occurrence: int = 1) -> Optional[dict[str, object]]:
    offset = occurrence_offset(text, needle, occurrence)
    return definition(URI, text, lsp_position(text, offset))


def expected_location(text: str, needle: str, occurrence: int = 1) -> dict[str, object]:
    offset = occurrence_offset(text, needle, occurrence)
    return {
        "uri": URI,
        "range": {
            "start": lsp_position(text, offset),
            "end": lsp_position(text, offset + len(needle)),
        },
    }


def initialize_params(*, definition_enabled: bool) -> dict:
    text_document = {}
    if definition_enabled:
        text_document["definition"] = {"linkSupport": False}
    return {
        "processId": None,
        "rootUri": "file:///C:/ApexForgeDefinition",
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


def definition_request(text: str, needle: str, occurrence: int = 1, *, message_id: int = 2) -> dict:
    offset = occurrence_offset(text, needle, occurrence)
    return request(
        message_id,
        DEFINITION_METHOD,
        {
            "textDocument": {"uri": URI},
            "position": lsp_position(text, offset),
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
        rootUri: 'file:///ApexForgeDefinition',
        capabilities: {
            textDocument: {
                definition: {linkSupport: false},
            },
        },
    });
    assert.strictEqual(initialized.capabilities.definitionProvider, true);
    const uri = 'file:///ApexForgeDefinition/main.apex';
    const text = 'directive Counter {\n state count : int = 0\n cause run {\n  path p @ 10 {\n   add count 1\n  }\n }\n}\n';
    client.sendNotification('textDocument/didOpen', {
        textDocument: {uri, languageId: 'apexforge', version: 1, text},
    });
    const result = await client.sendRequest('textDocument/definition', {
        textDocument: {uri},
        position: {line: 4, character: 7},
    });
    assert.strictEqual(result.uri, uri);
    assert.deepStrictEqual(result.range.start, {line: 1, character: 7});
    assert.deepStrictEqual(result.range.end, {line: 1, character: 12});
    await client.stop();
    process.stdout.write('node-definition-lifecycle: PASS\n');
})().catch((error) => {
    console.error(error && error.stack ? error.stack : error);
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
    require(P10_T4_DEFINITION_VERSION == "10-T4.7", "server definition version changed")
    require(DEFINITION_SCHEMA == 1, "server definition schema changed")
    require(DEFINITION_KIND == "apexforge.language-server-definition", "server definition kind changed")
    require(DEFINITION_METHOD == "textDocument/definition", "definition method changed")
    require(definition_fingerprint() == EXPECTED_SERVER_SHA256, "server definition fingerprint changed")
    require(CANONICAL_DEFINITION_SHA256 == EXPECTED_SERVER_SHA256, "declared server definition hash changed")

    require(P10_T4_VSCODE_DEFINITION_VERSION == "10-T4.7", "VS Code definition version changed")
    require(VSCODE_DEFINITION_SCHEMA == 1, "VS Code definition schema changed")
    require(VSCODE_DEFINITION_KIND == "apexforge.vscode-definition", "VS Code definition kind changed")

    require(definition_at(FUNCTION_SOURCE, "Identity", 1) == expected_location(FUNCTION_SOURCE, "Identity", 1), "function declaration did not define itself")
    require(definition_at(FUNCTION_SOURCE, "T", 2) == expected_location(FUNCTION_SOURCE, "T", 1), "parameter type did not resolve to type parameter")
    require(definition_at(FUNCTION_SOURCE, "T", 4) == expected_location(FUNCTION_SOURCE, "T", 1), "call type argument did not resolve to type parameter")
    require(definition_at(FUNCTION_SOURCE, "value", 2) == expected_location(FUNCTION_SOURCE, "value", 1), "let expression did not resolve to parameter")
    require(definition_at(FUNCTION_SOURCE, "copy", 2) == expected_location(FUNCTION_SOURCE, "copy", 1), "when expression did not resolve to local")
    require(definition_at(FUNCTION_SOURCE, "Identity", 2) == expected_location(FUNCTION_SOURCE, "Identity", 1), "recursive call did not resolve to function")
    require(definition_at(FUNCTION_SOURCE, "copy", 3) == expected_location(FUNCTION_SOURCE, "copy", 1), "call argument did not resolve to local")
    require(definition_at(FUNCTION_SOURCE, "return", 1) is None, "keyword unexpectedly resolved")

    require(definition_at(DIRECTIVE_SOURCE, "Counter", 1) == expected_location(DIRECTIVE_SOURCE, "Counter", 1), "directive declaration did not define itself")
    for occurrence in (2, 3, 4, 5, 6):
        require(definition_at(DIRECTIVE_SOURCE, "count", occurrence) == expected_location(DIRECTIVE_SOURCE, "count", 1), f"directive state occurrence {occurrence} did not resolve")
    require(definition_at(DIRECTIVE_SOURCE, "changed", 2) == expected_location(DIRECTIVE_SOURCE, "changed", 1), "emit target did not resolve to event")
    require(definition_at(DIRECTIVE_SOURCE, "changed", 3) == expected_location(DIRECTIVE_SOURCE, "changed", 1), "nested emit target did not resolve to event")

    workflow = "workflow Main {\n invoke Worker\n}\n"
    require(definition_at(workflow, "Main") == expected_location(workflow, "Main"), "workflow declaration did not define itself")
    require(definition_at(workflow, "Worker") is None, "cross-file invocation unexpectedly resolved")
    require(definition(URI, "directive Broken {", {"line": 0, "character": 10}) is None, "invalid source did not return null")
    require(definition(URI, DIRECTIVE_SOURCE, {"line": 0, "character": 0}) is None, "unmatched keyword did not return null")

    foundation = server_capabilities()
    require("definitionProvider" not in foundation, "frozen T4.1 foundation gained definition")
    active = active_server_capabilities(definition_enabled=True)
    require(active.get("definitionProvider") is True, "active capabilities omitted definition provider")

    disabled = LanguageServerSession()
    disabled.process(request(1, "initialize", initialize_params(definition_enabled=False)))
    disabled.process(did_open(DIRECTIVE_SOURCE))
    disabled_response = disabled.process(definition_request(DIRECTIVE_SOURCE, "count", 2))
    require(error_code(disabled_response) == METHOD_NOT_FOUND, "definition ran without negotiated capability")

    session = LanguageServerSession()
    initialize_response = session.process(request(1, "initialize", initialize_params(definition_enabled=True)))
    require(initialize_response["result"]["capabilities"]["definitionProvider"] is True, "initialize omitted definitionProvider")
    session.process(did_open(DIRECTIVE_SOURCE))
    response = session.process(definition_request(DIRECTIVE_SOURCE, "count", 2))
    require(response["result"] == expected_location(DIRECTIVE_SOURCE, "count", 1), "server definition response changed")
    unopened = session.process(request(3, DEFINITION_METHOD, {"textDocument": {"uri": "file:///missing.apex"}, "position": {"line": 0, "character": 0}}))
    require(error_code(unopened) == INVALID_PARAMS, "unopened document did not fail with invalid params")

    stdout = StringIO()
    stderr = StringIO()
    require(server_main(("--definition-contract",), stdout=stdout, stderr=stderr) == EXIT_SUCCESS, "definition contract CLI failed")
    require(stdout.getvalue() == EXPECTED_SERVER_SHA256 + "\n", "definition contract CLI output changed")
    require(stderr.getvalue() == "", "definition contract CLI wrote stderr")

    payload = b"".join(
        encode_message(value)
        for value in (
            request(1, "initialize", initialize_params(definition_enabled=True)),
            notification("initialized", {}),
            did_open(DIRECTIVE_SOURCE),
            definition_request(DIRECTIVE_SOURCE, "changed", 2, message_id=2),
            request(3, "shutdown"),
            notification("exit"),
        )
    )
    output = BytesIO()
    require(run_language_server(BytesIO(payload), output, error_stream=StringIO()) == EXIT_SUCCESS, "stdio definition lifecycle failed")
    framed = decode_all(output.getvalue())
    require(framed[1]["result"] == expected_location(DIRECTIVE_SOURCE, "changed", 1), "stdio definition result changed")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    completion_audit = audit_vscode_completion(extension_root)
    require(completion_audit.completion_sha256 == EXPECTED_T4_6_SHA256, "frozen T4.6 completion changed")
    audit = audit_vscode_definition(extension_root)
    require(audit.definition_sha256 == EXPECTED_VSCODE_SHA256, "VS Code definition audit hash changed")
    runtime_hashes = {
        name: __import__("hashlib").sha256((extension_root / name).read_bytes()).hexdigest()
        for name in ("extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
    }
    require(vscode_definition_fingerprint(runtime_hashes) == EXPECTED_VSCODE_SHA256, "VS Code definition projection is not deterministic")

    require(CANONICAL_VSCODE_DEFINITION_SHA256 == EXPECTED_VSCODE_SHA256, "declared VS Code definition hash changed")
    require(CANONICAL_VSCODE_COMPLETION_SHA256 == EXPECTED_T4_6_SHA256, "T4.6 completion constant changed")
    require(CANONICAL_COMPLETION_SHA256 == "8a6054d257a8b98c1a64584c7c8b9f9a5416a62769c11a500ab34afd333f21c5", "server completion constant changed")
    require(CANONICAL_VSCODE_HOVER_SHA256 == EXPECTED_T4_5_SHA256, "T4.5 hover constant changed")
    require(CANONICAL_VSCODE_DOCUMENT_SYMBOLS_SHA256 == EXPECTED_T4_4_SHA256, "T4.4 symbol constant changed")
    require(CANONICAL_VSCODE_LSP_ACTIVATION_SHA256 == EXPECTED_T4_3_SHA256, "T4.3 activation constant changed")

    node = which("node")
    if node:
        client_path = extension_root / "runtime" / "lsp-client.js"
        server_path = repository_root / "apexforge" / "apexforge_lsp.py"
        completed = subprocess.run(
            (node, "-e", node_harness(client_path, server_path, repository_root)),
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, "Node definition lifecycle failed: " + (completed.stderr or completed.stdout))
        require("node-definition-lifecycle: PASS" in completed.stdout, "Node lifecycle omitted PASS")

    print("AFP-P10-T4.7 same-document definition navigation: PASS")
    print("Function type/value resolution: PASS")
    print("Directive state/event/message resolution: PASS")
    print("JSON-RPC and VS Code definition integration: PASS")
    print("Deterministic T4.7 fingerprints: PASS")


if __name__ == "__main__":
    main()
