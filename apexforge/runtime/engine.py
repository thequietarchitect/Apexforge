"""AIR runtime execution engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from air.ids import event_record_id
from air.model import EventRecord, VerifiedAIRProgram, facts
from air.indexes import index_by_id

from causality.engine import CausalEngine

from runtime.context import ExecutionContext
from runtime.diagnostics import (
    Diagnostic,
    Trace,
    TraceStep,
    append_diagnostic,
)
from runtime.state import StateDelta, StateSnapshot


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

                path_delta = StateDelta(
                    selected.assignments
                )

                working_state = working_state.apply(
                    path_delta
                )

                assignments.extend(
                    selected.assignments
                )

                trace_steps.append(
                TraceStep(
                    "state.delta",
                    "queued selected path assignments",
                        facts(
                            assignments=len(selected.assignments),
                            path=selected.id,
                            state=selected.assignments[0].state if selected.assignments else "",
                            operation=selected.assignments[0].operation if selected.assignments else "",
                            value=selected.assignments[0].value if selected.assignments else 0,
                    )
                )
            )
                
                for index, emission in enumerate(
                    selected.emits
                ):

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
                        facts=emission.facts,
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
