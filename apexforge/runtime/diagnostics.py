"""Runtime diagnostics and execution trace objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

from air.model import Fact


@dataclass(frozen=True, order=True)
class Diagnostic:
    severity: Literal["error", "warning", "info"]
    code: str
    message: str
    node_id: str = ""

    @property
    def is_error(self) -> bool:
        return self.severity == "error"


def append_diagnostic(
    diagnostics: list[Diagnostic],
    severity: Literal["error", "warning", "info"],
    code: str,
    message: str,
    node_id: str = "",
) -> None:
    diagnostics.append(Diagnostic(severity, code, message, node_id))


@dataclass(frozen=True, order=True)
class TraceStep:
    kind: str
    message: str
    facts: Tuple[Fact, ...] = ()


@dataclass(frozen=True)
class Trace:
    steps: Tuple[TraceStep, ...] = ()

    def render(self) -> str:
        lines = []
        for step in self.steps:
            facts = ", ".join(f"{fact.key}={fact.value!r}" for fact in step.facts)
            suffix = f" [{facts}]" if facts else ""
            lines.append(f"{step.kind}: {step.message}{suffix}")
        return "\n".join(lines)
