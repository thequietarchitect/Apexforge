"""Opt-in composition of the frozen narrative analysis stages."""

from __future__ import annotations

from dataclasses import dataclass

from language.narrative_graph import (
    NarrativeSemanticGraph,
    build_narrative_semantic_graph,
)
from language.narrative_lowering import lower_narrative_source
from language.narrative_model import NarrativeStory
from language.narrative_parser import parse_narrative_source
from language.narrative_source import NarrativeSourceDocument
from language.narrative_validation import (
    NarrativeValidationReport,
    validate_narrative_semantic_graph,
)


__all__ = (
    "NarrativeSourceAnalysis",
    "analyze_narrative_source",
)


@dataclass(frozen=True)
class NarrativeSourceAnalysis:
    """Exact immutable products of one opt-in narrative source analysis."""

    source_document: NarrativeSourceDocument
    semantic_story: NarrativeStory
    semantic_graph: NarrativeSemanticGraph
    validation_report: NarrativeValidationReport

    def __post_init__(self) -> None:
        if type(self.source_document) is not NarrativeSourceDocument:
            raise TypeError(
                "NarrativeSourceAnalysis.source_document must be an exact "
                "NarrativeSourceDocument."
            )
        if type(self.semantic_story) is not NarrativeStory:
            raise TypeError(
                "NarrativeSourceAnalysis.semantic_story must be an exact "
                "NarrativeStory."
            )
        if type(self.semantic_graph) is not NarrativeSemanticGraph:
            raise TypeError(
                "NarrativeSourceAnalysis.semantic_graph must be an exact "
                "NarrativeSemanticGraph."
            )
        if type(self.validation_report) is not NarrativeValidationReport:
            raise TypeError(
                "NarrativeSourceAnalysis.validation_report must be an exact "
                "NarrativeValidationReport."
            )

        source_story_name = self.source_document.story.name.text
        semantic_identity = self.semantic_story.identity
        if (
            semantic_identity.kind != "story"
            or semantic_identity.path != (source_story_name,)
        ):
            raise ValueError(
                "NarrativeSourceAnalysis source and semantic story "
                "identities must agree."
            )
        if self.semantic_graph.story != semantic_identity:
            raise ValueError(
                "NarrativeSourceAnalysis semantic graph must describe the "
                "semantic story identity."
            )
        if self.validation_report.story != semantic_identity:
            raise ValueError(
                "NarrativeSourceAnalysis validation report must describe "
                "the semantic story identity."
            )


def analyze_narrative_source(
    source: str,
    *,
    source_name: str = "<memory>",
) -> NarrativeSourceAnalysis:
    """Run parse, lower, graph, and passive validation in fixed order."""

    source_document = parse_narrative_source(
        source,
        source_name=source_name,
    )
    semantic_story = lower_narrative_source(source_document)
    semantic_graph = build_narrative_semantic_graph(semantic_story)
    validation_report = validate_narrative_semantic_graph(
        semantic_graph
    )
    return NarrativeSourceAnalysis(
        source_document=source_document,
        semantic_story=semantic_story,
        semantic_graph=semantic_graph,
        validation_report=validation_report,
    )
