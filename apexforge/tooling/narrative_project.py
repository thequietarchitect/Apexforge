"""Canonical project-level entry and start semantics for narrative projects."""

from __future__ import annotations

from typing import Optional

from language.narrative_model import NarrativeIdentity, NarrativeStory


class NarrativeProjectEntryError(ValueError):
    """The selected project entry does not identify the authored story."""


class NarrativeProjectStartError(ValueError):
    """The authored narrative does not provide one canonical start scene."""


def _require_story(story: NarrativeStory) -> NarrativeStory:
    if type(story) is not NarrativeStory:
        raise TypeError("narrative project semantics require an exact NarrativeStory.")
    return story


def resolve_narrative_project_entry(
    story: NarrativeStory,
    entry: Optional[str],
) -> NarrativeIdentity:
    """Resolve omitted, bare, or canonical story entry spelling."""

    selected_story = _require_story(story)
    identity = selected_story.identity
    bare = ".".join(identity.path)
    canonical = f"{identity.kind}:{bare}"

    if entry is None:
        return identity
    if type(entry) is not str:
        raise TypeError("narrative project entry must be a str or None.")
    if not entry or entry != entry.strip():
        raise NarrativeProjectEntryError(
            "narrative project entry must be a non-empty trimmed string."
        )
    if entry not in (bare, canonical):
        raise NarrativeProjectEntryError(
            f"narrative project entry {entry!r} does not identify {canonical!r}."
        )
    return identity


def resolve_narrative_start_scene(story: NarrativeStory) -> NarrativeIdentity:
    """Resolve the first scene of the first authored timeline as canonical start."""

    selected_story = _require_story(story)
    if not selected_story.timelines:
        raise NarrativeProjectStartError(
            "Narrative project requires an authored timeline with at least one scene."
        )
    first_timeline = selected_story.timelines[0]
    if not first_timeline.scenes:
        raise NarrativeProjectStartError(
            "Narrative project requires an authored timeline with at least one scene."
        )
    start = first_timeline.scenes[0]
    if type(start) is not NarrativeIdentity or start.kind != "scene":
        raise NarrativeProjectStartError(
            "Narrative project start must identify a scene."
        )
    return start


__all__ = (
    "NarrativeProjectEntryError",
    "NarrativeProjectStartError",
    "resolve_narrative_project_entry",
    "resolve_narrative_start_scene",
)
