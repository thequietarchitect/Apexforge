"""AFP-P10-T4.8 same-document references and safe rename smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
import json
from pathlib import Path
from shutil import which
import subprocess
import sys

from language_server.definition import CANONICAL_DEFINITION_SHA256
from language_server.protocol import INVALID_PARAMS, METHOD_NOT_FOUND, encode_message, read_message
from language_server.references import (
    CANONICAL_REFERENCES_SHA256,
    P10_T4_REFERENCES_VERSION,
    REFERENCES_KIND,
    REFERENCES_METHOD,
    REFERENCES_SCHEMA,
    references,
    references_fingerprint,
)
from language_server.rename import (
    CANONICAL_RENAME_SHA256,
    P10_T4_RENAME_VERSION,
    PREPARE_RENAME_METHOD,
    RENAME_KIND,
    RENAME_METHOD,
    RENAME_SCHEMA,
    prepare_rename,
    rename,
    rename_fingerprint,
)
from language_server.server import (
    EXIT_SUCCESS,
    LanguageServerSession,
    active_server_capabilities,
    main as server_main,
    run_language_server,
    server_capabilities,
)
from tooling.vscode_definition import (
    CANONICAL_VSCODE_DEFINITION_SHA256,
    audit_vscode_definition,
)
from tooling.vscode_references_rename import (
    CANONICAL_VSCODE_REFERENCES_RENAME_SHA256,
    P10_T4_VSCODE_REFERENCES_RENAME_VERSION,
    VSCODE_REFERENCES_RENAME_KIND,
    VSCODE_REFERENCES_RENAME_SCHEMA,
    audit_vscode_references_rename,
    references_rename_fingerprint as vscode_fingerprint,
)

EXPECTED_REFERENCES = "183f9e12a4907b3a00911d5ef693934a187d1a4478995f0ccd19080cd2bc4c30"
EXPECTED_RENAME = "ab631c77123a367b6feb2713e3afa250ab9c7817aef3761a9f905dfdfccdc510"
EXPECTED_VSCODE = "8dcb0b5ca57e2a8a507d16513fcb75d96e7f15d72db3d768afdcb8161d7d6119"
EXPECTED_T47 = "939e9649c7c44d7b5a7cce0ac9eaa7ab900b12a49df1b7dab7d55500b8996e1a"
URI = "file:///C:/ApexForgeReferences/main.apex"

SOURCE = """directive Counter {
    state count : int = 0
    event changed
    cause run {
        path primary @ 10 {
            add count 1
            set count = count + 1
            emit changed
            message "😀" + count
            when count > 0 {
                emit changed
            }
        }
    }
}
"""
FUNCTION = """function Identity<T : numeric>(value : T) : T {
    let copy = value
    when copy > 0 {
        return Identity<T>(copy)
    } otherwise {
        return value
    }
}
"""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def lsp_position(text: str, offset: int) -> dict[str, int]:
    line = text.count("\n", 0, offset)
    line_start = text.rfind("\n", 0, offset) + 1
    return {
        "line": line,
        "character": len(text[line_start:offset].encode("utf-16-le")) // 2,
    }


def occurrence_offset(text: str, needle: str, occurrence: int = 1) -> int:
    start = -1
    for _ in range(occurrence):
        start = text.find(needle, start + 1)
        require(start >= 0, f"missing occurrence {occurrence} of {needle!r}")
    return start


def position_at(text: str, needle: str, occurrence: int = 1) -> dict[str, int]:
    return lsp_position(text, occurrence_offset(text, needle, occurrence))


def location_at(text: str, needle: str, occurrence: int = 1) -> dict[str, object]:
    start = occurrence_offset(text, needle, occurrence)
    return {
        "uri": URI,
        "range": {
            "start": lsp_position(text, start),
            "end": lsp_position(text, start + len(needle)),
        },
    }


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


def initialize_params(enabled: bool = True) -> dict[str, object]:
    text_document: dict[str, object] = {}
    if enabled:
        text_document = {
            "references": {},
            "rename": {"prepareSupport": True},
        }
    return {
        "processId": None,
        "rootUri": "file:///C:/ApexForgeReferences",
        "capabilities": {"textDocument": text_document},
    }


def did_open(text: str) -> dict[str, object]:
    return notification(
        "textDocument/didOpen",
        {"textDocument": {"uri": URI, "languageId": "apexforge", "version": 1, "text": text}},
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
        rootUri: 'file:///ApexForgeReferences',
        capabilities: {textDocument: {references: {}, rename: {prepareSupport: true}}},
    });
    assert.strictEqual(initialized.capabilities.referencesProvider, true);
    assert.deepStrictEqual(initialized.capabilities.renameProvider, {prepareProvider: true});
    const uri = 'file:///ApexForgeReferences/main.apex';
    const text = 'directive Counter {\n state count : int = 0\n cause run {\n  path p @ 10 {\n   add count 1\n  }\n }\n}\n';
    client.sendNotification('textDocument/didOpen', {textDocument: {uri, languageId: 'apexforge', version: 1, text}});
    const refs = await client.sendRequest('textDocument/references', {textDocument: {uri}, position: {line: 4, character: 7}, context: {includeDeclaration: true}});
    assert.strictEqual(refs.length, 2);
    const prepared = await client.sendRequest('textDocument/prepareRename', {textDocument: {uri}, position: {line: 4, character: 7}});
    assert.strictEqual(prepared.placeholder, 'count');
    const edit = await client.sendRequest('textDocument/rename', {textDocument: {uri}, position: {line: 4, character: 7}, newName: 'total'});
    assert.strictEqual(edit.changes[uri].length, 2);
    await client.stop();
    process.stdout.write('node-references-rename-lifecycle: PASS\n');
})().catch((error) => { console.error(error && error.stack ? error.stack : error); process.exitCode = 1; });
"""
    return (
        template.replace("__CLIENT_PATH__", json.dumps(str(client_path)))
        .replace("__PYTHON_COMMAND__", json.dumps(sys.executable))
        .replace("__SERVER_PATH__", json.dumps(str(server_path)))
        .replace("__REPOSITORY_ROOT__", json.dumps(str(repository_root)))
    )


def main() -> None:
    require(P10_T4_REFERENCES_VERSION == "10-T4.8", "references version changed")
    require(REFERENCES_SCHEMA == 1, "references schema changed")
    require(REFERENCES_KIND == "apexforge.language-server-references", "references kind changed")
    require(references_fingerprint() == EXPECTED_REFERENCES, "references fingerprint changed")
    require(CANONICAL_REFERENCES_SHA256 == EXPECTED_REFERENCES, "references constant changed")
    require(P10_T4_RENAME_VERSION == "10-T4.8", "rename version changed")
    require(RENAME_SCHEMA == 1, "rename schema changed")
    require(RENAME_KIND == "apexforge.language-server-rename", "rename kind changed")
    require(rename_fingerprint() == EXPECTED_RENAME, "rename fingerprint changed")
    require(CANONICAL_RENAME_SHA256 == EXPECTED_RENAME, "rename constant changed")

    count_position = position_at(SOURCE, "count", 2)
    with_declaration = references(URI, SOURCE, count_position, {"includeDeclaration": True})
    without_declaration = references(URI, SOURCE, count_position, {"includeDeclaration": False})
    require(len(with_declaration) == 6, "state reference count changed")
    require(len(without_declaration) == 5, "declaration exclusion changed")
    require(with_declaration[0] == location_at(SOURCE, "count", 1), "declaration range changed")
    require(with_declaration[-1] == location_at(SOURCE, "count", 6), "UTF-16 occurrence range changed")

    event_refs = references(URI, SOURCE, position_at(SOURCE, "changed", 2), {"includeDeclaration": True})
    require(len(event_refs) == 3, "event reference count changed")
    local_refs = references(URI, FUNCTION, position_at(FUNCTION, "copy", 2), {"includeDeclaration": True})
    require(len(local_refs) == 3, "local reference count changed")
    callable_refs = references(URI, FUNCTION, position_at(FUNCTION, "Identity", 2), {"includeDeclaration": True})
    require(len(callable_refs) == 2, "recursive callable references changed")
    require(references(URI, "directive Broken {", {"line": 0, "character": 10}, {"includeDeclaration": True}) == (), "invalid source returned references")

    prepared = prepare_rename(URI, SOURCE, count_position)
    require(prepared is not None and prepared["placeholder"] == "count", "prepareRename changed")
    edit = rename(URI, SOURCE, count_position, "total")
    require(edit is not None and len(edit["changes"][URI]) == 6, "rename edit count changed")
    require(prepare_rename(URI, FUNCTION, position_at(FUNCTION, "Identity", 1)) is None, "workspace-visible callable became renameable")
    require(rename(URI, FUNCTION, position_at(FUNCTION, "Identity", 1), "Other") is None, "protected callable rename produced edits")
    for bad in ("", "9count", "count-value", "state", "int"):
        try:
            rename(URI, SOURCE, count_position, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe rename {bad!r} unexpectedly passed")

    collision_source = """function Example<T : numeric>(left : T, right : T) : T {
    let copy = left
    return right
}
"""
    try:
        rename(URI, collision_source, position_at(collision_source, "left", 1), "right")
    except ValueError:
        pass
    else:
        raise AssertionError("same-namespace collision unexpectedly passed")

    foundation = server_capabilities()
    require("referencesProvider" not in foundation and "renameProvider" not in foundation, "T4.1 foundation changed")
    active = active_server_capabilities(references_enabled=True, rename_enabled=True)
    require(active["referencesProvider"] is True, "active references capability missing")
    require(active["renameProvider"] == {"prepareProvider": True}, "active rename capability missing")

    disabled = LanguageServerSession()
    disabled.process(request(1, "initialize", initialize_params(False)))
    disabled.process(did_open(SOURCE))
    response = disabled.process(request(2, REFERENCES_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "context": {"includeDeclaration": True}}))
    require(error_code(response) == METHOD_NOT_FOUND, "references ran without negotiation")

    session = LanguageServerSession()
    initialized = session.process(request(1, "initialize", initialize_params(True)))
    require(initialized["result"]["capabilities"]["referencesProvider"] is True, "initialize omitted references")
    require(initialized["result"]["capabilities"]["renameProvider"] == {"prepareProvider": True}, "initialize omitted rename")
    session.process(did_open(SOURCE))
    refs_response = session.process(request(2, REFERENCES_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "context": {"includeDeclaration": True}}))
    require(len(refs_response["result"]) == 6, "JSON-RPC references changed")
    prepare_response = session.process(request(3, PREPARE_RENAME_METHOD, {"textDocument": {"uri": URI}, "position": count_position}))
    require(prepare_response["result"]["placeholder"] == "count", "JSON-RPC prepareRename changed")
    rename_response = session.process(request(4, RENAME_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "newName": "total"}))
    require(len(rename_response["result"]["changes"][URI]) == 6, "JSON-RPC rename changed")
    bad_context = session.process(request(5, REFERENCES_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "context": {"includeDeclaration": "yes"}}))
    require(error_code(bad_context) == INVALID_PARAMS, "invalid reference context did not fail")
    bad_name = session.process(request(6, RENAME_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "newName": "state"}))
    require(error_code(bad_name) == INVALID_PARAMS, "invalid rename did not fail")

    for option, expected in (("--references-contract", EXPECTED_REFERENCES), ("--rename-contract", EXPECTED_RENAME)):
        stdout, stderr = StringIO(), StringIO()
        require(server_main((option,), stdout=stdout, stderr=stderr) == EXIT_SUCCESS, f"{option} failed")
        require(stdout.getvalue() == expected + "\n" and stderr.getvalue() == "", f"{option} output changed")

    payload = b"".join(encode_message(value) for value in (
        request(1, "initialize", initialize_params(True)),
        notification("initialized", {}),
        did_open(SOURCE),
        request(2, REFERENCES_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "context": {"includeDeclaration": False}}),
        request(3, RENAME_METHOD, {"textDocument": {"uri": URI}, "position": count_position, "newName": "total"}),
        request(4, "shutdown"),
        notification("exit"),
    ))
    output = BytesIO()
    require(run_language_server(BytesIO(payload), output, error_stream=StringIO()) == EXIT_SUCCESS, "stdio lifecycle failed")
    framed = decode_all(output.getvalue())
    require(len(framed[1]["result"]) == 5, "stdio references changed")
    require(len(framed[2]["result"]["changes"][URI]) == 6, "stdio rename changed")

    repository_root = Path(__file__).resolve().parent.parent
    extension_root = repository_root / "editors" / "vscode-apexforge"
    require(audit_vscode_definition(extension_root).definition_sha256 == EXPECTED_T47, "frozen T4.7 definition changed")
    audit = audit_vscode_references_rename(extension_root)
    require(audit.references_rename_sha256 == EXPECTED_VSCODE, "VS Code T4.8 audit changed")
    runtime_hashes = {
        name: __import__("hashlib").sha256((extension_root / name).read_bytes()).hexdigest()
        for name in ("extension.js", "runtime/lsp-client.js", "LANGUAGE_SERVER.md")
    }
    require(vscode_fingerprint(runtime_hashes) == EXPECTED_VSCODE, "VS Code projection not deterministic")
    require(CANONICAL_VSCODE_REFERENCES_RENAME_SHA256 == EXPECTED_VSCODE, "VS Code constant changed")
    require(CANONICAL_VSCODE_DEFINITION_SHA256 == EXPECTED_T47, "T4.7 constant changed")
    require(CANONICAL_DEFINITION_SHA256 == "6a8c78f39e5f265bc2f8c1c9b1085834570712f4607cf09ce95d6464b1b647cd", "server T4.7 constant changed")
    require(P10_T4_VSCODE_REFERENCES_RENAME_VERSION == "10-T4.8", "VS Code version changed")
    require(VSCODE_REFERENCES_RENAME_SCHEMA == 1, "VS Code schema changed")
    require(VSCODE_REFERENCES_RENAME_KIND == "apexforge.vscode-references-rename", "VS Code kind changed")

    node = which("node")
    if node:
        completed = subprocess.run(
            (node, "-e", node_harness(extension_root / "runtime" / "lsp-client.js", repository_root / "apexforge" / "apexforge_lsp.py", repository_root)),
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, "Node lifecycle failed: " + (completed.stderr or completed.stdout))
        require("node-references-rename-lifecycle: PASS" in completed.stdout, "Node lifecycle omitted PASS")

    print("AFP-P10-T4.8 same-document references and safe rename: PASS")
    print("Declaration filtering and exact occurrence identity: PASS")
    print("Rename validation and protected-symbol safety: PASS")
    print("JSON-RPC and VS Code references/rename integration: PASS")
    print("Deterministic T4.8 fingerprints: PASS")


if __name__ == "__main__":
    main()
