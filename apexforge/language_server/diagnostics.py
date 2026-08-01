"""AFP-P10-T4.2 live ApexForge syntax diagnostics for LSP clients.

The analyzer reuses the frozen module-header, lexer, and parser pipeline. It
projects canonical ``BuildDiagnostic`` values into Language Server Protocol
``Diagnostic`` objects without compiling, linking, or executing source text.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final, Mapping, Optional

from language.diagnostics import BuildDiagnostic, diagnostics_from_exception
from language.modules import parse_module_source
from language.parser import parse
from language.source import SourceSpan


P10_T4_LSP_DIAGNOSTICS_VERSION: Final[str] = "10-T4.2"
LSP_DIAGNOSTICS_SCHEMA: Final[int] = 1
LSP_DIAGNOSTICS_KIND: Final[str] = "apexforge.language-server-diagnostics"
LSP_DIAGNOSTIC_SOURCE: Final[str] = "apexforge"
PUBLISH_DIAGNOSTICS_METHOD: Final[str] = "textDocument/publishDiagnostics"

LSP_DIAGNOSTIC_ERROR: Final[int] = 1
LSP_DIAGNOSTIC_WARNING: Final[int] = 2
LSP_DIAGNOSTIC_INFORMATION: Final[int] = 3

_SEVERITY_TO_LSP: Final[Mapping[str, int]] = {
    "error": LSP_DIAGNOSTIC_ERROR,
    "warning": LSP_DIAGNOSTIC_WARNING,
    "info": LSP_DIAGNOSTIC_INFORMATION,
}


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _utf16_length(value: str) -> int:
    """Return the number of UTF-16 code units in one Python string."""

    return len(value.encode("utf-16-le")) // 2


def offset_to_lsp_position(text: str, offset: int) -> dict[str, int]:
    """Convert a zero-based Python character offset to an LSP UTF-16 position."""

    source = _require_text(text, "text")
    if type(offset) is not int or isinstance(offset, bool):
        raise TypeError("offset must be an integer.")
    if offset < 0 or offset > len(source):
        raise ValueError(f"offset {offset} lies outside 0..{len(source)}.")

    line = source.count("\n", 0, offset)
    line_start = source.rfind("\n", 0, offset) + 1
    character = _utf16_length(source[line_start:offset])
    return {
        "line": line,
        "character": character,
    }


def span_to_lsp_range(text: str, span: Optional[SourceSpan]) -> dict[str, object]:
    """Project one end-exclusive ApexForge span into an LSP range."""

    source = _require_text(text, "text")
    if span is None:
        origin = {"line": 0, "character": 0}
        return {"start": origin, "end": dict(origin)}
    if not isinstance(span, SourceSpan):
        raise TypeError("span must be SourceSpan or None.")

    return {
        "start": offset_to_lsp_position(source, span.start.offset),
        "end": offset_to_lsp_position(source, span.end.offset),
    }


def diagnostic_to_lsp(
    diagnostic: BuildDiagnostic,
    *,
    uri: str,
    text: str,
    include_related_information: bool = False,
) -> dict[str, object]:
    """Convert one canonical ApexForge diagnostic to an LSP Diagnostic."""

    if not isinstance(diagnostic, BuildDiagnostic):
        raise TypeError("diagnostic must be BuildDiagnostic.")
    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")

    value: dict[str, object] = {
        "range": span_to_lsp_range(source, diagnostic.span),
        "severity": _SEVERITY_TO_LSP[diagnostic.severity],
        "code": diagnostic.code,
        "source": LSP_DIAGNOSTIC_SOURCE,
        "message": diagnostic.message,
        "data": {
            "stage": diagnostic.stage,
        },
    }

    if include_related_information and diagnostic.related_spans:
        value["relatedInformation"] = [
            {
                "location": {
                    "uri": selected_uri,
                    "range": span_to_lsp_range(source, related_span),
                },
                "message": f"Related location for {diagnostic.code}.",
            }
            for related_span in diagnostic.related_spans
        ]

    return value


def analyze_document(
    uri: str,
    text: str,
    *,
    include_related_information: bool = False,
) -> tuple[dict[str, object], ...]:
    """Run the frozen module/lexer/parser pipeline and return LSP diagnostics."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")

    try:
        module_source = parse_module_source(selected_uri, source)
        parse(module_source.masked_source, source_name=selected_uri)
    except Exception as error:
        diagnostics = diagnostics_from_exception(error)
        if not diagnostics:
            raise
        return tuple(
            diagnostic_to_lsp(
                diagnostic,
                uri=selected_uri,
                text=source,
                include_related_information=include_related_information,
            )
            for diagnostic in diagnostics
        )

    return ()


def publish_diagnostics_notification(
    uri: str,
    diagnostics: tuple[Mapping[str, object], ...],
    *,
    version: Optional[int] = None,
) -> dict[str, object]:
    """Create one deterministic ``textDocument/publishDiagnostics`` notification."""

    selected_uri = _require_uri(uri, "uri")
    normalized = tuple(dict(item) for item in diagnostics)
    if version is not None and type(version) is not int:
        raise TypeError("publishDiagnostics version must be an int or None.")

    params: dict[str, object] = {
        "uri": selected_uri,
        "diagnostics": list(normalized),
    }
    if version is not None:
        params["version"] = version

    return {
        "jsonrpc": "2.0",
        "method": PUBLISH_DIAGNOSTICS_METHOD,
        "params": params,
    }


def diagnostics_contract() -> dict[str, object]:
    """Return the deterministic public AFP-P10-T4.2 diagnostics contract."""

    return {
        "schema": LSP_DIAGNOSTICS_SCHEMA,
        "kind": LSP_DIAGNOSTICS_KIND,
        "diagnostics_version": P10_T4_LSP_DIAGNOSTICS_VERSION,
        "method": PUBLISH_DIAGNOSTICS_METHOD,
        "source": LSP_DIAGNOSTIC_SOURCE,
        "position_encoding": "utf-16",
        "pipeline": (
            "module_headers",
            "lexer",
            "parser",
        ),
        "triggers": (
            "textDocument/didOpen",
            "textDocument/didChange",
            "textDocument/didClose",
        ),
        "activation": "client textDocument.publishDiagnostics capability",
        "document_sync": "full",
        "close_behavior": "publish empty diagnostics without a version",
        "severity": {
            "error": LSP_DIAGNOSTIC_ERROR,
            "warning": LSP_DIAGNOSTIC_WARNING,
            "info": LSP_DIAGNOSTIC_INFORMATION,
        },
        "features_deferred": (
            "compile_diagnostics",
            "project_diagnostics",
            "completion",
            "hover",
            "definition",
            "references",
            "formatting",
        ),
    }


def diagnostics_fingerprint() -> str:
    payload = json.dumps(
        diagnostics_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Filled after the public projection above is serialized. The T4.2 smoke test
# rejects accidental changes while the frozen T4.1 foundation remains intact.
CANONICAL_LSP_DIAGNOSTICS_SHA256: Final[str] = "7b3ddf129201c64ecc839af197cec945c09388112a8cf080977d43aec9f66a5f"


__all__ = (
    "CANONICAL_LSP_DIAGNOSTICS_SHA256",
    "LSP_DIAGNOSTICS_KIND",
    "LSP_DIAGNOSTICS_SCHEMA",
    "LSP_DIAGNOSTIC_ERROR",
    "LSP_DIAGNOSTIC_INFORMATION",
    "LSP_DIAGNOSTIC_SOURCE",
    "LSP_DIAGNOSTIC_WARNING",
    "P10_T4_LSP_DIAGNOSTICS_VERSION",
    "PUBLISH_DIAGNOSTICS_METHOD",
    "analyze_document",
    "diagnostic_to_lsp",
    "diagnostics_contract",
    "diagnostics_fingerprint",
    "offset_to_lsp_position",
    "publish_diagnostics_notification",
    "span_to_lsp_range",
)
