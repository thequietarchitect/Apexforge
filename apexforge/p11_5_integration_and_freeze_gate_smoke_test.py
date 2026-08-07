"""Executable P11.5 integration and freeze-gate smoke test."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
DOCUMENT_DIRECTORY = REPOSITORY_ROOT / "docs" / "p11"

EXPECTED_BRANCH = "p11.5-integration-and-freeze-gate"
BASELINE_TAG = "afp-p11.5i-freeze"
EXPECTED_BASELINE_HEAD = "d51d052ce7ac29e73753bc741ba1818c712e6473"

FROZEN_SLICES = (
    (
        "P11.5A",
        "afp-p11.5a-freeze",
        "3349617a689eb0d9c9849dc604f749d7951d62a0",
    ),
    (
        "P11.5B",
        "afp-p11.5b-freeze",
        "52a3e96194c5474b460076837d2cdbae00a93294",
    ),
    (
        "P11.5C",
        "afp-p11.5c-freeze",
        "d7d19bb84845400c4b004c52e011c89a4a9b1c0d",
    ),
    (
        "P11.5D",
        "afp-p11.5d-freeze",
        "c264a2c1f1eb9e1058bc859b78da86c3dad1b28b",
    ),
    (
        "P11.5E",
        "afp-p11.5e-freeze",
        "eba9a27a34563a8df5f77b796c82b032ab2b0485",
    ),
    (
        "P11.5F",
        "afp-p11.5f-freeze",
        "f24bd96217fb541f105e3bb1f1564f4c593e5111",
    ),
    (
        "P11.5G",
        "afp-p11.5g-freeze",
        "6afe6a3a8e3842a27bbaba99aaef379485a31c5b",
    ),
    (
        "P11.5H",
        "afp-p11.5h-freeze",
        "f9af32adb5cf56a5d78f6bcd59ed4ecc70c933c1",
    ),
    (
        "P11.5I",
        "afp-p11.5i-freeze",
        EXPECTED_BASELINE_HEAD,
    ),
)

CLOSURE_PATHS = {
    "apexforge/p11_5_integration_and_freeze_gate_smoke_test.py",
    "docs/p11/P11_5_INTEGRATION_AND_FREEZE_GATE.md",
}

EXPECTED_PRODUCTION_MODULES = {
    "apexforge/language/narrative_analysis.py",
    "apexforge/language/narrative_graph.py",
    "apexforge/language/narrative_lowering.py",
    "apexforge/language/narrative_model.py",
    "apexforge/language/narrative_parser.py",
    "apexforge/language/narrative_source.py",
    "apexforge/language/narrative_validation.py",
    "apexforge/tools/narrative_report.py",
}

EXPECTED_TESTS = {
    "p11_5_integration_and_freeze_gate_smoke_test.py",
    "p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py",
    "p11_5b_minimal_narrative_semantic_model_smoke_test.py",
    "p11_5c_narrative_semantic_graph_construction_architecture_audit_smoke_test.py",
    "p11_5c_narrative_semantic_graph_construction_smoke_test.py",
    "p11_5d_narrative_graph_validation_architecture_audit_smoke_test.py",
    "p11_5d_passive_narrative_graph_validation_smoke_test.py",
    "p11_5e_immutable_narrative_source_ast_smoke_test.py",
    "p11_5e_narrative_source_syntax_foundation_architecture_audit_smoke_test.py",
    "p11_5f_opt_in_narrative_source_parser_architecture_audit_smoke_test.py",
    "p11_5f_opt_in_narrative_source_parser_smoke_test.py",
    "p11_5g_narrative_semantic_lowering_architecture_audit_smoke_test.py",
    "p11_5g_narrative_semantic_lowering_smoke_test.py",
    "p11_5h_opt_in_narrative_analysis_pipeline_architecture_audit_smoke_test.py",
    "p11_5h_opt_in_narrative_analysis_pipeline_smoke_test.py",
    "p11_5i_narrative_analysis_result_reporting_architecture_audit_smoke_test.py",
    "p11_5i_narrative_analysis_result_reporting_smoke_test.py",
}

EXPECTED_DOCUMENTS = {
    "P11_5_INTEGRATION_AND_FREEZE_GATE.md",
    "P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md",
    "P11_5B_MINIMAL_NARRATIVE_SEMANTIC_MODEL_CONTRACT.md",
    "P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_ARCHITECTURE_AUDIT.md",
    "P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_CONTRACT.md",
    "P11_5D_NARRATIVE_GRAPH_VALIDATION_ARCHITECTURE_AUDIT.md",
    "P11_5D_PASSIVE_NARRATIVE_GRAPH_VALIDATION_CONTRACT.md",
    "P11_5E_IMMUTABLE_NARRATIVE_SOURCE_AST_CONTRACT.md",
    "P11_5E_NARRATIVE_SOURCE_SYNTAX_FOUNDATION_ARCHITECTURE_AUDIT.md",
    "P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_ARCHITECTURE_AUDIT.md",
    "P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_CONTRACT.md",
    "P11_5G_NARRATIVE_SEMANTIC_LOWERING_ARCHITECTURE_AUDIT.md",
    "P11_5G_NARRATIVE_SEMANTIC_LOWERING_CONTRACT.md",
    "P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_ARCHITECTURE_AUDIT.md",
    "P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_CONTRACT.md",
    "P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_ARCHITECTURE_AUDIT.md",
    "P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_CONTRACT.md",
}

FROZEN_OPERATIONAL_PATHS = (
    "apexforge/language/lexer.py",
    "apexforge/language/parser.py",
    "apexforge/language/compiler.py",
    "apexforge/language/project.py",
    "apexforge/language/diagnostics.py",
    "apexforge/language/source.py",
    "apexforge/air/model.py",
    "apexforge/air/serialization.py",
    "apexforge/runtime/engine.py",
    "apexforge/tooling/cli.py",
    "apexforge/tools/runtime_report.py",
    "apexforge/regression_harness.py",
)

PROTECTED_FIXTURE_HASH = (
    "93662dc3891887288b9646be8ef33fa4fe7d7413b4bb0ad6918d405a4b5045a9"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str, check: bool = True) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=check,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_controlling_freeze_and_exact_closure_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5 closure gate is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_BASELINE_HEAD,
        "P11.5 closure predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5I controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip()
        == EXPECTED_BASELINE_HEAD,
        "P11.5I controlling freeze resolves incorrectly",
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
        committed | working == CLOSURE_PATHS,
        "P11.5 closure-gate path ownership changed",
    )


def test_all_slice_freezes_and_ancestry() -> None:
    for slice_name, tag, expected_commit in FROZEN_SLICES:
        require(
            git("cat-file", "-t", tag).strip() == "tag",
            f"{slice_name} freeze tag is not annotated",
        )
        require(
            git("rev-parse", f"{tag}^{{}}").strip() == expected_commit,
            f"{slice_name} freeze tag resolves incorrectly",
        )
        ancestor = subprocess.run(
            ("git", "merge-base", "--is-ancestor", expected_commit, "HEAD"),
            cwd=REPOSITORY_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        require(
            ancestor.returncode == 0,
            f"{slice_name} frozen commit is not an ancestor of the closure candidate",
        )


def test_exact_p11_5_inventory() -> None:
    production = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for directory in (
            PACKAGE_DIRECTORY / "language",
            PACKAGE_DIRECTORY / "tools",
        )
        for path in directory.glob("narrative*.py")
    }
    require(
        production == EXPECTED_PRODUCTION_MODULES,
        "P11.5 narrative production-module inventory changed",
    )

    tests = {
        path.name
        for path in PACKAGE_DIRECTORY.glob("p11_5*_smoke_test.py")
    }
    require(
        tests == EXPECTED_TESTS,
        "P11.5 smoke-test inventory changed",
    )

    documents = {
        path.name
        for path in DOCUMENT_DIRECTORY.glob("P11_5*.md")
    }
    require(
        documents == EXPECTED_DOCUMENTS,
        "P11.5 document inventory changed",
    )

    require(
        not tuple(PACKAGE_DIRECTORY.glob("p11_5j*_smoke_test.py")),
        "P11.5J work exists inside the P11.5 closure candidate",
    )
    require(
        not tuple(DOCUMENT_DIRECTORY.glob("P11_5J*.md")),
        "P11.5J documentation exists inside the P11.5 closure candidate",
    )


def test_freeze_gate_document() -> None:
    document = (
        DOCUMENT_DIRECTORY / "P11_5_INTEGRATION_AND_FREEZE_GATE.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(
        document.replace(chr(96), "").split()
    ).casefold()

    required_phrases = (
        "status: freeze candidate",
        "adds no production feature",
        "P11.5A",
        "P11.5B",
        "P11.5C",
        "P11.5D",
        "P11.5E",
        "P11.5F",
        "P11.5G",
        "P11.5H",
        "P11.5I",
        "semantic foundation",
        "immutable source AST",
        "opt-in narrative source parser",
        "semantic lowering",
        "semantic graph",
        "passive validation",
        "analysis pipeline",
        "human-readable reporting",
        "execution remains deferred",
        "CLI integration remains deferred",
        "editor integration remains deferred",
        "syntax highlighting remains deferred",
        "P11.6 has not begun",
        "afp-p11.5-freeze",
        "human freeze checklist",
        "full applicable regression",
        "protected P11Validation fixture",
        "change control after freeze",
    )
    for phrase in required_phrases:
        require(
            phrase.casefold() in normalized,
            f"P11.5 freeze-gate document omits required phrase: {phrase}",
        )


def test_operational_surfaces_remain_at_p11_5i() -> None:
    for relative in FROZEN_OPERATIONAL_PATHS:
        baseline = git("show", f"{BASELINE_TAG}:{relative}").encode("utf-8")
        require(
            (REPOSITORY_ROOT / relative).read_bytes() == baseline,
            f"operational surface changed during P11.5 closure: {relative}",
        )


def test_protected_fixture_and_no_repository_mutation() -> None:
    fixture = REPOSITORY_ROOT / "examples" / "P11Validation" / "main.apex"
    require(fixture.is_file(), "protected P11Validation fixture is missing")
    require(
        sha256(fixture) == PROTECTED_FIXTURE_HASH,
        "protected P11Validation main.apex hash changed",
    )

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    filesystem_mutators = {
        "write_text",
        "write_bytes",
        "unlink",
        "mkdir",
        "rename",
    }
    git_mutators = {
        "add",
        "commit",
        "tag",
        "push",
        "reset",
        "switch",
        "checkout",
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in filesystem_mutators
        ):
            raise AssertionError(
                "P11.5 closure test contains a filesystem mutation call"
            )
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "git"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value in git_mutators
        ):
            raise AssertionError(
                "P11.5 closure test contains a Git mutation call"
            )


def main() -> None:
    before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )

    test_controlling_freeze_and_exact_closure_ownership()
    test_all_slice_freezes_and_ancestry()
    test_exact_p11_5_inventory()
    test_freeze_gate_document()
    test_operational_surfaces_remain_at_p11_5i()
    test_protected_fixture_and_no_repository_mutation()

    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5 closure test mutated repository status")

    print("AFP-P11.5 integration and freeze-gate smoke test passed.")
    print("P11.5I annotated controlling freeze and exact predecessor HEAD: PASS")
    print("P11.5A through P11.5I annotated freezes and ancestry: PASS")
    print("Exact two-file closure-gate ownership: PASS")
    print("Exact eight-module narrative production inventory: PASS")
    print("Exact seventeen-test and seventeen-document inventory: PASS")
    print("Semantic, source, parser, lowering, graph, validation, analysis, and reporting chain: PASS")
    print("Execution, CLI, editor, and syntax-highlighting deferrals retained: PASS")
    print("No P11.5J or P11.6 implementation present: PASS")
    print("Frozen operational surfaces preserved at P11.5I: PASS")
    print("Protected P11Validation fixture hash: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
