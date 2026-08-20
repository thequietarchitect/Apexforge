"""One-way lowering from semantic-decision source records to P11.10 bridge inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.semantic_decision_source import (
    SemanticDecisionSourceCandidate,
    SemanticDecisionSourceDeclaration,
    SemanticDecisionSourceDocument,
    SemanticDecisionSourceIdentifier,
    SemanticDecisionSourceScalar,
)
from language.source import SourceSpan
from semantic_decision import (
    AdvancedCondition,
    CandidateAlternative,
    ConvergencePolicy,
    ParadoxIncompatibilityEvidence,
)


__all__ = (
    "LoweredSemanticDecisionCandidate",
    "LoweredSemanticDecisionDeclaration",
    "LoweredSemanticDecisionDocument",
    "SemanticDecisionSourceLoweringError",
    "lower_semantic_decision_source",
)


_EXPLICIT_ORDER_POLICY_IDS = frozenset(
    {
        "select.explicit-order",
        "rank.explicit-order",
    }
)


def _require_span(value: Any, field_name: str) -> SourceSpan:
    if not isinstance(value, SourceSpan):
        raise TypeError(f"{field_name} must be SourceSpan.")
    return value


def _require_exact_record(
    value: Any,
    expected_type: type,
    field_name: str,
):
    if type(value) is not expected_type:
        raise TypeError(
            f"{field_name} must be an exact {expected_type.__name__}."
        )
    return value


def _require_tuple(
    value: Any,
    item_type: type,
    field_name: str,
) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if any(type(item) is not item_type for item in value):
        raise TypeError(
            f"{field_name} must contain exact {item_type.__name__} values."
        )
    return value


def _require_exact_text(value: Any, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty and trimmed.")
    return value


def _require_provenance(value: Any, field_name: str) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    for index, item in enumerate(value):
        _require_exact_text(item, f"{field_name}[{index}]")
    return value


@dataclass(frozen=True)
class LoweredSemanticDecisionCandidate:
    """One P11.10 candidate plus an optional passive source condition."""

    candidate: CandidateAlternative
    condition: Optional[AdvancedCondition]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_record(
            self.candidate,
            CandidateAlternative,
            "LoweredSemanticDecisionCandidate.candidate",
        )
        if self.condition is not None:
            _require_exact_record(
                self.condition,
                AdvancedCondition,
                "LoweredSemanticDecisionCandidate.condition",
            )
        _require_span(self.span, "LoweredSemanticDecisionCandidate.span")


@dataclass(frozen=True)
class LoweredSemanticDecisionDeclaration:
    """One source decision lowered only to passive P11.10 bridge inputs."""

    identity: str
    candidates: tuple[LoweredSemanticDecisionCandidate, ...]
    policy: Optional[ConvergencePolicy]
    convergence_candidates: tuple[CandidateAlternative, ...]
    incompatibilities: tuple[ParadoxIncompatibilityEvidence, ...]
    paradox_requested: bool
    paradox_condition: Optional[AdvancedCondition]
    paradox_requirement: Optional[AdvancedCondition]
    span: SourceSpan
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_exact_text(
            self.identity,
            "LoweredSemanticDecisionDeclaration.identity",
        )
        _require_tuple(
            self.candidates,
            LoweredSemanticDecisionCandidate,
            "LoweredSemanticDecisionDeclaration.candidates",
        )
        if self.policy is not None:
            _require_exact_record(
                self.policy,
                ConvergencePolicy,
                "LoweredSemanticDecisionDeclaration.policy",
            )
        _require_tuple(
            self.convergence_candidates,
            CandidateAlternative,
            "LoweredSemanticDecisionDeclaration.convergence_candidates",
        )
        _require_tuple(
            self.incompatibilities,
            ParadoxIncompatibilityEvidence,
            "LoweredSemanticDecisionDeclaration.incompatibilities",
        )
        if type(self.paradox_requested) is not bool:
            raise TypeError(
                "LoweredSemanticDecisionDeclaration.paradox_requested "
                "must be an exact bool."
            )
        if self.paradox_condition is not None:
            _require_exact_record(
                self.paradox_condition,
                AdvancedCondition,
                "LoweredSemanticDecisionDeclaration.paradox_condition",
            )
        if self.paradox_requirement is not None:
            _require_exact_record(
                self.paradox_requirement,
                AdvancedCondition,
                "LoweredSemanticDecisionDeclaration.paradox_requirement",
            )
        if not self.paradox_requested and (
            self.paradox_condition is not None
            or self.paradox_requirement is not None
        ):
            raise ValueError(
                "Paradox condition/requirement requires paradox_requested=True."
            )
        _require_span(self.span, "LoweredSemanticDecisionDeclaration.span")
        _require_provenance(
            self.provenance,
            "LoweredSemanticDecisionDeclaration.provenance",
        )


@dataclass(frozen=True)
class LoweredSemanticDecisionDocument:
    """Immutable source-to-P11.10 bridge result for one parsed document."""

    decisions: tuple[LoweredSemanticDecisionDeclaration, ...]
    span: SourceSpan
    provenance: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_tuple(
            self.decisions,
            LoweredSemanticDecisionDeclaration,
            "LoweredSemanticDecisionDocument.decisions",
        )
        if not self.decisions:
            raise ValueError(
                "LoweredSemanticDecisionDocument.decisions must not be empty."
            )
        _require_span(self.span, "LoweredSemanticDecisionDocument.span")
        _require_provenance(
            self.provenance,
            "LoweredSemanticDecisionDocument.provenance",
        )


class SemanticDecisionSourceLoweringError(DiagnosticError):
    """One deterministic source-to-P11.10 bridge representability failure."""


def _provenance(span: SourceSpan) -> tuple[str, ...]:
    return (
        (
            f"source:{span.source_name}:"
            f"{span.start.offset}-{span.end.offset}"
        ),
    )


def _lowering_error(
    span: SourceSpan,
    message: str,
) -> SemanticDecisionSourceLoweringError:
    return SemanticDecisionSourceLoweringError(
        BuildDiagnostic(
            severity="error",
            code="APX-SEMANTIC-DECISION-LOWERING",
            message=message,
            stage="compile",
            span=span,
        )
    )


def _semantic_text(
    scalar: SemanticDecisionSourceScalar,
    field_name: str,
) -> str:
    _require_exact_record(
        scalar,
        SemanticDecisionSourceScalar,
        field_name,
    )
    text = scalar.text
    if not text or text != text.strip():
        raise _lowering_error(
            scalar.span,
            f"{field_name} must lower to a non-empty trimmed string.",
        )
    return text


def _condition(
    scalar: Optional[SemanticDecisionSourceScalar],
    *,
    identity: str,
) -> Optional[AdvancedCondition]:
    if scalar is None:
        return None
    _require_exact_record(
        scalar,
        SemanticDecisionSourceScalar,
        "semantic-decision condition scalar",
    )
    return AdvancedCondition(
        identity=identity,
        condition_kind=f"source.{scalar.kind}",
        payload=scalar.text,
        provenance=_provenance(scalar.span),
    )


def _candidate(
    decision: SemanticDecisionSourceDeclaration,
    source_candidate: SemanticDecisionSourceCandidate,
) -> LoweredSemanticDecisionCandidate:
    candidate = CandidateAlternative(
        identity=source_candidate.name.text,
        provenance=_provenance(source_candidate.span),
    )
    condition = _condition(
        source_candidate.condition,
        identity=(
            f"{decision.name.text}."
            f"{source_candidate.name.text}.when"
        ),
    )
    return LoweredSemanticDecisionCandidate(
        candidate=candidate,
        condition=condition,
        span=source_candidate.span,
    )


def _candidate_matches(
    reference: SemanticDecisionSourceIdentifier,
    candidates: tuple[LoweredSemanticDecisionCandidate, ...],
) -> tuple[CandidateAlternative, ...]:
    return tuple(
        item.candidate
        for item in candidates
        if item.candidate.identity == reference.text
    )


def _resolve_candidate(
    reference: SemanticDecisionSourceIdentifier,
    candidates: tuple[LoweredSemanticDecisionCandidate, ...],
    *,
    owner: str,
) -> CandidateAlternative:
    matches = _candidate_matches(reference, candidates)
    if not matches:
        raise _lowering_error(
            reference.span,
            f"{owner} references unknown candidate {reference.text!r}.",
        )
    if len(matches) != 1:
        raise _lowering_error(
            reference.span,
            f"{owner} references ambiguous candidate {reference.text!r}.",
        )
    return matches[0]


def _lower_declaration(
    source_decision: SemanticDecisionSourceDeclaration,
) -> LoweredSemanticDecisionDeclaration:
    candidates = tuple(
        _candidate(source_decision, item)
        for item in source_decision.candidates
    )

    incompatibilities = tuple(
        ParadoxIncompatibilityEvidence(
            left=_resolve_candidate(
                item.left,
                candidates,
                owner="incompatible declaration",
            ),
            right=_resolve_candidate(
                item.right,
                candidates,
                owner="incompatible declaration",
            ),
            materially_incompatible=True,
            provenance=_provenance(item.span),
        )
        for item in source_decision.incompatibilities
    )

    policy = None
    convergence_candidates: tuple[CandidateAlternative, ...] = ()
    if source_decision.convergence is not None:
        source_convergence = source_decision.convergence
        convergence_candidates = tuple(
            _resolve_candidate(
                item,
                candidates,
                owner="converge declaration",
            )
            for item in source_convergence.candidates
        )
        policy_id = _semantic_text(
            source_convergence.policy,
            "Semantic-decision convergence policy",
        )
        parameters = (
            (
                "order",
                tuple(
                    item.identity
                    for item in convergence_candidates
                ),
            ),
        ) if policy_id in _EXPLICIT_ORDER_POLICY_IDS else ()
        policy = ConvergencePolicy(
            identity=policy_id,
            parameters=parameters,
            provenance=_provenance(source_convergence.span),
        )

    paradox_requested = source_decision.paradox_elevation is not None
    paradox_condition = None
    paradox_requirement = None
    if source_decision.paradox_elevation is not None:
        source_paradox = source_decision.paradox_elevation
        paradox_condition = _condition(
            source_paradox.condition,
            identity=f"{source_decision.name.text}.paradox.when",
        )
        paradox_requirement = _condition(
            source_paradox.requirement,
            identity=f"{source_decision.name.text}.paradox.requires",
        )

    return LoweredSemanticDecisionDeclaration(
        identity=source_decision.name.text,
        candidates=candidates,
        policy=policy,
        convergence_candidates=convergence_candidates,
        incompatibilities=incompatibilities,
        paradox_requested=paradox_requested,
        paradox_condition=paradox_condition,
        paradox_requirement=paradox_requirement,
        span=source_decision.span,
        provenance=_provenance(source_decision.span),
    )


def lower_semantic_decision_source(
    document: SemanticDecisionSourceDocument,
) -> LoweredSemanticDecisionDocument:
    """Lower source structure to passive P11.10 objects without semantic execution."""

    if type(document) is not SemanticDecisionSourceDocument:
        raise TypeError(
            "lower_semantic_decision_source requires an exact "
            "SemanticDecisionSourceDocument."
        )

    return LoweredSemanticDecisionDocument(
        decisions=tuple(
            _lower_declaration(item)
            for item in document.decisions
        ),
        span=document.span,
        provenance=_provenance(document.span),
    )