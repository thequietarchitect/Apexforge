"""Deterministic observational projection from TAM TraceMap to TAP ledger."""

from __future__ import annotations

from typing import Optional, Tuple

from tam.model import TraceMap, TraceRecord

from .model import TapCheckAuditLedger, TapCheckLedgerEntry


_DIRECT_TRACE_CATEGORY_MAP: Tuple[Tuple[str, str, str, str, str], ...] = (
    (
        "transformation",
        "language.compiler",
        "language.compiler",
        "source-map-entry",
        "compiler-transformations",
    ),
    (
        "authority",
        "authority.model",
        "authority.model",
        "authority-check",
        "authority-intervention",
    ),
    (
        "authority",
        "authority.model",
        "authority.model",
        "authority-grant",
        "authority-intervention",
    ),
)


def _category_id_for_record(record: TraceRecord) -> Optional[str]:
    signature = (
        record.domain.canonical_id,
        record.producer,
        record.owner,
        record.representation,
    )
    for domain_id, producer, owner, representation, category_id in (
        _DIRECT_TRACE_CATEGORY_MAP
    ):
        if signature == (domain_id, producer, owner, representation):
            return category_id
    return None


def _subject_for_record(record: TraceRecord) -> str:
    if record.canonical_identity is not None:
        return record.canonical_identity
    return record.trace_id.value


def _evidence_for_record(record: TraceRecord) -> Tuple[str, ...]:
    evidence = (
        "domain={}".format(record.domain.canonical_id),
        "producer={}".format(record.producer),
        "owner={}".format(record.owner),
        "representation={}".format(record.representation),
        "schema_version={}".format(record.schema_version),
    )
    if record.canonical_identity is not None:
        evidence += (
            "canonical_identity={}".format(record.canonical_identity),
        )
    return evidence


def audit_trace_map(trace_map: TraceMap) -> TapCheckAuditLedger:
    """Project directly-mappable frozen TAM records into a passive TAP ledger."""

    if type(trace_map) is not TraceMap:
        raise TypeError("audit_trace_map requires an exact TraceMap")

    entries: Tuple[TapCheckLedgerEntry, ...] = ()
    for record in trace_map.records:
        category_id = _category_id_for_record(record)
        if category_id is None:
            continue
        entries += (
            TapCheckLedgerEntry(
                category_id=category_id,
                subject=_subject_for_record(record),
                evidence=_evidence_for_record(record),
                trace_ids=(record.trace_id,),
            ),
        )

    return TapCheckAuditLedger(entries)


__all__ = ("audit_trace_map",)