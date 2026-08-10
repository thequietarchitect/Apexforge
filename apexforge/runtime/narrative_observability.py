"""Deterministic P11.6E narrative transition observability and termination.

This module is the narrative execution boundary for P11.6E.  It delegates
choice-path resolution, predicate evaluation, consequence application, and
state construction to P11.6D, then packages the observed outcome in the
immutable P11.6B result contracts.

It does not select a choice, resolve an initial scene, inspect graph shape, or
reuse AIR execution, diagnostic, or tracing types.
"""

from __future__ import annotations

from typing import Literal, Optional

from language.narrative_model import NarrativeIdentity
from runtime.narrative_binding import NarrativeExecutableBindingSet
from runtime.narrative_execution import (
    NarrativeChoiceEvidence,
    NarrativeExecutionDiagnostic,
    NarrativeExecutionResult,
    NarrativeExecutionState,
    NarrativeExecutionTraceEvent,
    NarrativeExecutionTraceFact,
    NarrativeTermination,
)
from runtime.narrative_transition import (
    NarrativeTransitionError,
    transition_narrative_choice,
)

__all__ = (
    "NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME",
    "execute_narrative_choice",
    "terminate_narrative",
)


NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME = "explicit_outcome"
_TERMINATION_REASONS = frozenset(
    (NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME,)
)

_FAILURE_DIAGNOSTIC_CODES = {
    "story_mismatch": "NARRATIVE_TRANSITION_STORY_MISMATCH",
    "choice_not_found": "NARRATIVE_TRANSITION_CHOICE_NOT_FOUND",
    "choice_not_current_scene": "NARRATIVE_TRANSITION_CHOICE_NOT_CURRENT_SCENE",
    "path_not_found": "NARRATIVE_TRANSITION_PATH_NOT_FOUND",
    "ambiguous_path": "NARRATIVE_TRANSITION_AMBIGUOUS_PATH",
    "condition_unsatisfied": "NARRATIVE_TRANSITION_CONDITION_UNSATISFIED",
}


def _require_identity(
    value: object,
    field_name: str,
    expected_kind: Optional[str] = None,
) -> NarrativeIdentity:
    if type(value) is not NarrativeIdentity:
        raise TypeError(f"{field_name} must be an exact NarrativeIdentity.")
    if expected_kind is not None and value.kind != expected_kind:
        raise ValueError(
            f"{field_name} must have narrative identity kind "
            f"{expected_kind!r}; received {value.kind!r}."
        )
    return value


def _identity_text(identity: NarrativeIdentity) -> str:
    return f"{identity.kind}:{'/'.join(identity.path)}"


def _require_execution_inputs(
    state: object,
    bindings: object,
    choice: object,
    path_index: object,
) -> tuple[
    NarrativeExecutionState,
    NarrativeExecutableBindingSet,
    NarrativeIdentity,
    int,
]:
    if type(state) is not NarrativeExecutionState:
        raise TypeError("state must be an exact NarrativeExecutionState.")
    if type(bindings) is not NarrativeExecutableBindingSet:
        raise TypeError(
            "bindings must be an exact NarrativeExecutableBindingSet."
        )
    selected_choice = _require_identity(choice, "choice", "choice")
    if type(path_index) is not int:
        raise TypeError("path_index must be an exact int.")
    if path_index < 0:
        raise ValueError("path_index must be non-negative.")
    return state, bindings, selected_choice, path_index


def _transition_trace(
    *,
    state: NarrativeExecutionState,
    choice: NarrativeIdentity,
    path_index: int,
    outcome: str,
    destination: Optional[NarrativeIdentity] = None,
    failure_kind: Optional[str] = None,
) -> NarrativeExecutionTraceEvent:
    facts = [
        NarrativeExecutionTraceFact(
            "source_scene",
            _identity_text(state.current_scene),
        ),
        NarrativeExecutionTraceFact("selected_choice", _identity_text(choice)),
        NarrativeExecutionTraceFact("selected_path_index", str(path_index)),
    ]
    if destination is not None:
        facts.append(
            NarrativeExecutionTraceFact(
                "destination_scene",
                _identity_text(destination),
            )
        )
    if failure_kind is not None:
        facts.append(NarrativeExecutionTraceFact("failure_kind", failure_kind))
    facts.append(NarrativeExecutionTraceFact("outcome", outcome))
    return NarrativeExecutionTraceEvent(
        kind="narrative_transition",
        message=(
            "explicit narrative choice transition succeeded"
            if outcome == "success"
            else "explicit narrative choice transition failed"
        ),
        facts=tuple(facts),
    )


def _failure_diagnostic(
    error: NarrativeTransitionError,
) -> NarrativeExecutionDiagnostic:
    code = _FAILURE_DIAGNOSTIC_CODES[error.failure_kind]
    return NarrativeExecutionDiagnostic(
        severity="error",
        code=code,
        message=f"narrative transition failed: {error.failure_kind}",
        subject=error.choice,
    )


def _terminated_result(
    state: NarrativeExecutionState,
    choice: NarrativeIdentity,
    path_index: int,
) -> NarrativeExecutionResult:
    diagnostic = NarrativeExecutionDiagnostic(
        severity="error",
        code="NARRATIVE_EXECUTION_TERMINATED",
        message="narrative transition rejected: execution is terminated",
        subject=choice,
    )
    trace = _transition_trace(
        state=state,
        choice=choice,
        path_index=path_index,
        outcome="failure",
        failure_kind="terminated",
    )
    return NarrativeExecutionResult(
        initial_state=state,
        final_state=state,
        trace=(trace,),
        diagnostics=(diagnostic,),
    )


def execute_narrative_choice(
    state: NarrativeExecutionState,
    bindings: NarrativeExecutableBindingSet,
    choice: NarrativeIdentity,
    path_index: int,
) -> NarrativeExecutionResult:
    """Execute one explicit choice path and return immutable observations.

    P11.6D remains the sole authority for resolving the path and changing the
    state.  Its deterministic transition failures become one narrative
    diagnostic and one narrative trace record; the input state is retained as
    the result's final state in every failure case.
    """

    state, bindings, choice, path_index = _require_execution_inputs(
        state,
        bindings,
        choice,
        path_index,
    )
    if state.termination.is_terminated:
        return _terminated_result(state, choice, path_index)

    try:
        next_state = transition_narrative_choice(
            state,
            bindings,
            choice,
            path_index,
        )
    except NarrativeTransitionError as error:
        trace = _transition_trace(
            state=state,
            choice=choice,
            path_index=path_index,
            outcome="failure",
            failure_kind=error.failure_kind,
        )
        return NarrativeExecutionResult(
            initial_state=state,
            final_state=state,
            trace=(trace,),
            diagnostics=(_failure_diagnostic(error),),
        )

    evidence: NarrativeChoiceEvidence = next_state.choice_history[-1]
    trace = _transition_trace(
        state=state,
        choice=choice,
        path_index=path_index,
        outcome="success",
        destination=next_state.current_scene,
    )
    return NarrativeExecutionResult(
        initial_state=state,
        final_state=next_state,
        trace=(trace,),
        choice_evidence=(evidence,),
    )


def terminate_narrative(
    state: NarrativeExecutionState,
    reason: Literal["explicit_outcome"] =
    NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME,
) -> NarrativeExecutionState:
    """Create an explicit terminal state without inspecting story graph shape."""

    if type(state) is not NarrativeExecutionState:
        raise TypeError("state must be an exact NarrativeExecutionState.")
    if type(reason) is not str or reason not in _TERMINATION_REASONS:
        raise ValueError(
            "reason must be 'explicit_outcome'; termination is caller-driven."
        )
    if state.termination.is_terminated:
        raise ValueError("narrative execution state is already terminated.")
    return NarrativeExecutionState(
        story=state.story,
        current_scene=state.current_scene,
        facts=state.facts,
        progression=state.progression,
        choice_history=state.choice_history,
        termination=NarrativeTermination(
            status="terminated",
            reason=reason,
        ),
    )
