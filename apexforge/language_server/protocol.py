"""Dependency-free JSON-RPC 2.0 and LSP stdio framing primitives.

AFP-P10-T4.1 implements the byte-level Language Server Protocol transport. The
transport is deliberately independent from ApexForge parsing and compilation so
future language features can reuse one deterministic protocol boundary.
"""

from __future__ import annotations

import json
from typing import BinaryIO, Final, Mapping, Optional


JSONRPC_VERSION: Final[str] = "2.0"
CONTENT_LENGTH_HEADER: Final[str] = "content-length"
CONTENT_TYPE_HEADER: Final[str] = "content-type"
DEFAULT_CONTENT_TYPE: Final[str] = "application/vscode-jsonrpc; charset=utf-8"
MAX_CONTENT_LENGTH: Final[int] = 16 * 1024 * 1024
MAX_HEADER_LINE_LENGTH: Final[int] = 8192
MAX_HEADER_COUNT: Final[int] = 32

PARSE_ERROR: Final[int] = -32700
INVALID_REQUEST: Final[int] = -32600
METHOD_NOT_FOUND: Final[int] = -32601
INVALID_PARAMS: Final[int] = -32602
INTERNAL_ERROR: Final[int] = -32603
SERVER_NOT_INITIALIZED: Final[int] = -32002


class EndOfStream(EOFError):
    """The input stream ended between complete LSP messages."""


class LSPTransportError(ValueError):
    """Malformed or incomplete LSP Content-Length framing."""

    code: Final[str] = "APX-LSP-001"

    def __init__(self, message: str) -> None:
        if type(message) is not str or not message:
            raise ValueError("LSPTransportError.message must be non-empty.")
        self.message = message
        super().__init__(f"[{self.code}] {message}")


class JsonRpcFault(ValueError):
    """A JSON-RPC error that can be projected into an ErrorResponse."""

    def __init__(
        self,
        rpc_code: int,
        message: str,
        *,
        data: object = None,
        has_data: bool = False,
    ) -> None:
        if type(rpc_code) is not int:
            raise TypeError("JsonRpcFault.rpc_code must be an int.")
        if type(message) is not str or not message:
            raise ValueError("JsonRpcFault.message must be non-empty.")
        self.rpc_code = rpc_code
        self.message = message
        self.data = data
        self.has_data = has_data
        super().__init__(f"JSON-RPC {rpc_code}: {message}")


def is_message_id(value: object) -> bool:
    """Return whether ``value`` is an LSP request identifier."""

    return (type(value) is int) or (type(value) is str)


def result_response(message_id: object, result: object) -> dict[str, object]:
    """Create a deterministic JSON-RPC success response."""

    if not is_message_id(message_id):
        raise TypeError("JSON-RPC response id must be a string or int.")
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": message_id,
        "result": result,
    }


def error_response(
    message_id: object,
    code: int,
    message: str,
    *,
    data: object = None,
    has_data: bool = False,
) -> dict[str, object]:
    """Create a deterministic JSON-RPC error response."""

    if message_id is not None and not is_message_id(message_id):
        message_id = None
    if type(code) is not int:
        raise TypeError("JSON-RPC error code must be an int.")
    if type(message) is not str or not message:
        raise ValueError("JSON-RPC error message must be non-empty.")

    error: dict[str, object] = {
        "code": code,
        "message": message,
    }
    if has_data:
        error["data"] = data

    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": message_id,
        "error": error,
    }


def encode_message(message: Mapping[str, object]) -> bytes:
    """Encode one JSON-RPC object with canonical LSP Content-Length framing."""

    if not isinstance(message, Mapping):
        raise TypeError("LSP messages must be mappings.")

    content = json.dumps(
        dict(message),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(content) > MAX_CONTENT_LENGTH:
        raise LSPTransportError(
            f"LSP message exceeds {MAX_CONTENT_LENGTH} bytes."
        )

    header = f"Content-Length: {len(content)}\r\n\r\n".encode("ascii")
    return header + content


def write_message(stream: BinaryIO, message: Mapping[str, object]) -> None:
    """Write and flush one framed JSON-RPC message."""

    stream.write(encode_message(message))
    flush = getattr(stream, "flush", None)
    if callable(flush):
        flush()


def _read_header_line(stream: BinaryIO, *, first: bool) -> bytes:
    line = stream.readline(MAX_HEADER_LINE_LENGTH + 1)
    if line == b"":
        if first:
            raise EndOfStream()
        raise LSPTransportError("Unexpected EOF inside LSP headers.")
    if len(line) > MAX_HEADER_LINE_LENGTH:
        raise LSPTransportError("LSP header line exceeds the size limit.")
    if not line.endswith(b"\r\n"):
        raise LSPTransportError("LSP headers must use CRLF line endings.")
    return line


def read_payload(stream: BinaryIO) -> bytes:
    """Read one exact Content-Length-delimited payload from ``stream``."""

    headers: dict[str, str] = {}
    for index in range(MAX_HEADER_COUNT + 1):
        if index == MAX_HEADER_COUNT:
            raise LSPTransportError("LSP message contains too many headers.")

        line = _read_header_line(stream, first=(index == 0))
        if line == b"\r\n":
            break

        raw = line[:-2]
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise LSPTransportError("LSP headers must be ASCII.") from error

        if ":" not in text:
            raise LSPTransportError(f"Malformed LSP header line {text!r}.")
        name, value = text.split(":", 1)
        normalized_name = name.strip().casefold()
        normalized_value = value.strip()
        if not normalized_name or not normalized_value:
            raise LSPTransportError(f"Malformed LSP header line {text!r}.")
        if normalized_name in headers:
            raise LSPTransportError(
                f"Duplicate LSP header {normalized_name!r}."
            )
        headers[normalized_name] = normalized_value

    length_text = headers.get(CONTENT_LENGTH_HEADER)
    if length_text is None:
        raise LSPTransportError("LSP message is missing Content-Length.")
    if not length_text.isdecimal():
        raise LSPTransportError("Content-Length must be a decimal byte count.")

    content_length = int(length_text, 10)
    if content_length > MAX_CONTENT_LENGTH:
        raise LSPTransportError(
            f"Content-Length exceeds {MAX_CONTENT_LENGTH} bytes."
        )

    content_type = headers.get(CONTENT_TYPE_HEADER)
    if content_type is not None:
        compact = content_type.casefold().replace(" ", "")
        if "charset=" in compact and not (
            "charset=utf-8" in compact or "charset=utf8" in compact
        ):
            raise LSPTransportError("Only UTF-8 LSP content is supported.")

    payload = stream.read(content_length)
    if len(payload) != content_length:
        raise LSPTransportError(
            "Unexpected EOF inside the LSP content body; "
            f"expected {content_length} bytes, received {len(payload)}."
        )
    return payload


def decode_payload(payload: bytes) -> Mapping[str, object]:
    """Decode one UTF-8 JSON-RPC object from exact payload bytes."""

    if not isinstance(payload, bytes):
        raise TypeError("LSP payload must be bytes.")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise JsonRpcFault(PARSE_ERROR, "Parse error") from error

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise JsonRpcFault(PARSE_ERROR, "Parse error") from error

    if type(value) is not dict:
        raise JsonRpcFault(
            INVALID_REQUEST,
            "Invalid Request",
            data="LSP batch and primitive messages are unsupported.",
            has_data=True,
        )
    return value


def read_message(stream: BinaryIO) -> Mapping[str, object]:
    """Read and decode one framed JSON-RPC object."""

    return decode_payload(read_payload(stream))


__all__ = (
    "CONTENT_LENGTH_HEADER",
    "DEFAULT_CONTENT_TYPE",
    "EndOfStream",
    "INTERNAL_ERROR",
    "INVALID_PARAMS",
    "INVALID_REQUEST",
    "JSONRPC_VERSION",
    "JsonRpcFault",
    "LSPTransportError",
    "MAX_CONTENT_LENGTH",
    "METHOD_NOT_FOUND",
    "PARSE_ERROR",
    "SERVER_NOT_INITIALIZED",
    "decode_payload",
    "encode_message",
    "error_response",
    "is_message_id",
    "read_message",
    "read_payload",
    "result_response",
    "write_message",
)
