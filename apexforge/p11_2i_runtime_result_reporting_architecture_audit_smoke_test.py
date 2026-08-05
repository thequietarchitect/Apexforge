"""AFP-P11.2I-A runtime-result reporting architecture audit smoke test."""

from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
FREEZE_TAG = "afp-p11.2h-freeze"
FREEZE_COMMIT = "28b61e7392d164cc91c3ecaf2bb8c24cba522153"

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


def paths(value: str) -> set[str]:
    return {
        line.strip().replace("\\", "/")
        for line in value.splitlines()
        if line.strip()
    }


def status() -> str:
    completed = git(
        "status",
        "--porcelain=v2",
        "--untracked-files=all",
    )
    require(completed.returncode == 0, "git status failed")
    return completed.stdout


def test_frozen_baseline() -> None:
    tag_type = git("cat-file", "-t", FREEZE_TAG)
    require(
        tag_type.returncode == 0 and tag_type.stdout.strip() == "tag",
        "P11.2H annotated tag is missing",
    )
    target = git("rev-list", "-n", "1", FREEZE_TAG)
    require(
        target.returncode == 0 and target.stdout.strip() == FREEZE_COMMIT,
        "P11.2H freeze target changed",
    )
    require(
        git("merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD").returncode
        == 0,
        "HEAD no longer descends from P11.2H",
    )


def test_reviewed_successor_ownership() -> None:
    tracked = paths(git("diff", "--name-only").stdout)
    staged = paths(git("diff", "--cached", "--name-only").stdout)
    untracked = paths(
        git("ls-files", "--others", "--exclude-standard").stdout
    )
    require(staged == set(), "P11.2I staged files")
    candidate = (
        tracked == CANDIDATE_TRACKED
        and untracked == CANDIDATE_UNTRACKED
    )
    committed = tracked == set() and untracked == CLEAN_UNTRACKED
    require(
        candidate or committed,
        "the reviewed P11.2I-A/P11.2I-B path set changed",
    )


def test_execution_and_result_boundaries() -> None:
    cli = (ROOT / "apexforge/tooling/cli.py").read_text(encoding="utf-8")
    project = (ROOT / "apexforge/language/project.py").read_text(encoding="utf-8")
    engine = (ROOT / "apexforge/runtime/engine.py").read_text(encoding="utf-8")
    state = (ROOT / "apexforge/runtime/state.py").read_text(encoding="utf-8")
    diagnostics = (
        ROOT / "apexforge/runtime/diagnostics.py"
    ).read_text(encoding="utf-8")

    require(
        'run.add_argument(\n        "--report",' in cli
        and "report=namespace.report" in cli
        and "result = build.execute(" in cli
        and "render_runtime_report(result)" in cli,
        "P11.2I-B CLI successor markers changed",
    )
    require(
        'f"ApexForge run succeeded: {loaded.manifest.name}"' in cli
        and 'print(f"Entry: {resolved_entry}", file=stdout)' in cli
        and 'print("Runtime diagnostics: 0", file=stdout)' in cli,
        "ordinary run success preamble changed",
    )
    require(
        project.count("return runtime.execute(") >= 1,
        "ProjectBuild execution delegation changed",
    )
    require(
        "class ExecutionResult:" in engine
        and "delta: StateDelta" in engine
        and "trace: Trace" in engine
        and "final_state: StateSnapshot" in engine,
        "ExecutionResult projection changed",
    )
    require(
        "class StateDelta:" in state
        and "assignments: Tuple[StateAssignment, ...]" in state
        and "events: Tuple[EventRecord, ...]" in state
        and "effects: Tuple[EffectIntent, ...]" in state,
        "StateDelta projection changed",
    )
    require(
        "class TraceStep:" in diagnostics and "class Trace:" in diagnostics,
        "trace projection changed",
    )


def test_renderer_and_separation() -> None:
    report = (
        ROOT / "apexforge/tools/runtime_report.py"
    ).read_text(encoding="utf-8")
    artifact = (
        ROOT / "apexforge/tooling/build_artifact.py"
    ).read_text(encoding="utf-8")

    require(
        "def render_runtime_report(result: Any) -> str:" in report
        and 'REPORT_HEADING = "APEXFORGE RUNTIME REPORT"' in report
        and '"ASSIGNMENTS"' in report
        and '"EVENTS"' in report
        and '"EFFECTS"' in report
        and '"TRACE"' in report
        and '"FINAL STATE"' in report,
        "canonical report renderer changed",
    )
    require(
        "def print_runtime_report" not in report
        and "state_key" not in report,
        "legacy state-key or direct-print interface survived",
    )
    require(
        'BUILD_ARTIFACT_SCHEMA = "apexforge.build-artifact/v1"' in artifact
        and "runtime_report" not in artifact
        and "ExecutionResult" not in artifact,
        "runtime reporting leaked into build-artifact v1",
    )


def test_documents_and_successor_test() -> None:
    required = (
        ROOT / "docs/p11/P11_2I_RUNTIME_RESULT_REPORTING_ARCHITECTURE_AUDIT.md",
        ROOT / "apexforge/p11_2i_opt_in_runtime_result_report_smoke_test.py",
        ROOT / "docs/p11/P11_2I_B_OPT_IN_RUNTIME_RESULT_REPORT.md",
    )
    for path in required:
        require(path.is_file(), f"required P11.2I file missing: {path.name}")


def main() -> None:
    before = status()
    bytecode_before = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.pyc", "*.pyo")
        for path in ROOT.rglob(pattern)
    }
    test_frozen_baseline()
    test_reviewed_successor_ownership()
    test_execution_and_result_boundaries()
    test_renderer_and_separation()
    test_documents_and_successor_test()
    require(status() == before, "audit changed repository status")
    bytecode_after = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.pyc", "*.pyo")
        for path in ROOT.rglob(pattern)
    }
    require(bytecode_after == bytecode_before, "audit changed bytecode state")

    print("AFP-P11.2I-A runtime-result reporting architecture audit passed.")
    print("P11.2H annotated baseline and ancestry: PASS")
    print("Reviewed P11.2I-B successor ownership: PASS")
    print("Ordinary run output and single-execution boundary: PASS")
    print("ExecutionResult, StateDelta, trace, and final state: PASS")
    print("Canonical opt-in renderer successor: PASS")
    print("Build-artifact v1 separation: PASS")
    print("Repository and bytecode preservation: PASS")


if __name__ == "__main__":
    main()
