"""AFP-P11.2I-B opt-in runtime result report smoke test."""

from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
import subprocess

from air.expressions import AIRIntegerLiteral
from air.model import EventRecord, StateAssignment
from effects.model import EffectIntent
from runtime.diagnostics import Diagnostic, Trace, TraceStep
from runtime.engine import ExecutionResult, RuntimeEngine
from runtime.state import StateCell, StateDelta, StateSnapshot
from tooling.cli import EXIT_RUNTIME, EXIT_SUCCESS, main
from tools.runtime_report import render_runtime_report


PACKAGE_ROOT = Path(__file__).resolve().parent
ROOT = PACKAGE_ROOT.parent
FIXTURE_ROOT = PACKAGE_ROOT / "fixtures/p11_1b"

CANDIDATE_TRACKED = {
    "apexforge/tooling/cli.py",
    "apexforge/tools/runtime_report.py",
}
CANDIDATE_UNTRACKED = {
    "apexforge/p11_2i_runtime_result_reporting_architecture_audit_smoke_test.py",
    "docs/p11/P11_2I_RUNTIME_RESULT_REPORTING_ARCHITECTURE_AUDIT.md",
    "apexforge/p11_2i_opt_in_runtime_result_report_smoke_test.py",
    "docs/p11/P11_2I_B_OPT_IN_RUNTIME_RESULT_REPORT.md",
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
}
CLEAN_UNTRACKED = {
    "examples/P11Validation/apexforge.json",
    "examples/P11Validation/main.apex",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )


def path_set(value: str) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in value.splitlines()
        if line.strip()
    }


def repository_status() -> str:
    completed = git(
        "status",
        "--porcelain=v2",
        "--untracked-files=all",
    )
    require(completed.returncode == 0, "git status failed")
    return completed.stdout


def invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def ordinary_success(project: str, entry: str) -> str:
    return (
        f"ApexForge run succeeded: {project}\n"
        f"Entry: directive:{entry}\n"
        "Runtime diagnostics: 0\n"
    )


def test_exact_renderer_contract() -> None:
    result = ExecutionResult(
        delta=StateDelta(
            assignments=(
                StateAssignment(
                    "state:count",
                    "set_int",
                    AIRIntegerLiteral(3),
                ),
            ),
            events=(
                EventRecord(
                    "event-record:1",
                    "event:Done",
                    "directive:Main",
                    "principal:Main",
                ),
            ),
            effects=(
                EffectIntent(
                    "effect:1",
                    "host.log",
                ),
            ),
        ),
        trace=Trace(
            (
                TraceStep(
                    "runtime.complete",
                    "Execution completed.",
                ),
            )
        ),
        diagnostics=(
            Diagnostic(
                "info",
                "RUN900",
                "Informational runtime note.",
                "directive:Main",
            ),
        ),
        final_state=StateSnapshot(
            (
                StateCell("state:ready", True),
                StateCell("state:count", 3),
            )
        ),
    )

    expected = (
        "APEXFORGE RUNTIME REPORT\n"
        "\n"
        "RESULT\n"
        "OK: true\n"
        "\n"
        "DIAGNOSTICS\n"
        "1. severity=info; code=RUN900; node=directive:Main; "
        'message="Informational runtime note."\n'
        "\n"
        "ASSIGNMENTS\n"
        "1. state=state:count; operation=set_int; value=3\n"
        "\n"
        "EVENTS\n"
        "1. id=event-record:1; event=event:Done; "
        "directive=directive:Main; principal=principal:Main; facts=(none)\n"
        "\n"
        "EFFECTS\n"
        "1. id=effect:1; type=host.log; facts=(none)\n"
        "\n"
        "TRACE\n"
        "1. kind=runtime.complete; "
        'message="Execution completed."; facts=(none)\n'
        "\n"
        "FINAL STATE\n"
        "state:count = 3\n"
        "state:ready = true\n"
        "END RUNTIME REPORT"
    )
    require(
        render_runtime_report(result) == expected,
        "canonical human-readable report changed",
    )
    require(
        render_runtime_report(result) == render_runtime_report(result),
        "report rendering is not repeatable",
    )


def test_cli_opt_in_and_ordinary_compatibility() -> None:
    fixture = FIXTURE_ROOT / "manifest_entry"
    require(fixture.is_dir(), "P11.1B manifest-entry fixture is missing")

    observations = []
    original_execute = RuntimeEngine.execute

    def recording_execute(
        runtime,
        verified,
        context,
        entry_directives=None,
    ):
        observations.append(entry_directives)
        return original_execute(
            runtime,
            verified,
            context,
            entry_directives=entry_directives,
        )

    RuntimeEngine.execute = recording_execute
    try:
        code, stdout, stderr = invoke(("run", str(fixture)))
        require(code == EXIT_SUCCESS, "ordinary run failed")
        require(
            stdout == ordinary_success("ManifestEntry", "Main"),
            "ordinary run output changed",
        )
        require(stderr == "", "ordinary successful run wrote stderr")

        code, reported, stderr = invoke(
            ("run", str(fixture), "--report")
        )
        require(code == EXIT_SUCCESS, "reported run failed")
        require(stderr == "", "reported successful run wrote stderr")
        require(
            reported.startswith(
                ordinary_success("ManifestEntry", "Main")
                + "\nAPEXFORGE RUNTIME REPORT\n"
            ),
            "report did not append after the frozen success preamble",
        )
        for heading in (
            "RESULT\n",
            "DIAGNOSTICS\n",
            "ASSIGNMENTS\n",
            "EVENTS\n",
            "EFFECTS\n",
            "TRACE\n",
            "FINAL STATE\n",
            "END RUNTIME REPORT\n",
        ):
            require(heading in reported, "report omitted " + repr(heading))
        require(
            reported.count("APEXFORGE RUNTIME REPORT") == 1,
            "report rendered more than once",
        )
    finally:
        RuntimeEngine.execute = original_execute

    require(
        len(observations) == 2,
        "ordinary and reported runs did not execute exactly once each",
    )
    require(
        observations == [
            ("directive:Main",),
            ("directive:Main",),
        ],
        "report mode changed canonical entry selection",
    )


def test_failure_does_not_emit_success_report() -> None:
    fixture = FIXTURE_ROOT / "downstream_denial"
    code, stdout, stderr = invoke(
        ("run", str(fixture), "--report")
    )
    require(code == EXIT_RUNTIME, "reported failure exit code changed")
    require(stdout == "", "failed run emitted success/report output")
    require(
        "RUN001" in stderr
        and "APEXFORGE RUNTIME REPORT" not in stderr,
        "failed run diagnostics/report routing changed",
    )


def test_repository_boundary() -> None:
    tracked = path_set(git("diff", "--name-only").stdout)
    staged = path_set(git("diff", "--cached", "--name-only").stdout)
    untracked = path_set(
        git("ls-files", "--others", "--exclude-standard").stdout
    )
    require(staged == set(), "P11.2I-B staged files")
    candidate = (
        tracked == CANDIDATE_TRACKED
        and untracked == CANDIDATE_UNTRACKED
    )
    committed = tracked == set() and untracked == CLEAN_UNTRACKED
    require(
        candidate or committed,
        "P11.2I-B repository path set changed",
    )


def main_test() -> None:
    status_before = repository_status()
    directory_before = Path.cwd()
    environment_before = dict(os.environ)
    bytecode_before = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.pyc", "*.pyo")
        for path in ROOT.rglob(pattern)
    }

    test_exact_renderer_contract()
    test_cli_opt_in_and_ordinary_compatibility()
    test_failure_does_not_emit_success_report()
    test_repository_boundary()

    require(Path.cwd() == directory_before, "test changed cwd")
    require(dict(os.environ) == environment_before, "test changed environment")
    require(
        repository_status() == status_before,
        "test changed repository status",
    )
    bytecode_after = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.pyc", "*.pyo")
        for path in ROOT.rglob(pattern)
    }
    require(bytecode_after == bytecode_before, "test changed bytecode state")

    print("AFP-P11.2I-B opt-in runtime result report smoke test passed.")
    print("Exact deterministic report projection and empty markers: PASS")
    print("Frozen ordinary run output without --report: PASS")
    print("Opt-in report append and one execution per invocation: PASS")
    print("Canonical entry selection and exit-code compatibility: PASS")
    print("Failure diagnostics remain stderr-only with no report: PASS")
    print("Build/runtime models and repository state preservation: PASS")


if __name__ == "__main__":
    main_test()
