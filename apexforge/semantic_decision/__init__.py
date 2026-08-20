"""P11.10 semantic-decision layer."""

from .convergence import (
    ConvergencePolicy,
    EvaluatedCandidate,
    SemanticConvergenceSet,
    construct_semantic_convergence_set,
)
from .evaluation import (
    AdmissibilityState,
    AdvancedConditionEvaluation,
    ConditionEvidence,
    CORE_ADMISSIBILITY_STATES,
    evaluate_advanced_condition,
)
from .model import (
    AdvancedCondition,
    CandidateAlternative,
    CORE_SEMANTIC_OUTCOME_KINDS,
    SemanticOutcome,
    SemanticOutcomeKind,
)
from .paradox import (
    ElevatedSemanticState,
    ParadoxElevationAssessment,
    ParadoxElevationEvidence,
    ParadoxIncompatibilityEvidence,
    assess_paradox_elevation,
    elevate_paradox_assessment,
)
from .projection import (
    SemanticDecisionDownstreamProjection,
    project_validated_semantic_decision,
)
from .reporting import (
    render_semantic_decision_downstream_projection_report,
)
from .resolution import (
    CORE_CONVERGENCE_POLICY_IDS,
    RankedCandidate,
    SemanticConvergenceResolution,
    apply_semantic_convergence_policy,
)
from .validation import (
    ElevatedSemanticStateValidationReceipt,
    ParadoxElevationValidationReceipt,
    SemanticDecisionValidationReceipt,
    validate_elevated_semantic_state,
    validate_paradox_elevation_assessment,
    validate_semantic_convergence_resolution,
)

__all__ = (
    "AdvancedCondition",
    "CandidateAlternative",
    "SemanticOutcomeKind",
    "SemanticOutcome",
    "CORE_SEMANTIC_OUTCOME_KINDS",
    "ConditionEvidence",
    "AdmissibilityState",
    "CORE_ADMISSIBILITY_STATES",
    "AdvancedConditionEvaluation",
    "evaluate_advanced_condition",
    "ConvergencePolicy",
    "EvaluatedCandidate",
    "SemanticConvergenceSet",
    "construct_semantic_convergence_set",
    "CORE_CONVERGENCE_POLICY_IDS",
    "RankedCandidate",
    "SemanticConvergenceResolution",
    "apply_semantic_convergence_policy",
    "ParadoxIncompatibilityEvidence",
    "ParadoxElevationEvidence",
    "ParadoxElevationAssessment",
    "ElevatedSemanticState",
    "assess_paradox_elevation",
    "elevate_paradox_assessment",
    "SemanticDecisionValidationReceipt",
    "ParadoxElevationValidationReceipt",
    "ElevatedSemanticStateValidationReceipt",
    "validate_semantic_convergence_resolution",
    "validate_paradox_elevation_assessment",
    "validate_elevated_semantic_state",
    "SemanticDecisionDownstreamProjection",
    "project_validated_semantic_decision",
    "render_semantic_decision_downstream_projection_report",
)
