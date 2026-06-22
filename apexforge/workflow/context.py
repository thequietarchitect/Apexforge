"""Shared workflow context for ApexForge directive chaining."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class WorkflowContext:
    states: Dict[str, int] = field(default_factory=dict)
    events: List[str] = field(default_factory=list)

    def set_state(self, key: str, value: int) -> None:
        self.states[key] = value

    def get_state(self, key: str, default: int = 0) -> int:
        return self.states.get(key, default)

    def record_event(self, event: str) -> None:
        self.events.append(event)

    def absorb_result(self, result) -> None:
        for cell in result.final_state.cells:
            self.set_state(cell.key, cell.value)

        for event in result.delta.events:
            self.record_event(event.event)

    def summary(self) -> str:
        lines = ["Workflow Context"]

        lines.append("States:")
        for key, value in sorted(self.states.items()):
            lines.append(f"  {key}: {value}")

        lines.append("Events:")
        for event in self.events:
            lines.append(f"  {event}")

        return "\n".join(lines)