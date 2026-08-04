"""Passive immutable narrative semantic records for P11.5B."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Optional as _Optional


__all__ = (
    "NarrativeIdentity",
    "NarrativeCharacter",
    "NarrativeScene",
    "NarrativeDialogue",
    "NarrativeChoicePath",
    "NarrativeChoice",
    "NarrativePerspective",
    "NarrativeTimeline",
    "NarrativeStateFact",
    "NarrativeState",
    "NarrativeContinuityConstraint",
    "NarrativeContinuity",
    "NarrativeStory",
)


_IDENTITY_KINDS = frozenset(
    {
        "story",
        "character",
        "scene",
        "dialogue",
        "choice",
        "perspective",
        "timeline",
        "narrative_state",
        "continuity",
    }
)


def _require_trimmed_string(value: object, field_name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be nonblank.")
    if value != value.strip():
        raise ValueError(f"{field_name} must already be trimmed.")


def _require_optional_trimmed_string(value: object, field_name: str) -> None:
    if value is None:
        return
    _require_trimmed_string(value, field_name)


def _require_identity(
    value: object,
    expected_kind: str,
    field_name: str,
) -> None:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    if value.kind != expected_kind:
        raise ValueError(f"{field_name} must have kind {expected_kind!r}.")


def _require_identity_tuple(
    value: object,
    *,
    field_name: str,
    expected_kind: _Optional[str] = None,
    allow_empty: bool,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty.")
    for item in value:
        if type(item) is not NarrativeIdentity:
            raise TypeError(
                f"every {field_name} item must be an exact NarrativeIdentity."
            )
        if expected_kind is not None and item.kind != expected_kind:
            raise ValueError(
                f"every {field_name} item must have kind {expected_kind!r}."
            )


def _require_record_tuple(
    value: object,
    *,
    field_name: str,
    record_type: type,
    allow_empty: bool,
) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty.")
    for item in value:
        if type(item) is not record_type:
            raise TypeError(
                f"every {field_name} item must be an exact {record_type.__name__}."
            )


@_dataclass(frozen=True)
class NarrativeIdentity:
    kind: str
    path: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.kind) is not str:
            raise TypeError("NarrativeIdentity.kind must be an exact str.")
        if self.kind not in _IDENTITY_KINDS:
            raise ValueError(f"unsupported narrative identity kind {self.kind!r}.")
        if type(self.path) is not tuple:
            raise TypeError("NarrativeIdentity.path must be an exact tuple.")
        if not self.path:
            raise ValueError("NarrativeIdentity.path must not be empty.")
        for segment in self.path:
            _require_trimmed_string(segment, "NarrativeIdentity.path segment")


@_dataclass(frozen=True)
class NarrativeCharacter:
    identity: NarrativeIdentity

    def __post_init__(self) -> None:
        _require_identity(self.identity, "character", "NarrativeCharacter.identity")


@_dataclass(frozen=True)
class NarrativeScene:
    identity: NarrativeIdentity

    def __post_init__(self) -> None:
        _require_identity(self.identity, "scene", "NarrativeScene.identity")


@_dataclass(frozen=True)
class NarrativeDialogue:
    identity: NarrativeIdentity
    scene: NarrativeIdentity
    speaker: NarrativeIdentity
    participants: tuple[NarrativeIdentity, ...]

    def __post_init__(self) -> None:
        _require_identity(self.identity, "dialogue", "NarrativeDialogue.identity")
        _require_identity(self.scene, "scene", "NarrativeDialogue.scene")
        _require_identity(self.speaker, "character", "NarrativeDialogue.speaker")
        _require_identity_tuple(
            self.participants,
            field_name="NarrativeDialogue.participants",
            expected_kind="character",
            allow_empty=False,
        )


@_dataclass(frozen=True)
class NarrativeChoicePath:
    label: str
    destination: NarrativeIdentity
    condition: _Optional[str] = None
    consequence: _Optional[str] = None

    def __post_init__(self) -> None:
        _require_trimmed_string(self.label, "NarrativeChoicePath.label")
        _require_identity(
            self.destination,
            "scene",
            "NarrativeChoicePath.destination",
        )
        _require_optional_trimmed_string(
            self.condition,
            "NarrativeChoicePath.condition",
        )
        _require_optional_trimmed_string(
            self.consequence,
            "NarrativeChoicePath.consequence",
        )


@_dataclass(frozen=True)
class NarrativeChoice:
    identity: NarrativeIdentity
    scene: NarrativeIdentity
    paths: tuple[NarrativeChoicePath, ...]

    def __post_init__(self) -> None:
        _require_identity(self.identity, "choice", "NarrativeChoice.identity")
        _require_identity(self.scene, "scene", "NarrativeChoice.scene")
        _require_record_tuple(
            self.paths,
            field_name="NarrativeChoice.paths",
            record_type=NarrativeChoicePath,
            allow_empty=False,
        )


@_dataclass(frozen=True)
class NarrativePerspective:
    identity: NarrativeIdentity
    viewpoint: _Optional[NarrativeIdentity] = None

    def __post_init__(self) -> None:
        _require_identity(
            self.identity,
            "perspective",
            "NarrativePerspective.identity",
        )
        if self.viewpoint is not None:
            _require_identity(
                self.viewpoint,
                "character",
                "NarrativePerspective.viewpoint",
            )


@_dataclass(frozen=True)
class NarrativeTimeline:
    identity: NarrativeIdentity
    scenes: tuple[NarrativeIdentity, ...]

    def __post_init__(self) -> None:
        _require_identity(self.identity, "timeline", "NarrativeTimeline.identity")
        _require_identity_tuple(
            self.scenes,
            field_name="NarrativeTimeline.scenes",
            expected_kind="scene",
            allow_empty=True,
        )


@_dataclass(frozen=True)
class NarrativeStateFact:
    subject: NarrativeIdentity
    name: str
    value: str

    def __post_init__(self) -> None:
        if type(self.subject) is not NarrativeIdentity:
            raise TypeError(
                "NarrativeStateFact.subject must be an exact NarrativeIdentity."
            )
        _require_trimmed_string(self.name, "NarrativeStateFact.name")
        _require_trimmed_string(self.value, "NarrativeStateFact.value")


@_dataclass(frozen=True)
class NarrativeState:
    identity: NarrativeIdentity
    facts: tuple[NarrativeStateFact, ...]

    def __post_init__(self) -> None:
        _require_identity(
            self.identity,
            "narrative_state",
            "NarrativeState.identity",
        )
        _require_record_tuple(
            self.facts,
            field_name="NarrativeState.facts",
            record_type=NarrativeStateFact,
            allow_empty=True,
        )


@_dataclass(frozen=True)
class NarrativeContinuityConstraint:
    subjects: tuple[NarrativeIdentity, ...]
    assertion: str

    def __post_init__(self) -> None:
        _require_identity_tuple(
            self.subjects,
            field_name="NarrativeContinuityConstraint.subjects",
            allow_empty=False,
        )
        _require_trimmed_string(
            self.assertion,
            "NarrativeContinuityConstraint.assertion",
        )


@_dataclass(frozen=True)
class NarrativeContinuity:
    identity: NarrativeIdentity
    constraints: tuple[NarrativeContinuityConstraint, ...]

    def __post_init__(self) -> None:
        _require_identity(
            self.identity,
            "continuity",
            "NarrativeContinuity.identity",
        )
        _require_record_tuple(
            self.constraints,
            field_name="NarrativeContinuity.constraints",
            record_type=NarrativeContinuityConstraint,
            allow_empty=True,
        )


@_dataclass(frozen=True)
class NarrativeStory:
    identity: NarrativeIdentity
    characters: tuple[NarrativeCharacter, ...]
    scenes: tuple[NarrativeScene, ...]
    dialogues: tuple[NarrativeDialogue, ...]
    choices: tuple[NarrativeChoice, ...]
    perspectives: tuple[NarrativePerspective, ...]
    timelines: tuple[NarrativeTimeline, ...]
    states: tuple[NarrativeState, ...]
    continuities: tuple[NarrativeContinuity, ...]

    def __post_init__(self) -> None:
        _require_identity(self.identity, "story", "NarrativeStory.identity")
        collections = (
            ("characters", self.characters, NarrativeCharacter),
            ("scenes", self.scenes, NarrativeScene),
            ("dialogues", self.dialogues, NarrativeDialogue),
            ("choices", self.choices, NarrativeChoice),
            ("perspectives", self.perspectives, NarrativePerspective),
            ("timelines", self.timelines, NarrativeTimeline),
            ("states", self.states, NarrativeState),
            ("continuities", self.continuities, NarrativeContinuity),
        )
        for name, value, record_type in collections:
            _require_record_tuple(
                value,
                field_name=f"NarrativeStory.{name}",
                record_type=record_type,
                allow_empty=True,
            )
