"""Deterministic TAM production from existing canonical source-map evidence.

P11-TAM-C is a pure adapter layer. It consumes frozen SourceSpan, SourceMapEntry,
and SourceMap evidence and emits frozen P11-TAM-B TraceRecord/TraceMap values.
It does not instrument or execute the compiler.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Dict, List, Tuple

from language.compiler import SourceMap, SourceMapEntry
from language.source import SourceSpan

from .model import TraceDomain, TraceIdentity, TraceMap, TraceRecord


_SOURCE_DOMAIN = TraceDomain("source")
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


__all__ = (
    "trace_identity_for_source_map_entry",
    "trace_identity_for_source_span",
    "trace_map_from_source_map",
)