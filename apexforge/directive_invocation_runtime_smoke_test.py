"""Focused smoke tests for transactional directive invocation execution."""

from __future__ import annotations

from air.expressions import (
    AIRBinaryExpression,
    AIRIdentifierReference,
    AIRIntegerLiteral,
)
from air.model import (
    AIRDirective,
    AIRProgram,
    AIRWhenAction,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from authority.engine import AuthorityEngine
from authority.model import AuthorityCheck, AuthorityGrant, Principal
from causality.model import (
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)
from language.validation.runtime_validator import RuntimeValidator
from runtime.context import ExecutionContext
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invocation_program() -> AIRProgram:
    caller_check = AuthorityCheck(
        id="auth:Caller",
        principal="principal:Caller",
        capability="directive.invoke:Caller",
        resource="directive:Caller",
    )
    callee_check = AuthorityCheck(
        id="auth:Callee",
        principal="principal:Callee",
        capability="directive.invoke:Callee",
        resource="directive:Callee",
    )

    callee_path = CausalPath(
        id="path:Callee",
        weight=1,
        actions=(
            AIRWhenAction(
                condition=AIRBinaryExpression(
                    left=AIRIdentifierReference("count"),
                    operator="==",
                    right=AIRIntegerLiteral(1),
                ),
                actions=(
                    StateAssignment(
                        state="state:count",
                        operation="add_int",
                        value=AIRIntegerLiteral(2),
                    ),
                    EventEmission(
                        event="event:CalleeUpdated",
                    ),
                ),
                otherwise_actions=(
                    StateAssignment(
                        state="state:count",
                        operation="add_int",
                        value=AIRIntegerLiteral(100),
                    ),
                ),
            ),
        ),
    )

    caller_path = CausalPath(
        id="path:Caller",
        weight=1,
        actions=(
            StateAssignment(
                state="state:count",
                operation="add_int",
                value=AIRIntegerLiteral(1),
            ),
            DirectiveInvocation(
                target="Callee",
            ),
            AIRWhenAction(
                condition=AIRBinaryExpression(
                    left=AIRIdentifierReference("count"),
                    operator="==",
                    right=AIRIntegerLiteral(3),
                ),
                actions=(
                    StateAssignment(
                        state="state:count",
                        operation="add_int",
                        value=AIRIntegerLiteral(4),
                    ),
                ),
                otherwise_actions=(
                    StateAssignment(
                        state="state:count",
                        operation="add_int",
                        value=AIRIntegerLiteral(1000),
                    ),
                ),
            ),
            EventEmission(
                event="event:CallerUpdated",
            ),
        ),
    )

    return AIRProgram(
        version=AIR_VERSION,
        states=(
            StateDefinition(
                id="state:count",
                initial=AIRIntegerLiteral(0),
            ),
        ),
        events=(
            EventDefinition(
                id="event:CalleeUpdated",
                name="CalleeUpdated",
            ),
            EventDefinition(
                id="event:CallerUpdated",
                name="CallerUpdated",
            ),
        ),
        authority_checks=(
            caller_check,
            callee_check,
        ),
        causal_decisions=(
            CausalDecision(
                id="cause:Caller",
                cause="Caller",
                paths=(caller_path,),
            ),
            CausalDecision(
                id="cause:Callee",
                cause="Callee",
                paths=(callee_path,),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:Caller",
                name="Caller",
                principal="principal:Caller",
                authority_checks=(caller_check.id,),
                causal_decisions=("cause:Caller",),
                order=0,
            ),
            AIRDirective(
                id="directive:Callee",
                name="Callee",
                principal="principal:Callee",
                authority_checks=(callee_check.id,),
                causal_decisions=("cause:Callee",),
                order=1,
            ),
        ),
        requirements=(),
        authorities=(),
        principals=(
            Principal("principal:Caller", "Caller"),
            Principal("principal:Callee", "Callee"),
        ),
        roles=(),
    )


def cycle_program() -> AIRProgram:
    check_a = AuthorityCheck(
        id="auth:A",
        principal="principal:A",
        capability="directive.invoke:A",
        resource="directive:A",
    )
    check_b = AuthorityCheck(
        id="auth:B",
        principal="principal:B",
        capability="directive.invoke:B",
        resource="directive:B",
    )

    return AIRProgram(
        version=AIR_VERSION,
        states=(
            StateDefinition(
                id="state:count",
                initial=AIRIntegerLiteral(0),
            ),
        ),
        events=(),
        authority_checks=(check_a, check_b),
        causal_decisions=(
            CausalDecision(
                id="cause:A",
                cause="A",
                paths=(
                    CausalPath(
                        id="path:A",
                        weight=1,
                        actions=(
                            StateAssignment(
                                "state:count",
                                "add_int",
                                AIRIntegerLiteral(1),
                            ),
                            DirectiveInvocation(target="B"),
                        ),
                    ),
                ),
            ),
            CausalDecision(
                id="cause:B",
                cause="B",
                paths=(
                    CausalPath(
                        id="path:B",
                        weight=1,
                        actions=(
                            StateAssignment(
                                "state:count",
                                "add_int",
                                AIRIntegerLiteral(2),
                            ),
                            DirectiveInvocation(target="A"),
                        ),
                    ),
                ),
            ),
        ),
        directives=(
            AIRDirective(
                id="directive:A",
                name="A",
                principal="principal:A",
                authority_checks=(check_a.id,),
                causal_decisions=("cause:A",),
                order=0,
            ),
            AIRDirective(
                id="directive:B",
                name="B",
                principal="principal:B",
                authority_checks=(check_b.id,),
                causal_decisions=("cause:B",),
                order=1,
            ),
        ),
        requirements=(),
        authorities=(),
        principals=(
            Principal("principal:A", "A"),
            Principal("principal:B", "B"),
        ),
        roles=(),
    )


def grant(principal: str, name: str) -> AuthorityGrant:
    return AuthorityGrant(
        principal=f"principal:{principal}",
        capability=f"directive.invoke:{name}",
        resource=f"directive:{name}",
    )


def main() -> None:
    program = invocation_program()
    verified = RuntimeValidator().validate(program)
    initial = StateSnapshot.from_program_initials(program)

    authorized = RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=initial,
            authority=AuthorityEngine.from_grants(
                (
                    grant("Caller", "Caller"),
                    grant("Callee", "Callee"),
                )
            ),
        ),
        entry_directives=("Caller",),
    )

    require(authorized.ok, f"authorized invocation failed: {authorized.diagnostics}")
    require(
        authorized.final_state.get_int("count") == 7,
        "caller/callee state visibility produced the wrong final value",
    )
    require(
        tuple(item.value for item in authorized.delta.assignments)
        == (1, 2, 4),
        "nested assignments were not preserved in execution order",
    )
    require(
        tuple(event.directive for event in authorized.delta.events)
        == ("directive:Callee", "directive:Caller"),
        "nested events were not preserved in execution order",
    )
    require(
        len({event.id for event in authorized.delta.events}) == 2,
        "nested event IDs must remain unique",
    )

    trace_kinds = tuple(step.kind for step in authorized.trace.steps)
    require(
        "directive.invoke.start" in trace_kinds
        and "directive.invoke.finish" in trace_kinds,
        "successful invocation trace boundaries are missing",
    )

    denied = RuntimeEngine().execute(
        verified,
        ExecutionContext(
            state=initial,
            authority=AuthorityEngine.from_grants(
                (grant("Caller", "Caller"),)
            ),
        ),
        entry_directives=("directive:Caller",),
    )

    require(not denied.ok, "callee authority denial must fail the invocation")
    require(
        denied.final_state.get_int("count") == 0,
        "denied nested invocation must roll back the caller path",
    )
    require(
        denied.delta.is_empty,
        "denied nested invocation must return an empty delta",
    )

    cyclic_program = cycle_program()
    cyclic_verified = RuntimeValidator().validate(cyclic_program)
    cyclic_initial = StateSnapshot.from_program_initials(cyclic_program)

    cyclic = RuntimeEngine().execute(
        cyclic_verified,
        ExecutionContext(
            state=cyclic_initial,
            authority=AuthorityEngine.from_grants(
                (
                    grant("A", "A"),
                    grant("B", "B"),
                )
            ),
        ),
        entry_directives=("A",),
    )

    require(not cyclic.ok, "A -> B -> A must be rejected")
    require(
        cyclic.final_state.get_int("count") == 0,
        "cyclic invocation must roll back every candidate update",
    )
    require(
        any(diagnostic.code == "RUN003" for diagnostic in cyclic.diagnostics),
        "cycle rejection must produce RUN003",
    )

    print("Directive invocation runtime smoke test passed.")
    print("Nested state visibility: PASS")
    print("Independent authority checks: PASS")
    print("Transactional rollback: PASS")
    print("Cycle detection: PASS")
    print("Deterministic event order: PASS")


if __name__ == "__main__":
    main()