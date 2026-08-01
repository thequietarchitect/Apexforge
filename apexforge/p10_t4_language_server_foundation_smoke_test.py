"""AFP-P10-T4.1 language-server foundation smoke test."""

from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
import subprocess
import sys

from language_server.protocol import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    SERVER_NOT_INITIALIZED,
    LSPTransportError,
    decode_payload,
    encode_message,
    read_message,
    read_payload,
)
from language_server.server import (
    CANONICAL_LSP_FOUNDATION_SHA256,
    EXIT_SUCCESS,
    EXIT_TRANSPORT_ERROR,
    EXIT_UNCLEAN,
    LANGUAGE_ID,
    LSP_FOUNDATION_KIND,
    LSP_FOUNDATION_SCHEMA,
    LSP_SPECIFICATION_VERSION,
    P10_T4_LSP_FOUNDATION_VERSION,
    POSITION_ENCODING,
    SERVER_NAME,
    SERVER_VERSION,
    TEXT_DOCUMENT_SYNC_FULL,
    LanguageServerSession,
    foundation_fingerprint,
    main as server_main,
    run_language_server,
    server_capabilities,
)


EXPECTED_FOUNDATION_SHA256 = (
    "3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def request(message_id: object, method: str, params: object = None) -> dict:
    value = {
        "jsonrpc": "2.0",
        "id": message_id,
        "method": method,
    }
    if params is not None:
        value["params"] = params
    return value


def notification(method: str, params: object = None) -> dict:
    value = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if params is not None:
        value["params"] = params
    return value


def error_code(response: object) -> int:
    require(type(response) is dict, "expected JSON-RPC response object")
    error = response.get("error")
    require(type(error) is dict, "expected JSON-RPC error object")
    code = error.get("code")
    require(type(code) is int, "expected JSON-RPC integer error code")
    return code


def decode_all(data: bytes) -> tuple[dict, ...]:
    stream = BytesIO(data)
    values = []
    while stream.tell() < len(data):
        value = read_message(stream)
        require(type(value) is dict, "framed output was not an object")
        values.append(dict(value))
    return tuple(values)


def require_transport_error(data: bytes, message: str) -> LSPTransportError:
    try:
        read_payload(BytesIO(data))
    except LSPTransportError as error:
        require(error.code == "APX-LSP-001", "transport error code changed")
        return error
    raise AssertionError(message)


def initialize_params() -> dict:
    return {
        "processId": None,
        "clientInfo": {
            "name": "ApexForgeSmokeClient",
            "version": "1.0",
        },
        "rootUri": "file:///C:/ApexForgeDemo",
        "capabilities": {},
    }


def main() -> None:
    require(P10_T4_LSP_FOUNDATION_VERSION == "10-T4.1", "version changed")
    require(LSP_SPECIFICATION_VERSION == "3.18", "LSP version changed")
    require(LSP_FOUNDATION_SCHEMA == 1, "foundation schema changed")
    require(
        LSP_FOUNDATION_KIND == "apexforge.language-server-foundation",
        "foundation kind changed",
    )
    require(LANGUAGE_ID == "apexforge", "language id changed")
    require(SERVER_NAME == "apexforge-language-server", "server name changed")
    require(SERVER_VERSION == "0.1.0", "server version changed")
    require(POSITION_ENCODING == "utf-16", "position encoding changed")
    require(TEXT_DOCUMENT_SYNC_FULL == 1, "document sync kind changed")
    require(
        server_capabilities()
        == {
            "positionEncoding": "utf-16",
            "textDocumentSync": {
                "openClose": True,
                "change": 1,
                "save": False,
            },
        },
        "server capabilities changed",
    )

    unicode_message = request(
        1,
        "example/unicode",
        {"text": "ApexForge λ Sentinel"},
    )
    framed = encode_message(unicode_message)
    header, content = framed.split(b"\r\n\r\n", 1)
    require(
        header == f"Content-Length: {len(content)}".encode("ascii"),
        "Content-Length did not count UTF-8 bytes",
    )
    require(dict(read_message(BytesIO(framed))) == unicode_message, "frame roundtrip failed")
    require_transport_error(
        b"Content-Type: application/vscode-jsonrpc\r\n\r\n{}",
        "missing Content-Length unexpectedly succeeded",
    )
    require_transport_error(
        b"Content-Length: 4\n\nnull",
        "LF-only LSP headers unexpectedly succeeded",
    )

    session = LanguageServerSession()
    pre_initialize = session.process(request(10, "shutdown"))
    require(
        error_code(pre_initialize) == SERVER_NOT_INITIALIZED,
        "pre-initialize request did not use ServerNotInitialized",
    )

    initialized = session.process(request(11, "initialize", initialize_params()))
    require(type(initialized) is dict, "initialize omitted response")
    require(
        initialized.get("result")
        == {
            "capabilities": server_capabilities(),
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        },
        "initialize result changed",
    )
    require(session.initialized, "initialize did not update lifecycle state")
    require(session.root_uri == "file:///C:/ApexForgeDemo", "root URI was lost")

    duplicate_initialize = session.process(
        request(12, "initialize", initialize_params())
    )
    require(
        error_code(duplicate_initialize) == INVALID_REQUEST,
        "duplicate initialize was not rejected",
    )

    require(
        session.process(notification("initialized", {})) is None,
        "initialized notification produced a response",
    )
    require(
        session.initialized_notification_received,
        "initialized notification was not recorded",
    )

    uri = "file:///C:/ApexForgeDemo/main.apex"
    original = "function Identity(value : int) : int { return value }\n"
    updated = "function Identity(value : int) : int { return value + 1 }\n"
    require(
        session.process(
            notification(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "apexforge",
                        "version": 1,
                        "text": original,
                    }
                },
            )
        )
        is None,
        "didOpen produced a response",
    )
    document = session.documents.get(uri)
    require(document is not None and document.text == original, "didOpen lost text")

    session.process(
        notification(
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": 2},
                "contentChanges": [{"text": updated}],
            },
        )
    )
    document = session.documents.get(uri)
    require(
        document is not None and document.version == 2 and document.text == updated,
        "full document synchronization failed",
    )

    error_count = session.notification_error_count
    session.process(
        notification(
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": 2},
                "contentChanges": [{"text": "stale"}],
            },
        )
    )
    require(
        session.notification_error_count == error_count + 1,
        "invalid notification was not isolated",
    )
    require(
        session.last_notification_error is not None
        and session.last_notification_error.rpc_code == INVALID_PARAMS,
        "stale document version used the wrong error",
    )
    require(session.documents.get(uri).text == updated, "stale change mutated document")

    session.process(
        notification(
            "textDocument/didClose",
            {"textDocument": {"uri": uri}},
        )
    )
    require(session.documents.get(uri) is None, "didClose retained the document")

    unknown = session.process(request(13, "textDocument/hover", {}))
    require(
        error_code(unknown) == METHOD_NOT_FOUND,
        "deferred language feature did not return MethodNotFound",
    )

    shutdown = session.process(request(14, "shutdown"))
    require(
        shutdown == {"jsonrpc": "2.0", "id": 14, "result": None},
        "shutdown response changed",
    )
    after_shutdown = session.process(request(15, "textDocument/hover", {}))
    require(
        error_code(after_shutdown) == INVALID_REQUEST,
        "request after shutdown was not rejected",
    )
    session.process(notification("exit"))
    require(session.exited and session.exit_code == EXIT_SUCCESS, "clean exit failed")

    unclean = LanguageServerSession()
    unclean.process(notification("exit"))
    require(
        unclean.exited and unclean.exit_code == EXIT_UNCLEAN,
        "exit before shutdown did not use failure status",
    )

    transcript_messages = (
        request(21, "initialize", initialize_params()),
        notification("initialized", {}),
        notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "apexforge",
                    "version": 1,
                    "text": original,
                }
            },
        ),
        notification(
            "textDocument/didChange",
            {
                "textDocument": {"uri": uri, "version": 2},
                "contentChanges": [{"text": updated}],
            },
        ),
        notification(
            "textDocument/didClose",
            {"textDocument": {"uri": uri}},
        ),
        request(22, "shutdown"),
        notification("exit"),
    )
    transcript = b"".join(encode_message(item) for item in transcript_messages)
    output = BytesIO()
    errors = StringIO()
    code = run_language_server(BytesIO(transcript), output, error_stream=errors)
    require(code == EXIT_SUCCESS, "stdio transcript did not exit cleanly")
    require(errors.getvalue() == "", "clean transcript wrote to stderr")
    responses = decode_all(output.getvalue())
    require(tuple(item.get("id") for item in responses) == (21, 22), "response order changed")
    require(responses[1].get("result") is None, "shutdown transcript result changed")

    malformed = b"Content-Length: 1\r\n\r\n{" + b"".join(
        encode_message(item)
        for item in (
            request(31, "initialize", initialize_params()),
            request(32, "shutdown"),
            notification("exit"),
        )
    )
    malformed_output = BytesIO()
    malformed_code = run_language_server(
        BytesIO(malformed),
        malformed_output,
        error_stream=StringIO(),
    )
    require(malformed_code == EXIT_SUCCESS, "server did not recover from JSON parse error")
    malformed_responses = decode_all(malformed_output.getvalue())
    require(
        error_code(malformed_responses[0]) == PARSE_ERROR,
        "malformed JSON used the wrong error code",
    )
    require(
        tuple(item.get("id") for item in malformed_responses[1:]) == (31, 32),
        "server lost requests after parse recovery",
    )

    transport_errors = StringIO()
    transport_code = run_language_server(
        BytesIO(b"Content-Length: nope\r\n\r\n"),
        BytesIO(),
        error_stream=transport_errors,
    )
    require(transport_code == EXIT_TRANSPORT_ERROR, "transport failure exit changed")
    require("APX-LSP-001" in transport_errors.getvalue(), "transport diagnostic omitted")

    require(
        foundation_fingerprint() == EXPECTED_FOUNDATION_SHA256,
        "foundation projection is not deterministic",
    )
    require(
        CANONICAL_LSP_FOUNDATION_SHA256 == EXPECTED_FOUNDATION_SHA256,
        "declared foundation fingerprint changed",
    )

    version_out = StringIO()
    version_err = StringIO()
    version_code = server_main(
        ("--version",),
        stdout=version_out,
        stderr=version_err,
    )
    require(version_code == 0, "--version returned failure")
    require(
        version_out.getvalue()
        == "ApexForge Language Server 10-T4.1 (LSP 3.18)\n",
        "--version output changed",
    )
    require(version_err.getvalue() == "", "--version wrote stderr")

    package_dir = Path(__file__).resolve().parent
    wrapper = package_dir / "apexforge_lsp.py"
    completed = subprocess.run(
        [sys.executable, str(wrapper), "--version"],
        cwd=str(package_dir.parent),
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, "repository LSP wrapper returned failure")
    require(
        completed.stdout == "ApexForge Language Server 10-T4.1 (LSP 3.18)\n",
        "repository LSP wrapper output changed",
    )
    require(completed.stderr == "", "repository LSP wrapper wrote stderr")

    print("AFP-P10-T4.1 language-server foundation smoke test passed.")
    print("LSP 3.18 initialize/shutdown lifecycle: PASS")
    print("JSON-RPC 2.0 request and error handling: PASS")
    print("Content-Length stdio framing: PASS")
    print("Full document synchronization: PASS")
    print("Notification error isolation: PASS")
    print("Clean and unclean exit semantics: PASS")
    print("Deterministic foundation fingerprint: PASS")
    print("Direct repository entry point: PASS")


if __name__ == "__main__":
    main()
