"""Manifest-ordered composition of analyzed narrative source documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from language.narrative_analysis import NarrativeSourceAnalysis, analyze_narrative_source
from language.narrative_graph import NarrativeSemanticGraph, build_narrative_semantic_graph
from language.narrative_model import NarrativeStory
from language.narrative_validation import (
    NarrativeValidationReport,
    validate_narrative_semantic_graph,
)


class NarrativeProjectAnalysisError(ValueError):
    """One deterministic narrative project composition failure."""


@dataclass(frozen=True)
class NarrativeProjectAnalysis:
    """Immutable products of manifest-ordered multi-source narrative analysis."""

    source_analyses: Tuple[NarrativeSourceAnalysis, ...]
    semantic_story: NarrativeStory
    semantic_graph: NarrativeSemanticGraph
    validation_report: NarrativeValidationReport

    def __post_init__(self) -> None:
        if type(self.source_analyses) is not tuple or not self.source_analyses:
            raise ValueError(
                "NarrativeProjectAnalysis.source_analyses must be a non-empty exact tuple."
            )
        if any(
            type(analysis) is not NarrativeSourceAnalysis
            for analysis in self.source_analyses
        ):
            raise TypeError(
                "NarrativeProjectAnalysis.source_analyses must contain exact "
                "NarrativeSourceAnalysis values."
            )
        if type(self.semantic_story) is not NarrativeStory:
            raise TypeError(
                "NarrativeProjectAnalysis.semantic_story must be an exact NarrativeStory."
            )
        if type(self.semantic_graph) is not NarrativeSemanticGraph:
            raise TypeError(
                "NarrativeProjectAnalysis.semantic_graph must be an exact "
                "NarrativeSemanticGraph."
            )
        if type(self.validation_report) is not NarrativeValidationReport:
            raise TypeError(
                "NarrativeProjectAnalysis.validation_report must be an exact "
                "NarrativeValidationReport."
            )
        if self.semantic_graph.story != self.semantic_story.identity:
            raise ValueError(
                "NarrativeProjectAnalysis graph and semantic story identities disagree."
            )
        if self.validation_report.story != self.semantic_story.identity:
            raise ValueError(
                "NarrativeProjectAnalysis validation report and semantic story "
                "identities disagree."
            )


def _normalize_sources(
    sources: Tuple[Tuple[str, str], ...],
) -> Tuple[Tuple[str, str], ...]:
    if type(sources) is not tuple:
        raise TypeError(
            "narrative project sources must be an exact tuple of (name, source) pairs."
        )
    if not sources:
        raise NarrativeProjectAnalysisError(
            "narrative project requires at least one source."
        )

    normalized = []
    for index, item in enumerate(sources):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(
                f"narrative project source[{index}] must be an exact two-item tuple."
            )
        source_name, source = item
        if type(source_name) is not str or not source_name or source_name != source_name.strip():
            raise NarrativeProjectAnalysisError(
                f"narrative project source[{index} name must be non-empty and trimmed."
            )
        if type(source) is not str:
            raise TypeError(
                f"narrative project source[{index}] text must be an exact str."
            )
        normalized.append((source_name, source))
    return tuple(normalized)


def analyze_narrative_project_sources(
    sources: Tuple[Tuple[str, str], ...],
) -> NarrativeProjectAnalysis:
    """Analyze complete story documents and merge semantics in supplied order."""

    normalized = _normalize_sources(sources)
    analyses = tuple(
        analyze_narrative_source(source, source_name=source_name)
        for source_name, source in normalized
     )

    story_identity = analyses[0].semantic_story.identity
    for index, analysis in enumerate(analyses[1:], start=1):
        if analysis.semantic_story.identity != story_identity:
            raise NarrativeProjectAnalysisError(
                "narrative project sources must declare one shared story identity; "
                f"source[{index}] declares {analysis.semantic_story.identity!r} "
                f"instead of {story_identity!r}."
            )

    stories = tuple(analysis.semantic_story for analysis in analyses)
    merged_story = NarrativeStory(
        identity=story_identity,
        characters=tuple(
            record for story in stories for record in story.characters
        ),
        scenes=tuple(
            record for story in stories for record in story.scenes
        ),
        dialogues=tuple(
            record for story in stories for record in story.dialogues
         ),
        choices=tuple(
            record for story in stories for record in story.choices
        ),
        perspectives=tuple(
            record for story in stories for record in story.perspectives
        ),
        timelines=tuple(
            record for story in stories for record in story.timelines
         ),
        states=tuple(
            record for story in stories for record in story.states
        ),
        continuities=tuple(
            record for story in stories for record in story.continuities
         ),
    )
    graph = build_narrative_semantic_graph(merged_story)
    report = validate_narrative_semantic_graph(graph)
    return NarrativeProjectAnalysis(
        source_analyses=analyses,
        semantic_story=merged_story,
        semantic_graph=graph,
        validation_report=report,
    )


__all__ = (
    "NarrativeProjectAnalysis",
    "NarrativeProjectAnalysisError",
    "analyze_narrative_project_sources",
)
