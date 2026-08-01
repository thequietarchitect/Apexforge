"""AFP-P10-T4.11 integrated ApexForge language-server contract.

This module freezes the complete T4 capability surface and the protocol-hardening
boundary. It adds no language syntax and does not widen any same-document or
read-only workspace semantic scope established by T4.1 through T4.10.
"""
from __future__ import annotations

import hashlib
import json
from typing import Final, Mapping

from language_server.completion import CANONICAL_COMPLETION_SHA256
from language_server.definition import CANONICAL_DEFINITION_SHA256
from language_server.diagnostics import CANONICAL_LSP_DIAGNOSTICS_SHA256
from language_server.formatting import CANONICAL_FORMATTING_SHA256
from language_server.hover import CANONICAL_HOVER_SHA256
from language_server.references import CANONICAL_REFERENCES_SHA256
from language_server.rename import CANONICAL_RENAME_SHA256
from language_server.symbols import CANONICAL_DOCUMENT_SYMBOLS_SHA256
from language_server.workspace_symbols import CANONICAL_WORKSPACE_SYMBOLS_SHA256

P10_T4_INTEGRATION_VERSION: Final[str] = "10-T4.11"
INTEGRATION_SCHEMA: Final[int] = 1
INTEGRATION_KIND: Final[str] = "apexforge.language-server-integration"
CANCEL_REQUEST_METHOD: Final[str] = "$/cancelRequest"
SET_TRACE_METHOD: Final[str] = "$/setTrace"
REQUEST_CANCELLED: Final[int] = -32800
MAX_CANCELLED_REQUEST_IDS: Final[int] = 1024
TRACE_VALUES: Final[tuple[str, ...]] = ("off", "messages", "verbose")

_FROZEN_FOUNDATION_SHA256: Final[str] = "3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d"


def integrated_capabilities() -> dict[str, object]:
    return {'positionEncoding': 'utf-16', 'textDocumentSync': {'openClose': True, 'change': 1, 'save': False}, 'documentSymbolProvider': True, 'hoverProvider': True, 'completionProvider': {'resolveProvider': False, 'triggerCharacters': ['@', ':']}, 'definitionProvider': True, 'referencesProvider': True, 'renameProvider': {'prepareProvider': True}, 'workspaceSymbolProvider': True, 'documentFormattingProvider': True}


def integration_contract() -> Mapping[str, object]:
    return {'schema': 1, 'kind': 'apexforge.language-server-integration', 'integration_version': '10-T4.11', 'lsp_specification': '3.18', 'server': {'name': 'apexforge-language-server', 'version': '0.1.0'}, 'position_encoding': 'utf-16', 'capabilities': {'positionEncoding': 'utf-16', 'textDocumentSync': {'openClose': True, 'change': 1, 'save': False}, 'documentSymbolProvider': True, 'hoverProvider': True, 'completionProvider': {'resolveProvider': False, 'triggerCharacters': ['@', ':']}, 'definitionProvider': True, 'referencesProvider': True, 'renameProvider': {'prepareProvider': True}, 'workspaceSymbolProvider': True, 'documentFormattingProvider': True}, 'feature_methods': ('textDocument/documentSymbol', 'textDocument/hover', 'textDocument/completion', 'textDocument/definition', 'textDocument/references', 'textDocument/prepareRename', 'textDocument/rename', 'workspace/symbol', 'textDocument/formatting'), 'protocol_notifications': ('initialized', 'textDocument/didOpen', 'textDocument/didChange', 'textDocument/didClose', '$/cancelRequest', '$/setTrace', 'exit'), 'hardening': {'request_cancellation': 'client-local rejection plus bounded pre-dispatch server cancellation ledger', 'request_cancelled_code': -32800, 'trace_values': ('off', 'messages', 'verbose'), 'document_state': 'full synchronization with strictly increasing versions', 'notification_errors': 'recorded and isolated without terminating the session', 'unknown_requests': 'method-not-found response', 'unknown_notifications': 'ignored', 'post_exit_messages': 'contained', 'stdio_framing': 'bounded Content-Length messages', 'shutdown': 'shutdown request followed by exit notification'}, 'frozen_feature_sha256': {'foundation': '3297a9ab09f73ac52b2a67a1fd463b281e2ef5d997a1ba0342de8b6ff6e49b4d', 'diagnostics': '7b3ddf129201c64ecc839af197cec945c09388112a8cf080977d43aec9f66a5f', 'document_symbols': 'f4c337b1bbaab80093bb765323e27d3583609e4e0e229685a4aad9b82153484e', 'hover': 'c3038a06ccd7edc573571df165063d7d2eefb471748f23c40e80b4bc7b6a6e94', 'completion': '8a6054d257a8b98c1a64584c7c8b9f9a5416a62769c11a500ab34afd333f21c5', 'definition': '6a8c78f39e5f265bc2f8c1c9b1085834570712f4607cf09ce95d6464b1b647cd', 'references': '183f9e12a4907b3a00911d5ef693934a187d1a4478995f0ccd19080cd2bc4c30', 'rename': 'ab631c77123a367b6feb2713e3afa250ab9c7817aef3761a9f905dfdfccdc510', 'workspace_symbols': 'b163f9c607f9c592d3e1371788f99fc0ebaa1f271bc6e17ae183149de82ccf85', 'formatting': '63ac984979dd14832dd7d69490176a6e877c867c00c30116636d6c6e5fef3e4b'}, 'features_deferred': ('concurrent_server_request_execution', 'cross_file_definition', 'workspace_references', 'cross_file_rename', 'range_formatting', 'format_on_type', 'persistent_workspace_index')}


def integration_fingerprint() -> str:
    payload = json.dumps(
        integration_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_INTEGRATION_SHA256: Final[str] = "c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897"


def verify_frozen_feature_hashes() -> bool:
    observed = {
        "foundation": _FROZEN_FOUNDATION_SHA256,
        "diagnostics": CANONICAL_LSP_DIAGNOSTICS_SHA256,
        "document_symbols": CANONICAL_DOCUMENT_SYMBOLS_SHA256,
        "hover": CANONICAL_HOVER_SHA256,
        "completion": CANONICAL_COMPLETION_SHA256,
        "definition": CANONICAL_DEFINITION_SHA256,
        "references": CANONICAL_REFERENCES_SHA256,
        "rename": CANONICAL_RENAME_SHA256,
        "workspace_symbols": CANONICAL_WORKSPACE_SYMBOLS_SHA256,
        "formatting": CANONICAL_FORMATTING_SHA256,
    }
    expected = integration_contract()["frozen_feature_sha256"]
    return observed == expected


__all__ = (
    "CANONICAL_INTEGRATION_SHA256",
    "CANCEL_REQUEST_METHOD",
    "INTEGRATION_KIND",
    "INTEGRATION_SCHEMA",
    "MAX_CANCELLED_REQUEST_IDS",
    "P10_T4_INTEGRATION_VERSION",
    "REQUEST_CANCELLED",
    "SET_TRACE_METHOD",
    "TRACE_VALUES",
    "integrated_capabilities",
    "integration_contract",
    "integration_fingerprint",
    "verify_frozen_feature_hashes",
)
