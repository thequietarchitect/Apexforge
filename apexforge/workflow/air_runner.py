"""Run AIR programs loaded from AirRegistry."""

from __future__ import annotations

from authority.engine import AuthorityEngine
from authority.model import AuthorityGrant
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from air.verify import AIRVerifier


def build_default_context(program):
    capabilities = tuple(
        check.capability
        for check in program.authority_checks
    )

    grants = (
        AuthorityGrant(
            name=program.principals[0].id,
            capabilities=capabilities,
        ),
    )

    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(grants),
    )


def collect_invocations(program) -> tuple[str, ...]:
    targets = []

    for decision in program.causal_decisions:
        for path in decision.paths:
            for invocation in path.invocations:
                targets.append(invocation.target)

    return tuple(targets)


def run_air_program(program):
    verified = AIRVerifier().verify(program).require_verified()
    context = build_default_context(program)
    return RuntimeEngine().execute(verified, context)


def run_air_from_registry(registry, name: str):
    program = registry.resolve(name)
    return run_air_program(program)


def run_air_with_invocation_report(program):
    result = run_air_program(program)
    invocations = collect_invocations(program)

    return result, invocations