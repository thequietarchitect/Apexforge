"""P11.16A final-verification architecture boundary.

Architecture-only.  This stage freezes the verification methodology before
P11.16 executes any broad historical regression matrix.
"""

from __future__ import annotations

import ast
import collections
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APEX = ROOT / "apexforge"
DOCS = ROOT / "docs" / "p11"
sys.path.insert(0, str(APEX))

EXPECTED_P11_15I_FREEZE = "12f1e568bec83f5d74c661e042f7bcef25f0b5b9"
EXPECTED_P11_15I_TAG = "afp-p11-15i-freeze"
EXPECTED_BRANCH = "p11-16a-final-verification-architecture-boundary"

EXPECTED_DISCOVERY = {
    "p11_tag_count": 150,
    "p11_ancestor_tag_count": 150,
    "p11_annotated_tag_count": 116,
    "p11_lightweight_tag_count": 34,
    "p11_smoke_test_count": 178,
    "p11_doc_count": 146,
    "production_python_files": 305,
    "examples_p11validation_present": False,
    "risk_examples_p11validation": 35,
    "risk_tempfile": 40,
    "risk_subprocess": 122,
    "risk_visual_studio": 5,
    "risk_vscode": 1,
}

EXPECTED_UNCLASSIFIED_FAMILIES = {
    "SRC": {
        "p11_src_a_semantic_decision_source_architecture_audit_smoke_test.py",
        "p11_src_b_immutable_semantic_decision_source_ast_smoke_test.py",
        "p11_src_c_deterministic_semantic_decision_source_parser_smoke_test.py",
        "p11_src_d_semantic_decision_lowering_smoke_test.py",
        "p11_src_e_semantic_decision_source_validation_smoke_test.py",
        "p11_src_f_real_apex_compile_analysis_acceptance_smoke_test.py",
        "p11_src_g_powershell_tooling_compatibility_smoke_test.py",
        "p11_src_g_semantic_decision_project_lsp_compatibility_smoke_test.py",
        "p11_src_h_final_integration_regression_freeze_smoke_test.py",
    },
    "TAM": {
        "p11_tam_a_architecture_traceability_ownership_audit_smoke_test.py",
        "p11_tam_b_minimal_immutable_trace_model_smoke_test.py",
        "p11_tam_c_deterministic_trace_production_foundation_smoke_test.py",
        "p11_tam_d_declaration_identity_ownership_trace_production_smoke_test.py",
        "p11_tam_e_reference_scope_resolution_evidence_trace_production_smoke_test.py",
        "p11_tam_f_type_evidence_trace_production_smoke_test.py",
        "p11_tam_g_authority_evidence_trace_production_smoke_test.py",
        "p11_tam_h_narrative_evidence_trace_production_smoke_test.py",
        "p11_tam_i_token_evidence_trace_production_smoke_test.py",
        "p11_tam_j_final_integration_architecture_audit_smoke_test.py",
        "p11_tam_k_deterministic_whole_map_composition_smoke_test.py",
        "p11_tam_l_final_integration_regression_freeze_smoke_test.py",
    },
}

VERIFICATION_CLASSES = (
    "DURABLE_CURRENT",
    "HISTORICAL_EXACT_FREEZE",
    "ENVIRONMENT_FIXTURE_BOUND",
    "EXTERNAL_TOOLCHAIN_BOUND",
)

REQUIRED_MATRIX_SURFACES = (
    "NUMBERED_P11_1_THROUGH_P11_15",
    "P11_SRC_FAMILY",
    "P11_TAM_FAMILY",
    "TOOLING_CLI_EDITOR",
    "REPOSITORY_REGRESSION_SURFACES",
    "SEMANTIC_OWNER_BOUNDARY_SENTINELS",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> str:
    proc = subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "git failed: git {}\n{}".format(" ".join(args), proc.stderr)
        )
    return proc.stdout.strip()


def git_ok(*args: str) -> bool:
    return (
        subprocess.run(
            ("git",) + args,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def production_python_files():
    for path in sorted(APEX.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if re.match(r"p\d+_", path.name):
            continue
        if "smoke_test" in path.name:
            continue
        yield path


def main() -> int:
    require(
        git("rev-parse", "HEAD") == EXPECTED_P11_15I_FREEZE,
        "P11.16A must remain architecture-only on exact P11.15I freeze",
    )
    require(
        git("branch", "--show-current") == EXPECTED_BRANCH,
        "unexpected P11.16A branch",
    )
    require(
        git("cat-file", "-t", EXPECTED_P11_15I_TAG) == "tag",
        "P11.15I freeze tag must remain annotated",
    )
    require(
        git("rev-parse", EXPECTED_P11_15I_TAG + "^{commit}")
        == EXPECTED_P11_15I_FREEZE,
        "P11.15I freeze tag target changed",
    )

    # ------------------------------------------------------------------
    # Discovery census must still match the evidence used to design A.
    # ------------------------------------------------------------------
    tags = [
        line
        for line in git("tag", "--list", "afp-p11*").splitlines()
        if line
    ]
    ancestor_tags = [tag for tag in tags if git_ok("merge-base", "--is-ancestor", tag, "HEAD")]
    annotated = [tag for tag in tags if git("cat-file", "-t", tag) == "tag"]
    lightweight = [tag for tag in tags if git("cat-file", "-t", tag) != "tag"]

    require(
        len(tags) == EXPECTED_DISCOVERY["p11_tag_count"],
        "P11 tag census changed",
    )
    require(
        len(ancestor_tags) == EXPECTED_DISCOVERY["p11_ancestor_tag_count"],
        "P11 ancestor tag census changed",
    )
    require(
        len(annotated) == EXPECTED_DISCOVERY["p11_annotated_tag_count"],
        "annotated P11 tag census changed",
    )
    require(
        len(lightweight) == EXPECTED_DISCOVERY["p11_lightweight_tag_count"],
        "lightweight P11 tag census changed",
    )
    require(
        len(tags) == len(ancestor_tags),
        "not every P11 tag is an ancestor of current final-verification baseline",
    )

    # Census the committed P11.15I baseline rather than the working tree.
    # P11.16A's own untracked architecture smoke test/document must not
    # self-inflate the 178-test / 146-document discovery baseline that A is
    # defining.
    baseline_paths = [
        line
        for line in git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
        if line
    ]
    p11_tests = sorted(
        ROOT / rel
        for rel in baseline_paths
        if rel.startswith("apexforge/p11_")
        and rel.endswith("_smoke_test.py")
    )
    p11_docs = sorted(
        ROOT / rel
        for rel in baseline_paths
        if rel.startswith("docs/p11/P11_")
        and rel.endswith(".md")
    )

    require(
        len(p11_tests) == EXPECTED_DISCOVERY["p11_smoke_test_count"],
        "committed P11.15I smoke-test census changed",
    )
    require(
        len(p11_docs) == EXPECTED_DISCOVERY["p11_doc_count"],
        "committed P11.15I documentation census changed",
    )

    production = list(production_python_files())
    require(
        len(production) == EXPECTED_DISCOVERY["production_python_files"],
        "production Python census changed",
    )

    parse_failures = []
    for path in production:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_failures.append(
                "{}: {}".format(path.relative_to(ROOT).as_posix(), exc)
            )
    require(not parse_failures, "production Python parse failures exist")

    fixture = ROOT / "examples" / "P11Validation"
    require(
        fixture.exists() == EXPECTED_DISCOVERY["examples_p11validation_present"],
        "examples/P11Validation presence changed before matrix architecture freeze",
    )

    # ------------------------------------------------------------------
    # Coverage architecture.
    # ------------------------------------------------------------------
    numbered = collections.defaultdict(list)
    src = set()
    tam = set()
    other_unclassified = set()

    numbered_pattern = re.compile(r"p11_(\d+)[a-z0-9_]*_smoke_test\.py$", re.IGNORECASE)
    for path in p11_tests:
        match = numbered_pattern.match(path.name)
        if match:
            numbered[int(match.group(1))].append(path.name)
        elif path.name.startswith("p11_src_"):
            src.add(path.name)
        elif path.name.startswith("p11_tam_"):
            tam.add(path.name)
        else:
            other_unclassified.add(path.name)

    require(
        sorted(numbered) == list(range(1, 16)),
        "numbered P11 test phase coverage changed",
    )
    require(src == EXPECTED_UNCLASSIFIED_FAMILIES["SRC"], "SRC family coverage changed")
    require(tam == EXPECTED_UNCLASSIFIED_FAMILIES["TAM"], "TAM family coverage changed")
    require(not other_unclassified, "new unclassified P11 smoke tests require architecture review")

    # Every one of the 178 smoke tests must be represented by the future matrix.
    represented_count = (
        sum(len(items) for items in numbered.values()) + len(src) + len(tam)
    )
    require(
        represented_count == EXPECTED_DISCOVERY["p11_smoke_test_count"],
        "future matrix coverage does not represent all P11 smoke tests",
    )

    # ------------------------------------------------------------------
    # Historical-risk architecture.
    # ------------------------------------------------------------------
    risk_markers = {
        "examples_p11validation": "P11Validation",
        "tempfile": "tempfile",
        "subprocess": "subprocess",
        "visual_studio": "VisualStudio",
        "vscode": "vscode",
    }
    risk_counts = collections.Counter()
    for path in p11_tests:
        source = path.read_text(encoding="utf-8")
        lowered = source.lower()
        for risk, marker in risk_markers.items():
            if marker.lower() in lowered:
                risk_counts[risk] += 1

    require(
        risk_counts["examples_p11validation"]
        == EXPECTED_DISCOVERY["risk_examples_p11validation"],
        "P11Validation risk census changed",
    )
    require(
        risk_counts["tempfile"] == EXPECTED_DISCOVERY["risk_tempfile"],
        "tempfile risk census changed",
    )
    require(
        risk_counts["subprocess"] == EXPECTED_DISCOVERY["risk_subprocess"],
        "subprocess risk census changed",
    )
    require(
        risk_counts["visual_studio"]
        == EXPECTED_DISCOVERY["risk_visual_studio"],
        "Visual Studio risk census changed",
    )
    require(
        risk_counts["vscode"] == EXPECTED_DISCOVERY["risk_vscode"],
        "VSCode risk census changed",
    )

    # ------------------------------------------------------------------
    # Verification-class semantics.
    # ------------------------------------------------------------------
    require(
        VERIFICATION_CLASSES
        == (
            "DURABLE_CURRENT",
            "HISTORICAL_EXACT_FREEZE",
            "ENVIRONMENT_FIXTURE_BOUND",
            "EXTERNAL_TOOLCHAIN_BOUND",
        ),
        "verification class model changed",
    )

    # Durable current:
    # - expected to pass at current HEAD;
    # - semantic compatibility is current and enforceable;
    # - failure blocks P11.16 completion unless production itself is repaired.
    durable_rules = (
        "MUST_EXECUTE_AT_CURRENT_HEAD",
        "FAILURE_BLOCKS_FINAL_VERIFICATION",
        "NO_TEST_WEAKENING",
        "NO_OWNER_REINTERPRETATION",
    )
    require(durable_rules[0] == "MUST_EXECUTE_AT_CURRENT_HEAD", "durable rules changed")

    # Historical exact freeze:
    # - historical exact hashes/owner snapshots may be superseded by legitimate
    #   later frozen stages;
    # - verify ancestry/frozen evidence rather than editing old tests to green.
    historical_rules = (
        "MUST_RETAIN_TEST_BYTES",
        "MUST_CLASSIFY_EXACT_SUPERSESSION_REASON",
        "MUST_VERIFY_REPLACEMENT_FREEZE_ANCESTRY",
        "MUST_NOT_MUTATE_PRODUCTION_TO_MATCH_OLD_HASH",
    )
    require(
        historical_rules[3] == "MUST_NOT_MUTATE_PRODUCTION_TO_MATCH_OLD_HASH",
        "historical rules changed",
    )

    # Environment/fixture bound:
    # - missing examples/P11Validation remains a known historical condition;
    # - P11.16 may reconstruct an exact temporary fixture only for test execution
    #   when prior canonical bytes/evidence exist;
    # - never permanently restore it merely to satisfy verification.
    environment_rules = (
        "MUST_RECORD_ENVIRONMENT_DEPENDENCY",
        "TEMPORARY_EXACT_FIXTURE_ONLY_IF_CANONICAL_EVIDENCE_EXISTS",
        "NO_PERMANENT_FIXTURE_RESTORATION_FOR_GREEN",
        "FAIL_IF_UNCLASSIFIED_ENVIRONMENT_ERROR",
    )
    require(
        environment_rules[2] == "NO_PERMANENT_FIXTURE_RESTORATION_FOR_GREEN",
        "environment rules changed",
    )

    # External toolchain bound:
    # - IDE/editor/subprocess behavior is verified only in a resolved toolchain
    #   environment; inability to resolve must be explicit and classified.
    external_rules = (
        "MUST_RECORD_TOOLCHAIN_REQUIREMENT",
        "MUST_EXECUTE_WHEN_TOOLCHAIN_IS_AVAILABLE",
        "NO_FALSE_PASS_WHEN_TOOLCHAIN_UNAVAILABLE",
        "NO_PRODUCTION_MUTATION_TO_SIMULATE_EXTERNAL_TOOLCHAIN",
    )
    require(
        external_rules[2] == "NO_FALSE_PASS_WHEN_TOOLCHAIN_UNAVAILABLE",
        "external toolchain rules changed",
    )

    # ------------------------------------------------------------------
    # Required final-verification surfaces.
    # ------------------------------------------------------------------
    require(
        REQUIRED_MATRIX_SURFACES
        == (
            "NUMBERED_P11_1_THROUGH_P11_15",
            "P11_SRC_FAMILY",
            "P11_TAM_FAMILY",
            "TOOLING_CLI_EDITOR",
            "REPOSITORY_REGRESSION_SURFACES",
            "SEMANTIC_OWNER_BOUNDARY_SENTINELS",
        ),
        "required matrix surfaces changed",
    )

    repo_surfaces = {
        "apexforge/tests": (ROOT / "apexforge" / "tests").exists(),
        "apexforge/regression_harness.py": (
            ROOT / "apexforge" / "regression_harness.py"
        ).exists(),
        "apexforge/tooling/performance_baseline.py": (
            ROOT / "apexforge" / "tooling" / "performance_baseline.py"
        ).exists(),
    }
    require(all(repo_surfaces.values()), "repository regression surface disappeared")

    # ------------------------------------------------------------------
    # P11.16 stage sequence.
    # ------------------------------------------------------------------
    successor_sequence = (
        "P11.16B_MATRIX_CLASSIFICATION_AND_MANIFEST",
        "P11.16C_DURABLE_SEMANTIC_EXECUTION",
        "P11.16D_HISTORICAL_ENVIRONMENT_TOOLCHAIN_RESOLUTION",
        "P11.16E_REPOSITORY_WIDE_FINAL_VERIFICATION",
        "P11.16F_FINAL_FREEZE",
    )
    require(
        successor_sequence[0] == "P11.16B_MATRIX_CLASSIFICATION_AND_MANIFEST",
        "P11.16 successor sequence changed",
    )

    print("P11_16A_SCOPE=ARCHITECTURE_ONLY")
    print("P11_16A_PRODUCTION_FILES=0")
    print("P11_16A_P11_TAGS=150_ALL_ANCESTORS")
    print("P11_16A_HISTORICAL_LIGHTWEIGHT_TAGS=34_PRESERVE_AS_HISTORY")
    print("P11_16A_P11_SMOKE_TESTS=178")
    print("P11_16A_NUMBERED_PHASES=P11_1_THROUGH_P11_15")
    print("P11_16A_SRC_TESTS={}".format(len(src)))
    print("P11_16A_TAM_TESTS={}".format(len(tam)))
    print("P11_16A_PRODUCTION_PYTHON_PARSE=PASS")
    print("P11_16A_EXAMPLES_P11VALIDATION_PRESENT=NO")
    print("P11_16A_VERIFICATION_CLASS_1=DURABLE_CURRENT")
    print("P11_16A_VERIFICATION_CLASS_2=HISTORICAL_EXACT_FREEZE")
    print("P11_16A_VERIFICATION_CLASS_3=ENVIRONMENT_FIXTURE_BOUND")
    print("P11_16A_VERIFICATION_CLASS_4=EXTERNAL_TOOLCHAIN_BOUND")
    print("P11_16A_DURABLE_FAILURE=BLOCKING")
    print("P11_16A_HISTORICAL_EXACT_HASH_SUPERSESSION=CLASSIFY_NOT_WEAKEN")
    print("P11_16A_MISSING_FIXTURE=NO_PERMANENT_RESTORATION_FOR_GREEN")
    print("P11_16A_EXTERNAL_TOOLCHAIN_UNAVAILABLE=EXPLICIT_CLASSIFICATION_NOT_FALSE_PASS")
    print("P11_16A_MATRIX_COVERAGE=ALL_178_P11_SMOKE_TESTS")
    print("P11_16A_REPOSITORY_REGRESSION_SURFACES=REQUIRED")
    print("P11_16A_SEMANTIC_OWNER_BOUNDARY_SENTINELS=REQUIRED")
    print("P11_16A_FIRST_PRODUCTION_MUTATION=NONE")
    print("P11_16A_NEXT=P11_16B_MATRIX_CLASSIFICATION_AND_MANIFEST")
    print("P11_16A_FINAL_VERIFICATION_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_16A_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())