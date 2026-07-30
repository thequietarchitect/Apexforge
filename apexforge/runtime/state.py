"""Canonical runtime state snapshots and deltas.

This module owns runtime state. AIR declarations and event records remain in
``air.model``; host effect descriptions remain in ``effects.model``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple, Union

from air.expressions import (
    AIRBooleanLiteral,
    AIRFloatLiteral,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.model import EventRecord, StateAssignment
from effects.model import EffectIntent
from type_system.model import (
    ApexType,
    BOOL,
    FLOAT,
    INT,
    STRING,
    VOID,
    resolve_builtin_type,
)


StateValue = Union[int, bool, str, float]
_MISSING = object()


def _value_type(
    value: object,
) -> ApexType:
    if type(value) is int:
        return INT
    if type(value) is bool:
        return BOOL
    if type(value) is str:
        return STRING
    if type(value) is float:
        return FLOAT

    raise TypeError(
        "ApexForge runtime state values must be int, bool, string, or float; "
        f"received {type(value).__name__}."
    )


def _require_value_type(
    value: object,
    *,
    expected: ApexType,
    owner: str,
) -> StateValue:
    actual = _value_type(value)

    if actual is not expected:
        raise TypeError(
            f"{owner} must be {expected}; "
            f"received {actual}."
        )

    return value  # type: ignore[return-value]


def _program_initial_value(
    state: Any,
) -> StateValue:
    """Convert one verified literal state initializer into a runtime value.

    Initialization-order and cross-state expression evaluation remain outside
    this constructor. The compiler and validator guarantee the initializer's
    type before snapshot creation.
    """

    state_id = getattr(
        state,
        "id",
        "<unknown>",
    )
    value_type = resolve_builtin_type(
        getattr(
            state,
            "value_type",
            INT,
        )
    )

    if value_type is VOID:
        raise TypeError(
            f"state {state_id!r} cannot use void."
        )

    initial = getattr(
        state,
        "initial",
        None,
    )

    if type(initial) in {
        int,
        bool,
        str,
        float,
    }:
        return _require_value_type(
            initial,
            expected=value_type,
            owner=f"state {state_id!r} initializer",
        )

    literal_specs = (
        (
            AIRIntegerLiteral,
            INT,
        ),
        (
            AIRBooleanLiteral,
            BOOL,
        ),
        (
            AIRStringLiteral,
            STRING,
        ),
        (
            AIRFloatLiteral,
            FLOAT,
        ),
    )

    for literal_class, literal_type in literal_specs:
        if isinstance(
            initial,
            literal_class,
        ):
            if value_type is not literal_type:
                raise TypeError(
                    f"state {state_id!r} declares {value_type} "
                    f"but contains {literal_type} initializer."
                )

            return _require_value_type(
                initial.value,
                expected=literal_type,
                owner=f"state {state_id!r} initializer",
            )

    raise TypeError(
        f"state {state_id!r} initializer must be a verified literal before "
        "runtime snapshot creation; "
        f"received {type(initial).__name__}."
    )


def _candidate_keys(
    key: str,
) -> tuple[str, ...]:
    if not isinstance(key, str) or not key:
        raise ValueError(
            "State key must be a non-empty string."
        )

    if key.startswith("state:"):
        plain = key[len("state:"):]
        return (
            key,
            plain,
        ) if plain else (key,)

    return (
        key,
        f"state:{key}",
    )


@dataclass(frozen=True, order=True)
class StateCell:
    """One immutable runtime state value."""

    key: str
    value: StateValue

    def __post_init__(
        self,
    ) -> None:
        if not isinstance(
            self.key,
            str,
        ) or not self.key:
            raise ValueError(
                "StateCell key must be a non-empty string."
            )

        _value_type(
            self.value
        )


@dataclass(frozen=True)
class StateSnapshot:
    """An immutable, deterministic set of typed runtime state cells."""

    cells: Tuple[StateCell, ...] = ()

    def __post_init__(
        self,
    ) -> None:
        normalized = tuple(
            sorted(
                tuple(self.cells),
                key=lambda cell: cell.key,
            )
        )
        seen: set[str] = set()

        for cell in normalized:
            if not isinstance(
                cell,
                StateCell,
            ):
                raise TypeError(
                    "StateSnapshot cells must be StateCell objects; "
                    f"received {type(cell).__name__}."
                )

            if cell.key in seen:
                raise ValueError(
                    f"duplicate state cell: {cell.key}"
                )

            seen.add(
                cell.key
            )

        object.__setattr__(
            self,
            "cells",
            normalized,
        )

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, StateValue],
    ) -> "StateSnapshot":
        return cls(
            cells=tuple(
                StateCell(
                    key=key,
                    value=value,
                )
                for key, value in values.items()
            )
        )

    @classmethod
    def from_program_initials(
        cls,
        program: Any,
    ) -> "StateSnapshot":
        return cls(
            cells=tuple(
                StateCell(
                    key=state.id,
                    value=_program_initial_value(
                        state
                    ),
                )
                for state in program.states
            )
        )

    def get_value(
        self,
        key: str,
        default: object = _MISSING,
    ) -> StateValue:
        for candidate in _candidate_keys(key):
            for cell in self.cells:
                if cell.key == candidate:
                    return cell.value

        if default is _MISSING:
            raise KeyError(key)

        _value_type(default)
        return default  # type: ignore[return-value]

    def get_int(
        self,
        key: str,
        default: int = 0,
    ) -> int:
        _require_value_type(
            default,
            expected=INT,
            owner="StateSnapshot.get_int default",
        )
        return _require_value_type(
            self.get_value(key, default),
            expected=INT,
            owner=f"state {key!r}",
        )  # type: ignore[return-value]

    def get_bool(
        self,
        key: str,
        default: bool = False,
    ) -> bool:
        _require_value_type(
            default,
            expected=BOOL,
            owner="StateSnapshot.get_bool default",
        )
        return _require_value_type(
            self.get_value(key, default),
            expected=BOOL,
            owner=f"state {key!r}",
        )  # type: ignore[return-value]

    def get_string(
        self,
        key: str,
        default: str = "",
    ) -> str:
        _require_value_type(
            default,
            expected=STRING,
            owner="StateSnapshot.get_string default",
        )
        return _require_value_type(
            self.get_value(key, default),
            expected=STRING,
            owner=f"state {key!r}",
        )  # type: ignore[return-value]

    def get_float(
        self,
        key: str,
        default: float = 0.0,
    ) -> float:
        _require_value_type(
            default,
            expected=FLOAT,
            owner="StateSnapshot.get_float default",
        )
        return _require_value_type(
            self.get_value(key, default),
            expected=FLOAT,
            owner=f"state {key!r}",
        )  # type: ignore[return-value]

    def apply(
        self,
        delta: "StateDelta",
    ) -> "StateSnapshot":
        """Return a new snapshot with typed assignments applied."""

        if not isinstance(
            delta,
            StateDelta,
        ):
            raise TypeError(
                "StateSnapshot.apply requires StateDelta; "
                f"received {type(delta).__name__}."
            )

        values = {
            cell.key: cell.value
            for cell in self.cells
        }

        operation_types = {
            "set_int": INT,
            "add_int": INT,
            "set_bool": BOOL,
            "set_string": STRING,
            "set_float": FLOAT,
            "add_float": FLOAT,
        }

        for assignment in delta.assignments:
            expected = operation_types.get(
                assignment.operation
            )

            if expected is None:
                raise ValueError(
                    "unsupported state operation: "
                    f"{assignment.operation}"
                )

            value = _require_value_type(
                assignment.value,
                expected=expected,
                owner=(
                    f"assignment to state "
                    f"{assignment.state!r}"
                ),
            )

            if assignment.operation.startswith("set_"):
                values[
                    assignment.state
                ] = value
                continue

            previous_default: StateValue = (
                0
                if expected is INT
                else 0.0
            )
            previous = _require_value_type(
                values.get(
                    assignment.state,
                    previous_default,
                ),
                expected=expected,
                owner=(
                    f"existing state "
                    f"{assignment.state!r}"
                ),
            )
            values[
                assignment.state
            ] = previous + value  # type: ignore[operator]

        return type(self).from_mapping(
            values
        )


@dataclass(frozen=True)
class StateDelta:
    """The complete immutable result of one runtime execution step."""

    assignments: Tuple[StateAssignment, ...] = ()
    events: Tuple[EventRecord, ...] = ()
    effects: Tuple[EffectIntent, ...] = ()

    def __post_init__(
        self,
    ) -> None:
        object.__setattr__(
            self,
            "assignments",
            tuple(self.assignments),
        )
        object.__setattr__(
            self,
            "events",
            tuple(self.events),
        )
        object.__setattr__(
            self,
            "effects",
            tuple(self.effects),
        )

    @property
    def is_empty(
        self,
    ) -> bool:
        return not (
            self.assignments
            or self.events
            or self.effects
        )


__all__ = (
    "StateCell",
    "StateDelta",
    "StateSnapshot",
    "StateValue",
)