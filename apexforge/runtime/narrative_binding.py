"""Narrative condition/consequence binding contracts and deterministic binder.

P11.6C converts descriptive P11.5 choice-path condition/consequence text into
explicit narrative-specific executable representations. It does not evaluate
conditions, apply consequences, transition scenes, emit trace events, or
produce runtime diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from language.narrative_model import (
    NarrativeChoice,
    NarrativeChoicePath,
    NarrativeIdentity,
    NarrativeStory,
)

__all__ = (
    "NarrativeBindingError",
    "NarrativeConditionBinding",
    "NarrativeConsequenceBinding",
    "NarrativeExecutableBindingSet",
    "NarrativeExecutableChoicePath",
    "NarrativeFactAssignment",
    "NarrativeFactPredicate",
    "bind_narrative_story",
)

_PREDICATE_OPERATORS = frozenset(("equals", "not_equals"))


def _require_trimmed_string(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be an exact str.")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty trimmed string.")
    return value


def _require_identity(
    value: object,
    field_name: str,
    expected_kind: Optional[str] = None,
) -> NarrativeIdentity:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    if expected_kind is not None and value.kind != expected_kind:
        raise ValueError(
            f"{field_name} must have narrative identity kind "
            f"{expected_kind!r}; received {value.kind!r}."
        )
    return value


@dataclass(frozen=True)
class NarrativeFactPredicate:
    """Explicit condition representation over one current narrative fact slot."""

    subject: NarrativeIdentity
    name: str
    operator: Literal["equals", "not_equals"]
    value: str

    def __post_init__(self) -> None:
        _require_identity(self.subject, "NarrativeFactPredicate.subject")
        _require_trimmed_string(self.name, "NarrativeFactPredicate.name")
        if type(self.operator) is not str:
            raise TypeError("NarrativeFactPredicate.operator must be an exact str.")
        if self.operator not in _PREDICATE_OPERATORS:
            raise ValueError(
                "NarrativeFactPredicate.operator must be 'equals' or 'not_equals'."
            )
        _require_trimmed_string(self.value, "NarrativeFactPredicate.value")


@dataclass(frozen=True)
class NarrativeFactAssignment:
    """Explicit consequence representation that sets one narrative fact slot."""

    subject: NarrativeIdentity
    name: str
    value: str

    def __post_init__(self) -> None:
        _require_identity(self.subject, "NarrativeFactAssignment.subject")
        _require_trimmed_string(self.name, "NarrativeFactAssignment.name")
        _require_trimmed_string(self.value, "NarrativeFactAssignment.value")


@dataclass(frozen=True)
class NarrativeConditionBinding:
    """Exact descriptive condition text bound to one explicit predicate."""

    source_text: str
    predicate: NarrativeFactPredicate

    def __post_init__(self) -> None:
        _require_trimmed_string(self.source_text, "NarrativeConditionBinding.source_text")
        if type(self.predicate) is not NarrativeFactPredicate:
            raise TypeError(
                "NarrativeConditionBinding.predicate must be an exact "
                "NarrativeFactPredicate."
            )


@dataclass(frozen=True)
class NarrativeConsequenceBinding:
    """Exact descriptive consequence text bound to ordered fact assignments."""

    source_text: str
    assignments: tuple[NarrativeFactAssignment, ...]

    def __post_init__(self) -> None:
        _require_trimmed_string(self.source_text, "NarrativeConsequenceBinding.source_text")
        if type(self.assignments) is not tuple:
            raise TypeError(
                "NarrativeConsequenceBinding.assignments must be an exact tuple."
            )
        if not self.assignments:
            raise ValueError(
                "NarrativeConsequenceBinding.assignments must not be empty."
            )
        seen_slots = set()
        for assignment in self.assignments:
            if type(assignment) is not NarrativeFactAssignment:
                raise TypeError(
                    "NarrativeConsequenceBinding.assignments must contain exact "
                    "NarrativeFactAssignment objects."
                )
            slot = (assignment.subject.kind, assignment.subject.path, assignment.name)
            if slot in seen_slots:
                raise ValueError(
                    "NarrativeConsequenceBinding contains duplicate assignment slots."
                )
            seen_slots.add(slot)


@dataclass(frozen=True)
class NarrativeExecutableChoicePath:
    """One choice path after descriptive text crossed the binding boundary."""

    choice: NarrativeIdentity
    source_scene: NarrativeIdentity
    path_index: int
    path_label: str
    destination: NarrativeIdentity
    source_condition: Optional[str]
    condition: Optional[NarrativeFactPredicate]
    source_consequence: Optional[str]
    assignments: tuple[NarrativeFactAssignment, ...]

    def __post_init__(self) -> None:
        _require_identity(self.choice, "NarrativeExecutableChoicePath.choice", "choice")
        _require_identity(
            self.source_scene,
            "NarrativeExecutableChoicePath.source_scene",
            "scene",
        )
        if type(self.path_index) is not int:
            raise TypeError(
                "NarrativeExecutableChoicePath.path_index must be an exact int."
            )
        if self.path_index < 0:
            raise ValueError(
                "NarrativeExecutableChoicePath.path_index must be non-negative."
            )
        _require_trimmed_string(
            self.path_label,
            "NarrativeExecutableChoicePath.path_label",
        )
        _require_identity(
            self.destination,
            "NarrativeExecutableChoicePath.destination",
            "scene",
        )

        if self.source_condition is None:
            if self.condition is not None:
                raise ValueError(
                    "NarrativeExecutableChoicePath.condition must be None when "
                    "source_condition is None."
                )
        else:
            _require_trimmed_string(
                self.source_condition,
                "NarrativeExecutableChoicePath.source_condition",
            )
            if type(self.condition) is not NarrativeFactPredicate:
                raise TypeError(
                    "NarrativeExecutableChoicePath.condition must be an exact "
                    "NarrativeFactPredicate when source_condition is present."
                )

        if type(self.assignments) is not tuple:
            raise TypeError(
                "NarrativeExecutableChoicePath.assignments must be an exact tuple."
            )
        for assignment in self.assignments:
            if type(assignment) is not NarrativeFactAssignment:
                raise TypeError(
                    "NarrativeExecutableChoicePath.assignments must contain exact "
                    "NarrativeFactAssignment objects."
                )

        if self.source_consequence is None:
            if self.assignments:
                raise ValueError(
                    "NarrativeExecutableChoicePath.assignments must be empty when "
                    "source_consequence is None."
                )
        else:
            _require_trimmed_string(
                self.source_consequence,
                "NarrativeExecutableChoicePath.source_consequence",
            )
            if not self.assignments:
                raise ValueError(
                    "NarrativeExecutableChoicePath.assignments must not be empty "
                    "when source_consequence is present."
                )

    @property
    def is_ungated(self) -> bool:
        return self.source_condition is None

    @property
    def has_consequence(self) -> bool:
        return self.source_consequence is not None


@dataclass(frozen=True)
class NarrativeExecutableBindingSet:
    """Deterministic executable bindings for every choice path in one story."""

    story: NarrativeIdentity
    paths: tuple[NarrativeExecutableChoicePath, ...]

    def __post_init__(self) -> None:
        _require_identity(self.story, "NarrativeExecutableBindingSet.story", "story")
        if type(self.paths) is not tuple:
            raise TypeError(
                "NarrativeExecutableBindingSet.paths must be an exact tuple."
            )
        for path in self.paths:
            if type(path) is not NarrativeExecutableChoicePath:
                raise TypeError(
                    "NarrativeExecutableBindingSet.paths must contain exact "
                    "NarrativeExecutableChoicePath objects."
                )


class NarrativeBindingError(ValueError):
    """Raised when descriptive execution text has no explicit binding."""

    def __init__(
        self,
        *,
        binding_kind: Literal["condition", "consequence"],
        source_text: str,
        choice: NarrativeIdentity,
        path_index: int,
    ) -> None:
        if binding_kind not in ("condition", "consequence"):
            raise ValueError(
                "NarrativeBindingError.binding_kind must be condition or consequence."
            )
        _require_trimmed_string(source_text, "NarrativeBindingError.source_text")
        _require_identity(choice, "NarrativeBindingError.choice", "choice")
        if type(path_index) is not int:
            raise TypeError("NarrativeBindingError.path_index must be an exact int.")
        if path_index < 0:
            raise ValueError("NarrativeBindingError.path_index must be non-negative.")

        self.binding_kind = binding_kind
        self.source_text = source_text
        self.choice = choice
        self.path_index = path_index
        super().__init__(
            f"unbound narrative {binding_kind} text {source_text!r} at "
            f"{choice.kind}:{'/'.join(choice.path)} path[{path_index}]"
        )


def _condition_registry(
    bindings: tuple[NarrativeConditionBinding, ...],
) -> dict[str, NarrativeFactPredicate]:
    if type(bindings) is not tuple:
        raise TypeError("condition_bindings must be an exact tuple.")
    registry: dict[str, NarrativeFactPredicate] = {}
    for binding in bindings:
        if type(binding) is not NarrativeConditionBinding:
            raise TypeError(
                "condition_bindings must contain exact NarrativeConditionBinding objects."
            )
        if binding.source_text in registry:
            raise ValueError(
                f"duplicate narrative condition binding: {binding.source_text!r}"
            )
        registry[binding.source_text] = binding.predicate
    return registry


def _consequence_registry(
    bindings: tuple[NarrativeConsequenceBinding, ...],
) -> dict[str, tuple[NarrativeFactAssignment, ...]]:
    if type(bindings) is not tuple:
        raise TypeError("consequence_bindings must be an exact tuple.")
    registry: dict[str, tuple[NarrativeFactAssignment, ...]] = {}
    for binding in bindings:
        if type(binding) is not NarrativeConsequenceBinding:
            raise TypeError(
                "consequence_bindings must contain exact NarrativeConsequenceBinding objects."
            )
        if binding.source_text in registry:
            raise ValueError(
                f"duplicate narrative consequence binding: {binding.source_text!r}"
            )
        registry[binding.source_text] = binding.assignments
    return registry


def _bind_choice_path(
    choice: NarrativeChoice,
    path: NarrativeChoicePath,
    path_index: int,
    condition_registry: dict[str, NarrativeFactPredicate],
    consequence_registry: dict[str, tuple[NarrativeFactAssignment, ...]],
) -> NarrativeExecutableChoicePath:
    source_condition = path.condition
    if source_condition is None:
        condition = None
    else:
        try:
            condition = condition_registry[source_condition]
        except KeyError:
            raise NarrativeBindingError(
                binding_kind="condition",
                source_text=source_condition,
                choice=choice.identity,
                path_index=path_index,
            ) from None

    source_consequence = path.consequence
    if source_consequence is None:
        assignments: tuple[NarrativeFactAssignment, ...] = ()
    else:
        try:
            assignments = consequence_registry[source_consequence]
        except KeyError:
            raise NarrativeBindingError(
                binding_kind="consequence",
                source_text=source_consequence,
                choice=choice.identity,
                path_index=path_index,
            ) from None

    return NarrativeExecutableChoicePath(
        choice=choice.identity,
        source_scene=choice.scene,
        path_index=path_index,
        path_label=path.label,
        destination=path.destination,
        source_condition=source_condition,
        condition=condition,
        source_consequence=source_consequence,
        assignments=assignments,
    )


def bind_narrative_story(
    story: NarrativeStory,
    *,
    condition_bindings: tuple[NarrativeConditionBinding, ...] = (),
    consequence_bindings: tuple[NarrativeConsequenceBinding, ...] = (),
) -> NarrativeExecutableBindingSet:
    """Bind descriptive path execution strings by exact text without executing."""

    if type(story) is not NarrativeStory:
        raise TypeError("story must be an exact NarrativeStory.")

    condition_registry = _condition_registry(condition_bindings)
    consequence_registry = _consequence_registry(consequence_bindings)

    paths = []
    for choice in story.choices:
        for path_index, path in enumerate(choice.paths):
            paths.append(
                _bind_choice_path(
                    choice,
                    path,
                    path_index,
                    condition_registry,
                    consequence_registry,
                )
            )

    return NarrativeExecutableBindingSet(
        story=story.identity,
        paths=tuple(paths),
    )
