"""Experimental manifest-ordered multi-source narrative analysis contract."""

from __future__ import annotations

from language.narrative_project_analysis import (
    NarrativeProjectAnalysisError,
    analyze_narrative_project_sources,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type: type, action, message: str) -> None:
    try:
        action()
    except expected_type:
        return
    raise AssertionError(message)


def identity_names(records) -> tuple[str, ...]:
    return tuple(record.identity.path[0] for record in records)


def main() -> None:
    first = """story SplitStory {
    character Hero

    scene Start {
        body "The journey begins."
    }

    dialogue Greeting {
        scene Start
        speaker Guide
        participants [Hero, Guide]
        text "Follow me."
    }
}
"""
    second = """story SplitStory {
    character Guide

    scene End {
        body "The journey ends."
    }

    choice Advance {
        scene Start
        path "Continue" {
            destination End
        }
    }

    narrative_state Opening {
        fact Hero.ready = yes
    }

    timeline Main {
        scenes [Start, End]
    }
}
"""

    analysis = analyze_narrative_project_sources(
        (
            ("01-start.apex", first),
            ("02-end.apex", second),
        )
    )
    require(len(analysis.source_analyses) == 2, "project analysis source count changed")
    require(
        analysis.semantic_story.identity.kind == "story"
        and analysis.semantic_story.identity.path == ("SplitStory",),
        "merged project story identity changed",
    )
    require(
        identity_names(analysis.semantic_story.characters) == ("Hero", "Guide"),
        "character merge order did not follow manifest source order",
    )
    require(
        identity_names(analysis.semantic_story.scenes) == ("Start", "End"),
        "scene merge order did not follow manifest source order",
    )
    require(
        identity_names(analysis.semantic_story.dialogues) == ("Greeting",),
        "dialogue merge changed",
    )
    require(
        identity_names(analysis.semantic_story.choices) == ("Advance",),
        "choice merge changed",
    )
    require(
        identity_names(analysis.semantic_story.timelines) == ("Main",),
        "timeline merge changed",
    )
    require(
        not any(
            finding.classification == "referenced_only_identity"
            for finding in analysis.validation_report.findings
        ),
        "cross-source references remained unresolved at project validation",
    )
    print("Manifest-ordered narrative semantic merge: PASS")
    print("Cross-source narrative reference closure: PASS")

    reversed_analysis = analyze_narrative_project_sources(
        (
            ("02-end.apex", second),
            ("01-start.apex", first),
        )
    )
    require(
        identity_names(reversed_analysis.semantic_story.characters) == ("Guide", "Hero"),
        "project analysis ignored supplied source order",
    )
    require(
        identity_names(reversed_analysis.semantic_story.scenes) == ("End", "Start"),
        "project scene merge ignored supplied source order",
    )
    print("Narrative source-order determinism: PASS")

    duplicate = analyze_narrative_project_sources(
        (
            ("a.apex", "story DuplicateStory { character Echo }"),
            ("b.apex", "story DuplicateStory { character Echo }"),
        )
    )
    require(
        any(
            finding.classification == "duplicate_declaration"
            for finding in duplicate.validation_report.findings
        ),
        "cross-source duplicate declaration was not classified",
    )
    print("Cross-source duplicate validation: PASS")

    require_raises(
        NarrativeProjectAnalysisError,
        lambda: analyze_narrative_project_sources(
            (
                ("a.apex", "story FirstStory {}"),
                ("b.apex", "story OtherStory {}"),
            )
        ),
        "conflicting multi-source story identities were accepted",
    )
    require_raises(
        NarrativeProjectAnalysisError,
        lambda: analyze_narrative_project_sources(()),
        "empty narrative project source set was accepted",
    )
    print("Multi-source narrative identity boundary: PASS")
    print("Experimental multi-source narrative analysis: PASS")


if __name__ == "__main__":
    main()
