"""AIR workflow runner for ApexForge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from workflow.air_registry import AirRegistry
from workflow.air_runner import run_air_from_registry
from workflow.context import WorkflowContext


@dataclass(frozen=True)
class AirWorkflowResult:
    name: str
    context: WorkflowContext
    results: Tuple[tuple[str, object], ...]

    @property
    def ok(self) -> bool:
        return all(result.ok for _, result in self.results)


class AirWorkflowRunner:
    def run(
        self,
        name: str,
        registry: AirRegistry,
        steps: Tuple[str, ...],
    ) -> AirWorkflowResult:
        context = WorkflowContext()
        results = []

        for step_name in steps:
            result = run_air_from_registry(registry, step_name)
            context.absorb_result(result)
            results.append((step_name, result))

        return AirWorkflowResult(
            name=name,
            context=context,
            results=tuple(results),
        )