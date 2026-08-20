"""P11.10C canonical condition evidence and higher-order evaluation."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Any, Optional, Tuple

from .model import AdvancedCondition


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
class ConditionEvidence:
    """Explicit immutable evidence result for one exact advanced condition."""

    condition: AdvancedCondition
    result: Optional[bool]
    facts: Tuple[Tuple[str, Any], ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.condition) is not AdvancedCondition:
            raise TypeError("ConditionEvidence.condition must be an exact AdvancedCondition")
        if self.result is not None and type(self.result) is not bool:
            raise TypeError("ConditionEvidence.result must be an exact bool or None")
        if type(self.facts) is not tuple:
            raise TypeError("ConditionEvidence.facts must be an exact tuple")
        for index, fact in enumerate(self.facts):
            if type(fact) is not tuple or len(fact) != 2:
                raise TypeError(
                    "ConditionEvidence.facts entries must be exact key/value tuples"
                )
            key, value = fact
            _text(key, f"ConditionEvidence.facts[{index}].key")
            _value(value, f"ConditionEvidence.facts[{index}].value")
        _provenance(self.provenance, "ConditionEvidence.provenance")


@_dataclass(frozen=True)
class AdmissibilityState:
    """Passive canonical advanced-condition admissibility-state descriptor."""

    canonical_id: str

    def __post_init__(self) -> None:
        _text(self.canonical_id, "AdmissibilityState.canonical_id")


CORE_ADMISSIBILITY_STATES: Tuple[AdmissibilityState, ...] = tuple(
    AdmissibilityState(state_id)
    for state_id in (
        "admissible",
        "inadmissible",
        "indeterminate",
    )
)


@_dataclass(frozen=True)
class AdvancedConditionEvaluation:
    """Immutable deterministic evaluation result over explicit condition evidence."""

    condition: AdvancedCondition
    evidence: Tuple[ConditionEvidence, ...]
    state_id: str
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.condition) is not AdvancedCondition:
            raise TypeError(
                "AdvancedConditionEvaluation.condition must be an exact AdvancedCondition"
            )
        if type(self.evidence) is not tuple:
            raise TypeError("AdvancedConditionEvaluation.evidence must be an exact tuple")
        if any(type(item) is not ConditionEvidence for item in self.evidence):
            raise TypeError(
                "AdvancedConditionEvaluation.evidence must contain exact "
                "ConditionEvidence values"
            )
        _text(self.state_id, "AdvancedConditionEvaluation.state_id")
        _provenance(self.provenance, "AdvancedConditionEvaluation.provenance")


def evaluate_advanced_condition(
    condition: AdvancedCondition,
    *,
    evidence: Tuple[ConditionEvidence, ...] = (),
) -> AdvancedConditionEvaluation:
    """Aggregate explicit evidence without executing predecessor condition machinery."""

    if type(condition) is not AdvancedCondition:
        raise TypeError("condition must be an exact AdvancedCondition")
    if type(evidence) is not tuple:
        raise TypeError("evidence must be an exact tuple")
    if any(type(item) is not ConditionEvidence for item in evidence):
        raise TypeError("evidence must contain exact ConditionEvidence values")
    if any(item.condition is not condition for item in evidence):
        raise ValueError("all evidence must reference the exact supplied AdvancedCondition")

    results = tuple(item.result for item in evidence)
    if not results or any(result is None for result in results):
        state_id = "indeterminate"
    elif all(result is True for result in results):
        state_id = "admissible"
    elif all(result is False for result in results):
        state_id = "inadmissible"
    else:
        state_id = "indeterminate"

    provenance = condition.provenance + tuple(
        item
        for evidence_item in evidence
        for item in evidence_item.provenance
    )

    return AdvancedConditionEvaluation(
        condition=condition,
        evidence=evidence,
        state_id=state_id,
        provenance=provenance,
    )


__all__ = (
    "ConditionEvidence",
    "AdmissibilityState",
    "CORE_ADMISSIBILITY_STATES",
    "AdvancedConditionEvaluation",
    "evaluate_advanced_condition",
)
