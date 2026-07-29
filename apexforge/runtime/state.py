"""Canonical runtime state snapshots and deltas.

This module owns runtime state. AIR declarations and event records remain in
``air.model``; host effect descriptions remain in ``effects.model``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from air.expressions import AIRIntegerLiteral
from air.model import EventRecord, StateAssignment
from effects.model import EffectIntent


def _require_int(
    value: Any,
    *,
    owner: str,
) -> int:
    """Require a real integer rather than ``bool`` or an AIR expression."""

    if type(value) is not int:
        raise TypeError(
            f"{owner} must be an int; "
            f"received {type(value).__name__}."
        )

    return value


def _program_initial_int(
    state: Any,
) -> int:
    """Convert one verified state initializer into a runtime integer.

    AFP-P1 programs may contain primitive integers. AFP-P2 compilation wraps
    integer source literals in ``AIRIntegerLiteral``. More general initializer
    expressions are intentionally rejected here until initialization-order
    semantics are defined.
    """

    initial = getattr(
        state,
        "initial",
        None,
    )

    if type(initial) is int:
        return initial

    if isinstance(
        initial,
        AIRIntegerLiteral,
    ):
        return _require_int(
            initial.value,
            owner=(
                f"state '{getattr(state, 'id', '<unknown>')}' "
                "integer initializer"
            ),
        )

    raise TypeError(
        f"state '{getattr(state, 'id', '<unknown>')}' initializer "
        "must be an integer or AIRIntegerLiteral before runtime "
        f"snapshot creation; received {type(initial).__name__}."
    )


@dataclass(frozen=True, order=True)
class StateCell:
    """One immutable runtime state value."""

    key: str
    value: int

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

        _require_int(
            self.value,
            owner=f"state cell '{self.key}'",
        )


@dataclass(frozen=True)
class StateSnapshot:
    """An immutable, deterministic set of runtime state cells."""

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
        values: Mapping[str, int],
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
                    value=_program_initial_int(
                        state
                    ),
                )
                for state in program.states
            )
        )

    def get_int(
        self,
        key: str,
        default: int = 0,
    ) -> int:
        """Read either a canonical ``state:name`` ID or its plain alias."""

        _require_int(
            default,
            owner="StateSnapshot.get_int default",
        )

        candidates = [key]

        if key.startswith(
            "state:"
        ):
            plain_key = key[
                len("state:"):
            ]

            if plain_key:
                candidates.append(
                    plain_key
                )
        else:
            candidates.append(
                f"state:{key}"
            )

        for candidate in candidates:
            for cell in self.cells:
                if cell.key == candidate:
                    return cell.value

        return default

    def apply(
        self,
        delta: "StateDelta",
    ) -> "StateSnapshot":
        """Return a new snapshot with the delta's assignments applied."""

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

        for assignment in delta.assignments:
            value = _require_int(
                assignment.value,
                owner=(
                    f"assignment to state "
                    f"'{assignment.state}'"
                ),
            )

            previous = values.get(
                assignment.state,
                0,
            )

            if assignment.operation == "set_int":
                values[
                    assignment.state
                ] = value
                continue

            if assignment.operation == "add_int":
                values[
                    assignment.state
                ] = previous + value
                continue

            raise ValueError(
                "unsupported state operation: "
                f"{assignment.operation}"
            )

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