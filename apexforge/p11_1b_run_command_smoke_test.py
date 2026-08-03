"""Focused smoke test for the P11.1B canonical public run command."""

from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from runtime.engine import RuntimeEngine
from tooling.cli import (
    EXIT_CHECK,
    EXIT_RUNTIME,
    EXIT_SUCCESS,
    P10_T1_CLI_VERSION,
    main,
)


PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent
FIXTURE_ROOT = PACKAGE_DIR / "fixtures" / "p11_1b"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def success_output(project: str, entry: str) -> str:
    return (
        f"ApexForge run succeeded: {project}\n"
        f"Entry: directive:{entry}\n"
        "Runtime diagnostics: 0\n"
    )


def main_test() -> None:
    manifest_entry = FIXTURE_ROOT / "manifest_entry"
    single_fallback = FIXTURE_ROOT / "single_fallback"
    ambiguous = FIXTURE_ROOT / "ambiguous"
    downstream_denial = FIXTURE_ROOT / "downstream_denial"

    for fixture in (
        manifest_entry,
        single_fallback,
        ambiguous,
        downstream_denial,
    ):
        require(
            (fixture / "apexforge.json").is_file(),
            f"P11.1B fixture is missing: {fixture.name}",
        )

    observations = []
    original_execute = RuntimeEngine.execute

    def recording_execute(
        runtime,
        verified,
        context,
        entry_directives=None,
    ):
        observations.append(
            {
                "entries": entry_directives,
                "grants": context.authority.grants,
                "state_keys": tuple(cell.key for cell in context.state.cells),
            }
        )
        return original_execute(
            runtime,
            verified,
            context,
            entry_directives=entry_directives,
        )

    RuntimeEngine.execute = recording_execute
    try:
        previous_directory = Path.cwd()
        try:
            os.chdir(manifest_entry)
            code, stdout, stderr = invoke(("run",))
        finally:
            os.chdir(previous_directory)

        require(code == EXIT_SUCCESS, "default current-directory run failed")
        require(
            stdout == success_output("ManifestEntry", "Main"),
            "default current-directory success output changed",
        )
        require(stderr == "", "successful default run wrote to stderr")

        code, stdout, stderr = invoke(("run", str(manifest_entry)))
        require(code == EXIT_SUCCESS, "explicit project-path run failed")
        require(
            stdout == success_output("ManifestEntry", "Main"),
            "manifest entry was not selected deterministically",
        )
        require(stderr == "", "explicit project-path run wrote to stderr")
        require(
            str(manifest_entry.resolve()) not in stdout,
            "run success output exposed an absolute project path",
        )
        require("runtime.start" not in stdout, "run success exposed a trace")
        require("StateSnapshot" not in stdout, "run success exposed state")

        code, stdout, stderr = invoke(
            ("run", str(manifest_entry), "--entry", "Alternate")
        )
        require(code == EXIT_SUCCESS, "explicit entry override failed")
        require(
            stdout == success_output("ManifestEntry", "Alternate"),
            "explicit entry did not override the manifest entry",
        )
        require(stderr == "", "entry override wrote to stderr")

        code, stdout, stderr = invoke(("run", str(single_fallback)))
        require(code == EXIT_SUCCESS, "single-directive fallback failed")
        require(
            stdout == success_output("SingleFallback", "Solo"),
            "single-directive fallback did not report its canonical entry",
        )
        require(stderr == "", "single-directive fallback wrote to stderr")

        code, stdout, stderr = invoke(("run", str(ambiguous)))
        require(code == EXIT_CHECK, "ambiguous project exit code changed")
        require(stdout == "", "ambiguous project printed success output")
        require(
            stderr
            == (
                "A multi-directive project requires an explicit entry "
                "directive.\n"
            ),
            "ambiguous project diagnostic changed",
        )

        code, stdout, stderr = invoke(
            ("run", str(manifest_entry), "--entry", "Missing")
        )
        require(code == EXIT_CHECK, "undefined entry exit code changed")
        require(stdout == "", "undefined entry printed success output")
        require(
            stderr == "Undefined project entry directive 'Missing'.\n",
            "undefined entry diagnostic changed",
        )

        code, stdout, stderr = invoke(("run", str(downstream_denial)))
        require(code == EXIT_RUNTIME, "runtime authority denial exit changed")
        require(stdout == "", "runtime authority denial printed success")
        require(
            stderr
            == (
                "directive:Callee [RUN001] authority denied: "
                "principal:Callee lacks directive.invoke:Callee on "
                "directive:Callee\n"
            ),
            "runtime authority denial rendering changed",
        )
    finally:
        RuntimeEngine.execute = original_execute

    require(
        all(item["entries"] is not None for item in observations),
        "public run exposed the all-directive runtime fallback",
    )
    require(
        all(len(tuple(item["entries"])) == 1 for item in observations),
        "public run selected more than one runtime root",
    )

    main_observation = observations[0]
    require(
        main_observation["entries"] == ("directive:Main",),
        "manifest entry did not reach ProjectBuild.execute canonically",
    )
    require(
        tuple(
            (
                grant.principal,
                grant.capability,
                grant.resource,
            )
            for grant in main_observation["grants"]
        )
        == (
            (
                "principal:Main",
                "directive.invoke:Main",
                "directive:Main",
            ),
        ),
        "run did not construct exactly the entry-only invocation grant",
    )

    alternate_observation = observations[2]
    require(
        alternate_observation["entries"] == ("directive:Alternate",),
        "entry override did not reach ProjectBuild.execute canonically",
    )
    require(
        tuple(
            (
                grant.principal,
                grant.capability,
                grant.resource,
            )
            for grant in alternate_observation["grants"]
        )
        == (
            (
                "principal:Alternate",
                "directive.invoke:Alternate",
                "directive:Alternate",
            ),
        ),
        "entry override received an over-broad authority grant",
    )

    denial_observation = observations[-1]
    require(
        denial_observation["state_keys"]
        == ("state:caller_count", "state:count"),
        "run did not initialize state from the complete linked program",
    )
    require(
        tuple(grant.principal for grant in denial_observation["grants"])
        == ("principal:Caller",),
        "run granted downstream directive authority",
    )

    wrapper = PACKAGE_DIR / "apexforge_cli.py"
    completed = subprocess.run(
        [sys.executable, str(wrapper), "run", str(manifest_entry)],
        cwd=str(REPOSITORY_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, "repository wrapper run failed")
    require(
        completed.stdout == success_output("ManifestEntry", "Main"),
        "repository wrapper run output changed",
    )
    require(completed.stderr == "", "repository wrapper run wrote stderr")

    metadata = (REPOSITORY_ROOT / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    entry_point = "tooling.cli:main"
    require(
        f'apexforge = "{entry_point}"' in metadata,
        "packaged console entry point changed",
    )
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
            "run",
            str(manifest_entry),
        ],
        cwd=str(REPOSITORY_ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, "packaged entry-point run failed")
    require(
        completed.stdout == success_output("ManifestEntry", "Main"),
        "packaged entry-point run output changed",
    )
    require(completed.stderr == "", "packaged entry-point wrote stderr")

    code, stdout, stderr = invoke(("--version",))
    require(code == EXIT_SUCCESS, "--version behavior changed")
    require(
        stdout == f"ApexForge CLI {P10_T1_CLI_VERSION}\n",
        "--version output changed",
    )
    require(stderr == "", "--version wrote to stderr")

    code, stdout, stderr = invoke(("check", str(manifest_entry)))
    require(code == EXIT_SUCCESS, "check behavior changed")
    require(
        stdout == "ApexForge check passed: ManifestEntry (2 source(s)).\n",
        "check success output changed",
    )
    require(stderr == "", "check wrote to stderr")

    code, stdout, stderr = invoke(("project", str(manifest_entry)))
    require(code == EXIT_SUCCESS, "project behavior changed")
    require("Project: ManifestEntry\n" in stdout, "project name changed")
    require("Entry: Main\n" in stdout, "project entry output changed")
    require("Sources: 2\n" in stdout, "project source count changed")
    require(stderr == "", "project wrote to stderr")

    with TemporaryDirectory() as temporary:
        parent = Path(temporary)
        code, stdout, stderr = invoke(("new", "RunDemo", str(parent)))
        created = parent / "RunDemo"
        require(code == EXIT_SUCCESS, "new behavior changed")
        require(
            stdout
            == (
                "Created ApexForge project: RunDemo\n"
                f"Root: {created.resolve()}\n"
                f"Manifest: {(created / 'apexforge.json').resolve()}\n"
                f"Source: {(created / 'src' / 'main.apex').resolve()}\n"
            ),
            "new success output changed",
        )
        require(stderr == "", "new wrote to stderr")

    print("AFP-P11.1B canonical public run command smoke test passed.")
    print("Path default and explicit path: PASS")
    print("Entry precedence and canonicalization: PASS")
    print("Initial-state construction: PASS")
    print("Entry-only authority policy: PASS")
    print("Downstream authority denial: PASS")
    print("One-entry ProjectBuild execution: PASS")
    print("Deterministic success and diagnostic output: PASS")
    print("Repository wrapper and packaged entry point: PASS")
    print("Existing public command preservation: PASS")


if __name__ == "__main__":
    main_test()
