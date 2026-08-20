"""Deterministic TAM production from existing canonical compiler evidence.

P11-TAM-C introduced pure SourceMap adapters. P11-TAM-D extends the same
observational layer to frozen declaration ownership and declared identity
metadata. No producer in this module instruments or executes the compiler.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Dict, List, Tuple

from language.compiler import SourceMap, SourceMapEntry
from language.declarations import ProjectDeclarationOwner, ProjectDeclarationOwnership
from language.identities import ProjectDeclaredIdentity, ProjectIdentityIndex
from language.source import SourceSpan

from .model import TraceDomain, TraceIdentity, TraceMap, TraceRecord


_SOURCE_DOMAIN = TraceDomain("source")
_DECLARATION_DOMAIN = TraceDomain("declaration")
_OWNERSHIP_DOMAIN = TraceDomain("ownership")
_TRANSFORMATION_DOMAIN = TraceDomain("transformation")


def _require_index(value: object) -> int:
    if type(value) is not int:
        raise TypeError("entry_index must be an exact int")
    if value < 0:
        raise ValueError("entry_index must be non-negative")
    return value


def _position_key(position: object) -> str:
    line = getattr(position, "line")
    column = getattr(position, "column")
    offset = getattr(position, "offset", None)
    return "{}:{}:{}".format(line, column, "" if offset is None else offset)


def _span_key(span: SourceSpan) -> str:
    if not isinstance(span, SourceSpan):
        raise TypeError("span must be SourceSpan")
    return "{}|{}|{}".format(
        span.source_name,
        _position_key(span.start),
        _position_key(span.end),
    )


def _digest_identity(prefix: str, parts: Tuple[str, ...]) -> TraceIdentity:
    payload = "\x1f".join((prefix,) + parts).encode("utf-8")
    digest = sha256(payload).hexdigest()
    return TraceIdentity("tam:{}:{}".format(prefix, digest))


def trace_identity_for_source_span(span: SourceSpan) -> TraceIdentity:
    """Return the deterministic TAM identity for an existing source span."""

    return _digest_identity("source", (_span_key(span),))


def trace_identity_for_source_map_entry(
    entry: SourceMapEntry,
    *,
    entry_index: int,
) -> TraceIdentity:
    """Return the deterministic TAM identity for one ordered SourceMap entry."""

    if not isinstance(entry, SourceMapEntry):
        raise TypeError("entry must be SourceMapEntry")
    selected_index = _require_index(entry_index)
    return _digest_identity(
        "source-map-entry",
        (
            str(selected_index),
            entry.air_id,
            _span_key(entry.span),
        ),
    )


def trace_map_from_source_map(source_map: SourceMap) -> TraceMap:
    """Project an existing SourceMap into immutable observational TAM records.

    Every distinct source span produces one source-domain record. Every
    SourceMapEntry produces one transformation-domain record that references
    the existing AIR ID and exact SourceSpan. Source records are emitted at
    the first occurrence of their span; transformation records preserve
    SourceMap entry order.
    """

    if not isinstance(source_map, SourceMap):
        raise TypeError("source_map must be SourceMap")

    entries = tuple(source_map.entries)
    if not entries:
        return TraceMap()

    entry_ids = tuple(
        trace_identity_for_source_map_entry(entry, entry_index=index)
        for index, entry in enumerate(entries)
    )

    downstream_by_source: Dict[TraceIdentity, List[TraceIdentity]] = {}
    source_span_by_id: Dict[TraceIdentity, SourceSpan] = {}

    for entry, entry_id in zip(entries, entry_ids):
        source_id = trace_identity_for_source_span(entry.span)
        if source_id not in downstream_by_source:
            downstream_by_source[source_id] = []
            source_span_by_id[source_id] = entry.span
        downstream_by_source[source_id].append(entry_id)

    records: List[TraceRecord] = []
    emitted_sources = set()

    for entry, entry_id in zip(entries, entry_ids):
        source_id = trace_identity_for_source_span(entry.span)

        if source_id not in emitted_sources:
            records.append(
                TraceRecord(
                    trace_id=source_id,
                    domain=_SOURCE_DOMAIN,
                    producer="language.source",
                    owner="language.source",
                    representation="source-span",
                    source_span=source_span_by_id[source_id],
                    downstream_trace_ids=tuple(
                        downstream_by_source[source_id]
                    ),
                )
            )
            emitted_sources.add(source_id)

        records.append(
            TraceRecord(
                trace_id=entry_id,
                domain=_TRANSFORMATION_DOMAIN,
                producer="language.compiler",
                owner="language.compiler",
                representation="source-map-entry",
                source_span=entry.span,
                canonical_identity=entry.air_id,
                upstream_trace_ids=(source_id,),
            )
        )

    return TraceMap(tuple(records))


def trace_record_from_declaration_owner(
    declaration: ProjectDeclarationOwner,
    *,
    declaration_index: int,
) -> TraceRecord:
    """Project one frozen declaration-ownership record into TAM evidence."""

    if type(declaration) is not ProjectDeclarationOwner:
        raise TypeError("declaration must be ProjectDeclarationOwner")
    selected_index = _require_index(declaration_index)
    trace_id = _digest_identity(
        "declaration-owner",
        (
            str(selected_index),
            declaration.kind,
            declaration.air_id,
            declaration.source_name,
            "" if declaration.module_name is None else declaration.module_name,
            _span_key(declaration.span),
        ),
    )
    return TraceRecord(
        trace_id=trace_id,
        domain=_OWNERSHIP_DOMAIN,
        producer="language.declarations",
        owner="language.declarations",
        representation="project-declaration-owner",
        source_span=declaration.span,
        canonical_identity=declaration.air_id,
    )


def trace_record_from_declared_identity(
    identity: ProjectDeclaredIdentity,
    *,
    identity_index: int,
) -> TraceRecord:
    """Project one frozen declared-identity record into TAM evidence."""

    if type(identity) is not ProjectDeclaredIdentity:
        raise TypeError("identity must be ProjectDeclaredIdentity")
    selected_index = _require_index(identity_index)
    trace_id = _digest_identity(
        "declared-identity",
        (
            str(selected_index),
            identity.kind,
            identity.declared_name,
            identity.current_air_id,
            identity.source_name,
            "" if identity.module_name is None else identity.module_name,
            identity.qualified_display_name,
            _span_key(identity.span),
        ),
    )
    return TraceRecord(
        trace_id=trace_id,
        domain=_DECLARATION_DOMAIN,
        producer="language.identities",
        owner="language.identities",
        representation="project-declared-identity",
        source_span=identity.span,
        canonical_identity=identity.current_air_id,
    )


def trace_map_from_declaration_identity_indexes(
    declaration_ownership: ProjectDeclarationOwnership,
    identity_index: ProjectIdentityIndex,
) -> TraceMap:
    """Project frozen ownership and identity indexes into deterministic TAM.

    Ownership tuple order is preserved first. Declared-identity tuple order is
    preserved second. No resolution, joining, collapsing, or semantic inference
    is performed between records that happen to reference the same AIR ID.
    """

    if type(declaration_ownership) is not ProjectDeclarationOwnership:
        raise TypeError(
            "declaration_ownership must be ProjectDeclarationOwnership"
        )
    if type(identity_index) is not ProjectIdentityIndex:
        raise TypeError("identity_index must be ProjectIdentityIndex")

    ownership_records = tuple(
        trace_record_from_declaration_owner(
            declaration,
            declaration_index=index,
        )
        for index, declaration in enumerate(declaration_ownership.declarations)
    )
    identity_records = tuple(
        trace_record_from_declared_identity(
            identity,
            identity_index=index,
        )
        for index, identity in enumerate(identity_index.identities)
    )
    return TraceMap(ownership_records + identity_records)


__all__ = (
    "trace_identity_for_source_map_entry",
    "trace_identity_for_source_span",
    "trace_map_from_source_map",
    "trace_map_from_declaration_identity_indexes",
    "trace_record_from_declaration_owner",
    "trace_record_from_declared_identity",
)