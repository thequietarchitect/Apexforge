"""Capture-layer incremental reuse for documents, tokens, and formatting.

P11.12C binds the minimal P11.12B cache model to existing Capture owners.
Reuse is explicit through an optional single cached entry; no store,
persistence, project-builder integration, or semantic ownership is introduced.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Mapping, Optional, Tuple

from incremental_cache.model import (
    CACHE_SCHEMA_VERSION,
    CacheEntry,
    CacheIdentity,
    cache_fingerprint,
)
from language.lexer import Token, lex as _lex
from language_server.formatting import (
    format_document as _format_document,
    formatting_fingerprint,
)
from tooling.project_loader import LoadedProjectSource


_CAPTURE_LAYER = "capture"
_DOCUMENT_KIND = "document"
_TOKEN_KIND = "tokens"
_FORMATTING_KIND = "formatting"

_DOCUMENT_OWNER = "tooling.project_loader"
_TOKEN_OWNER = "language.lexer"
_FORMATTING_OWNER = "language_server.formatting"


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise TypeError("capture configuration/value must be JSON-safe") from exc
    return text.encode("utf-8")


def _require_source(source: object) -> LoadedProjectSource:
    if type(source) is not LoadedProjectSource:
        raise TypeError("source must be exact LoadedProjectSource")
    return source


def _require_cached(cached: object) -> Optional[CacheEntry]:
    if cached is None:
        return None
    if type(cached) is not CacheEntry:
        raise TypeError("cached must be None or exact CacheEntry")
    return cached


def _require_bool(value: object, owner: str) -> bool:
    if type(value) is not bool:
        raise TypeError("{} must be exact bool".format(owner))
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be exact str".format(owner))
    if not value:
        raise ValueError("{} must be non-empty".format(owner))
    return value


_FROZEN_JSON_MAPPING = "apexforge.incremental-cache/frozen-json-map/v1"
_FROZEN_JSON_SEQUENCE = "apexforge.incremental-cache/frozen-json-sequence/v1"


def _freeze_json(value: object) -> object:
    if value is None or type(value) in (str, int, float, bool):
        return value
    if type(value) in (list, tuple):
        return (
            _FROZEN_JSON_SEQUENCE,
            tuple(_freeze_json(item) for item in value),
        )
    if isinstance(value, Mapping):
        items = []
        for key in sorted(value):
            if type(key) is not str:
                raise TypeError("formatting edit mapping keys must be strings")
            items.append((key, _freeze_json(value[key])))
        return (
            _FROZEN_JSON_MAPPING,
            tuple(items),
        )
    raise TypeError(
        "formatting edits must contain only JSON-compatible values"
    )


def _thaw_json(value: object) -> object:
    if value is None or type(value) in (str, int, float, bool):
        return value
    if type(value) is tuple and len(value) == 2:
        tag, payload = value
        if tag == _FROZEN_JSON_SEQUENCE:
            if type(payload) is not tuple:
                raise TypeError(
                    "captured formatting sequence payload must be exact tuple"
                )
            return [_thaw_json(item) for item in payload]
        if tag == _FROZEN_JSON_MAPPING:
            if type(payload) is not tuple:
                raise TypeError(
                    "captured formatting mapping payload must be exact tuple"
                )
            result = {}
            for item in payload:
                if (
                    type(item) is not tuple
                    or len(item) != 2
                    or type(item[0]) is not str
                ):
                    raise TypeError(
                        "captured formatting mapping item is invalid"
                    )
                key, nested = item
                if key in result:
                    raise TypeError(
                        "captured formatting mapping contains duplicate key"
                    )
                result[key] = _thaw_json(nested)
            return result
    raise TypeError("captured formatting value is not canonical frozen JSON")


def _token_artifact_bytes(tokens: Tuple[Token, ...]) -> bytes:
    if type(tokens) is not tuple:
        raise TypeError("tokens must be exact tuple")
    payload = []
    for token in tokens:
        if type(token) is not Token:
            raise TypeError("tokens must contain exact Token values")
        payload.append(asdict(token))
    return _canonical_json_bytes(payload)


def _formatting_configuration_bytes(
    options: Mapping[str, object],
) -> bytes:
    if not isinstance(options, Mapping):
        raise TypeError("formatting options must be a mapping")

    relevant = {}
    for key in ("insertSpaces", "tabSize"):
        if key in options:
            relevant[key] = options[key]

    return _canonical_json_bytes(
        {
            "formatter_fingerprint": formatting_fingerprint(),
            "options": relevant,
        }
    )


def document_capture_identity(
    source: LoadedProjectSource,
) -> CacheIdentity:
    """Build the raw-document Capture identity for one loaded source."""

    selected = _require_source(source)
    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=_CAPTURE_LAYER,
        artifact_kind=_DOCUMENT_KIND,
        owner=_DOCUMENT_OWNER,
        subject=selected.name,
        input_fingerprint=cache_fingerprint(selected.source_bytes),
        configuration_fingerprint=cache_fingerprint(b""),
    )


def capture_document(
    source: LoadedProjectSource,
    *,
    cached: Optional[CacheEntry] = None,
) -> CacheEntry:
    """Reuse or wrap one exact loaded-source snapshot."""

    selected = _require_source(source)
    existing = _require_cached(cached)
    identity = document_capture_identity(selected)

    if (
        existing is not None
        and existing.identity == identity
        and type(existing.value) is LoadedProjectSource
        and existing.value == selected
        and existing.artifact_fingerprint
        == cache_fingerprint(existing.value.source_bytes)
    ):
        return existing

    return CacheEntry(
        identity=identity,
        artifact_fingerprint=identity.input_fingerprint,
        value=selected,
    )


def token_capture_identity(
    source: LoadedProjectSource,
    *,
    inter_directive_line_comments: bool = False,
) -> CacheIdentity:
    """Build the lexer Capture identity over normalized project-loader text."""

    selected = _require_source(source)
    selected_comments = _require_bool(
        inter_directive_line_comments,
        "inter_directive_line_comments",
    )
    configuration = _canonical_json_bytes(
        {
            "inter_directive_line_comments": selected_comments,
        }
    )
    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=_CAPTURE_LAYER,
        artifact_kind=_TOKEN_KIND,
        owner=_TOKEN_OWNER,
        subject=selected.name,
        input_fingerprint=cache_fingerprint(
            selected.source.encode("utf-8")
        ),
        configuration_fingerprint=cache_fingerprint(configuration),
    )


def capture_tokens(
    source: LoadedProjectSource,
    *,
    inter_directive_line_comments: bool = False,
    cached: Optional[CacheEntry] = None,
) -> CacheEntry:
    """Reuse or produce the canonical lexer token tuple for one source."""

    selected = _require_source(source)
    selected_comments = _require_bool(
        inter_directive_line_comments,
        "inter_directive_line_comments",
    )
    existing = _require_cached(cached)
    identity = token_capture_identity(
        selected,
        inter_directive_line_comments=selected_comments,
    )

    if (
        existing is not None
        and existing.identity == identity
        and type(existing.value) is tuple
    ):
        try:
            existing_bytes = _token_artifact_bytes(existing.value)
        except TypeError:
            existing_bytes = None
        if (
            existing_bytes is not None
            and existing.artifact_fingerprint
            == cache_fingerprint(existing_bytes)
        ):
            return existing

    tokens = tuple(
        _lex(
            selected.source,
            source_name=selected.name,
            inter_directive_line_comments=selected_comments,
        )
    )
    artifact_bytes = _token_artifact_bytes(tokens)
    return CacheEntry(
        identity=identity,
        artifact_fingerprint=cache_fingerprint(artifact_bytes),
        value=tokens,
    )


def formatting_capture_identity(
    uri: str,
    text: str,
    options: Mapping[str, object],
) -> CacheIdentity:
    """Build the formatting Capture identity for exact formatter input."""

    selected_uri = _require_text(uri, "uri")
    if type(text) is not str:
        raise TypeError("text must be exact str")
    configuration = _formatting_configuration_bytes(options)
    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=_CAPTURE_LAYER,
        artifact_kind=_FORMATTING_KIND,
        owner=_FORMATTING_OWNER,
        subject=selected_uri,
        input_fingerprint=cache_fingerprint(text.encode("utf-8")),
        configuration_fingerprint=cache_fingerprint(configuration),
    )


def _formatting_value_bytes(value: object) -> bytes:
    thawed = _thaw_json(value)
    if type(thawed) is not list:
        raise TypeError("captured formatting root must thaw to a list")
    if not all(type(item) is dict for item in thawed):
        raise TypeError("captured formatting edits must thaw to dictionaries")
    return _canonical_json_bytes(thawed)


def capture_formatting(
    uri: str,
    text: str,
    options: Mapping[str, object],
    *,
    cached: Optional[CacheEntry] = None,
) -> CacheEntry:
    """Reuse or produce one immutable canonical formatting-edit tuple."""

    existing = _require_cached(cached)
    identity = formatting_capture_identity(uri, text, options)

    if existing is not None and existing.identity == identity:
        try:
            existing_bytes = _formatting_value_bytes(existing.value)
        except TypeError:
            existing_bytes = None
        if (
            existing_bytes is not None
            and existing.artifact_fingerprint
            == cache_fingerprint(existing_bytes)
        ):
            return existing

    edits = _format_document(uri, text, options)
    if type(edits) is not tuple:
        raise TypeError("format_document must return exact tuple")
    if not all(type(edit) is dict for edit in edits):
        raise TypeError("format_document must return tuple of exact dict edits")

    owner_bytes = _canonical_json_bytes(edits)
    frozen = _freeze_json(edits)

    if type(frozen) is not tuple:
        raise TypeError("canonical frozen formatting value must be tuple")

    return CacheEntry(
        identity=identity,
        artifact_fingerprint=cache_fingerprint(owner_bytes),
        value=frozen,
    )


def formatting_edits_from_capture(
    entry: CacheEntry,
) -> Tuple[dict[str, object], ...]:
    """Rehydrate canonical formatting edits from one formatting entry."""

    if type(entry) is not CacheEntry:
        raise TypeError("entry must be exact CacheEntry")
    identity = entry.identity
    if (
        identity.layer_id != _CAPTURE_LAYER
        or identity.artifact_kind != _FORMATTING_KIND
        or identity.owner != _FORMATTING_OWNER
    ):
        raise ValueError("entry is not a formatting Capture entry")

    thawed = _thaw_json(entry.value)
    if type(thawed) is not list or not all(
        type(edit) is dict for edit in thawed
    ):
        raise TypeError("captured formatting value is invalid")

    expected = cache_fingerprint(_canonical_json_bytes(thawed))
    if entry.artifact_fingerprint != expected:
        raise ValueError("captured formatting artifact fingerprint mismatch")

    return tuple(thawed)


__all__ = (
    "document_capture_identity",
    "capture_document",
    "token_capture_identity",
    "capture_tokens",
    "formatting_capture_identity",
    "capture_formatting",
    "formatting_edits_from_capture",
)