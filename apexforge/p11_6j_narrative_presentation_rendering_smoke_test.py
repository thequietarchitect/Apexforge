"""P11.6J deterministic narrative presentation/rendering smoke test."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
import hashlib
from io import StringIO
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.narrative_model import (
    NarrativeDialogue,
    NarrativeIdentity,
    NarrativeScene,
    NarrativeStateFact,
)
from p11_6i_interactive_narrative_session_ux_smoke_test import (
    make_material,
    require,
    require_raises,
    test_explicit_selection_failure_and_persistence_ordering,
    test_loading_and_deterministic_presentation,
    test_quit_eof_termination_and_already_terminated,
)
from tooling.narrative_interactive import (
    NarrativeInteractiveMenuItem,
    narrative_interactive_menu,
    run_narrative_interactive_session,
)
from tooling.narrative_rendering import (
    NarrativeChoicePresentation,
    NarrativeFactPresentation,
    NarrativeSessionPresentation,
    narrative_session_presentation,
    render_narrative_presentation,
    render_narrative_session,
)
from tooling.narrative_session import (
    NarrativeSessionCreateRequest,
    NarrativeSessionStepRequest,
    NarrativeSessionTerminateRequest,
    create_narrative_session,
    terminate_narrative_session,
)


EXPECTED_BRANCH = "p11.6j-narrative-presentation-rendering"
EXPECTED_PREDECESSOR = "a2c5f8b1ce3f5e9f50632a8a7cdfd3a311e51587"
EXPECTED_TAG = "afp-p11.6i-freeze"
RENDERING_FILE = "apexforge/tooling/narrative_rendering.py"
INTERACTIVE_FILE = "apexforge/tooling/narrative_interactive.py"
EXPORT_FILE = "apexforge/tooling/__init__.py"
THIS_FILE = "apexforge/p11_6j_narrative_presentation_rendering_smoke_test.py"
DOC_FILE = "docs/p11/P11_6J_NARRATIVE_PRESENTATION_RENDERING.md"
AUTHORIZED_PATHS = (
    RENDERING_FILE,
    THIS_FILE,
    DOC_FILE,
    INTERACTIVE_FILE,
    EXPORT_FILE,
)
PROTECTED_FIXTURES = {
    "examples/P11Validation/apexforge.json": (
        "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405"
    ),
    "examples/P11Validation/main.apex": (
        "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
    ),
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(
        completed.returncode == 0,
        f"git {' '.join(arguments)} failed: {completed.stderr.strip()}",
    )
    return completed.stdout.rstrip()


def test_predecessor_ownership_and_protected_fixtures() -> None:
    root = repository_root()
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(git("rev-parse", "HEAD") == EXPECTED_PREDECESSOR, "wrong HEAD")
    require(
        git("rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6I freeze tag does not identify the exact predecessor",
    )
    require(not git("diff", "--cached", "--name-only"), "files are staged")
    status_paths = {
        line[3:].replace("\\", "/")
        for line in git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line
    }
    require(
        status_paths == set(AUTHORIZED_PATHS) | set(PROTECTED_FIXTURES),
        f"unexpected ownership set: {status_paths!r}",
    )
    require(
        set(git("diff", "--name-only", "HEAD").splitlines())
        == {INTERACTIVE_FILE, EXPORT_FILE},
        "tracked production integration ownership changed",
    )
    frozen_drift = set(
        git(
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "apexforge/language",
            "apexforge/runtime",
            "apexforge/tooling/cli.py",
            "apexforge/tooling/narrative_artifact.py",
            "apexforge/tooling/narrative_execution.py",
            "apexforge/tooling/narrative_session.py",
            "editors",
            "examples/P11Validation",
        ).splitlines()
    )
    require(not frozen_drift, f"frozen B-I production changed: {frozen_drift!r}")
    frozen_i_smoke = "apexforge/p11_6i_interactive_narrative_session_ux_smoke_test.py"
    expected_i_bytes = subprocess.run(
        ("git", "show", f"HEAD:{frozen_i_smoke}"),
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    require(
        (root / frozen_i_smoke).read_bytes() == expected_i_bytes,
        "frozen P11.6I smoke bytes changed",
    )
    for relative_path, expected_hash in PROTECTED_FIXTURES.items():
        actual = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        require(actual == expected_hash, f"protected fixture changed: {relative_path}")


def test_structured_and_text_determinism() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        _, _, material, _, _, story = make_material(temporary_root)
        hero = NarrativeIdentity("character", ("Hero",))
        session = create_narrative_session(
            material,
            NarrativeSessionCreateRequest(
                story.identity,
                story.scenes[0].identity,
                (
                    NarrativeStateFact(story.identity, "chapter", "one"),
                    NarrativeStateFact(hero, "ready", "yes"),
                ),
            ),
        )

        first = narrative_session_presentation(material, session)
        first_text = render_narrative_session(material, session)
        with patch.dict(
            os.environ,
            {
                "TZ": "Antarctica/Troll",
                "LANG": "zz_ZZ.invalid",
                "COLUMNS": "7",
                "USER": "different-user",
            },
        ):
            repeated = tuple(
                (
                    narrative_session_presentation(material, session),
                    render_narrative_session(material, session),
                )
                for _ in range(4)
            )
        require(all(model == first for model, _ in repeated),
                "structured presentation varied")
        require(all(text == first_text for _, text in repeated),
                "rendered presentation varied")
        require(all(text.encode("utf-8") == first_text.encode("utf-8")
                    for _, text in repeated), "rendered UTF-8 bytes varied")
        require(type(first) is NarrativeSessionPresentation,
                "structured model is not exact immutable presentation")
        require(all(type(fact) is NarrativeFactPresentation for fact in first.facts),
                "facts were not immutable presentation records")
        require(all(type(choice) is NarrativeChoicePresentation
                    for choice in first.choices),
                "choices were not immutable presentation records")
        require_raises(
            FrozenInstanceError,
            lambda: setattr(first, "status", "terminated"),
            "structured presentation was mutable",
        )

        expected = (
            "ApexForge narrative session\n"
            "Story: story:InteractiveStory\n"
            "Scene: scene:Start\n"
            "Status: active\n"
            "Transitions: 0\n"
            "Facts:\n"
            "  character:Hero:ready=yes\n"
            "  story:InteractiveStory:chapter=one\n"
            "Choices:\n"
            '  1. choice:Alpha path[0] "Continue" -> scene:Middle\n'
            '  2. choice:Alpha path[1] "Finish now" -> scene:End\n'
            '  3. choice:Zeta path[0] "Blocked" -> scene:End\n'
        )
        require(first_text == expected, "exact current-state format changed")
        require(render_narrative_presentation(first) == expected,
                "structured text renderer disagreed with convenience API")
        require(
            tuple(
                (
                    choice.number,
                    choice.choice,
                    choice.path_index,
                    choice.path_label,
                    choice.destination,
                )
                for choice in first.choices
            )
            == (
                (1, story.choices[1].identity, 0, "Continue", story.scenes[1].identity),
                (2, story.choices[1].identity, 1, "Finish now", story.scenes[2].identity),
                (3, story.choices[0].identity, 0, "Blocked", story.scenes[2].identity),
            ),
            "choice identity/index/label/destination projection changed",
        )
        require(
            all(choice.choice != story.choices[2].identity for choice in first.choices),
            "unrelated-scene choice leaked into presentation",
        )


def test_no_semantic_evaluation_or_narration_invention() -> None:
    root = repository_root()
    source = (root / RENDERING_FILE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_modules = {
        "runtime.narrative_transition",
        "random",
        "time",
        "threading",
        "subprocess",
        "socket",
        "urllib",
        "requests",
    }
    imported = set()
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    require(
        not {
            module
            for module in imported
            if module in forbidden_modules
            or any(module.startswith(name + ".") for name in forbidden_modules)
        },
        "renderer imports runtime/autonomy/network authority",
    )
    require(
        not called.intersection(
            {
                "input",
                "print",
                "open",
                "write_narrative_session_atomic",
                "step_narrative_session",
                "terminate_narrative_session",
                "sleep",
            }
        ),
        "renderer calls input/output/lifecycle/timing authority",
    )
    require("RuntimeEngine" not in source, "renderer references AIR runtime")
    require("source_condition" not in source and ".condition" not in source,
            "renderer inspects path conditions")
    require("source_consequence" not in source and ".assignments" not in source,
            "renderer inspects or applies consequences")

    require(tuple(NarrativeScene.__dataclass_fields__) == ("identity",),
            "frozen scene unexpectedly gained presentation prose")
    require(
        tuple(NarrativeDialogue.__dataclass_fields__)
        == ("identity", "scene", "speaker", "participants"),
        "frozen dialogue unexpectedly gained text",
    )
    with TemporaryDirectory() as temporary_name:
        _, _, material, session, _, _ = make_material(Path(temporary_name))
        text = render_narrative_session(material, session)
        require("Blocked" in text, "condition-bearing structural path was hidden")
        require("title" not in text.lower() and "dialogue" not in text.lower(),
                "renderer fabricated absent title/dialogue prose")
        terminated = terminate_narrative_session(
            material,
            session,
            NarrativeSessionTerminateRequest("explicit_outcome"),
        )
        terminated_text = render_narrative_session(material, terminated)
        require(
            terminated_text == render_narrative_session(material, terminated),
            "terminated rendering varied",
        )
        require(
            "Status: terminated\n"
            "Termination reason: explicit_outcome\n" in terminated_text
            and "Choices:\n  (session terminated)\n" in terminated_text,
            "terminated state was not rendered exactly",
        )


def test_i_mapping_and_renderer_input_exclusion() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        _, _, material, session, session_path, _ = make_material(temporary_root)
        menu = narrative_interactive_menu(material, session)
        presentation = narrative_session_presentation(material, session)
        require(
            tuple(
                (item.number, item.choice, item.path_index, item.path_label, item.destination)
                for item in menu
            )
            == tuple(
                (item.number, item.choice, item.path_index, item.path_label, item.destination)
                for item in presentation.choices
            ),
            "I exact selection mapping diverged from displayed J entries",
        )
        require(all(type(item) is NarrativeInteractiveMenuItem for item in menu),
                "I menu contract changed")
        require(
            tuple(item.request for item in menu)
            == tuple(
                NarrativeSessionStepRequest(item.choice, item.path_index)
                for item in presentation.choices
            ),
            "J display changed I exact H requests",
        )

        class ForbiddenInput:
            def readline(self) -> str:
                raise AssertionError("renderer consumed input")

        output = render_narrative_session(material, session)
        require(output.startswith("ApexForge narrative session\n"),
                "pure renderer returned unexpected text")
        with patch("tooling.narrative_interactive.step_narrative_session") as step, patch(
            "tooling.narrative_interactive.terminate_narrative_session"
        ) as terminate, patch(
            "tooling.narrative_interactive.write_narrative_session_atomic"
        ) as write:
            active_input = ForbiddenInput()
            require_raises(
                AssertionError,
                lambda: run_narrative_interactive_session(
                    material,
                    session,
                    session_path,
                    input_stream=active_input,
                    output_stream=StringIO(),
                ),
                "I did not reach its own input boundary",
            )
            require(not step.called and not terminate.called and not write.called,
                    "display caused a lifecycle call")

        terminated = terminate_narrative_session(
            material,
            session,
            NarrativeSessionTerminateRequest("explicit_outcome"),
        )
        terminated_input = StringIO("1\n")
        terminated_output = StringIO()
        with patch(
            "tooling.narrative_interactive.step_narrative_session",
            side_effect=AssertionError("terminated display attempted a step"),
        ), patch(
            "tooling.narrative_interactive.terminate_narrative_session",
            side_effect=AssertionError("terminated display retried termination"),
        ), patch(
            "tooling.narrative_interactive.write_narrative_session_atomic",
            side_effect=AssertionError("terminated display attempted a write"),
        ):
            returned = run_narrative_interactive_session(
                material,
                terminated,
                session_path,
                input_stream=terminated_input,
                output_stream=terminated_output,
            )
        require(returned is terminated, "terminated display replaced the session")
        require(terminated_input.tell() == 0, "terminated display consumed input")
        require(
            terminated_output.getvalue()
            == render_narrative_session(material, terminated)
            + "Session is already terminated; interaction closed.\n",
            "already-terminated I/J presentation changed",
        )


def main_test() -> None:
    test_predecessor_ownership_and_protected_fixtures()
    test_structured_and_text_determinism()
    test_no_semantic_evaluation_or_narration_invention()
    test_i_mapping_and_renderer_input_exclusion()
    test_loading_and_deterministic_presentation()
    test_explicit_selection_failure_and_persistence_ordering()
    test_quit_eof_termination_and_already_terminated()
    print("Frozen P11.6I predecessor, ownership, and fixtures: PASS")
    print("Immutable deterministic structured presentation/text: PASS")
    print("Current scene, facts, path labels, identities, and ordering: PASS")
    print("No semantic evaluation, narration invention, or lifecycle authority: PASS")
    print("P11.6I mapping, failure, persistence, quit/EOF, and termination: PASS")


if __name__ == "__main__":
    main_test()
