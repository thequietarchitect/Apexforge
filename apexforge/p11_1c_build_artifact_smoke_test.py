"""Focused smoke test for the P11.1C canonical build artifact."""

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

from air.serialization import air_to_dict
from language.project import ProjectBuild, build_project
from runtime.engine import RuntimeEngine
from tooling.build_artifact import (
    BUILD_ARTIFACT_SCHEMA,
    canonical_json_bytes,
    construct_build_artifact,
)
import tooling.build_artifact as build_artifact_module
from tooling.cli import (
    EXIT_ARTIFACT_OUTPUT,
    EXIT_CHECK,
    EXIT_SUCCESS,
    EXIT_USAGE,
    P10_T1_CLI_VERSION,
    main,
)
from tooling.project_loader import load_project


PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent
P11_1A_FIXTURES = PACKAGE_DIR / "fixtures" / "p11_1a"
P11_1B_FIXTURES = PACKAGE_DIR / "fixtures" / "p11_1b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def artifact_success_output(value: dict) -> str:
    entry = value["project"]["entry"]
    return (
        f"ApexForge build succeeded: {value['project']['name']}\n"
        f"Schema: {BUILD_ARTIFACT_SCHEMA}\n"
        f"Entry: {entry if entry is not None else '<none>'}\n"
        f"Sources: {value['project']['source_count']}\n"
        "Fingerprint: sha256:"
        f"{value['fingerprint']['value']}\n"
        "Artifact written.\n"
    )


def read_artifact(path: Path) -> tuple[bytes, dict]:
    content = path.read_bytes()
    return content, json.loads(content.decode("utf-8"))


def temporary_residue(output: Path) -> tuple[Path, ...]:
    prefix = f".{output.name}."
    return tuple(
        item
        for item in output.parent.iterdir()
        if item.name.startswith(prefix) and item.name.endswith(".tmp")
    )


def assert_canonical_artifact(
    content: bytes,
    value: dict,
    *,
    project_root: Path,
    output_path: Path,
) -> None:
    require(not content.startswith(b"\xef\xbb\xbf"), "artifact has a UTF-8 BOM")
    require(b"\r" not in content, "artifact does not use LF-only line endings")
    require(content.endswith(b"\n"), "artifact omitted its final newline")
    require(not content.endswith(b"\n\n"), "artifact has multiple final newlines")
    require(
        content == canonical_json_bytes(value),
        "artifact bytes are not canonical sorted two-space JSON",
    )
    require(
        set(value) == {"air", "fingerprint", "project", "schema"},
        "artifact top-level structure changed",
    )
    require(value["schema"] == BUILD_ARTIFACT_SCHEMA, "artifact schema changed")
    require(
        set(value["project"])
        == {"entry", "name", "source_count", "sources"},
        "project metadata shape changed",
    )
    require(
        set(value["fingerprint"]) == {"algorithm", "value"},
        "fingerprint shape changed",
    )
    require(
        value["fingerprint"]["algorithm"] == "sha256",
        "fingerprint algorithm changed",
    )
    payload = {
        "air": value["air"],
        "project": value["project"],
        "schema": value["schema"],
    }
    expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    require(
        value["fingerprint"]["value"] == expected,
        "fingerprint byte boundary changed",
    )
    require(
        len(expected) == 64 and expected == expected.lower(),
        "fingerprint is not lowercase SHA-256 hexadecimal",
    )
    serialized = content.decode("utf-8")
    for forbidden_path in (
        project_root.resolve(),
        REPOSITORY_ROOT.resolve(),
        output_path.resolve(),
    ):
        require(
            str(forbidden_path) not in serialized,
            "artifact exposed an absolute project, repository, or output path",
        )
    forbidden_keys = {
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
        "source_map",
        "tam",
    }

    def mapping_keys(item):
        if isinstance(item, dict):
            for key, child in item.items():
                yield key
                yield from mapping_keys(child)
        elif isinstance(item, list):
            for child in item:
                yield from mapping_keys(child)

    require(
        forbidden_keys.isdisjoint(set(mapping_keys(value))),
        "artifact included forbidden metadata",
    )


def write_unicode_project(root: Path) -> Path:
    source_name = "src/μ.apex"
    source_path = root / "src" / "μ.apex"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(
        (
            "directive Unicode {\n"
            "    event ready\n"
            "    cause start {\n"
            "        path primary @ 10 {\n"
            '            message "Vår"\n'
            "            emit ready\n"
            "        }\n"
            "    }\n"
            "}\n"
        ).encode("utf-8")
    )
    manifest = {
        "schema": 1,
        "name": "UnicodeBuild",
        "sources": [source_name],
    }
    (root / "apexforge.json").write_bytes(
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
    )
    return source_path


def main_test() -> None:
    manifest_entry = P11_1B_FIXTURES / "manifest_entry"
    single_fallback = P11_1B_FIXTURES / "single_fallback"
    ambiguous = P11_1B_FIXTURES / "ambiguous"
    representative = P11_1A_FIXTURES / "representative_linked"

    with TemporaryDirectory() as temporary:
        temporary_root = Path(temporary)

        missing_output = temporary_root / "missing.json"
        code, stdout, stderr = invoke(("build", str(manifest_entry)))
        require(code == EXIT_USAGE, "missing --output did not return usage")
        require(stdout == "", "missing --output wrote success output")
        require("--output" in stderr, "missing --output diagnostic changed")
        require(not missing_output.exists(), "usage failure created an artifact")

        default_output = temporary_root / "default.json"
        previous_directory = Path.cwd()
        try:
            os.chdir(manifest_entry)
            code, stdout, stderr = invoke(
                ("build", "--output", str(default_output))
            )
        finally:
            os.chdir(previous_directory)
        content, default_value = read_artifact(default_output)
        require(code == EXIT_SUCCESS, "default current-directory build failed")
        require(
            stdout == artifact_success_output(default_value),
            "default build success output changed",
        )
        require(stderr == "", "default build wrote to stderr")
        require(
            default_value["project"]["entry"] == "directive:Main",
            "manifest entry metadata was not canonicalized",
        )
        assert_canonical_artifact(
            content,
            default_value,
            project_root=manifest_entry,
            output_path=default_output,
        )

        explicit_output = temporary_root / "explicit.json"
        code, stdout, stderr = invoke(
            (
                "build",
                str(manifest_entry),
                "--output",
                str(explicit_output),
                "--entry",
                "Alternate",
            )
        )
        explicit_content, explicit_value = read_artifact(explicit_output)
        require(code == EXIT_SUCCESS, "explicit project-path build failed")
        require(stderr == "", "explicit project-path build wrote to stderr")
        require(
            stdout == artifact_success_output(explicit_value),
            "explicit project-path success output changed",
        )
        require(
            explicit_value["project"]["entry"] == "directive:Alternate",
            "explicit entry did not override the manifest entry",
        )
        require(
            explicit_content != content,
            "selected entry did not affect canonical artifact bytes",
        )

        fallback_output = temporary_root / "fallback.json"
        code, stdout, stderr = invoke(
            ("build", str(single_fallback), "--output", str(fallback_output))
        )
        _, fallback_value = read_artifact(fallback_output)
        require(code == EXIT_SUCCESS, "single-directive fallback failed")
        require(stdout == artifact_success_output(fallback_value), "fallback output changed")
        require(stderr == "", "single-directive fallback wrote to stderr")
        require(
            fallback_value["project"]["entry"] == "directive:Solo",
            "single-directive fallback entry changed",
        )

        ambiguous_output = temporary_root / "ambiguous.json"
        code, stdout, stderr = invoke(
            ("build", str(ambiguous), "--output", str(ambiguous_output))
        )
        _, ambiguous_value = read_artifact(ambiguous_output)
        require(code == EXIT_SUCCESS, "ambiguous build was incorrectly rejected")
        require(stdout == artifact_success_output(ambiguous_value), "ambiguous output changed")
        require(stderr == "", "ambiguous build wrote to stderr")
        require(
            ambiguous_value["project"]["entry"] is None,
            "ambiguous build did not record a null entry",
        )

        undefined_output = temporary_root / "undefined.json"
        undefined_output.write_bytes(b"existing-output")
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
        require(code == EXIT_CHECK, "undefined entry exit code changed")
        require(stdout == "", "undefined entry wrote success output")
        require(
            stderr == "Undefined project entry directive 'Missing'.\n",
            "undefined entry diagnostic changed",
        )
        require(
            undefined_output.read_bytes() == b"existing-output",
            "undefined entry altered an existing output",
        )

        deterministic_a = temporary_root / "deterministic-a.json"
        deterministic_b = temporary_root / "deterministic-b.json"
        for output in (deterministic_a, deterministic_b):
            code, _, stderr = invoke(
                ("build", str(representative), "--output", str(output))
            )
            require(code == EXIT_SUCCESS, "repeated representative build failed")
            require(stderr == "", "repeated representative build wrote stderr")
        first_bytes, first_value = read_artifact(deterministic_a)
        second_bytes, second_value = read_artifact(deterministic_b)
        require(first_bytes == second_bytes, "repeated build bytes differ")
        require(
            first_value["fingerprint"] == second_value["fingerprint"],
            "repeated build fingerprints differ",
        )
        require(
            tuple(item["path"] for item in first_value["project"]["sources"])
            == (
                "src/10-core.apex",
                "src/20-adjust.apex",
                "src/30-counter.apex",
            ),
            "artifact lost canonical manifest source ordering",
        )
        require(
            all("\\" not in item["path"] for item in first_value["project"]["sources"]),
            "artifact source path did not use forward slashes",
        )
        loaded = load_project(representative)
        linked = build_project(loaded.source_mapping(), entry=loaded.manifest.entry)
        require(
            first_value["air"] == air_to_dict(linked.program),
            "artifact AIR did not use existing canonical AIR serialization",
        )
        require(
            first_value["project"]["source_count"] == 3
            and len(first_value["air"]["functions"]) == 2
            and first_value["air"]["directives"][0]["id"]
            == "directive:Representative",
            "artifact omitted linked multi-source AIR",
        )
        for source_metadata in first_value["project"]["sources"]:
            source_path = representative.joinpath(*source_metadata["path"].split("/"))
            require(
                source_metadata["sha256"]
                == hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "source hash was not computed from exact source bytes",
            )
        assert_canonical_artifact(
            first_bytes,
            first_value,
            project_root=representative,
            output_path=deterministic_a,
        )

        changed_project = temporary_root / "changed-project"
        shutil.copytree(single_fallback, changed_project)
        unchanged_output = temporary_root / "unchanged-source.json"
        changed_output = temporary_root / "changed-source.json"
        code, _, _ = invoke(
            ("build", str(changed_project), "--output", str(unchanged_output))
        )
        require(code == EXIT_SUCCESS, "unchanged source build failed")
        source_path = changed_project / "src" / "solo.apex"
        source_path.write_bytes(source_path.read_bytes() + b"\n")
        code, _, _ = invoke(
            ("build", str(changed_project), "--output", str(changed_output))
        )
        require(code == EXIT_SUCCESS, "changed source build failed")
        _, unchanged_value = read_artifact(unchanged_output)
        _, changed_value = read_artifact(changed_output)
        require(
            unchanged_value["project"]["sources"][0]["sha256"]
            != changed_value["project"]["sources"][0]["sha256"],
            "source content change did not change source hash",
        )
        require(
            unchanged_value["fingerprint"]["value"]
            != changed_value["fingerprint"]["value"],
            "source content change did not change fingerprint",
        )

        snapshot_project = temporary_root / "snapshot-project"
        shutil.copytree(single_fallback, snapshot_project)
        snapshot_source = snapshot_project / "src" / "solo.apex"
        snapshot_bytes = snapshot_source.read_bytes().replace(b"\n", b"\r\n")
        snapshot_source.write_bytes(snapshot_bytes)
        snapshot_loaded = load_project(snapshot_project)
        require(
            "\r" not in snapshot_loaded.sources[0].source,
            "loader source-text newline behavior changed",
        )
        snapshot_build = build_project(snapshot_loaded.source_mapping())
        snapshot_source.write_bytes(snapshot_bytes + b"\n")
        snapshot_artifact = construct_build_artifact(
            snapshot_loaded,
            snapshot_build,
        )
        snapshot_value = json.loads(snapshot_artifact.content.decode("utf-8"))
        require(
            snapshot_value["project"]["sources"][0]["sha256"]
            == hashlib.sha256(snapshot_bytes).hexdigest(),
            "artifact reread a source instead of hashing loaded bytes",
        )

        unicode_project = temporary_root / "unicode-project"
        unicode_source = write_unicode_project(unicode_project)
        unicode_output = temporary_root / "unicode.json"
        code, _, stderr = invoke(
            ("build", str(unicode_project), "--output", str(unicode_output))
        )
        unicode_content, unicode_value = read_artifact(unicode_output)
        require(code == EXIT_SUCCESS, "Unicode project build failed")
        require(stderr == "", "Unicode project build wrote stderr")
        require(b"\xce\xbc" in unicode_content, "Unicode was escaped or lost")
        require(b"\\u03bc" not in unicode_content, "Unicode was JSON escaped")
        require(
            unicode_value["project"]["sources"][0]["sha256"]
            == hashlib.sha256(unicode_source.read_bytes()).hexdigest(),
            "Unicode source hash changed the exact byte boundary",
        )

        replacement_output = temporary_root / "replace.json"
        replacement_output.write_bytes(b"old-artifact")
        code, stdout, stderr = invoke(
            ("build", str(single_fallback), "--output", str(replacement_output))
        )
        replacement_bytes, replacement_value = read_artifact(replacement_output)
        require(code == EXIT_SUCCESS, "atomic replacement build failed")
        require(stdout == artifact_success_output(replacement_value), "replacement output changed")
        require(stderr == "", "atomic replacement wrote stderr")
        require(replacement_bytes != b"old-artifact", "existing output was not replaced")
        require(not temporary_residue(replacement_output), "success left temporary residue")

        broken_project = temporary_root / "broken-project"
        shutil.copytree(single_fallback, broken_project)
        (broken_project / "src" / "solo.apex").write_bytes(
            b"directive Broken { state count = }\n"
        )
        preserved_output = temporary_root / "preserved.json"
        preserved_output.write_bytes(b"preserve-me")
        code, stdout, stderr = invoke(
            ("build", str(broken_project), "--output", str(preserved_output))
        )
        require(code == EXIT_CHECK, "build failure exit code changed")
        require(stdout == "", "build failure wrote success output")
        require(stderr != "", "build failure omitted its diagnostic")
        require(
            preserved_output.read_bytes() == b"preserve-me",
            "build failure altered an existing output",
        )
        require(not temporary_residue(preserved_output), "build failure left temporary residue")

        serialization_output = temporary_root / "serialization-failure.json"
        serialization_output.write_bytes(b"serialized-before")
        original_air_to_dict = build_artifact_module.air_to_dict

        def fail_serialization(program):
            raise TypeError("synthetic AIR serialization failure")

        build_artifact_module.air_to_dict = fail_serialization
        try:
            code, stdout, stderr = invoke(
                (
                    "build",
                    str(single_fallback),
                    "--output",
                    str(serialization_output),
                )
            )
        finally:
            build_artifact_module.air_to_dict = original_air_to_dict
        require(code == 70, "serialization failure exit code changed")
        require(stdout == "", "serialization failure wrote success output")
        require(
            stderr
            == (
                "[APX-CLI-999] TypeError: "
                "synthetic AIR serialization failure\n"
            ),
            "serialization failure diagnostic changed",
        )
        require(
            serialization_output.read_bytes() == b"serialized-before",
            "serialization failure altered an existing output",
        )
        require(
            not temporary_residue(serialization_output),
            "serialization failure left temporary residue",
        )

        replace_failure_output = temporary_root / "replace-failure.json"
        replace_failure_output.write_bytes(b"replace-before")
        original_replace = build_artifact_module.os.replace

        def fail_replace(source, destination):
            raise OSError("synthetic replace failure")

        build_artifact_module.os.replace = fail_replace
        try:
            code, stdout, stderr = invoke(
                (
                    "build",
                    str(single_fallback),
                    "--output",
                    str(replace_failure_output),
                )
            )
        finally:
            build_artifact_module.os.replace = original_replace
        require(code == EXIT_ARTIFACT_OUTPUT, "replace failure exit code changed")
        require(stdout == "", "replace failure wrote success output")
        require(
            stderr == "[APX-BUILD-040] Unable to write build artifact.\n",
            "replace failure diagnostic changed",
        )
        require(
            replace_failure_output.read_bytes() == b"replace-before",
            "failed atomic replacement altered the existing output",
        )
        require(
            not temporary_residue(replace_failure_output),
            "replace failure left temporary residue",
        )

        unavailable_output = temporary_root / "missing-parent" / "artifact.json"
        code, stdout, stderr = invoke(
            ("build", str(single_fallback), "--output", str(unavailable_output))
        )
        require(code == EXIT_ARTIFACT_OUTPUT, "artifact output exit code changed")
        require(stdout == "", "artifact output failure wrote success output")
        require(
            stderr == "[APX-BUILD-040] Unable to write build artifact.\n",
            "artifact output diagnostic changed",
        )
        require(not unavailable_output.exists(), "output failure created an artifact")

        original_runtime_execute = RuntimeEngine.execute
        original_project_execute = ProjectBuild.execute

        def forbidden_execution(*args, **kwargs):
            raise AssertionError("build command attempted execution")

        RuntimeEngine.execute = forbidden_execution
        ProjectBuild.execute = forbidden_execution
        try:
            nonexecuting_output = temporary_root / "nonexecuting.json"
            code, _, stderr = invoke(
                ("build", str(single_fallback), "--output", str(nonexecuting_output))
            )
        finally:
            RuntimeEngine.execute = original_runtime_execute
            ProjectBuild.execute = original_project_execute
        require(code == EXIT_SUCCESS, "build command attempted runtime execution")
        require(stderr == "", "non-executing build wrote stderr")

        wrapper_output = temporary_root / "wrapper.json"
        wrapper = PACKAGE_DIR / "apexforge_cli.py"
        completed = subprocess.run(
            [
                sys.executable,
                str(wrapper),
                "build",
                str(single_fallback),
                "--output",
                str(wrapper_output),
            ],
            cwd=str(REPOSITORY_ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        _, wrapper_value = read_artifact(wrapper_output)
        require(completed.returncode == 0, "repository wrapper build failed")
        require(completed.stdout == artifact_success_output(wrapper_value), "wrapper output changed")
        require(completed.stderr == "", "repository wrapper wrote stderr")

        metadata = (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        entry_point = "tooling.cli:main"
        require(
            f'apexforge = "{entry_point}"' in metadata,
            "packaged public entry point changed",
        )
        packaged_output = temporary_root / "packaged.json"
        entry_loader = (
            "import importlib, sys; "
            "target = sys.argv.pop(1); "
            "module_name, function_name = target.split(':', 1); "
            "function = getattr(importlib.import_module(module_name), function_name); "
            "raise SystemExit(function())"
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                entry_loader,
                entry_point,
                "build",
                str(single_fallback),
                "--output",
                str(packaged_output),
            ],
            cwd=str(REPOSITORY_ROOT),
            check=False,
            capture_output=True,
            text=True,
        )
        _, packaged_value = read_artifact(packaged_output)
        require(completed.returncode == 0, "packaged public build failed")
        require(completed.stdout == artifact_success_output(packaged_value), "packaged output changed")
        require(completed.stderr == "", "packaged entry point wrote stderr")

        code, stdout, stderr = invoke(("--version",))
        require(code == EXIT_SUCCESS, "--version behavior changed")
        require(stdout == f"ApexForge CLI {P10_T1_CLI_VERSION}\n", "version output changed")
        require(stderr == "", "--version wrote stderr")

        code, stdout, stderr = invoke(("project", str(manifest_entry)))
        require(code == EXIT_SUCCESS, "project behavior changed")
        require("Project: ManifestEntry\n" in stdout, "project output changed")
        require(stderr == "", "project wrote stderr")

        code, stdout, stderr = invoke(("check", str(manifest_entry)))
        require(code == EXIT_SUCCESS, "check behavior changed")
        require(
            stdout == "ApexForge check passed: ManifestEntry (2 source(s)).\n",
            "check output changed",
        )
        require(stderr == "", "check wrote stderr")

        code, stdout, stderr = invoke(("run", str(single_fallback)))
        require(code == EXIT_SUCCESS, "run behavior changed")
        require(
            stdout
            == (
                "ApexForge run succeeded: SingleFallback\n"
                "Entry: directive:Solo\n"
                "Runtime diagnostics: 0\n"
            ),
            "run output changed",
        )
        require(stderr == "", "run wrote stderr")

        new_parent = temporary_root / "new-projects"
        code, stdout, stderr = invoke(("new", "BuildDemo", str(new_parent)))
        created = new_parent / "BuildDemo"
        require(code == EXIT_SUCCESS, "new behavior changed")
        require(
            stdout
            == (
                "Created ApexForge project: BuildDemo\n"
                f"Root: {created.resolve()}\n"
                f"Manifest: {(created / 'apexforge.json').resolve()}\n"
                f"Source: {(created / 'src' / 'main.apex').resolve()}\n"
            ),
            "new output changed",
        )
        require(stderr == "", "new wrote stderr")

    print("AFP-P11.1C canonical multi-source build artifact smoke test passed.")
    print("Explicit output and path behavior: PASS")
    print("Entry metadata precedence: PASS")
    print("Canonical AIR, source hashing, and fingerprinting: PASS")
    print("Deterministic UTF-8 JSON bytes: PASS")
    print("Atomic replacement and failure preservation: PASS")
    print("Non-executing build pipeline: PASS")
    print("Repository wrapper and packaged entry point: PASS")
    print("Existing public command preservation: PASS")


if __name__ == "__main__":
    main_test()
