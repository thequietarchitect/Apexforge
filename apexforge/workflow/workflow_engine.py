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
        *,
        authority_registry,
        principal_registry,
        principal_name: str,
        max_depth: int = 10,
    ) -> WorkflowExecutionResult:
        results = []
        directive_engine = DirectiveExecutionEngine()

        for invocation in workflow.invocations:
            directive_result = directive_engine.execute(
                registry=registry,
                authority_registry=authority_registry,
                principal_registry=principal_registry,
                principal_name=principal_name,
                root=invocation.target.lower(),
                max_depth=max_depth,
            )

            results.extend(directive_result.results)

        return WorkflowExecutionResult(
            name=workflow.name,
            results=tuple(results),
        )
