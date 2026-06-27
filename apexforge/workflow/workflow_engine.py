"""Workflow execution engine for ApexForge workflow AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from language.parser import WorkflowNode
from workflow.directive_engine import DirectiveExecutionEngine


@dataclass(frozen=True)
class WorkflowExecutionResult:
    name: str
    results: Tuple[tuple[str, object], ...]

    @property
    def ok(self) -> bool:
        return all(result.ok for _, result in self.results)


class WorkflowExecutionEngine:
    def execute(
        self,
        registry,
        workflow: WorkflowNode,
    ) -> WorkflowExecutionResult:
        results = []
        directive_engine = DirectiveExecutionEngine()

        for invocation in workflow.invocations:
            directive_result = directive_engine.execute(
                registry,
                invocation.target.lower(),
            )

            results.extend(directive_result.results)

        return WorkflowExecutionResult(
            name=workflow.name,
            results=tuple(results),
        )