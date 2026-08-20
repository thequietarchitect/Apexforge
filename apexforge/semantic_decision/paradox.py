"""P11.10F Paradox Elevation eligibility and elevated semantic state."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Optional, Tuple

from .model import CandidateAlternative, SemanticOutcome
from .resolution import (
    RankedCandidate,
    SemanticConvergenceResolution,
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
class ParadoxIncompatibilityEvidence:
    """Explicit pairwise material-incompatibility evidence."""

    left: CandidateAlternative
    right: CandidateAlternative
    materially_incompatible: bool
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.left) is not CandidateAlternative:
            raise TypeError(
                "ParadoxIncompatibilityEvidence.left must be an exact "
                "CandidateAlternative"
            )
        if type(self.right) is not CandidateAlternative:
            raise TypeError(
                "ParadoxIncompatibilityEvidence.right must be an exact "
                "CandidateAlternative"
            )
        if type(self.materially_incompatible) is not bool:
            raise TypeError(
                "ParadoxIncompatibilityEvidence.materially_incompatible "
                "must be an exact bool"
            )
        _provenance(
            self.provenance,
            "ParadoxIncompatibilityEvidence.provenance",
        )


@_dataclass(frozen=True)
class ParadoxElevationEvidence:
    """Explicit evidence offered for one exact ordinary convergence resolution."""

    resolution: SemanticConvergenceResolution
    incompatibilities: Tuple[ParadoxIncompatibilityEvidence, ...]
    reduction_requires_information_loss: bool
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.resolution) is not SemanticConvergenceResolution:
            raise TypeError(
                "ParadoxElevationEvidence.resolution must be an exact "
                "SemanticConvergenceResolution"
            )
        if type(self.incompatibilities) is not tuple:
            raise TypeError(
                "ParadoxElevationEvidence.incompatibilities must be an exact tuple"
            )
        if any(
            type(item) is not ParadoxIncompatibilityEvidence
            for item in self.incompatibilities
        ):
            raise TypeError(
                "ParadoxElevationEvidence.incompatibilities must contain exact "
                "ParadoxIncompatibilityEvidence values"
            )
        if type(self.reduction_requires_information_loss) is not bool:
            raise TypeError(
                "ParadoxElevationEvidence.reduction_requires_information_loss "
                "must be an exact bool"
            )
        _provenance(self.provenance, "ParadoxElevationEvidence.provenance")


@_dataclass(frozen=True)
class ParadoxElevationAssessment:
    """Immutable eligibility assessment over explicit Paradox Elevation evidence."""

    evidence: ParadoxElevationEvidence
    eligible: bool
    candidate_outcome: Optional[SemanticOutcome]
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.evidence) is not ParadoxElevationEvidence:
            raise TypeError(
                "ParadoxElevationAssessment.evidence must be an exact "
                "ParadoxElevationEvidence"
            )
        if type(self.eligible) is not bool:
            raise TypeError("ParadoxElevationAssessment.eligible must be an exact bool")
        if (
            self.candidate_outcome is not None
            and type(self.candidate_outcome) is not SemanticOutcome
        ):
            raise TypeError(
                "ParadoxElevationAssessment.candidate_outcome must be an exact "
                "SemanticOutcome or None"
            )
        _provenance(self.provenance, "ParadoxElevationAssessment.provenance")


@_dataclass(frozen=True)
class ElevatedSemanticState:
    """Immutable represented state preserving irreducible semantic alternatives."""

    assessment: ParadoxElevationAssessment
    alternatives: Tuple[CandidateAlternative, ...]
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.assessment) is not ParadoxElevationAssessment:
            raise TypeError(
                "ElevatedSemanticState.assessment must be an exact "
                "ParadoxElevationAssessment"
            )
        if type(self.alternatives) is not tuple:
            raise TypeError("ElevatedSemanticState.alternatives must be an exact tuple")
        if any(type(item) is not CandidateAlternative for item in self.alternatives):
            raise TypeError(
                "ElevatedSemanticState.alternatives must contain exact "
                "CandidateAlternative values"
            )
        _provenance(self.provenance, "ElevatedSemanticState.provenance")


def _same_identity_tuple(
    left: Tuple[CandidateAlternative, ...],
    right: Tuple[CandidateAlternative, ...],
) -> bool:
    return len(left) == len(right) and all(
        left_item is right_item
        for left_item, right_item in zip(left, right)
    )


def _member_candidates(
    resolution: SemanticConvergenceResolution,
) -> Tuple[CandidateAlternative, ...]:
    return tuple(
        item.candidate
        for item in resolution.convergence_set.members
    )


def _valid_rank_unresolved(
    resolution: SemanticConvergenceResolution,
    alternatives: Tuple[CandidateAlternative, ...],
) -> bool:
    policy = resolution.convergence_set.policy
    if policy.identity != "rank.explicit-order":
        return False
    if len(resolution.ranking) != len(alternatives):
        return False
    if any(type(item) is not RankedCandidate for item in resolution.ranking):
        return False
    if tuple(item.rank for item in resolution.ranking) != tuple(
        range(1, len(alternatives) + 1)
    ):
        return False
    ranked_candidates = tuple(item.candidate for item in resolution.ranking)
    if len(ranked_candidates) != len(alternatives):
        return False
    for alternative in alternatives:
        if sum(candidate is alternative for candidate in ranked_candidates) != 1:
            return False
    return True


def _complete_material_incompatibility(
    alternatives: Tuple[CandidateAlternative, ...],
    incompatibilities: Tuple[ParadoxIncompatibilityEvidence, ...],
) -> bool:
    expected_pairs = {
        (left_index, right_index)
        for left_index in range(len(alternatives))
        for right_index in range(left_index + 1, len(alternatives))
    }
    observed_pairs = set()

    for item in incompatibilities:
        left_matches = tuple(
            index
            for index, alternative in enumerate(alternatives)
            if item.left is alternative
        )
        right_matches = tuple(
            index
            for index, alternative in enumerate(alternatives)
            if item.right is alternative
        )
        if len(left_matches) != 1 or len(right_matches) != 1:
            return False

        left_index = left_matches[0]
        right_index = right_matches[0]
        if left_index == right_index:
            return False
        pair = (
            min(left_index, right_index),
            max(left_index, right_index),
        )
        if pair in observed_pairs:
            return False
        if item.materially_incompatible is not True:
            return False
        observed_pairs.add(pair)

    return observed_pairs == expected_pairs


def assess_paradox_elevation(
    evidence: ParadoxElevationEvidence,
) -> ParadoxElevationAssessment:
    """Assess explicit evidence without inferring incompatibility from payloads."""

    if type(evidence) is not ParadoxElevationEvidence:
        raise TypeError("evidence must be an exact ParadoxElevationEvidence")

    resolution = evidence.resolution
    alternatives = resolution.outcome.alternatives
    member_candidates = _member_candidates(resolution)

    eligible = (
        resolution.outcome.kind_id == "unresolved"
        and len(alternatives) >= 2
        and len({id(item) for item in alternatives}) == len(alternatives)
        and _same_identity_tuple(alternatives, member_candidates)
        and all(
            item.evaluation.state_id == "admissible"
            for item in resolution.convergence_set.members
        )
        and _valid_rank_unresolved(resolution, alternatives)
        and evidence.reduction_requires_information_loss is True
        and _complete_material_incompatibility(
            alternatives,
            evidence.incompatibilities,
        )
    )

    provenance = (
        resolution.provenance
        + evidence.provenance
        + tuple(
            provenance_item
            for incompatibility in evidence.incompatibilities
            for provenance_item in incompatibility.provenance
        )
    )

    candidate_outcome = (
        SemanticOutcome(
            kind_id="paradox.elevation_candidate",
            alternatives=alternatives,
            provenance=provenance,
        )
        if eligible
        else None
    )
    return ParadoxElevationAssessment(
        evidence=evidence,
        eligible=eligible,
        candidate_outcome=candidate_outcome,
        provenance=provenance,
    )


def elevate_paradox_assessment(
    assessment: ParadoxElevationAssessment,
) -> ElevatedSemanticState:
    """Construct an elevated state only from a positively eligible assessment."""

    if type(assessment) is not ParadoxElevationAssessment:
        raise TypeError("assessment must be an exact ParadoxElevationAssessment")
    if assessment.eligible is not True:
        raise ValueError("assessment is not eligible for Paradox Elevation")
    if (
        type(assessment.candidate_outcome) is not SemanticOutcome
        or assessment.candidate_outcome.kind_id != "paradox.elevation_candidate"
    ):
        raise ValueError(
            "eligible assessment must contain a paradox.elevation_candidate outcome"
        )

    alternatives = assessment.candidate_outcome.alternatives
    if len(alternatives) < 2:
        raise ValueError("Paradox Elevation requires multiple alternatives")

    return ElevatedSemanticState(
        assessment=assessment,
        alternatives=alternatives,
        provenance=assessment.provenance,
    )


__all__ = (
    "ParadoxIncompatibilityEvidence",
    "ParadoxElevationEvidence",
    "ParadoxElevationAssessment",
    "ElevatedSemanticState",
    "assess_paradox_elevation",
    "elevate_paradox_assessment",
)
