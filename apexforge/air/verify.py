"""AIR verifier.

The runtime must consume VerifiedAIRProgram only. Verification is where missing
references, unsupported operations, version mismatches, and duplicate IDs are
rejected before execution.
"""

from __future__ import annotations

from typing import Iterable

from air.indexes import HasId, index_by_id
from air.model import (
    AIRProgram,
    VerificationResult,
    validate_assignment_shape,
    validate_state_definition_shape,
)
from air.types import AIR_VERSION, is_int
from runtime.diagnostics import Diagnostic, append_diagnostic


class AIRVerifier:
    def verify(self, program: AIRProgram) -> VerificationResult:
        diagnostics: list[Diagnostic] = []

        if program.version != AIR_VERSION:
            append_diagnostic(
                diagnostics,
                "error",
                "AIR001",
                f"unsupported AIR version: {program.version}",
            )

        self._check_unique("principal", program.principals, diagnostics)
        self._check_unique("state", program.states, diagnostics)
        self._check_unique("event", program.events, diagnostics)
        self._check_unique("authority_check", program.authority_checks, diagnostics)
        self._check_unique("causal_decision", program.causal_decisions, diagnostics)
        self._check_unique("directive", program.directives, diagnostics)

        principals = index_by_id(program.principals)
        states = index_by_id(program.states)
        events = index_by_id(program.events)
        checks = index_by_id(program.authority_checks)
        decisions = index_by_id(program.causal_decisions)

        for state in program.states:
            if not validate_state_definition_shape(state):
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR010",
                    "state must be an int state with an int initial value",
                    state.id,
                )

        for check in program.authority_checks:
            if check.principal not in principals:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR020",
                    f"authority principal does not exist: {check.principal}",
                    check.id,
                )

        for decision in program.causal_decisions:
            if decision.policy != "max_weight":
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR030",
                    f"unsupported causal policy: {decision.policy}",
                    decision.id,
                )

            if not decision.paths:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR031",
                    "causal decision must have at least one path",
                    decision.id,
                )

            self._check_unique(f"path in {decision.id}", decision.paths, diagnostics)

            for path in decision.paths:
                if not is_int(path.weight):
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR032",
                        "causal path weight must be an int",
                        path.id,
                    )

                for assignment in path.assignments:
                    if assignment.state not in states:
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR033",
                            f"assignment state does not exist: {assignment.state}",
                            path.id,
                        )

                    if not validate_assignment_shape(assignment):
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR034",
                            "assignment operation/value shape is invalid",
                            path.id,
                        )

                for emission in path.emits:
                    if emission.event not in events:
                        append_diagnostic(
                            diagnostics,
                            "error",
                            "AIR036",
                            f"event does not exist: {emission.event}",
                            path.id,
                        )

        for directive in program.directives:
            if directive.principal not in principals:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR040",
                    f"directive principal does not exist: {directive.principal}",
                    directive.id,
                )

            if not is_int(directive.order):
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR041",
                    "directive order must be an int",
                    directive.id,
                )

            for check_id in directive.authority_checks:
                if check_id not in checks:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR042",
                        f"authority check does not exist: {check_id}",
                        directive.id,
                    )
                    continue

                check = checks[check_id]
                if check.principal != directive.principal:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR043",
                        "authority check principal must match directive principal",
                        directive.id,
                    )

            for decision_id in directive.causal_decisions:
                if decision_id not in decisions:
                    append_diagnostic(
                        diagnostics,
                        "error",
                        "AIR044",
                        f"causal decision does not exist: {decision_id}",
                        directive.id,
                    )

        return VerificationResult(program, tuple(sorted(diagnostics)))

    @staticmethod
    def _check_unique(
        label: str,
        items: Iterable[HasId],
        diagnostics: list[Diagnostic],
    ) -> None:
        seen: set[str] = set()

        for item in items:
            if item.id in seen:
                append_diagnostic(
                    diagnostics,
                    "error",
                    "AIR000",
                    f"duplicate {label} id: {item.id}",
                    item.id,
                )

            seen.add(item.id)
