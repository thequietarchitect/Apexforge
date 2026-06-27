"""Recursive directive execution engine for ApexForge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from workflow.air_runner import run_air_from_registry
from authority.validator import validate_requirements, AuthorizationError, validate_authorities

@dataclass(frozen=True)
class DirectiveExecutionResult:
    root: str
    results: Tuple[tuple[str, object], ...]

    @property
    def ok(self) -> bool:
        return all(result.ok for _, result in self.results)

class TestDirectiveRegistry:
    def __init__(self):
        self._programs = {}

    def register(self, name, program):
        self._programs[name.lower()] = program

    def resolve(self, name):
        return self._programs[name.lower()]


class DirectiveExecutionEngine:
    def execute(
        self,
        registry,
        authority_registry,
        root: str,
        max_depth: int = 10,
    ) -> DirectiveExecutionResult:
        results = []
        visited = set()

        def run(name: str, depth: int) -> None:
            if depth > max_depth:
                raise RuntimeError(
                    f"Maximum invocation depth exceeded at {name}"
                )

            if name in visited:
                raise RuntimeError(
                    f"Recursive invocation cycle detected at {name}"
                )

            visited.add(name)

            result = run_air_from_registry(registry, name)
            results.append((name, result))

            program = registry.resolve(name)
            validate_authorities(
                program,
                authority_registry,
            )
            validate_requirements(
                program,
                authority_registry,
            )

            for decision in program.causal_decisions:
                for path in decision.paths:
                    for invocation in path.invocations:
                        target = invocation.target.lower()
                        run(target, depth + 1)

            visited.remove(name)

        run(root, 0)

        return DirectiveExecutionResult(
            root=root,
            results=tuple(results),
        )