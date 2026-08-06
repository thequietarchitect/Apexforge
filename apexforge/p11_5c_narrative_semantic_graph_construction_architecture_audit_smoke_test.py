"""Executable architecture contract for P11.5C-A and reviewed P11.5C-B."""

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
    / "P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_ARCHITECTURE_AUDIT.md"
)
BASELINE_TAG = "afp-p11.2i-freeze"
SEMANTIC_PREDECESSOR_TAG = "afp-p11.5b-freeze"
EXPECTED_BRANCH = "p11.5c-narrative-semantic-graph"
P11_5C_A_OWNED_PATHS = {
    "apexforge/p11_5c_narrative_semantic_graph_construction_architecture_audit_smoke_test.py",
    "docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_ARCHITECTURE_AUDIT.md",
}
P11_5C_B_OWNED_PATHS = {
    "apexforge/language/narrative_graph.py",
    "apexforge/p11_5c_narrative_semantic_graph_construction_smoke_test.py",
    "docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_CONTRACT.md",
}
REVIEWED_BRANCH_PATHS = P11_5C_A_OWNED_PATHS | P11_5C_B_OWNED_PATHS


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


def test_baseline_and_reviewed_candidate_ownership() -> None:
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.2I controlling freeze is not annotated",
    )
    require(
        git("cat-file", "-t", SEMANTIC_PREDECESSOR_TAG).strip() == "tag",
        "P11.5B semantic predecessor is not annotated",
    )
    ancestry = subprocess.run(
        (
            "git",
            "merge-base",
            "--is-ancestor",
            SEMANTIC_PREDECESSOR_TAG,
            BASELINE_TAG,
        ),
        cwd=REPOSITORY_ROOT,
    )
    require(
        ancestry.returncode == 0,
        "P11.5B is not an ancestor of the P11.2I integration freeze",
    )
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5C audit is running on an unexpected branch",
    )

    committed = {
        item
        for item in git(
            "diff", "--name-only", f"{BASELINE_TAG}..HEAD"
        ).splitlines()
        if item
    }
    working = {
        line[3:].replace("\\", "/")
        for line in git(
            "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if len(line) >= 4
        and not line[3:].replace("\\", "/").startswith(
            "examples/P11Validation/"
        )
    }
    require(
        committed | working == REVIEWED_BRANCH_PATHS,
        "reviewed P11.5C-A/P11.5C-B branch path set changed",
    )
    require(
        all(
            (REPOSITORY_ROOT / path).is_file()
            for path in REVIEWED_BRANCH_PATHS
        ),
        "a reviewed P11.5C file is missing",
    )


def test_audit_contract() -> None:
    document = DOCUMENT_PATH.read_text(encoding="utf-8")
    required = (
        "P11.2I is the controlling integration freeze",
        "P11.5B is the semantic predecessor",
        "Reviewed P11.5C-B successor",
        "declared occurrences retain duplicates",
        "referenced-only identities",
        "fixed relation-family order",
        "source tuple order",
        "Narrative Semantic Graph != AIR",
        "Narrative Semantic Graph != artifact v1",
        "no parser integration",
        "no compiler integration",
        "no runtime integration",
        "no diagnostics",
        "no serialization",
    )
    normalized = " ".join(document.split())
    for phrase in required:
        require(phrase in normalized, f"audit omits required phrase: {phrase}")

    relation_terms = {
        "containment",
        "dialogue participation",
        "choice destination",
        "perspective viewpoint",
        "timeline membership",
        "temporal precedence",
        "narrative-state subject",
        "continuity subject",
    }
    require(
        all(term in document for term in relation_terms),
        "audit omits a required relation family",
    )


def test_reviewed_graph_production_boundary() -> None:
    graph_names = {
        "NarrativeSemanticGraph",
        "NarrativeGraphNode",
        "NarrativeGraphEdge",
        "build_narrative_semantic_graph",
    }
    declaration_files: set[str] = set()
    for path in PACKAGE_DIRECTORY.rglob("*.py"):
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(
                node,
                (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            )
        }
        if names & graph_names:
            declaration_files.add(relative)
    require(
        declaration_files == {"apexforge/language/narrative_graph.py"},
        "graph production API escaped its reviewed one-file boundary",
    )

    graph_text = (
        PACKAGE_DIRECTORY / "language" / "narrative_graph.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "BuildDiagnostic",
        "APX-NARRATIVE-",
        "APX-STORY-",
        "APX-CONTINUITY-",
        "parse_",
        "AIRProgram",
        "language.project",
        "language.parser",
        "runtime.",
    )
    require(
        all(marker not in graph_text for marker in forbidden),
        "reviewed graph module acquired forbidden integration",
    )

    baseline_model = git(
        "show", f"{BASELINE_TAG}:apexforge/language/narrative_model.py"
    ).encode("utf-8")
    current_model = (
        PACKAGE_DIRECTORY / "language" / "narrative_model.py"
    ).read_bytes()
    require(
        current_model == baseline_model,
        "P11.5B narrative_model.py changed during P11.5C",
    )

    for relative in (
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/air/model.py",
        "apexforge/air/serialization.py",
        "apexforge/tooling/cli.py",
    ):
        require(
            (REPOSITORY_ROOT / relative).read_bytes()
            == git("show", f"{BASELINE_TAG}:{relative}").encode("utf-8"),
            f"operational baseline changed: {relative}",
        )


def main() -> None:
    before = git("status", "--porcelain=v1", "--untracked-files=all")
    test_baseline_and_reviewed_candidate_ownership()
    test_audit_contract()
    test_reviewed_graph_production_boundary()
    after = git("status", "--porcelain=v1", "--untracked-files=all")
    require(before == after, "P11.5C-A audit mutated repository status")

    print("AFP-P11.5C-A Narrative Semantic Graph architecture audit passed.")
    print("P11.2I controlling freeze and P11.5B semantic ancestry: PASS")
    print("Reviewed P11.5C-A/P11.5C-B five-file ownership: PASS")
    print("Graph purpose, ordering, duplicate, and reference policy: PASS")
    print("Relation-family construction boundary: PASS")
    print("Graph production API constrained to one passive file: PASS")
    print("P11.5B and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
