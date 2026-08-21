"""Immutable passive TAP Check audit-ledger contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from tam.model import TraceIdentity


TAP_CHECK_CATEGORY_IDS: Tuple[str, ...] = (
    "active-directives",
    "compiler-transformations",
    "semantic-changes",
    "authority-intervention",
    "optimization-decisions",
    "continuity-effects",
    "narrative-state-changes",
    "convergence-rulings",
    "air-lowering",
    "runtime-results",
)


def _require_text(value: object, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError("{} must be a non-empty string".format(owner))
    return value


def _require_exact_tuple(value: object, *, owner: str) -> tuple:
    if type(value) is not tuple:
        raise TypeError("{} must be an exact tuple".format(owner))
    return value


@dataclass(frozen=True)
class TapCheckLedgerEntry:
    """One immutable observational TAP Check ledger entry."""

    category_id: str
    subject: str
    evidence: Tuple[str, ...] = ()
    trace_ids: Tuple[TraceIdentity, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.category_id, owner="TapCheckLedgerEntry.category_id")
        if self.category_id not in TAP_CHECK_CATEGORY_IDS:
            raise ValueError(
                "TapCheckLedgerEntry.category_id must be a canonical TAP Check "
                "category id"
            )

        _require_text(self.subject, owner="TapCheckLedgerEntry.subject")

        _require_exact_tuple(
            self.evidence,
            owner="TapCheckLedgerEntry.evidence",
        )
        for index, item in enumerate(self.evidence):
            _require_text(
                item,
                owner="TapCheckLedgerEntry.evidence[{}]".format(index),
            )

        _require_exact_tuple(
            self.trace_ids,
            owner="TapCheckLedgerEntry.trace_ids",
        )
        for index, trace_id in enumerate(self.trace_ids):
            if type(trace_id) is not TraceIdentity:
                raise TypeError(
                    "TapCheckLedgerEntry.trace_ids[{}] must be an exact "
                    "TraceIdentity".format(index)
                )


@dataclass(frozen=True)
class TapCheckAuditLedger:
    """Ordered immutable collection of passive TAP Check ledger entries."""

    entries: Tuple[TapCheckLedgerEntry, ...] = ()

    def __post_init__(self) -> None:
        _require_exact_tuple(
            self.entries,
            owner="TapCheckAuditLedger.entries",
        )
        for index, entry in enumerate(self.entries):
            if type(entry) is not TapCheckLedgerEntry:
                raise TypeError(
                    "TapCheckAuditLedger.entries[{}] must be an exact "
                    "TapCheckLedgerEntry".format(index)
                )


__all__ = (
    "TAP_CHECK_CATEGORY_IDS",
    "TapCheckLedgerEntry",
    "TapCheckAuditLedger",
)