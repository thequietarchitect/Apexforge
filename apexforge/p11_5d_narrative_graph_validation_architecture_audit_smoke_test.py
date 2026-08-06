"""Executable P11.5D-A audit aligned to the reviewed P11.5D-B successor."""

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
    / "P11_5D_NARRATIVE_GRAPH_VALIDATION_ARCHITECTURE_AUDIT.md"
)

BASELINE_TAG = "afp-p11.5c-freeze"
EXPECTED_HEAD = "d7d19bb84845400c4b004c52e011c89a4a9b1c0d"
EXPECTED_BRANCH = "p11.5d-narrative-graph-validation"

AUDIT_PATHS = {
    "apexforge/p11_5d_narrative_graph_validation_architecture_audit_smoke_test.py",
    "docs/p11/P11_5D_NARRATIVE_GRAPH_VALIDATION_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_validation.py",
    "apexforge/p11_5d_passive_narrative_graph_validation_smoke_test.py",
    "docs/p11/P11_5D_PASSIVE_NARRATIVE_GRAPH_VALIDATION_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS

PROTECTED_BASELINE_PATHS = (
    "apexforge/language/narrative_model.py",
    "apexforge/language/narrative_graph.py",
    "apexforge/language/parser.py",
    "apexforge/language/compiler.py",
    "apexforge/language/project.py",
    "apexforge/air/model.py",
    "apexforge/air/serialization.py",
    "apexforge/runtime/engine.py",
    "apexforge/tooling/cli.py",
)


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
        "P11.5D is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5D predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5C controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5C controlling freeze resolves incorrectly",
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
        "reviewed P11.5D-A/P11.5D-B path set changed",
    )


def test_aligned_architecture_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    normalized = " ".join(document.split()).casefold()

    required_phrases = (
        "P11.5C is the frozen construction predecessor",
        "reviewed P11.5D-B successor",
        "validation consumes the graph without mutating it",
        "classification is not a diagnostic",
        "duplicate declaration",
        "referenced-only identity",
        "conflicting state value",
        "temporal cycle",
        "repeated relation evidence",
        "continuity assertion cluster",
        "multiple perspectives are not inherently contradictory",
        "free-form continuity text is not semantically interpreted",
        "deterministic first-evidence order",
        "one passive production module",
        "no parser integration",
        "no compiler integration",
        "no runtime integration",
        "no diagnostic codes",
        "no source spans",
        "no graph serialization",
    )
    for phrase in required_phrases:
        require(
            phrase.casefold() in normalized,
            f"aligned P11.5D audit omits required phrase: {phrase}",
        )


def test_exact_production_validation_surface() -> None:
    expected = {
        "NarrativeValidationFinding",
        "NarrativeValidationReport",
        "validate_narrative_semantic_graph",
    }
    locations: dict[str, set[str]] = {}

    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ) and node.name in expected:
                locations.setdefault(node.name, set()).add(relative)

    require(
        set(locations) == expected,
        "reviewed passive validation declarations changed",
    )
    require(
        all(
            paths == {"apexforge/language/narrative_validation.py"}
            for paths in locations.values()
        ),
        "passive validation declarations escaped one production module",
    )


def test_frozen_predecessor_and_operational_preservation() -> None:
    for relative in PROTECTED_BASELINE_PATHS:
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
    test_exact_production_validation_surface()
    test_frozen_predecessor_and_operational_preservation()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "aligned P11.5D-A audit mutated repository status")

    print("AFP-P11.5D-A aligned Narrative Graph validation architecture audit passed.")
    print("P11.5C annotated freeze and exact predecessor HEAD: PASS")
    print("Reviewed P11.5D-A/P11.5D-B five-file ownership: PASS")
    print("Deterministic structural evidence classifications: PASS")
    print("Continuity-text and perspective non-contradiction boundaries: PASS")
    print("Passive validator production API constrained to one file: PASS")
    print("Frozen graph and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
