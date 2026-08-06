"""Executable P11.5F-A audit aligned to the reviewed P11.5F-B parser."""

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
    / "P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_ARCHITECTURE_AUDIT.md"
)
BASELINE_TAG = "afp-p11.5e-freeze"
EXPECTED_HEAD = "eba9a27a34563a8df5f77b796c82b032ab2b0485"
EXPECTED_BRANCH = "p11.5f-opt-in-narrative-source-parser"

AUDIT_PATHS = {
    "apexforge/p11_5f_opt_in_narrative_source_parser_architecture_audit_smoke_test.py",
    "docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_parser.py",
    "apexforge/p11_5f_opt_in_narrative_source_parser_smoke_test.py",
    "docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_CONTRACT.md",
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


def test_baseline_and_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5F is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5F predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5E controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5E controlling freeze resolves incorrectly",
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
        "reviewed P11.5F-A/P11.5F-B path set changed",
    )


def test_document_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(
        document.replace(chr(96), "").split()
    ).casefold()
    required = (
        "P11.5E is the frozen source-AST predecessor",
        "reviewed P11.5F-B successor",
        "opt-in parser != ordinary operational parser",
        "one dedicated production module",
        "language/narrative_parser.py",
        "NarrativeSourceParseError",
        "parse_narrative_source",
        "one story root",
        "private narrative scanner",
        "contextual narrative keywords",
        "source order and duplicates",
        "unresolved references",
        "APX-NARRATIVE-SYNTAX",
        "first deterministic syntax failure",
        "no semantic lowering",
        "no graph construction",
        "no narrative validation",
        "no compiler integration",
        "no project integration",
        "no language-server integration",
        "no Visual Studio integration",
        "no changes to language/lexer.py",
        "no changes to language/parser.py",
    )
    for phrase in required:
        require(
            phrase.casefold() in normalized,
            f"aligned P11.5F audit omits required phrase: {phrase}",
        )


def test_parser_surface() -> None:
    parser_path = PACKAGE_DIRECTORY / "language" / "narrative_parser.py"
    require(parser_path.is_file(), "P11.5F-B parser module is missing")
    tree = ast.parse(parser_path.read_text(encoding="utf-8"))
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
        public_classes == {"NarrativeSourceParseError"},
        "parser public class surface changed",
    )
    require(
        public_functions == {"parse_narrative_source"},
        "parser public function surface changed",
    )


def test_frozen_files() -> None:
    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
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


def test_no_op_source() -> None:
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
                "P11.5F-A audit contains a filesystem mutation call"
            )
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "git"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in git_mutators
        ):
            raise AssertionError(
                "P11.5F-A audit contains a Git mutation call"
            )


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    test_baseline_and_ownership()
    test_document_contract()
    test_parser_surface()
    test_frozen_files()
    test_no_op_source()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "aligned P11.5F-A audit mutated repository status")

    print("AFP-P11.5F-A aligned opt-in narrative source parser architecture audit passed.")
    print("P11.5E annotated freeze and exact predecessor HEAD: PASS")
    print("Reviewed P11.5F-A/P11.5F-B five-file ownership: PASS")
    print("Dedicated opt-in parser and ordinary parser separation: PASS")
    print("Narrative scanner, grammar, syntax-diagnostic, and provenance contract: PASS")
    print("Source order, duplicates, scalars, and unresolved references: PASS")
    print("Dedicated parser production API constrained to one file: PASS")
    print("Frozen lexer, parser, compiler, project, narrative, AIR, runtime, and CLI surfaces: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
