"""Run AIR programs loaded from AirRegistry."""

from __future__ import annotations

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from air.verify import AIRVerifier


def build_default_context(program):
    grants = []

    for check in program.authority_checks:
        grants.append(
            AuthorityGrant(
                principal=check.principal,
                capability=check.capability,
                resource=check.resource,
            )
        )

    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(tuple(grants)),
    )


def run_air_program(program):
    verified = AIRVerifier().verify(program).require_verified()
    context = build_default_context(program)
    return RuntimeEngine().execute(verified, context)


def run_air_from_registry(registry, name: str):
    program = registry.resolve(name)
    return run_air_program(program)