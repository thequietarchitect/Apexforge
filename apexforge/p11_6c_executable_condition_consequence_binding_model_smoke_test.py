"""P11.6C executable condition/consequence binding model smoke test."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
from pathlib import Path

from language.narrative_model import (
    NarrativeChoice,
    NarrativeChoicePath,
    NarrativeIdentity,
    NarrativeStory,
)
from runtime.narrative_binding import (
    NarrativeBindingError,
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeExecutableBindingSet,
    NarrativeExecutableChoicePath,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)

EXPECTED_BRANCH = "p11.6c-executable-condition-consequence-binding-model"
EXPECTED_PREDECESSOR = "b339791715670ad752d3a82e315b1f9334b1e55a"
EXPECTED_TAG = "afp-p11.6b-freeze"
THIS_FILE = "apexforge/p11_6c_executable_condition_consequence_binding_model_smoke_test.py"
MODULE_FILE = "apexforge/runtime/narrative_binding.py"
DOC_FILE = "docs/p11/P11_6C_EXECUTABLE_CONDITION_CONSEQUENCE_BINDING_MODEL.md"
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


def expect_raises(exc_type, action, fragment: str = ""):
    try:
        action()
    except exc_type as exc:
        if fragment:
            require(fragment in str(exc), f"exception omitted {fragment!r}: {exc}")
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def identity(kind: str, *path: str) -> NarrativeIdentity:
    return NarrativeIdentity(kind, tuple(path))


def make_story():
    story_id = identity("story", "Story")
    hero = identity("character", "Story", "Hero")
    scene_a = identity("scene", "Story", "SceneA")
    scene_b = identity("scene", "Story", "SceneB")
    choice_id = identity("choice", "Story", "Decision")

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
            NarrativeChoicePath("Wait", scene_a),
        ),
    )
    story = NarrativeStory(
        identity=story_id,
        characters=(),
        scenes=(),
        dialogues=(),
        choices=(choice,),
        perspectives=(),
        timelines=(),
        states=(),
        continuities=(),
    )
    return story, hero, scene_a, scene_b


def test_baseline_and_ownership() -> None:
    root = repo_root()
    require(
        git(root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6C smoke test is running on an unexpected branch",
    )
    require(
        git(root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6B freeze must remain an annotated tag",
    )
    require(
        git(root, "rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6B freeze resolves to an unexpected predecessor",
    )

    head = git(root, "rev-parse", "HEAD")
    candidate_mode = head == EXPECTED_PREDECESSOR
    if not candidate_mode:
        require(
            git(root, "rev-parse", "HEAD^") == EXPECTED_PREDECESSOR,
            "P11.6C committed predecessor is not the P11.6B freeze",
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
        f"unexpected P11.6C ownership/protected-fixture set: {observed_paths!r}",
    )
    require(
        all(line.startswith("?? ") for line in status_lines),
        "P11.6C candidate and protected fixture must remain untracked/unstaged",
    )

    fixture_main = root / "examples/P11Validation/main.apex"
    require(fixture_main.is_file(), "protected main.apex is missing")
    require(
        hashlib.sha256(fixture_main.read_bytes()).hexdigest()
        == PROTECTED_MAIN_SHA256,
        "protected main.apex hash changed",
    )


def test_public_inventory_and_immutability() -> None:
    import runtime.narrative_binding as module

    require(
        module.__all__
        == (
            "NarrativeBindingError",
            "NarrativeConditionBinding",
            "NarrativeConsequenceBinding",
            "NarrativeExecutableBindingSet",
            "NarrativeExecutableChoicePath",
            "NarrativeFactAssignment",
            "NarrativeFactPredicate",
            "bind_narrative_story",
        ),
        "P11.6C public contract inventory changed",
    )

    for record_type in (
        NarrativeConditionBinding,
        NarrativeConsequenceBinding,
        NarrativeExecutableBindingSet,
        NarrativeExecutableChoicePath,
        NarrativeFactAssignment,
        NarrativeFactPredicate,
    ):
        params = getattr(record_type, "__dataclass_params__", None)
        require(params is not None and params.frozen, f"{record_type.__name__} is not frozen")


def test_predicate_assignment_contracts() -> None:
    _, hero, _, _ = make_story()
    predicate = NarrativeFactPredicate(hero, "status", "equals", "ready")
    assignment = NarrativeFactAssignment(hero, "entered", "yes")
    require(predicate.operator == "equals", "predicate operator changed")
    require(assignment.value == "yes", "assignment value changed")
    expect_raises(
        ValueError,
        lambda: NarrativeFactPredicate(hero, "status", "contains", "ready"),
        "equals' or 'not_equals",
    )
    expect_raises(
        ValueError,
        lambda: NarrativeFactAssignment(hero, " entered", "yes"),
        "trimmed",
    )


def test_missing_and_bound_semantics() -> None:
    story, hero, _, _ = make_story()
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
    require(len(bindings.paths) == 2, "choice-path count changed")
    first, second = bindings.paths
    require(not first.is_ungated, "bound condition reported ungated")
    require(first.has_consequence, "bound consequence was omitted")
    require(second.is_ungated, "missing condition did not become ungated")
    require(second.condition is None, "missing condition created a predicate")
    require(
        not second.has_consequence and second.assignments == (),
        "missing consequence created assignments",
    )


def test_unbound_rejection() -> None:
    story, hero, _, _ = make_story()

    exc = expect_raises(
        NarrativeBindingError,
        lambda: bind_narrative_story(story),
        "unbound narrative condition text",
    )
    require(exc.binding_kind == "condition", "wrong unbound condition kind")

    exc = expect_raises(
        NarrativeBindingError,
        lambda: bind_narrative_story(
            story,
            condition_bindings=(
                NarrativeConditionBinding(
                    "hero is ready",
                    NarrativeFactPredicate(hero, "status", "equals", "ready"),
                ),
            ),
        ),
        "unbound narrative consequence text",
    )
    require(exc.binding_kind == "consequence", "wrong unbound consequence kind")


def test_exact_text_and_duplicate_rejection() -> None:
    story, hero, _, _ = make_story()
    predicate = NarrativeFactPredicate(hero, "status", "equals", "ready")
    expect_raises(
        ValueError,
        lambda: bind_narrative_story(
            story,
            condition_bindings=(
                NarrativeConditionBinding("hero is ready", predicate),
                NarrativeConditionBinding("hero is ready", predicate),
            ),
        ),
        "duplicate narrative condition binding",
    )
    expect_raises(
        NarrativeBindingError,
        lambda: bind_narrative_story(
            story,
            condition_bindings=(
                NarrativeConditionBinding("Hero is ready", predicate),
            ),
        ),
        "unbound narrative condition text",
    )


def test_order_and_story_preservation() -> None:
    story, hero, scene_a, scene_b = make_story()
    original = repr(story)
    result = bind_narrative_story(
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
                (
                    NarrativeFactAssignment(hero, "entered", "yes"),
                    NarrativeFactAssignment(hero, "mode", "inside"),
                ),
            ),
        ),
    )
    require(repr(story) == original, "frozen semantic story was mutated")
    require(
        tuple(path.path_index for path in result.paths) == (0, 1),
        "choice-path order changed",
    )
    require(
        result.paths[0].source_scene == scene_a
        and result.paths[0].destination == scene_b,
        "bound path identities changed",
    )
    require(
        tuple(a.name for a in result.paths[0].assignments) == ("entered", "mode"),
        "consequence assignment order changed",
    )
    expect_raises(
        dataclasses.FrozenInstanceError,
        lambda: setattr(result.paths[0], "path_label", "Changed"),
    )


def test_runtime_separation_and_stage_boundary() -> None:
    import runtime.narrative_binding as module

    text = Path(module.__file__).read_text(encoding="utf-8")
    for token in (
        "from air.",
        "import air.",
        "AIRExpression",
        "StateAssignment",
        "AIRWhenAction",
        "RuntimeEngine",
        "ExecutionResult",
        "StateSnapshot",
        "StateDelta",
        "from runtime.narrative_execution import",
    ):
        require(token not in text, f"P11.6C crossed boundary via {token!r}")

    for forbidden_name in (
        "evaluate",
        "evaluate_condition",
        "apply",
        "apply_consequence",
        "transition",
        "execute",
        "run",
    ):
        require(
            not hasattr(module, forbidden_name),
            f"P11.6C unexpectedly exposes {forbidden_name}",
        )


def test_documented_stage_boundary() -> None:
    root = repo_root()
    doc = (root / DOC_FILE).read_text(encoding="utf-8")
    for phrase in (
        "P11.6C binds descriptive execution text; it does not execute it",
        "Missing condition means ungated",
        "Present but unbound condition text is rejected",
        "Present but unbound consequence text is rejected",
        "Exact-text binding",
        "NarrativeFactPredicate",
        "NarrativeFactAssignment",
        "AIR expressions are not reused",
        "P11.6B remains unchanged",
        "No condition evaluation",
        "No consequence application",
        "No scene transition",
        "No runtime diagnostics",
        "No CLI routing",
    ):
        require(phrase in doc, f"documentation omitted required phrase: {phrase!r}")


def main() -> None:
    test_baseline_and_ownership()
    test_public_inventory_and_immutability()
    test_predicate_assignment_contracts()
    test_missing_and_bound_semantics()
    test_unbound_rejection()
    test_exact_text_and_duplicate_rejection()
    test_order_and_story_preservation()
    test_runtime_separation_and_stage_boundary()
    test_documented_stage_boundary()

    root = repo_root()
    print("AFP-P11.6C executable condition/consequence binding model smoke test passed.")
    print("Frozen P11.6B predecessor and annotated tag: PASS")
    print("Exact P11.6C ownership and protected-fixture boundary: PASS")
    print("Narrative-specific immutable binding vocabulary: PASS")
    print("Missing condition -> ungated; missing consequence -> no assignments: PASS")
    print("Present unbound condition/consequence rejection: PASS")
    print("Exact-text deterministic binding and order preservation: PASS")
    print("Frozen P11.5 semantic story preservation: PASS")
    print("AIR runtime and P11.6B execution-contract separation: PASS")
    print("No evaluation, application, transition, diagnostics, CLI, or artifact integration: PASS")
    for relative in AUTHORIZED_PATHS:
        path = root / relative
        print(f"{relative} sha256={hashlib.sha256(path.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
