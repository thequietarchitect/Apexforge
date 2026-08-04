"""Synchronous linked directive execution engine for ApexForge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from air.model import PrincipalAuthority
from air.verify import AIRVerifier
from authority.validator import (
    authorize_principal,
    authorize_principal_capabilities,
    validate_authorities,
    validate_principal_authorities,
)
from role.registry import RoleRegistry
from workflow.air_runner import (
    build_registry_execution_plan,
    run_air_program,
)


@dataclass(frozen=True)
class DirectiveExecutionResult:
    root: str
    results: Tuple[tuple[str, object], ...]

    @property
    def ok(self) -> bool:
        return all(result.ok for _, result in self.results)


class DirectiveRequirementOwnershipError(RuntimeError):
    """Raised when program-level requirements have ambiguous ownership."""


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
        principal_registry,
        principal_name: str,
        root: str,
        max_depth: int = 10,
    ) -> DirectiveExecutionResult:
        if (
            isinstance(max_depth, bool)
            or not isinstance(max_depth, int)
            or max_depth < 0
        ):
            raise ValueError(
                "max_depth must be a non-negative integer."
            )

        executing_principal = principal_registry.get(
            principal_name
        )
        plan = build_registry_execution_plan(
            registry,
            root,
        )
        ownership_result = AIRVerifier().verify(
            plan.program,
            allow_unresolved_directive_invocations=True,
            directive_requirement_owners=plan.directive_owners,
        )
        ownership_diagnostics = tuple(
            diagnostic
            for diagnostic in ownership_result.diagnostics
            if diagnostic.code == "AIR065"
        )

        if ownership_diagnostics:
            raise DirectiveRequirementOwnershipError(
                "cannot determine capability requirement ownership "
                "for selected directive "
                f"{ownership_diagnostics[0].node_id!r}"
            )

        def authorize_directive_entry(directive) -> None:
            owner = plan.owner_of(directive.id)

            if owner.requirements and len(owner.directives) != 1:
                raise DirectiveRequirementOwnershipError(
                    "cannot determine capability requirement ownership "
                    f"for selected directive {directive.id!r}"
                )

            validate_authorities(
                owner,
                authority_registry,
            )
            validate_principal_authorities(
                owner,
                authority_registry,
            )

            role_registry = RoleRegistry()
            role_registry.register_all(owner.roles)

            for authority in directive.authorities:
                authorize_principal(
                    principal=executing_principal,
                    authority=PrincipalAuthority(
                        name=authority.name,
                    ),
                    role_registry=role_registry,
                    authority_registry=authority_registry,
                    program=owner,
                )

            required_capabilities = {
                requirement.capability
                for requirement in owner.requirements
            }

            if required_capabilities:
                authorize_principal_capabilities(
                    principal=executing_principal,
                    required_capabilities=required_capabilities,
                    role_registry=role_registry,
                    authority_registry=authority_registry,
                    program=owner,
                )

        result = run_air_program(
            plan.program,
            entry_directives=(plan.entry_directive,),
            directive_entry_guard=authorize_directive_entry,
            max_invocation_depth=max_depth + 1,
            allow_unresolved_directive_invocations=True,
            directive_requirement_owners=plan.directive_owners,
        )

        return DirectiveExecutionResult(
            root=root,
            results=((root, result),),
        )
