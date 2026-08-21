"""Read-only adapters from existing owner evidence into TAP ledger entries."""

from __future__ import annotations

from runtime.engine import ExecutionResult
from runtime.narrative_execution import NarrativeExecutionResult
from semantic_decision.resolution import SemanticConvergenceResolution
from type_system.lowering import GenericLoweringResult
from workflow.directive_engine import DirectiveExecutionResult

from .model import TapCheckLedgerEntry


def _identity_text(identity: object) -> str:
    kind = getattr(identity, "kind")
    path = getattr(identity, "path")
    return "{}:{}".format(kind, "/".join(path))


def adapt_runtime_result(result: ExecutionResult) -> TapCheckLedgerEntry:
    """Observe one already-produced core runtime execution result."""

    if type(result) is not ExecutionResult:
        raise TypeError("adapt_runtime_result requires an exact ExecutionResult")

    return TapCheckLedgerEntry(
        category_id="runtime-results",
        subject="runtime.engine.ExecutionResult",
        evidence=(
            "assignment_count={}".format(len(result.delta.assignments)),
            "event_count={}".format(len(result.delta.events)),
            "effect_count={}".format(len(result.delta.effects)),
            "diagnostic_count={}".format(len(result.diagnostics)),
            "final_state_cell_count={}".format(len(result.final_state.cells)),
        ),
    )


def adapt_convergence_ruling(
    resolution: SemanticConvergenceResolution,
) -> TapCheckLedgerEntry:
    """Observe one already-produced semantic convergence resolution."""

    if type(resolution) is not SemanticConvergenceResolution:
        raise TypeError(
            "adapt_convergence_ruling requires an exact "
            "SemanticConvergenceResolution"
        )

    convergence_set = resolution.convergence_set
    return TapCheckLedgerEntry(
        category_id="convergence-rulings",
        subject=convergence_set.policy.identity,
        evidence=(
            "outcome_kind_id={}".format(resolution.outcome.kind_id),
            "ranking_count={}".format(len(resolution.ranking)),
            "candidate_count={}".format(len(convergence_set.candidates)),
            "member_count={}".format(len(convergence_set.members)),
            "provenance_count={}".format(len(resolution.provenance)),
        ),
    )


def adapt_narrative_state_change(
    result: NarrativeExecutionResult,
) -> TapCheckLedgerEntry:
    """Observe initial/final state carried by one narrative execution result."""

    if type(result) is not NarrativeExecutionResult:
        raise TypeError(
            "adapt_narrative_state_change requires an exact "
            "NarrativeExecutionResult"
        )

    initial = result.initial_state
    final = result.final_state
    return TapCheckLedgerEntry(
        category_id="narrative-state-changes",
        subject=_identity_text(final.story),
        evidence=(
            "initial_scene={}".format(_identity_text(initial.current_scene)),
            "final_scene={}".format(_identity_text(final.current_scene)),
            "state_changed={}".format(
                str(initial != final).lower()
            ),
            "initial_fact_count={}".format(len(initial.facts)),
            "final_fact_count={}".format(len(final.facts)),
            "progression_count={}".format(len(final.progression)),
            "choice_history_count={}".format(len(final.choice_history)),
            "trace_count={}".format(len(result.trace)),
            "diagnostic_count={}".format(len(result.diagnostics)),
            "choice_evidence_count={}".format(len(result.choice_evidence)),
        ),
    )


def adapt_air_lowering(
    result: GenericLoweringResult,
) -> TapCheckLedgerEntry:
    """Observe one already-produced generic lowering result over AIR."""

    if type(result) is not GenericLoweringResult:
        raise TypeError(
            "adapt_air_lowering requires an exact GenericLoweringResult"
        )

    return TapCheckLedgerEntry(
        category_id="air-lowering",
        subject="type_system.lowering.GenericLoweringResult",
        evidence=(
            "binding_count={}".format(len(result.bindings)),
            "rewritten_function_count={}".format(
                len(result.rewritten_functions)
            ),
            "specialized_function_count={}".format(
                len(result.specialized_functions)
            ),
            "function_count={}".format(len(result.functions)),
        ),
    )


def adapt_active_directive(
    result: DirectiveExecutionResult,
) -> TapCheckLedgerEntry:
    """Observe a directive root from an already-produced execution result."""

    if type(result) is not DirectiveExecutionResult:
        raise TypeError(
            "adapt_active_directive requires an exact DirectiveExecutionResult"
        )

    return TapCheckLedgerEntry(
        category_id="active-directives",
        subject=result.root,
        evidence=(
            "owner=workflow.directive_engine",
            "result_count={}".format(len(result.results)),
        ),
    )


__all__ = (
    "adapt_runtime_result",
    "adapt_convergence_ruling",
    "adapt_narrative_state_change",
    "adapt_air_lowering",
    "adapt_active_directive",
)