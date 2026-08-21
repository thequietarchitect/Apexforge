"""Deterministic composition and category coverage for TAP Check ledgers."""

from __future__ import annotations

from typing import Tuple

from .model import (
    TAP_CHECK_CATEGORY_IDS,
    TapCheckAuditLedger,
)


def compose_tap_check_ledgers(
    ledgers: Tuple[TapCheckAuditLedger, ...],
) -> TapCheckAuditLedger:
    """Compose already-produced TAP ledgers in caller-supplied block order."""

    if type(ledgers) is not tuple:
        raise TypeError("compose_tap_check_ledgers requires an exact tuple")

    entries = ()
    for index, ledger in enumerate(ledgers):
        if type(ledger) is not TapCheckAuditLedger:
            raise TypeError(
                "compose_tap_check_ledgers ledgers[{}] must be an exact "
                "TapCheckAuditLedger".format(index)
            )
        entries += ledger.entries

    return TapCheckAuditLedger(entries)


def tap_check_category_coverage(
    ledger: TapCheckAuditLedger,
) -> Tuple[Tuple[str, int], ...]:
    """Count observed ledger entries in canonical TAP category order."""

    if type(ledger) is not TapCheckAuditLedger:
        raise TypeError(
            "tap_check_category_coverage requires an exact TapCheckAuditLedger"
        )

    return tuple(
        (
            category_id,
            sum(
                1
                for entry in ledger.entries
                if entry.category_id == category_id
            ),
        )
        for category_id in TAP_CHECK_CATEGORY_IDS
    )


__all__ = (
    "compose_tap_check_ledgers",
    "tap_check_category_coverage",
)