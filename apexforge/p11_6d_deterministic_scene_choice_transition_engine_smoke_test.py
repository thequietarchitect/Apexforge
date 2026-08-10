"""P11.6D deterministic narrative scene/choice transition smoke test."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import subprocess
from pathlib import Path

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
    NarrativeExecutableBindingSet,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from runtime.narrative_execution import NarrativeExecutionState
from runtime.narrative_transition import (
    NarrativeTransitionError,
    transition_narrative_choice,
)


EXPECTED_BRANCH = "p11.6d-deterministic-scene-choice-transition-engine"
EXPECTED_PREDECESSOR = "b7a811f"
EXPECTED_TAG = "afp-p11.6c-freeze"
THIS_FILE = "apexforge/p11_6d_deterministic_scene_choice_transition_engine_smoke_test.py"
MODULE_FILE = "apexforge/runtime/narrative_transition.py"
DOC_FILE = "docs/p11/P11_6D_DETERMINISTIC_SCENE_CHOICE_TRANSITION_ENGINE.md"
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
    require(
        git(root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6D smoke test is running on an unexpected branch",
    )
    require(
        git(root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6C freeze must remain an annotated tag",
    )
    require(
        git(root, "rev-parse", EXPECTED_TAG + "^{}") == git(root, "rev-parse", EXPECTED_PREDECESSOR),
        "P11.6D predecessor is not the P11.6C freeze",
    )
    status_lines = tuple(
        line
        for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line
    )
    observed_paths = tuple(sorted(line[3:].replace("\\", "/") for line in status_lines))
    require(
        observed_paths == tuple(sorted(AUTHORIZED_PATHS + PROTECTED_FIXTURE_PATHS)),
        f"unexpected P11.6D ownership/protected-fixture set: {observed_paths!r}",
    )
    require(all(line.startswith("?? ") for line in status_lines), "P11.6D files must remain untracked/unstaged")

    fixture_main = root / "examples/P11Validation/main.apex"
    require(fixture_main.is_file(), "protected main.apex is missing")
    require(
        hashlib.sha256(fixture_main.read_bytes()).hexdigest() == PROTECTED_MAIN_SHA256,
        "protected main.apex hash changed",
    )


def test_public_api_and_immutable_success() -> None:
    story, bindings, hero, scene_a, scene_b, scene_c, choice_id, _ = make_story()
    state = NarrativeExecutionState(
        story=story.identity,
        current_scene=scene_a,
        facts=(NarrativeStateFact(hero, "status", "ready"),),
    )
    original_state = repr(state)
    original_story = repr(story)
    result = transition_narrative_choice(state, bindings, choice_id, 0)

    require(result is not state, "transition returned the input state")
    require(result.current_scene == scene_b, "destination scene was not applied")
    require(result.progression == (scene_a, scene_b), "destination was not appended to progression")
    require(result.choice_history[0].choice == choice_id, "choice evidence omitted choice identity")
    require(result.choice_history[0].source_scene == scene_a, "choice evidence omitted source scene")
    require(result.choice_history[0].path_index == 0, "choice evidence omitted path index")
    require(result.choice_history[0].path_label == "Enter", "choice evidence omitted path label")
    require(result.choice_history[0].destination == scene_b, "choice evidence omitted destination")
    require(
        NarrativeStateFact(hero, "entered", "yes") in result.facts,
        "bound consequence did not immutably assign the fact",
    )
    require(NarrativeStateFact(hero, "status", "ready") in result.facts, "existing fact was lost")
    require(repr(state) == original_state and repr(story) == original_story, "input object was mutated")
    expect_raises(dataclasses.FrozenInstanceError, lambda: setattr(result, "current_scene", scene_a))

    ungated_result = transition_narrative_choice(state, bindings, choice_id, 1)
    require(ungated_result.current_scene == scene_c, "ungated path did not transition")
    require(
        NarrativeStateFact(hero, "entered", "yes") not in ungated_result.facts,
        "ungated path unexpectedly applied another path's consequence",
    )

    import runtime.narrative_transition as module

    require(
        module.__all__ == ("NarrativeTransitionError", "transition_narrative_choice"),
        "P11.6D public API inventory changed",
    )
    require(
        tuple(inspect.signature(transition_narrative_choice).parameters) ==
        ("state", "bindings", "choice", "path_index"),
        "transition API is wider than the narrow explicit selection contract",
    )


def test_condition_semantics_and_structural_failures() -> None:
    story, bindings, hero, scene_a, _, scene_c, choice_id, other_choice_id = make_story()
    ready = NarrativeExecutionState(
        story.identity,
        scene_a,
        facts=(NarrativeStateFact(hero, "status", "ready"),),
    )
    not_ready = NarrativeExecutionState(
        story.identity,
        scene_a,
        facts=(NarrativeStateFact(hero, "status", "blocked"),),
    )
    missing = NarrativeExecutionState(story.identity, scene_a)

    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(not_ready, bindings, choice_id, 0),
        "condition_unsatisfied",
    )
    require(error.failure_kind == "condition_unsatisfied", "wrong gated failure kind")
    expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(missing, bindings, choice_id, 0),
        "condition_unsatisfied",
    )

    not_equals_story = NarrativeStory(
        identity=story.identity,
        characters=(), scenes=(), dialogues=(),
        choices=(NarrativeChoice(
            choice_id, scene_a,
            (NarrativeChoicePath("Open", scene_c, condition="hero is not ready"),),
        ),),
        perspectives=(), timelines=(), states=(), continuities=(),
    )
    not_equals_bindings = bind_narrative_story(
        not_equals_story,
        condition_bindings=(NarrativeConditionBinding(
            "hero is not ready",
            NarrativeFactPredicate(hero, "status", "not_equals", "ready"),
        ),),
    )
    require(
        transition_narrative_choice(not_equals_story_state := NarrativeExecutionState(
            not_equals_story.identity, scene_a,
            facts=(NarrativeStateFact(hero, "status", "blocked"),),
        ), not_equals_bindings, choice_id, 0).current_scene == scene_c,
        "not_equals did not accept an existing different value",
    )
    expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(
            NarrativeExecutionState(not_equals_story.identity, scene_a),
            not_equals_bindings,
            choice_id,
            0,
        ),
        "condition_unsatisfied",
    )

    unknown_choice = identity("choice", "Story", "Missing")
    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(ready, bindings, unknown_choice, 0),
        "choice_not_found",
    )
    require(error.failure_kind == "choice_not_found", "wrong unknown-choice failure kind")
    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(ready, bindings, other_choice_id, 0),
        "choice_not_current_scene",
    )
    require(error.failure_kind == "choice_not_current_scene", "wrong scene ownership failure kind")
    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(ready, bindings, choice_id, 8),
        "path_not_found",
    )
    require(error.failure_kind == "path_not_found", "wrong path lookup failure kind")

    ambiguous_bindings = NarrativeExecutableBindingSet(
        story.identity,
        bindings.paths + (bindings.paths[0],),
    )
    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(ready, ambiguous_bindings, choice_id, 0),
        "ambiguous_path",
    )
    require(error.failure_kind == "ambiguous_path", "wrong ambiguous-path failure kind")

    mismatched_story = identity("story", "OtherStory")
    error = expect_raises(
        NarrativeTransitionError,
        lambda: transition_narrative_choice(
            NarrativeExecutionState(mismatched_story, scene_a),
            bindings,
            choice_id,
            0,
        ),
        "story_mismatch",
    )
    require(error.failure_kind == "story_mismatch", "wrong binding story failure kind")
    require(not_equals_story_state.current_scene == scene_a, "test input state changed")


def test_runtime_boundary_documentation_and_types() -> None:
    import runtime.narrative_transition as module

    source = Path(module.__file__).read_text(encoding="utf-8")
    for token in (
        "from air.",
        "import air.",
        "AIRExpression",
        "StateAssignment",
        "StateSnapshot",
        "StateDelta",
        "RuntimeEngine",
        "ExecutionResult",
        "NarrativeExecutionDiagnostic",
        "NarrativeExecutionTraceEvent",
    ):
        require(token not in source, f"P11.6D crossed boundary via {token!r}")
    expect_raises(TypeError, lambda: transition_narrative_choice("state", None, identity("choice", "x"), 0))
    expect_raises(TypeError, lambda: transition_narrative_choice(NarrativeExecutionState(identity("story", "S"), identity("scene", "S", "A")), None, identity("choice", "x"), 0))

    doc = (repo_root() / DOC_FILE).read_text(encoding="utf-8")
    for phrase in (
        "P11.6D",
        "explicit choice identity and path index",
        "Missing fact slots satisfy neither operator",
        "NarrativeTransitionError",
        "No automatic choice selection",
        "No AIR runtime reuse",
        "No runtime diagnostics",
        "No termination algorithm",
        "No ProjectBuild integration",
    ):
        require(phrase in doc, f"P11.6D documentation omitted {phrase!r}")


def main() -> None:
    test_baseline_and_ownership()
    test_public_api_and_immutable_success()
    test_condition_semantics_and_structural_failures()
    test_runtime_boundary_documentation_and_types()

    root = repo_root()
    print("AFP-P11.6D deterministic narrative scene/choice transition smoke test passed.")
    print("Frozen P11.6C predecessor and exact ownership boundary: PASS")
    print("Explicit choice/path selection and current-scene verification: PASS")
    print("Equals/not_equals evaluation with fail-closed missing facts: PASS")
    print("Immutable assignment, destination, progression, and choice evidence: PASS")
    print("Structural transition failures without runtime diagnostics: PASS")
    print("Narrative-specific AIR/runtime boundary: PASS")
    for relative in AUTHORIZED_PATHS:
        path = root / relative
        print(f"{relative} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
