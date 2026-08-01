"""AFP-P10-T4.1 ApexForge Language Server foundation.

The foundation implements JSON-RPC/LSP lifecycle handling and full text-document
synchronization over stdio. Diagnostics, document symbols, hover, completion, same-document definition,
references, safe rename, and workspace symbols and deterministic whole-document formatting are layered onto
this frozen foundation; range formatting remains deliberately deferred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from typing import BinaryIO, Final, Mapping, Optional, Sequence, TextIO

from language_server.diagnostics import (
    CANONICAL_LSP_DIAGNOSTICS_SHA256,
    P10_T4_LSP_DIAGNOSTICS_VERSION,
    analyze_document,
    publish_diagnostics_notification,
)

from language_server.symbols import (
    CANONICAL_DOCUMENT_SYMBOLS_SHA256,
    DOCUMENT_SYMBOL_METHOD,
    P10_T4_DOCUMENT_SYMBOL_VERSION,
    document_symbols,
)

from language_server.hover import (
    CANONICAL_HOVER_SHA256,
    HOVER_METHOD,
    P10_T4_HOVER_VERSION,
    hover,
)

from language_server.completion import (
    CANONICAL_COMPLETION_SHA256,
    COMPLETION_METHOD,
    COMPLETION_TRIGGER_CHARACTERS,
    P10_T4_COMPLETION_VERSION,
    completion,
)

from language_server.definition import (
    CANONICAL_DEFINITION_SHA256,
    DEFINITION_METHOD,
    P10_T4_DEFINITION_VERSION,
    definition,
)

from language_server.references import (
    CANONICAL_REFERENCES_SHA256,
    P10_T4_REFERENCES_VERSION,
    REFERENCES_METHOD,
    references,
)

from language_server.rename import (
    CANONICAL_RENAME_SHA256,
    P10_T4_RENAME_VERSION,
    PREPARE_RENAME_METHOD,
    RENAME_METHOD,
    prepare_rename,
    rename,
)


from language_server.formatting import (
    CANONICAL_FORMATTING_SHA256,
    FORMATTING_METHOD,
    P10_T4_FORMATTING_VERSION,
    format_document,
)

from language_server.workspace_symbols import (
    CANONICAL_WORKSPACE_SYMBOLS_SHA256,
    P10_T4_WORKSPACE_SYMBOL_VERSION,
    WORKSPACE_SYMBOL_METHOD,
    workspace_symbols,
)

from language_server.protocol import (
    INTERNAL_ERROR,
    INVALID_PARAMS,
    INVALID_REQUEST,
    JSONRPC_VERSION,
    METHOD_NOT_FOUND,
    PARSE_ERROR,
    SERVER_NOT_INITIALIZED,
    EndOfStream,
    JsonRpcFault,
    LSPTransportError,
    decode_payload,
    error_response,
    is_message_id,
    read_payload,
    result_response,
    write_message,
)


P10_T4_LSP_FOUNDATION_VERSION: Final[str] = "10-T4.1"
LSP_SPECIFICATION_VERSION: Final[str] = "3.18"
LSP_FOUNDATION_SCHEMA: Final[int] = 1
LSP_FOUNDATION_KIND: Final[str] = "apexforge.language-server-foundation"

SERVER_NAME: Final[str] = "apexforge-language-server"
SERVER_VERSION: Final[str] = "0.1.0"
LANGUAGE_ID: Final[str] = "apexforge"
POSITION_ENCODING: Final[str] = "utf-16"
TEXT_DOCUMENT_SYNC_FULL: Final[int] = 1

EXIT_SUCCESS: Final[int] = 0
EXIT_UNCLEAN: Final[int] = 1
EXIT_TRANSPORT_ERROR: Final[int] = 2


@dataclass(frozen=True, order=True)
class OpenDocument:
    """One full-text document snapshot owned by the LSP session."""

    uri: str
    language_id: str
    version: int
    text: str

    def __post_init__(self) -> None:
        if type(self.uri) is not str or not self.uri:
            raise ValueError("OpenDocument.uri must be a non-empty string.")
        if ":" not in self.uri:
            raise ValueError("OpenDocument.uri must be an absolute URI.")
        if type(self.language_id) is not str or not self.language_id:
            raise ValueError("OpenDocument.language_id must be non-empty.")
        if type(self.version) is not int:
            raise TypeError("OpenDocument.version must be an int.")
        if type(self.text) is not str:
            raise TypeError("OpenDocument.text must be a string.")


class DocumentStore:
    """Deterministic full-synchronization document storage."""

    def __init__(self) -> None:
        self._documents: dict[str, OpenDocument] = {}

    def __len__(self) -> int:
        return len(self._documents)

    def get(self, uri: str) -> Optional[OpenDocument]:
        return self._documents.get(uri)

    def snapshot(self) -> tuple[OpenDocument, ...]:
        return tuple(
            self._documents[uri]
            for uri in sorted(
                self._documents,
                key=lambda value: (value.casefold(), value),
            )
        )

    def open(self, document: OpenDocument) -> None:
        if document.language_id != LANGUAGE_ID:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=(
                    "ApexForge didOpen requires languageId "
                    f"{LANGUAGE_ID!r}."
                ),
                has_data=True,
            )
        if document.uri in self._documents:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is already open: {document.uri}.",
                has_data=True,
            )
        self._documents[document.uri] = document

    def change(
        self,
        *,
        uri: str,
        version: int,
        changes: object,
    ) -> None:
        current = self._documents.get(uri)
        if current is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        if type(version) is not int:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="didChange textDocument.version must be an integer.",
                has_data=True,
            )
        if version <= current.version:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=(
                    "didChange document versions must increase; "
                    f"current={current.version}, received={version}."
                ),
                has_data=True,
            )
        if type(changes) is not list or not changes:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="didChange contentChanges must be a non-empty array.",
                has_data=True,
            )

        final_text = current.text
        for index, item in enumerate(changes):
            if type(item) is not dict:
                raise JsonRpcFault(
                    INVALID_PARAMS,
                    "Invalid params",
                    data=f"contentChanges[{index}] must be an object.",
                    has_data=True,
                )
            if "range" in item or "rangeLength" in item:
                raise JsonRpcFault(
                    INVALID_PARAMS,
                    "Invalid params",
                    data=(
                        "ApexForge T4.1 advertises full document sync; "
                        "incremental ranges are unsupported."
                    ),
                    has_data=True,
                )
            text = item.get("text")
            if type(text) is not str:
                raise JsonRpcFault(
                    INVALID_PARAMS,
                    "Invalid params",
                    data=f"contentChanges[{index}].text must be a string.",
                    has_data=True,
                )
            final_text = text

        self._documents[uri] = OpenDocument(
            uri=uri,
            language_id=current.language_id,
            version=version,
            text=final_text,
        )

    def close(self, uri: str) -> None:
        if uri not in self._documents:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        del self._documents[uri]


def server_capabilities() -> dict[str, object]:
    """Return the exact capability set frozen by AFP-P10-T4.1."""

    return {
        "positionEncoding": POSITION_ENCODING,
        "textDocumentSync": {
            "openClose": True,
            "change": TEXT_DOCUMENT_SYNC_FULL,
            "save": False,
        },
    }


def active_server_capabilities(
    *,
    document_symbols_enabled: bool = False,
    hover_enabled: bool = False,
    completion_enabled: bool = False,
    definition_enabled: bool = False,
    references_enabled: bool = False,
    rename_enabled: bool = False,
    workspace_symbols_enabled: bool = False,
    formatting_enabled: bool = False,
) -> dict[str, object]:
    """Return negotiated capabilities without changing the frozen T4.1 projection."""

    capabilities = server_capabilities()
    if document_symbols_enabled:
        capabilities["documentSymbolProvider"] = True
    if hover_enabled:
        capabilities["hoverProvider"] = True
    if completion_enabled:
        capabilities["completionProvider"] = {
            "resolveProvider": False,
            "triggerCharacters": list(COMPLETION_TRIGGER_CHARACTERS),
        }
    if definition_enabled:
        capabilities["definitionProvider"] = True
    if references_enabled:
        capabilities["referencesProvider"] = True
    if rename_enabled:
        capabilities["renameProvider"] = {"prepareProvider": True}
    if workspace_symbols_enabled:
        capabilities["workspaceSymbolProvider"] = True
    if formatting_enabled:
        capabilities["documentFormattingProvider"] = True
    return capabilities


def foundation_contract() -> dict[str, object]:
    """Return the deterministic public T4.1 protocol contract."""

    return {
        "schema": LSP_FOUNDATION_SCHEMA,
        "kind": LSP_FOUNDATION_KIND,
        "foundation_version": P10_T4_LSP_FOUNDATION_VERSION,
        "lsp_specification": LSP_SPECIFICATION_VERSION,
        "jsonrpc": JSONRPC_VERSION,
        "server": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "language_id": LANGUAGE_ID,
        },
        "capabilities": server_capabilities(),
        "lifecycle": (
            "initialize",
            "initialized",
            "shutdown",
            "exit",
        ),
        "document_notifications": (
            "textDocument/didOpen",
            "textDocument/didChange",
            "textDocument/didClose",
        ),
        "jsonrpc_errors": {
            "parse_error": PARSE_ERROR,
            "invalid_request": INVALID_REQUEST,
            "method_not_found": METHOD_NOT_FOUND,
            "invalid_params": INVALID_PARAMS,
            "internal_error": INTERNAL_ERROR,
            "server_not_initialized": SERVER_NOT_INITIALIZED,
        },
        "exit_codes": {
            "clean": EXIT_SUCCESS,
            "unclean": EXIT_UNCLEAN,
            "transport_error": EXIT_TRANSPORT_ERROR,
        },
    }


def foundation_fingerprint() -> str:
    payload = json.dumps(
        foundation_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Filled after the public projection above is serialized. Smoke tests reject
# drift while later T4 slices add language features outside this foundation.
CANONICAL_LSP_FOUNDATION_SHA256: Final[str] = "3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d"


class LanguageServerSession:
    """One deterministic LSP client/server lifecycle."""

    def __init__(self) -> None:
        self.initialized = False
        self.initialized_notification_received = False
        self.shutdown_requested = False
        self.exited = False
        self.exit_code: Optional[int] = None
        self.client_info: Optional[Mapping[str, object]] = None
        self.root_uri: Optional[str] = None
        self.documents = DocumentStore()
        self.diagnostics_enabled = False
        self.diagnostics_related_information = False
        self.diagnostics_version_support = False
        self.document_symbols_enabled = False
        self.hover_enabled = False
        self.completion_enabled = False
        self.definition_enabled = False
        self.references_enabled = False
        self.rename_enabled = False
        self.workspace_symbols_enabled = False
        self.formatting_enabled = False
        self._outgoing_notifications: list[dict[str, object]] = []
        self.notification_error_count = 0
        self.last_notification_error: Optional[JsonRpcFault] = None

    def drain_outgoing_notifications(self) -> tuple[dict[str, object], ...]:
        """Return queued server notifications and clear the deterministic queue."""

        queued = tuple(self._outgoing_notifications)
        self._outgoing_notifications.clear()
        return queued

    def process(self, message: Mapping[str, object]) -> Optional[dict[str, object]]:
        """Process one decoded JSON-RPC object and return an optional response."""

        message_id: object = None
        is_request = type(message) is dict and "id" in message
        if is_request:
            message_id = message.get("id")
        try:
            method, message_id, is_request, params = self._validate_envelope(message)
            return self._dispatch(
                method=method,
                message_id=message_id,
                is_request=is_request,
                params=params,
            )
        except JsonRpcFault as fault:
            if is_request:
                return error_response(
                    message_id,
                    fault.rpc_code,
                    fault.message,
                    data=fault.data,
                    has_data=fault.has_data,
                )
            self.notification_error_count += 1
            self.last_notification_error = fault
            return None
        except Exception as error:  # deterministic protocol containment
            if is_request:
                return error_response(
                    message_id,
                    INTERNAL_ERROR,
                    "Internal error",
                    data=f"{type(error).__name__}: {error}",
                    has_data=True,
                )
            self.notification_error_count += 1
            self.last_notification_error = JsonRpcFault(
                INTERNAL_ERROR,
                "Internal error",
                data=f"{type(error).__name__}: {error}",
                has_data=True,
            )
            return None

    def _validate_envelope(
        self,
        message: Mapping[str, object],
    ) -> tuple[str, object, bool, object]:
        if type(message) is not dict:
            raise JsonRpcFault(INVALID_REQUEST, "Invalid Request")
        if message.get("jsonrpc") != JSONRPC_VERSION:
            raise JsonRpcFault(
                INVALID_REQUEST,
                "Invalid Request",
                data='jsonrpc must be exactly "2.0".',
                has_data=True,
            )

        method = message.get("method")
        if type(method) is not str or not method:
            raise JsonRpcFault(
                INVALID_REQUEST,
                "Invalid Request",
                data="Request and notification objects require method.",
                has_data=True,
            )

        is_request = "id" in message
        message_id = message.get("id")
        if is_request and not is_message_id(message_id):
            raise JsonRpcFault(
                INVALID_REQUEST,
                "Invalid Request",
                data="LSP request id must be a string or integer.",
                has_data=True,
            )

        params = message.get("params")
        if "params" in message and params is not None and type(params) not in (
            dict,
            list,
        ):
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="JSON-RPC params must be an object or array.",
                has_data=True,
            )
        return method, message_id, is_request, params

    def _dispatch(
        self,
        *,
        method: str,
        message_id: object,
        is_request: bool,
        params: object,
    ) -> Optional[dict[str, object]]:
        if not self.initialized:
            if method == "initialize":
                if not is_request:
                    raise JsonRpcFault(
                        INVALID_REQUEST,
                        "Invalid Request",
                        data="initialize must be a request.",
                        has_data=True,
                    )
                return result_response(
                    message_id,
                    self._initialize(params),
                )
            if method == "exit" and not is_request:
                self._exit(clean=False)
                return None
            if is_request:
                raise JsonRpcFault(
                    SERVER_NOT_INITIALIZED,
                    "Server not initialized",
                )
            return None

        if self.shutdown_requested:
            if method == "exit" and not is_request:
                self._require_void_params(params, "exit")
                self._exit(clean=True)
                return None
            if is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data="The language server has already shut down.",
                    has_data=True,
                )
            return None

        if method == "initialize":
            raise JsonRpcFault(
                INVALID_REQUEST,
                "Invalid Request",
                data="initialize may be sent only once.",
                has_data=True,
            )
        if method == "initialized":
            if is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data="initialized must be a notification.",
                    has_data=True,
                )
            self._require_mapping(params, "initialized params", allow_none=True)
            self.initialized_notification_received = True
            return None
        if method == "shutdown":
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data="shutdown must be a request.",
                    has_data=True,
                )
            self._require_void_params(params, "shutdown")
            self.shutdown_requested = True
            return result_response(message_id, None)
        if method == "exit":
            if is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data="exit must be a notification.",
                    has_data=True,
                )
            self._require_void_params(params, "exit")
            self._exit(clean=False)
            return None
        if method == "textDocument/didOpen":
            self._require_notification(is_request, method)
            self._did_open(params)
            return None
        if method == "textDocument/didChange":
            self._require_notification(is_request, method)
            self._did_change(params)
            return None
        if method == "textDocument/didClose":
            self._require_notification(is_request, method)
            self._did_close(params)
            return None
        if method == HOVER_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{HOVER_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._hover(params),
            )
        if method == COMPLETION_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{COMPLETION_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._completion(params),
            )
        if method == DEFINITION_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{DEFINITION_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._definition(params),
            )
        if method == REFERENCES_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{REFERENCES_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._references(params),
            )
        if method == PREPARE_RENAME_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{PREPARE_RENAME_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._prepare_rename(params),
            )
        if method == RENAME_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{RENAME_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._rename(params),
            )
        if method == WORKSPACE_SYMBOL_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{WORKSPACE_SYMBOL_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._workspace_symbols(params),
            )
        if method == FORMATTING_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{FORMATTING_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(message_id, self._formatting(params))
        if method == DOCUMENT_SYMBOL_METHOD:
            if not is_request:
                raise JsonRpcFault(
                    INVALID_REQUEST,
                    "Invalid Request",
                    data=f"{DOCUMENT_SYMBOL_METHOD} must be a request.",
                    has_data=True,
                )
            return result_response(
                message_id,
                self._document_symbols(params),
            )

        if is_request:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")
        return None

    def _initialize(self, params: object) -> dict[str, object]:
        value = self._require_mapping(params, "initialize params")
        capabilities = value.get("capabilities")
        if type(capabilities) is not dict:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="initialize capabilities must be an object.",
                has_data=True,
            )
        self._configure_diagnostics(capabilities)
        self._configure_document_symbols(capabilities)
        self._configure_hover(capabilities)
        self._configure_completion(capabilities)
        self._configure_definition(capabilities)
        self._configure_references(capabilities)
        self._configure_rename(capabilities)
        self._configure_workspace_symbols(capabilities)
        self._configure_formatting(capabilities)

        process_id = value.get("processId")
        if process_id is not None and type(process_id) is not int:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="initialize processId must be an integer or null.",
                has_data=True,
            )

        root_uri = value.get("rootUri")
        if root_uri is not None and (type(root_uri) is not str or not root_uri):
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="initialize rootUri must be a non-empty URI or null.",
                has_data=True,
            )

        client_info = value.get("clientInfo")
        if client_info is not None:
            if type(client_info) is not dict:
                raise JsonRpcFault(
                    INVALID_PARAMS,
                    "Invalid params",
                    data="initialize clientInfo must be an object.",
                    has_data=True,
                )
            name = client_info.get("name")
            if type(name) is not str or not name:
                raise JsonRpcFault(
                    INVALID_PARAMS,
                    "Invalid params",
                    data="initialize clientInfo.name must be non-empty.",
                    has_data=True,
                )
            self.client_info = dict(client_info)

        self.root_uri = root_uri
        self.initialized = True
        return {
            "capabilities": active_server_capabilities(
                document_symbols_enabled=self.document_symbols_enabled,
                hover_enabled=self.hover_enabled,
                completion_enabled=self.completion_enabled,
                definition_enabled=self.definition_enabled,
                references_enabled=self.references_enabled,
                rename_enabled=self.rename_enabled,
                workspace_symbols_enabled=self.workspace_symbols_enabled,
                formatting_enabled=self.formatting_enabled,
            ),
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }

    def _did_open(self, params: object) -> None:
        value = self._require_mapping(params, "didOpen params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "didOpen textDocument",
        )
        document = OpenDocument(
            uri=self._required_uri(
                text_document.get("uri"),
                "didOpen textDocument.uri",
            ),
            language_id=self._required_string(
                text_document.get("languageId"),
                "didOpen textDocument.languageId",
            ),
            version=self._required_int(
                text_document.get("version"),
                "didOpen textDocument.version",
            ),
            text=self._required_string_value(
                text_document.get("text"),
                "didOpen textDocument.text",
            ),
        )
        self.documents.open(document)
        self._publish_document_diagnostics(document)

    def _did_change(self, params: object) -> None:
        value = self._require_mapping(params, "didChange params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "didChange textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "didChange textDocument.uri",
        )
        self.documents.change(
            uri=uri,
            version=self._required_int(
                text_document.get("version"),
                "didChange textDocument.version",
            ),
            changes=value.get("contentChanges"),
        )
        document = self.documents.get(uri)
        assert document is not None
        self._publish_document_diagnostics(document)

    def _did_close(self, params: object) -> None:
        value = self._require_mapping(params, "didClose params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "didClose textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "didClose textDocument.uri",
        )
        self.documents.close(uri)
        if self.diagnostics_enabled:
            self._outgoing_notifications.append(
                publish_diagnostics_notification(uri, ())
            )

    def _configure_diagnostics(self, capabilities: Mapping[str, object]) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        publish = text_document.get("publishDiagnostics")
        if type(publish) is not dict:
            return

        self.diagnostics_enabled = True
        self.diagnostics_related_information = (
            publish.get("relatedInformation") is True
        )
        self.diagnostics_version_support = publish.get("versionSupport") is True

    def _configure_document_symbols(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        document_symbol = text_document.get("documentSymbol")
        if type(document_symbol) is dict:
            self.document_symbols_enabled = True

    def _configure_hover(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        hover_capability = text_document.get("hover")
        if type(hover_capability) is dict:
            self.hover_enabled = True

    def _configure_completion(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        completion_capability = text_document.get("completion")
        if type(completion_capability) is dict:
            self.completion_enabled = True

    def _configure_definition(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        definition_capability = text_document.get("definition")
        if type(definition_capability) is dict:
            self.definition_enabled = True

    def _configure_references(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        references_capability = text_document.get("references")
        if type(references_capability) is dict:
            self.references_enabled = True

    def _configure_rename(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        rename_capability = text_document.get("rename")
        if type(rename_capability) is dict:
            self.rename_enabled = True

    def _configure_workspace_symbols(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        workspace = capabilities.get("workspace")
        if type(workspace) is not dict:
            return
        symbol_capability = workspace.get("symbol")
        if type(symbol_capability) is dict:
            self.workspace_symbols_enabled = True

    def _configure_formatting(
        self,
        capabilities: Mapping[str, object],
    ) -> None:
        text_document = capabilities.get("textDocument")
        if type(text_document) is not dict:
            return
        formatting_capability = text_document.get("formatting")
        if type(formatting_capability) is dict:
            self.formatting_enabled = True

    def _hover(self, params: object) -> Optional[dict[str, object]]:
        if not self.hover_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "hover params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "hover textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "hover textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "hover position",
        )
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return hover(document.uri, document.text, position)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _completion(self, params: object) -> dict[str, object]:
        if not self.completion_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "completion params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "completion textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "completion textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "completion position",
        )
        context = value.get("context")
        if context is not None:
            context = self._require_mapping(context, "completion context")

        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return completion(
                document.uri,
                document.text,
                position,
                context,
            )
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _definition(self, params: object) -> Optional[dict[str, object]]:
        if not self.definition_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "definition params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "definition textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "definition textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "definition position",
        )
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return definition(document.uri, document.text, position)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _references(self, params: object) -> tuple[dict[str, object], ...]:
        if not self.references_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "references params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "references textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "references textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "references position",
        )
        context = self._require_mapping(
            value.get("context"),
            "references context",
        )
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return references(document.uri, document.text, position, context)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _prepare_rename(self, params: object) -> Optional[dict[str, object]]:
        if not self.rename_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "prepareRename params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "prepareRename textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "prepareRename textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "prepareRename position",
        )
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return prepare_rename(document.uri, document.text, position)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _rename(self, params: object) -> Optional[dict[str, object]]:
        if not self.rename_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "rename params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "rename textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "rename textDocument.uri",
        )
        position = self._require_mapping(
            value.get("position"),
            "rename position",
        )
        new_name = value.get("newName")
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        try:
            return rename(document.uri, document.text, position, new_name)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _workspace_symbols(self, params: object) -> list[dict[str, object]]:
        if not self.workspace_symbols_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "workspace/symbol params")
        query = value.get("query")
        if self.root_uri is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data="workspace/symbol requires initialize.rootUri.",
                has_data=True,
            )
        overlays = {
            document.uri: document.text
            for document in self.documents.snapshot()
        }
        try:
            return list(workspace_symbols(self.root_uri, query, overlays))
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=str(error),
                has_data=True,
            ) from error

    def _formatting(self, params: object) -> tuple[dict[str, object], ...]:
        if not self.formatting_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")
        value = self._require_mapping(params, "formatting params")
        text_document = self._require_mapping(value.get("textDocument"), "formatting textDocument")
        uri = self._required_uri(text_document.get("uri"), "formatting textDocument.uri")
        options = self._require_mapping(value.get("options"), "formatting options")
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(INVALID_PARAMS, "Invalid params", data=f"Document is not open: {uri}.", has_data=True)
        try:
            return format_document(document.uri, document.text, options)
        except (TypeError, ValueError) as error:
            raise JsonRpcFault(INVALID_PARAMS, "Invalid params", data=str(error), has_data=True) from error

    def _document_symbols(self, params: object) -> list[dict[str, object]]:
        if not self.document_symbols_enabled:
            raise JsonRpcFault(METHOD_NOT_FOUND, "Method not found")

        value = self._require_mapping(params, "documentSymbol params")
        text_document = self._require_mapping(
            value.get("textDocument"),
            "documentSymbol textDocument",
        )
        uri = self._required_uri(
            text_document.get("uri"),
            "documentSymbol textDocument.uri",
        )
        document = self.documents.get(uri)
        if document is None:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"Document is not open: {uri}.",
                has_data=True,
            )
        return list(document_symbols(document.uri, document.text))

    def _publish_document_diagnostics(self, document: OpenDocument) -> None:
        if not self.diagnostics_enabled:
            return
        diagnostics = analyze_document(
            document.uri,
            document.text,
            include_related_information=self.diagnostics_related_information,
        )
        version = document.version if self.diagnostics_version_support else None
        self._outgoing_notifications.append(
            publish_diagnostics_notification(
                document.uri,
                diagnostics,
                version=version,
            )
        )

    def _exit(self, *, clean: bool) -> None:
        self.exited = True
        self.exit_code = EXIT_SUCCESS if clean else EXIT_UNCLEAN

    @staticmethod
    def _require_notification(is_request: bool, method: str) -> None:
        if is_request:
            raise JsonRpcFault(
                INVALID_REQUEST,
                "Invalid Request",
                data=f"{method} must be a notification.",
                has_data=True,
            )

    @staticmethod
    def _require_void_params(params: object, owner: str) -> None:
        if params not in (None, {}, []):
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} does not accept parameters.",
                has_data=True,
            )

    @staticmethod
    def _require_mapping(
        value: object,
        owner: str,
        *,
        allow_none: bool = False,
    ) -> Mapping[str, object]:
        if allow_none and value is None:
            return {}
        if type(value) is not dict:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} must be an object.",
                has_data=True,
            )
        return value

    @staticmethod
    def _required_string(value: object, owner: str) -> str:
        if type(value) is not str or not value:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} must be a non-empty string.",
                has_data=True,
            )
        return value

    @staticmethod
    def _required_uri(value: object, owner: str) -> str:
        uri = LanguageServerSession._required_string(value, owner)
        if ":" not in uri:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} must be an absolute URI.",
                has_data=True,
            )
        return uri

    @staticmethod
    def _required_string_value(value: object, owner: str) -> str:
        if type(value) is not str:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} must be a string.",
                has_data=True,
            )
        return value

    @staticmethod
    def _required_int(value: object, owner: str) -> int:
        if type(value) is not int:
            raise JsonRpcFault(
                INVALID_PARAMS,
                "Invalid params",
                data=f"{owner} must be an integer.",
                has_data=True,
            )
        return value


def run_language_server(
    input_stream: BinaryIO,
    output_stream: BinaryIO,
    *,
    error_stream: TextIO = sys.stderr,
    session: Optional[LanguageServerSession] = None,
) -> int:
    """Run one stdio-style LSP session until ``exit`` or a transport failure."""

    active = session or LanguageServerSession()

    while True:
        try:
            payload = read_payload(input_stream)
        except EndOfStream:
            return (
                active.exit_code
                if active.exited and active.exit_code is not None
                else EXIT_UNCLEAN
            )
        except LSPTransportError as error:
            print(str(error), file=error_stream)
            return EXIT_TRANSPORT_ERROR

        try:
            message = decode_payload(payload)
        except JsonRpcFault as fault:
            write_message(
                output_stream,
                error_response(
                    None,
                    fault.rpc_code,
                    fault.message,
                    data=fault.data,
                    has_data=fault.has_data,
                ),
            )
            continue

        response = active.process(message)
        if response is not None:
            write_message(output_stream, response)
        for notification in active.drain_outgoing_notifications():
            write_message(output_stream, notification)

        if active.exited:
            return active.exit_code if active.exit_code is not None else EXIT_UNCLEAN


def _binary_reader(stream: object) -> BinaryIO:
    buffer = getattr(stream, "buffer", None)
    return buffer if buffer is not None else stream  # type: ignore[return-value]


def _binary_writer(stream: object) -> BinaryIO:
    buffer = getattr(stream, "buffer", None)
    return buffer if buffer is not None else stream  # type: ignore[return-value]


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    stdin: object = sys.stdin,
    stdout: object = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    parser = argparse.ArgumentParser(
        prog="apexforge-lsp",
        description="Run the AFP-P10-T4.1 ApexForge Language Server.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stdio", action="store_true", help="serve LSP over stdio")
    mode.add_argument("--version", action="store_true", help="print server version")
    mode.add_argument(
        "--contract",
        action="store_true",
        help="print the frozen foundation fingerprint",
    )
    mode.add_argument(
        "--diagnostics-contract",
        action="store_true",
        help="print the frozen T4.2 diagnostics fingerprint",
    )
    mode.add_argument(
        "--hover-contract",
        action="store_true",
        help="print the frozen AFP-P10-T4.5 hover fingerprint",
    )
    mode.add_argument(
        "--completion-contract",
        action="store_true",
        help="print the AFP-P10-T4.6 completion fingerprint",
    )
    mode.add_argument(
        "--definition-contract",
        action="store_true",
        help="print the AFP-P10-T4.7 definition fingerprint",
    )
    mode.add_argument(
        "--references-contract",
        action="store_true",
        help="print the AFP-P10-T4.8 references fingerprint",
    )
    mode.add_argument(
        "--rename-contract",
        action="store_true",
        help="print the AFP-P10-T4.8 rename fingerprint",
    )
    mode.add_argument(
        "--workspace-symbols-contract",
        action="store_true",
        help="print the AFP-P10-T4.9 workspace-symbol fingerprint",
    )
    mode.add_argument(
        "--formatting-contract",
        action="store_true",
        help="print the AFP-P10-T4.10 formatting fingerprint",
    )
    mode.add_argument(
        "--symbols-contract",
        action="store_true",
        help="print the AFP-P10-T4.4 document-symbol fingerprint",
    )
    arguments = parser.parse_args(tuple(argv) if argv is not None else None)

    if arguments.version:
        print(
            "ApexForge Language Server "
            f"{P10_T4_LSP_FOUNDATION_VERSION} (LSP {LSP_SPECIFICATION_VERSION})",
            file=stdout,
        )
        return EXIT_SUCCESS
    if arguments.contract:
        print(CANONICAL_LSP_FOUNDATION_SHA256, file=stdout)
        return EXIT_SUCCESS
    if arguments.diagnostics_contract:
        print(CANONICAL_LSP_DIAGNOSTICS_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.hover_contract:
        print(CANONICAL_HOVER_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.completion_contract:
        print(CANONICAL_COMPLETION_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.definition_contract:
        print(CANONICAL_DEFINITION_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.references_contract:
        print(CANONICAL_REFERENCES_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.rename_contract:
        print(CANONICAL_RENAME_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.workspace_symbols_contract:
        print(CANONICAL_WORKSPACE_SYMBOLS_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.formatting_contract:
        print(CANONICAL_FORMATTING_SHA256, file=stdout)
        return EXIT_SUCCESS

    if arguments.symbols_contract:
        print(CANONICAL_DOCUMENT_SYMBOLS_SHA256, file=stdout)
        return EXIT_SUCCESS

    return run_language_server(
        _binary_reader(stdin),
        _binary_writer(stdout),
        error_stream=stderr,
    )


__all__ = (
    "CANONICAL_COMPLETION_SHA256",
    "CANONICAL_DEFINITION_SHA256",
    "CANONICAL_REFERENCES_SHA256",
    "CANONICAL_RENAME_SHA256",
    "CANONICAL_WORKSPACE_SYMBOLS_SHA256",
    "CANONICAL_FORMATTING_SHA256",
    "CANONICAL_DOCUMENT_SYMBOLS_SHA256",
    "CANONICAL_HOVER_SHA256",
    "CANONICAL_LSP_DIAGNOSTICS_SHA256",
    "CANONICAL_LSP_FOUNDATION_SHA256",
    "COMPLETION_METHOD",
    "DEFINITION_METHOD",
    "REFERENCES_METHOD",
    "PREPARE_RENAME_METHOD",
    "RENAME_METHOD",
    "WORKSPACE_SYMBOL_METHOD",
    "FORMATTING_METHOD",
    "DOCUMENT_SYMBOL_METHOD",
    "HOVER_METHOD",
    "DocumentStore",
    "EXIT_SUCCESS",
    "EXIT_TRANSPORT_ERROR",
    "EXIT_UNCLEAN",
    "LANGUAGE_ID",
    "LSP_FOUNDATION_KIND",
    "LSP_FOUNDATION_SCHEMA",
    "LSP_SPECIFICATION_VERSION",
    "LanguageServerSession",
    "OpenDocument",
    "P10_T4_COMPLETION_VERSION",
    "P10_T4_DEFINITION_VERSION",
    "P10_T4_REFERENCES_VERSION",
    "P10_T4_RENAME_VERSION",
    "P10_T4_WORKSPACE_SYMBOL_VERSION",
    "P10_T4_FORMATTING_VERSION",
    "P10_T4_DOCUMENT_SYMBOL_VERSION",
    "P10_T4_HOVER_VERSION",
    "P10_T4_LSP_DIAGNOSTICS_VERSION",
    "P10_T4_LSP_FOUNDATION_VERSION",
    "POSITION_ENCODING",
    "SERVER_NAME",
    "SERVER_VERSION",
    "TEXT_DOCUMENT_SYNC_FULL",
    "active_server_capabilities",
    "foundation_contract",
    "foundation_fingerprint",
    "main",
    "run_language_server",
    "server_capabilities",
)


if __name__ == "__main__":
    raise SystemExit(main())
