"""AFP-P10-T4.8 ApexForge safe same-document rename.

Rename consumes the exact reference target produced by the T4.8 references
analyzer. Only lexically complete same-document namespaces are renameable;
workspace-visible declarations remain protected until cross-file indexing.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Final, Mapping, Optional

from language_server.diagnostics import offset_to_lsp_position
from language_server.references import ReferenceTarget, resolve_reference_target
from language_server.definition import _definition_index
from type_system.model import BUILTIN_TYPES


P10_T4_RENAME_VERSION: Final[str] = "10-T4.8"
RENAME_SCHEMA: Final[int] = 1
RENAME_KIND: Final[str] = "apexforge.language-server-rename"
PREPARE_RENAME_METHOD: Final[str] = "textDocument/prepareRename"
RENAME_METHOD: Final[str] = "textDocument/rename"

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_RENAMEABLE_NAMESPACES: Final[frozenset[str]] = frozenset(
    {"type", "value", "state", "event", "cause", "path"}
)
_RESERVED_WORDS: Final[frozenset[str]] = frozenset(
    {
        "module", "import", "function", "directive", "workflow", "authority",
        "role", "principal", "state", "event", "cause", "requires",
        "capability", "extends", "path", "add", "set", "emit", "message",
        "invoke", "when", "otherwise", "let", "return", "true", "false",
        *(apex_type.name for apex_type in BUILTIN_TYPES),
    }
)


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _renameable(target: Optional[ReferenceTarget]) -> bool:
    return target is not None and target.namespace in _RENAMEABLE_NAMESPACES


def _range(text: str, start: int, end: int) -> dict[str, object]:
    return {
        "start": offset_to_lsp_position(text, start),
        "end": offset_to_lsp_position(text, end),
    }


def prepare_rename(
    uri: str,
    text: str,
    position: Mapping[str, object],
) -> Optional[dict[str, object]]:
    """Return the selected rename range and placeholder, or null if unsafe."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    target = resolve_reference_target(selected_uri, source, position)
    if not _renameable(target):
        return None
    assert target is not None
    selected = next(
        (
            occurrence
            for occurrence in target.occurrences
            if occurrence[0] <= _position_offset(source, position) < occurrence[1]
        ),
        (target.target_start, target.target_end),
    )
    return {
        "range": _range(source, selected[0], selected[1]),
        "placeholder": target.name,
    }


def _position_offset(text: str, position: Mapping[str, object]) -> int:
    from language_server.hover import lsp_position_to_offset
    return lsp_position_to_offset(text, position)


def _validate_new_name(new_name: object) -> str:
    if type(new_name) is not str or not new_name:
        raise ValueError("newName must be a non-empty string.")
    if _IDENTIFIER.fullmatch(new_name) is None:
        raise ValueError(
            "newName must be an ApexForge identifier matching "
            "[A-Za-z_][A-Za-z0-9_]*."
        )
    if new_name in _RESERVED_WORDS:
        raise ValueError(f"newName {new_name!r} is reserved by ApexForge.")
    return new_name


def _reject_collision(uri: str, text: str, target: ReferenceTarget, new_name: str) -> None:
    if new_name == target.name:
        return
    index = _definition_index(uri, text)
    for definition in index.definitions:
        if (
            definition.namespace == target.namespace
            and definition.name == new_name
            and not (
                definition.start == target.target_start
                and definition.end == target.target_end
            )
        ):
            raise ValueError(
                f"newName {new_name!r} collides with an existing "
                f"{target.namespace} declaration."
            )


def rename(
    uri: str,
    text: str,
    position: Mapping[str, object],
    new_name: object,
) -> Optional[dict[str, object]]:
    """Return one same-document WorkspaceEdit, or null when rename is unsafe."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    replacement = _validate_new_name(new_name)
    target = resolve_reference_target(selected_uri, source, position)
    if not _renameable(target):
        return None
    assert target is not None
    _reject_collision(selected_uri, source, target, replacement)

    edits = [
        {
            "range": _range(source, start, end),
            "newText": replacement,
        }
        for start, end in target.occurrences
    ]
    return {"changes": {selected_uri: edits}}


def rename_contract() -> dict[str, object]:
    return {
        "schema": RENAME_SCHEMA,
        "kind": RENAME_KIND,
        "rename_version": P10_T4_RENAME_VERSION,
        "methods": (PREPARE_RENAME_METHOD, RENAME_METHOD),
        "result": "prepare range | WorkspaceEdit | null",
        "position_encoding": "utf-16",
        "scope": "one open document",
        "edit_source": "exact T4.8 reference set",
        "renameable_namespaces": tuple(sorted(_RENAMEABLE_NAMESPACES)),
        "protected_namespaces": (
            "module",
            "callable",
            "directive",
            "workflow",
            "authority",
            "capability",
            "role",
            "principal",
        ),
        "safety": (
            "identifier_validation",
            "reserved_word_rejection",
            "same_namespace_collision_rejection",
            "prepareRename_required",
        ),
        "invalid_source": "null; diagnostics remain T4.2 responsibility",
        "features_deferred": (
            "cross_file_rename",
            "workspace_indexing",
            "file_and_module_rename",
            "workspace_visible_declaration_rename",
            "workspace_symbols",
            "formatting",
            "type_inference",
        ),
    }


def rename_fingerprint() -> str:
    payload = json.dumps(
        rename_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_RENAME_SHA256: Final[str] = "ab631c77123a367b6feb2713e3afa250ab9c7817aef3761a9f905dfdfccdc510"


__all__ = (
    "CANONICAL_RENAME_SHA256",
    "P10_T4_RENAME_VERSION",
    "PREPARE_RENAME_METHOD",
    "RENAME_KIND",
    "RENAME_METHOD",
    "RENAME_SCHEMA",
    "prepare_rename",
    "rename",
    "rename_contract",
    "rename_fingerprint",
)
