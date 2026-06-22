"""ApexForge workflow execution layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

from workflow.context import WorkflowContext
from workflow.rules import GOVERNANCE_RULES


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    runner: Callable


@dataclass(frozen=True)
class WorkflowResult:
    name: str
    context: WorkflowContext
    results: Tuple[tuple[str, object], ...]

    @property
    def ok(self) -> bool:
        return all(result.ok for _, result in self.results)


class WorkflowEngine:
    def execute(
        self,
        name: str,
        steps: Tuple[WorkflowStep, ...],
    ) -> WorkflowResult:
        context = WorkflowContext()
        results = []

        for step in steps:
            rule = GOVERNANCE_RULES.get(step.name)

            if rule and not rule.is_satisfied(context):
                missing = [
                    key
                    for key in rule.requires
                    if key not in context.states
                ]

                raise RuntimeError(
                    f"Workflow rule failed for {step.name}. Missing: {missing}"
                )

            result = step.runner()
            context.absorb_result(result)
            results.append((step.name, result))

        return WorkflowResult(
            name=name,
            context=context,
            results=tuple(results),
        )