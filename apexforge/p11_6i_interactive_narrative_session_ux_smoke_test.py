"""P11.6I deterministic interactive narrative session UX smoke test."""

from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import NarrativeIdentity
from language.project import build_project
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from tooling.build_artifact import (
    canonical_json_bytes,
    construct_build_artifact,
    write_build_artifact_atomic,
)
from tooling.cli import (
    EXIT_NARRATIVE_SESSION,
    EXIT_SUCCESS,
    main,
)
from tooling.narrative_artifact import route_narrative_build_material
from tooling.narrative_execution import (
    NarrativeExecutionRequest,
    narrative_execution_request_payload,
)
from tooling.narrative_interactive import (
    INTERACTIVE_TERMINATION_REASON,
    NarrativeInteractiveMenuItem,
    interact_narrative_session,
    narrative_interactive_menu,
    run_narrative_interactive_session,
)
from tooling.narrative_session import (
    NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
    NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
    NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
    NarrativeSessionCreateRequest,
    NarrativeSessionOutputError,
    NarrativeSessionStepRequest,
    create_narrative_session,
    load_narrative_session,
    load_narrative_session_material,
    step_narrative_session,
    terminate_narrative_session,
    write_narrative_session_atomic,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6i-interactive-narrative-session-ux"
EXPECTED_PREDECESSOR = "c3557f817bf4c46d579d4dfc2498e620c7967e0a"
EXPECTED_TAG = "afp-p11.6h-freeze"
INTERACTIVE_FILE = "apexforge/tooling/narrative_interactive.py"
THIS_FILE = "apexforge/p11_6i_interactive_narrative_session_ux_smoke_test.py"
CLI_FILE = "apexforge/tooling/cli.py"
EXPORT_FILE = "apexforge/tooling/__init__.py"
DOC_FILE = "docs/p11/P11_6I_INTERACTIVE_NARRATIVE_SESSION_UX.md"
AUTHORIZED_PATHS = (
    INTERACTIVE_FILE,
    THIS_FILE,
    CLI_FILE,
    EXPORT_FILE,
    DOC_FILE,
)
PROTECTED_FIXTURES = {
    "examples/P11Validation/apexforge.json": (
        "8154bdc7668b7ba7979557e27db8c97ea945b3ca8993d7b0230fb3c550463405"
    ),
    "examples/P11Validation/main.apex": (
        "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
    ),
}

NARRATIVE_SOURCE = "\n".join(
    (
        "story InteractiveStory {",
        "    character Hero",
        "    scene Start",
        "    scene Middle",
        "    scene End",
        "    choice Zeta {",
        "        scene Start",
        '        path "Blocked" {',
        "            destination End",
        "            condition hero_ready",
        "        }",
        "    }",
        "    choice Alpha {",
        "        scene Start",
        '        path "Continue" {',
        "            destination Middle",
        "        }",
        '        path "Finish now" {',
        "            destination End",
        "        }",
        "    }",
        "    choice MiddleChoice {",
        "        scene Middle",
        '        path "Finish" {',
        "            destination End",
        "        }",
        "    }",
        "}",
    )
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(exc_type, operation, message: str):
    try:
        operation()
    except exc_type as exc:
        return exc
    raise AssertionError(message)


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


def invoke(
    arguments: tuple[str, ...],
    *,
    stdin_text: str = "",
) -> tuple[int, str, str]:
    stdin = StringIO(stdin_text)
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdin=stdin, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def identity_payload(identity: NarrativeIdentity) -> dict:
    return {"kind": identity.kind, "path": list(identity.path)}


def write_json(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json_bytes(value))


def make_material(temporary_root: Path, name: str = "InteractiveProject"):
    project_root = temporary_root / name
    source_path = project_root / "src" / "main.apex"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("directive Main {}\n", encoding="utf-8")
    (project_root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": ["src/main.apex"],
                "entry": "Main",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = load_project(project_root)
    build = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
    analysis = analyze_narrative_source(
        NARRATIVE_SOURCE,
        source_name="interactive-story.apex",
    )
    story = analysis.semantic_story
    hero = NarrativeIdentity("character", ("Hero",))
    bindings = bind_narrative_story(
        story,
        condition_bindings=(
            NarrativeConditionBinding(
                "hero_ready",
                NarrativeFactPredicate(hero, "ready", "equals", "yes"),
            ),
        ),
    )
    narrative = route_narrative_build_material(analysis, bindings)
    artifact = construct_build_artifact(
        loaded,
        build,
        narrative_artifact=narrative,
    )
    artifact_path = temporary_root / f"{name}.json"
    write_build_artifact_atomic(artifact, artifact_path)
    material = load_narrative_session_material(artifact_path)
    session = create_narrative_session(
        material,
        NarrativeSessionCreateRequest(
            story.identity,
            story.scenes[0].identity,
        ),
    )
    session_path = temporary_root / f"{name}.session.json"
    write_narrative_session_atomic(session, session_path)
    return project_root, artifact_path, material, session, session_path, story


def test_predecessor_ownership_and_protected_fixtures() -> None:
    root = repository_root()
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "wrong branch")
    require(git("rev-parse", "HEAD") == EXPECTED_PREDECESSOR, "wrong HEAD")
    require(
        git("rev-parse", EXPECTED_TAG + "^{}") == EXPECTED_PREDECESSOR,
        "P11.6H freeze tag does not identify the exact predecessor",
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
    changed_frozen = set(
        git(
            "diff",
            "--name-only",
            "HEAD",
            "--",
            "apexforge/runtime",
            "apexforge/language",
            "apexforge/tooling/narrative_session.py",
            "apexforge/tooling/narrative_execution.py",
            "apexforge/tooling/narrative_artifact.py",
            "editors",
            "examples/P11Validation",
        ).splitlines()
    )
    require(not changed_frozen, f"frozen production changed: {changed_frozen!r}")
    for relative_path, expected_hash in PROTECTED_FIXTURES.items():
        actual = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
        require(actual == expected_hash, f"protected fixture changed: {relative_path}")


def test_loading_and_deterministic_presentation() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        _, artifact_path, material, session, session_path, story = make_material(
            temporary_root
        )
        loaded = load_narrative_session(session_path)
        require(loaded == session, "valid H session did not load exactly")
        menu = narrative_interactive_menu(material, loaded)
        require(
            tuple((item.number, item.choice.path[-1], item.path_index) for item in menu)
            == ((1, "Alpha", 0), (2, "Alpha", 1), (3, "Zeta", 0)),
            "menu did not use canonical choice identity/path index order",
        )
        require(
            all(type(item) is NarrativeInteractiveMenuItem for item in menu),
            "menu records are not exact immutable menu items",
        )
        require(menu[0].request == NarrativeSessionStepRequest(menu[0].choice, 0),
                "menu number did not map to its exact choice/path request")
        require(
            all(item.choice != story.choices[2].identity for item in menu),
            "unrelated-scene choice leaked into the current menu",
        )

        output = StringIO()
        returned = run_narrative_interactive_session(
            material,
            session,
            session_path,
            input_stream=StringIO("quit\n"),
            output_stream=output,
        )
        expected_prefix = (
            "ApexForge narrative session\n"
            "Story: story:InteractiveStory\n"
            "Scene: scene:Start\n"
            "Status: active\n"
            "Transitions: 0\n"
            "Facts:\n"
            "  (none)\n"
            "Choices:\n"
            '  1. choice:Alpha path[0] "Continue" -> scene:Middle\n'
            '  2. choice:Alpha path[1] "Finish now" -> scene:End\n'
            '  3. choice:Zeta path[0] "Blocked" -> scene:End\n'
        )
        require(output.getvalue().startswith(expected_prefix), "state/menu output changed")
        require(returned is session, "quit replaced the immutable current session")

        _, wrong_artifact, _, _, _, _ = make_material(temporary_root, "OtherProject")
        code, wrong_out, wrong_err = invoke(
            ("narrative-session", "interact", str(wrong_artifact), str(session_path)),
            stdin_text="1\n",
        )
        require(code == EXIT_NARRATIVE_SESSION, "wrong artifact did not fail closed")
        require("APX-NARRATIVE-230" in wrong_err and not wrong_out,
                "wrong artifact failure was not stable")

        malformed = temporary_root / "malformed.session.json"
        malformed.write_text("{}\n", encoding="utf-8")
        code, _, error = invoke(
            ("narrative-session", "interact", str(artifact_path), str(malformed))
        )
        require(code == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-211" in error,
                "malformed session did not fail closed")
        missing = temporary_root / "missing.session.json"
        code, _, error = invoke(
            ("narrative-session", "interact", str(artifact_path), str(missing))
        )
        require(code == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-210" in error,
                "missing session was not rejected")
        require(not missing.exists(), "interaction automatically created a session")


def test_explicit_selection_failure_and_persistence_ordering() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        _, _, material, session, session_path, _ = make_material(temporary_root)
        original_bytes = session_path.read_bytes()
        events = []
        real_step = step_narrative_session
        real_write = write_narrative_session_atomic

        class OrderingOutput(StringIO):
            def write(self, value: str) -> int:
                if "Scene: scene:Middle" in value:
                    require(events[-1][0] == "write", "new state shown before persistence")
                return super().write(value)

        def recording_step(actual_material, actual_session, request):
            events.append(("step", request.choice.path[-1], request.path_index))
            return real_step(actual_material, actual_session, request)

        def recording_write(next_session, path):
            events.append(("write", next_session.state.current_scene.path[-1]))
            real_write(next_session, path)

        with patch("tooling.narrative_interactive.step_narrative_session", recording_step), patch(
            "tooling.narrative_interactive.write_narrative_session_atomic",
            recording_write,
        ):
            result = run_narrative_interactive_session(
                material,
                session,
                session_path,
                input_stream=StringIO("invalid\n0\n1\nquit\n"),
                output_stream=OrderingOutput(),
            )
        require(events == [("step", "Alpha", 0), ("write", "Middle")],
                f"selection delegation/write ordering changed: {events!r}")
        require(result.state.current_scene.path[-1] == "Middle", "success not adopted")
        require(load_narrative_session(session_path) == result,
                "successful state was not atomically persisted")
        require(session_path.read_bytes() != original_bytes, "successful step did not write")

        failure_calls = []
        before_failure = session_path.read_bytes()

        def failure_step(actual_material, actual_session, request):
            failure_calls.append((request.choice.path[-1], request.path_index))
            return real_step(actual_material, actual_session, request)

        def forbidden_write(*_arguments):
            raise AssertionError("failed semantic step attempted a session write")

        with patch("tooling.narrative_interactive.step_narrative_session", failure_step), patch(
            "tooling.narrative_interactive.write_narrative_session_atomic",
            forbidden_write,
        ):
            failure_output = StringIO()
            failure_result = run_narrative_interactive_session(
                material,
                session,
                session_path,
                input_stream=StringIO("3\nquit\n"),
                output_stream=failure_output,
            )
        require(failure_calls == [("Zeta", 0)], "failed path was retried or remapped")
        require(failure_result is session, "semantic failure mutated current state")
        require(session_path.read_bytes() == before_failure, "semantic failure rewrote session")
        require("NARRATIVE_TRANSITION_CONDITION_UNSATISFIED" in failure_output.getvalue(),
                "authoritative condition diagnostic was not preserved")

        def failed_persistence(*_arguments):
            raise NarrativeSessionOutputError("expected persistence failure")

        with patch(
            "tooling.narrative_interactive.write_narrative_session_atomic",
            failed_persistence,
        ):
            require_raises(
                NarrativeSessionOutputError,
                lambda: run_narrative_interactive_session(
                    material,
                    session,
                    session_path,
                    input_stream=StringIO("1\n2\n"),
                    output_stream=StringIO(),
                ),
                "persistence failure did not stop interaction",
            )
        require(session_path.read_bytes() == before_failure,
                "persistence failure changed the prior persisted session")


def test_quit_eof_termination_and_already_terminated() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        _, artifact_path, material, session, session_path, _ = make_material(
            temporary_root
        )
        original = session_path.read_bytes()
        for input_text in ("quit\n", ""):
            with patch(
                "tooling.narrative_interactive.step_narrative_session",
                side_effect=AssertionError("quit/EOF attempted a step"),
            ), patch(
                "tooling.narrative_interactive.terminate_narrative_session",
                side_effect=AssertionError("quit/EOF attempted termination"),
            ), patch(
                "tooling.narrative_interactive.write_narrative_session_atomic",
                side_effect=AssertionError("quit/EOF attempted a write"),
            ):
                run_narrative_interactive_session(
                    material,
                    session,
                    session_path,
                    input_stream=StringIO(input_text),
                    output_stream=StringIO(),
                )
        require(session_path.read_bytes() == original, "quit/EOF changed persistence")

        events = []
        real_terminate = terminate_narrative_session
        real_write = write_narrative_session_atomic

        def recording_terminate(actual_material, actual_session, request):
            events.append(("terminate", request.reason))
            return real_terminate(actual_material, actual_session, request)

        def recording_write(next_session, path):
            events.append(("write", next_session.state.termination.status))
            real_write(next_session, path)

        with patch(
            "tooling.narrative_interactive.terminate_narrative_session",
            recording_terminate,
        ), patch(
            "tooling.narrative_interactive.write_narrative_session_atomic",
            recording_write,
        ), patch(
            "tooling.narrative_interactive.step_narrative_session",
            side_effect=AssertionError("termination invocation attempted a later step"),
        ):
            terminated = run_narrative_interactive_session(
                material,
                session,
                session_path,
                input_stream=StringIO("terminate\n1\n"),
                output_stream=StringIO(),
            )
        require(events == [("terminate", INTERACTIVE_TERMINATION_REASON),
                           ("write", "terminated")],
                f"termination delegation changed: {events!r}")
        require(terminated.state.termination.is_terminated, "termination not adopted")
        require(load_narrative_session(session_path) == terminated,
                "termination was not persisted atomically")

        terminated_input = StringIO("1\n")
        with patch(
            "tooling.narrative_interactive.step_narrative_session",
            side_effect=AssertionError("terminated session was revived"),
        ), patch(
            "tooling.narrative_interactive.terminate_narrative_session",
            side_effect=AssertionError("terminated session was re-terminated"),
        ):
            returned = interact_narrative_session(
                artifact_path,
                session_path,
                input_stream=terminated_input,
                output_stream=StringIO(),
            )
        require(returned == terminated, "already-terminated session changed")
        require(terminated_input.tell() == 0, "terminated session consumed input")


def test_cli_and_historical_routes() -> None:
    with TemporaryDirectory() as temporary_name:
        temporary_root = Path(temporary_name)
        project_root, artifact_path, material, session, session_path, story = make_material(
            temporary_root
        )
        code, output, error = invoke(
            ("narrative-session", "interact", str(artifact_path), str(session_path)),
            stdin_text="1\nquit\n",
        )
        require(code == EXIT_SUCCESS and not error, "interactive CLI route failed")
        require("Scene: scene:Middle" in output, "interactive CLI did not show next state")

        code, output, error = invoke(("run", str(project_root)))
        require(code == EXIT_SUCCESS and "ApexForge run succeeded:" in output and not error,
                "historical AIR run route changed")
        build_output = temporary_root / "historical-build.json"
        code, output, error = invoke(
            ("build", str(project_root), "--output", str(build_output))
        )
        require(code == EXIT_SUCCESS and build_output.exists() and not error,
                "historical build route changed")

        one_shot = temporary_root / "one-shot.json"
        write_json(
            one_shot,
            narrative_execution_request_payload(
                NarrativeExecutionRequest(
                    session.state,
                    story.choices[1].identity,
                    0,
                )
            ),
        )
        code, output, error = invoke(
            ("narrative", str(artifact_path), "--request", str(one_shot))
        )
        require(code == EXIT_SUCCESS and '"ok": true' in output and not error,
                "P11.6G one-shot route changed")

        create_request = temporary_root / "create.json"
        created_session = temporary_root / "created.json"
        write_json(
            create_request,
            {
                "schema": NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
                "story": identity_payload(story.identity),
                "start_scene": identity_payload(story.scenes[0].identity),
                "facts": [],
            },
        )
        code, _, error = invoke(
            (
                "narrative-session", "create", str(artifact_path),
                "--request", str(create_request), "--output", str(created_session),
            )
        )
        require(code == EXIT_SUCCESS and created_session.exists() and not error,
                "P11.6H create route changed")

        step_request = temporary_root / "step.json"
        stepped_session = temporary_root / "stepped.json"
        write_json(
            step_request,
            {
                "schema": NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
                "choice": identity_payload(story.choices[1].identity),
                "path_index": 0,
            },
        )
        code, _, error = invoke(
            (
                "narrative-session", "step", str(artifact_path), str(created_session),
                "--request", str(step_request), "--output", str(stepped_session),
            )
        )
        require(code == EXIT_SUCCESS and stepped_session.exists() and not error,
                "P11.6H step route changed")

        terminate_request = temporary_root / "terminate.json"
        terminated_session = temporary_root / "terminated.json"
        write_json(
            terminate_request,
            {
                "schema": NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
                "reason": INTERACTIVE_TERMINATION_REASON,
            },
        )
        code, _, error = invoke(
            (
                "narrative-session", "terminate", str(artifact_path),
                str(stepped_session), "--request", str(terminate_request),
                "--output", str(terminated_session),
            )
        )
        require(code == EXIT_SUCCESS and terminated_session.exists() and not error,
                "P11.6H terminate route changed")

        failed_step = step_narrative_session(
            material,
            session,
            NarrativeSessionStepRequest(story.choices[0].identity, 0),
        )
        require(not failed_step.execution_result.ok and failed_step.session is None,
                "condition-unsatisfied H result changed")


def test_no_autonomy_or_authority_expansion() -> None:
    root = repository_root()
    source = (root / INTERACTIVE_FILE).read_text(encoding="utf-8")
    forbidden = (
        "runtime.narrative_transition",
        "RuntimeEngine",
        "random.",
        "import random",
        "threading",
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "http.client",
        "sleep(",
        "input(",
        "print(",
    )
    require(not [term for term in forbidden if term in source],
            "interactive module gained autonomous/runtime/network behavior")
    require("step_narrative_session(" in source,
            "P11.6H step delegation disappeared")
    require("write_narrative_session_atomic(" in source,
            "P11.6H persistence delegation disappeared")
    require("terminate_narrative_session(" in source,
            "P11.6H termination delegation disappeared")
    require("source_condition" not in source and ".condition" not in source,
            "interactive module inspects semantic path conditions")
    require("source_consequence" not in source and ".assignments" not in source,
            "interactive module applies or inspects consequences")


def main_test() -> None:
    test_predecessor_ownership_and_protected_fixtures()
    test_loading_and_deterministic_presentation()
    test_explicit_selection_failure_and_persistence_ordering()
    test_quit_eof_termination_and_already_terminated()
    test_cli_and_historical_routes()
    test_no_autonomy_or_authority_expansion()
    print("Frozen P11.6H predecessor, ownership, and fixtures: PASS")
    print("Existing-session loading and artifact association: PASS")
    print("Deterministic structural presentation and exact menu mapping: PASS")
    print("Explicit single-step delegation and persistence ordering: PASS")
    print("Failure immutability, quit, EOF, and termination behavior: PASS")
    print("Historical AIR/build/P11.6G/P11.6H routes: PASS")
    print("No autonomous selection, semantic duplication, or runtime expansion: PASS")


if __name__ == "__main__":
    main_test()
