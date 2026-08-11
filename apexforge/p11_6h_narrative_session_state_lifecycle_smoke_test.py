"""P11.6H deterministic narrative session/state lifecycle smoke test."""

from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from language.project import build_project
from runtime import narrative_observability
from runtime.engine import RuntimeEngine
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
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
    EXIT_RUNTIME,
    EXIT_SUCCESS,
    EXIT_USAGE,
    main,
)
from tooling.narrative_artifact import route_narrative_build_material
from tooling.narrative_execution import (
    NARRATIVE_EXECUTION_REQUEST_SCHEMA,
    NarrativeExecutionRequest,
    narrative_execution_request_payload,
)
from tooling.narrative_session import (
    NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
    NARRATIVE_SESSION_SCHEMA,
    NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
    NARRATIVE_SESSION_STEP_RESULT_SCHEMA,
    NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
    NarrativeSessionError,
    NarrativeSessionOutputError,
    NarrativeSessionStepRequest,
    create_narrative_session,
    load_narrative_session,
    load_narrative_session_material,
    narrative_session_bytes,
    narrative_session_payload,
    step_narrative_session,
    terminate_narrative_session,
    write_narrative_session_atomic,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6h-narrative-session-state-lifecycle"
EXPECTED_PREDECESSOR = "401990113b539ef4aee5213cdc8d444c49160643"
EXPECTED_TAG = "afp-p11.6g-freeze"
THIS_FILE = (
    "apexforge/p11_6h_narrative_session_state_lifecycle_smoke_test.py"
)
SESSION_FILE = "apexforge/tooling/narrative_session.py"
CLI_FILE = "apexforge/tooling/cli.py"
EXPORT_FILE = "apexforge/tooling/__init__.py"
DOC_FILE = "docs/p11/P11_6H_NARRATIVE_SESSION_STATE_LIFECYCLE.md"
AUTHORIZED_PATHS = (
    THIS_FILE,
    SESSION_FILE,
    CLI_FILE,
    EXPORT_FILE,
    DOC_FILE,
)
PROTECTED_FIXTURE_PATHS = (
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
)
PROTECTED_MAIN_SHA256 = (
    "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
)

NARRATIVE_SOURCE = "\n".join(
    (
        "story SessionStory {",
        "    character Hero",
        "    scene Start",
        "    scene End",
        "    choice Decide {",
        "        scene Start",
        '        path "Continue" {',
        "            destination End",
        "            condition hero_ready",
        "            consequence mark_done",
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


def git(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository_root,
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


def root() -> Path:
    return Path(__file__).resolve().parents[1]


def invoke(arguments: tuple[str, ...]) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def write_json(path: Path, value: dict) -> bytes:
    content = canonical_json_bytes(value)
    path.write_bytes(content)
    return content


def identity_payload(identity: NarrativeIdentity) -> dict:
    return {"kind": identity.kind, "path": list(identity.path)}


def create_request(story, hero, *, ready: bool = True) -> dict:
    return {
        "schema": NARRATIVE_SESSION_CREATE_REQUEST_SCHEMA,
        "story": identity_payload(story.identity),
        "start_scene": identity_payload(story.scenes[0].identity),
        "facts": (
            [
                {
                    "subject": identity_payload(hero),
                    "name": "ready",
                    "value": "yes",
                }
            ]
            if ready
            else []
        ),
    }


def step_request(story, *, path_index: int = 0) -> dict:
    return {
        "schema": NARRATIVE_SESSION_STEP_REQUEST_SCHEMA,
        "choice": identity_payload(story.choices[0].identity),
        "path_index": path_index,
    }


def terminate_request() -> dict:
    return {
        "schema": NARRATIVE_SESSION_TERMINATE_REQUEST_SCHEMA,
        "reason": "explicit_outcome",
    }


def make_material(temporary_root: Path, name: str = "SessionProject"):
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
        source_name="session-story.apex",
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
        consequence_bindings=(
            NarrativeConsequenceBinding(
                "mark_done",
                (NarrativeFactAssignment(hero, "done", "yes"),),
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
    return artifact_path, artifact, story, hero


def create_via_cli(temporary_root: Path, artifact_path, story, hero):
    request_path = temporary_root / "create.json"
    output_path = temporary_root / "session.json"
    write_json(request_path, create_request(story, hero))
    result = invoke(
        (
            "narrative-session",
            "create",
            str(artifact_path),
            "--request",
            str(request_path),
            "--output",
            str(output_path),
        )
    )
    return result, output_path


def test_predecessor_ownership_and_fixture() -> None:
    repository_root = root()
    require(
        git(repository_root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6H is running on an unexpected branch",
    )
    require(
        git(repository_root, "rev-parse", "HEAD") == EXPECTED_PREDECESSOR,
        "candidate no longer rests on the frozen P11.6G predecessor",
    )
    require(
        git(repository_root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6G freeze must be annotated",
    )
    require(
        git(repository_root, "rev-parse", EXPECTED_TAG + "^{}")
        == EXPECTED_PREDECESSOR,
        "P11.6G freeze does not identify the exact predecessor",
    )
    status_paths = {
        line[3:].replace("\\", "/")
        for line in git(
            repository_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if line
    }
    require(
        status_paths == set(AUTHORIZED_PATHS) | set(PROTECTED_FIXTURE_PATHS),
        f"unexpected P11.6H ownership/protected set: {status_paths!r}",
    )
    fixture = repository_root / "examples/P11Validation/main.apex"
    require(
        hashlib.sha256(fixture.read_bytes()).hexdigest()
        == PROTECTED_MAIN_SHA256,
        "protected main.apex changed",
    )


def test_explicit_creation_round_trip_and_association() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact_path, artifact, story, hero = make_material(temporary_root)
        first, session_path = create_via_cli(
            temporary_root, artifact_path, story, hero
        )
        code, stdout, stderr = first
        require(code == EXIT_SUCCESS, "explicit session creation failed")
        require(stderr == "", "session creation wrote stderr")
        require(session_path.read_text(encoding="utf-8") == stdout, "creation output and persisted session differ")
        value = json.loads(stdout)
        require(value["schema"] == NARRATIVE_SESSION_SCHEMA, "session schema changed")
        require(
            value["artifact"]
            == {"algorithm": "sha256", "value": artifact.fingerprint},
            "session lacks exact canonical artifact association",
        )
        require(value["story"] == identity_payload(story.identity), "story identity was not explicit")
        require(value["state"]["current_scene"] == identity_payload(story.scenes[0].identity), "explicit starting scene changed")
        require(value["state"]["progression"] == [identity_payload(story.scenes[0].identity)], "initial progression invariant changed")
        require(value["state"]["choice_history"] == [], "creation invented choice history")
        require(value["state"]["termination"] == {"reason": None, "status": "active"}, "creation inferred termination")
        loaded = load_narrative_session(session_path)
        require(narrative_session_bytes(loaded) == session_path.read_bytes(), "session round trip changed immutable state")
        require(narrative_session_payload(loaded) == value, "session projection changed after load")

        second_path = temporary_root / "session-2.json"
        request_path = temporary_root / "create.json"
        second = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(request_path),
                "--output",
                str(second_path),
            )
        )
        require(first == second, "equivalent creation inputs changed output")
        require(session_path.read_bytes() == second_path.read_bytes(), "equivalent sessions changed deterministic bytes")

        missing_scene = create_request(story, hero)
        del missing_scene["start_scene"]
        missing_path = temporary_root / "missing-scene.json"
        write_json(missing_path, missing_scene)
        missing_output = temporary_root / "missing-output.json"
        missing = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(missing_path),
                "--output",
                str(missing_output),
            )
        )
        require(missing[0] == EXIT_NARRATIVE_SESSION and missing[1] == "", "missing start scene was inferred")
        require("APX-NARRATIVE-232" in missing[2], "missing start scene classification changed")
        require(not missing_output.exists(), "failed creation wrote a session")

        invalid_scene = create_request(story, hero)
        invalid_scene["start_scene"] = {"kind": "scene", "path": ["Other"]}
        invalid_path = temporary_root / "invalid-scene.json"
        write_json(invalid_path, invalid_scene)
        invalid = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(invalid_path),
                "--output",
                str(temporary_root / "invalid-output.json"),
            )
        )
        require(invalid[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-232" in invalid[2], "invalid explicit scene failure changed")

        wrong_story = create_request(story, hero)
        wrong_story["story"] = {"kind": "story", "path": ["Other"]}
        wrong_story_path = temporary_root / "wrong-story.json"
        write_json(wrong_story_path, wrong_story)
        wrong_story_result = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(wrong_story_path),
                "--output",
                str(temporary_root / "wrong-story-output.json"),
            )
        )
        require(wrong_story_result[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-231" in wrong_story_result[2], "explicit story mismatch classification changed")

        malformed_facts = create_request(story, hero)
        malformed_facts["facts"][0]["subject"] = {
            "kind": "character",
            "path": ["Unknown"],
        }
        malformed_facts_path = temporary_root / "malformed-facts.json"
        write_json(malformed_facts_path, malformed_facts)
        malformed_facts_result = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(malformed_facts_path),
                "--output",
                str(temporary_root / "malformed-facts-output.json"),
            )
        )
        require(malformed_facts_result[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-233" in malformed_facts_result[2], "malformed initial-facts classification changed")


def test_strict_loading_and_wrong_artifact_rejection() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact_path, _, story, hero = make_material(temporary_root, "First")
        other_artifact_path, _, _, _ = make_material(temporary_root, "Second")
        _, session_path = create_via_cli(
            temporary_root, artifact_path, story, hero
        )
        session = load_narrative_session(session_path)

        material = load_narrative_session_material(artifact_path)
        other_material = load_narrative_session_material(other_artifact_path)
        request_path = temporary_root / "step.json"
        write_json(request_path, step_request(story))
        wrong_output = temporary_root / "wrong.json"
        wrong = invoke(
            (
                "narrative-session",
                "step",
                str(other_artifact_path),
                str(session_path),
                "--request",
                str(request_path),
                "--output",
                str(wrong_output),
            )
        )
        require(wrong[0] == EXIT_NARRATIVE_SESSION and wrong[1] == "", "wrong artifact was accepted")
        require("APX-NARRATIVE-230" in wrong[2], "fingerprint mismatch classification changed")
        require(not wrong_output.exists(), "wrong association persisted state")
        error = require_raises(
            NarrativeSessionError,
            lambda: step_narrative_session(
                other_material,
                session,
                NarrativeSessionStepRequest(story.choices[0].identity, 0),
            ),
            "public lifecycle accepted a wrong artifact",
        )
        require(error.classification == "artifact_mismatch", "public mismatch classification changed")
        require(material.artifact_fingerprint == session.artifact_fingerprint, "canonical association did not round trip")

        malformed = temporary_root / "malformed.json"
        malformed.write_bytes(b"{\n")
        malformed_result = invoke(
            (
                "narrative-session",
                "step",
                str(artifact_path),
                str(malformed),
                "--request",
                str(request_path),
                "--output",
                str(temporary_root / "malformed-output.json"),
            )
        )
        require(malformed_result[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-211" in malformed_result[2], "malformed session classification changed")

        duplicate = temporary_root / "duplicate.json"
        duplicate.write_text('{"schema":"x","schema":"y"}\n', encoding="utf-8")
        duplicate_error = require_raises(
            NarrativeSessionError,
            lambda: load_narrative_session(duplicate),
            "duplicate session key was accepted",
        )
        require(duplicate_error.classification == "malformed_session", "duplicate-key policy changed")

        noncanonical = temporary_root / "noncanonical.json"
        noncanonical.write_text(json.dumps(json.loads(session_path.read_text(encoding="utf-8"))), encoding="utf-8")
        noncanonical_error = require_raises(
            NarrativeSessionError,
            lambda: load_narrative_session(noncanonical),
            "noncanonical session was accepted",
        )
        require(noncanonical_error.classification == "malformed_session", "noncanonical policy changed")

        unavailable_session = invoke(
            (
                "narrative-session",
                "step",
                str(artifact_path),
                str(temporary_root / "unavailable-session.json"),
                "--request",
                str(request_path),
                "--output",
                str(temporary_root / "unavailable-session-output.json"),
            )
        )
        require(unavailable_session[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-210" in unavailable_session[2], "unavailable session classification changed")
        unavailable_artifact = invoke(
            (
                "narrative-session",
                "step",
                str(temporary_root / "unavailable-artifact.json"),
                str(session_path),
                "--request",
                str(request_path),
                "--output",
                str(temporary_root / "unavailable-artifact-output.json"),
            )
        )
        require(unavailable_artifact[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-220" in unavailable_artifact[2], "unavailable build classification changed")


def test_one_step_delegation_success_and_fail_closed_state() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact_path, artifact, story, hero = make_material(temporary_root)
        _, session_path = create_via_cli(
            temporary_root, artifact_path, story, hero
        )
        session_before_bytes = session_path.read_bytes()
        session = load_narrative_session(session_path)
        material = load_narrative_session_material(artifact_path)

        calls = {"p11_6e": 0, "p11_6d": 0}
        original_execute = narrative_observability.execute_narrative_choice
        original_transition = narrative_observability.transition_narrative_choice
        original_air_execute = RuntimeEngine.execute

        def recording_transition(*arguments, **keywords):
            calls["p11_6d"] += 1
            return original_transition(*arguments, **keywords)

        def recording_execute(*arguments, **keywords):
            calls["p11_6e"] += 1
            return original_execute(*arguments, **keywords)

        def forbidden_air_execute(*arguments, **keywords):
            raise AssertionError("narrative session step used AIR RuntimeEngine")

        narrative_observability.transition_narrative_choice = recording_transition
        narrative_observability.execute_narrative_choice = recording_execute
        RuntimeEngine.execute = forbidden_air_execute
        try:
            result = step_narrative_session(
                material,
                session,
                NarrativeSessionStepRequest(story.choices[0].identity, 0),
            )
        finally:
            narrative_observability.transition_narrative_choice = original_transition
            narrative_observability.execute_narrative_choice = original_execute
            RuntimeEngine.execute = original_air_execute
        require(calls == {"p11_6e": 1, "p11_6d": 1}, "step did not delegate once through G/E/D")
        require(result.execution_result.ok and result.session is not None, "valid explicit step failed")
        require(result.session.state.current_scene == story.scenes[1].identity, "next session scene changed")
        require(session.state.current_scene == story.scenes[0].identity, "step mutated prior session")
        require(session_path.read_bytes() == session_before_bytes, "API step mutated persisted prior session")
        require(artifact_path.read_bytes() == artifact.content, "step mutated canonical artifact")
        require(not result.session.state.termination.is_terminated, "destination graph shape inferred termination")

        failed_create = create_request(story, hero, ready=False)
        failed_create_path = temporary_root / "failed-create.json"
        failed_session_path = temporary_root / "failed-session.json"
        write_json(failed_create_path, failed_create)
        create_result = invoke(
            (
                "narrative-session",
                "create",
                str(artifact_path),
                "--request",
                str(failed_create_path),
                "--output",
                str(failed_session_path),
            )
        )
        require(create_result[0] == EXIT_SUCCESS, "fact-free session creation failed")
        failed_before = failed_session_path.read_bytes()
        request_path = temporary_root / "step.json"
        write_json(request_path, step_request(story))
        failed_output = temporary_root / "failed-output.json"
        failed_output.write_bytes(b"prior-valid-session")
        failed_step = invoke(
            (
                "narrative-session",
                "step",
                str(artifact_path),
                str(failed_session_path),
                "--request",
                str(request_path),
                "--output",
                str(failed_output),
            )
        )
        require(failed_step[0] == EXIT_RUNTIME and failed_step[2] == "", "condition failure routing changed")
        failed_value = json.loads(failed_step[1])
        require(failed_value["schema"] == NARRATIVE_SESSION_STEP_RESULT_SCHEMA, "step output schema changed")
        require(failed_value["execution"]["diagnostics"][0]["code"] == "NARRATIVE_TRANSITION_CONDITION_UNSATISFIED", "P11.6E diagnostic was hidden")
        require(failed_value["execution"]["initial_state"] == failed_value["execution"]["final_state"], "failed transition advanced state")
        require(failed_value["session"] is None, "failed transition invented next session")
        require(failed_session_path.read_bytes() == failed_before, "failed transition mutated prior session")
        require(failed_output.read_bytes() == b"prior-valid-session", "failed transition overwrote output")

        for field_name in ("choice", "path_index"):
            incomplete = step_request(story)
            del incomplete[field_name]
            incomplete_path = temporary_root / f"missing-{field_name}.json"
            write_json(incomplete_path, incomplete)
            incomplete_output = temporary_root / f"missing-{field_name}-output.json"
            incomplete_result = invoke(
                (
                    "narrative-session",
                    "step",
                    str(artifact_path),
                    str(session_path),
                    "--request",
                    str(incomplete_path),
                    "--output",
                    str(incomplete_output),
                )
            )
            require(incomplete_result[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-200" in incomplete_result[2], f"missing explicit {field_name} was inferred")
            require(not incomplete_output.exists(), f"missing {field_name} wrote a next session")


def test_explicit_termination_and_terminated_step() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact_path, _, story, hero = make_material(temporary_root)
        _, session_path = create_via_cli(
            temporary_root, artifact_path, story, hero
        )
        terminate_path = temporary_root / "terminate.json"
        terminated_path = temporary_root / "terminated-session.json"
        write_json(terminate_path, terminate_request())
        calls = {"terminate": 0}
        original_terminate = narrative_observability.terminate_narrative

        def recording_terminate(*arguments, **keywords):
            calls["terminate"] += 1
            return original_terminate(*arguments, **keywords)

        narrative_observability.terminate_narrative = recording_terminate
        try:
            terminated = invoke(
                (
                    "narrative-session",
                    "terminate",
                    str(artifact_path),
                    str(session_path),
                    "--request",
                    str(terminate_path),
                    "--output",
                    str(terminated_path),
                )
            )
        finally:
            narrative_observability.terminate_narrative = original_terminate
        require(terminated[0] == EXIT_SUCCESS and terminated[2] == "", "explicit termination failed")
        require(calls["terminate"] == 1, "termination did not delegate once to P11.6E")
        terminated_value = json.loads(terminated[1])
        require(terminated_value["state"]["termination"] == {"reason": "explicit_outcome", "status": "terminated"}, "terminated state changed")
        require(json.loads(session_path.read_text(encoding="utf-8"))["state"]["termination"]["status"] == "active", "termination mutated prior session")

        step_path = temporary_root / "step.json"
        write_json(step_path, step_request(story))
        terminated_output = temporary_root / "terminated-output.json"
        rejected = invoke(
            (
                "narrative-session",
                "step",
                str(artifact_path),
                str(terminated_path),
                "--request",
                str(step_path),
                "--output",
                str(terminated_output),
            )
        )
        require(rejected[0] == EXIT_RUNTIME and rejected[2] == "", "terminated step routing changed")
        rejected_value = json.loads(rejected[1])
        require(rejected_value["execution"]["diagnostics"][0]["code"] == "NARRATIVE_EXECUTION_TERMINATED", "terminated-state P11.6E diagnostic was replaced")
        require(rejected_value["session"] is None and not terminated_output.exists(), "terminated step advanced state")

        again = invoke(
            (
                "narrative-session",
                "terminate",
                str(artifact_path),
                str(terminated_path),
                "--request",
                str(terminate_path),
                "--output",
                str(temporary_root / "again.json"),
            )
        )
        require(again[0] == EXIT_NARRATIVE_SESSION and "APX-NARRATIVE-240" in again[2], "repeat termination silently succeeded")


def test_atomic_write_and_historical_compatibility() -> None:
    import tooling.narrative_session as session_module

    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact_path, _, story, hero = make_material(temporary_root)
        _, session_path = create_via_cli(
            temporary_root, artifact_path, story, hero
        )
        session = load_narrative_session(session_path)
        output = temporary_root / "replace.json"
        output.write_bytes(b"valid-prior")
        original_replace = session_module.os.replace

        def fail_replace(source, destination):
            raise OSError("synthetic replacement failure")

        session_module.os.replace = fail_replace
        try:
            error = require_raises(
                NarrativeSessionOutputError,
                lambda: write_narrative_session_atomic(session, output),
                "atomic replacement failure was swallowed",
            )
        finally:
            session_module.os.replace = original_replace
        require("APX-NARRATIVE-250" in str(error), "session output classification changed")
        require(output.read_bytes() == b"valid-prior", "failed write damaged prior session")
        require(not tuple(temporary_root.glob(".replace.json.*.tmp")), "failed write left temporary residue")

        serialization_output = temporary_root / "serialization.json"
        serialization_output.write_bytes(b"serialized-prior")
        original_serializer = session_module.canonical_json_bytes

        def fail_serialization(value):
            raise ValueError("synthetic serialization failure")

        session_module.canonical_json_bytes = fail_serialization
        try:
            serialization_error = require_raises(
                NarrativeSessionOutputError,
                lambda: write_narrative_session_atomic(
                    session, serialization_output
                ),
                "session serialization failure was swallowed",
            )
        finally:
            session_module.canonical_json_bytes = original_serializer
        require("APX-NARRATIVE-250" in str(serialization_error), "serialization output classification changed")
        require(serialization_output.read_bytes() == b"serialized-prior", "serialization failure damaged prior session")
        require(not tuple(temporary_root.glob(".serialization.json.*.tmp")), "serialization failure left temporary residue")

        fixture = root() / "apexforge/fixtures/p11_1b/single_fallback"
        original_narrative_execute = narrative_observability.execute_narrative_choice
        narrative_calls = {"count": 0}

        def forbidden_narrative(*arguments, **keywords):
            narrative_calls["count"] += 1
            raise AssertionError("historical command activated narrative execution")

        narrative_observability.execute_narrative_choice = forbidden_narrative
        try:
            run_result = invoke(("run", str(fixture)))
            build_path = temporary_root / "historical.json"
            build_result = invoke(
                ("build", str(fixture), "--output", str(build_path))
            )
        finally:
            narrative_observability.execute_narrative_choice = original_narrative_execute
        require(run_result[0] == EXIT_SUCCESS and run_result[2] == "", "historical AIR run changed")
        require(build_result[0] == EXIT_SUCCESS and build_result[2] == "", "historical build changed")
        require("narrative" not in json.loads(build_path.read_text(encoding="utf-8")), "historical build gained narrative state")
        require(narrative_calls["count"] == 0, "historical commands activated narrative route")

        one_shot_path = temporary_root / "one-shot.json"
        one_shot = NarrativeExecutionRequest(
            state=session.state,
            choice=story.choices[0].identity,
            path_index=0,
        )
        one_shot_value = narrative_execution_request_payload(one_shot)
        require(one_shot_value["schema"] == NARRATIVE_EXECUTION_REQUEST_SCHEMA, "P11.6G request schema changed")
        write_json(one_shot_path, one_shot_value)
        one_shot_result = invoke(
            ("narrative", str(artifact_path), "--request", str(one_shot_path))
        )
        require(one_shot_result[0] == EXIT_SUCCESS and json.loads(one_shot_result[1])["ok"] is True, "P11.6G one-shot route changed")
        narrative_value = json.loads(artifact_path.read_text(encoding="utf-8"))[
            "narrative"
        ]
        for runtime_field in (
            "state",
            "session",
            "progression",
            "choice_history",
            "termination",
            "trace",
            "diagnostics",
        ):
            require(runtime_field not in narrative_value, f"P11.6F artifact gained runtime field {runtime_field!r}")


def test_boundaries_and_cli_shape() -> None:
    repository_root = root()
    text = (repository_root / SESSION_FILE).read_text(encoding="utf-8")
    cli_text = (repository_root / CLI_FILE).read_text(encoding="utf-8")
    for forbidden in (
        "RuntimeEngine",
        "input(",
        "sys.stdin",
        "while ",
        "analyze_narrative_source",
        "parse_narrative_source",
        "bind_narrative_story",
        "transition_narrative_choice(",
    ):
        require(forbidden not in text, f"session lifecycle crossed boundary via {forbidden!r}")
    require("execute_narrative_request(" in text, "session step bypasses P11.6G")
    require("terminate_narrative(" in text, "session termination bypasses P11.6E")
    require('commands.add_parser(\n        "narrative"' in cli_text, "P11.6G command disappeared")
    require('commands.add_parser(\n        "narrative-session"' in cli_text, "session namespace is unavailable")
    for action in ("create", "step", "terminate"):
        require(f'("{action}",' in cli_text, f"session action {action!r} is unavailable")
    require("narrative_artifact=" not in text, "runtime state was inserted into P11.6F build construction")
    usage = invoke(("narrative-session",))
    require(usage[0] == EXIT_USAGE and usage[1] == "", "omitted lifecycle action did not produce usage failure")


def main_test() -> None:
    test_predecessor_ownership_and_fixture()
    test_explicit_creation_round_trip_and_association()
    test_strict_loading_and_wrong_artifact_rejection()
    test_one_step_delegation_success_and_fail_closed_state()
    test_explicit_termination_and_terminated_step()
    test_atomic_write_and_historical_compatibility()
    test_boundaries_and_cli_shape()
    print("AFP-P11.6H narrative session/state lifecycle smoke test passed.")
    print("Frozen P11.6G predecessor, exact ownership, and fixture: PASS")
    print("Explicit initialization, artifact association, and round trip: PASS")
    print("Strict deterministic persistence and atomic replacement: PASS")
    print("One-step P11.6G/P11.6E/P11.6D delegation and immutability: PASS")
    print("Explicit P11.6E termination and terminated-state rejection: PASS")
    print("Historical AIR run/build and P11.6G one-shot compatibility: PASS")
    print("No inference, loop, prompt, AIR reuse, or graph termination: PASS")


if __name__ == "__main__":
    main_test()
