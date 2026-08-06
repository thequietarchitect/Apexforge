"""Executable P11.5E-A audit aligned to the reviewed P11.5E-B successor."""

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
    / "P11_5E_NARRATIVE_SOURCE_SYNTAX_FOUNDATION_ARCHITECTURE_AUDIT.md"
)
BASELINE_TAG = "afp-p11.5d-freeze"
EXPECTED_HEAD = "c264a2c1f1eb9e1058bc859b78da86c3dad1b28b"
EXPECTED_BRANCH = "p11.5e-narrative-source-syntax"

AUDIT_PATHS = {
    "apexforge/p11_5e_narrative_source_syntax_foundation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5E_NARRATIVE_SOURCE_SYNTAX_FOUNDATION_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_source.py",
    "apexforge/p11_5e_immutable_narrative_source_ast_smoke_test.py",
    "docs/p11/P11_5E_IMMUTABLE_NARRATIVE_SOURCE_AST_CONTRACT.md",
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
        "P11.5E is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5E predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5D controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5D controlling freeze resolves incorrectly",
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
        "reviewed P11.5E-A/P11.5E-B path set changed",
    )


def test_aligned_architecture_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(document.split()).casefold()
    required = (
        "P11.5D is the frozen validation predecessor",
        "reviewed P11.5E-B successor",
        "source syntax AST != narrative semantic model",
        "parsing != semantic lowering",
        "one opt-in narrative source document",
        "one story root",
        "every declared name carries a source span",
        "every reference carries a source span",
        "every scalar value carries a source span",
        "preserve source order and duplicates",
        "one passive production module",
        "no lexer changes",
        "no parser changes",
        "no compiler integration",
        "no project integration",
        "no diagnostics",
        "no language-server integration",
        "no Visual Studio integration",
    )
    for phrase in required:
        require(
            phrase.casefold() in normalized,
            f"aligned P11.5E audit omits required phrase: {phrase}",
        )


def test_exact_source_ast_production_surface() -> None:
    expected = {
        "NarrativeSourceIdentifier",
        "NarrativeSourceScalar",
        "NarrativeSourceReference",
        "NarrativeSourceCharacter",
        "NarrativeSourceScene",
        "NarrativeSourceDialogue",
        "NarrativeSourceChoicePath",
        "NarrativeSourceChoice",
        "NarrativeSourcePerspective",
        "NarrativeSourceTimeline",
        "NarrativeSourceStateFact",
        "NarrativeSourceState",
        "NarrativeSourceContinuityConstraint",
        "NarrativeSourceContinuity",
        "NarrativeSourceStory",
        "NarrativeSourceDocument",
    }
    locations: dict[str, set[str]] = {}
    for path in (PACKAGE_DIRECTORY / "language").rglob("*.py"):
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in expected:
                locations.setdefault(node.name, set()).add(relative)

    require(set(locations) == expected, "source-AST declaration set changed")
    require(
        all(
            paths == {"apexforge/language/narrative_source.py"}
            for paths in locations.values()
        ),
        "source-AST declarations escaped one passive production module",
    )


def test_frozen_operational_files() -> None:
    for relative in (
        "apexforge/language/source.py",
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


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    test_frozen_baseline_and_reviewed_ownership()
    test_aligned_architecture_contract()
    test_exact_source_ast_production_surface()
    test_frozen_operational_files()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "aligned P11.5E-A audit mutated repository status")

    print("AFP-P11.5E-A aligned Narrative Source Syntax foundation architecture audit passed.")
    print("P11.5D annotated freeze and exact predecessor HEAD: PASS")
    print("Reviewed P11.5E-A/P11.5E-B five-file ownership: PASS")
    print("Source AST, semantic model, graph, and validation separations: PASS")
    print("Narrative vocabulary, one-story document, and source-span boundary: PASS")
    print("Passive source-AST production API constrained to one file: PASS")
    print("No lexer, parser, compiler, project, diagnostic, runtime, or editor integration: PASS")
    print("Frozen narrative and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
