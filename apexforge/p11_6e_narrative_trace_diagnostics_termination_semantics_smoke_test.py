"""P11.6E narrative trace, diagnostics, and termination smoke test."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import subprocess
from pathlib import Path
from unittest.mock import patch

from language.narrative_model import (
    NarrativeChoice,
    NarrativeChoicePath,
    NarrativeIdentity,
    NarrativeStateFact,
    NarrativeStory,
)
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from runtime.narrative_execution import (
    NarrativeExecutionDiagnostic,
    NarrativeExecutionState,
    NarrativeExecutionTraceEvent,
    NarrativeTermination,
)
from runtime.narrative_observability import (
    NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME,
    execute_narrative_choice,
    terminate_narrative,
)
from runtime.narrative_transition import transition_narrative_choice


EXPECTED_BRANCH = "p11.6e-narrative-trace-diagnostics-termination-semantics"
EXPECTED_PREDECESSOR = "f32e296da893a1be5aa2cfb0f107c3e067b0bd64"
EXPECTED_TAG = "afp-p11.6d-freeze"
THIS_FILE = "apexforge/p11_6e_narrative_trace_diagnostics_termination_semantics_smoke_test.py"
MODULE_FILE = "apexforge/runtime/narrative_observability.py"
DOC_FILE = "docs/p11/P11_6E_NARRATIVE_TRACE_DIAGNOSTICS_TERMINATION_SEMANTICS.md"
AUTHORIZED_PATHS = (THIS_FILE, MODULE_FILE, DOC_FILE)
PROTECTED_FIXTURE_PATHS = (
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
)
PROTECTED_MAIN_SHA256 = "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_raises(exc_type, action, message_fragment: str = ""):
    try:
        action()
    except exc_type as exc:
        if message_fragment:
            require(message_fragment in str(exc), f"exception omitted {message_fragment!r}: {exc}")
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


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


def identity(kind: str, *path: str) -> NarrativeIdentity:
    return NarrativeIdentity(kind, tuple(path))


def make_story():
    story_id = identity("story", "Story")
    hero = identity("character", "Story", "Hero")
    scene_a = identity("scene", "Story", "SceneA")
    scene_b = identity("scene", "Story", "SceneB")
    scene_c = identity("scene", "Story", "SceneC")
    choice_id = identity("choice", "Story", "Decision")
    other_choice_id = identity("choice", "Story", "OtherDecision")
    choice = NarrativeChoice(
        choice_id,
        scene_a,
        (
            NarrativeChoicePath(
                "Enter",
                scene_b,
                condition="hero is ready",
                consequence="mark hero entered",
            ),
            NarrativeChoicePath("Wait", scene_c),
        ),
    )
    other_choice = NarrativeChoice(
        other_choice_id,
        scene_b,
        (NarrativeChoicePath("Return", scene_a),),
    )
    story = NarrativeStory(
        identity=story_id,
        characters=(),
        scenes=(),
        dialogues=(),
        choices=(choice, other_choice),
        perspectives=(),
        timelines=(),
        states=(),
        continuities=(),
    )
    bindings = bind_narrative_story(
        story,
        condition_bindings=(
            NarrativeConditionBinding(
                "hero is ready",
                NarrativeFactPredicate(hero, "status", "equals", "ready"),
            ),
        ),
        consequence_bindings=(
            NarrativeConsequenceBinding(
                "mark hero entered",
                (NarrativeFactAssignment(hero, "entered", "yes"),),
            ),
        ),
    )
    return story, bindings, hero, scene_a, scene_b, scene_c, choice_id, other_choice_id


def test_baseline_and_ownership() -> None:
    root = repo_root()
    require(git(root, "branch", "--show-current") == EXPECTED_BRANCH, "unexpected branch")
    require(git(root, "cat-file", "-t", EXPECTED_TAG) == "tag", "P11.6D freeze must be annotated")
    require(
        git(root, "rev-parse", EXPECTED_TAG + "^{}") == git(root, "rev-parse", EXPECTED_PREDECESSOR),
        "P11.6D predecessor mismatch",
    )
    status_lines = tuple(
        line
        for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line
    )
    observed_paths = tuple(sorted(line[3:].replace("\\", "/") for line in status_lines))
    require(
        observed_paths == tuple(sorted(AUTHORIZED_PATHS + PROTECTED_FIXTURE_PATHS)),
        f"unexpected P11.6E ownership/protected-fixture set: {observed_paths!r}",
    )
    require(all(line.startswith("?? ") for line in status_lines), "P11.6E files must be untracked/unstaged")
    fixture_main = root / "examples/P11Validation/main.apex"
    require(fixture_main.is_file(), "protected main.apex is missing")
    require(hashlib.sha256(fixture_main.read_bytes()).hexdigest() == PROTECTED_MAIN_SHA256, "protected main.apex changed")


def test_success_trace_and_transition_authority() -> None:
    story, bindings, hero, scene_a, scene_b, _, choice_id, _ = make_story()
    state = NarrativeExecutionState(
        story.identity,
        scene_a,
        facts=(NarrativeStateFact(hero, "status", "ready"),),
    )
    original_state = repr(state)
    with patch("runtime.narrative_observability.transition_narrative_choice", wraps=transition_narrative_choice) as delegated:
        result = execute_narrative_choice(state, bindings, choice_id, 0)
    require(delegated.call_count == 1, "P11.6E did not delegate to P11.6D")
    require(result.ok and not result.diagnostics, "successful transition was not diagnostic-free")
    require(result.final_state is not state, "success reused the input state")
    require(result.final_state.current_scene == scene_b, "wrong immutable next scene")
    require(result.final_state.progression == (scene_a, scene_b), "wrong progression")
    require(result.final_state.choice_history[-1].choice == choice_id, "choice evidence missing")
    require(NarrativeStateFact(hero, "entered", "yes") in result.final_state.facts, "consequence missing")
    require(repr(state) == original_state, "successful execution mutated input state")
    require(type(result.trace) is tuple and len(result.trace) == 1, "trace ordering/count is not deterministic")
    event = result.trace[0]
    require(type(event) is NarrativeExecutionTraceEvent and dataclasses.is_dataclass(event), "trace is not narrative-specific immutable evidence")
    require(
        tuple((fact.key, fact.value) for fact in event.facts) == (
            ("source_scene", "scene:Story/SceneA"),
            ("selected_choice", "choice:Story/Decision"),
            ("selected_path_index", "0"),
            ("destination_scene", "scene:Story/SceneB"),
            ("outcome", "success"),
        ),
        "success trace facts are incomplete or nondeterministic",
    )
    require(result.choice_evidence == (result.final_state.choice_history[-1],), "result evidence was not separated from trace")
    require(dataclasses.is_dataclass(result.final_state) and dataclasses.is_dataclass(result.final_state.termination), "state contracts are not immutable dataclasses")


def test_failure_diagnostics_and_fail_closed_condition() -> None:
    story, bindings, hero, scene_a, _, _, choice_id, other_choice_id = make_story()
    ready = NarrativeExecutionState(story.identity, scene_a, facts=(NarrativeStateFact(hero, "status", "ready"),))
    blocked = NarrativeExecutionState(story.identity, scene_a, facts=(NarrativeStateFact(hero, "status", "blocked"),))
    missing = NarrativeExecutionState(story.identity, scene_a)
    cases = (
        (NarrativeExecutionState(identity("story", "OtherStory"), scene_a), choice_id, 0, "story_mismatch", "NARRATIVE_TRANSITION_STORY_MISMATCH"),
        (ready, identity("choice", "Story", "Missing"), 0, "choice_not_found", "NARRATIVE_TRANSITION_CHOICE_NOT_FOUND"),
        (ready, other_choice_id, 0, "choice_not_current_scene", "NARRATIVE_TRANSITION_CHOICE_NOT_CURRENT_SCENE"),
        (ready, choice_id, 8, "path_not_found", "NARRATIVE_TRANSITION_PATH_NOT_FOUND"),
    )
    for case_state, case_choice, case_index, failure_kind, code in cases:
        before = repr(case_state)
        result = execute_narrative_choice(case_state, bindings, case_choice, case_index)
        require(not result.ok and result.final_state == case_state, f"{failure_kind} changed state")
        require(result.diagnostics[0].code == code, f"{failure_kind} was not classified deterministically")
        require(result.diagnostics[0].message == f"narrative transition failed: {failure_kind}", f"{failure_kind} message changed")
        require(result.diagnostics[0].severity == "error" and result.diagnostics[0].subject == case_choice, f"{failure_kind} diagnostic shape changed")
        require(result.trace[0].facts[-2].key == "failure_kind" and result.trace[0].facts[-2].value == failure_kind, f"{failure_kind} trace omitted failure evidence")
        require(repr(case_state) == before, f"{failure_kind} mutated input state")

    for gated_state in (blocked, missing):
        result = execute_narrative_choice(gated_state, bindings, choice_id, 0)
        require(result.diagnostics[0].code == "NARRATIVE_TRANSITION_CONDITION_UNSATISFIED", "condition was not fail-closed")
        require(result.final_state == gated_state and not result.final_state.choice_history, "failed gated transition changed state")

    ambiguous = type(bindings)(bindings.story, bindings.paths + (bindings.paths[0],))
    result = execute_narrative_choice(ready, ambiguous, choice_id, 0)
    require(result.diagnostics[0].code == "NARRATIVE_TRANSITION_AMBIGUOUS_PATH", "ambiguous path was swallowed")
    require(result.trace[0].facts[-2].value == "ambiguous_path", "ambiguous path trace evidence changed")


def test_termination_and_no_implicit_behavior() -> None:
    story, bindings, _, scene_a, _, _, choice_id, _ = make_story()
    state = NarrativeExecutionState(story.identity, scene_a)
    require(state.termination == NarrativeTermination(), "active state was not active by default")
    terminated = terminate_narrative(state)
    require(terminated is not state, "terminal construction reused input state")
    require(terminated.termination.status == "terminated", "termination status missing")
    require(terminated.termination.reason == NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME, "termination reason changed")
    require(state.termination.status == "active", "terminal construction mutated prior state")
    require(terminate_narrative(state) == terminated, "equivalent terminal inputs diverged")
    expect_raises(ValueError, lambda: terminate_narrative(terminated), "already terminated")
    terminal_result = execute_narrative_choice(terminated, bindings, choice_id, 0)
    require(terminal_result.final_state is terminated and not terminal_result.ok, "terminated execution was not explicit")
    require(terminal_result.diagnostics[0].code == "NARRATIVE_EXECUTION_TERMINATED", "terminal rejection code changed")
    signature = inspect.signature(execute_narrative_choice)
    require(tuple(signature.parameters) == ("state", "bindings", "choice", "path_index"), "execution surface added automatic selection")
    require("initial_scene" not in signature.parameters, "initial-scene resolver appeared")
    source = Path(__file__).with_name("runtime").joinpath("narrative_observability.py").read_text(encoding="utf-8")
    for token in ("from air.", "import air.", "AIRExpression", "StateAssignment", "StateSnapshot", "StateDelta", "RuntimeEngine", "AIR runtime"):
        require(token not in source, f"narrative boundary crossed via {token!r}")


def test_public_api_and_documentation() -> None:
    import runtime.narrative_observability as module

    require(module.__all__ == ("NARRATIVE_TERMINATION_REASON_EXPLICIT_OUTCOME", "execute_narrative_choice", "terminate_narrative"), "P11.6E API expanded unexpectedly")
    require(all(isinstance(item, str) for item in module.__all__), "P11.6E API names are not deterministic")
    doc = (repo_root() / DOC_FILE).read_text(encoding="utf-8")
    for phrase in (
        "P11.6E",
        "execute_narrative_choice",
        "NarrativeTransitionError",
        "explicit_outcome",
        "condition_unsatisfied",
        "No automatic choice selection",
        "No initial-scene resolver",
        "No AIR runtime reuse",
        "No graph-shape termination",
    ):
        require(phrase in doc, f"P11.6E documentation omitted {phrase!r}")


def main() -> None:
    test_baseline_and_ownership()
    test_success_trace_and_transition_authority()
    test_failure_diagnostics_and_fail_closed_condition()
    test_termination_and_no_implicit_behavior()
    test_public_api_and_documentation()
    print("AFP-P11.6E narrative trace/diagnostic/termination smoke test passed.")
    print("P11.6D frozen predecessor and exact ownership boundary: PASS")
    print("Immutable successful transition and deterministic trace evidence: PASS")
    print("Narrative diagnostics for structural and gated failures: PASS")
    print("Explicit immutable termination without graph inference: PASS")
    print("Narrative-only AIR/runtime boundary and repeated-input determinism: PASS")
    for relative in AUTHORIZED_PATHS:
        path = repo_root() / relative
        print(f"{relative} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
