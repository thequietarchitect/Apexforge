"""P11.10E deterministic convergence selection, composition, and ranking."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Optional, Tuple

from .convergence import SemanticConvergenceSet
from .model import CandidateAlternative, SemanticOutcome


CORE_CONVERGENCE_POLICY_IDS: Tuple[str, ...] = (
    "select.explicit-order",
    "compose.all-admissible",
    "rank.explicit-order",
)


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _provenance(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    for index, item in enumerate(value):
        _text(item, f"{field}[{index}]")


@_dataclass(frozen=True)
class RankedCandidate:
    """One explicit P11.10 policy rank over one canonical candidate."""

    candidate: CandidateAlternative
    rank: int

    def __post_init__(self) -> None:
        if type(self.candidate) is not CandidateAlternative:
            raise TypeError(
                "RankedCandidate.candidate must be an exact CandidateAlternative"
            )
        if type(self.rank) is not int:
            raise TypeError("RankedCandidate.rank must be an exact int")
        if self.rank < 1:
            raise ValueError("RankedCandidate.rank must be positive")


@_dataclass(frozen=True)
class SemanticConvergenceResolution:
    """Immutable result of applying one explicit P11.10 convergence policy."""

    convergence_set: SemanticConvergenceSet
    ranking: Tuple[RankedCandidate, ...]
    outcome: SemanticOutcome
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.convergence_set) is not SemanticConvergenceSet:
            raise TypeError(
                "SemanticConvergenceResolution.convergence_set must be an exact "
                "SemanticConvergenceSet"
            )
        if type(self.ranking) is not tuple:
            raise TypeError(
                "SemanticConvergenceResolution.ranking must be an exact tuple"
            )
        if any(type(item) is not RankedCandidate for item in self.ranking):
            raise TypeError(
                "SemanticConvergenceResolution.ranking must contain exact "
                "RankedCandidate values"
            )
        if type(self.outcome) is not SemanticOutcome:
            raise TypeError(
                "SemanticConvergenceResolution.outcome must be an exact SemanticOutcome"
            )
        _provenance(self.provenance, "SemanticConvergenceResolution.provenance")


def _member_candidates(
    convergence_set: SemanticConvergenceSet,
) -> Tuple[CandidateAlternative, ...]:
    return tuple(item.candidate for item in convergence_set.members)


def _unresolved(
    convergence_set: SemanticConvergenceSet,
) -> SemanticConvergenceResolution:
    alternatives = _member_candidates(convergence_set)
    outcome = SemanticOutcome(
        kind_id="unresolved",
        alternatives=alternatives,
        provenance=convergence_set.provenance,
    )
    return SemanticConvergenceResolution(
        convergence_set=convergence_set,
        ranking=(),
        outcome=outcome,
        provenance=convergence_set.provenance,
    )


def _explicit_order(
    convergence_set: SemanticConvergenceSet,
) -> Optional[Tuple[CandidateAlternative, ...]]:
    parameters = convergence_set.policy.parameters
    if (
        len(parameters) != 1
        or parameters[0][0] != "order"
        or type(parameters[0][1]) is not tuple
    ):
        return None

    order = parameters[0][1]
    if any(
        type(identity) is not str
        or not identity
        or identity != identity.strip()
        for identity in order
    ):
        return None
    if len(set(order)) != len(order):
        return None

    members = _member_candidates(convergence_set)
    identities = tuple(candidate.identity for candidate in members)
    if len(set(identities)) != len(identities):
        return None
    if len(order) != len(identities) or set(order) != set(identities):
        return None

    by_identity = {candidate.identity: candidate for candidate in members}
    return tuple(by_identity[identity] for identity in order)


def _ranking(
    ordered: Tuple[CandidateAlternative, ...],
) -> Tuple[RankedCandidate, ...]:
    return tuple(
        RankedCandidate(candidate=candidate, rank=index)
        for index, candidate in enumerate(ordered, start=1)
    )


def apply_semantic_convergence_policy(
    convergence_set: SemanticConvergenceSet,
) -> SemanticConvergenceResolution:
    """Apply one explicit P11.10 policy without runtime execution or elevation."""

    if type(convergence_set) is not SemanticConvergenceSet:
        raise TypeError("convergence_set must be an exact SemanticConvergenceSet")

    members = _member_candidates(convergence_set)
    if len(members) < 2:
        return _unresolved(convergence_set)

    policy_id = convergence_set.policy.identity

    if policy_id == "compose.all-admissible":
        if convergence_set.policy.parameters:
            return _unresolved(convergence_set)
        outcome = SemanticOutcome(
            kind_id="composed",
            alternatives=members,
            provenance=convergence_set.provenance,
        )
        return SemanticConvergenceResolution(
            convergence_set=convergence_set,
            ranking=(),
            outcome=outcome,
            provenance=convergence_set.provenance,
        )

    if policy_id in ("select.explicit-order", "rank.explicit-order"):
        ordered = _explicit_order(convergence_set)
        if ordered is None:
            return _unresolved(convergence_set)
        ranking = _ranking(ordered)
        if policy_id == "select.explicit-order":
            outcome = SemanticOutcome(
                kind_id="selected",
                alternatives=(ordered[0],),
                provenance=convergence_set.provenance,
            )
        else:
            outcome = SemanticOutcome(
                kind_id="unresolved",
                alternatives=members,
                provenance=convergence_set.provenance,
            )
        return SemanticConvergenceResolution(
            convergence_set=convergence_set,
            ranking=ranking,
            outcome=outcome,
            provenance=convergence_set.provenance,
        )

    return _unresolved(convergence_set)


__all__ = (
    "CORE_CONVERGENCE_POLICY_IDS",
    "RankedCandidate",
    "SemanticConvergenceResolution",
    "apply_semantic_convergence_policy",
)
