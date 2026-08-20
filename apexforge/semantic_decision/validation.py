"""P11.10G semantic-decision validation, collision, closure, and extension contracts."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Tuple

from .convergence import (
    EvaluatedCandidate,
    SemanticConvergenceSet,
)
from .evaluation import (
    CORE_ADMISSIBILITY_STATES,
    AdvancedConditionEvaluation,
    ConditionEvidence,
    evaluate_advanced_condition as _evaluate_advanced_condition,
)
from .model import (
    CORE_SEMANTIC_OUTCOME_KINDS,
    CandidateAlternative,
    SemanticOutcome,
)
from .paradox import (
    ElevatedSemanticState,
    ParadoxElevationAssessment,
    ParadoxElevationEvidence,
    ParadoxIncompatibilityEvidence,
    assess_paradox_elevation as _assess_paradox_elevation,
    elevate_paradox_assessment as _elevate_paradox_assessment,
)
from .resolution import (
    CORE_CONVERGENCE_POLICY_IDS,
    RankedCandidate,
    SemanticConvergenceResolution,
    apply_semantic_convergence_policy as _apply_semantic_convergence_policy,
)


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _text_tuple(value: object, field: str) -> Tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    for index, item in enumerate(value):
        _text(item, f"{field}[{index}]")
    return value


def _duplicates_by_equality(values: tuple) -> bool:
    for index, item in enumerate(values):
        if any(item == prior for prior in values[:index]):
            return True
    return False


def _duplicates_by_identity(values: tuple) -> bool:
    for index, item in enumerate(values):
        if any(item is prior for prior in values[:index]):
            return True
    return False


def _same_identity_tuple(left: tuple, right: tuple) -> bool:
    return len(left) == len(right) and all(
        left_item is right_item
        for left_item, right_item in zip(left, right)
    )


def _require_unique_provenance(value: Tuple[str, ...], owner: str) -> None:
    _text_tuple(value, owner)
    if len(set(value)) != len(value):
        raise ValueError(f"{owner} contains duplicate entries")


def _extension_ids(
    value: Tuple[str, ...],
    *,
    owner: str,
    core_ids: Tuple[str, ...],
) -> Tuple[str, ...]:
    _text_tuple(value, owner)
    if len(set(value)) != len(value):
        raise ValueError(f"{owner} contains duplicate identifiers")
    collision = tuple(item for item in value if item in core_ids)
    if collision:
        raise ValueError(f"{owner} collides with a canonical core identifier")
    return value


def _member_candidates(
    convergence_set: SemanticConvergenceSet,
) -> Tuple[CandidateAlternative, ...]:
    return tuple(item.candidate for item in convergence_set.members)


def _validate_condition_evaluation(
    evaluation: AdvancedConditionEvaluation,
    *,
    allowed_state_ids: Tuple[str, ...],
) -> None:
    if type(evaluation) is not AdvancedConditionEvaluation:
        raise TypeError("evaluation must be an exact AdvancedConditionEvaluation")

    _require_unique_provenance(
        evaluation.condition.provenance,
        "AdvancedCondition.provenance",
    )
    _require_unique_provenance(
        evaluation.provenance,
        "AdvancedConditionEvaluation.provenance",
    )

    if evaluation.state_id not in allowed_state_ids:
        raise ValueError("undeclared advanced-condition admissibility state")

    evidence_coordinates = []
    expected_provenance = evaluation.condition.provenance
    for evidence in evaluation.evidence:
        if type(evidence) is not ConditionEvidence:
            raise TypeError(
                "AdvancedConditionEvaluation.evidence must contain exact ConditionEvidence values"
            )
        if evidence.condition is not evaluation.condition:
            raise ValueError(
                "condition evidence is not closed over the exact evaluated condition"
            )
        _require_unique_provenance(
            evidence.provenance,
            "ConditionEvidence.provenance",
        )
        fact_keys = tuple(key for key, _ in evidence.facts)
        if len(set(fact_keys)) != len(fact_keys):
            raise ValueError("condition evidence contains duplicate fact keys")
        coordinate = (evidence.result, evidence.facts, evidence.provenance)
        if any(coordinate == prior for prior in evidence_coordinates):
            raise ValueError("duplicate condition evidence coordinate")
        evidence_coordinates.append(coordinate)
        expected_provenance += evidence.provenance

    if evaluation.provenance != expected_provenance:
        raise ValueError("advanced-condition evaluation provenance lineage disagrees")

    core_state_ids = tuple(item.canonical_id for item in CORE_ADMISSIBILITY_STATES)
    if evaluation.state_id in core_state_ids:
        expected = _evaluate_advanced_condition(
            evaluation.condition,
            evidence=evaluation.evidence,
        )
        if evaluation.state_id != expected.state_id:
            raise ValueError("advanced-condition core admissibility result disagrees")


def _validate_convergence_set(
    convergence_set: SemanticConvergenceSet,
    *,
    allowed_state_ids: Tuple[str, ...],
    allowed_policy_ids: Tuple[str, ...],
) -> None:
    if type(convergence_set) is not SemanticConvergenceSet:
        raise TypeError("convergence_set must be an exact SemanticConvergenceSet")

    policy = convergence_set.policy
    _require_unique_provenance(policy.provenance, "ConvergencePolicy.provenance")
    if policy.identity not in allowed_policy_ids:
        raise ValueError("undeclared convergence policy identifier")

    parameter_keys = tuple(key for key, _ in policy.parameters)
    if len(set(parameter_keys)) != len(parameter_keys):
        raise ValueError("convergence policy contains duplicate parameter keys")

    candidate_identities = tuple(
        item.candidate.identity for item in convergence_set.candidates
    )
    if len(set(candidate_identities)) != len(candidate_identities):
        raise ValueError("duplicate candidate identity in convergence set")
    if _duplicates_by_identity(convergence_set.candidates):
        raise ValueError("duplicate evaluated-candidate object in convergence set")

    for item in convergence_set.candidates:
        if type(item) is not EvaluatedCandidate:
            raise TypeError(
                "SemanticConvergenceSet.candidates must contain exact EvaluatedCandidate values"
            )
        _require_unique_provenance(
            item.candidate.provenance,
            "CandidateAlternative.provenance",
        )
        _validate_condition_evaluation(
            item.evaluation,
            allowed_state_ids=allowed_state_ids,
        )

    expected_members = tuple(
        item
        for item in convergence_set.candidates
        if item.evaluation.state_id == "admissible"
    )
    if not _same_identity_tuple(convergence_set.members, expected_members):
        raise ValueError("semantic convergence membership closure disagrees")

    expected_provenance = policy.provenance + tuple(
        provenance_item
        for item in convergence_set.candidates
        for provenance_item in (
            item.candidate.provenance + item.evaluation.provenance
        )
    )
    if convergence_set.provenance != expected_provenance:
        raise ValueError("semantic convergence-set provenance lineage disagrees")
    _require_unique_provenance(
        convergence_set.provenance,
        "SemanticConvergenceSet.provenance",
    )


@_dataclass(frozen=True)
class SemanticDecisionValidationReceipt:
    """Passive validation receipt for one exact B-E semantic-decision resolution."""

    resolution: SemanticConvergenceResolution
    extension_admissibility_state_ids: Tuple[str, ...]
    extension_outcome_kind_ids: Tuple[str, ...]
    extension_policy_ids: Tuple[str, ...]
    provenance: Tuple[str, ...]
    checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.resolution) is not SemanticConvergenceResolution:
            raise TypeError(
                "SemanticDecisionValidationReceipt.resolution must be an exact "
                "SemanticConvergenceResolution"
            )
        _text_tuple(
            self.extension_admissibility_state_ids,
            "SemanticDecisionValidationReceipt.extension_admissibility_state_ids",
        )
        _text_tuple(
            self.extension_outcome_kind_ids,
            "SemanticDecisionValidationReceipt.extension_outcome_kind_ids",
        )
        _text_tuple(
            self.extension_policy_ids,
            "SemanticDecisionValidationReceipt.extension_policy_ids",
        )
        _text_tuple(
            self.provenance,
            "SemanticDecisionValidationReceipt.provenance",
        )
        _text_tuple(self.checks, "SemanticDecisionValidationReceipt.checks")


@_dataclass(frozen=True)
class ParadoxElevationValidationReceipt:
    """Passive validation receipt for one exact F eligibility assessment."""

    assessment: ParadoxElevationAssessment
    resolution_receipt: SemanticDecisionValidationReceipt
    provenance: Tuple[str, ...]
    checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.assessment) is not ParadoxElevationAssessment:
            raise TypeError(
                "ParadoxElevationValidationReceipt.assessment must be an exact "
                "ParadoxElevationAssessment"
            )
        if type(self.resolution_receipt) is not SemanticDecisionValidationReceipt:
            raise TypeError(
                "ParadoxElevationValidationReceipt.resolution_receipt must be an exact "
                "SemanticDecisionValidationReceipt"
            )
        _text_tuple(self.provenance, "ParadoxElevationValidationReceipt.provenance")
        _text_tuple(self.checks, "ParadoxElevationValidationReceipt.checks")


@_dataclass(frozen=True)
class ElevatedSemanticStateValidationReceipt:
    """Passive validation receipt for one exact elevated semantic state."""

    state: ElevatedSemanticState
    assessment_receipt: ParadoxElevationValidationReceipt
    provenance: Tuple[str, ...]
    checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.state) is not ElevatedSemanticState:
            raise TypeError(
                "ElevatedSemanticStateValidationReceipt.state must be an exact "
                "ElevatedSemanticState"
            )
        if type(self.assessment_receipt) is not ParadoxElevationValidationReceipt:
            raise TypeError(
                "ElevatedSemanticStateValidationReceipt.assessment_receipt must be an exact "
                "ParadoxElevationValidationReceipt"
            )
        _text_tuple(
            self.provenance,
            "ElevatedSemanticStateValidationReceipt.provenance",
        )
        _text_tuple(
            self.checks,
            "ElevatedSemanticStateValidationReceipt.checks",
        )


def validate_semantic_convergence_resolution(
    resolution: SemanticConvergenceResolution,
    *,
    extension_admissibility_state_ids: Tuple[str, ...] = (),
    extension_outcome_kind_ids: Tuple[str, ...] = (),
    extension_policy_ids: Tuple[str, ...] = (),
) -> SemanticDecisionValidationReceipt:
    """Validate B-E collision, closure, extension, provenance, and result consistency."""

    if type(resolution) is not SemanticConvergenceResolution:
        raise TypeError("resolution must be an exact SemanticConvergenceResolution")

    core_state_ids = tuple(item.canonical_id for item in CORE_ADMISSIBILITY_STATES)
    core_outcome_ids = tuple(item.canonical_id for item in CORE_SEMANTIC_OUTCOME_KINDS)
    core_policy_ids = tuple(CORE_CONVERGENCE_POLICY_IDS)

    extension_admissibility_state_ids = _extension_ids(
        extension_admissibility_state_ids,
        owner="extension_admissibility_state_ids",
        core_ids=core_state_ids,
    )
    extension_outcome_kind_ids = _extension_ids(
        extension_outcome_kind_ids,
        owner="extension_outcome_kind_ids",
        core_ids=core_outcome_ids,
    )
    extension_policy_ids = _extension_ids(
        extension_policy_ids,
        owner="extension_policy_ids",
        core_ids=core_policy_ids,
    )

    allowed_state_ids = core_state_ids + extension_admissibility_state_ids
    allowed_outcome_ids = core_outcome_ids + extension_outcome_kind_ids
    allowed_policy_ids = core_policy_ids + extension_policy_ids

    _validate_convergence_set(
        resolution.convergence_set,
        allowed_state_ids=allowed_state_ids,
        allowed_policy_ids=allowed_policy_ids,
    )

    if resolution.outcome.kind_id not in allowed_outcome_ids:
        raise ValueError("undeclared semantic outcome kind identifier")

    members = _member_candidates(resolution.convergence_set)
    member_id_set = {id(item) for item in members}

    ranked_candidates = tuple(item.candidate for item in resolution.ranking)
    if any(id(item) not in member_id_set for item in ranked_candidates):
        raise ValueError("ranking contains candidate outside convergence members")
    if len({id(item) for item in ranked_candidates}) != len(ranked_candidates):
        raise ValueError("ranking contains duplicate candidate")
    ranks = tuple(item.rank for item in resolution.ranking)
    if len(set(ranks)) != len(ranks):
        raise ValueError("ranking contains duplicate rank")
    if ranks and ranks != tuple(range(1, len(ranks) + 1)):
        raise ValueError("ranking is not consecutive from rank 1")

    outcome_alternatives = resolution.outcome.alternatives
    if any(id(item) not in member_id_set for item in outcome_alternatives):
        raise ValueError("semantic outcome contains candidate outside convergence members")
    if len({id(item) for item in outcome_alternatives}) != len(outcome_alternatives):
        raise ValueError("semantic outcome contains duplicate candidate")

    expected = _apply_semantic_convergence_policy(resolution.convergence_set)
    expected_ranked = tuple(item.candidate for item in expected.ranking)
    if tuple(item.rank for item in resolution.ranking) != tuple(
        item.rank for item in expected.ranking
    ):
        raise ValueError("semantic convergence ranking disagrees with frozen E policy")
    if not _same_identity_tuple(ranked_candidates, expected_ranked):
        raise ValueError("semantic convergence ranked candidates disagree with frozen E policy")
    if resolution.outcome.kind_id != expected.outcome.kind_id:
        raise ValueError("semantic convergence outcome kind disagrees with frozen E policy")
    if not _same_identity_tuple(
        resolution.outcome.alternatives,
        expected.outcome.alternatives,
    ):
        raise ValueError(
            "semantic convergence outcome alternatives disagree with frozen E policy"
        )
    if resolution.outcome.payload != expected.outcome.payload:
        raise ValueError("semantic convergence outcome payload disagrees with frozen E policy")
    if resolution.outcome.provenance != expected.outcome.provenance:
        raise ValueError(
            "semantic convergence outcome provenance disagrees with frozen E policy"
        )
    if resolution.provenance != expected.provenance:
        raise ValueError("semantic convergence resolution provenance disagrees with frozen E policy")

    _require_unique_provenance(
        resolution.outcome.provenance,
        "SemanticOutcome.provenance",
    )
    _require_unique_provenance(
        resolution.provenance,
        "SemanticConvergenceResolution.provenance",
    )

    checks = (
        "extension-identifier-collision",
        "condition-evidence-closure",
        "condition-evidence-collision",
        "admissibility-state-closure",
        "candidate-identity-collision",
        "convergence-membership-closure",
        "policy-parameter-collision",
        "policy-extension-closure",
        "ranking-closure",
        "outcome-alternative-closure",
        "outcome-extension-closure",
        "policy-result-consistency",
        "provenance-integrity",
    )
    return SemanticDecisionValidationReceipt(
        resolution=resolution,
        extension_admissibility_state_ids=extension_admissibility_state_ids,
        extension_outcome_kind_ids=extension_outcome_kind_ids,
        extension_policy_ids=extension_policy_ids,
        provenance=resolution.provenance,
        checks=checks,
    )


def _validate_paradox_evidence_structure(
    evidence: ParadoxElevationEvidence,
) -> None:
    if type(evidence) is not ParadoxElevationEvidence:
        raise TypeError("evidence must be an exact ParadoxElevationEvidence")

    alternatives = evidence.resolution.outcome.alternatives
    alternative_ids = {id(item) for item in alternatives}
    observed_pairs = set()

    _require_unique_provenance(
        evidence.provenance,
        "ParadoxElevationEvidence.provenance",
    )

    for item in evidence.incompatibilities:
        if type(item) is not ParadoxIncompatibilityEvidence:
            raise TypeError(
                "ParadoxElevationEvidence.incompatibilities must contain exact "
                "ParadoxIncompatibilityEvidence values"
            )
        _require_unique_provenance(
            item.provenance,
            "ParadoxIncompatibilityEvidence.provenance",
        )
        if id(item.left) not in alternative_ids or id(item.right) not in alternative_ids:
            raise ValueError("Paradox incompatibility endpoint is outside outcome alternatives")
        if item.left is item.right:
            raise ValueError("Paradox incompatibility evidence contains a self-pair")

        left_index = next(
            index for index, candidate in enumerate(alternatives)
            if candidate is item.left
        )
        right_index = next(
            index for index, candidate in enumerate(alternatives)
            if candidate is item.right
        )
        pair = (
            min(left_index, right_index),
            max(left_index, right_index),
        )
        if pair in observed_pairs:
            raise ValueError("duplicate unordered Paradox incompatibility pair")
        observed_pairs.add(pair)


def validate_paradox_elevation_assessment(
    assessment: ParadoxElevationAssessment,
    *,
    extension_admissibility_state_ids: Tuple[str, ...] = (),
    extension_outcome_kind_ids: Tuple[str, ...] = (),
    extension_policy_ids: Tuple[str, ...] = (),
) -> ParadoxElevationValidationReceipt:
    """Validate one exact F eligibility assessment without redefining eligibility."""

    if type(assessment) is not ParadoxElevationAssessment:
        raise TypeError("assessment must be an exact ParadoxElevationAssessment")

    evidence = assessment.evidence
    _validate_paradox_evidence_structure(evidence)

    resolution_receipt = validate_semantic_convergence_resolution(
        evidence.resolution,
        extension_admissibility_state_ids=extension_admissibility_state_ids,
        extension_outcome_kind_ids=extension_outcome_kind_ids,
        extension_policy_ids=extension_policy_ids,
    )

    expected = _assess_paradox_elevation(evidence)
    if assessment.eligible is not expected.eligible:
        raise ValueError("Paradox Elevation eligibility disagrees with frozen F semantics")

    if expected.candidate_outcome is None:
        if assessment.candidate_outcome is not None:
            raise ValueError("ineligible Paradox assessment carries a candidate outcome")
    else:
        if type(assessment.candidate_outcome) is not SemanticOutcome:
            raise ValueError("eligible Paradox assessment omits candidate outcome")
        if assessment.candidate_outcome.kind_id != expected.candidate_outcome.kind_id:
            raise ValueError("Paradox candidate outcome kind disagrees with frozen F semantics")
        if not _same_identity_tuple(
            assessment.candidate_outcome.alternatives,
            expected.candidate_outcome.alternatives,
        ):
            raise ValueError(
                "Paradox candidate outcome alternatives disagree with frozen F semantics"
            )
        if assessment.candidate_outcome.payload != expected.candidate_outcome.payload:
            raise ValueError(
                "Paradox candidate outcome payload disagrees with frozen F semantics"
            )
        if assessment.candidate_outcome.provenance != expected.candidate_outcome.provenance:
            raise ValueError(
                "Paradox candidate outcome provenance disagrees with frozen F semantics"
            )
        _require_unique_provenance(
            assessment.candidate_outcome.provenance,
            "ParadoxElevationAssessment.candidate_outcome.provenance",
        )

    if assessment.provenance != expected.provenance:
        raise ValueError("Paradox Elevation assessment provenance disagrees with frozen F semantics")
    _require_unique_provenance(
        assessment.provenance,
        "ParadoxElevationAssessment.provenance",
    )

    checks = (
        "resolution-validation",
        "paradox-endpoint-closure",
        "paradox-pair-collision",
        "paradox-assessment-consistency",
        "paradox-provenance-integrity",
    )
    return ParadoxElevationValidationReceipt(
        assessment=assessment,
        resolution_receipt=resolution_receipt,
        provenance=assessment.provenance,
        checks=checks,
    )


def validate_elevated_semantic_state(
    state: ElevatedSemanticState,
    *,
    extension_admissibility_state_ids: Tuple[str, ...] = (),
    extension_outcome_kind_ids: Tuple[str, ...] = (),
    extension_policy_ids: Tuple[str, ...] = (),
) -> ElevatedSemanticStateValidationReceipt:
    """Validate one exact elevated state through its exact validated assessment."""

    if type(state) is not ElevatedSemanticState:
        raise TypeError("state must be an exact ElevatedSemanticState")

    assessment_receipt = validate_paradox_elevation_assessment(
        state.assessment,
        extension_admissibility_state_ids=extension_admissibility_state_ids,
        extension_outcome_kind_ids=extension_outcome_kind_ids,
        extension_policy_ids=extension_policy_ids,
    )
    if state.assessment.eligible is not True:
        raise ValueError("elevated semantic state references an ineligible assessment")

    expected = _elevate_paradox_assessment(state.assessment)
    if not _same_identity_tuple(state.alternatives, expected.alternatives):
        raise ValueError("elevated semantic-state alternative closure disagrees")
    if state.provenance != expected.provenance:
        raise ValueError("elevated semantic-state provenance disagrees")
    _require_unique_provenance(
        state.provenance,
        "ElevatedSemanticState.provenance",
    )

    checks = (
        "assessment-validation",
        "elevated-eligibility",
        "elevated-alternative-closure",
        "elevated-provenance-integrity",
    )
    return ElevatedSemanticStateValidationReceipt(
        state=state,
        assessment_receipt=assessment_receipt,
        provenance=state.provenance,
        checks=checks,
    )


__all__ = (
    "SemanticDecisionValidationReceipt",
    "ParadoxElevationValidationReceipt",
    "ElevatedSemanticStateValidationReceipt",
    "validate_semantic_convergence_resolution",
    "validate_paradox_elevation_assessment",
    "validate_elevated_semantic_state",
)
