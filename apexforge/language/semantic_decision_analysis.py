"""Opt-in composition of the frozen semantic-decision source bridge stages."""

from __future__ import annotations

from dataclasses import dataclass

from language.semantic_decision_lowering import (
    LoweredSemanticDecisionDocument,
    lower_semantic_decision_source,
)
from language.semantic_decision_parser import parse_semantic_decision_source
from language.semantic_decision_source import SemanticDecisionSourceDocument
from language.semantic_decision_source_validation import (
    validate_semantic_decision_source_bridge,
)


__all__ = (
    "SemanticDecisionSourceAnalysis",
    "analyze_semantic_decision_source",
)


@dataclass(frozen=True)
class SemanticDecisionSourceAnalysis:
    """Exact immutable products of one opt-in semantic-decision source analysis."""

    source_document: SemanticDecisionSourceDocument
    semantic_bridge: LoweredSemanticDecisionDocument

    def __post_init__(self) -> None:
        if type(self.source_document) is not SemanticDecisionSourceDocument:
            raise TypeError(
                "SemanticDecisionSourceAnalysis.source_document must be an exact "
                "SemanticDecisionSourceDocument."
            )
        if type(self.semantic_bridge) is not LoweredSemanticDecisionDocument:
            raise TypeError(
                "SemanticDecisionSourceAnalysis.semantic_bridge must be an exact "
                "LoweredSemanticDecisionDocument."
            )

        source_identities = tuple(
            item.name.text
            for item in self.source_document.decisions
        )
        lowered_identities = tuple(
            item.identity
            for item in self.semantic_bridge.decisions
        )
        if source_identities != lowered_identities:
            raise ValueError(
                "SemanticDecisionSourceAnalysis source and lowered decision "
                "identities must agree in source order."
            )
        if self.semantic_bridge.span != self.source_document.span:
            raise ValueError(
                "SemanticDecisionSourceAnalysis source and bridge spans must agree."
            )


def analyze_semantic_decision_source(
    source: str,
    *,
    source_name: str = "<memory>",
) -> SemanticDecisionSourceAnalysis:
    """Run parse, lower, and source/bridge validation in fixed order."""

    source_document = parse_semantic_decision_source(
        source,
        source_name=source_name,
    )
    semantic_bridge = lower_semantic_decision_source(source_document)
    validated_bridge = validate_semantic_decision_source_bridge(
        semantic_bridge
    )
    if validated_bridge is not semantic_bridge:
        raise RuntimeError(
            "semantic-decision source validation must return the exact bridge"
        )

    return SemanticDecisionSourceAnalysis(
        source_document=source_document,
        semantic_bridge=semantic_bridge,
    )