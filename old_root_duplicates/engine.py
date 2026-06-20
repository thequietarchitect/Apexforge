"""Deterministic causal weighted evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from air.model import Fact, facts
from causality.model import CausalDecision, CausalPath
from runtime.diagnostics import TraceStep


@dataclass(frozen=True)
class CausalSelection:
    path: CausalPath
    trace_steps: Tuple[TraceStep, ...]


class CausalEngine:
    def select_path(self, decision: CausalDecision) -> CausalSelection:
        if decision.policy != "max_weight":
            raise ValueError(f"unsupported causal policy: {decision.policy}")
        if not decision.paths:
            raise ValueError(f"causal decision has no paths: {decision.id}")

        ordered_paths = tuple(sorted(decision.paths, key=lambda path: (-path.weight, path.id)))
        selected = ordered_paths[0]
        trace_facts: list[Fact] = [
            Fact("cause", decision.cause),
            Fact("selected", selected.id),
            Fact("weight", selected.weight),
        ]
        for path in sorted(decision.paths, key=lambda item: item.id):
            trace_facts.append(Fact(f"path.{path.id}.weight", path.weight))

        return CausalSelection(
            path=selected,
            trace_steps=(
                TraceStep("causal.evaluate", "evaluated weighted paths", tuple(trace_facts)),
                TraceStep("causal.select", "selected deterministic causal path", facts(path=selected.id, weight=selected.weight)),
            ),
        )
