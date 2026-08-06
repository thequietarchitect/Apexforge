"""Immutable source-provenance AST records for narrative syntax."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from language.source import SourceSpan


__all__ = (
    "NarrativeSourceIdentifier",
    "NarrativeSourceScalar",
    "NarrativeSourceReference",
    "NarrativeSourceCharacter",
    "NarrativeSourceScene",
    "NarrativeSourceDialogue",
    "NarrativeSourceChoicePath",
    "NarrativeSourceChoice",
    "NarrativeSourcePerspective",
    "NarrativeSourceTimeline",
    "NarrativeSourceStateFact",
    "NarrativeSourceState",
    "NarrativeSourceContinuityConstraint",
    "NarrativeSourceContinuity",
    "NarrativeSourceStory",
    "NarrativeSourceDocument",
)


_NARRATIVE_KINDS = frozenset(
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

_SCALAR_KINDS = frozenset({"identifier", "string", "boolean"})


def _require_span(value: Any, field_name: str) -> SourceSpan:
    if not isinstance(value, SourceSpan):
        raise TypeError(f"{field_name} must be SourceSpan.")
    return value


def _require_exact_text(
    value: Any,
    field_name: str,
    *,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty.")
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace.")
    return value


def _require_exact_record(
    value: Any,
    expected_type: type,
    field_name: str,
):
    if type(value) is not expected_type:
        raise TypeError(
            f"{field_name} must be an exact {expected_type.__name__}."
        )
    return value


def _require_tuple(
    value: Any,
    item_type: type,
    field_name: str,
) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be an exact tuple.")
    if any(type(item) is not item_type for item in value):
        raise TypeError(
            f"{field_name} must contain exact {item_type.__name__} values."
        )
    return value


@dataclass(frozen=True)
class NarrativeSourceIdentifier:
    """One exact bare source identifier and its complete token span."""

    text: str
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_text(self.text, "NarrativeSourceIdentifier.text")
        _require_span(self.span, "NarrativeSourceIdentifier.span")


@dataclass(frozen=True)
class NarrativeSourceScalar:
    """One exact identifier, quoted-string, or boolean source scalar."""

    kind: str
    text: str
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_text(self.kind, "NarrativeSourceScalar.kind")
        if self.kind not in _SCALAR_KINDS:
            raise ValueError(
                f"unsupported narrative source scalar kind {self.kind!r}."
            )
        if type(self.text) is not str:
            raise TypeError("NarrativeSourceScalar.text must be an exact str.")
        if self.kind in {"identifier", "boolean"}:
            _require_exact_text(
                self.text,
                "NarrativeSourceScalar.text",
            )
        if self.kind == "boolean" and self.text not in {"true", "false"}:
            raise ValueError(
                "NarrativeSourceScalar boolean text must be 'true' or 'false'."
            )
        _require_span(self.span, "NarrativeSourceScalar.span")


@dataclass(frozen=True)
class NarrativeSourceReference:
    """One unresolved exact source name with an expected narrative kind."""

    expected_kind: str
    name: NarrativeSourceIdentifier

    def __post_init__(self) -> None:
        _require_exact_text(
            self.expected_kind,
            "NarrativeSourceReference.expected_kind",
        )
        if self.expected_kind not in _NARRATIVE_KINDS:
            raise ValueError(
                "NarrativeSourceReference.expected_kind is unsupported."
            )
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceReference.name",
        )


@dataclass(frozen=True)
class NarrativeSourceCharacter:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceCharacter.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceCharacter.name",
        )
        _require_span(self.span, "NarrativeSourceCharacter.span")


@dataclass(frozen=True)
class NarrativeSourceScene:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceScene.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceScene.name",
        )
        _require_span(self.span, "NarrativeSourceScene.span")


@dataclass(frozen=True)
class NarrativeSourceDialogue:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    scene_keyword_span: SourceSpan
    scene: NarrativeSourceReference
    speaker_keyword_span: SourceSpan
    speaker: NarrativeSourceReference
    participants_keyword_span: SourceSpan
    participants: tuple[NarrativeSourceReference, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceDialogue.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceDialogue.name",
        )
        _require_span(
            self.scene_keyword_span,
            "NarrativeSourceDialogue.scene_keyword_span",
        )
        _require_exact_record(
            self.scene,
            NarrativeSourceReference,
            "NarrativeSourceDialogue.scene",
        )
        if self.scene.expected_kind != "scene":
            raise ValueError("NarrativeSourceDialogue.scene must expect scene.")
        _require_span(
            self.speaker_keyword_span,
            "NarrativeSourceDialogue.speaker_keyword_span",
        )
        _require_exact_record(
            self.speaker,
            NarrativeSourceReference,
            "NarrativeSourceDialogue.speaker",
        )
        if self.speaker.expected_kind != "character":
            raise ValueError(
                "NarrativeSourceDialogue.speaker must expect character."
            )
        _require_span(
            self.participants_keyword_span,
            "NarrativeSourceDialogue.participants_keyword_span",
        )
        _require_tuple(
            self.participants,
            NarrativeSourceReference,
            "NarrativeSourceDialogue.participants",
        )
        if not self.participants:
            raise ValueError(
                "NarrativeSourceDialogue.participants must not be empty."
            )
        if any(
            item.expected_kind != "character"
            for item in self.participants
        ):
            raise ValueError(
                "NarrativeSourceDialogue participants must expect character."
            )
        _require_span(self.span, "NarrativeSourceDialogue.span")


@dataclass(frozen=True)
class NarrativeSourceChoicePath:
    keyword_span: SourceSpan
    label: NarrativeSourceScalar
    destination_keyword_span: SourceSpan
    destination: NarrativeSourceReference
    span: SourceSpan
    condition_keyword_span: Optional[SourceSpan] = None
    condition: Optional[NarrativeSourceScalar] = None
    consequence_keyword_span: Optional[SourceSpan] = None
    consequence: Optional[NarrativeSourceScalar] = None

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourceChoicePath.keyword_span",
        )
        _require_exact_record(
            self.label,
            NarrativeSourceScalar,
            "NarrativeSourceChoicePath.label",
        )
        if self.label.kind != "string" or not self.label.text:
            raise ValueError(
                "NarrativeSourceChoicePath.label must be a non-empty string scalar."
            )
        _require_span(
            self.destination_keyword_span,
            "NarrativeSourceChoicePath.destination_keyword_span",
        )
        _require_exact_record(
            self.destination,
            NarrativeSourceReference,
            "NarrativeSourceChoicePath.destination",
        )
        if self.destination.expected_kind != "scene":
            raise ValueError(
                "NarrativeSourceChoicePath.destination must expect scene."
            )
        _require_span(self.span, "NarrativeSourceChoicePath.span")
        self._require_optional_scalar_pair(
            self.condition_keyword_span,
            self.condition,
            "condition",
        )
        self._require_optional_scalar_pair(
            self.consequence_keyword_span,
            self.consequence,
            "consequence",
        )

    @staticmethod
    def _require_optional_scalar_pair(
        keyword_span: Optional[SourceSpan],
        value: Optional[NarrativeSourceScalar],
        field_name: str,
    ) -> None:
        if keyword_span is None and value is None:
            return
        if keyword_span is None or value is None:
            raise ValueError(
                f"NarrativeSourceChoicePath.{field_name} keyword and value "
                "must be present together."
            )
        _require_span(
            keyword_span,
            f"NarrativeSourceChoicePath.{field_name}_keyword_span",
        )
        _require_exact_record(
            value,
            NarrativeSourceScalar,
            f"NarrativeSourceChoicePath.{field_name}",
        )


@dataclass(frozen=True)
class NarrativeSourceChoice:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    scene_keyword_span: SourceSpan
    scene: NarrativeSourceReference
    paths: tuple[NarrativeSourceChoicePath, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceChoice.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceChoice.name",
        )
        _require_span(
            self.scene_keyword_span,
            "NarrativeSourceChoice.scene_keyword_span",
        )
        _require_exact_record(
            self.scene,
            NarrativeSourceReference,
            "NarrativeSourceChoice.scene",
        )
        if self.scene.expected_kind != "scene":
            raise ValueError("NarrativeSourceChoice.scene must expect scene.")
        _require_tuple(
            self.paths,
            NarrativeSourceChoicePath,
            "NarrativeSourceChoice.paths",
        )
        if not self.paths:
            raise ValueError("NarrativeSourceChoice.paths must not be empty.")
        _require_span(self.span, "NarrativeSourceChoice.span")


@dataclass(frozen=True)
class NarrativeSourcePerspective:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    viewpoint_keyword_span: SourceSpan
    viewpoint: NarrativeSourceReference
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourcePerspective.keyword_span",
        )
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourcePerspective.name",
        )
        _require_span(
            self.viewpoint_keyword_span,
            "NarrativeSourcePerspective.viewpoint_keyword_span",
        )
        _require_exact_record(
            self.viewpoint,
            NarrativeSourceReference,
            "NarrativeSourcePerspective.viewpoint",
        )
        if self.viewpoint.expected_kind != "character":
            raise ValueError(
                "NarrativeSourcePerspective.viewpoint must expect character."
            )
        _require_span(self.span, "NarrativeSourcePerspective.span")


@dataclass(frozen=True)
class NarrativeSourceTimeline:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    scenes_keyword_span: SourceSpan
    scenes: tuple[NarrativeSourceReference, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourceTimeline.keyword_span",
        )
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceTimeline.name",
        )
        _require_span(
            self.scenes_keyword_span,
            "NarrativeSourceTimeline.scenes_keyword_span",
        )
        _require_tuple(
            self.scenes,
            NarrativeSourceReference,
            "NarrativeSourceTimeline.scenes",
        )
        if any(item.expected_kind != "scene" for item in self.scenes):
            raise ValueError(
                "NarrativeSourceTimeline scenes must expect scene."
            )
        _require_span(self.span, "NarrativeSourceTimeline.span")


@dataclass(frozen=True)
class NarrativeSourceStateFact:
    keyword_span: SourceSpan
    subject: NarrativeSourceReference
    name: NarrativeSourceIdentifier
    value: NarrativeSourceScalar
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourceStateFact.keyword_span",
        )
        _require_exact_record(
            self.subject,
            NarrativeSourceReference,
            "NarrativeSourceStateFact.subject",
        )
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceStateFact.name",
        )
        _require_exact_record(
            self.value,
            NarrativeSourceScalar,
            "NarrativeSourceStateFact.value",
        )
        _require_span(self.span, "NarrativeSourceStateFact.span")


@dataclass(frozen=True)
class NarrativeSourceState:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    facts: tuple[NarrativeSourceStateFact, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceState.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceState.name",
        )
        _require_tuple(
            self.facts,
            NarrativeSourceStateFact,
            "NarrativeSourceState.facts",
        )
        _require_span(self.span, "NarrativeSourceState.span")


@dataclass(frozen=True)
class NarrativeSourceContinuityConstraint:
    keyword_span: SourceSpan
    subjects: tuple[NarrativeSourceReference, ...]
    assertion: NarrativeSourceScalar
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourceContinuityConstraint.keyword_span",
        )
        _require_tuple(
            self.subjects,
            NarrativeSourceReference,
            "NarrativeSourceContinuityConstraint.subjects",
        )
        if not self.subjects:
            raise ValueError(
                "NarrativeSourceContinuityConstraint.subjects must not be empty."
            )
        _require_exact_record(
            self.assertion,
            NarrativeSourceScalar,
            "NarrativeSourceContinuityConstraint.assertion",
        )
        if self.assertion.kind != "string":
            raise ValueError(
                "NarrativeSourceContinuityConstraint.assertion must be string."
            )
        _require_span(
            self.span,
            "NarrativeSourceContinuityConstraint.span",
        )


@dataclass(frozen=True)
class NarrativeSourceContinuity:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    constraints: tuple[NarrativeSourceContinuityConstraint, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(
            self.keyword_span,
            "NarrativeSourceContinuity.keyword_span",
        )
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceContinuity.name",
        )
        _require_tuple(
            self.constraints,
            NarrativeSourceContinuityConstraint,
            "NarrativeSourceContinuity.constraints",
        )
        _require_span(self.span, "NarrativeSourceContinuity.span")


@dataclass(frozen=True)
class NarrativeSourceStory:
    keyword_span: SourceSpan
    name: NarrativeSourceIdentifier
    characters: tuple[NarrativeSourceCharacter, ...]
    scenes: tuple[NarrativeSourceScene, ...]
    dialogues: tuple[NarrativeSourceDialogue, ...]
    choices: tuple[NarrativeSourceChoice, ...]
    perspectives: tuple[NarrativeSourcePerspective, ...]
    timelines: tuple[NarrativeSourceTimeline, ...]
    states: tuple[NarrativeSourceState, ...]
    continuities: tuple[NarrativeSourceContinuity, ...]
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_span(self.keyword_span, "NarrativeSourceStory.keyword_span")
        _require_exact_record(
            self.name,
            NarrativeSourceIdentifier,
            "NarrativeSourceStory.name",
        )
        for field_name, values, expected_type in (
            ("characters", self.characters, NarrativeSourceCharacter),
            ("scenes", self.scenes, NarrativeSourceScene),
            ("dialogues", self.dialogues, NarrativeSourceDialogue),
            ("choices", self.choices, NarrativeSourceChoice),
            ("perspectives", self.perspectives, NarrativeSourcePerspective),
            ("timelines", self.timelines, NarrativeSourceTimeline),
            ("states", self.states, NarrativeSourceState),
            ("continuities", self.continuities, NarrativeSourceContinuity),
        ):
            _require_tuple(
                values,
                expected_type,
                f"NarrativeSourceStory.{field_name}",
            )
        _require_span(self.span, "NarrativeSourceStory.span")


@dataclass(frozen=True)
class NarrativeSourceDocument:
    story: NarrativeSourceStory
    span: SourceSpan

    def __post_init__(self) -> None:
        _require_exact_record(
            self.story,
            NarrativeSourceStory,
            "NarrativeSourceDocument.story",
        )
        _require_span(self.span, "NarrativeSourceDocument.span")
