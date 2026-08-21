"""P11.11D read-only owner-evidence adapter coverage."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import subprocess

from runtime.engine import ExecutionResult
from runtime.narrative_execution import (
    NarrativeExecutionResult,
    NarrativeExecutionState,
)
from semantic_decision.resolution import SemanticConvergenceResolution
from type_system.lowering import GenericLoweringResult
from workflow.directive_engine import DirectiveExecutionResult

from tam import TraceDomain, TraceIdentity, TraceMap, TraceRecord
from tap_check import (
    TAP_CHECK_CATEGORY_IDS,
    TapCheckLedgerEntry,
    adapt_active_directive,
    adapt_air_lowering,
    adapt_convergence_ruling,
    adapt_narrative_state_change,
    adapt_runtime_result,
    audit_trace_map,
)


PREDECESSOR_TAG = "afp-p11-11c-freeze"
PREDECESSOR_COMMIT = "80a690c04f2fd6dcc6cd30f69373040ee8973bb2"

FROZEN_HASHES = {
    "apexforge/tap_check/model.py":
        "C1E6F650977A73A7E3F3655A948416129AAB0AFDDB69DA561582F771C16B8769",
    "apexforge/tap_check/projection.py":
        "C43F222DC98704A3C3803F475359F97B72FCB0BEAB6F829188493CF591B117A2",
    "apexforge/p11_11c_trace_map_observational_audit_projection_smoke_test.py":
        "5CB06947633CBDB1D7A5A1D173E2D546196B3029095047AE3146BCE9183F489D",
    "docs/p11/P11_11C_TRACE_MAP_OBSERVATIONAL_AUDIT_PROJECTION.md":
        "67230EF7CC74EFD000C4C59B3B89698AB7E49C2612F19D7115919675116C7FE0",
}

EXPECTED_PUBLIC_SURFACE = (
    "TAP_CHECK_CATEGORY_IDS",
    "TapCheckLedgerEntry",
    "TapCheckAuditLedger",
    "audit_trace_map",
    "adapt_runtime_result",
    "adapt_convergence_ruling",
    "adapt_narrative_state_change",
    "adapt_air_lowering",
    "adapt_active_directive",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _frozen_instance(cls, **values):
    value = object.__new__(cls)
    for name, item in values.items():
        object.__setattr__(value, name, item)
    return value


def _identity(kind: str, *path: str):
    return SimpleNamespace(kind=kind, path=tuple(path))


def _state(*, story, scene, facts=(), progression=(), history=(), termination=None):
    return _frozen_instance(
        NarrativeExecutionState,
        story=story,
        current_scene=scene,
        facts=tuple(facts),
        progression=tuple(progression),
        choice_history=tuple(history),
        termination=termination,
    )


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.11C freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode
        == 0,
        "P11.11C freeze is not an ancestor of P11.11D",
    )
    for relative, expected in FROZEN_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen predecessor hash changed".format(relative),
        )


def _assert_public_surface() -> None:
    import tap_check

    _require(
        tap_check.__all__ == EXPECTED_PUBLIC_SURFACE,
        "tap_check public surface changed",
    )
    _require(len(TAP_CHECK_CATEGORY_IDS) == 10, "category taxonomy changed")


def _assert_runtime_result_adapter() -> None:
    delta = SimpleNamespace(
        assignments=("a", "b"),
        events=("e",),
        effects=("x", "y", "z"),
    )
    final_state = SimpleNamespace(cells=("c1", "c2"))
    result = _frozen_instance(
        ExecutionResult,
        delta=delta,
        trace=object(),
        diagnostics=("d1",),
        final_state=final_state,
    )

    first = adapt_runtime_result(result)
    second = adapt_runtime_result(result)
    _require(type(first) is TapCheckLedgerEntry, "runtime adapter returned wrong type")
    _require(first == second, "runtime adapter is nondeterministic")
    _require(first.category_id == "runtime-results", "runtime category changed")
    _require(
        first.subject == "runtime.engine.ExecutionResult",
        "runtime subject changed",
    )
    _require(
        first.evidence
        == (
            "assignment_count=2",
            "event_count=1",
            "effect_count=3",
            "diagnostic_count=1",
            "final_state_cell_count=2",
        ),
        "runtime evidence changed",
    )
    _require(first.trace_ids == (), "runtime adapter fabricated TAM links")


def _assert_convergence_adapter() -> None:
    resolution = _frozen_instance(
        SemanticConvergenceResolution,
        convergence_set=SimpleNamespace(
            policy=SimpleNamespace(identity="policy:priority"),
            candidates=("a", "b", "c"),
            members=("a", "b"),
        ),
        ranking=("first", "second"),
        outcome=SimpleNamespace(kind_id="selected"),
        provenance=("semantic:resolution",),
    )

    entry = adapt_convergence_ruling(resolution)
    _require(entry.category_id == "convergence-rulings", "convergence category changed")
    _require(entry.subject == "policy:priority", "convergence subject changed")
    _require(
        entry.evidence
        == (
            "outcome_kind_id=selected",
            "ranking_count=2",
            "candidate_count=3",
            "member_count=2",
            "provenance_count=1",
        ),
        "convergence evidence changed",
    )
    _require(entry.trace_ids == (), "convergence adapter fabricated TAM links")


def _assert_narrative_state_adapter() -> None:
    story = _identity("story", "AuditStory")
    initial = _state(
        story=story,
        scene=_identity("scene", "Opening"),
        facts=("fact-a",),
        progression=(_identity("scene", "Opening"),),
    )
    final = _state(
        story=story,
        scene=_identity("scene", "Second"),
        facts=("fact-a", "fact-b"),
        progression=(
            _identity("scene", "Opening"),
            _identity("scene", "Second"),
        ),
        history=("choice-a",),
    )
    result = _frozen_instance(
        NarrativeExecutionResult,
        initial_state=initial,
        final_state=final,
        trace=("transition",),
        diagnostics=(),
        choice_evidence=("choice-a",),
    )

    entry = adapt_narrative_state_change(result)
    _require(
        entry.category_id == "narrative-state-changes",
        "narrative-state category changed",
    )
    _require(entry.subject == "story:AuditStory", "narrative subject changed")
    _require(
        entry.evidence
        == (
            "initial_scene=scene:Opening",
            "final_scene=scene:Second",
            "state_changed=true",
            "initial_fact_count=1",
            "final_fact_count=2",
            "progression_count=2",
            "choice_history_count=1",
            "trace_count=1",
            "diagnostic_count=0",
            "choice_evidence_count=1",
        ),
        "narrative-state evidence changed",
    )
    _require(entry.trace_ids == (), "narrative adapter fabricated TAM links")

    unchanged_state = _state(
        story=story,
        scene=_identity("scene", "Opening"),
    )
    unchanged = _frozen_instance(
        NarrativeExecutionResult,
        initial_state=unchanged_state,
        final_state=unchanged_state,
        trace=(),
        diagnostics=(),
        choice_evidence=(),
    )
    unchanged_entry = adapt_narrative_state_change(unchanged)
    _require(
        "state_changed=false" in unchanged_entry.evidence,
        "explicit no-change evidence was not preserved",
    )


def _assert_air_lowering_adapter() -> None:
    result = _frozen_instance(
        GenericLoweringResult,
        manifest=object(),
        bindings=("binding",),
        rewritten_functions=("rewritten-a", "rewritten-b"),
        specialized_functions=("specialized",),
        functions=("f1", "f2", "f3"),
        program=object(),
    )

    entry = adapt_air_lowering(result)
    _require(entry.category_id == "air-lowering", "AIR lowering category changed")
    _require(
        entry.subject == "type_system.lowering.GenericLoweringResult",
        "AIR lowering subject changed",
    )
    _require(
        entry.evidence
        == (
            "binding_count=1",
            "rewritten_function_count=2",
            "specialized_function_count=1",
            "function_count=3",
        ),
        "AIR lowering evidence changed",
    )
    _require(entry.trace_ids == (), "AIR lowering adapter fabricated TAM links")


def _assert_active_directive_adapter() -> None:
    result = _frozen_instance(
        DirectiveExecutionResult,
        root="Main",
        results=(("Main", "ok"), ("Child", "ok")),
    )

    entry = adapt_active_directive(result)
    _require(entry.category_id == "active-directives", "active category changed")
    _require(entry.subject == "Main", "active directive subject changed")
    _require(
        entry.evidence
        == (
            "owner=workflow.directive_engine",
            "result_count=2",
        ),
        "active directive evidence changed",
    )
    _require(entry.trace_ids == (), "active adapter fabricated TAM links")


def _assert_exact_types() -> None:
    adapters = (
        adapt_runtime_result,
        adapt_convergence_ruling,
        adapt_narrative_state_change,
        adapt_air_lowering,
        adapt_active_directive,
    )
    for adapter in adapters:
        try:
            adapter(object())
        except TypeError:
            pass
        else:
            raise AssertionError("{} accepted unrelated evidence".format(adapter.__name__))


def _assert_c_projection_continuity() -> None:
    trace_id = TraceIdentity("trace:d-c-regression")
    record = TraceRecord(
        trace_id=trace_id,
        domain=TraceDomain("transformation"),
        producer="language.compiler",
        owner="language.compiler",
        representation="source-map-entry",
        canonical_identity="air:Main",
    )
    ledger = audit_trace_map(TraceMap((record,)))
    _require(len(ledger.entries) == 1, "C projection stopped mapping source-map entry")
    entry = ledger.entries[0]
    _require(
        entry.category_id == "compiler-transformations",
        "C projection category changed",
    )
    _require(entry.trace_ids == (trace_id,), "C trace link changed")
    _require(entry.trace_ids[0] is trace_id, "C TraceIdentity reference was replaced")


def _assert_adapter_module_is_read_only() -> None:
    text = (_root() / "apexforge/tap_check/adapters.py").read_text(encoding="utf-8")

    required = (
        "ExecutionResult",
        "NarrativeExecutionResult",
        "SemanticConvergenceResolution",
        "GenericLoweringResult",
        "DirectiveExecutionResult",
    )
    for token in required:
        _require(token in text, "adapter owner contract missing " + token)

    forbidden = (
        "RuntimeEngine(",
        "DirectiveExecutionEngine(",
        "apply_semantic_convergence_policy(",
        "validate_semantic_convergence_resolution(",
        "lower_linked_generics(",
        "transform_aether_air_snapshot(",
        "lower_narrative",
        "compile_",
        "parse_",
        "execute(",
        "subprocess",
        "Path(",
        "open(",
        "TraceIdentity(",
    )
    for token in forbidden:
        _require(token not in text, "adapter acquired active behavior: " + token)


def _assert_owner_boundaries() -> None:
    paths = (
        "apexforge/tam",
        "apexforge/governance",
        "apexforge/language",
        "apexforge/air",
        "apexforge/authority",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
        "apexforge/semantic_decision",
        "apexforge/aether_air",
        "apexforge/type_system",
        "apexforge/workflow",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.11D mutated existing evidence owners")


def main() -> None:
    _assert_predecessor()
    _assert_public_surface()
    _assert_runtime_result_adapter()
    _assert_convergence_adapter()
    _assert_narrative_state_adapter()
    _assert_air_lowering_adapter()
    _assert_active_directive_adapter()
    _assert_exact_types()
    _assert_c_projection_continuity()
    _assert_adapter_module_is_read_only()
    _assert_owner_boundaries()

    print("P11_11C_FREEZE_ANCESTRY=PASS")
    print("OWNER_EVIDENCE_ADAPTER_COUNT=5")
    print("OWNER_EVIDENCE_ADAPTER_STYLE=NARROW_TYPE_SPECIFIC")
    print("RUNTIME_RESULT=runtime.engine.ExecutionResult")
    print("RUNTIME_RESULT_CATEGORY=runtime-results")
    print("CONVERGENCE_RULING=SemanticConvergenceResolution")
    print("CONVERGENCE_RULING_CATEGORY=convergence-rulings")
    print("NARRATIVE_STATE_CHANGE=NarrativeExecutionResult")
    print("NARRATIVE_STATE_CHANGE_CATEGORY=narrative-state-changes")
    print("NARRATIVE_NO_CHANGE=EXPLICIT_FALSE_EVIDENCE_ALLOWED")
    print("AIR_LOWERING=GenericLoweringResult")
    print("AIR_LOWERING_CATEGORY=air-lowering")
    print("ACTIVE_DIRECTIVE=DirectiveExecutionResult")
    print("ACTIVE_DIRECTIVE_CATEGORY=active-directives")
    print("TRACE_LINK_POLICY=EMPTY_WHEN_OWNER_HAS_NO_EXACT_TAM_LINK")
    print("TRACE_IDENTITY_FABRICATION=NONE")
    print("SEMANTIC_CHANGE_ADAPTER=DEFERRED_NO_UNAMBIGUOUS_OWNER_EVENT")
    print("OPTIMIZATION_DECISION_ADAPTER=DEFERRED_NO_CANONICAL_DECISION_OBJECT")
    print("CONTINUITY_EFFECT_ADAPTER=DEFERRED_NO_UNAMBIGUOUS_EFFECT_OBJECT")
    print("ADAPTER_EXECUTION=NONE")
    print("ADAPTER_VALIDATION_EXECUTION=NONE")
    print("ADAPTER_LOWERING_EXECUTION=NONE")
    print("ADAPTER_SEMANTIC_RESOLUTION_EXECUTION=NONE")
    print("C_TRACE_MAP_PROJECTION_CONTINUITY=PASS")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_11D_READ_ONLY_OWNER_EVIDENCE_ADAPTERS=PASS")


if __name__ == "__main__":
    main()