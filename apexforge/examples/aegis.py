from __future__ import annotations

from air.model import (
    AIRDirective,
    AIRProgram,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
    facts,
)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.engine import AuthorityEngine
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from causality.engine import CausalEngine
from causality.model import CausalDecision, CausalPath
from runtime.context import ExecutionContext
from runtime.engine import ExecutionResult, RuntimeEngine
from runtime.state import StateSnapshot


EXPECTED_EVENT_ID = "directive:AEGIS:cause:Validation:path:Stabilize:event:0:event:AegisValidation"


def build_aegis_program() -> AIRProgram:
    """Build the canonical hand-authored AEGIS AIR program."""
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(id="principal:AEGIS", display_name="AEGIS"),
        ),
        states=(
            StateDefinition(id="state:Integrity", initial=5),
        ),
        events=(
            EventDefinition(id="event:AegisValidation", name="AegisValidation"),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:AEGIS",
                principal="principal:AEGIS",
                capability="directive.invoke:AEGIS",
                resource="state:Integrity",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Validation",
                cause="Validation",
                paths=(
                    CausalPath(
                        id="path:Pass",
                        weight=30,
                        assignments=(StateAssignment("state:Integrity", "add_int", 0),),
                        emits=(EventEmission("event:AegisValidation", facts(path="Pass")),),
                        rationale="Validation succeeded with no corrective action required.",
                    ),
                    CausalPath(
                        id="path:Review",
                        weight=60,
                        assignments=(StateAssignment("state:Integrity", "add_int", 2),),
                        emits=(EventEmission("event:AegisValidation", facts(path="Review")),),
                        rationale="Additional evaluation is warranted before final acceptance.",
                    ),
                    CausalPath(
                        id="path:Stabilize",
                        weight=90,
                        assignments=(StateAssignment("state:Integrity", "add_int", 4),),
                        emits=(EventEmission("event:AegisValidation", facts(path="Stabilize")),),
                        rationale="Integrity risk detected;stabilization is the highest-priority response.",
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


def build_aegis_context(program: AIRProgram) -> ExecutionContext:
    """Build an execution context where Sentinel is allowed to invoke Gravitas."""
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:AEGIS",
                    capability="directive.invoke:AEGIS",
                    resource="state:Integrity",
                ),
            )
        ),
    )


def build_denied_context(program: AIRProgram) -> ExecutionContext:
    """Build an execution context with no grants."""
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(()),
    )


def run_aegis_demo() -> ExecutionResult:
    """Verify and execute the canonical Gravitas AIR program."""
    program = build_aegis_program()
    verified = AIRVerifier().verify(program).require_verified()
    return RuntimeEngine().execute(verified, build_aegis_context(program))


def run_smoke_tests() -> None:
    """Run dependency-free checks for the AEGIS AIR demo."""
    program = build_aegis_program()
    verifier = AIRVerifier()
    verification = verifier.verify(program)
    if not verification.ok:
        raise AssertionError(f"valid AEGIS AIR should verify: {verification.diagnostics}")

    verified = verification.require_verified()
    decision = program.causal_decisions[0]
    causal_selection = CausalEngine().select_path(decision)
    if causal_selection.path.id != "path:Stabilize":
        raise AssertionError("highest-weight causal path should be path:Stabilize")

    original_state = StateSnapshot.from_program_initials(program)
    allowed_context = ExecutionContext(
        state=original_state,
        authority=build_aegis_context(program).authority,
    )
    result = RuntimeEngine().execute(verified, allowed_context)
    if not result.ok:
        raise AssertionError(f"AEGIS execution should succeed: {result.diagnostics}")
    if result.final_state.get_int("state:Integrity") != 9:
        raise AssertionError("Stabilize should add 4 to Integrity")
    if result.delta.events[0].id != EXPECTED_EVENT_ID:
        raise AssertionError("event ID must be deterministic")
    if original_state.get_int("state:Integrity") != 5:
        raise AssertionError("StateSnapshot must remain immutable after execution")

    denied_result = RuntimeEngine().execute(verified, build_denied_context(program))
    if denied_result.ok:
        raise AssertionError("authority denial should produce an error diagnostic")
    if not any(diagnostic.code == "RUN001" for diagnostic in denied_result.diagnostics):
        raise AssertionError("authority denial should produce RUN001")
    if not denied_result.delta.is_empty:
        raise AssertionError("authority denial should produce no state delta")
    if denied_result.final_state.get_int("state:Integrity") != 5:
        raise AssertionError("authority denial should not change state")


__all__ = [
    "EXPECTED_EVENT_ID",
    "build_denied_context",
    "build_aegis_context",
    "build_aegis_program",
    "run_aegis_demo",
    "run_smoke_tests",
]

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
                resource="state:Integrity",
            ),
        ),

        causal_decisions=(
            CausalDecision(
                id="cause:Validation",
                cause="Validation",

                paths=(

                    CausalPath(
                        id="path:Pass",
                        weight=30,

                        assignments=(
                            StateAssignment(
                                "state:Integrity",
                                "add_int",
                                0,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:AegisValidation",
                                facts(path="Pass"),
                            ),
                        ),

                        rationale="Validation succeeded with no corrective action required.",
                    ),

                    CausalPath(
                        id="path:Review",
                        weight=60,

                        assignments=(
                            StateAssignment(
                                "state:Integrity",
                                "add_int",
                                2,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:AegisValidation",
                                facts(path="Review"),
                            ),
                        ),

                        rationale="Additional evaluation is warranted before final acceptance.",
                    ),

                    CausalPath(
                        id="path:Stabilize",
                        weight=90,

                        assignments=(
                            StateAssignment(
                                "state:Integrity",
                                "add_int",
                                4,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:AegisValidation",
                                facts(path="Stabilize"),
                            ),
                        ),

                        rationale="Integrity risk detected;stabilization is the highest-priority response.",
                    ),
                ),
            ),
        ),

        directives=(
            AIRDirective(
                id="directive:AEGIS",
                name="AEGIS",
                principal="principal:AEGIS",

                authority_checks=(
                    "auth:AEGIS",
                ),

                causal_decisions=(
                    "cause:Validation",
                ),

                order=0,
            ),
        ),
    )