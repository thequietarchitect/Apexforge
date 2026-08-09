"""P11.6B immutable narrative execution state/result contract smoke test."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
from pathlib import Path

from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from runtime.narrative_execution import (
    NarrativeChoiceEvidence,
    NarrativeExecutionDiagnostic,
    NarrativeExecutionResult,
    NarrativeExecutionState,
    NarrativeExecutionTraceEvent,
    NarrativeExecutionTraceFact,
    NarrativeTermination,
)


EXPECTED_BRANCH = "p11.6b-immutable-narrative-execution-state-result-contracts"
EXPECTED_PREDECESSOR = "7438aec1f105e749287998aff6cc35d01d174425"
EXPECTED_TAG = "afp-p11.6a-freeze"
THIS_FILE = "apexforge/p11_6b_immutable_narrative_execution_state_result_contracts_smoke_test.py"
MODULE_FILE = "apexforge/runtime/narrative_execution.py"
DOC_FILE = "docs/p11/P11_6B_IMMUTABLE_NARRATIVE_EXECUTION_STATE_RESULT_CONTRACTS.md"
AUTHORIZED_PATHS = (THIS_FILE, MODULE_FILE, DOC_FILE)
PROTECTED_FIXTURE_PATHS = (
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
)
PROTECTED_MAIN_SHA256 = "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"git {' '.join(args)} failed: {completed.stderr.strip()}",
    )
    return completed.stdout.strip()


def expect_raises(exc_type, action, message_fragment: str = "") -> None:
    try:
        action()
    except exc_type as exc:
        if message_fragment:
            require(
                message_fragment in str(exc),
                f"exception omitted {message_fragment!r}: {exc}",
            )
    else:
        raise AssertionError(f"expected {exc_type.__name__}")


def identity(kind: str, *path: str) -> NarrativeIdentity:
    return NarrativeIdentity(kind, tuple(path))


def test_baseline_and_ownership() -> None:
    root = repo_root()
    require(
        git(root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6B smoke test is running on an unexpected branch",
    )
    require(
        git(root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6A freeze must remain an annotated tag",
    )
    require(
        git(root, "rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6A freeze resolves to an unexpected predecessor",
    )

    head = git(root, "rev-parse", "HEAD")
    candidate_mode = head == EXPECTED_PREDECESSOR
    if not candidate_mode:
        require(
            git(root, "rev-parse", "HEAD^") == EXPECTED_PREDECESSOR,
            "P11.6B committed predecessor is not the P11.6A freeze",
        )

    status_lines = tuple(
        line
        for line in git(
            root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if line
    )
    observed_paths = tuple(
        sorted(line[3:].replace("\\", "/") for line in status_lines)
    )
    expected_paths = (
        AUTHORIZED_PATHS + PROTECTED_FIXTURE_PATHS
        if candidate_mode
        else PROTECTED_FIXTURE_PATHS
    )
    require(
        observed_paths == tuple(sorted(expected_paths)),
        f"unexpected P11.6B ownership/protected-fixture set: {observed_paths!r}",
    )
    require(
        all(line.startswith("?? ") for line in status_lines),
        "P11.6B candidate and protected fixture must remain untracked/unstaged",
    )

    fixture_main = root / "examples/P11Validation/main.apex"
    require(fixture_main.is_file(), "protected P11Validation main.apex is missing")
    require(
        hashlib.sha256(fixture_main.read_bytes()).hexdigest()
        == PROTECTED_MAIN_SHA256,
        "protected P11Validation main.apex hash changed",
    )
    require(
        (root / "examples/P11Validation/apexforge.json").is_file(),
        "protected P11Validation apexforge.json is missing",
    )


def test_public_contract_inventory_and_immutability() -> None:
    import runtime.narrative_execution as module

    require(
        module.__all__
        == (
            "NarrativeChoiceEvidence",
            "NarrativeExecutionDiagnostic",
            "NarrativeExecutionResult",
            "NarrativeExecutionState",
            "NarrativeExecutionTraceEvent",
            "NarrativeExecutionTraceFact",
            "NarrativeTermination",
        ),
        "P11.6B public contract inventory changed",
    )

    for record_type in (
        NarrativeChoiceEvidence,
        NarrativeExecutionDiagnostic,
        NarrativeExecutionResult,
        NarrativeExecutionState,
        NarrativeExecutionTraceEvent,
        NarrativeExecutionTraceFact,
        NarrativeTermination,
    ):
        params = getattr(record_type, "__dataclass_params__", None)
        require(
            params is not None and params.frozen,
            f"{record_type.__name__} is not frozen",
        )


def test_choice_evidence_contract() -> None:
    choice = identity("choice", "Story", "ChoiceA")
    scene_a = identity("scene", "Story", "SceneA")
    scene_b = identity("scene", "Story", "SceneB")

    evidence = NarrativeChoiceEvidence(
        choice=choice,
        source_scene=scene_a,
        path_index=0,
        path_label="Continue",
        destination=scene_b,
    )
    require(evidence.path_index == 0, "choice path index changed")
    require(evidence.destination == scene_b, "choice destination changed")

    expect_raises(
        TypeError,
        lambda: NarrativeChoiceEvidence(
            choice=choice,
            source_scene=scene_a,
            path_index=True,
            path_label="Continue",
            destination=scene_b,
        ),
        "exact int",
    )
    expect_raises(
        ValueError,
        lambda: NarrativeChoiceEvidence(
            choice=choice,
            source_scene=scene_a,
            path_index=-1,
            path_label="Continue",
            destination=scene_b,
        ),
        "non-negative",
    )


def test_termination_contract_without_policy() -> None:
    active = NarrativeTermination()
    require(active.status == "active", "default termination status changed")
    require(not active.is_terminated, "active termination reports terminated")
    require(active.reason is None, "active termination unexpectedly has a reason")

    ended = NarrativeTermination("terminated", "story complete")
    require(ended.is_terminated, "terminated state did not report terminated")
    require(ended.reason == "story complete", "termination reason changed")

    expect_raises(
        ValueError,
        lambda: NarrativeTermination("active", "not allowed"),
        "must be None",
    )


def test_trace_and_diagnostic_records_are_narrative_specific() -> None:
    fact_a = NarrativeExecutionTraceFact("scene", "SceneA")
    fact_b = NarrativeExecutionTraceFact("choice", "ChoiceA")
    event = NarrativeExecutionTraceEvent(
        "narrative.contract",
        "contract evidence only",
        (fact_a, fact_b),
    )
    require(
        event.facts == (fact_a, fact_b),
        "trace fact order was not preserved",
    )

    diagnostic = NarrativeExecutionDiagnostic(
        "warning",
        "NAR-CONTRACT",
        "contract-only diagnostic",
        identity("scene", "Story", "SceneA"),
    )
    require(not diagnostic.is_error, "warning diagnostic reported as error")

    from runtime.diagnostics import Diagnostic, Trace, TraceStep

    require(
        type(diagnostic) is not Diagnostic,
        "narrative diagnostic reused AIR runtime Diagnostic",
    )
    require(
        type(event) is not TraceStep,
        "narrative trace event reused AIR runtime TraceStep",
    )
    require(
        type((event,)) is not Trace,
        "narrative trace reused AIR runtime Trace",
    )


def test_state_normalization_and_invariants() -> None:
    story = identity("story", "Story")
    scene_a = identity("scene", "Story", "SceneA")
    scene_b = identity("scene", "Story", "SceneB")
    hero = identity("character", "Story", "Hero")

    fact_b = NarrativeStateFact(hero, "zeta", "2")
    fact_a = NarrativeStateFact(hero, "alpha", "1")
    state = NarrativeExecutionState(
        story=story,
        current_scene=scene_a,
        facts=(fact_b, fact_a),
    )
    require(
        state.progression == (scene_a,),
        "empty progression did not canonicalize to current scene",
    )
    require(
        state.facts == (fact_a, fact_b),
        "narrative execution facts are not deterministically ordered",
    )

    expect_raises(
        ValueError,
        lambda: NarrativeExecutionState(
            story=story,
            current_scene=scene_a,
            progression=(scene_b,),
        ),
        "end at current_scene",
    )
    expect_raises(
        ValueError,
        lambda: NarrativeExecutionState(
            story=story,
            current_scene=scene_a,
            facts=(
                NarrativeStateFact(hero, "mood", "calm"),
                NarrativeStateFact(hero, "mood", "alert"),
            ),
        ),
        "duplicate narrative execution fact slot",
    )

    expect_raises(
        dataclasses.FrozenInstanceError,
        lambda: setattr(state, "current_scene", scene_b),
    )


def test_result_contract_and_separate_air_boundary() -> None:
    story = identity("story", "Story")
    scene_a = identity("scene", "Story", "SceneA")
    scene_b = identity("scene", "Story", "SceneB")
    choice = identity("choice", "Story", "ChoiceA")

    initial = NarrativeExecutionState(story, scene_a)
    evidence = NarrativeChoiceEvidence(
        choice,
        scene_a,
        0,
        "Continue",
        scene_b,
    )
    final = NarrativeExecutionState(
        story,
        scene_b,
        progression=(scene_a, scene_b),
        choice_history=(evidence,),
        termination=NarrativeTermination("terminated", "story complete"),
    )
    result = NarrativeExecutionResult(
        initial_state=initial,
        final_state=final,
        trace=(
            NarrativeExecutionTraceEvent(
                "narrative.contract",
                "result container evidence",
            ),
        ),
        diagnostics=(
            NarrativeExecutionDiagnostic(
                "info",
                "NAR-CONTRACT",
                "no execution semantics",
            ),
        ),
        choice_evidence=(evidence,),
    )
    require(result.ok, "info-only narrative result is not ok")
    require(
        result.termination == final.termination,
        "result termination projection changed",
    )

    from runtime.engine import ExecutionResult

    require(
        type(result) is not ExecutionResult,
        "narrative result reused runtime.engine.ExecutionResult",
    )


def test_stage_boundary_and_documentation() -> None:
    root = repo_root()
    module_text = (root / MODULE_FILE).read_text(encoding="utf-8")
    doc = (root / DOC_FILE).read_text(encoding="utf-8")

    for forbidden in (
        "from runtime.engine import",
        "from runtime.state import",
        "from runtime.diagnostics import",
        "ProjectBuild",
        "RuntimeEngine(",
        "apexforge build",
        "apexforge run",
    ):
        require(
            forbidden not in module_text,
            f"P11.6B runtime contract crossed boundary via {forbidden!r}",
        )

    required_phrases = (
        "P11.6B defines immutable containers and invariants only",
        "P11.6E owns trace, diagnostic, and termination execution semantics",
        "NarrativeExecutionState",
        "NarrativeExecutionResult",
        "NarrativeChoiceEvidence",
        "NarrativeTermination",
        "AIR runtime remains unchanged",
        "No scene selection",
        "No condition evaluation",
        "No consequence application",
        "No scene transition",
        "No CLI routing",
    )
    for phrase in required_phrases:
        require(
            phrase in doc,
            f"P11.6B document omitted required phrase: {phrase!r}",
        )


def main() -> None:
    test_baseline_and_ownership()
    test_public_contract_inventory_and_immutability()
    test_choice_evidence_contract()
    test_termination_contract_without_policy()
    test_trace_and_diagnostic_records_are_narrative_specific()
    test_state_normalization_and_invariants()
    test_result_contract_and_separate_air_boundary()
    test_stage_boundary_and_documentation()

    root = repo_root()
    print("AFP-P11.6B immutable narrative execution state/result contracts smoke test passed.")
    print("Frozen P11.6A predecessor and annotated tag: PASS")
    print("Exact P11.6B ownership and protected-fixture boundary: PASS")
    print("Frozen immutable public narrative execution contracts: PASS")
    print("Deterministic state normalization and duplicate rejection: PASS")
    print("Narrative-specific result/trace/diagnostic records: PASS")
    print("AIR runtime/state/result separation: PASS")
    print("No execution, transition, binding, CLI, or artifact integration: PASS")
    for relative in AUTHORIZED_PATHS:
        path = root / relative
        print(f"{relative} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
