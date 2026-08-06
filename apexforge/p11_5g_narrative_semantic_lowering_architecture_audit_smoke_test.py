"""Executable P11.5G-A audit aligned to the reviewed P11.5G-B lowerer."""

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
    / "P11_5G_NARRATIVE_SEMANTIC_LOWERING_ARCHITECTURE_AUDIT.md"
)
BASELINE_TAG = "afp-p11.5f-freeze"
EXPECTED_HEAD = "f24bd96217fb541f105e3bb1f1564f4c593e5111"
EXPECTED_BRANCH = "p11.5g-narrative-semantic-lowering"

AUDIT_PATHS = {
    "apexforge/p11_5g_narrative_semantic_lowering_architecture_audit_smoke_test.py",
    "docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_lowering.py",
    "apexforge/p11_5g_narrative_semantic_lowering_smoke_test.py",
    "docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_CONTRACT.md",
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
        "P11.5G is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5G predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5F controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5F controlling freeze resolves incorrectly",
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
        "reviewed P11.5G-A/P11.5G-B path set changed",
    )


def test_aligned_architecture_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(
        document.replace(chr(96), "").split()
    ).casefold()
    required = (
        "P11.5F is the frozen parser predecessor",
        "reviewed P11.5G-B successor",
        "source AST != semantic model",
        "semantic lowering != graph construction",
        "one dedicated production module",
        "language/narrative_lowering.py",
        "NarrativeSemanticLoweringError",
        "lower_narrative_source",
        "single-segment identity paths",
        "reference expected kind becomes identity kind",
        "source order and duplicates",
        "scalar text is preserved",
        "scalar source-form kind is not preserved",
        "source spans remain in the source AST",
        "APX-NARRATIVE-LOWERING",
        "first deterministic lowering failure",
        "no name resolution",
        "no graph construction",
        "no narrative validation",
        "no parser invocation",
        "no compiler integration",
        "no project integration",
        "no runtime integration",
        "no language-server integration",
        "no Visual Studio integration",
        "no changes to language/narrative_source.py",
        "no changes to language/narrative_model.py",
        "no changes to language/narrative_parser.py",
    )
    for phrase in required:
        require(
            phrase.casefold() in normalized,
            f"aligned P11.5G audit omits required phrase: {phrase}",
        )


def test_exact_lowering_production_surface() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_lowering.py"
    require(module_path.is_file(), "P11.5G-B lowering module is missing")
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
        public_classes == {"NarrativeSemanticLoweringError"},
        "lowering public class surface changed",
    )
    require(
        public_functions == {"lower_narrative_source"},
        "lowering public function surface changed",
    )


def test_frozen_source_parser_semantic_and_operational_surfaces() -> None:
    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
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
                "P11.5G-A audit contains a filesystem mutation call"
            )
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "git"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in git_mutators
        ):
            raise AssertionError(
                "P11.5G-A audit contains a Git mutation call"
            )


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    test_frozen_baseline_and_reviewed_ownership()
    test_aligned_architecture_contract()
    test_exact_lowering_production_surface()
    test_frozen_source_parser_semantic_and_operational_surfaces()
    test_audit_is_repository_no_op()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "aligned P11.5G-A audit mutated repository status")

    print("AFP-P11.5G-A aligned narrative semantic lowering architecture audit passed.")
    print("P11.5F annotated freeze and exact predecessor HEAD: PASS")
    print("Reviewed P11.5G-A/P11.5G-B five-file ownership: PASS")
    print("Source AST, semantic model, graph, and validation separations: PASS")
    print("Deterministic identity, reference, scalar, order, and duplicate mapping: PASS")
    print("Source-aware lowering failure boundary: PASS")
    print("Dedicated lowering production API constrained to one file: PASS")
    print("Frozen source, parser, semantic, graph, validation, compiler, project, runtime, and CLI surfaces: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
