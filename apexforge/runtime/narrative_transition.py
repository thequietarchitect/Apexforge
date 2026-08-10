"""Deterministic immutable narrative scene/choice transitions.

P11.6D consumes the immutable P11.6B execution state and the immutable P11.6C
executable bindings.  It requires an explicit choice identity and path index;
it does not select choices, resolve an initial scene, emit diagnostics or
trace, or apply termination policy.
"""

from __future__ import annotations

from typing import Literal, Optional

from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from runtime.narrative_binding import (
    NarrativeExecutableBindingSet,
    NarrativeExecutableChoicePath,
)
from runtime.narrative_execution import (
    NarrativeChoiceEvidence,
    NarrativeExecutionState,
)

__all__ = (
    "NarrativeTransitionError",
    "transition_narrative_choice",
)


_FAILURE_KINDS = frozenset(
    (
        "story_mismatch",
        "choice_not_found",
        "choice_not_current_scene",
        "path_not_found",
        "ambiguous_path",
        "condition_unsatisfied",
    )
)


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


class NarrativeTransitionError(ValueError):
    """Raised for one deterministic structural transition failure."""

    def __init__(
        self,
        *,
        failure_kind: Literal[
            "story_mismatch",
            "choice_not_found",
            "choice_not_current_scene",
            "path_not_found",
            "ambiguous_path",
            "condition_unsatisfied",
        ],
        choice: NarrativeIdentity,
        path_index: int,
        current_scene: NarrativeIdentity,
    ) -> None:
        if failure_kind not in _FAILURE_KINDS:
            raise ValueError(
                "NarrativeTransitionError.failure_kind is unsupported."
            )
        _require_identity(
            choice,
            "NarrativeTransitionError.choice",
            "choice",
        )
        if type(path_index) is not int:
            raise TypeError(
                "NarrativeTransitionError.path_index must be an exact int."
            )
        if path_index < 0:
            raise ValueError(
                "NarrativeTransitionError.path_index must be non-negative."
            )
        _require_identity(
            current_scene,
            "NarrativeTransitionError.current_scene",
            "scene",
        )

        self.failure_kind = failure_kind
        self.choice = choice
        self.path_index = path_index
        self.current_scene = current_scene
        super().__init__(
            f"narrative transition {failure_kind}: "
            f"{choice.kind}:{'/'.join(choice.path)} path[{path_index}] "
            f"from {current_scene.kind}:{'/'.join(current_scene.path)}"
        )


def _path_matches(
    paths: tuple[NarrativeExecutableChoicePath, ...],
    choice: NarrativeIdentity,
    path_index: int,
    current_scene: NarrativeIdentity,
) -> NarrativeExecutableChoicePath:
    choice_paths = tuple(path for path in paths if path.choice == choice)
    if not choice_paths:
        raise NarrativeTransitionError(
            failure_kind="choice_not_found",
            choice=choice,
            path_index=path_index,
            current_scene=current_scene,
        )

    current_scene_paths = tuple(
        path for path in choice_paths if path.source_scene == current_scene
    )
    if not current_scene_paths:
        raise NarrativeTransitionError(
            failure_kind="choice_not_current_scene",
            choice=choice,
            path_index=path_index,
            current_scene=current_scene,
        )

    requested_paths = tuple(
        path for path in current_scene_paths if path.path_index == path_index
    )
    if not requested_paths:
        raise NarrativeTransitionError(
            failure_kind="path_not_found",
            choice=choice,
            path_index=path_index,
            current_scene=current_scene,
        )
    if len(requested_paths) != 1:
        raise NarrativeTransitionError(
            failure_kind="ambiguous_path",
            choice=choice,
            path_index=path_index,
            current_scene=current_scene,
        )
    return requested_paths[0]


def _predicate_satisfied(
    path: NarrativeExecutableChoicePath,
    state: NarrativeExecutionState,
) -> bool:
    predicate = path.condition
    if predicate is None:
        return True

    for fact in state.facts:
        if fact.subject == predicate.subject and fact.name == predicate.name:
            if predicate.operator == "equals":
                return fact.value == predicate.value
            return fact.value != predicate.value
    return False


def _apply_assignments(
    path: NarrativeExecutableChoicePath,
    state: NarrativeExecutionState,
) -> tuple[NarrativeStateFact, ...]:
    facts = {(fact.subject, fact.name): fact for fact in state.facts}
    for assignment in path.assignments:
        facts[(assignment.subject, assignment.name)] = NarrativeStateFact(
            assignment.subject,
            assignment.name,
            assignment.value,
        )
    return tuple(facts.values())


def transition_narrative_choice(
    state: NarrativeExecutionState,
    bindings: NarrativeExecutableBindingSet,
    choice: NarrativeIdentity,
    path_index: int,
) -> NarrativeExecutionState:
    """Apply one explicitly selected executable choice path immutably."""

    if type(state) is not NarrativeExecutionState:
        raise TypeError("state must be an exact NarrativeExecutionState.")
    if type(bindings) is not NarrativeExecutableBindingSet:
        raise TypeError(
            "bindings must be an exact NarrativeExecutableBindingSet."
        )
    _require_identity(choice, "choice", "choice")
    if type(path_index) is not int:
        raise TypeError("path_index must be an exact int.")
    if path_index < 0:
        raise ValueError("path_index must be non-negative.")

    if bindings.story != state.story:
        raise NarrativeTransitionError(
            failure_kind="story_mismatch",
            choice=choice,
            path_index=path_index,
            current_scene=state.current_scene,
        )

    path = _path_matches(
        bindings.paths,
        choice,
        path_index,
        state.current_scene,
    )
    if not _predicate_satisfied(path, state):
        raise NarrativeTransitionError(
            failure_kind="condition_unsatisfied",
            choice=choice,
            path_index=path_index,
            current_scene=state.current_scene,
        )

    evidence = NarrativeChoiceEvidence(
        choice=path.choice,
        source_scene=path.source_scene,
        path_index=path.path_index,
        path_label=path.path_label,
        destination=path.destination,
    )
    return NarrativeExecutionState(
        story=state.story,
        current_scene=path.destination,
        facts=_apply_assignments(path, state),
        progression=state.progression + (path.destination,),
        choice_history=state.choice_history + (evidence,),
        termination=state.termination,
    )
