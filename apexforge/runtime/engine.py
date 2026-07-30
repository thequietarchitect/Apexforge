"""AIR runtime execution engine with expression evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping, Optional, Sequence, Tuple

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
    AIRCallExpression,
)

from causality.engine import CausalEngine

from runtime.context import ExecutionContext
from runtime.diagnostics import (
    Diagnostic,
    Trace,
    TraceStep,
    append_diagnostic,
)
from runtime.call_stack import CallFrame, CallStack
from runtime.state import StateDelta, StateSnapshot


MAX_CONDITIONAL_DEPTH = 64
MAX_INVOCATION_DEPTH = 32
MAX_FUNCTION_CALL_DEPTH = 64


class RuntimeExpressionError(RuntimeError):
    """Raised when an AIR expression cannot be evaluated safely."""

    def __init__(
        self,
        message: str,
        *,
        trace_steps: Tuple[TraceStep, ...] = (),
    ) -> None:
        self.trace_steps = tuple(trace_steps)
        super().__init__(message)


@dataclass(frozen=True)
class ExecutionResult:
    delta: StateDelta
    trace: Trace
    diagnostics: Tuple[Diagnostic, ...]
    final_state: StateSnapshot

    @property
    def ok(self) -> bool:
        return not any(d.is_error for d in self.diagnostics)


@dataclass(frozen=True)
class _ActionExecution:
    ok: bool
    state: StateSnapshot
    assignments: Tuple[Any, ...]
    events: Tuple[EventRecord, ...]
    effects: Tuple[Any, ...]
    trace_steps: Tuple[TraceStep, ...]
    next_event_index: int


@dataclass(frozen=True)
class _DirectiveExecution:
    ok: bool
    state: StateSnapshot
    assignments: Tuple[Any, ...]
    events: Tuple[EventRecord, ...]
    effects: Tuple[Any, ...]
    trace_steps: Tuple[TraceStep, ...]
    next_event_index: int


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
        entry_directives: Optional[Sequence[str]] = None,
    ) -> ExecutionResult:
        """Execute verified AIR.

        ``entry_directives`` selects explicit root directives for a linked,
        multi-directive program. ``None`` preserves AFP-P1/AFP-P2 behavior by
        executing every directive in program order.
        """

        if not isinstance(verified, VerifiedAIRProgram):
            raise TypeError(
                "RuntimeEngine.execute requires VerifiedAIRProgram"
            )

        program = verified.program

        diagnostics: list[Diagnostic] = []
        trace_steps: list[TraceStep] = []
        assignments: list[Any] = []
        events: list[EventRecord] = []
        effects: list[Any] = []

        checks = index_by_id(program.authority_checks)
        decisions = index_by_id(program.causal_decisions)
        directives = index_by_id(program.directives)
        functions = index_by_id(
            tuple(getattr(program, "functions", ()) or ())
        )

        roots = self._resolve_entry_directives(
            entry_directives=entry_directives,
            directives=directives,
            program_directives=tuple(program.directives),
        )

        working_state = context.state
        next_event_index = 0

        trace_steps.append(
            TraceStep(
                "runtime.start",
                "started AIR execution",
                facts(
                    version=program.version,
                    roots=len(roots),
                ),
            )
        )

        for directive in roots:
            outcome = self._execute_directive(
                directive=directive,
                state=working_state,
                checks=checks,
                decisions=decisions,
                directives=directives,
                functions=functions,
                context=context,
                diagnostics=diagnostics,
                invocation_stack=(),
                event_index=next_event_index,
            )

            trace_steps.extend(outcome.trace_steps)

            if not outcome.ok:
                continue

            working_state = outcome.state
            next_event_index = outcome.next_event_index
            assignments.extend(outcome.assignments)
            events.extend(outcome.events)
            effects.extend(outcome.effects)

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
            diagnostics=tuple(sorted(diagnostics)),
            final_state=working_state,
        )

    def _resolve_entry_directives(
        self,
        entry_directives: Optional[Sequence[str]],
        directives: Mapping[str, Any],
        program_directives: Tuple[Any, ...],
    ) -> Tuple[Any, ...]:
        if entry_directives is None:
            return program_directives

        if isinstance(entry_directives, str):
            references = (entry_directives,)
        else:
            references = tuple(entry_directives)

        resolved = []
        seen: set[str] = set()

        for reference in references:
            directive = self._resolve_directive_reference(
                reference,
                directives,
            )

            if directive.id in seen:
                raise ValueError(
                    "duplicate entry directive: "
                    f"{directive.id}"
                )

            seen.add(directive.id)
            resolved.append(directive)

        return tuple(resolved)

    def _resolve_directive_reference(
        self,
        reference: str,
        directives: Mapping[str, Any],
    ) -> Any:
        if not isinstance(reference, str) or not reference:
            raise RuntimeExpressionError(
                "directive reference must be a non-empty string"
            )

        if reference in directives:
            return directives[reference]

        canonical = (
            reference
            if reference.startswith("directive:")
            else f"directive:{reference}"
        )

        if canonical in directives:
            return directives[canonical]

        raise RuntimeExpressionError(
            f"undefined directive invocation target {reference!r}"
        )

    def _execute_directive(
        self,
        directive: Any,
        state: StateSnapshot,
        checks: Mapping[str, Any],
        decisions: Mapping[str, Any],
        directives: Mapping[str, Any],
        functions: Mapping[str, Any],
        context: ExecutionContext,
        diagnostics: list[Diagnostic],
        invocation_stack: Tuple[str, ...],
        event_index: int,
    ) -> _DirectiveExecution:
        start_event_index = event_index
        trace_steps: list[TraceStep] = []

        if directive.id in invocation_stack:
            cycle = invocation_stack + (directive.id,)
            rendered_cycle = " -> ".join(cycle)

            append_diagnostic(
                diagnostics,
                "error",
                "RUN003",
                f"directive invocation cycle detected: {rendered_cycle}",
                directive.id,
            )

            trace_steps.append(
                TraceStep(
                    "directive.invoke.cycle",
                    "rejected cyclic directive invocation",
                    facts(
                        directive=directive.id,
                        cycle=rendered_cycle,
                    ),
                )
            )

            return _DirectiveExecution(
                ok=False,
                state=state,
                assignments=(),
                events=(),
                effects=(),
                trace_steps=tuple(trace_steps),
                next_event_index=start_event_index,
            )

        if len(invocation_stack) >= MAX_INVOCATION_DEPTH:
            append_diagnostic(
                diagnostics,
                "error",
                "RUN004",
                (
                    "directive invocation depth exceeds runtime limit "
                    f"of {MAX_INVOCATION_DEPTH}"
                ),
                directive.id,
            )

            trace_steps.append(
                TraceStep(
                    "directive.invoke.depth",
                    "rejected over-depth directive invocation",
                    facts(
                        directive=directive.id,
                        depth=len(invocation_stack),
                    ),
                )
            )

            return _DirectiveExecution(
                ok=False,
                state=state,
                assignments=(),
                events=(),
                effects=(),
                trace_steps=tuple(trace_steps),
                next_event_index=start_event_index,
            )

        active_stack = invocation_stack + (directive.id,)

        trace_steps.append(
            TraceStep(
                "directive.start",
                "entered directive",
                facts(
                    directive=directive.id,
                    name=directive.name,
                    principal=directive.principal,
                    depth=len(invocation_stack),
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
                        f"authority denied: {check.principal} lacks "
                        f"{check.capability} on {check.resource}"
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

            return _DirectiveExecution(
                ok=False,
                state=state,
                assignments=(),
                events=(),
                effects=(),
                trace_steps=tuple(trace_steps),
                next_event_index=start_event_index,
            )

        candidate_state = state
        evaluated_assignments: list[Any] = []
        evaluated_events: list[EventRecord] = []
        evaluated_effects: list[Any] = []
        next_event_index = event_index

        for decision_id in directive.causal_decisions:
            decision = decisions[decision_id]
            selection = self._causality.select_path(decision)
            selected = selection.path
            trace_steps.extend(selection.trace_steps)

            ordered_actions = tuple(
                getattr(selected, "actions", ()) or ()
            )

            if not ordered_actions:
                ordered_actions = (
                    tuple(getattr(selected, "assignments", ()) or ())
                    + tuple(getattr(selected, "emits", ()) or ())
                    + tuple(getattr(selected, "invocations", ()) or ())
                )

            try:
                action_result = self._execute_ordered_actions(
                    actions=ordered_actions,
                    state=candidate_state,
                    directive=directive,
                    decision=decision,
                    path=selected,
                    checks=checks,
                    decisions=decisions,
                    directives=directives,
                    functions=functions,
                    context=context,
                    diagnostics=diagnostics,
                    invocation_stack=active_stack,
                    event_index=next_event_index,
                    depth=0,
                )
            except RuntimeExpressionError as exc:
                trace_steps.extend(
                    tuple(getattr(exc, "trace_steps", ()) or ())
                )
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

                return _DirectiveExecution(
                    ok=False,
                    state=state,
                    assignments=(),
                    events=(),
                    effects=(),
                    trace_steps=tuple(trace_steps),
                    next_event_index=start_event_index,
                )

            trace_steps.extend(action_result.trace_steps)

            if not action_result.ok:
                return _DirectiveExecution(
                    ok=False,
                    state=state,
                    assignments=(),
                    events=(),
                    effects=(),
                    trace_steps=tuple(trace_steps),
                    next_event_index=start_event_index,
                )

            candidate_state = action_result.state
            next_event_index = action_result.next_event_index
            evaluated_assignments.extend(action_result.assignments)
            evaluated_events.extend(action_result.events)
            evaluated_effects.extend(action_result.effects)

            evaluated_effects.extend(selected.effects)

            for effect in selected.effects:
                trace_steps.append(
                    TraceStep(
                        "effect.intent",
                        "queued host effect intent without executing it",
                        facts(
                            effect=effect.id,
                            effect_type=effect.effect_type,
                        ),
                    )
                )

        trace_steps.append(
            TraceStep(
                "directive.finish",
                "finished directive",
                facts(
                    directive=directive.id,
                    depth=len(invocation_stack),
                ),
            )
        )

        return _DirectiveExecution(
            ok=True,
            state=candidate_state,
            assignments=tuple(evaluated_assignments),
            events=tuple(evaluated_events),
            effects=tuple(evaluated_effects),
            trace_steps=tuple(trace_steps),
            next_event_index=next_event_index,
        )

    def _execute_ordered_actions(
        self,
        actions: Tuple[Any, ...],
        state: StateSnapshot,
        directive: Any,
        decision: Any,
        path: Any,
        checks: Mapping[str, Any],
        decisions: Mapping[str, Any],
        directives: Mapping[str, Any],
        functions: Mapping[str, Any],
        context: ExecutionContext,
        diagnostics: list[Diagnostic],
        invocation_stack: Tuple[str, ...],
        event_index: int = 0,
        depth: int = 0,
    ) -> _ActionExecution:
        """Execute one ordered action stream transactionally."""

        if depth > MAX_CONDITIONAL_DEPTH:
            raise RuntimeExpressionError(
                "conditional nesting exceeds runtime limit of "
                f"{MAX_CONDITIONAL_DEPTH}"
            )

        start_event_index = event_index
        candidate_state = state
        evaluated_assignments: list[Any] = []
        evaluated_events: list[EventRecord] = []
        evaluated_effects: list[Any] = []
        action_trace_steps: list[TraceStep] = []
        next_event_index = event_index

        for action_index, action in enumerate(actions):
            action_type = type(action).__name__

            if action_type == "StateAssignment":
                evaluated = self._evaluate_assignment(
                    action,
                    candidate_state,
                    functions=functions,
                    trace_steps=action_trace_steps,
                )

                candidate_state = candidate_state.apply(
                    StateDelta((evaluated,))
                )

                evaluated_assignments.append(evaluated)
                action_trace_steps.append(
                    TraceStep(
                        "state.delta",
                        "applied ordered state assignment",
                        facts(
                            assignments=1,
                            path=path.id,
                            state=evaluated.state,
                            operation=evaluated.operation,
                            value=evaluated.value,
                        ),
                    )
                )
                continue

            if action_type == "EventEmission":
                evaluated_facts = self._evaluate_facts(
                    action.facts,
                    candidate_state,
                    functions=functions,
                    trace_steps=action_trace_steps,
                )

                event = EventRecord(
                    id=event_record_id(
                        directive.id,
                        decision.id,
                        path.id,
                        next_event_index,
                        action.event,
                    ),
                    event=action.event,
                    directive=directive.id,
                    principal=directive.principal,
                    facts=evaluated_facts,
                )

                next_event_index += 1
                evaluated_events.append(event)
                action_trace_steps.append(
                    TraceStep(
                        "event.emit",
                        "queued ordered event emission",
                        facts(
                            event=event.event,
                            event_id=event.id,
                        ),
                    )
                )
                continue

            if action_type == "DirectiveInvocation":
                target_reference = getattr(action, "target", None)

                if target_reference is None:
                    target_reference = getattr(
                        action,
                        "directive",
                        None,
                    )

                target = self._resolve_directive_reference(
                    target_reference,
                    directives,
                )

                action_trace_steps.append(
                    TraceStep(
                        "directive.invoke.start",
                        "started directive invocation",
                        facts(
                            caller=directive.id,
                            target=target.id,
                            path=path.id,
                            action=action_index,
                        ),
                    )
                )

                invoked = self._execute_directive(
                    directive=target,
                    state=candidate_state,
                    checks=checks,
                    decisions=decisions,
                    directives=directives,
                    functions=functions,
                    context=context,
                    diagnostics=diagnostics,
                    invocation_stack=invocation_stack,
                    event_index=next_event_index,
                )

                action_trace_steps.extend(invoked.trace_steps)

                if not invoked.ok:
                    action_trace_steps.append(
                        TraceStep(
                            "directive.invoke.abort",
                            "aborted directive invocation transaction",
                            facts(
                                caller=directive.id,
                                target=target.id,
                                path=path.id,
                            ),
                        )
                    )

                    return _ActionExecution(
                        ok=False,
                        state=state,
                        assignments=(),
                        events=(),
                        effects=(),
                        trace_steps=tuple(action_trace_steps),
                        next_event_index=start_event_index,
                    )

                candidate_state = invoked.state
                next_event_index = invoked.next_event_index
                evaluated_assignments.extend(invoked.assignments)
                evaluated_events.extend(invoked.events)
                evaluated_effects.extend(invoked.effects)

                action_trace_steps.append(
                    TraceStep(
                        "directive.invoke.finish",
                        "finished directive invocation",
                        facts(
                            caller=directive.id,
                            target=target.id,
                            path=path.id,
                        ),
                    )
                )
                continue

            if action_type == "AIRWhenAction":
                condition_result = self._evaluate_expression(
                    action.condition,
                    candidate_state,
                    functions=functions,
                    frame=None,
                    call_stack=CallStack(),
                    trace_steps=action_trace_steps,
                )

                if type(condition_result) is not bool:
                    raise RuntimeExpressionError(
                        "AIRWhenAction condition must evaluate to bool; "
                        f"received {type(condition_result).__name__}."
                    )

                if condition_result:
                    branch_name = "when"
                    branch_actions = tuple(
                        getattr(action, "actions", ()) or ()
                    )
                else:
                    branch_name = "otherwise"
                    branch_actions = tuple(
                        getattr(action, "otherwise_actions", ()) or ()
                    )

                action_trace_steps.append(
                    TraceStep(
                        "when.evaluate",
                        "evaluated conditional action",
                        facts(
                            branch=branch_name,
                            depth=depth,
                            result=condition_result,
                        ),
                    )
                )

                nested = self._execute_ordered_actions(
                    actions=branch_actions,
                    state=candidate_state,
                    directive=directive,
                    decision=decision,
                    path=path,
                    checks=checks,
                    decisions=decisions,
                    directives=directives,
                    functions=functions,
                    context=context,
                    diagnostics=diagnostics,
                    invocation_stack=invocation_stack,
                    event_index=next_event_index,
                    depth=depth + 1,
                )

                action_trace_steps.extend(nested.trace_steps)

                if not nested.ok:
                    return _ActionExecution(
                        ok=False,
                        state=state,
                        assignments=(),
                        events=(),
                        effects=(),
                        trace_steps=tuple(action_trace_steps),
                        next_event_index=start_event_index,
                    )

                candidate_state = nested.state
                next_event_index = nested.next_event_index
                evaluated_assignments.extend(nested.assignments)
                evaluated_events.extend(nested.events)
                evaluated_effects.extend(nested.effects)
                continue

            raise RuntimeExpressionError(
                "unsupported ordered AIR action type "
                f"{action_type!r}"
            )

        return _ActionExecution(
            ok=True,
            state=candidate_state,
            assignments=tuple(evaluated_assignments),
            events=tuple(evaluated_events),
            effects=tuple(evaluated_effects),
            trace_steps=tuple(action_trace_steps),
            next_event_index=next_event_index,
        )

    def _evaluate_assignment(
        self,
        assignment: Any,
        state: StateSnapshot,
        *,
        functions: Mapping[str, Any],
        trace_steps: list[TraceStep],
    ) -> Any:
        value = self._evaluate_expression(
            assignment.value,
            state,
            functions=functions,
            frame=None,
            call_stack=CallStack(),
            trace_steps=trace_steps,
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
                    f"{type(value).__name__}, not int",
                    trace_steps=tuple(trace_steps),
                )

        return replace(
            assignment,
            value=value,
        )

    def _evaluate_facts(
        self,
        fact_values: Tuple[Any, ...],
        state: StateSnapshot,
        *,
        functions: Mapping[str, Any],
        trace_steps: list[TraceStep],
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
                functions=functions,
                frame=None,
                call_stack=CallStack(),
                trace_steps=trace_steps,
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
        *,
        functions: Optional[Mapping[str, Any]] = None,
        frame: Optional[CallFrame] = None,
        call_stack: Optional[CallStack] = None,
        trace_steps: Optional[list[TraceStep]] = None,
    ) -> Any:
        """
        Evaluate AIR expressions recursively.

        Primitive AFP-P1 values pass through unchanged. P7 calls execute only
        against linked, verified AIRFunction declarations and immutable frames.
        """

        function_index = functions or {}
        active_stack = call_stack or CallStack()
        active_trace = trace_steps if trace_steps is not None else []

        def evaluate(nested: Any) -> Any:
            return self._evaluate_expression(
                nested,
                state,
                functions=function_index,
                frame=frame,
                call_stack=active_stack,
                trace_steps=active_trace,
            )

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
            if frame is not None:
                found, value = frame.try_resolve(
                    expression.name
                )

                if found:
                    return value

                raise RuntimeExpressionError(
                    "undefined function-local identifier "
                    f"{expression.name!r} in {frame.function_id!r}",
                    trace_steps=tuple(active_trace),
                )

            return self._resolve_identifier(
                expression.name,
                state,
            )

        if isinstance(
            expression,
            AIRCallExpression,
        ):
            return self._evaluate_function_call(
                expression=expression,
                state=state,
                functions=function_index,
                caller_frame=frame,
                call_stack=active_stack,
                trace_steps=active_trace,
            )

        if isinstance(
            expression,
            AIRUnaryExpression,
        ):
            operand = evaluate(
                expression.operand
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
                f"{operator!r}",
                trace_steps=tuple(active_trace),
            )

        if isinstance(
            expression,
            AIRBinaryExpression,
        ):
            operator = expression.operator

            # Preserve short-circuit behavior.
            if operator == "and":
                left = self._require_boolean(
                    evaluate(
                        expression.left
                    ),
                    operator,
                )

                if not left:
                    return False

                return self._require_boolean(
                    evaluate(
                        expression.right
                    ),
                    operator,
                )

            if operator == "or":
                left = self._require_boolean(
                    evaluate(
                        expression.left
                    ),
                    operator,
                )

                if left:
                    return True

                return self._require_boolean(
                    evaluate(
                        expression.right
                    ),
                    operator,
                )

            left = evaluate(
                expression.left
            )

            right = evaluate(
                expression.right
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
                        "division by zero",
                        trace_steps=tuple(active_trace),
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
                        "modulo by zero",
                        trace_steps=tuple(active_trace),
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
                f"{operator!r}",
                trace_steps=tuple(active_trace),
            )

        raise RuntimeExpressionError(
            "unsupported AIR expression type "
            f"{type(expression).__name__}",
            trace_steps=tuple(active_trace),
        )

    def _evaluate_function_call(
        self,
        *,
        expression: AIRCallExpression,
        state: StateSnapshot,
        functions: Mapping[str, Any],
        caller_frame: Optional[CallFrame],
        call_stack: CallStack,
        trace_steps: list[TraceStep],
    ) -> Any:
        function = self._resolve_function_reference(
            expression.target,
            functions,
        )

        arguments: list[Any] = []

        # Argument evaluation order is semantic and deterministic.
        for argument in tuple(
            getattr(expression, "arguments", ()) or ()
        ):
            arguments.append(
                self._evaluate_expression(
                    argument,
                    state,
                    functions=functions,
                    frame=caller_frame,
                    call_stack=call_stack,
                    trace_steps=trace_steps,
                )
            )

        parameters = tuple(
            getattr(function, "parameters", ()) or ()
        )

        if len(arguments) != len(parameters):
            raise RuntimeExpressionError(
                f"function '{function.id}' expects {len(parameters)} "
                f"argument(s), received {len(arguments)}",
                trace_steps=tuple(trace_steps),
            )

        if call_stack.contains(
            function.id
        ):
            cycle = (
                tuple(frame.function_id for frame in call_stack.frames)
                + (function.id,)
            )
            raise RuntimeExpressionError(
                "function recursion detected at runtime: "
                + " -> ".join(cycle),
                trace_steps=tuple(trace_steps),
            )

        if call_stack.depth >= MAX_FUNCTION_CALL_DEPTH:
            raise RuntimeExpressionError(
                "function call depth exceeds runtime limit "
                f"of {MAX_FUNCTION_CALL_DEPTH}",
                trace_steps=tuple(trace_steps),
            )

        frame = CallFrame.bind(
            function=function,
            values=tuple(arguments),
            depth=call_stack.depth,
        )
        nested_stack = call_stack.push(
            frame
        )

        trace_steps.append(
            TraceStep(
                "function.call.start",
                "entered pure function call frame",
                facts(
                    arguments=len(arguments),
                    depth=frame.depth,
                    function=function.id,
                    name=function.name,
                ),
            )
        )

        try:
            value = self._evaluate_expression(
                function.return_expression,
                state,
                functions=functions,
                frame=frame,
                call_stack=nested_stack,
                trace_steps=trace_steps,
            )
        except RuntimeExpressionError as exc:
            trace_steps.append(
                TraceStep(
                    "function.call.abort",
                    "aborted pure function evaluation",
                    facts(
                        depth=frame.depth,
                        function=function.id,
                        name=function.name,
                    ),
                )
            )
            raise RuntimeExpressionError(
                str(exc),
                trace_steps=tuple(trace_steps),
            ) from exc

        trace_steps.append(
            TraceStep(
                "function.call.finish",
                "returned from pure function call frame",
                facts(
                    depth=frame.depth,
                    function=function.id,
                    name=function.name,
                    result_type=type(value).__name__,
                ),
            )
        )

        return value

    def _resolve_function_reference(
        self,
        reference: str,
        functions: Mapping[str, Any],
    ) -> Any:
        if not isinstance(reference, str) or not reference:
            raise RuntimeExpressionError(
                "function reference must be a non-empty string"
            )

        if reference in functions:
            return functions[reference]

        canonical = (
            reference
            if reference.startswith("function:")
            else f"function:{reference}"
        )

        if canonical in functions:
            return functions[canonical]

        raise RuntimeExpressionError(
            f"undefined function call target {reference!r}"
        )

    def _resolve_identifier(
        self,
        name: str,
        state: StateSnapshot,
    ) -> Any:
        """Resolve a plain state name or canonical ``state:<name>`` ID."""

        candidates = (
            name,
            name if name.startswith("state:")
            else f"state:{name}",
        )

        # Canonical StateSnapshot exposes immutable cells. Inspecting them
        # directly preserves reliable missing-state detection without passing
        # a non-integer sentinel into StateSnapshot.get_int.
        cells = getattr(
            state,
            "cells",
            None,
        )

        if cells is not None:
            for candidate in candidates:
                for cell in cells:
                    if getattr(
                        cell,
                        "key",
                        None,
                    ) == candidate:
                        return getattr(
                            cell,
                            "value",
                        )

            raise RuntimeExpressionError(
                f"undefined state identifier {name!r}"
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

        # Compatibility fallback for snapshot-like objects that expose only
        # get_int. Canonical StateSnapshot was handled above.
        get_int = getattr(
            state,
            "get_int",
            None,
        )

        if callable(get_int):
            return get_int(
                name,
                0,
            )

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