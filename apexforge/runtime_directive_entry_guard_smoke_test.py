"""Focused transactional RuntimeEngine directive-entry guard coverage."""

from __future__ import annotations

from air.expressions import AIRIntegerLiteral
from air.model import (
    AIRDirective,
    AIRProgram,
    EventDefinition,
    EventEmission,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from air.verify import AIRVerifier
from authority.engine import AuthorityEngine
from authority.model import Principal
from authority.validator import (
    PrincipalAuthorizationError,
    PrincipalCapabilityAuthorizationError,
)
from causality.model import (
    CausalDecision,
    CausalPath,
    DirectiveInvocation,
)
from effects.model import EffectIntent
from runtime.context import ExecutionContext
from runtime.engine import (
    DirectiveEntryConfigurationError,
    RuntimeEngine,
    RuntimeExpressionError,
)
from runtime.state import StateSnapshot


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class RecordingRuntimeEngine(RuntimeEngine):
    def __init__(self):
        super().__init__()
        self.evaluated_assignment_values = []
        self.evaluated_event_batches = 0

    def _evaluate_assignment(
        self,
        assignment,
        state,
        *,
        functions,
        trace_steps,
    ):
        self.evaluated_assignment_values.append(
            assignment.value.value
        )
        return super()._evaluate_assignment(
            assignment,
            state,
            functions=functions,
            trace_steps=trace_steps,
        )

    def _evaluate_facts(
        self,
        fact_values,
        state,
        *,
        functions,
        trace_steps,
    ):
        self.evaluated_event_batches += 1
        return super()._evaluate_facts(
            fact_values,
            state,
            functions=functions,
            trace_steps=trace_steps,
        )


def make_program():
    caller_decision = CausalDecision(
        id="cause:Caller",
        cause="Caller",
        paths=(
            CausalPath(
                id="path:Caller",
                weight=10,
                actions=(
                    StateAssignment(
                        state="state:value",
                        operation="add_int",
                        value=AIRIntegerLiteral(1),
                    ),
                    DirectiveInvocation(target="Child"),
                    StateAssignment(
                        state="state:value",
                        operation="add_int",
                        value=AIRIntegerLiteral(1000),
                    ),
                    EventEmission(event="event:After"),
                    DirectiveInvocation(target="After"),
                ),
                effects=(
                    EffectIntent(
                        id="effect:Caller",
                        effect_type="caller.effect",
                    ),
                ),
            ),
        ),
    )
    child_decision = CausalDecision(
        id="cause:Child",
        cause="Child",
        paths=(
            CausalPath(
                id="path:Child",
                weight=10,
                actions=(
                    StateAssignment(
                        state="state:value",
                        operation="add_int",
                        value=AIRIntegerLiteral(100),
                    ),
                    EventEmission(event="event:Child"),
                    DirectiveInvocation(target="Grandchild"),
                ),
                effects=(
                    EffectIntent(
                        id="effect:Child",
                        effect_type="child.effect",
                    ),
                ),
            ),
        ),
    )
    after_decision = CausalDecision(
        id="cause:After",
        cause="After",
        paths=(
            CausalPath(
                id="path:After",
                weight=10,
                actions=(
                    StateAssignment(
                        state="state:value",
                        operation="add_int",
                        value=AIRIntegerLiteral(10000),
                    ),
                ),
            ),
        ),
    )
    grandchild_decision = CausalDecision(
        id="cause:Grandchild",
        cause="Grandchild",
        paths=(
            CausalPath(
                id="path:Grandchild",
                weight=10,
                actions=(
                    StateAssignment(
                        state="state:value",
                        operation="add_int",
                        value=AIRIntegerLiteral(100000),
                    ),
                ),
            ),
        ),
    )

    directives = tuple(
        AIRDirective(
            id=f"directive:{name}",
            name=name,
            principal=f"principal:{name}",
            authority_checks=(),
            causal_decisions=(f"cause:{name}",),
            order=order,
        )
        for order, name in enumerate(
            (
                "Caller",
                "Child",
                "After",
                "Grandchild",
            )
        )
    )

    return AIRProgram(
        version=AIR_VERSION,
        states=(
            StateDefinition(
                id="state:value",
                initial=AIRIntegerLiteral(0),
            ),
        ),
        events=(
            EventDefinition("event:Child", "Child"),
            EventDefinition("event:After", "After"),
        ),
        authority_checks=(),
        causal_decisions=(
            caller_decision,
            child_decision,
            after_decision,
            grandchild_decision,
        ),
        directives=directives,
        requirements=(),
        authorities=(),
        principals=tuple(
            Principal(
                id=directive.principal,
                display_name=directive.name,
            )
            for directive in directives
        ),
        roles=(),
        functions=(),
        workflows=(),
    )


def test_authorization_exception_rolls_back_candidate():
    program = make_program()
    verified = AIRVerifier().verify(program).require_verified()
    initial = StateSnapshot.from_program_initials(program)
    context = ExecutionContext(
        state=initial,
        authority=AuthorityEngine.from_grants(()),
    )
    runtime = RecordingRuntimeEngine()
    guard_entries = []
    escaped_result = None

    def deny_child(directive):
        guard_entries.append(directive.id)

        if directive.id == "directive:Child":
            raise PrincipalAuthorizationError(
                "Principal 'principal:Actor' lacks "
                "authority 'Denied'."
            )

    try:
        escaped_result = runtime.execute(
            verified,
            context,
            entry_directives=("Caller",),
            directive_entry_guard=deny_child,
        )
    except PrincipalAuthorizationError as error:
        require(
            str(error)
            == (
                "Principal 'principal:Actor' lacks "
                "authority 'Denied'."
            ),
            "authorization exception changed",
        )
    else:
        raise AssertionError(
            "child authorization denial did not escape"
        )

    require(
        escaped_result is None,
        "denied transaction exposed an ExecutionResult",
    )
    require(
        guard_entries
        == ["directive:Caller", "directive:Child"],
        "child or later caller invocations executed after denial",
    )
    require(
        runtime.evaluated_assignment_values == [1],
        "child or post-invocation caller assignments executed",
    )
    require(
        runtime.evaluated_event_batches == 0,
        "child or post-invocation caller events executed",
    )
    require(
        context.state == initial
        and context.state.get_int("value") == 0,
        "original execution context was mutated",
    )

    # Effects are passive values exposed only through ExecutionResult.delta.
    # Because no result escaped and neither selected path completed, neither
    # the child nor caller EffectIntent escaped the failed transaction.


def test_capability_exception_is_not_run002():
    program = make_program()
    verified = AIRVerifier().verify(program).require_verified()
    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(()),
    )

    def deny_child(directive):
        if directive.id == "directive:Child":
            raise PrincipalCapabilityAuthorizationError(
                "Principal 'principal:Actor' lacks required "
                "capabilities: Execute."
            )

    try:
        RuntimeEngine().execute(
            verified,
            context,
            entry_directives=("Caller",),
            directive_entry_guard=deny_child,
        )
    except PrincipalCapabilityAuthorizationError as error:
        require(
            "Execute" in str(error),
            "capability exception changed",
        )
    else:
        raise AssertionError(
            "capability denial was converted into a runtime result"
        )


def test_guard_expression_error_is_configuration_error():
    program = make_program()
    verified = AIRVerifier().verify(program).require_verified()
    context = ExecutionContext(
        state=StateSnapshot.from_program_initials(program),
        authority=AuthorityEngine.from_grants(()),
    )

    def invalid_guard(directive):
        if directive.id == "directive:Child":
            raise RuntimeExpressionError(
                "guard configuration is invalid"
            )

    try:
        RuntimeEngine().execute(
            verified,
            context,
            entry_directives=("Caller",),
            directive_entry_guard=invalid_guard,
        )
    except DirectiveEntryConfigurationError as error:
        require(
            str(error) == "guard configuration is invalid",
            "guard configuration diagnostic changed",
        )
    else:
        raise AssertionError(
            "guard error was mislabeled as RUN002"
        )


def main():
    test_authorization_exception_rolls_back_candidate()
    test_capability_exception_is_not_run002()
    test_guard_expression_error_is_configuration_error()
    print(
        "Runtime directive-entry guard smoke test passed."
    )


if __name__ == "__main__":
    main()
