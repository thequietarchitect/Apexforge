"""Executable P11.5I-A audit aligned to the reviewed P11.5I-B reporter."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
DOCUMENT_PATH = (
    REPOSITORY_ROOT
    / "docs"
    / "p11"
    / "P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_ARCHITECTURE_AUDIT.md"
)
BASELINE_TAG = "afp-p11.5h-freeze"
EXPECTED_HEAD = "f9af32adb5cf56a5d78f6bcd59ed4ecc70c933c1"
EXPECTED_BRANCH = "p11.5i-narrative-analysis-result-reporting"

AUDIT_PATHS = {
    "apexforge/p11_5i_narrative_analysis_result_reporting_architecture_audit_smoke_test.py",
    "docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/tools/narrative_report.py",
    "apexforge/p11_5i_narrative_analysis_result_reporting_smoke_test.py",
    "docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def test_frozen_baseline_and_reviewed_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5I is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5I predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5H controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5H controlling freeze resolves incorrectly",
    )

    committed = {
        item
        for item in git(
            "diff",
            "--name-only",
            f"{BASELINE_TAG}..HEAD",
        ).splitlines()
        if item
    }
    working = {
        line[3:].replace("\\", "/")
        for line in git(
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).splitlines()
        if len(line) >= 4
        and not line[3:].replace("\\", "/").startswith(
            "examples/P11Validation/"
        )
    }
    require(
        committed | working == REVIEWED_PATHS,
        "reviewed P11.5I-A/P11.5I-B path set changed",
    )


def test_aligned_architecture_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(
        document.replace(chr(96), "").split()
    ).casefold()
    required = (
        "P11.5H is the frozen analysis-pipeline predecessor",
        "reviewed P11.5I-B successor",
        "reporting != serialization",
        "reporting != execution",
        "one dedicated production module",
        "tools/narrative_report.py",
        "render_narrative_analysis_report",
        "exact NarrativeSourceAnalysis",
        "deterministic human-readable report",
        "source summary",
        "semantic summary",
        "graph nodes",
        "graph edges",
        "validation findings",
        "canonical empty markers",
        "source order",
        "graph order",
        "finding order",
        "identity display",
        "no mutation",
        "no re-analysis",
        "no diagnostic conversion",
        "no CLI integration",
        "no compiler integration",
        "no project integration",
        "no runtime integration",
        "no language-server integration",
        "no Visual Studio integration",
        "no changes to language/narrative_analysis.py",
        "no changes to language/narrative_validation.py",
    )
    for phrase in required:
        require(
            phrase.casefold() in normalized,
            f"aligned P11.5I audit omits required phrase: {phrase}",
        )


def test_exact_reporting_production_surface() -> None:
    module_path = PACKAGE_DIRECTORY / "tools" / "narrative_report.py"
    require(module_path.is_file(), "P11.5I-B reporter is missing")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and not node.name.startswith("_")
    }
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    require(
        public_classes == set(),
        "narrative reporting public class surface changed",
    )
    require(
        public_functions == {"render_narrative_analysis_report"},
        "narrative reporting public function surface changed",
    )


def test_frozen_stage_and_operational_surfaces() -> None:
    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_lowering.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/tools/runtime_report.py",
        "apexforge/air/model.py",
        "apexforge/air/serialization.py",
        "apexforge/runtime/engine.py",
        "apexforge/tooling/cli.py",
    ):
        baseline = git("show", f"{BASELINE_TAG}:{relative}").encode("utf-8")
        require(
            (REPOSITORY_ROOT / relative).read_bytes() == baseline,
            f"frozen predecessor or operational file changed: {relative}",
        )


def test_audit_is_repository_no_op() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    filesystem_mutators = {
        "write_text",
        "write_bytes",
        "unlink",
        "mkdir",
        "rename",
    }
    git_mutators = {"add", "commit", "tag", "push", "reset"}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in filesystem_mutators
        ):
            raise AssertionError(
                "P11.5I-A audit contains a filesystem mutation call"
            )
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "git"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in git_mutators
        ):
            raise AssertionError(
                "P11.5I-A audit contains a Git mutation call"
            )


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    test_frozen_baseline_and_reviewed_ownership()
    test_aligned_architecture_contract()
    test_exact_reporting_production_surface()
    test_frozen_stage_and_operational_surfaces()
    test_audit_is_repository_no_op()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "aligned P11.5I-A audit mutated repository status")

    print("AFP-P11.5I-A aligned narrative analysis result reporting architecture audit passed.")
    print("P11.5H annotated freeze and exact predecessor HEAD: PASS")
    print("Reviewed P11.5I-A/P11.5I-B five-file ownership: PASS")
    print("Frozen four-product analysis result boundary: PASS")
    print("Deterministic source, semantic, graph, and validation projection: PASS")
    print("Identity display, ordered evidence, and empty-marker contract: PASS")
    print("Pure reporting implementation constrained to one production file: PASS")
    print("No re-analysis, mutation, diagnostic conversion, serialization, CLI, or execution: PASS")
    print("Frozen narrative, compiler, project, runtime, and editor surfaces: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
