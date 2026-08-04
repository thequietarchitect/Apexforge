"""P11.2F-F passive Concordat conflict-evidence boundary coverage."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

from governance.conflicts import (
    CONCORDAT_COURT,
    CONCORDAT_METHODS,
    TAP_CHECK_MODE,
    ConflictEvidence,
    ConflictPosition,
    route_conflict_evidence,
)


MODULE_PATH = (
    Path(__file__).resolve().parent
    / "governance"
    / "conflicts.py"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_policy_conflict_referral_is_passive_and_deterministic() -> None:
    evidence = ConflictEvidence(
        id="conflict:Retention",
        kind="policy",
        subject="Retention versus deletion policy",
        positions=(
            ConflictPosition(
                id="position:Delete",
                statement="Delete after the minimum period.",
                weight=40,
                rationale="Minimize retained exposure.",
            ),
            ConflictPosition(
                id="position:Retain",
                statement="Retain for audit continuity.",
                weight=60,
                rationale="Preserve accountable history.",
            ),
        ),
        source_nodes=(
            "directive:Retention",
            "cause:Lifecycle",
            "directive:Retention",
        ),
    )

    require(
        tuple(position.id for position in evidence.positions)
        == (
            "position:Delete",
            "position:Retain",
        ),
        "conflict positions are not canonically ordered",
    )
    require(
        evidence.source_nodes
        == (
            "cause:Lifecycle",
            "directive:Retention",
        ),
        "conflict source nodes are not deterministic",
    )

    first = route_conflict_evidence(evidence)
    second = route_conflict_evidence(evidence)

    require(first == second, "conflict referral is not deterministic")
    require(first.eligible, "policy conflict was not eligible")
    require(
        first.destination == CONCORDAT_COURT,
        "policy conflict destination changed",
    )
    require(
        first.methods == CONCORDAT_METHODS,
        "policy conflict methods changed",
    )
    require(
        first.tap_check_mode == TAP_CHECK_MODE
        and first.tap_check_mode == "observational",
        "Tap Check stopped being observational",
    )
    require(
        first.activates_directives is False,
        "passive referral activated directives",
    )
    require(
        first.evidence is evidence,
        "referral replaced the supplied evidence",
    )
    require(
        not hasattr(first, "selected")
        and not hasattr(first, "winner")
        and not hasattr(first, "execute"),
        "passive referral acquired decision or execution behavior",
    )

    try:
        evidence.subject = "mutated"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("conflict evidence is mutable")


def test_non_overridable_categories_are_not_referred() -> None:
    structural = route_conflict_evidence(
        ConflictEvidence(
            id="conflict:MissingTarget",
            kind="structural",
            subject="Missing directive target",
            source_nodes=("directive:Main",),
        )
    )
    authorization = route_conflict_evidence(
        ConflictEvidence(
            id="conflict:Denied",
            kind="authorization",
            subject="Principal authorization denial",
            source_nodes=("principal:Operator",),
        )
    )

    for referral, phrase in (
        (structural, "structural AIR errors are non-overridable"),
        (authorization, "authorization denials are non-overridable"),
    ):
        require(
            referral.eligible is False,
            "non-overridable evidence became eligible",
        )
        require(
            referral.destination is None,
            "non-overridable evidence received a court destination",
        )
        require(
            referral.methods == (),
            "non-overridable evidence received governance methods",
        )
        require(
            phrase in referral.reason,
            "non-overridable reason changed",
        )
        require(
            referral.activates_directives is False,
            "ineligible referral activated directives",
        )


def test_evidence_validation_and_module_isolation() -> None:
    try:
        ConflictEvidence(
            id="conflict:Incomplete",
            kind="policy",
            subject="Only one policy position",
            positions=(
                ConflictPosition(
                    id="position:Only",
                    statement="Only position.",
                ),
            ),
        )
    except ValueError as error:
        require(
            "at least two positions" in str(error),
            "incomplete policy diagnostic changed",
        )
    else:
        raise AssertionError(
            "single-position policy conflict was accepted"
        )

    try:
        ConflictEvidence(
            id="conflict:Unknown",
            kind="runtime",
            subject="Unknown conflict category",
        )
    except ValueError as error:
        require(
            "structural" in str(error)
            and "authorization" in str(error),
            "unknown conflict-kind diagnostic changed",
        )
    else:
        raise AssertionError("unknown conflict kind was accepted")

    module = MODULE_PATH.read_text(encoding="utf-8")
    forbidden = (
        "AIRVerifier",
        "RuntimeEngine",
        "AuthorityRegistry",
        "subprocess",
        "open(",
        "Path(",
        "execute(",
        "selected_path",
    )
    require(
        all(token not in module for token in forbidden),
        "passive governance module acquired active dependencies",
    )


def main() -> None:
    test_policy_conflict_referral_is_passive_and_deterministic()
    test_non_overridable_categories_are_not_referred()
    test_evidence_validation_and_module_isolation()
    print("P11.2F-F Concordat conflict-evidence smoke test passed.")
    print("Passive deterministic policy referral: PASS")
    print("Structural and authorization non-override: PASS")
    print("Evidence validation and module isolation: PASS")


if __name__ == "__main__":
    main()
