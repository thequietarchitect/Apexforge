"""Passive Concordat conflict evidence and referral metadata.

This module records and classifies conflict evidence only. It does not verify
AIR, authorize principals, select causal paths, execute directives, activate
Tap Check, or mutate canonical directive artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Tuple


ConflictKind = Literal[
    "policy",
    "structural",
    "authorization",
]

CONCORDAT_COURT = "Concordat Court"
CONCORDAT_METHODS = (
    "WCCD",
    "Gravitas Mode",
)
TAP_CHECK_MODE = "observational"


def _require_text(value: object, *, owner: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string.")

    return value.strip()


@dataclass(frozen=True, order=True)
class ConflictPosition:
    """One weighted position preserved as passive conflict evidence."""

    id: str
    statement: str
    weight: int = 0
    rationale: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "id",
            _require_text(self.id, owner="ConflictPosition.id"),
        )
        object.__setattr__(
            self,
            "statement",
            _require_text(
                self.statement,
                owner="ConflictPosition.statement",
            ),
        )

        if type(self.weight) is not int:
            raise TypeError(
                "ConflictPosition.weight must be an int; "
                f"received {type(self.weight).__name__}."
            )

        if not isinstance(self.rationale, str):
            raise TypeError(
                "ConflictPosition.rationale must be a string."
            )

        object.__setattr__(
            self,
            "rationale",
            self.rationale.strip(),
        )


@dataclass(frozen=True)
class ConflictEvidence:
    """Immutable evidence describing one possible governance conflict."""

    id: str
    kind: ConflictKind
    subject: str
    positions: Tuple[ConflictPosition, ...] = ()
    source_nodes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "id",
            _require_text(self.id, owner="ConflictEvidence.id"),
        )
        object.__setattr__(
            self,
            "subject",
            _require_text(
                self.subject,
                owner="ConflictEvidence.subject",
            ),
        )

        if self.kind not in (
            "policy",
            "structural",
            "authorization",
        ):
            raise ValueError(
                "ConflictEvidence.kind must be 'policy', "
                "'structural', or 'authorization'."
            )

        positions = tuple(self.positions)
        seen: set[str] = set()

        for position in positions:
            if not isinstance(position, ConflictPosition):
                raise TypeError(
                    "ConflictEvidence.positions must contain "
                    "ConflictPosition values."
                )

            canonical = position.id.casefold()
            if canonical in seen:
                raise ValueError(
                    "ConflictEvidence position ids must be "
                    f"case-insensitively unique: {position.id!r}."
                )
            seen.add(canonical)

        if self.kind == "policy" and len(positions) < 2:
            raise ValueError(
                "Policy conflict evidence requires at least "
                "two positions."
            )

        object.__setattr__(
            self,
            "positions",
            tuple(
                sorted(
                    positions,
                    key=lambda position: (
                        position.id.casefold(),
                        position.id,
                        position.statement,
                        position.weight,
                        position.rationale,
                    ),
                )
            ),
        )

        normalized_nodes = tuple(
            _require_text(
                node,
                owner="ConflictEvidence.source_nodes item",
            )
            for node in tuple(self.source_nodes)
        )
        object.__setattr__(
            self,
            "source_nodes",
            tuple(
                sorted(
                    set(normalized_nodes),
                    key=lambda node: (
                        node.casefold(),
                        node,
                    ),
                )
            ),
        )


@dataclass(frozen=True)
class ConflictReferral:
    """Deterministic passive classification of conflict evidence."""

    evidence: ConflictEvidence
    eligible: bool
    destination: Optional[str]
    methods: Tuple[str, ...]
    reason: str
    tap_check_mode: str = TAP_CHECK_MODE
    activates_directives: bool = False


def route_conflict_evidence(
    evidence: ConflictEvidence,
) -> ConflictReferral:
    """Classify evidence without deciding or executing the conflict."""

    if not isinstance(evidence, ConflictEvidence):
        raise TypeError(
            "route_conflict_evidence requires ConflictEvidence."
        )

    if evidence.kind == "policy":
        return ConflictReferral(
            evidence=evidence,
            eligible=True,
            destination=CONCORDAT_COURT,
            methods=CONCORDAT_METHODS,
            reason=(
                "eligible policy conflict referred for "
                "Concordat Court review"
            ),
        )

    if evidence.kind == "structural":
        reason = (
            "structural AIR errors are non-overridable "
            "and cannot be referred for governance resolution"
        )
    else:
        reason = (
            "authorization denials are non-overridable "
            "and cannot be referred for governance resolution"
        )

    return ConflictReferral(
        evidence=evidence,
        eligible=False,
        destination=None,
        methods=(),
        reason=reason,
    )
