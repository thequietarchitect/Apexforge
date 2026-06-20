"""Hand-authored AIR example for Gravitas/Sentinel/Vigilance/Response.

This module is deliberately AIR-first:
- no lexer
- no parser
- no AST execution
- runtime consumes verified AIR only
"""

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


EXPECTED_EVENT_ID = "directive:Gravitas:cause:Response:path:Escalate:event:0:event:Response"


def build_gravitas_program() -> AIRProgram:
    """Build the canonical hand-authored Gravitas AIR program."""
    return AIRProgram(
        version=AIR_VERSION,
        principals=(
            Principal(id="principal:Sentinel", display_name="Sentinel"),
        ),
        states=(
            StateDefinition(id="state:Vigilance", initial=10),
        ),
        events=(
            EventDefinition(id="event:Response", name="Response"),
        ),
        authority_checks=(
            AuthorityCheck(
                id="auth:Sentinel:Gravitas",
                principal="principal:Sentinel",
                capability="directive.invoke:Gravitas",
                resource="state:Vigilance",
            ),
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Response",
                cause="Response",
                paths=(
                    CausalPath(
                        id="path:Observe",
                        weight=30,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 1),),
                        emits=(EventEmission("event:Response", facts(path="Observe")),),
                        rationale="Low-pressure observation.",
                    ),
                    CausalPath(
                        id="path:Hold",
                        weight=40,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 2),),
                        emits=(EventEmission("event:Response", facts(path="Hold")),),
                        rationale="Moderate response path.",
                    ),
                    CausalPath(
                        id="path:Escalate",
                        weight=70,
                        assignments=(StateAssignment("state:Vigilance", "add_int", 5),),
                        emits=(EventEmission("event:Response", facts(path="Escalate")),),
                        rationale="Highest-weight response path.",
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:Gravitas",
                name="Gravitas",
                principal="principal:Sentinel",
                authority_checks=("auth:Sentinel:Gravitas",),
                causal_decisions=("cause:Response",),
                order=0,
            ),
        ),
    )


def build_gravitas_context(program: AIRProgram) -> ExecutionContext:
    """Build an execution context where Sentinel is allowed to invoke Gravitas."""
    return ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(
            (
                AuthorityGrant(
                    principal="principal:Sentinel",
                    capability="directive.invoke:Gravitas",
                    resource="state:Vigilance",
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


def run_gravitas_demo() -> ExecutionResult:
    """Verify and execute the canonical Gravitas AIR program."""
    program = build_gravitas_program()
    verified = AIRVerifier().verify(program).require_verified()
    return RuntimeEngine().execute(verified, build_gravitas_context(program))


def run_smoke_tests() -> None:
    """Run dependency-free checks for the Gravitas AIR demo."""
    program = build_gravitas_program()
    verifier = AIRVerifier()
    verification = verifier.verify(program)
    if not verification.ok:
        raise AssertionError(f"valid Gravitas AIR should verify: {verification.diagnostics}")

    verified = verification.require_verified()
    decision = program.causal_decisions[0]
    causal_selection = CausalEngine().select_path(decision)
    if causal_selection.path.id != "path:Escalate":
        raise AssertionError("highest-weight causal path should be path:Escalate")

    original_state = StateSnapshot.from_program_initials(program)
    allowed_context = ExecutionContext(
        state=original_state,
        authority=build_gravitas_context(program).authority,
    )
    result = RuntimeEngine().execute(verified, allowed_context)
    if not result.ok:
        raise AssertionError(f"Gravitas execution should succeed: {result.diagnostics}")
    if result.final_state.get_int("state:Vigilance") != 15:
        raise AssertionError("Escalate should add 5 to Vigilance")
    if result.delta.events[0].id != EXPECTED_EVENT_ID:
        raise AssertionError("event ID must be deterministic")
    if original_state.get_int("state:Vigilance") != 10:
        raise AssertionError("StateSnapshot must remain immutable after execution")

    denied_result = RuntimeEngine().execute(verified, build_denied_context(program))
    if denied_result.ok:
        raise AssertionError("authority denial should produce an error diagnostic")
    if not any(diagnostic.code == "RUN001" for diagnostic in denied_result.diagnostics):
        raise AssertionError("authority denial should produce RUN001")
    if not denied_result.delta.is_empty:
        raise AssertionError("authority denial should produce no state delta")
    if denied_result.final_state.get_int("state:Vigilance") != 10:
        raise AssertionError("authority denial should not change state")


__all__ = [
    "EXPECTED_EVENT_ID",
    "build_denied_context",
    "build_gravitas_context",
    "build_gravitas_program",
    "run_gravitas_demo",
    "run_smoke_tests",
]
