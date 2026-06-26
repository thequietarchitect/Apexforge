"""Sentinel directive demo."""

from __future__ import annotations

from air.model import (
    AIRDirective,
    AIRProgram,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from authority.engine import AuthorityEngine
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from causality.model import CausalDecision, CausalPath
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from air.verify import AIRVerifier


def build_sentinel_program() -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(
                id="principal:Sentinel",
                display_name="Sentinel",
            ),
        ),
        states=(
            StateDefinition(
                id="state:Awareness",
                initial=0,
            ),
        ),
        events=(
            EventDefinition(
                id="event:SentinelObservation",
                name="SentinelObservation",
            ),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:Sentinel",
                principal="principal:Sentinel",
                capability="directive.invoke:Sentinel",
                resource="directive:Sentinel",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Observation",
                cause="Observation",
                policy="max_weight",
                paths=(
                    CausalPath(
                        id="path:Ignore",
                        weight=20,
                        assignments=(
                            StateAssignment(
                                state="state:Awareness",
                                operation="add_int",
                                value=0,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:SentinelObservation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Sentinel ignores the observation.",
                    ),
                    CausalPath(
                        id="path:Monitor",
                        weight=50,
                        assignments=(
                            StateAssignment(
                                state="state:Awareness",
                                operation="add_int",
                                value=1,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:SentinelObservation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Sentinel monitors the observation.",
                    ),
                    CausalPath(
                        id="path:Investigate",
                        weight=80,
                        assignments=(
                            StateAssignment(
                                state="state:Awareness",
                                operation="add_int",
                                value=3,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:SentinelObservation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Sentinel investigates the observation.",
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:Sentinel",
                name="Sentinel",
                principal="principal:Sentinel",
                authority_checks=("auth:Sentinel",),
                causal_decisions=("cause:Observation",),
                order=0,
            ),
        ),
    )


def run_sentinel_demo():
    program = build_sentinel_program()

    verified = AIRVerifier().verify(program).require_verified()

    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Sentinel",
                    capability="directive.invoke:Sentinel",
                    resource="directive:Sentinel",
                ),
            )
        ),
    )

    return RuntimeEngine().execute(verified, context)


if __name__ == "__main__":
    result = run_sentinel_demo()

    print("ok:", result.ok)
    print("Awareness:", result.final_state.get_int("state:Awareness"))
    print("events:", [event.event for event in result.delta.events])