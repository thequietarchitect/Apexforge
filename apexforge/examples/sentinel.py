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


EXPECTED_EVENT_ID = "directive:Sentinel:cause:Observation:path:Investigate:event:0:event:SentinelObservation"


def build_sentinel_program() -> AIRProgram:
    """Build the canonical hand-authored Sentinel AIR program."""
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(id="principal:Sentinel", display_name="Sentinel"),
        ),
        states=(
            StateDefinition(id="state:Awareness", initial=0),
        ),
        events=(
            EventDefinition(id="event:SentinelObservation", name="SentinelObservation"),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:Sentinel:Gravitas",
                principal="principal:Sentinel",
                capability="directive.invoke:Sentinel",
                resource="state:Awareness",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Observation",
                cause="Observation",
                paths=(
                    CausalPath(
                        id="path:Ignore",
                        weight=20,
                        assignments=(StateAssignment("state:Awareness", "add_int", 0),),
                        emits=(EventEmission("event:SentinelObservation", facts(path="Ignore")),),
                        rationale="No significant signal.",
                    ),
                    CausalPath(
                        id="path:Monitor",
                        weight=50,
                        assignments=(StateAssignment("state:Awareness", "add_int", 1),),
                        emits=(EventEmission("event:SentinelObservation", facts(path="Monitor")),),
                        rationale="Continue Observation.",
                    ),
                    CausalPath(
                        id="path:Investigate",
                        weight=80,
                        assignments=(StateAssignment("state:Awareness", "add_int", 3),),
                        emits=(EventEmission("event:Response", facts(path="Investigate")),),
                        rationale="Highest awareness path.",
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


def build_sentinel_context(program: AIRProgram) -> ExecutionContext:
    """Build an execution context where Sentinel is allowed to invoke Gravitas."""
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Sentinel",
                    capability="directive.invoke:Sentinel",
                    resource="state:Awareness",
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


def run_sentinel_demo() -> ExecutionResult:
    """Verify and execute the canonical SENTINEL AIR program."""
    program = build_sentinel_program()
    verified = AIRVerifier().verify(program).require_verified()
    return RuntimeEngine().execute(verified, build_sentinel_context(program))


def run_smoke_tests() -> None:
    """Run dependency-free checks for the Sentinel AIR demo."""
    program = build_sentinel_program()
    verifier = AIRVerifier()
    verification = verifier.verify(program)
    if not verification.ok:
        raise AssertionError(f"valid Sentinel AIR should verify: {verification.diagnostics}")

    verified = verification.require_verified()
    decision = program.causal_decisions[0]
    causal_selection = CausalEngine().select_path(decision)
    if causal_selection.path.id != "path:Investigate":
        raise AssertionError("highest-weight causal path should be path:Investigate")

    original_state = StateSnapshot.from_program_initials(program)
    allowed_context = ExecutionContext(
        state=original_state,
        authority=build_sentinel_context(program).authority,
    )
    result = RuntimeEngine().execute(verified, allowed_context)
    if not result.ok:
        raise AssertionError(f"Sentinel execution should succeed: {result.diagnostics}")
    if result.final_state.get_int("state:Awareness") != 3:
        raise AssertionError("Investigate should add 3 to Awareness")
    if result.delta.events[0].id != EXPECTED_EVENT_ID:
        raise AssertionError("event ID must be deterministic")
    if original_state.get_int("state:Awareness") != 0:
        raise AssertionError("StateSnapshot must remain immutable after execution")

    denied_result = RuntimeEngine().execute(verified, build_denied_context(program))
    if denied_result.ok:
        raise AssertionError("authority denial should produce an error diagnostic")
    if not any(diagnostic.code == "RUN001" for diagnostic in denied_result.diagnostics):
        raise AssertionError("authority denial should produce RUN001")
    if not denied_result.delta.is_empty:
        raise AssertionError("authority denial should produce no state delta")
    if denied_result.final_state.get_int("state:Awareness") != 0:
        raise AssertionError("authority denial should not change state")


__all__ = [
    "EXPECTED_EVENT_ID",
    "build_denied_context",
    "build_sentinel_context",
    "build_sentinel_program",
    "run_sentinel_demo",
    "run_smoke_tests",
]

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
                resource="state:Awareness",
            ),
        ),

        causal_decisions=(
            CausalDecision(
                id="cause:Observation",
                cause="Observation",

                paths=(

                    CausalPath(
                        id="path:Ignore",
                        weight=20,

                        assignments=(
                            StateAssignment(
                                "state:Awareness",
                                "add_int",
                                0,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:SentinelObservation",
                                facts(path="Ignore"),
                            ),
                        ),

                        rationale="No significant signal.",
                    ),

                    CausalPath(
                        id="path:Monitor",
                        weight=50,

                        assignments=(
                            StateAssignment(
                                "state:Awareness",
                                "add_int",
                                1,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:SentinelObservation",
                                facts(path="Monitor"),
                            ),
                        ),

                        rationale="Continue observation.",
                    ),

                    CausalPath(
                        id="path:Investigate",
                        weight=80,

                        assignments=(
                            StateAssignment(
                                "state:Awareness",
                                "add_int",
                                3,
                            ),
                        ),

                        emits=(
                            EventEmission(
                                "event:SentinelObservation",
                                facts(path="Investigate"),
                            ),
                        ),

                        rationale="Highest awareness path.",
                    ),
                ),
            ),
        ),

        directives=(
            AIRDirective(
                id="directive:Sentinel",
                name="Sentinel",
                principal="principal:Sentinel",

                authority_checks=(
                    "auth:Sentinel",
                ),

                causal_decisions=(
                    "cause:Observation",
                ),

                order=0,
            ),
        ),
    )