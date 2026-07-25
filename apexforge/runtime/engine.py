"""AIR runtime execution engine with expression evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, Tuple

from air.ids import event_record_id
from air.model import EventRecord, VerifiedAIRProgram, facts
from air.indexes import index_by_id

from air.expressions import (
    AIRExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
    AIRBooleanLiteral,
    AIRIdentifierReference,
    AIRUnaryExpression,
    AIRBinaryExpression,
    )

from causality.engine import CausalEngine

from runtime.context import ExecutionContext
from runtime.diagnostics import (
    Diagnostic,
    Trace,
    TraceStep,
    append_diagnostic,
)
from runtime.state import StateDelta, StateSnapshot


class RuntimeExpressionError(RuntimeError):
    """Raised when an AIR expression cannot be evaluated safely."""


@dataclass(frozen=True)
class ExecutionResult:
    delta: StateDelta
    trace: Trace
    diagnostics: Tuple[Diagnostic, ...]
    final_state: StateSnapshot

    @property
    def ok(self) -> bool:
        return not any(d.is_error for d in self.diagnostics)


class RuntimeEngine:
    def __init__(
        self,
        causality: Optional[CausalEngine] = None,
    ) -> None:
        self._causality = causality or CausalEngine()

    def execute(
        self,
        verified: VerifiedAIRProgram,
        context: ExecutionContext,
    ) -> ExecutionResult:

        if not isinstance(verified, VerifiedAIRProgram):
            raise TypeError(
                "RuntimeEngine.execute requires VerifiedAIRProgram"
            )

        program = verified.program

        diagnostics: list[Diagnostic] = []
        trace_steps: list[TraceStep] = []

        assignments = []
        events = []
        effects = []

        checks = index_by_id(program.authority_checks)
        decisions = index_by_id(program.causal_decisions)

        working_state = context.state

        trace_steps.append(
            TraceStep(
                "runtime.start",
                "started AIR execution",
                facts(version=program.version),
            )
        )

        for directive in program.directives:

            trace_steps.append(
                TraceStep(
                    "directive.start",
                    "entered directive",
                    facts(
                        directive=directive.id,
                        name=directive.name,
                        principal=directive.principal,
                    ),
                )
            )

            denied = False

            for check_id in directive.authority_checks:

                check = checks[check_id]
                allowed = context.authority.allows(check)

                trace_steps.append(
                    TraceStep(
                        "authority.check",
                        "evaluated authority check",
                        facts(
                            allowed=allowed,
                            capability=check.capability,
                            check=check.id,
                            principal=check.principal,
                            resource=check.resource,
                        ),
                    )
                )

                if not allowed:
                    denied = True

                    append_diagnostic(
                        diagnostics,
                        "error",
                        "RUN001",
                        (
                            f"authority denied: "
                            f"{check.principal} lacks "
                            f"{check.capability} on "
                            f"{check.resource}"
                        ),
                        directive.id,
                    )

            if denied:
                trace_steps.append(
                    TraceStep(
                        "directive.skip",
                        "skipped directive after authority denial",
                        facts(directive=directive.id),
                    )
                )
                continue

            for decision_id in directive.causal_decisions:

                decision = decisions[decision_id]

                selection = self._causality.select_path(
                    decision
                )

                selected = selection.path

                trace_steps.extend(
                    selection.trace_steps
                )

                try:
                    evaluated_assignments = tuple(
                        self._evaluate_assignment(
                            assignment,
                            working_state,
                        )
                        for assignment in selected.assignments
                    )

                    # Build the candidate state first. The selected path is
                    # committed only after all expressions and event facts
                    # evaluate successfully.
                    path_delta = StateDelta(
                        evaluated_assignments
                    )

                    candidate_state = working_state.apply(
                        path_delta
                    )

                    evaluated_emissions = tuple(
                        (
                            emission,
                            self._evaluate_facts(
                                emission.facts,
                                candidate_state,
                            ),
                        )
                        for emission in selected.emits
                    )

                except RuntimeExpressionError as exc:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "RUN002",
                        str(exc),
                        selected.id,
                    )

                    trace_steps.append(
                        TraceStep(
                            "expression.error",
                            "failed to evaluate selected path expression",
                            facts(
                                path=selected.id,
                                error=str(exc),
                            ),
                        )
                    )
                    continue

                working_state = candidate_state

                assignments.extend(
                    evaluated_assignments
                )

                trace_steps.append(
                    TraceStep(
                        "state.delta",
                        "applied selected path assignments",
                        facts(
                            assignments=len(evaluated_assignments),
                            path=selected.id,
                            state=(
                                evaluated_assignments[0].state
                                if evaluated_assignments
                                else ""
                            ),
                            operation=(
                                evaluated_assignments[0].operation
                                if evaluated_assignments
                                else ""
                            ),
                            value=(
                                evaluated_assignments[0].value
                                if evaluated_assignments
                                else 0
                            ),
                        ),
                    )
                )

                for index, (
                    emission,
                    evaluated_facts,
                ) in enumerate(evaluated_emissions):

                    event = EventRecord(
                        id=event_record_id(
                            directive.id,
                            decision.id,
                            selected.id,
                            index,
                            emission.event,
                        ),
                        event=emission.event,
                        directive=directive.id,
                        principal=directive.principal,
                        facts=evaluated_facts,
                    )

                    events.append(event)

                    trace_steps.append(
                        TraceStep(
                            "event.emit",
                            "queued event emission",
                            facts(
                                event=event.event,
                                event_id=event.id,
                            ),
                        )
                    )

                effects.extend(
                    selected.effects
                )

                for effect in selected.effects:
                    trace_steps.append(
                        TraceStep(
                            "effect.intent",
                            (
                                "queued host effect intent "
                                "without executing it"
                            ),
                            facts(
                                effect=effect.id,
                                effect_type=effect.effect_type,
                            ),
                        )
                    )

        delta = StateDelta(
            tuple(assignments),
            tuple(events),
            tuple(effects),
        )

        trace_steps.append(
            TraceStep(
                "runtime.finish",
                "finished AIR execution",
                facts(
                    events=len(events),
                    updates=len(assignments),
                ),
            )
        )

        return ExecutionResult(
            delta=delta,
            trace=Trace(tuple(trace_steps)),
            diagnostics=tuple(
                sorted(diagnostics)
            ),
            final_state=working_state,
        )

    def _evaluate_assignment(
        self,
        assignment: Any,
        state: StateSnapshot,
    ) -> Any:
        value = self._evaluate_expression(
            assignment.value,
            state,
        )

        operation = assignment.operation

        if operation in {
            "set_int",
            "add_int",
        }:
            if isinstance(value, bool) or not isinstance(
                value,
                int,
            ):
                raise RuntimeExpressionError(
                    f"assignment '{assignment.state}' uses "
                    f"{operation} but evaluated to "
                    f"{type(value).__name__}, not int"
                )

        return replace(
            assignment,
            value=value,
        )

    def _evaluate_facts(
        self,
        fact_values: Tuple[Any, ...],
        state: StateSnapshot,
    ) -> Tuple[Any, ...]:
        evaluated = []

        for fact in fact_values:
            raw_value = getattr(
                fact,
                "value",
                None,
            )

            value = self._evaluate_expression(
                raw_value,
                state,
            )

            evaluated.append(
                replace(
                    fact,
                    value=value,
                )
            )

        return tuple(evaluated)

    def _evaluate_expression(
        self,
        expression: Any,
        state: StateSnapshot,
    ) -> Any:
        """
        Evaluate AIR expressions recursively.

        Primitive AFP-P1 values pass through unchanged, preserving backward
        compatibility with programs compiled before expression support.
        """

        if not isinstance(
            expression,
            AIRExpression,
        ):
            return expression

        if isinstance(
            expression,
            AIRIntegerLiteral,
        ):
            return expression.value

        if isinstance(
            expression,
            AIRStringLiteral,
        ):
            return expression.value

        if isinstance(
            expression,
            AIRBooleanLiteral,
        ):
            return expression.value

        if isinstance(
            expression,
            AIRIdentifierReference,
        ):
            return self._resolve_identifier(
                expression.name,
                state,
            )

        if isinstance(
            expression,
            AIRUnaryExpression,
        ):
            operand = self._evaluate_expression(
                expression.operand,
                state,
            )

            operator = expression.operator

            if operator == "+":
                return self._require_number(
                    operand,
                    operator,
                )

            if operator == "-":
                return -self._require_number(
                    operand,
                    operator,
                )

            if operator == "not":
                return not self._require_boolean(
                    operand,
                    operator,
                )

            raise RuntimeExpressionError(
                f"unsupported unary operator "
                f"{operator!r}"
            )

        if isinstance(
            expression,
            AIRBinaryExpression,
        ):
            operator = expression.operator

            # Preserve short-circuit behavior.
            if operator == "and":
                left = self._require_boolean(
                    self._evaluate_expression(
                        expression.left,
                        state,
                    ),
                    operator,
                )

                if not left:
                    return False

                return self._require_boolean(
                    self._evaluate_expression(
                        expression.right,
                        state,
                    ),
                    operator,
                )

            if operator == "or":
                left = self._require_boolean(
                    self._evaluate_expression(
                        expression.left,
                        state,
                    ),
                    operator,
                )

                if left:
                    return True

                return self._require_boolean(
                    self._evaluate_expression(
                        expression.right,
                        state,
                    ),
                    operator,
                )

            left = self._evaluate_expression(
                expression.left,
                state,
            )

            right = self._evaluate_expression(
                expression.right,
                state,
            )

            if operator == "+":
                # ApexForge permits message-oriented concatenation such as:
                # "Count: " + count
                if isinstance(left, str) or isinstance(
                    right,
                    str,
                ):
                    return str(left) + str(right)

                return (
                    self._require_number(
                        left,
                        operator,
                    )
                    + self._require_number(
                        right,
                        operator,
                    )
                )

            if operator == "-":
                return (
                    self._require_number(
                        left,
                        operator,
                    )
                    - self._require_number(
                        right,
                        operator,
                    )
                )

            if operator == "*":
                return (
                    self._require_number(
                        left,
                        operator,
                    )
                    * self._require_number(
                        right,
                        operator,
                    )
                )

            if operator == "/":
                divisor = self._require_number(
                    right,
                    operator,
                )

                if divisor == 0:
                    raise RuntimeExpressionError(
                        "division by zero"
                    )

                return (
                    self._require_number(
                        left,
                        operator,
                    )
                    / divisor
                )

            if operator == "%":
                divisor = self._require_number(
                    right,
                    operator,
                )

                if divisor == 0:
                    raise RuntimeExpressionError(
                        "modulo by zero"
                    )

                return (
                    self._require_number(
                        left,
                        operator,
                    )
                    % divisor
                )

            if operator == "==":
                return left == right

            if operator == "!=":
                return left != right

            if operator in {
                "<",
                "<=",
                ">",
                ">=",
            }:
                left_number = self._require_number(
                    left,
                    operator,
                )

                right_number = self._require_number(
                    right,
                    operator,
                )

                if operator == "<":
                    return left_number < right_number

                if operator == "<=":
                    return left_number <= right_number

                if operator == ">":
                    return left_number > right_number

                return left_number >= right_number

            raise RuntimeExpressionError(
                f"unsupported binary operator "
                f"{operator!r}"
            )

        raise RuntimeExpressionError(
            "unsupported AIR expression type "
            f"{type(expression).__name__}"
        )

    def _resolve_identifier(
        self,
        name: str,
        state: StateSnapshot,
    ) -> Any:
        """
        Resolve either a plain state name or its canonical state:<name> ID.

        This helper supports the common StateSnapshot layouts used during
        ApexForge prototyping. If your StateSnapshot exposes a dedicated lookup
        method, keep only that branch once its API is finalized.
        """

        candidates = (
            name,
            name if name.startswith("state:")
            else f"state:{name}",
        )

        sentinel = object()

        get_value = getattr(
            state,
            "get_value",
            None,
        )

        if callable(get_value):
            for candidate in candidates:
                try:
                    value = get_value(candidate)
                except (KeyError, LookupError):
                    continue

                if value is not sentinel:
                    return value

        if isinstance(state, Mapping):
            for candidate in candidates:
                if candidate in state:
                    return state[candidate]

        for attribute_name in (
            "values",
            "data",
            "_values",
        ):
            mapping = getattr(
                state,
                attribute_name,
                None,
            )

            if isinstance(mapping, Mapping):
                for candidate in candidates:
                    if candidate in mapping:
                        return mapping[candidate]

        get_method = getattr(
            state,
            "get",
            None,
        )

        if callable(get_method):
            for candidate in candidates:
                value = get_method(
                    candidate,
                    sentinel,
                )

                if value is not sentinel:
                    return value

        for candidate in candidates:
            try:
                return state[candidate]
            except (
                KeyError,
                LookupError,
                TypeError,
                AttributeError,
            ):
                continue

        raise RuntimeExpressionError(
            f"undefined state identifier {name!r}"
        )

    def _require_number(
        self,
        value: Any,
        operator: str,
    ) -> Any:
        if isinstance(value, bool) or not isinstance(
            value,
            (int, float),
        ):
            raise RuntimeExpressionError(
                f"operator {operator!r} requires numeric "
                f"operands; received {type(value).__name__}"
            )

        return value

    def _require_boolean(
        self,
        value: Any,
        operator: str,
    ) -> bool:
        if not isinstance(value, bool):
            raise RuntimeExpressionError(
                f"operator {operator!r} requires boolean "
                f"operands; received {type(value).__name__}"
            )

        return value