"""Manifest-ordered semantic-decision project analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.semantic_decision_analysis import (
    SemanticDecisionSourceAnalysis,
    analyze_semantic_decision_source,
)
from language.source import SourceSpan


class SemanticDecisionProjectAnalysisError(DiagnosticError):
    """One deterministic semantic-decision project composition failure."""


def _project_error(
    span: SourceSpan,
    message: str,
    *,
    related_spans: Tuple[SourceSpan, ...] = (),
) -> SemanticDecisionProjectAnalysisError:
    return SemanticDecisionProjectAnalysisError(
        BuildDiagnostic(
            severity="error",
            code="APX-SEMANTIC-DECISION-PROJECT",
            message=message,
            stage="link",
            span=span,
            related_spans=related_spans,
        )
    )


@dataclass(frozen=True)
class SemanticDecisionProjectAnalysis:
    """Immutable manifest-ordered semantic-decision source analyses."""

    source_analyses: Tuple[SemanticDecisionSourceAnalysis, ...]

    def __post_init__(self) -> None:
        if type(self.source_analyses) is not tuple or not self.source_analyses:
            raise ValueError(
                "SemanticDecisionProjectAnalysis.source_analyses must be "
                "a non-empty exact tuple."
            )
        if any(
            type(analysis) is not SemanticDecisionSourceAnalysis
            for analysis in self.source_analyses
        ):
            raise TypeError(
                "SemanticDecisionProjectAnalysis.source_analyses must contain "
                "exact SemanticDecisionSourceAnalysis values."
            )

        seen = set()
        for analysis in self.source_analyses:
            for decision in analysis.semantic_bridge.decisions:
                if decision.identity in seen:
                    raise ValueError(
                        "SemanticDecisionProjectAnalysis contains duplicate "
                        "semantic-decision identities."
                    )
                seen.add(decision.identity)


def _normalize_sources(
    sources: Tuple[Tuple[str, str], ...],
) -> Tuple[Tuple[str, str], ...]:
    if type(sources) is not tuple:
        raise TypeError(
            "semantic-decision project sources must be an exact tuple of "
            "(name, source) pairs."
        )
    if not sources:
        raise ValueError(
            "semantic-decision project requires at least one source."
        )

    normalized = []
    for index, item in enumerate(sources):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                f"semantic-decision project source[{index}] must be an exact "
                "two-item tuple."
            )
        source_name, source = item
        if (
            type(source_name) is not str
            or not source_name
            or source_name != source_name.strip()
        ):
            raise ValueError(
                f"semantic-decision project source[{index}] name must be "
                "non-empty and trimmed."
            )
        if type(source) is not str:
            raise TypeError(
                f"semantic-decision project source[{index}] text must be "
                "an exact str."
            )
        normalized.append((source_name, source))
    return tuple(normalized)


def analyze_semantic_decision_project_sources(
    sources: Tuple[Tuple[str, str], ...],
) -> SemanticDecisionProjectAnalysis:
    """Analyze semantic-decision sources and enforce project identity uniqueness."""

    normalized = _normalize_sources(sources)
    analyses = tuple(
        analyze_semantic_decision_source(
            source,
            source_name=source_name,
        )
        for source_name, source in normalized
    )

    first_span_by_identity = {}
    for analysis in analyses:
        for decision in analysis.semantic_bridge.decisions:
            first_span = first_span_by_identity.get(decision.identity)
            if first_span is not None:
                raise _project_error(
                    decision.span,
                    (
                        "Duplicate semantic-decision identity "
                        f"{decision.identity!r} across project sources."
                    ),
                    related_spans=(first_span,),
                )
            first_span_by_identity[decision.identity] = decision.span

    return SemanticDecisionProjectAnalysis(
        source_analyses=analyses,
    )


__all__ = (
    "SemanticDecisionProjectAnalysis",
    "SemanticDecisionProjectAnalysisError",
    "analyze_semantic_decision_project_sources",
)