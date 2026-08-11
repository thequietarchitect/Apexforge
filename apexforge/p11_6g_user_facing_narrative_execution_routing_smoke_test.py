"""P11.6G user-facing narrative execution routing smoke test."""

from __future__ import annotations

import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Optional

from language.narrative_analysis import analyze_narrative_source
from language.narrative_model import NarrativeIdentity, NarrativeStateFact
from language.project import ProjectBuild, build_project
from runtime import narrative_observability
from runtime.engine import RuntimeEngine
from runtime.narrative_binding import (
    NarrativeConditionBinding,
    NarrativeConsequenceBinding,
    NarrativeFactAssignment,
    NarrativeFactPredicate,
    bind_narrative_story,
)
from runtime.narrative_execution import (
    NarrativeExecutionState,
    NarrativeTermination,
)
from tooling.build_artifact import (
    canonical_json_bytes,
    construct_build_artifact,
    write_build_artifact_atomic,
)
from tooling.cli import (
    EXIT_NARRATIVE_REQUEST,
    EXIT_RUNTIME,
    EXIT_SUCCESS,
    EXIT_USAGE,
    main,
)
from tooling.narrative_artifact import route_narrative_build_material
from tooling.narrative_execution import (
    NARRATIVE_EXECUTION_REQUEST_SCHEMA,
    NARRATIVE_EXECUTION_RESULT_SCHEMA,
    NarrativeExecutionRequest,
    load_narrative_execution_request,
    narrative_execution_request_payload,
)
from tooling.project_loader import load_project


EXPECTED_BRANCH = "p11.6g-user-facing-narrative-execution-routing"
EXPECTED_PREDECESSOR = "6963c606d408131be4f76adf3f2ecdf077ab4447"
EXPECTED_TAG = "afp-p11.6f-freeze"
THIS_FILE = (
    "apexforge/"
    "p11_6g_user_facing_narrative_execution_routing_smoke_test.py"
)
ROUTING_FILE = "apexforge/tooling/narrative_execution.py"
CLI_FILE = "apexforge/tooling/cli.py"
EXPORT_FILE = "apexforge/tooling/__init__.py"
DOC_FILE = (
    "docs/p11/P11_6G_USER_FACING_NARRATIVE_EXECUTION_ROUTING.md"
)
AUTHORIZED_PATHS = (
    THIS_FILE,
    ROUTING_FILE,
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
        "story RoutingStory {",
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


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
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


def write_request(path: Path, request: NarrativeExecutionRequest) -> bytes:
    content = canonical_json_bytes(
        narrative_execution_request_payload(request)
    )
    path.write_bytes(content)
    return content


def make_material(root_path: Path):
    project_root = root_path / "air-project"
    source_path = project_root / "src" / "main.apex"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("directive Main {}\n", encoding="utf-8")
    (project_root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": "NarrativeRouting",
                "sources": ["src/main.apex"],
                "entry": "Main",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    loaded = load_project(project_root)
    build = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )

    analysis = analyze_narrative_source(
        NARRATIVE_SOURCE,
        source_name="story.apex",
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
    integrated = construct_build_artifact(
        loaded,
        build,
        narrative_artifact=narrative,
    )
    historical = construct_build_artifact(loaded, build)
    integrated_path = root_path / "integrated.json"
    historical_path = root_path / "historical.json"
    write_build_artifact_atomic(integrated, integrated_path)
    write_build_artifact_atomic(historical, historical_path)
    return (
        integrated_path,
        historical_path,
        story,
        hero,
        integrated.content,
    )


def request_for(
    story,
    hero: NarrativeIdentity,
    *,
    ready: bool = True,
    story_identity: Optional[NarrativeIdentity] = None,
    path_index: int = 0,
    terminated: bool = False,
) -> NarrativeExecutionRequest:
    scene = story.scenes[0].identity
    facts = (
        (NarrativeStateFact(hero, "ready", "yes"),)
        if ready
        else ()
    )
    return NarrativeExecutionRequest(
        state=NarrativeExecutionState(
            story=(story.identity if story_identity is None else story_identity),
            current_scene=scene,
            facts=facts,
            progression=(scene,),
            choice_history=(),
            termination=(
                NarrativeTermination("terminated", "explicit_outcome")
                if terminated
                else NarrativeTermination()
            ),
        ),
        choice=story.choices[0].identity,
        path_index=path_index,
    )


def test_predecessor_ownership_and_fixture() -> None:
    repository_root = root()
    require(
        git(repository_root, "branch", "--show-current") == EXPECTED_BRANCH,
        "P11.6G is running on an unexpected branch",
    )
    require(
        git(repository_root, "rev-parse", "HEAD") == EXPECTED_PREDECESSOR,
        "candidate no longer rests on the exact frozen predecessor",
    )
    require(
        git(repository_root, "cat-file", "-t", EXPECTED_TAG) == "tag",
        "P11.6F freeze must be annotated",
    )
    require(
        git(repository_root, "rev-parse", EXPECTED_TAG + "^{}")
        == EXPECTED_PREDECESSOR,
        "P11.6F tag does not identify the exact predecessor",
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
        f"unexpected P11.6G ownership/protected set: {status_paths!r}",
    )
    fixture = repository_root / "examples/P11Validation/main.apex"
    require(
        hashlib.sha256(fixture.read_bytes()).hexdigest()
        == PROTECTED_MAIN_SHA256,
        "protected main.apex changed",
    )


def test_historical_commands_and_explicit_activation() -> None:
    repository_root = root()
    fixture = repository_root / "apexforge/fixtures/p11_1b/single_fallback"
    cli_text = (repository_root / CLI_FILE).read_text(encoding="utf-8")
    for command in ("project", "check", "run", "build", "new", "narrative"):
        require(
            f'commands.add_parser(\n        "{command}"' in cli_text,
            f"public command {command!r} is unavailable",
        )

    original_narrative_execute = (
        narrative_observability.execute_narrative_choice
    )

    def forbidden_narrative_execution(*arguments, **keywords):
        raise AssertionError("historical command activated narrative execution")

    narrative_observability.execute_narrative_choice = (
        forbidden_narrative_execution
    )
    try:
        code, stdout, stderr = invoke(("run", str(fixture)))
        require(code == EXIT_SUCCESS, "historical AIR run failed")
        require(
            stdout
            == (
                "ApexForge run succeeded: SingleFallback\n"
                "Entry: directive:Solo\n"
                "Runtime diagnostics: 0\n"
            ),
            "historical AIR run behavior changed",
        )
        require(stderr == "", "historical AIR run wrote stderr")

        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "air.json"
            code, stdout, stderr = invoke(
                ("build", str(fixture), "--output", str(output))
            )
            require(code == EXIT_SUCCESS, "historical build failed")
            value = json.loads(output.read_text(encoding="utf-8"))
            require(
                "narrative" not in value,
                "historical build activated narrative",
            )
            require(
                "ApexForge build succeeded" in stdout,
                "build output changed",
            )
            require(stderr == "", "historical build wrote stderr")
    finally:
        narrative_observability.execute_narrative_choice = (
            original_narrative_execute
        )


def test_success_delegates_once_and_projects_canonical_output() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact, _, story, hero, artifact_before = make_material(
            temporary_root
        )
        request = request_for(story, hero)
        request_path = temporary_root / "request.json"
        request_bytes = write_request(request_path, request)
        original_state = request.state

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

        def forbidden_air_execution(*arguments, **keywords):
            raise AssertionError("narrative route used AIR runtime machinery")

        narrative_observability.transition_narrative_choice = (
            recording_transition
        )
        narrative_observability.execute_narrative_choice = recording_execute
        RuntimeEngine.execute = forbidden_air_execution
        try:
            first = invoke(
                ("narrative", str(artifact), "--request", str(request_path))
            )
        finally:
            narrative_observability.transition_narrative_choice = (
                original_transition
            )
            narrative_observability.execute_narrative_choice = original_execute
            RuntimeEngine.execute = original_air_execute

        code, stdout, stderr = first
        require(code == EXIT_SUCCESS, "explicit narrative transition failed")
        require(stderr == "", "successful narrative route wrote stderr")
        require(calls == {"p11_6e": 1, "p11_6d": 1}, "frozen authority stack was not delegated through exactly once")
        value = json.loads(stdout)
        require(
            value["schema"] == NARRATIVE_EXECUTION_RESULT_SCHEMA,
            "public result schema changed",
        )
        require(value["ok"] is True, "successful output reports failure")
        require(
            value["final_state"]["current_scene"]
            == {"kind": "scene", "path": ["End"]},
            "resulting current scene is unavailable",
        )
        require(
            value["final_state"]["progression"]
            == [
                {"kind": "scene", "path": ["Start"]},
                {"kind": "scene", "path": ["End"]},
            ],
            "resulting progression is unavailable",
        )
        require(
            value["choice_evidence"][0]["path_index"] == 0,
            "selected-choice evidence is unavailable",
        )
        require(
            value["trace"][0]["facts"][-1]
            == {"key": "outcome", "value": "success"},
            "P11.6E trace evidence is unavailable",
        )
        require(
            value["final_state"]["termination"]
            == {"status": "active", "reason": None},
            "graph shape inferred termination",
        )
        require(
            original_state == request.state,
            "successful execution mutated the request state",
        )
        require(
            artifact.read_bytes() == artifact_before,
            "narrative execution modified its immutable build artifact",
        )
        require(
            request_path.read_bytes() == request_bytes,
            "narrative execution modified its explicit request",
        )
        second = invoke(
            ("narrative", str(artifact), "--request", str(request_path))
        )
        require(first == second, "equivalent requests produced different output")

        completed = subprocess.run(
            (
                sys.executable,
                str(root() / "apexforge/apexforge_cli.py"),
                "narrative",
                str(artifact),
                "--request",
                str(request_path),
            ),
            cwd=root(),
            check=False,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        require(completed.returncode == EXIT_SUCCESS, "public wrapper route failed")
        require(completed.stdout == stdout, "public wrapper output changed")
        require(completed.stderr == "", "public wrapper wrote stderr")

        loaded_request = load_narrative_execution_request(request_path)
        require(loaded_request == request, "state request round trip changed")
        require(
            request_bytes
            == canonical_json_bytes(
                narrative_execution_request_payload(loaded_request)
            ),
            "request projection is not canonical deterministic JSON",
        )


def test_failures_remain_deterministic_and_immutable() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact, historical, story, hero, _ = make_material(temporary_root)

        cases = (
            (
                "path",
                request_for(story, hero, path_index=9),
                "NARRATIVE_TRANSITION_PATH_NOT_FOUND",
            ),
            (
                "condition",
                request_for(story, hero, ready=False),
                "NARRATIVE_TRANSITION_CONDITION_UNSATISFIED",
            ),
            (
                "terminated",
                request_for(story, hero, terminated=True),
                "NARRATIVE_EXECUTION_TERMINATED",
            ),
            (
                "story-mismatch",
                request_for(
                    story,
                    hero,
                    story_identity=NarrativeIdentity("story", ("Other",)),
                ),
                "NARRATIVE_TRANSITION_STORY_MISMATCH",
            ),
        )
        for name, request, diagnostic_code in cases:
            request_path = temporary_root / f"{name}.json"
            write_request(request_path, request)
            before = request.state
            first = invoke(
                ("narrative", str(artifact), "--request", str(request_path))
            )
            second = invoke(
                ("narrative", str(artifact), "--request", str(request_path))
            )
            require(first == second, f"{name} failure was nondeterministic")
            code, stdout, stderr = first
            require(code == EXIT_RUNTIME, f"{name} failure exit changed")
            require(stderr == "", f"{name} failure leaked generic stderr")
            value = json.loads(stdout)
            require(value["ok"] is False, f"{name} reported success")
            require(
                value["diagnostics"][0]["code"] == diagnostic_code,
                f"{name} lost the P11.6E diagnostic",
            )
            require(
                value["initial_state"] == value["final_state"],
                f"{name} failure changed public state",
            )
            require(request.state == before, f"{name} mutated original state")
            require(
                value["choice_evidence"] == [],
                f"{name} invented selected-choice evidence",
            )

        code, stdout, stderr = invoke(
            ("narrative", str(historical), "--request", str(request_path))
        )
        require(code == EXIT_NARRATIVE_REQUEST, "absent narrative material exit changed")
        require(stdout == "", "absent narrative material wrote result output")
        require(
            stderr
            == (
                "[APX-NARRATIVE-112] canonical narrative build material "
                "is unavailable.\n"
            ),
            "absent narrative material classification changed",
        )

        missing_artifact = temporary_root / "missing.json"
        code, stdout, stderr = invoke(
            ("narrative", str(missing_artifact), "--request", str(request_path))
        )
        require(code == EXIT_NARRATIVE_REQUEST, "missing artifact exit changed")
        require(stdout == "", "missing artifact wrote stdout")
        require(
            stderr
            == "[APX-NARRATIVE-110] narrative build artifact is unavailable.\n",
            "missing artifact classification changed",
        )

        malformed_artifact = temporary_root / "malformed-artifact.json"
        malformed_artifact.write_bytes(b"{}\n")
        code, stdout, stderr = invoke(
            ("narrative", str(malformed_artifact), "--request", str(request_path))
        )
        require(code == EXIT_NARRATIVE_REQUEST, "malformed artifact exit changed")
        require(stdout == "", "malformed artifact wrote stdout")
        require(
            stderr
            == "[APX-NARRATIVE-111] narrative build artifact is malformed.\n",
            "malformed artifact classification changed",
        )


def test_malformed_requests_and_boundaries() -> None:
    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)
        artifact, _, story, hero, artifact_bytes = make_material(temporary_root)
        valid = narrative_execution_request_payload(request_for(story, hero))

        malformed_state = dict(valid)
        malformed_state["state"] = dict(valid["state"])
        malformed_state["state"]["progression"] = []
        malformed_state_path = temporary_root / "malformed-state.json"
        malformed_state_path.write_bytes(canonical_json_bytes(malformed_state))
        first = invoke(
            (
                "narrative",
                str(artifact),
                "--request",
                str(malformed_state_path),
            )
        )
        second = invoke(
            (
                "narrative",
                str(artifact),
                "--request",
                str(malformed_state_path),
            )
        )
        require(first == second, "malformed state failure was nondeterministic")
        require(
            first
            == (
                EXIT_NARRATIVE_REQUEST,
                "",
                "[APX-NARRATIVE-120] explicit narrative execution state "
                "is malformed.\n",
            ),
            "malformed explicit state classification changed",
        )

        for field_name in ("choice", "path_index"):
            missing = dict(valid)
            del missing[field_name]
            missing_path = temporary_root / f"missing-{field_name}.json"
            missing_path.write_bytes(canonical_json_bytes(missing))
            code, stdout, stderr = invoke(
                (
                    "narrative",
                    str(artifact),
                    "--request",
                    str(missing_path),
                )
            )
            require(
                code == EXIT_NARRATIVE_REQUEST,
                f"missing {field_name} exit changed",
            )
            require(stdout == "", f"missing {field_name} wrote stdout")
            require(
                stderr
                == (
                    "[APX-NARRATIVE-100] invalid narrative execution "
                    "request.\n"
                ),
                f"missing {field_name} was inferred",
            )

        for field_name in ("story", "current_scene"):
            missing = dict(valid)
            missing["state"] = dict(valid["state"])
            del missing["state"][field_name]
            missing_path = temporary_root / f"missing-state-{field_name}.json"
            missing_path.write_bytes(canonical_json_bytes(missing))
            code, stdout, stderr = invoke(
                (
                    "narrative",
                    str(artifact),
                    "--request",
                    str(missing_path),
                )
            )
            require(
                code == EXIT_NARRATIVE_REQUEST,
                f"missing state {field_name} exit changed",
            )
            require(stdout == "", f"missing state {field_name} wrote stdout")
            require(
                stderr
                == (
                    "[APX-NARRATIVE-120] explicit narrative execution "
                    "state is malformed.\n"
                ),
                f"missing state {field_name} was inferred",
            )

        code, stdout, stderr = invoke(("narrative", str(artifact)))
        require(code == EXIT_USAGE, "missing request did not fail CLI shape")
        require(stdout == "", "usage failure wrote stdout")
        require("--request" in stderr, "usage failure omitted required request")

        routing_text = (root() / ROUTING_FILE).read_text(encoding="utf-8")
        for forbidden in (
            "analyze_narrative_source",
            "parse_narrative_source",
            "bind_narrative_story",
            "RuntimeEngine",
            "input(",
            "sys.stdin",
            "while ",
        ):
            require(
                forbidden not in routing_text,
                f"routing module crossed a frozen/deferred boundary via {forbidden!r}",
            )
        require(
            "execute_narrative_choice(" in routing_text,
            "routing module does not delegate to P11.6E",
        )
        require(
            "transition_narrative_choice(" not in routing_text,
            "routing module bypasses P11.6E for P11.6D",
        )
        artifact_value = json.loads(artifact_bytes.decode("utf-8"))
        narrative_value = artifact_value["narrative"]
        for forbidden in (
            "initial_state",
            "final_state",
            "progression",
            "choice_history",
            "termination",
            "trace",
            "diagnostics",
        ):
            require(
                forbidden not in narrative_value,
                f"P11.6F artifact gained runtime field {forbidden!r}",
            )


def main_test() -> None:
    test_predecessor_ownership_and_fixture()
    test_historical_commands_and_explicit_activation()
    test_success_delegates_once_and_projects_canonical_output()
    test_failures_remain_deterministic_and_immutable()
    test_malformed_requests_and_boundaries()
    print("AFP-P11.6G user-facing narrative execution routing smoke test passed.")
    print("Frozen P11.6F predecessor, exact ownership, and fixture: PASS")
    print("Historical command, AIR run, and build compatibility: PASS")
    print("Explicit artifact/state/choice/path request and canonical output: PASS")
    print("P11.6E boundary and P11.6D transition delegation: PASS")
    print("Deterministic failures, immutability, and fail-closed conditions: PASS")
    print("No inference, loop, graph termination, AIR runtime, or state artifact: PASS")


if __name__ == "__main__":
    main_test()
