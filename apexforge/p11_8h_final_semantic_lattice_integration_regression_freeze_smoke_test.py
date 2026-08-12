"""AFP-P11.8H final semantic-lattice integration regression and freeze audit."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = ROOT / "apexforge"
EXPECTED_BRANCH = "p11.8h-final-integration-regression-freeze"
EXPECTED_G_FREEZE = "5589cd4a40f7ee6f861b1f09cba54af1f91da7f5"

STAGE_TAGS = (
    ("afp-p11.8a-freeze", "9d0043e32d803c7d9ca43b11c48d3b90df5a5112"),
    ("afp-p11.8b-freeze", "63b1dd605723cb9393a6e5d42de16f3b6b67c4a5"),
    ("afp-p11.8c-freeze", "50abea9e27df4b696c12496ae9058f75881e13f8"),
    ("afp-p11.8d-freeze", "b715906ef607b977ed8c1e2e6f75317999ee98d3"),
    ("afp-p11.8e-freeze", "f1510b67bc2f4d0397f5cbfc24693a18bd897eac"),
    ("afp-p11.8f-freeze", "06dc8ca8efd3e3e39aa8ac881284e04f497710ea"),
    ("afp-p11.8g-freeze", EXPECTED_G_FREEZE),
)

SEMANTIC_LATTICE_PRODUCTION_FILES = (
    "apexforge/semantic_lattice/__init__.py",
    "apexforge/semantic_lattice/adapters.py",
    "apexforge/semantic_lattice/authoring.py",
    "apexforge/semantic_lattice/construction.py",
    "apexforge/semantic_lattice/model.py",
    "apexforge/semantic_lattice/records.py",
    "apexforge/semantic_lattice/reporting.py",
    "apexforge/semantic_lattice/validation.py",
)

PREDECESSOR_SMOKES = (
    "p11_8a_parametric_semantic_lattice_architecture_audit_smoke_test.py",
    "p11_8b_minimal_immutable_lattice_model_smoke_test.py",
    "p11_8c_canonical_subject_relations_evidence_smoke_test.py",
    "p11_8d_deterministic_lattice_construction_indexing_smoke_test.py",
    "p11_8e_canonical_projection_adapters_codex_advisory_smoke_test.py",
    "p11_8f_validation_collision_provenance_extension_contracts_smoke_test.py",
    "p11_8g_semantic_lattice_reporting_tooling_compatibility_smoke_test.py",
)

PREDECESSOR_DOCUMENTS = (
    "P11_8A_PARAMETRIC_SEMANTIC_LATTICE_ARCHITECTURE_AUDIT.md",
    "P11_8B_MINIMAL_IMMUTABLE_LATTICE_MODEL_AND_METADATA_AXIS_TAXONOMY.md",
    "P11_8C_CANONICAL_SUBJECT_REFERENCES_RELATIONSHIPS_AND_EVIDENCE_MODEL.md",
    "P11_8D_DETERMINISTIC_LATTICE_CONSTRUCTION_AND_INDEXING.md",
    "P11_8E_CANONICAL_PROJECTION_ADAPTERS_AND_OPTIONAL_CODEX_ADVISORY_ADAPTER.md",
    "P11_8F_VALIDATION_COLLISION_PROVENANCE_AND_EXTENSION_CONTRACTS.md",
    "P11_8G_SEMANTIC_LATTICE_REPORTING_AND_TOOLING_COMPATIBILITY.md",
)

EXPECTED_PUBLIC_SURFACE = (
    "CORE_SEMANTIC_LATTICE_AXES",
    "ParametricSemanticLattice",
    "SemanticLatticeAuthoringProposal",
    "SemanticLatticeAuthoringSource",
    "SemanticLatticeAxis",
    "SemanticLatticeEvidence",
    "SemanticLatticeParameter",
    "SemanticLatticeRelationship",
    "SemanticLatticeSnapshot",
    "SemanticLatticeSubjectReference",
    "adapt_codex_semantic_lattice_proposal",
    "adapt_semantic_lattice_authoring_proposal",
    "construct_semantic_lattice_snapshot",
    "project_air_subject",
    "project_authority_grant_evidence",
    "project_authority_subject",
    "project_declared_air_identity",
    "project_narrative_subject",
    "project_quad_vector_input_subject",
    "project_resultant_vector_evidence",
    "project_tam_traceability_parameter",
    "relationships_for_relation",
    "relationships_from_subject",
    "relationships_to_subject",
    "subjects_for_domain",
    "subjects_for_identity",
    "subjects_for_kind",
    "SemanticLatticeAuthoringValidationReceipt",
    "SemanticLatticeValidationReceipt",
    "validate_codex_semantic_lattice_proposal",
    "validate_semantic_lattice_authoring_proposal",
    "validate_semantic_lattice_snapshot",
    "render_semantic_lattice_authoring_validation_report",
    "render_semantic_lattice_validation_report",
)

ALLOWED_H_PATHS = {
    "apexforge/p11_8h_final_semantic_lattice_integration_regression_freeze_smoke_test.py",
    "docs/p11/P11_8H_FINAL_SEMANTIC_LATTICE_INTEGRATION_REGRESSION_AND_FREEZE.md",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git",) + arguments,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "git command failed: "
            + " ".join(arguments)
            + "\n"
            + completed.stderr.strip()
        )
    return completed.stdout.strip()


def repository_status() -> str:
    return git("status", "--porcelain=v1")


def run_smoke(path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        (sys.executable, "-B", str(path)),
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"regression smoke failed: {path.name}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
    )


def test_stage_freeze_chain_and_branch() -> None:
    require(git("branch", "--show-current") == EXPECTED_BRANCH, "unexpected P11.8H branch")
    previous = None
    for tag, expected_commit in STAGE_TAGS:
        actual = git("rev-list", "-n", "1", tag)
        require(actual == expected_commit, f"{tag} moved from its frozen commit")
        if previous is not None:
            result = subprocess.run(
                ("git", "merge-base", "--is-ancestor", previous, actual),
                cwd=str(ROOT),
                check=False,
            )
            require(result.returncode == 0, f"freeze ancestry broke before {tag}")
        previous = actual
    require(
        git("rev-list", "-n", "1", "afp-p11.8g-freeze") == EXPECTED_G_FREEZE,
        "P11.8G freeze target changed",
    )
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", EXPECTED_G_FREEZE, "HEAD"),
        cwd=str(ROOT),
        check=False,
    )
    require(result.returncode == 0, "P11.8H no longer descends from the G freeze")


def test_frozen_production_surface_is_unchanged() -> None:
    actual_files = tuple(
        "apexforge/semantic_lattice/" + path.name
        for path in sorted((PACKAGE_DIRECTORY / "semantic_lattice").glob("*.py"))
    )
    require(
        actual_files == SEMANTIC_LATTICE_PRODUCTION_FILES,
        "semantic-lattice production file set changed during final integration",
    )
    for path in SEMANTIC_LATTICE_PRODUCTION_FILES:
        current_blob = git("rev-parse", f"HEAD:{path}")
        frozen_blob = git("rev-parse", f"afp-p11.8g-freeze:{path}")
        require(current_blob == frozen_blob, f"frozen production file changed: {path}")
    changed_from_g = {
        line
        for line in git(
            "diff",
            "--name-only",
            "afp-p11.8g-freeze..HEAD",
        ).splitlines()
        if line
    }
    require(
        changed_from_g <= ALLOWED_H_PATHS,
        "P11.8H committed changes escaped the audit-only boundary",
    )
    working_tracked = {
        line
        for line in git("diff", "--name-only").splitlines()
        if line
    }
    require(
        not working_tracked,
        "P11.8H has unstaged tracked production changes",
    )


def test_predecessor_artifact_inventory() -> None:
    actual_smokes = tuple(
        path.name
        for path in sorted(PACKAGE_DIRECTORY.glob("p11_8[a-g]*_smoke_test.py"))
    )
    require(
        actual_smokes == PREDECESSOR_SMOKES,
        "P11.8 A-G smoke inventory changed",
    )
    for name in PREDECESSOR_DOCUMENTS:
        require((ROOT / "docs" / "p11" / name).is_file(), f"missing P11.8 document: {name}")


def test_public_surface_exactness() -> None:
    sys.path.insert(0, str(PACKAGE_DIRECTORY))
    try:
        import semantic_lattice
    finally:
        sys.path.pop(0)
    require(
        tuple(semantic_lattice.__all__) == EXPECTED_PUBLIC_SURFACE,
        "semantic-lattice package public surface changed",
    )
    require(
        "REPORT_HEADING" not in semantic_lattice.__all__
        and "REPORT_END" not in semantic_lattice.__all__
        and "AUTHORING_REPORT_HEADING" not in semantic_lattice.__all__
        and "AUTHORING_REPORT_END" not in semantic_lattice.__all__,
        "report constants leaked into package-level API",
    )


def test_p11_8_a_g_regression() -> None:
    for name in PREDECESSOR_SMOKES:
        run_smoke(PACKAGE_DIRECTORY / name)


def test_p11_7_compatibility_regression() -> None:
    smokes = tuple(sorted(PACKAGE_DIRECTORY.glob("p11_7*_smoke_test.py")))
    require(len(smokes) == 21, "frozen P11.7 compatibility smoke count changed")
    for path in smokes:
        run_smoke(path)


def test_final_integration_is_observational() -> None:
    reporting = (PACKAGE_DIRECTORY / "semantic_lattice" / "reporting.py").read_text(
        encoding="utf-8"
    )
    validation = (PACKAGE_DIRECTORY / "semantic_lattice" / "validation.py").read_text(
        encoding="utf-8"
    )
    require(
        "validate_semantic_lattice_snapshot(" not in reporting,
        "reporting gained direct revalidation",
    )
    require(
        "construct_semantic_lattice_snapshot(" not in reporting,
        "reporting gained reconstruction behavior",
    )
    require(
        "adapt_codex_semantic_lattice_proposal(" not in reporting
        and "adapt_semantic_lattice_authoring_proposal(" not in reporting,
        "reporting gained authoring adaptation",
    )
    require(
        "SemanticLatticeValidationReceipt" in validation
        and "validate_codex_semantic_lattice_proposal" in validation,
        "frozen validation boundary disappeared",
    )


def main() -> None:
    before = repository_status()
    test_stage_freeze_chain_and_branch()
    test_frozen_production_surface_is_unchanged()
    test_predecessor_artifact_inventory()
    test_public_surface_exactness()
    test_p11_8_a_g_regression()
    test_p11_7_compatibility_regression()
    test_final_integration_is_observational()
    after = repository_status()
    require(before == after, "P11.8H integration audit mutated repository status")

    print("AFP-P11.8H final semantic-lattice integration regression audit passed.")
    print("P11.8 A-G annotated freeze chain and exact G ancestry: PASS")
    print("Frozen eight-file semantic-lattice production surface unchanged: PASS")
    print("Seven predecessor smoke and document families preserved: PASS")
    print("Exact package public surface and reporting containment: PASS")
    print("P11.8 A-G full regression suite: PASS")
    print("Frozen P11.7 twenty-one-smoke compatibility suite: PASS")
    print("Audit-only observational boundary with no new semantic behavior: PASS")
    print("Repository no-op final integration boundary: PASS")


if __name__ == "__main__":
    main()
