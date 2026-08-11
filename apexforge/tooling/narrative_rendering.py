"""Pure deterministic P11.6J narrative session presentation and rendering.

The module projects frozen canonical structural material and one immutable
P11.6H session into an immutable presentation value, then renders that value
as stable text.  It does not read input, interpret narrative semantics, invoke
lifecycle operations, or perform persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Optional

from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from runtime.narrative_binding import NarrativeExecutableChoicePath
from tooling.narrative_session import (
    NarrativeSession,
    NarrativeSessionError,
    NarrativeSessionMaterial,
)


def _identity_text(identity: NarrativeIdentity) -> str:
    return f"{identity.kind}:{'/'.join(identity.path)}"


def _fact_key(
    fact: NarrativeStateFact,
) -> tuple[str, tuple[str, ...], str, str]:
    return (
        fact.subject.kind,
        fact.subject.path,
        fact.name,
        fact.value,
    )


def _path_key(
    path: NarrativeExecutableChoicePath,
) -> tuple[str, tuple[str, ...], int]:
    return path.choice.kind, path.choice.path, path.path_index


def _dialogue_key(
    dialogue,
) -> tuple[str, tuple[str, ...]]:
    return dialogue.identity.kind, dialogue.identity.path


def _require_optional_prose(value: object, field_name: str) -> None:
    if value is None:
        return
    if type(value) is not str or not value or "\r" in value:
        raise ValueError(f"{field_name} must be nonempty LF prose or None.")


def _require_association(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> None:
    """Fail closed before projecting artifact-associated session data."""

    if type(material) is not NarrativeSessionMaterial:
        raise TypeError("material must be exact NarrativeSessionMaterial.")
    if type(session) is not NarrativeSession:
        raise TypeError("session must be exact NarrativeSession.")
    if session.artifact_fingerprint != material.artifact_fingerprint:
        raise NarrativeSessionError("artifact_mismatch")
    if session.story != material.story:
        raise NarrativeSessionError("story_mismatch")
    if session.state.current_scene not in material.scenes:
        raise NarrativeSessionError("malformed_session")


@dataclass(frozen=True)
class NarrativeFactPresentation:
    """One exact canonical fact value prepared for stable display."""

    subject: NarrativeIdentity
    name: str
    value: str

    def __post_init__(self) -> None:
        if type(self.subject) is not NarrativeIdentity:
            raise TypeError("presented fact subject must be a narrative identity.")
        if type(self.name) is not str or not self.name:
            raise ValueError("presented fact name must be a non-empty exact str.")
        if type(self.value) is not str or not self.value:
            raise ValueError("presented fact value must be a non-empty exact str.")


@dataclass(frozen=True)
class NarrativeChoicePresentation:
    """One numbered structural path without a semantic legality claim."""

    number: int
    choice: NarrativeIdentity
    path_index: int
    path_label: str
    destination: NarrativeIdentity

    def __post_init__(self) -> None:
        if type(self.number) is not int or self.number < 1:
            raise ValueError("presented choice number must be a positive exact int.")
        if type(self.choice) is not NarrativeIdentity or self.choice.kind != "choice":
            raise TypeError("presented choice must have a choice identity.")
        if type(self.path_index) is not int or self.path_index < 0:
            raise ValueError("presented path index must be a non-negative exact int.")
        if type(self.path_label) is not str or not self.path_label:
            raise ValueError("presented path label must be a non-empty exact str.")
        if (
            type(self.destination) is not NarrativeIdentity
            or self.destination.kind != "scene"
        ):
            raise TypeError("presented destination must have a scene identity.")


@dataclass(frozen=True)
class NarrativeDialoguePresentation:
    """One current-scene authored dialogue item prepared for display."""

    identity: NarrativeIdentity
    speaker: NarrativeIdentity
    text: str

    def __post_init__(self) -> None:
        if type(self.identity) is not NarrativeIdentity or self.identity.kind != "dialogue":
            raise TypeError("presented dialogue must have a dialogue identity.")
        if type(self.speaker) is not NarrativeIdentity or self.speaker.kind != "character":
            raise TypeError("presented dialogue speaker must have a character identity.")
        if self.text is None:
            raise TypeError("presented dialogue text must be an exact str.")
        _require_optional_prose(self.text, "presented dialogue text")


@dataclass(frozen=True)
class NarrativeSessionPresentation:
    """Immutable human-facing projection of one exact narrative session."""

    story: NarrativeIdentity
    scene: NarrativeIdentity
    status: str
    termination_reason: Optional[str]
    transition_count: int
    facts: tuple[NarrativeFactPresentation, ...]
    choices: tuple[NarrativeChoicePresentation, ...]
    title: Optional[str] = None
    body: Optional[str] = None
    dialogues: tuple[NarrativeDialoguePresentation, ...] = ()

    def __post_init__(self) -> None:
        if type(self.story) is not NarrativeIdentity or self.story.kind != "story":
            raise TypeError("presentation story must have a story identity.")
        if type(self.scene) is not NarrativeIdentity or self.scene.kind != "scene":
            raise TypeError("presentation scene must have a scene identity.")
        if type(self.status) is not str or self.status not in ("active", "terminated"):
            raise ValueError("presentation status must be active or terminated.")
        if self.termination_reason is not None and (
            type(self.termination_reason) is not str
            or not self.termination_reason
        ):
            raise ValueError("presentation termination reason must be explicit.")
        if self.status == "active" and self.termination_reason is not None:
            raise ValueError("active presentation cannot have a termination reason.")
        if type(self.transition_count) is not int or self.transition_count < 0:
            raise ValueError("presentation transition count must be non-negative.")
        _require_optional_prose(self.title, "presentation title")
        _require_optional_prose(self.body, "presentation body")
        if type(self.dialogues) is not tuple or any(
            type(dialogue) is not NarrativeDialoguePresentation
            for dialogue in self.dialogues
        ):
            raise TypeError(
                "presentation dialogues must be exact immutable dialogues."
            )
        if type(self.facts) is not tuple or any(
            type(fact) is not NarrativeFactPresentation for fact in self.facts
        ):
            raise TypeError("presentation facts must be exact immutable facts.")
        if type(self.choices) is not tuple or any(
            type(choice) is not NarrativeChoicePresentation
            for choice in self.choices
        ):
            raise TypeError("presentation choices must be exact immutable choices.")
        if tuple(choice.number for choice in self.choices) != tuple(
            range(1, len(self.choices) + 1)
        ):
            raise ValueError("presentation choice numbers must be consecutive.")
        if self.status == "terminated" and self.choices:
            raise ValueError("terminated presentation cannot expose choices.")


def narrative_session_presentation(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> NarrativeSessionPresentation:
    """Project canonical material/session data into a deterministic model."""

    _require_association(material, session)
    state = session.state
    facts = tuple(
        NarrativeFactPresentation(fact.subject, fact.name, fact.value)
        for fact in sorted(state.facts, key=_fact_key)
    )
    scene = next(
        (
            scene
            for scene in material.scene_records
            if scene.identity == state.current_scene
        ),
        None,
    )
    dialogues = tuple(
        NarrativeDialoguePresentation(
            identity=dialogue.identity,
            speaker=dialogue.speaker,
            text=dialogue.text,
        )
        for dialogue in sorted(
            (
                dialogue
                for dialogue in material.dialogues
                if dialogue.scene == state.current_scene
                and dialogue.text is not None
            ),
            key=_dialogue_key,
        )
    )

    choices: tuple[NarrativeChoicePresentation, ...] = ()
    if not state.termination.is_terminated:
        current_paths = sorted(
            (
                path
                for path in material.bindings.paths
                if path.source_scene == state.current_scene
            ),
            key=_path_key,
        )
        choices = tuple(
            NarrativeChoicePresentation(
                number=number,
                choice=path.choice,
                path_index=path.path_index,
                path_label=path.path_label,
                destination=path.destination,
            )
            for number, path in enumerate(current_paths, start=1)
        )

    return NarrativeSessionPresentation(
        story=state.story,
        scene=state.current_scene,
        status=state.termination.status,
        termination_reason=state.termination.reason,
        transition_count=len(state.choice_history),
        title=None if scene is None else scene.title,
        body=None if scene is None else scene.body,
        dialogues=dialogues,
        facts=facts,
        choices=choices,
    )


def render_narrative_presentation(
    presentation: NarrativeSessionPresentation,
) -> str:
    """Render one exact structured presentation with stable LF delimiters."""

    if type(presentation) is not NarrativeSessionPresentation:
        raise TypeError("presentation must be exact NarrativeSessionPresentation.")

    lines = [
        "ApexForge narrative session",
        f"Story: {_identity_text(presentation.story)}",
        f"Scene: {_identity_text(presentation.scene)}",
        f"Status: {presentation.status}",
    ]
    if presentation.termination_reason is not None:
        lines.append(f"Termination reason: {presentation.termination_reason}")
    lines.append(f"Transitions: {presentation.transition_count}")
    if presentation.title is not None:
        lines.extend(("Title:", presentation.title))
    if presentation.body is not None:
        lines.extend(("Body:", presentation.body))
    if presentation.dialogues:
        lines.append("Dialogue:")
        for dialogue in presentation.dialogues:
            lines.extend(
                (
                    f"  {_identity_text(dialogue.identity)}",
                    f"    Speaker: {_identity_text(dialogue.speaker)}",
                    "    Text:",
                    dialogue.text,
                )
            )
    lines.append("Facts:")
    if presentation.facts:
        lines.extend(
            "  "
            + _identity_text(fact.subject)
            + f":{fact.name}={fact.value}"
            for fact in presentation.facts
        )
    else:
        lines.append("  (none)")

    lines.append("Choices:")
    if presentation.status == "terminated":
        lines.append("  (session terminated)")
    elif not presentation.choices:
        lines.append("  (none)")
    else:
        lines.extend(
            f"  {choice.number}. {_identity_text(choice.choice)} "
            f"path[{choice.path_index}] "
            f"{json.dumps(choice.path_label, ensure_ascii=False)} -> "
            f"{_identity_text(choice.destination)}"
            for choice in presentation.choices
        )
    return "\n".join(lines) + "\n"


def render_narrative_session(
    material: NarrativeSessionMaterial,
    session: NarrativeSession,
) -> str:
    """Return deterministic text for one associated immutable session."""

    return render_narrative_presentation(
        narrative_session_presentation(material, session)
    )


__all__ = (
    "NarrativeChoicePresentation",
    "NarrativeDialoguePresentation",
    "NarrativeFactPresentation",
    "NarrativeSessionPresentation",
    "narrative_session_presentation",
    "render_narrative_presentation",
    "render_narrative_session",
)
