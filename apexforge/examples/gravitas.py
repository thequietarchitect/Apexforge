"""Gravitas directive demo."""

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


def build_gravitas_program() -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(
                id="principal:Gravitas",
                display_name="Gravitas",
            ),
        ),
        states=(
            StateDefinition(
                id="state:Vigilance",
                initial=10,
            ),
        ),
        events=(
            EventDefinition(
                id="event:Response",
                name="Response",
            ),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:Gravitas",
                principal="principal:Gravitas",
                capability="directive.invoke:Gravitas",
                resource="directive:Gravitas",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Response",
                cause="Response",
                policy="max_weight",
                paths=(
                    CausalPath(
                        id="path:Observe",
                        weight=30,
                        assignments=(
                            StateAssignment(
                                state="state:Vigilance",
                                operation="add_int",
                                value=1,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:Response",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Gravitas observes without escalation.",
                    ),
                    CausalPath(
                        id="path:Hold",
                        weight=40,
                        assignments=(
                            StateAssignment(
                                state="state:Vigilance",
                                operation="add_int",
                                value=2,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:Response",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Gravitas holds position and increases vigilance.",
                    ),
                    CausalPath(
                        id="path:Escalate",
                        weight=70,
                        assignments=(
                            StateAssignment(
                                state="state:Vigilance",
                                operation="add_int",
                                value=5,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:Response",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="Gravitas escalates response under highest causal weight.",
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:Gravitas",
                name="Gravitas",
                principal="principal:Gravitas",
                authority_checks=("auth:Gravitas",),
                causal_decisions=("cause:Response",),
                order=0,
            ),
        ),
    )


def run_gravitas_demo():
    program = build_gravitas_program()

    verified = AIRVerifier().verify(program).require_verified()

    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Gravitas",
                    capability="directive.invoke:Gravitas",
                    resource="directive:Gravitas",
                ),
            )
        ),
    )

    return RuntimeEngine().execute(verified, context)


if __name__ == "__main__":
    result = run_gravitas_demo()

    print("ok:", result.ok)
    print("Vigilance:", result.final_state.get_int("state:Vigilance"))
    print("events:", [event.event for event in result.delta.events])