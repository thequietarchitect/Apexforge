"""Deterministic P11.6F narrative build-artifact routing.

This module is the packaging boundary between the opt-in P11.5 semantic
analysis/P11.6C binding material and ApexForge's existing build-artifact
serializer.  It contains no narrative execution, transition, trace,
diagnostic, or termination policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from language.narrative_analysis import NarrativeSourceAnalysis
from language.narrative_model import (
    NarrativeIdentity,
    NarrativeStory,
)
from runtime.narrative_binding import (
    NarrativeExecutableBindingSet,
    NarrativeExecutableChoicePath,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
)


NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1 = "apexforge.narrative-build-artifact/v1"
NARRATIVE_BUILD_ARTIFACT_SCHEMA = "apexforge.narrative-build-artifact/v2"


class NarrativeArtifactError(ValueError):
    """Raised when compiled narrative material cannot form one artifact."""


def _require_trimmed_string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string.")
    return value


def _identity_payload(identity: NarrativeIdentity) -> dict[str, Any]:
    return {
        "kind": identity.kind,
        "path": list(identity.path),
    }


def _predicate_payload(predicate: NarrativeFactPredicate) -> dict[str, Any]:
    return {
        "operator": predicate.operator,
        "subject": _identity_payload(predicate.subject),
        "value": predicate.value,
        "name": predicate.name,
    }


def _assignment_payload(assignment: NarrativeFactAssignment) -> dict[str, Any]:
    return {
        "subject": _identity_payload(assignment.subject),
        "value": assignment.value,
        "name": assignment.name,
    }


def _choice_path_payload(path: NarrativeExecutableChoicePath) -> dict[str, Any]:
    return {
        "choice": _identity_payload(path.choice),
        "source_scene": _identity_payload(path.source_scene),
        "path_index": path.path_index,
        "path_label": path.path_label,
        "destination": _identity_payload(path.destination),
        "source_condition": path.source_condition,
        "condition": (
            None
            if path.condition is None
            else _predicate_payload(path.condition)
        ),
        "source_consequence": path.source_consequence,
        "assignments": [
            _assignment_payload(assignment)
            for assignment in path.assignments
        ],
    }


def _story_payload(story: NarrativeStory) -> dict[str, Any]:
    def identity_records(records: tuple[object, ...]) -> list[dict[str, Any]]:
        return [
            {"identity": _identity_payload(record.identity)}
            for record in records
        ]

    return {
        "identity": _identity_payload(story.identity),
        "characters": identity_records(story.characters),
        "scenes": [
            {
                "identity": _identity_payload(scene.identity),
                "title": scene.title,
                "body": scene.body,
            }
            for scene in story.scenes
        ],
        "dialogues": [
            {
                "identity": _identity_payload(dialogue.identity),
                "scene": _identity_payload(dialogue.scene),
                "speaker": _identity_payload(dialogue.speaker),
                "participants": [
                    _identity_payload(participant)
                    for participant in dialogue.participants
                ],
                "text": dialogue.text,
            }
            for dialogue in story.dialogues
        ],
        "choices": [
            {
                "identity": _identity_payload(choice.identity),
                "scene": _identity_payload(choice.scene),
                "paths": [
                    {
                        "label": path.label,
                        "destination": _identity_payload(path.destination),
                        "condition": path.condition,
                        "consequence": path.consequence,
                    }
                    for path in choice.paths
                ],
            }
            for choice in story.choices
        ],
        "perspectives": [
            {
                "identity": _identity_payload(perspective.identity),
                "viewpoint": (
                    None
                    if perspective.viewpoint is None
                    else _identity_payload(perspective.viewpoint)
                ),
            }
            for perspective in story.perspectives
        ],
        "timelines": [
            {
                "identity": _identity_payload(timeline.identity),
                "scenes": [
                    _identity_payload(scene)
                    for scene in timeline.scenes
                ],
            }
            for timeline in story.timelines
        ],
        "states": [
            {
                "identity": _identity_payload(state.identity),
                "facts": [
                    {
                        "subject": _identity_payload(fact.subject),
                        "name": fact.name,
                        "value": fact.value,
                    }
                    for fact in state.facts
                ],
            }
            for state in story.states
        ],
        "continuities": [
            {
                "identity": _identity_payload(continuity.identity),
                "constraints": [
                    {
                        "subjects": [
                            _identity_payload(subject)
                            for subject in constraint.subjects
                        ],
                        "assertion": constraint.assertion,
                    }
                    for constraint in continuity.constraints
                ],
            }
            for continuity in story.continuities
        ],
    }


@dataclass(frozen=True)
class NarrativeBuildArtifact:
    """Immutable narrative material associated with one canonical build."""

    source_name: str
    story: NarrativeStory
    bindings: NarrativeExecutableBindingSet

    def __post_init__(self) -> None:
        _require_trimmed_string(
            self.source_name,
            "NarrativeBuildArtifact.source_name",
        )
        if type(self.story) is not NarrativeStory:
            raise TypeError(
                "NarrativeBuildArtifact.story must be an exact NarrativeStory."
            )
        if type(self.bindings) is not NarrativeExecutableBindingSet:
            raise TypeError(
                "NarrativeBuildArtifact.bindings must be an exact "
                "NarrativeExecutableBindingSet."
            )
        if self.bindings.story != self.story.identity:
            raise NarrativeArtifactError(
                "narrative artifact story and executable bindings disagree."
            )

    def payload(self) -> dict[str, Any]:
        """Return a fresh canonical-JSON-compatible payload projection."""

        return {
            "schema": NARRATIVE_BUILD_ARTIFACT_SCHEMA,
            "source": self.source_name,
            "story": _story_payload(self.story),
            "bindings": {
                "story": _identity_payload(self.bindings.story),
                "paths": [
                    _choice_path_payload(path)
                    for path in self.bindings.paths
                ],
            },
        }


def route_narrative_build_material(
    analysis: NarrativeSourceAnalysis,
    bindings: NarrativeExecutableBindingSet,
    *,
    source_name: Optional[str] = None,
) -> NarrativeBuildArtifact:
    """Route exact compiled narrative semantics into immutable build material."""

    if type(analysis) is not NarrativeSourceAnalysis:
        raise TypeError(
            "route_narrative_build_material requires an exact "
            "NarrativeSourceAnalysis."
        )
    if type(bindings) is not NarrativeExecutableBindingSet:
        raise TypeError(
            "route_narrative_build_material requires an exact "
            "NarrativeExecutableBindingSet."
        )
    selected_source_name = (
        analysis.source_document.span.source_name
        if source_name is None
        else source_name
    )
    return NarrativeBuildArtifact(
        source_name=selected_source_name,
        story=analysis.semantic_story,
        bindings=bindings,
    )


def narrative_build_artifact_payload(
    artifact: NarrativeBuildArtifact,
) -> Mapping[str, Any]:
    """Project one exact narrative artifact for canonical build JSON."""

    if type(artifact) is not NarrativeBuildArtifact:
        raise TypeError(
            "narrative_build_artifact_payload requires an exact "
            "NarrativeBuildArtifact."
        )
    return artifact.payload()


__all__ = (
    "NARRATIVE_BUILD_ARTIFACT_SCHEMA",
    "NARRATIVE_BUILD_ARTIFACT_SCHEMA_V1",
    "NarrativeArtifactError",
    "NarrativeBuildArtifact",
    "narrative_build_artifact_payload",
    "route_narrative_build_material",
)
