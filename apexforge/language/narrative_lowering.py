"""One-way lowering from narrative source records to semantic records."""

from __future__ import annotations

from typing import Optional

from language.diagnostics import BuildDiagnostic, DiagnosticError
from language.narrative_model import (
    NarrativeCharacter,
    NarrativeChoice,
    NarrativeChoicePath,
    NarrativeContinuity,
    NarrativeContinuityConstraint,
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativePerspective,
    NarrativeScene,
    NarrativeState,
    NarrativeStateFact,
    NarrativeStory,
    NarrativeTimeline,
)
from language.narrative_source import (
    NarrativeSourceChoicePath,
    NarrativeSourceDocument,
    NarrativeSourceIdentifier,
    NarrativeSourceReference,
    NarrativeSourceScalar,
)


__all__ = (
    "NarrativeSemanticLoweringError",
    "lower_narrative_source",
)


class NarrativeSemanticLoweringError(DiagnosticError):
    """One deterministic source-to-semantic representability failure."""


def _lowering_error(
    scalar: NarrativeSourceScalar,
    field_name: str,
) -> NarrativeSemanticLoweringError:
    return NarrativeSemanticLoweringError(
        BuildDiagnostic(
            severity="error",
            code="APX-NARRATIVE-LOWERING",
            message=(
                f"{field_name} must lower to a non-empty trimmed string."
            ),
            stage="compile",
            span=scalar.span,
        )
    )


def _semantic_text(
    scalar: NarrativeSourceScalar,
    field_name: str,
) -> str:
    text = scalar.text
    if not text or text != text.strip():
        raise _lowering_error(scalar, field_name)
    return text


def _optional_semantic_text(
    scalar: Optional[NarrativeSourceScalar],
    field_name: str,
) -> Optional[str]:
    if scalar is None:
        return None
    return _semantic_text(scalar, field_name)


def _declared_identity(
    kind: str,
    name: NarrativeSourceIdentifier,
) -> NarrativeIdentity:
    return NarrativeIdentity(kind, (name.text,))


def _reference_identity(
    reference: NarrativeSourceReference,
) -> NarrativeIdentity:
    return NarrativeIdentity(
        reference.expected_kind,
        (reference.name.text,),
    )


def _lower_choice_path(
    path: NarrativeSourceChoicePath,
) -> NarrativeChoicePath:
    return NarrativeChoicePath(
        label=_semantic_text(
            path.label,
            "Narrative choice-path label",
        ),
        destination=_reference_identity(path.destination),
        condition=_optional_semantic_text(
            path.condition,
            "Narrative choice-path condition",
        ),
        consequence=_optional_semantic_text(
            path.consequence,
            "Narrative choice-path consequence",
        ),
    )


def lower_narrative_source(
    document: NarrativeSourceDocument,
) -> NarrativeStory:
    """Lower one exact source document into one exact semantic story."""

    if type(document) is not NarrativeSourceDocument:
        raise TypeError(
            "lower_narrative_source requires an exact "
            "NarrativeSourceDocument."
        )

    source_story = document.story

    characters = tuple(
        NarrativeCharacter(
            identity=_declared_identity("character", character.name),
        )
        for character in source_story.characters
    )

    scenes = tuple(
        NarrativeScene(
            identity=_declared_identity("scene", scene.name),
        )
        for scene in source_story.scenes
    )

    dialogues = tuple(
        NarrativeDialogue(
            identity=_declared_identity("dialogue", dialogue.name),
            scene=_reference_identity(dialogue.scene),
            speaker=_reference_identity(dialogue.speaker),
            participants=tuple(
                _reference_identity(participant)
                for participant in dialogue.participants
            ),
        )
        for dialogue in source_story.dialogues
    )

    choices = tuple(
        NarrativeChoice(
            identity=_declared_identity("choice", choice.name),
            scene=_reference_identity(choice.scene),
            paths=tuple(
                _lower_choice_path(path)
                for path in choice.paths
            ),
        )
        for choice in source_story.choices
    )

    perspectives = tuple(
        NarrativePerspective(
            identity=_declared_identity(
                "perspective",
                perspective.name,
            ),
            viewpoint=_reference_identity(perspective.viewpoint),
        )
        for perspective in source_story.perspectives
    )

    timelines = tuple(
        NarrativeTimeline(
            identity=_declared_identity("timeline", timeline.name),
            scenes=tuple(
                _reference_identity(scene)
                for scene in timeline.scenes
            ),
        )
        for timeline in source_story.timelines
    )

    states = tuple(
        NarrativeState(
            identity=_declared_identity(
                "narrative_state",
                state.name,
            ),
            facts=tuple(
                NarrativeStateFact(
                    subject=_reference_identity(fact.subject),
                    name=fact.name.text,
                    value=_semantic_text(
                        fact.value,
                        "Narrative state-fact value",
                    ),
                )
                for fact in state.facts
            ),
        )
        for state in source_story.states
    )

    continuities = tuple(
        NarrativeContinuity(
            identity=_declared_identity(
                "continuity",
                continuity.name,
            ),
            constraints=tuple(
                NarrativeContinuityConstraint(
                    subjects=tuple(
                        _reference_identity(subject)
                        for subject in constraint.subjects
                    ),
                    assertion=_semantic_text(
                        constraint.assertion,
                        "Narrative continuity assertion",
                    ),
                )
                for constraint in continuity.constraints
            ),
        )
        for continuity in source_story.continuities
    )

    return NarrativeStory(
        identity=_declared_identity("story", source_story.name),
        characters=characters,
        scenes=scenes,
        dialogues=dialogues,
        choices=choices,
        perspectives=perspectives,
        timelines=timelines,
        states=states,
        continuities=continuities,
    )
