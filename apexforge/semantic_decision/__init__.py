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
from .resolution import (
    CORE_CONVERGENCE_POLICY_IDS,
    RankedCandidate,
    SemanticConvergenceResolution,
    apply_semantic_convergence_policy,
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
)
