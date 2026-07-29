"""Runtime state snapshots and deltas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from air.model import EventRecord, StateAssignment


@dataclass(frozen=True, order=True)
class StateCell:
    key: str
    value: int


@dataclass(frozen=True)
class StateSnapshot:
    cells: Tuple[StateCell, ...] = ()

    @classmethod
    def from_mapping(
        cls,
        values: dict[str, int],
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

    def get_int(
        self,
        key: str,
        default: int = 0,
    ) -> int:
        ...

    @classmethod
    def from_program_initials(cls, program) -> "StateSnapshot":
        return cls(tuple(StateCell(state.id, state.initial) for state in program.states))

    def get_int(self, key: str, default: int = 0) -> int:
        for cell in self.cells:
            if cell.key == key:
                return cell.value
        return default

    def apply(self, delta: "StateDelta") -> "StateSnapshot":
        values = {cell.key: cell.value for cell in self.cells}

        for assignment in delta.assignments:
            previous = values.get(assignment.state, 0)

            if assignment.operation == "set_int":
                values[assignment.state] = assignment.value
            elif assignment.operation == "add_int":
                values[assignment.state] = previous + assignment.value
            else:
                raise ValueError(f"unsupported state operation: {assignment.operation}")

        return StateSnapshot(tuple(StateCell(key, value) for key, value in sorted(values.items())))


@dataclass(frozen=True)
class StateDelta:
    assignments: Tuple[StateAssignment, ...] = ()
    events: Tuple[EventRecord, ...] = ()
    effects: tuple = ()

    @property
    def is_empty(self) -> bool:
        return not self.assignments and not self.events and not self.effects