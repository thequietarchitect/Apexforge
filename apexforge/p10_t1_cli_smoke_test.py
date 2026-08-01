"""AFP-P10-T1.2 CLI foundation smoke test."""

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from tooling.cli import (
    EXIT_CHECK,
    EXIT_PROJECT,
    EXIT_SUCCESS,
    EXIT_USAGE,
    P10_T1_CLI_VERSION,
    main,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(arguments, *, project_builder=None):
    stdout = StringIO()
    stderr = StringIO()
    code = main(
        arguments,
        stdout=stdout,
        stderr=stderr,
        project_builder=project_builder,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def main_test() -> None:
    require(
        P10_T1_CLI_VERSION == "10-T1.2",
        "CLI version changed",
    )

    code, stdout, stderr = invoke(("--version",))
    require(code == EXIT_SUCCESS, "--version returned a failure")
    require(stdout == "ApexForge CLI 10-T1.2\n", "version output changed")
    require(stderr == "", "--version wrote to stderr")

    code, _, stderr = invoke(())
    require(code == EXIT_USAGE, "missing command did not return usage status")
    require("usage: apexforge" in stderr, "missing command omitted usage")

    with TemporaryDirectory() as temporary:
        root = Path(temporary) / "demo"
        source_dir = root / "src"
        nested = source_dir / "nested"
        nested.mkdir(parents=True)

        source_path = source_dir / "main.future"
        source_text = (
            "function Identity(value : int) : int { return value }\n"
        )
        source_path.write_text(source_text, encoding="utf-8")

        manifest_path = root / "apexforge.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schema": 1,
                    "name": "CliDemo",
                    "sources": ["src/main.future"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        code, stdout, stderr = invoke(("project", str(nested)))
        require(code == EXIT_SUCCESS, "project command failed")
        require("Project: CliDemo\n" in stdout, "project name omitted")
        require("Sources: 1\n" in stdout, "source count omitted")
        require("  src/main.future\n" in stdout, "source inventory omitted")
        require(stderr == "", "project command wrote to stderr")

        observed = {}

        def fake_builder(sources, entry):
            observed["names"] = tuple(sources)
            observed["source"] = sources["src/main.future"]
            observed["entry"] = entry
            return object()

        code, stdout, stderr = invoke(
            ("check", str(root)),
            project_builder=fake_builder,
        )
        require(code == EXIT_SUCCESS, "check command failed")
        require(
            stdout == "ApexForge check passed: CliDemo (1 source(s)).\n",
            "check success output changed",
        )
        require(stderr == "", "successful check wrote to stderr")
        require(
            observed["names"] == ("src/main.future",),
            "check did not forward canonical source order",
        )
        require(observed["source"] == source_text, "check lost source text")
        require(observed["entry"] is None, "check changed absent entry")

        def failing_builder(sources, entry):
            raise RuntimeError("synthetic check failure")

        code, stdout, stderr = invoke(
            ("check", str(root)),
            project_builder=failing_builder,
        )
        require(code == EXIT_CHECK, "check failure exit code changed")
        require(stdout == "", "failed check wrote success output")
        require(
            stderr == "synthetic check failure\n",
            "check failure rendering changed",
        )

        missing = Path(temporary) / "no-project"
        code, stdout, stderr = invoke(("project", str(missing)))
        require(code == EXIT_PROJECT, "missing manifest exit code changed")
        require(stdout == "", "missing manifest wrote success output")
        require("[APX-TOOL-001]" in stderr, "missing manifest code omitted")

        # Exercise the direct repository wrapper as a separate process.
        package_dir = Path(__file__).resolve().parent
        wrapper = package_dir / "apexforge_cli.py"
        completed = subprocess.run(
            [sys.executable, str(wrapper), "--version"],
            cwd=str(package_dir.parent),
            check=False,
            capture_output=True,
            text=True,
        )
        require(completed.returncode == 0, "CLI wrapper returned failure")
        require(
            completed.stdout == "ApexForge CLI 10-T1.2\n",
            "CLI wrapper version output changed",
        )
        require(completed.stderr == "", "CLI wrapper wrote to stderr")

    print("AFP-P10-T1.2 CLI foundation smoke test passed.")
    print("Stable version command: PASS")
    print("Deterministic usage status: PASS")
    print("Project inventory command: PASS")
    print("Canonical ProjectBuilder boundary: PASS")
    print("Check success and failure exits: PASS")
    print("Manifest failure exit: PASS")
    print("Direct repository entry point: PASS")
    print("Extension-neutral source loading: PASS")


if __name__ == "__main__":
    main_test()