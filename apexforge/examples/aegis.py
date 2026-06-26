"""AEGIS directive demo."""

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


def build_aegis_program() -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(
                id="principal:AEGIS",
                display_name="AEGIS",
            ),
        ),
        states=(
            StateDefinition(
                id="state:Integrity",
                initial=5,
            ),
        ),
        events=(
            EventDefinition(
                id="event:AegisValidation",
                name="AegisValidation",
            ),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:AEGIS",
                principal="principal:AEGIS",
                capability="directive.invoke:AEGIS",
                resource="directive:AEGIS",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Validation",
                cause="Validation",
                policy="max_weight",
                paths=(
                    CausalPath(
                        id="path:Pass",
                        weight=30,
                        assignments=(
                            StateAssignment(
                                state="state:Integrity",
                                operation="add_int",
                                value=0,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:AegisValidation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="AEGIS passes validation without intervention.",
                    ),
                    CausalPath(
                        id="path:Review",
                        weight=60,
                        assignments=(
                            StateAssignment(
                                state="state:Integrity",
                                operation="add_int",
                                value=2,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:AegisValidation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="AEGIS reviews and reinforces integrity.",
                    ),
                    CausalPath(
                        id="path:Stabilize",
                        weight=90,
                        assignments=(
                            StateAssignment(
                                state="state:Integrity",
                                operation="add_int",
                                value=4,
                            ),
                        ),
                        emits=(
                            EventEmission(
                                event="event:AegisValidation",
                                facts=(),
                            ),
                        ),
                        invocations=(),
                        effects=(),
                        rationale="AEGIS stabilizes integrity under validated pressure.",
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:AEGIS",
                name="AEGIS",
                principal="principal:AEGIS",
                authority_checks=("auth:AEGIS",),
                causal_decisions=("cause:Validation",),
                order=0,
            ),
        ),
    )


def run_aegis_demo():
    program = build_aegis_program()

    verified = AIRVerifier().verify(program).require_verified()

    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:AEGIS",
                    capability="directive.invoke:AEGIS",
                    resource="directive:AEGIS",
                ),
            )
        ),
    )

    return RuntimeEngine().execute(verified, context)


if __name__ == "__main__":
    result = run_aegis_demo()

    print("ok:", result.ok)
    print("Integrity:", result.final_state.get_int("state:Integrity"))
    print("events:", [event.event for event in result.delta.events])