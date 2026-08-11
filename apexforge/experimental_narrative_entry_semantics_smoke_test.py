"""Experimental canonical narrative project entry/start semantics."""

from __future__ import annotations

from dataclasses import replace

from language.narrative_analysis import analyze_narrative_source
from tooling.narrative_project import (
    NarrativeProjectEntryError,
    NarrativeProjectStartError,
    resolve_narrative_project_entry,
    resolve_narrative_start_scene,
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


def main() -> None:
    source = """story EntryStory {
    scene First { body "Declared first." }
    scene Second { body "Timeline starts here." }
    timeline Main {
        scenes [Second, First]
    }
}
"""
    story = analyze_narrative_source(source, source_name="story.apex").semantic_story

    omitted = resolve_narrative_project_entry(story, None)
    bare = resolve_narrative_project_entry(story, "EntryStory")
    canonical = resolve_narrative_project_entry(story, "story:EntryStory")
    require(omitted == story.identity, "omitted narrative entry did not select the story")
    require(bare == story.identity, "bare narrative story entry did not resolve canonically")
    require(canonical == story.identity, "canonical narrative story entry did not resolve")
    require_raises(NarrativeProjectEntryError, lambda: resolve_narrative_project_entry(story, "OtherStory"), "wrong narrative story entry was accepted")
    require_raises(NarrativeProjectEntryError, lambda: resolve_narrative_project_entry(story, "scene:Second"), "scene identity was accepted as project entry")
    print("Narrative project story-entry resolution: PASS")

    start = resolve_narrative_start_scene(story)
    require(start.kind == "scene" and start.path == ("Second",), "narrative start did not follow first timeline order")
    print("Narrative canonical start-scene resolution: PASS")

    no_timelines = replace(story, timelines=())
    require_raises(NarrativeProjectStartError, lambda: resolve_narrative_start_scene(no_timelines), "story without timeline gained an implicit start")
    empty_timeline = replace(story.timelines[0], scenes=())
    empty_start = replace(story, timelines=(empty_timeline,))
    require_raises(NarrativeProjectStartError, lambda: resolve_narrative_start_scene(empty_start), "empty timeline gained an implicit start")
    print("Narrative invalid-start rejection: PASS")
    print("Experimental narrative entry/start semantics: PASS")


if __name__ == "__main__":
    main()
