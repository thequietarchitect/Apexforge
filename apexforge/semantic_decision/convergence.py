"""P11.10D semantic convergence-set construction and explicit policy boundary."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Any, Tuple

from .evaluation import AdvancedConditionEvaluation
from .model import CandidateAlternative


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
class ConvergencePolicy:
    """Passive explicit P11.10 convergence-policy descriptor."""

    identity: str
    parameters: Tuple[Tuple[str, Any], ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.identity, "ConvergencePolicy.identity")
        if type(self.parameters) is not tuple:
            raise TypeError("ConvergencePolicy.parameters must be an exact tuple")
        for index, parameter in enumerate(self.parameters):
            if type(parameter) is not tuple or len(parameter) != 2:
                raise TypeError(
                    "ConvergencePolicy.parameters entries must be exact key/value tuples"
                )
            key, value = parameter
            _text(key, f"ConvergencePolicy.parameters[{index}].key")
            _value(value, f"ConvergencePolicy.parameters[{index}].value")
        _provenance(self.provenance, "ConvergencePolicy.provenance")


@_dataclass(frozen=True)
class EvaluatedCandidate:
    """Exact binding of one candidate to one canonical condition evaluation."""

    candidate: CandidateAlternative
    evaluation: AdvancedConditionEvaluation

    def __post_init__(self) -> None:
        if type(self.candidate) is not CandidateAlternative:
            raise TypeError(
                "EvaluatedCandidate.candidate must be an exact CandidateAlternative"
            )
        if type(self.evaluation) is not AdvancedConditionEvaluation:
            raise TypeError(
                "EvaluatedCandidate.evaluation must be an exact AdvancedConditionEvaluation"
            )


@_dataclass(frozen=True)
class SemanticConvergenceSet:
    """Immutable convergence-set construction result with explicit passive policy."""

    policy: ConvergencePolicy
    candidates: Tuple[EvaluatedCandidate, ...]
    members: Tuple[EvaluatedCandidate, ...]
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.policy) is not ConvergencePolicy:
            raise TypeError(
                "SemanticConvergenceSet.policy must be an exact ConvergencePolicy"
            )
        if type(self.candidates) is not tuple:
            raise TypeError("SemanticConvergenceSet.candidates must be an exact tuple")
        if any(type(item) is not EvaluatedCandidate for item in self.candidates):
            raise TypeError(
                "SemanticConvergenceSet.candidates must contain exact "
                "EvaluatedCandidate values"
            )
        if type(self.members) is not tuple:
            raise TypeError("SemanticConvergenceSet.members must be an exact tuple")
        if any(type(item) is not EvaluatedCandidate for item in self.members):
            raise TypeError(
                "SemanticConvergenceSet.members must contain exact EvaluatedCandidate values"
            )
        _provenance(self.provenance, "SemanticConvergenceSet.provenance")


def construct_semantic_convergence_set(
    candidates: Tuple[EvaluatedCandidate, ...],
    *,
    policy: ConvergencePolicy,
) -> SemanticConvergenceSet:
    """Construct a traceable admissible-member set without applying policy semantics."""

    if type(candidates) is not tuple:
        raise TypeError("candidates must be an exact tuple")
    if any(type(item) is not EvaluatedCandidate for item in candidates):
        raise TypeError("candidates must contain exact EvaluatedCandidate values")
    if type(policy) is not ConvergencePolicy:
        raise TypeError("policy must be an exact ConvergencePolicy")

    members = tuple(
        item
        for item in candidates
        if item.evaluation.state_id == "admissible"
    )
    provenance = policy.provenance + tuple(
        provenance_item
        for item in candidates
        for provenance_item in (
            item.candidate.provenance + item.evaluation.provenance
        )
    )
    return SemanticConvergenceSet(
        policy=policy,
        candidates=candidates,
        members=members,
        provenance=provenance,
    )


__all__ = (
    "ConvergencePolicy",
    "EvaluatedCandidate",
    "SemanticConvergenceSet",
    "construct_semantic_convergence_set",
)
