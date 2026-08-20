"""P11.10B minimal immutable semantic-decision model."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Any, Tuple


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _value(value: Any, field: str) -> None:
    if type(value) in (str, int, float, bool, type(None)):
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _value(item, f"{field}[{index}]")
        return
    raise TypeError(f"{field} must be an immutable scalar or tuple")


def _provenance(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    for index, item in enumerate(value):
        _text(item, f"{field}[{index}]")


@_dataclass(frozen=True)
class AdvancedCondition:
    """Passive higher-order semantic condition description."""

    identity: str
    condition_kind: str
    payload: Any = None
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.identity, "AdvancedCondition.identity")
        _text(self.condition_kind, "AdvancedCondition.condition_kind")
        _value(self.payload, "AdvancedCondition.payload")
        _provenance(self.provenance, "AdvancedCondition.provenance")


@_dataclass(frozen=True)
class CandidateAlternative:
    """Passive canonical semantic possibility."""

    identity: str
    payload: Any = None
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.identity, "CandidateAlternative.identity")
        _value(self.payload, "CandidateAlternative.payload")
        _provenance(self.provenance, "CandidateAlternative.provenance")


@_dataclass(frozen=True)
class SemanticOutcomeKind:
    """Passive canonical outcome-kind descriptor."""

    canonical_id: str

    def __post_init__(self) -> None:
        _text(self.canonical_id, "SemanticOutcomeKind.canonical_id")


CORE_SEMANTIC_OUTCOME_KINDS: Tuple[SemanticOutcomeKind, ...] = tuple(
    SemanticOutcomeKind(kind_id)
    for kind_id in (
        "selected",
        "composed",
        "unresolved",
        "paradox.elevation_candidate",
    )
)


@_dataclass(frozen=True)
class SemanticOutcome:
    """Passive immutable semantic-decision outcome envelope."""

    kind_id: str
    alternatives: Tuple[CandidateAlternative, ...] = ()
    payload: Any = None
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.kind_id, "SemanticOutcome.kind_id")
        if type(self.alternatives) is not tuple:
            raise TypeError("SemanticOutcome.alternatives must be an exact tuple")
        if any(type(item) is not CandidateAlternative for item in self.alternatives):
            raise TypeError(
                "SemanticOutcome.alternatives must contain exact "
                "CandidateAlternative values"
            )
        _value(self.payload, "SemanticOutcome.payload")
        _provenance(self.provenance, "SemanticOutcome.provenance")


__all__ = (
    "AdvancedCondition",
    "CandidateAlternative",
    "SemanticOutcomeKind",
    "SemanticOutcome",
    "CORE_SEMANTIC_OUTCOME_KINDS",
)