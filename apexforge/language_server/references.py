"""AFP-P10-T4.8 ApexForge same-document reference discovery.

The analyzer reuses the exact occurrence graph frozen by T4.7 definition
navigation. It performs no workspace indexing, linking, import resolution,
validation, type inference, rename, or runtime execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Final, Mapping, Optional

from language_server.definition import _definition_index
from language_server.diagnostics import offset_to_lsp_position
from language_server.hover import lsp_position_to_offset


P10_T4_REFERENCES_VERSION: Final[str] = "10-T4.8"
REFERENCES_SCHEMA: Final[int] = 1
REFERENCES_KIND: Final[str] = "apexforge.language-server-references"
REFERENCES_METHOD: Final[str] = "textDocument/references"


@dataclass(frozen=True, order=True)
class ReferenceTarget:
    """One resolved symbol and its exact same-document occurrence set."""

    target_start: int
    target_end: int
    name: str
    namespace: str
    occurrences: tuple[tuple[int, int], ...]


def _require_uri(value: object, owner: str) -> str:
    if type(value) is not str or not value or ":" not in value:
        raise ValueError(f"{owner} must be a non-empty absolute URI.")
    return value


def _require_text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{owner} must be a string.")
    return value


def _selected_occurrence(index: object, offset: int) -> Optional[object]:
    candidates = tuple(
        occurrence
        for occurrence in index.occurrences
        if occurrence.start <= offset < occurrence.end
    )
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            item.end - item.start,
            item.start,
            item.target_start,
            item.namespace,
            item.name,
        ),
    )


def resolve_reference_target(
    uri: str,
    text: str,
    position: Mapping[str, object],
) -> Optional[ReferenceTarget]:
    """Resolve the selected occurrence to the exact T4.7 symbol identity."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    offset = lsp_position_to_offset(source, position)
    index = _definition_index(selected_uri, source)
    selected = _selected_occurrence(index, offset)
    if selected is None:
        return None

    occurrences = tuple(
        sorted(
            {
                (occurrence.start, occurrence.end)
                for occurrence in index.occurrences
                if occurrence.target_start == selected.target_start
                and occurrence.target_end == selected.target_end
                and occurrence.name == selected.name
                and occurrence.namespace == selected.namespace
            }
        )
    )
    if not occurrences:
        return None
    return ReferenceTarget(
        target_start=selected.target_start,
        target_end=selected.target_end,
        name=selected.name,
        namespace=selected.namespace,
        occurrences=occurrences,
    )


def references(
    uri: str,
    text: str,
    position: Mapping[str, object],
    context: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """Return deterministic same-document LSP Locations for one symbol."""

    selected_uri = _require_uri(uri, "uri")
    source = _require_text(text, "text")
    if type(context) is not dict:
        raise TypeError("context must be an object.")
    include_declaration = context.get("includeDeclaration")
    if type(include_declaration) is not bool:
        raise ValueError("context.includeDeclaration must be a boolean.")

    target = resolve_reference_target(selected_uri, source, position)
    if target is None:
        return ()

    locations: list[dict[str, object]] = []
    for start, end in target.occurrences:
        if (
            not include_declaration
            and start == target.target_start
            and end == target.target_end
        ):
            continue
        locations.append(
            {
                "uri": selected_uri,
                "range": {
                    "start": offset_to_lsp_position(source, start),
                    "end": offset_to_lsp_position(source, end),
                },
            }
        )
    return tuple(locations)


def references_contract() -> dict[str, object]:
    return {
        "schema": REFERENCES_SCHEMA,
        "kind": REFERENCES_KIND,
        "references_version": P10_T4_REFERENCES_VERSION,
        "method": REFERENCES_METHOD,
        "result": "Location[]",
        "position_encoding": "utf-16",
        "scope": "one open document",
        "identity_source": "exact T4.7 definition occurrence graph",
        "include_declaration": "honored exactly",
        "targets": (
            "function_type_parameters",
            "function_parameters_and_prior_locals",
            "recursive_function_calls",
            "directive_states",
            "directive_events",
            "cause_and_path_declarations",
            "supported_declaration_names",
        ),
        "invalid_source": "empty result; diagnostics remain T4.2 responsibility",
        "unresolved_reference": "empty result",
        "ordering": "source range ascending",
        "features_deferred": (
            "cross_file_references",
            "workspace_indexing",
            "import_resolution",
            "workflow_and_directive_target_resolution",
            "authority_role_and_capability_resolution",
            "rename",
            "workspace_symbols",
            "formatting",
            "type_inference",
        ),
    }


def references_fingerprint() -> str:
    payload = json.dumps(
        references_contract(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


CANONICAL_REFERENCES_SHA256: Final[str] = "183f9e12a4907b3a00911d5ef693934a187d1a4478995f0ccd19080cd2bc4c30"


__all__ = (
    "CANONICAL_REFERENCES_SHA256",
    "P10_T4_REFERENCES_VERSION",
    "REFERENCES_KIND",
    "REFERENCES_METHOD",
    "REFERENCES_SCHEMA",
    "ReferenceTarget",
    "references",
    "references_contract",
    "references_fingerprint",
    "resolve_reference_target",
)
