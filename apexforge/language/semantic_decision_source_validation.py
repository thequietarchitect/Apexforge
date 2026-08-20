"""Source/bridge validation for lowered ApexForge semantic-decision documents."""

from __future__ import annotations

from typing import Any

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.semantic_decision_lowering import (
    LoweredSemanticDecisionDeclaration,
    LoweredSemanticDecisionDocument,
)
from language.source import SourceSpan


__all__ = (
    "SemanticDecisionSourceValidationError",
    "validate_semantic_decision_source_bridge",
)


class SemanticDecisionSourceValidationError(DiagnosticError):
    """One deterministic semantic-decision source/bridge validation failure."""


def _validation_error(
    span: SourceSpan,
    message: str,
) -> SemanticDecisionSourceValidationError:
    return SemanticDecisionSourceValidationError(
        BuildDiagnostic(
            severity="error",
            code="APX-SEMANTIC-DECISION-SOURCE-VALIDATION",
            message=message,
            stage="compile",
            span=span,
        )
    )


def _candidate_objects(
    decision: LoweredSemanticDecisionDeclaration,
) -> tuple[Any, ...]:
    return tuple(item.candidate for item in decision.candidates)


def _contains_exact(
    values: tuple[Any, ...],
    target: Any,
) -> bool:
    return any(item is target for item in values)


def _validate_decision(
    decision: LoweredSemanticDecisionDeclaration,
) -> None:
    if not decision.candidates:
        raise _validation_error(
            decision.span,
            f"Decision {decision.identity!r} must declare at least one candidate.",
        )

    seen_candidate_identities = set()
    for item in decision.candidates:
        identity = item.candidate.identity
        if identity in seen_candidate_identities:
            raise _validation_error(
                item.span,
                (
                    f"Decision {decision.identity!r} declares duplicate candidate "
                    f"identity {identity!r}."
                ),
            )
        seen_candidate_identities.add(identity)

    owned_candidates = _candidate_objects(decision)

    if decision.policy is None:
        if decision.convergence_candidates:
            raise _validation_error(
                decision.span,
                (
                    f"Decision {decision.identity!r} has convergence candidate "
                    "references without a convergence policy."
                ),
            )
    elif not decision.convergence_candidates:
        raise _validation_error(
            decision.span,
            (
                f"Decision {decision.identity!r} has a convergence policy "
                "without convergence candidate references."
            ),
        )

    for candidate in decision.convergence_candidates:
        if not _contains_exact(owned_candidates, candidate):
            raise _validation_error(
                decision.span,
                (
                    f"Decision {decision.identity!r} convergence references a "
                    "candidate object not owned by the decision."
                ),
            )

    for incompatibility in decision.incompatibilities:
        if (
            not _contains_exact(owned_candidates, incompatibility.left)
            or not _contains_exact(owned_candidates, incompatibility.right)
        ):
            raise _validation_error(
                decision.span,
                (
                    f"Decision {decision.identity!r} incompatibility evidence "
                    "references a candidate object not owned by the decision."
                ),
            )


def validate_semantic_decision_source_bridge(
    document: LoweredSemanticDecisionDocument,
) -> LoweredSemanticDecisionDocument:
    """Validate source/bridge coherence and return the exact input on success."""

    if type(document) is not LoweredSemanticDecisionDocument:
        raise TypeError(
            "validate_semantic_decision_source_bridge requires an exact "
            "LoweredSemanticDecisionDocument."
        )

    seen_decision_identities = set()
    for decision in document.decisions:
        if decision.identity in seen_decision_identities:
            raise _validation_error(
                decision.span,
                f"Duplicate semantic-decision identity {decision.identity!r}.",
            )
        seen_decision_identities.add(decision.identity)
        _validate_decision(decision)

    return document