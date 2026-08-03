"""Consolidated P11.1 integration and freeze-gate smoke test."""

from __future__ import annotations

import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from authority.engine import AuthorityEngine
from language.project import ProjectBuild
from runtime.engine import RuntimeEngine
from tooling import cli as cli_module
from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    canonical_json_bytes,
)
from tooling.cli import (
    EXIT_ARTIFACT_OUTPUT,
    EXIT_CHECK,
    EXIT_INTERNAL,
    EXIT_PROJECT,
    EXIT_RUNTIME,
    EXIT_SUCCESS,
    EXIT_USAGE,
    P10_T1_CLI_VERSION,
    main,
)
from tooling.performance_baseline import (
    PERFORMANCE_BASELINE_SCHEMA,
    main as performance_baseline_main,
)
from tooling.project_loader import load_project
from tooling.project_scaffold import (
    DEFAULT_PROJECT_ENTRY,
    DEFAULT_PROJECT_SOURCE,
    DEFAULT_PROJECT_SOURCE_TEXT,
)


PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent
P11_1A_FIXTURES = PACKAGE_DIR / "fixtures" / "p11_1a"
P11_1B_FIXTURES = PACKAGE_DIR / "fixtures" / "p11_1b"
ENTRY_LOADER = (
    "import importlib, sys; "
    "target = sys.argv.pop(1); "
    "module_name, function_name = target.split(':', 1); "
    "function = getattr(importlib.import_module(module_name), function_name); "
    "raise SystemExit(function())"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def snapshot_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix().casefold(),
        )
    }


def read_artifact(path: Path) -> tuple[bytes, dict]:
    content = path.read_bytes()
    return content, json.loads(content.decode("utf-8"))


def artifact_output(value: dict) -> str:
    entry = value["project"]["entry"]
    return (
        f"ApexForge build succeeded: {value['project']['name']}\n"
        f"Schema: {BUILD_ARTIFACT_SCHEMA}\n"
        f"Entry: {entry if entry is not None else '<none>'}\n"
        f"Sources: {value['project']['source_count']}\n"
        f"Fingerprint: sha256:{value['fingerprint']['value']}\n"
        "Artifact written.\n"
    )


def run_output(project: str, entry: str) -> str:
    return (
        f"ApexForge run succeeded: {project}\n"
        f"Entry: directive:{entry}\n"
        "Runtime diagnostics: 0\n"
    )


def temporary_residue(output: Path) -> tuple[Path, ...]:
    return tuple(
        item
        for item in output.parent.iterdir()
        if item.name.startswith(f".{output.name}.")
        and item.name.endswith(".tmp")
    )


def invoke_process(prefix: tuple[str, ...], arguments: tuple[str, ...]):
    return subprocess.run(
        [sys.executable, *prefix, *arguments],
        cwd=str(REPOSITORY_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )


def main_test() -> None:
    manifest_entry = P11_1B_FIXTURES / "manifest_entry"
    single_fallback = P11_1B_FIXTURES / "single_fallback"
    ambiguous = P11_1B_FIXTURES / "ambiguous"
    downstream_denial = P11_1B_FIXTURES / "downstream_denial"
    representative = P11_1A_FIXTURES / "representative_linked"

    require(
        (
            EXIT_SUCCESS,
            EXIT_USAGE,
            EXIT_PROJECT,
            EXIT_CHECK,
            EXIT_RUNTIME,
            EXIT_ARTIFACT_OUTPUT,
            EXIT_INTERNAL,
        )
        == (0, 2, 10, 20, 30, 40, 70),
        "public CLI exit-code assignments changed",
    )

    accepted_fixture_snapshot = snapshot_tree(P11_1B_FIXTURES)

    code, stdout, stderr = invoke(("--version",))
    require(code == EXIT_SUCCESS, "--version failed")
    require(
        stdout == f"ApexForge CLI {P10_T1_CLI_VERSION}\n",
        "--version output changed",
    )
    require(stderr == "", "--version wrote to stderr")

    code, stdout, stderr = invoke(("project", str(manifest_entry)))
    require(code == EXIT_SUCCESS, "project command failed")
    require(
        stdout
        == (
            "Project: ManifestEntry\n"
            f"Manifest: {(manifest_entry / 'apexforge.json').resolve()}\n"
            f"Root: {manifest_entry.resolve()}\n"
            "Entry: Main\n"
            "Sources: 2\n"
            "  src/alternate.apex\n"
            "  src/main.apex\n"
        ),
        "project observational output changed",
    )
    require(stderr == "", "project wrote to stderr")

    with TemporaryDirectory(
        prefix=".p11_1d_",
        dir=str(REPOSITORY_ROOT),
    ) as temporary:
        temporary_root = Path(temporary)

        scaffold_parent = temporary_root / "projects"
        code, stdout, stderr = invoke(
            ("new", "IntegrationDemo", str(scaffold_parent))
        )
        scaffold = scaffold_parent / "IntegrationDemo"
        require(code == EXIT_SUCCESS, "new command failed")
        require(stderr == "", "new command wrote to stderr")
        require(
            stdout
            == (
                "Created ApexForge project: IntegrationDemo\n"
                f"Root: {scaffold.resolve()}\n"
                f"Manifest: {(scaffold / 'apexforge.json').resolve()}\n"
                f"Source: {(scaffold / DEFAULT_PROJECT_SOURCE).resolve()}\n"
            ),
            "new command output changed",
        )
        scaffold_loaded = load_project(scaffold)
        require(
            scaffold_loaded.manifest.entry == DEFAULT_PROJECT_ENTRY
            and scaffold_loaded.manifest.sources == (DEFAULT_PROJECT_SOURCE,),
            "new command scaffold contract changed",
        )
        require(
            (scaffold / DEFAULT_PROJECT_SOURCE).read_text(encoding="utf-8")
            == DEFAULT_PROJECT_SOURCE_TEXT,
            "new command source template changed",
        )

        original_runtime_init = RuntimeEngine.__init__
        original_runtime_execute = RuntimeEngine.execute
        original_project_execute = ProjectBuild.execute
        original_from_grants = AuthorityEngine.__dict__["from_grants"]

        def forbidden_execution(*args, **kwargs):
            raise AssertionError("non-executing command crossed runtime boundary")

        def forbidden_authority(cls, grants):
            raise AssertionError("non-executing command constructed authority")

        RuntimeEngine.__init__ = forbidden_execution
        RuntimeEngine.execute = forbidden_execution
        ProjectBuild.execute = forbidden_execution
        AuthorityEngine.from_grants = classmethod(forbidden_authority)
        try:
            check_artifact = temporary_root / "check-should-not-exist.json"
            code, stdout, stderr = invoke(("check", str(manifest_entry)))
            require(code == EXIT_SUCCESS, "check command failed")
            require(
                stdout
                == "ApexForge check passed: ManifestEntry (2 source(s)).\n",
                "check output changed",
            )
            require(stderr == "", "check wrote to stderr")
            require(
                not check_artifact.exists(),
                "check created a project artifact",
            )

            manifest_output = temporary_root / "manifest-entry.json"
            code, stdout, stderr = invoke(
                (
                    "build",
                    str(manifest_entry),
                    "--output",
                    str(manifest_output),
                )
            )
            manifest_content, manifest_value = read_artifact(manifest_output)
            require(code == EXIT_SUCCESS, "non-executing build failed")
            require(stdout == artifact_output(manifest_value), "build output changed")
            require(stderr == "", "build wrote to stderr")
        finally:
            RuntimeEngine.__init__ = original_runtime_init
            RuntimeEngine.execute = original_runtime_execute
            ProjectBuild.execute = original_project_execute
            AuthorityEngine.from_grants = original_from_grants

        project_execute_entries = []
        runtime_observations = []

        def recording_project_execute(self, context, *, entry=None, engine=None):
            project_execute_entries.append(entry)
            return original_project_execute(
                self,
                context,
                entry=entry,
                engine=engine,
            )

        def recording_runtime_execute(
            self,
            verified,
            context,
            entry_directives=None,
        ):
            runtime_observations.append(
                (
                    entry_directives,
                    tuple(
                        (
                            grant.principal,
                            grant.capability,
                            grant.resource,
                        )
                        for grant in context.authority.grants
                    ),
                )
            )
            return original_runtime_execute(
                self,
                verified,
                context,
                entry_directives=entry_directives,
            )

        ProjectBuild.execute = recording_project_execute
        RuntimeEngine.execute = recording_runtime_execute
        run_directory_before = snapshot_tree(temporary_root)
        previous_directory = Path.cwd()
        try:
            os.chdir(temporary_root)
            code, stdout, stderr = invoke(("run", str(manifest_entry)))
            require(code == EXIT_SUCCESS, "manifest-entry run failed")
            require(stdout == run_output("ManifestEntry", "Main"), "manifest run changed")
            require(stderr == "", "manifest-entry run wrote stderr")

            code, stdout, stderr = invoke(
                ("run", str(manifest_entry), "--entry", "Alternate")
            )
            require(code == EXIT_SUCCESS, "explicit-entry run failed")
            require(
                stdout == run_output("ManifestEntry", "Alternate"),
                "run entry override changed",
            )
            require(stderr == "", "explicit-entry run wrote stderr")

            code, stdout, stderr = invoke(("run", str(single_fallback)))
            require(code == EXIT_SUCCESS, "single-entry fallback run failed")
            require(
                stdout == run_output("SingleFallback", "Solo"),
                "single-entry fallback run changed",
            )
            require(stderr == "", "single-entry fallback wrote stderr")

            code, stdout, stderr = invoke(("run", str(downstream_denial)))
            require(code == EXIT_RUNTIME, "downstream denial exit changed")
            require(stdout == "", "downstream denial wrote success output")
            require("[RUN001]" in stderr, "downstream denial lost RUN001")
        finally:
            os.chdir(previous_directory)
            ProjectBuild.execute = original_project_execute
            RuntimeEngine.execute = original_runtime_execute

        require(
            snapshot_tree(temporary_root) == run_directory_before,
            "run created a build artifact or other project output",
        )

        require(
            project_execute_entries
            == (
                [
                    "directive:Main",
                    "directive:Alternate",
                    "directive:Solo",
                    "directive:Caller",
                ]
            ),
            "run did not execute through ProjectBuild.execute with one entry",
        )
        require(
            all(
                entries is not None and len(tuple(entries)) == 1
                for entries, _ in runtime_observations
            ),
            "public run exposed RuntimeEngine.execute(entry_directives=None)",
        )
        require(
            runtime_observations[0]
            == (
                ("directive:Main",),
                (
                    (
                        "principal:Main",
                        "directive.invoke:Main",
                        "directive:Main",
                    ),
                ),
            ),
            "public run did not grant exactly the selected entry invocation",
        )
        require(
            tuple(item[0] for item in runtime_observations[-1][1])
            == ("principal:Caller",),
            "public run granted downstream invocation authority",
        )

        code, stdout, stderr = invoke(("run", str(ambiguous)))
        require(code == EXIT_CHECK, "ambiguous run exit changed")
        require(stdout == "", "ambiguous run wrote success output")
        require(
            stderr
            == "A multi-directive project requires an explicit entry directive.\n",
            "accepted ambiguous-entry diagnostic changed",
        )

        code, stdout, stderr = invoke(
            ("run", str(manifest_entry), "--entry", "Missing")
        )
        require(code == EXIT_CHECK, "undefined run entry exit changed")
        require(stdout == "", "undefined run entry wrote success output")
        require(stderr != "", "undefined run entry omitted its diagnostic")

        override_output = temporary_root / "override.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(manifest_entry),
                "--output",
                str(override_output),
                "--entry",
                "Alternate",
            )
        )
        _, override_value = read_artifact(override_output)
        require(code == EXIT_SUCCESS, "explicit-entry build failed")
        require(stdout == artifact_output(override_value), "override build output changed")
        require(stderr == "", "explicit-entry build wrote stderr")
        require(
            manifest_value["project"]["entry"] == "directive:Main"
            and override_value["project"]["entry"] == "directive:Alternate",
            "run/build manifest and explicit entry precedence diverged",
        )

        fallback_output = temporary_root / "fallback.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(single_fallback),
                "--output",
                str(fallback_output),
            )
        )
        _, fallback_value = read_artifact(fallback_output)
        require(code == EXIT_SUCCESS, "single-entry fallback build failed")
        require(stdout == artifact_output(fallback_value), "fallback build output changed")
        require(stderr == "", "fallback build wrote stderr")
        require(
            fallback_value["project"]["entry"] == "directive:Solo",
            "run/build single-entry fallback diverged",
        )

        ambiguous_output = temporary_root / "ambiguous.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(ambiguous),
                "--output",
                str(ambiguous_output),
            )
        )
        _, ambiguous_value = read_artifact(ambiguous_output)
        require(code == EXIT_SUCCESS, "ambiguous artifact build failed")
        require(stdout == artifact_output(ambiguous_value), "ambiguous build output changed")
        require(stderr == "", "ambiguous build wrote stderr")
        require(
            ambiguous_value["project"]["entry"] is None,
            "ambiguous artifact entry is not null",
        )

        undefined_output = temporary_root / "undefined.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(manifest_entry),
                "--output",
                str(undefined_output),
                "--entry",
                "Missing",
            )
        )
        require(code == EXIT_CHECK, "undefined build entry exit changed")
        require(stdout == "", "undefined build entry wrote success output")
        require(stderr != "", "undefined build entry omitted its diagnostic")
        require(not undefined_output.exists(), "undefined build entry created output")

        require(
            manifest_content == canonical_json_bytes(manifest_value),
            "artifact is not canonical JSON",
        )
        require(
            not manifest_content.startswith(b"\xef\xbb\xbf")
            and b"\r" not in manifest_content
            and manifest_content.endswith(b"\n")
            and not manifest_content.endswith(b"\n\n"),
            "artifact UTF-8/LF/final-newline contract changed",
        )
        require(
            manifest_value["schema"] == BUILD_ARTIFACT_SCHEMA,
            "artifact schema changed",
        )
        fingerprint_payload = {
            "schema": manifest_value["schema"],
            "project": manifest_value["project"],
            "air": manifest_value["air"],
        }
        expected_fingerprint = hashlib.sha256(
            canonical_json_bytes(fingerprint_payload)
        ).hexdigest()
        require(
            set(fingerprint_payload) == {"schema", "project", "air"}
            and "fingerprint" not in fingerprint_payload
            and manifest_value["fingerprint"]
            == {"algorithm": "sha256", "value": expected_fingerprint},
            "artifact fingerprint boundary changed",
        )
        loaded_manifest = load_project(manifest_entry)
        require(
            tuple(
                item["sha256"]
                for item in manifest_value["project"]["sources"]
            )
            == tuple(
                hashlib.sha256(source.source_bytes).hexdigest()
                for source in loaded_manifest.sources
            ),
            "source hashes are not over exact loaded source bytes",
        )

        repeated_output = temporary_root / "manifest-entry-repeat.json"
        code, _, stderr = invoke(
            (
                "build",
                str(manifest_entry),
                "--output",
                str(repeated_output),
            )
        )
        require(code == EXIT_SUCCESS and stderr == "", "repeated build failed")
        require(
            repeated_output.read_bytes() == manifest_content,
            "identical builds produced different bytes",
        )

        serialized = manifest_content.decode("utf-8")
        require(
            str(REPOSITORY_ROOT.resolve()) not in serialized
            and str(manifest_entry.resolve()) not in serialized
            and str(manifest_output.resolve()) not in serialized,
            "artifact exposed an absolute path",
        )
        forbidden_metadata = {
            "timestamp",
            "duration",
            "performance",
            "username",
            "hostname",
            "home_directory",
            "repository_path",
            "output_path",
            "credentials",
            "tokens",
        }

        def keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield key
                    yield from keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from keys(child)

        require(
            forbidden_metadata.isdisjoint(set(keys(manifest_value))),
            "artifact exposed forbidden host metadata",
        )

        broken_project = temporary_root / "broken-project"
        shutil.copytree(single_fallback, broken_project)
        (broken_project / "src" / "solo.apex").write_text(
            "directive Broken { state count = }\n",
            encoding="utf-8",
        )
        preserved_output = temporary_root / "preserved.json"
        preserved_output.write_bytes(b"preserve-existing-output")
        code, stdout, stderr = invoke(
            (
                "build",
                str(broken_project),
                "--output",
                str(preserved_output),
            )
        )
        require(code == EXIT_CHECK, "failed build exit changed")
        require(stdout == "" and stderr != "", "failed build success boundary changed")
        require(
            preserved_output.read_bytes() == b"preserve-existing-output",
            "failed build altered an existing output",
        )
        require(
            not temporary_residue(preserved_output),
            "failed build left temporary sibling residue",
        )

        artifact_manifest_root = temporary_root / "artifact-input"
        artifact_manifest_root.mkdir()
        artifact_manifest = artifact_manifest_root / "apexforge.json"
        artifact_manifest.write_bytes(manifest_content)
        ProjectBuild.execute = forbidden_execution
        RuntimeEngine.execute = forbidden_execution
        try:
            code, stdout, stderr = invoke(("run", str(artifact_manifest)))
        finally:
            ProjectBuild.execute = original_project_execute
            RuntimeEngine.execute = original_runtime_execute
        require(code == EXIT_PROJECT, "artifact input crossed the loading boundary")
        require(stdout == "", "artifact input executed or wrote success output")
        require(stderr != "", "artifact input rejection omitted its diagnostic")

        missing_parent_output = temporary_root / "missing" / "artifact.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(single_fallback),
                "--output",
                str(missing_parent_output),
            )
        )
        require(code == EXIT_ARTIFACT_OUTPUT, "artifact-output failure exit changed")
        require(stdout == "" and stderr != "", "artifact-output failure rendering changed")

        code, stdout, stderr = invoke(("build", str(single_fallback)))
        require(code == EXIT_USAGE, "usage exit changed")
        require(stdout == "" and stderr != "", "usage failure rendering changed")

        baseline_fixture_before = snapshot_tree(P11_1A_FIXTURES)
        baseline_output = temporary_root / "baseline.json"
        baseline_stdout = StringIO()
        baseline_code = performance_baseline_main(
            (
                "--warmups",
                "0",
                "--samples",
                "1",
                "--json-output",
                str(baseline_output),
            ),
            stdout=baseline_stdout,
        )
        baseline_value = json.loads(baseline_output.read_text(encoding="utf-8"))
        require(baseline_code == 0, "P11.1A baseline failed")
        require(
            set(baseline_value)
            == {
                "schema",
                "clock",
                "duration_unit",
                "configuration",
                "environment",
                "benchmarks",
            }
            and baseline_value["schema"] == PERFORMANCE_BASELINE_SCHEMA,
            "P11.1A JSON schema changed",
        )
        require(
            "no pass/fail performance threshold"
            in baseline_stdout.getvalue(),
            "P11.1A baseline introduced a performance threshold",
        )
        require(
            snapshot_tree(P11_1A_FIXTURES) == baseline_fixture_before,
            "P11.1A baseline changed a fixture source",
        )
        require(
            BUILD_ARTIFACT_SCHEMA not in baseline_output.read_text(encoding="utf-8"),
            "P11.1A baseline created a project artifact",
        )

        metadata = (REPOSITORY_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        entry_point = "tooling.cli:main"
        require(
            f'apexforge = "{entry_point}"' in metadata,
            "packaged console entry point changed",
        )
        wrapper = PACKAGE_DIR / "apexforge_cli.py"
        wrapper_prefix = (str(wrapper),)
        packaged_prefix = ("-c", ENTRY_LOADER, entry_point)
        for label, prefix in (
            ("repository wrapper", wrapper_prefix),
            ("packaged console entry", packaged_prefix),
        ):
            completed = invoke_process(prefix, ("--help",))
            require(completed.returncode == 0, f"{label} help failed")
            require(completed.stderr == "", f"{label} help wrote stderr")
            require(
                all(
                    command in completed.stdout
                    for command in ("project", "check", "run", "build", "new")
                )
                and "--version" in completed.stdout,
                f"{label} does not expose the complete public command surface",
            )

            completed = invoke_process(prefix, ("run", str(single_fallback)))
            require(completed.returncode == 0, f"{label} run failed")
            require(
                completed.stdout == run_output("SingleFallback", "Solo")
                and completed.stderr == "",
                f"{label} run output changed",
            )

            surface_output = temporary_root / f"{label.replace(' ', '-')}.json"
            completed = invoke_process(
                prefix,
                (
                    "build",
                    str(representative),
                    "--output",
                    str(surface_output),
                ),
            )
            _, surface_value = read_artifact(surface_output)
            require(completed.returncode == 0, f"{label} build failed")
            require(
                completed.stdout == artifact_output(surface_value)
                and completed.stderr == "",
                f"{label} build output changed",
            )

        original_load_project = cli_module.load_project

        def interrupted_load(path):
            raise KeyboardInterrupt()

        cli_module.load_project = interrupted_load
        try:
            code, stdout, stderr = invoke(("project", str(manifest_entry)))
        finally:
            cli_module.load_project = original_load_project
        require(code == 130, "interruption exit changed")
        require(stdout == "" and stderr != "", "interruption rendering changed")

        def failed_load(path):
            raise RuntimeError("synthetic integration failure")

        cli_module.load_project = failed_load
        try:
            code, stdout, stderr = invoke(("project", str(manifest_entry)))
        finally:
            cli_module.load_project = original_load_project
        require(code == EXIT_INTERNAL, "unexpected-failure exit changed")
        require(stdout == "" and stderr != "", "internal-failure rendering changed")

    require(
        snapshot_tree(P11_1B_FIXTURES) == accepted_fixture_snapshot,
        "project/check/run changed an accepted fixture or created an artifact",
    )

    print("AFP-P11.1D integration and freeze-gate smoke test passed.")
    print("Existing public command preservation: PASS")
    print("Run/build/check execution boundaries: PASS")
    print("Entry-selection consistency: PASS")
    print("Entry-only authority and downstream denial: PASS")
    print("Artifact schema, fingerprint, and deterministic bytes: PASS")
    print("Atomic failure preservation and residue cleanup: PASS")
    print("Artifact execution remains unsupported: PASS")
    print("Performance-baseline isolation: PASS")
    print("Repository wrapper and packaged console entry: PASS")
    print("Public exit-code matrix: PASS")


if __name__ == "__main__":
    main_test()
