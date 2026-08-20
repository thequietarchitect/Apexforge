"""Minimal immutable Compiler Token Analysis Map (TAM) records.

P11-TAM-B defines trace data only. It does not instrument the compiler,
interpret semantics, perform resolution, or execute runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from language.source import SourceSpan


TRACE_SCHEMA_VERSION = 1
TRACE_DOMAIN_IDS: Tuple[str, ...] = (
    "source",
    "token",
    "declaration",
    "reference",
    "scope",
    "type",
    "authority",
    "narrative",
    "ownership",
    "transformation",
)


def _text(value: object, owner: str) -> str:
    if type(value) is not str:
        raise TypeError("{} must be an exact str".format(owner))
    if not value or value != value.strip():
        raise ValueError("{} must be a non-empty canonical string".format(owner))
    return value


def _optional_text(value: object, owner: str) -> Optional[str]:
    if value is None:
        return None
    return _text(value, owner)


def _trace_id_tuple(value: object, owner: str) -> Tuple["TraceIdentity", ...]:
    if type(value) is not tuple:
        raise TypeError("{} must be an exact tuple".format(owner))
    for index, item in enumerate(value):
        if type(item) is not TraceIdentity:
            raise TypeError(
                "{}[{}] must be TraceIdentity".format(owner, index)
            )
    if len(set(value)) != len(value):
        raise ValueError("{} cannot contain duplicate trace identities".format(owner))
    return value


def _provenance_tuple(value: object, owner: str) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("{} must be an exact tuple".format(owner))
    normalized = []
    for index, item in enumerate(value):
        normalized.append(_text(item, "{}[{}]".format(owner, index)))
    if len(set(normalized)) != len(normalized):
        raise ValueError("{} cannot contain duplicate entries".format(owner))
    return tuple(normalized)


@dataclass(frozen=True, order=True)
class TraceDomain:
    """Canonical TAM traceability domain."""

    canonical_id: str

    def __post_init__(self) -> None:
        selected = _text(self.canonical_id, "TraceDomain.canonical_id")
        if selected not in TRACE_DOMAIN_IDS:
            raise ValueError(
                "TraceDomain.canonical_id must be one of the canonical TAM domains"
            )
        object.__setattr__(self, "canonical_id", selected)


CANONICAL_TRACE_DOMAINS: Tuple[TraceDomain, ...] = tuple(
    TraceDomain(domain_id) for domain_id in TRACE_DOMAIN_IDS
)


@dataclass(frozen=True, order=True)
class TraceIdentity:
    """Stable TAM-local identity for one observational trace record."""

    value: str

    def __post_init__(self) -> None:
        selected = _text(self.value, "TraceIdentity.value")
        object.__setattr__(self, "value", selected)


@dataclass(frozen=True)
class TraceRecord:
    """One immutable observational relationship record.

    Payload semantics remain owned by the producing ApexForge subsystem.
    """

    trace_id: TraceIdentity
    domain: TraceDomain
    producer: str
    owner: str
    representation: str
    schema_version: int = TRACE_SCHEMA_VERSION
    source_span: Optional[SourceSpan] = None
    canonical_identity: Optional[str] = None
    provenance: Tuple[str, ...] = ()
    upstream_trace_ids: Tuple[TraceIdentity, ...] = ()
    downstream_trace_ids: Tuple[TraceIdentity, ...] = ()

    def __post_init__(self) -> None:
        if type(self.trace_id) is not TraceIdentity:
            raise TypeError("TraceRecord.trace_id must be TraceIdentity")
        if type(self.domain) is not TraceDomain:
            raise TypeError("TraceRecord.domain must be TraceDomain")

        object.__setattr__(
            self,
            "producer",
            _text(self.producer, "TraceRecord.producer"),
        )
        object.__setattr__(
            self,
            "owner",
            _text(self.owner, "TraceRecord.owner"),
        )
        object.__setattr__(
            self,
            "representation",
            _text(self.representation, "TraceRecord.representation"),
        )

        if type(self.schema_version) is not int:
            raise TypeError("TraceRecord.schema_version must be an exact int")
        if self.schema_version < 1:
            raise ValueError("TraceRecord.schema_version must be positive")

        if self.source_span is not None and not isinstance(
            self.source_span,
            SourceSpan,
        ):
            raise TypeError("TraceRecord.source_span must be SourceSpan or None")

        object.__setattr__(
            self,
            "canonical_identity",
            _optional_text(
                self.canonical_identity,
                "TraceRecord.canonical_identity",
            ),
        )
        object.__setattr__(
            self,
            "provenance",
            _provenance_tuple(
                self.provenance,
                "TraceRecord.provenance",
            ),
        )
        object.__setattr__(
            self,
            "upstream_trace_ids",
            _trace_id_tuple(
                self.upstream_trace_ids,
                "TraceRecord.upstream_trace_ids",
            ),
        )
        object.__setattr__(
            self,
            "downstream_trace_ids",
            _trace_id_tuple(
                self.downstream_trace_ids,
                "TraceRecord.downstream_trace_ids",
            ),
        )

        if self.trace_id in self.upstream_trace_ids:
            raise ValueError("TraceRecord cannot list itself as upstream")
        if self.trace_id in self.downstream_trace_ids:
            raise ValueError("TraceRecord cannot list itself as downstream")


@dataclass(frozen=True)
class TraceMap:
    """Immutable ordered collection of TAM records.

    The map preserves supplied record order. It does not infer missing edges,
    perform transitive closure, or require referenced traces to be present.
    """

    records: Tuple[TraceRecord, ...] = ()

    def __post_init__(self) -> None:
        if type(self.records) is not tuple:
            raise TypeError("TraceMap.records must be an exact tuple")
        for index, item in enumerate(self.records):
            if type(item) is not TraceRecord:
                raise TypeError(
                    "TraceMap.records[{}] must be TraceRecord".format(index)
                )

        identities = tuple(item.trace_id for item in self.records)
        if len(set(identities)) != len(identities):
            raise ValueError("TraceMap.records cannot contain duplicate trace identities")

    def find(self, trace_id: TraceIdentity) -> Optional[TraceRecord]:
        if type(trace_id) is not TraceIdentity:
            raise TypeError("TraceMap.find trace_id must be TraceIdentity")
        for record in self.records:
            if record.trace_id == trace_id:
                return record
        return None

    def for_domain(self, domain: TraceDomain) -> Tuple[TraceRecord, ...]:
        if type(domain) is not TraceDomain:
            raise TypeError("TraceMap.for_domain domain must be TraceDomain")
        return tuple(record for record in self.records if record.domain == domain)


__all__ = (
    "CANONICAL_TRACE_DOMAINS",
    "TRACE_DOMAIN_IDS",
    "TRACE_SCHEMA_VERSION",
    "TraceDomain",
    "TraceIdentity",
    "TraceMap",
    "TraceRecord",
)