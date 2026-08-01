"""AFP-P10-T4.2 live syntax diagnostics and document-analysis smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
import subprocess
import sys

from language_server.diagnostics import (
    CANONICAL_LSP_DIAGNOSTICS_SHA256,
    LSP_DIAGNOSTICS_KIND,
    LSP_DIAGNOSTICS_SCHEMA,
    LSP_DIAGNOSTIC_ERROR,
    LSP_DIAGNOSTIC_SOURCE,
    P10_T4_LSP_DIAGNOSTICS_VERSION,
    PUBLISH_DIAGNOSTICS_METHOD,
    analyze_document,
    diagnostics_fingerprint,
    offset_to_lsp_position,
)
from language_server.protocol import encode_message, read_message
from language_server.server import (
    CANONICAL_LSP_FOUNDATION_SHA256,
    EXIT_SUCCESS,
    LanguageServerSession,
    foundation_fingerprint,
    main as server_main,
    run_language_server,
)


EXPECTED_FOUNDATION_SHA256 = (
    "3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d"
)
EXPECTED_DIAGNOSTICS_SHA256 = (
    "7b3ddf129201c64ecc839af197cec945c09388112a8cf080977d43aec9f66a5f"
)

VALID_SOURCE = "function Good() : int { return 1 }\n"
LEX_FAILURE = 'function Bad() : string { return "😀" # }\n'
PARSE_FAILURE = "directive Broken {\n    state count =\n}\n"
MODULE_FAILURE = """module app.main
import app.shared
import app.shared

function Good() : int { return 1 }
"""
URI = "file:///C:/ApexForgeDemo/main.apex"


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


def initialize_params(*, diagnostics: bool) -> dict:
    capabilities = {}
    if diagnostics:
        capabilities = {
            "textDocument": {
                "publishDiagnostics": {
                    "relatedInformation": True,
                    "versionSupport": True,
                }
            }
        }
    return {
        "processId": None,
        "clientInfo": {"name": "ApexForgeDiagnosticsSmoke", "version": "1.0"},
        "rootUri": "file:///C:/ApexForgeDemo",
        "capabilities": capabilities,
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


def did_change(text: str, *, version: int) -> dict:
    return notification(
        "textDocument/didChange",
        {
            "textDocument": {"uri": URI, "version": version},
            "contentChanges": [{"text": text}],
        },
    )


def did_close() -> dict:
    return notification(
        "textDocument/didClose",
        {"textDocument": {"uri": URI}},
    )


def publish_params(message: object) -> dict:
    require(type(message) is dict, "publishDiagnostics message must be an object")
    require(message.get("method") == PUBLISH_DIAGNOSTICS_METHOD, "wrong method")
    params = message.get("params")
    require(type(params) is dict, "publishDiagnostics params must be an object")
    return params


def decode_all(data: bytes) -> tuple[dict, ...]:
    stream = BytesIO(data)
    values = []
    while stream.tell() < len(data):
        value = read_message(stream)
        require(type(value) is dict, "framed output must be an object")
        values.append(dict(value))
    return tuple(values)


def main() -> None:
    require(P10_T4_LSP_DIAGNOSTICS_VERSION == "10-T4.2", "version changed")
    require(LSP_DIAGNOSTICS_SCHEMA == 1, "schema changed")
    require(
        LSP_DIAGNOSTICS_KIND == "apexforge.language-server-diagnostics",
        "kind changed",
    )
    require(LSP_DIAGNOSTIC_SOURCE == "apexforge", "diagnostic source changed")
    require(LSP_DIAGNOSTIC_ERROR == 1, "error severity changed")
    require(
        foundation_fingerprint() == EXPECTED_FOUNDATION_SHA256,
        "T4.1 foundation fingerprint changed",
    )
    require(
        CANONICAL_LSP_FOUNDATION_SHA256 == EXPECTED_FOUNDATION_SHA256,
        "declared T4.1 fingerprint changed",
    )
    require(
        diagnostics_fingerprint() == EXPECTED_DIAGNOSTICS_SHA256,
        "T4.2 diagnostics fingerprint is not deterministic",
    )
    require(
        CANONICAL_LSP_DIAGNOSTICS_SHA256 == EXPECTED_DIAGNOSTICS_SHA256,
        "declared T4.2 fingerprint changed",
    )

    require(analyze_document(URI, VALID_SOURCE) == (), "valid source diagnosed")

    lex_diagnostics = analyze_document(URI, LEX_FAILURE)
    require(len(lex_diagnostics) == 1, "lex failure did not yield one diagnostic")
    lex_diagnostic = lex_diagnostics[0]
    require(lex_diagnostic.get("code") == "APX-LEX-001", "wrong lex code")
    require(lex_diagnostic.get("severity") == 1, "wrong lex severity")
    require(lex_diagnostic.get("source") == "apexforge", "wrong source label")
    hash_offset = LEX_FAILURE.index("#")
    expected_position = offset_to_lsp_position(LEX_FAILURE, hash_offset)
    require(
        lex_diagnostic["range"]["start"] == expected_position,
        "UTF-16 diagnostic position changed",
    )
    require(
        expected_position["character"] > hash_offset,
        "supplementary Unicode did not consume two UTF-16 code units",
    )

    parse_diagnostics = analyze_document(URI, PARSE_FAILURE)
    require(len(parse_diagnostics) == 1, "parse failure count changed")
    require(
        parse_diagnostics[0].get("code") == "APX-PARSE-004",
        "wrong parse code",
    )
    require(
        parse_diagnostics[0]["data"] == {"stage": "parse"},
        "parse stage metadata changed",
    )

    module_diagnostics = analyze_document(
        URI,
        MODULE_FAILURE,
        include_related_information=True,
    )
    require(len(module_diagnostics) == 1, "module failure count changed")
    require(
        module_diagnostics[0].get("code") == "APX-MODULE-004",
        "wrong module code",
    )
    related = module_diagnostics[0].get("relatedInformation")
    require(type(related) is list and len(related) == 1, "related span was lost")
    require(
        related[0]["location"]["uri"] == URI,
        "related information used the wrong URI",
    )

    legacy = LanguageServerSession()
    legacy.process(request(1, "initialize", initialize_params(diagnostics=False)))
    legacy.process(notification("initialized", {}))
    legacy.process(did_open(VALID_SOURCE))
    require(
        legacy.drain_outgoing_notifications() == (),
        "T4.1 clients unexpectedly received diagnostics",
    )

    session = LanguageServerSession()
    session.process(request(2, "initialize", initialize_params(diagnostics=True)))
    session.process(notification("initialized", {}))
    require(session.diagnostics_enabled, "diagnostics capability was not activated")
    require(session.diagnostics_related_information, "related-information support lost")
    require(session.diagnostics_version_support, "version support lost")

    session.process(did_open(LEX_FAILURE, version=1))
    outgoing = session.drain_outgoing_notifications()
    require(len(outgoing) == 1, "didOpen did not publish diagnostics")
    opened = publish_params(outgoing[0])
    require(opened.get("uri") == URI, "didOpen publish used the wrong URI")
    require(opened.get("version") == 1, "didOpen publish lost version")
    require(len(opened.get("diagnostics", [])) == 1, "didOpen diagnostic missing")

    session.process(did_change(VALID_SOURCE, version=2))
    outgoing = session.drain_outgoing_notifications()
    require(len(outgoing) == 1, "didChange did not publish diagnostics")
    changed = publish_params(outgoing[0])
    require(changed.get("version") == 2, "didChange publish lost version")
    require(changed.get("diagnostics") == [], "fixed source did not clear diagnostics")

    session.process(did_close())
    outgoing = session.drain_outgoing_notifications()
    require(len(outgoing) == 1, "didClose did not clear diagnostics")
    closed = publish_params(outgoing[0])
    require(closed.get("diagnostics") == [], "didClose clear was not empty")
    require("version" not in closed, "didClose clear retained a document version")

    transcript_messages = (
        request(11, "initialize", initialize_params(diagnostics=True)),
        notification("initialized", {}),
        did_open(LEX_FAILURE, version=1),
        did_change(VALID_SOURCE, version=2),
        did_close(),
        request(12, "shutdown"),
        notification("exit"),
    )
    transcript = b"".join(encode_message(item) for item in transcript_messages)
    output = BytesIO()
    errors = StringIO()
    exit_code = run_language_server(BytesIO(transcript), output, error_stream=errors)
    require(exit_code == EXIT_SUCCESS, "diagnostics transcript did not exit cleanly")
    require(errors.getvalue() == "", "diagnostics transcript wrote stderr")
    messages = decode_all(output.getvalue())
    require(len(messages) == 5, "diagnostics transcript output count changed")
    require(messages[0].get("id") == 11, "initialize response order changed")
    require(messages[1].get("method") == PUBLISH_DIAGNOSTICS_METHOD, "open publish missing")
    require(messages[2].get("method") == PUBLISH_DIAGNOSTICS_METHOD, "change publish missing")
    require(messages[3].get("method") == PUBLISH_DIAGNOSTICS_METHOD, "close publish missing")
    require(messages[4].get("id") == 12, "shutdown response order changed")

    contract_out = StringIO()
    contract_err = StringIO()
    contract_code = server_main(
        ("--diagnostics-contract",),
        stdout=contract_out,
        stderr=contract_err,
    )
    require(contract_code == 0, "--diagnostics-contract returned failure")
    require(
        contract_out.getvalue() == EXPECTED_DIAGNOSTICS_SHA256 + "\n",
        "--diagnostics-contract output changed",
    )
    require(contract_err.getvalue() == "", "--diagnostics-contract wrote stderr")

    package_dir = Path(__file__).resolve().parent
    wrapper = package_dir / "apexforge_lsp.py"
    completed = subprocess.run(
        [sys.executable, str(wrapper), "--diagnostics-contract"],
        cwd=str(package_dir.parent),
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, "repository LSP wrapper returned failure")
    require(
        completed.stdout == EXPECTED_DIAGNOSTICS_SHA256 + "\n",
        "repository LSP diagnostics contract changed",
    )
    require(completed.stderr == "", "repository LSP wrapper wrote stderr")

    print("AFP-P10-T4.2 live syntax diagnostics smoke test passed.")
    print("Module, lexer, and parser analysis pipeline: PASS")
    print("UTF-16 source-range conversion: PASS")
    print("Versioned didOpen/didChange diagnostics: PASS")
    print("didClose diagnostic clearing: PASS")
    print("Client capability activation: PASS")
    print("Related diagnostic information: PASS")
    print("Deterministic diagnostics fingerprint: PASS")
    print("Frozen T4.1 compatibility: PASS")


if __name__ == "__main__":
    main()
