"""AFP-P11.9I final AETHER-AIR 2.0 integration regression and freeze audit."""

from __future__ import annotations

import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = ROOT / "apexforge"
EXPECTED_BRANCH = "p11.9i-final-integration-regression-freeze"

STAGE_TAGS = (
    ("afp-p11.9a-freeze", "3e4ca23"),
    ("afp-p11.9b-freeze", "681d156"),
    ("afp-p11.9c-freeze", "72b26e8"),
    ("afp-p11.9d-freeze", "cc37ad9"),
    ("afp-p11.9e-freeze", "c025491"),
    ("afp-p11.9f-freeze", "c8095a5"),
    ("afp-p11.9g-freeze", "39bc07f"),
    ("afp-p11.9h-freeze", "f613403"),
)

AETHER_PRODUCTION_FILES = (
    "apexforge/aether_air/__init__.py",
    "apexforge/aether_air/construction.py",
    "apexforge/aether_air/model.py",
    "apexforge/aether_air/projection.py",
    "apexforge/aether_air/records.py",
    "apexforge/aether_air/reporting.py",
    "apexforge/aether_air/transformation.py",
    "apexforge/aether_air/validation.py",
)

PREDECESSOR_SMOKES = (
    "p11_9a_aether_air_2_interstitial_behavior_architecture_audit_smoke_test.py",
    "p11_9b_minimal_immutable_aether_air_interstitial_model_smoke_test.py",
    "p11_9c_canonical_predecessor_references_identity_evidence_provenance_smoke_test.py",
    "p11_9d_deterministic_interstitial_construction_smoke_test.py",
    "p11_9e_non_executing_transformation_normalization_smoke_test.py",
    "p11_9f_validation_collision_closure_extension_smoke_test.py",
    "p11_9g_explicit_downstream_projection_boundary_smoke_test.py",
    "p11_9h_aether_air_reporting_tooling_traceability_smoke_test.py",
)

CURRENT_BRANCH_SMOKES = PREDECESSOR_SMOKES[1:]

PREDECESSOR_DOCUMENTS = (
    "P11_9A_AETHER_AIR_2_INTERSTITIAL_BEHAVIOR_ARCHITECTURE_AUDIT.md",
    "P11_9B_MINIMAL_IMMUTABLE_AETHER_AIR_INTERSTITIAL_MODEL_AND_BEHAVIOR_KIND_TAXONOMY.md",
    "P11_9C_CANONICAL_PREDECESSOR_REFERENCES_IDENTITY_PRESERVATION_EVIDENCE_AND_PROVENANCE.md",
    "P11_9D_DETERMINISTIC_INTERSTITIAL_CONSTRUCTION_FROM_EXPLICIT_VALIDATED_PREDECESSOR_INPUTS.md",
    "P11_9E_NON_EXECUTING_TRANSFORMATION_AND_NORMALIZATION_CONTRACTS.md",
    "P11_9F_VALIDATION_COLLISION_CLOSURE_AND_EXTENSION_CONTRACTS.md",
    "P11_9G_EXPLICIT_DOWNSTREAM_PROJECTION_BOUNDARY.md",
    "P11_9H_AETHER_AIR_REPORTING_TOOLING_COMPATIBILITY_AND_TRACEABILITY.md",
)

EXPECTED_PUBLIC_SURFACE = (
    "AetherBehaviorKind",
    "AetherIntentParameter",
    "AetherBehaviorIntent",
    "AetherAirRepresentation",
    "CORE_AETHER_BEHAVIOR_KINDS",
    "AetherPredecessorReference",
    "AetherEvidence",
    "AetherIntentTrace",
    "AetherAirSnapshot",
    "construct_aether_air_snapshot",
    "AetherAirTransformation",
    "transform_aether_air_snapshot",
    "normalize_aether_air_snapshot",
    "AetherAirValidationReceipt",
    "AetherAirTransformationValidationReceipt",
    "validate_aether_air_snapshot",
    "validate_aether_air_transformation",
    "AetherAirDownstreamProjection",
    "project_validated_aether_air",
    "render_aether_air_downstream_projection_report",
)

EXPECTED_FIELDS = {
    "AetherBehaviorKind": ("canonical_id",),
    "AetherIntentParameter": ("key", "value"),
    "AetherBehaviorIntent": ("kind_id", "intent", "parameters"),
    "AetherAirRepresentation": ("behaviors",),
    "AetherPredecessorReference": ("source_domain", "source_kind", "source_identity"),
    "AetherEvidence": ("kind", "facts", "provenance"),
    "AetherIntentTrace": ("predecessor", "intent", "evidence"),
    "AetherAirSnapshot": ("representation", "traces"),
    "AetherAirTransformation": ("operation", "source", "result", "provenance"),
    "AetherAirValidationReceipt": ("snapshot", "extension_kind_ids", "provenance", "checks"),
    "AetherAirTransformationValidationReceipt": ("transformation", "source_receipt", "result_receipt", "checks"),
    "AetherAirDownstreamProjection": ("validation", "consumer", "provenance"),
}

ALLOWED_I_PATHS = {
    "apexforge/p11_9i_final_aether_air_2_integration_regression_freeze_smoke_test.py",
    "docs/p11/P11_9I_FINAL_AETHER_AIR_2_INTEGRATION_REGRESSION_AND_FREEZE.md",
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


def run_smoke(path: Path, *, root: Path = ROOT) -> None:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(root / "apexforge")
    completed = subprocess.run(
        (sys.executable, "-B", str(path)),
        cwd=str(root),
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


def run_isolated_branch_smoke(
    *,
    branch: str,
    freeze_tag: str,
    smoke_name: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="apexforge-p11-9i-") as directory:
        clone_root = Path(directory) / "repo"
        clone = subprocess.run(
            (
                "git",
                "clone",
                "--quiet",
                "--shared",
                "--no-checkout",
                str(ROOT),
                str(clone_root),
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        require(
            clone.returncode == 0,
            "isolated predecessor clone failed:\n" + clone.stderr.strip(),
        )
        checkout = subprocess.run(
            (
                "git",
                "-C",
                str(clone_root),
                "checkout",
                "--quiet",
                "-b",
                branch,
                freeze_tag,
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        require(
            checkout.returncode == 0,
            f"isolated checkout failed for {branch}:\n" + checkout.stderr.strip(),
        )
        run_smoke(clone_root / "apexforge" / smoke_name, root=clone_root)


def test_stage_freeze_chain_and_branch() -> None:
    require(
        git("branch", "--show-current") == EXPECTED_BRANCH,
        "unexpected P11.9I branch",
    )
    previous = None
    for tag, expected_short in STAGE_TAGS:
        actual = git("rev-list", "-n", "1", tag)
        require(
            actual.startswith(expected_short),
            f"{tag} moved from its reviewed frozen commit",
        )
        if previous is not None:
            ancestry = subprocess.run(
                ("git", "merge-base", "--is-ancestor", previous, actual),
                cwd=str(ROOT),
                check=False,
            )
            require(
                ancestry.returncode == 0,
                f"P11.9 freeze ancestry broke before {tag}",
            )
        previous = actual
    h_commit = git("rev-list", "-n", "1", "afp-p11.9h-freeze")
    ancestry = subprocess.run(
        ("git", "merge-base", "--is-ancestor", h_commit, "HEAD"),
        cwd=str(ROOT),
        check=False,
    )
    require(
        ancestry.returncode == 0,
        "P11.9I no longer descends from the H freeze",
    )


def test_frozen_production_surface_is_unchanged() -> None:
    actual_files = tuple(
        "apexforge/aether_air/" + path.name
        for path in sorted((PACKAGE_DIRECTORY / "aether_air").glob("*.py"))
    )
    require(
        actual_files == AETHER_PRODUCTION_FILES,
        "AETHER-AIR production file set changed during final integration",
    )
    for path in AETHER_PRODUCTION_FILES:
        current_blob = git("rev-parse", f"HEAD:{path}")
        frozen_blob = git("rev-parse", f"afp-p11.9h-freeze:{path}")
        require(
            current_blob == frozen_blob,
            f"frozen AETHER-AIR production file changed: {path}",
        )
    changed_from_h = {
        line
        for line in git(
            "diff",
            "--name-only",
            "afp-p11.9h-freeze..HEAD",
        ).splitlines()
        if line
    }
    require(
        changed_from_h <= ALLOWED_I_PATHS,
        "P11.9I committed changes escaped the audit-only boundary",
    )
    tracked_working = {
        line
        for line in git("diff", "--name-only").splitlines()
        if line
    }
    require(
        not tracked_working,
        "P11.9I has unstaged tracked changes",
    )


def test_predecessor_artifact_inventory() -> None:
    actual_smokes = tuple(
        path.name
        for path in sorted(PACKAGE_DIRECTORY.glob("p11_9[a-h]*_smoke_test.py"))
    )
    require(
        actual_smokes == PREDECESSOR_SMOKES,
        "P11.9 A-H smoke inventory changed",
    )
    for name in PREDECESSOR_DOCUMENTS:
        require(
            (ROOT / "docs" / "p11" / name).is_file(),
            f"missing P11.9 predecessor document: {name}",
        )


def test_public_surface_exactness() -> None:
    sys.path.insert(0, str(PACKAGE_DIRECTORY))
    try:
        import dataclasses
        import aether_air
    finally:
        sys.path.pop(0)
    require(
        tuple(aether_air.__all__) == EXPECTED_PUBLIC_SURFACE,
        "AETHER-AIR package public surface changed",
    )
    for name, expected in EXPECTED_FIELDS.items():
        value = getattr(aether_air, name)
        require(
            tuple(field.name for field in dataclasses.fields(value)) == expected,
            f"frozen dataclass field shape changed: {name}",
        )
    require(
        tuple(
            kind.canonical_id
            for kind in aether_air.CORE_AETHER_BEHAVIOR_KINDS
        )
        == (
            "behavior.intent",
            "transformation.intent",
            "constraint.intent",
            "projection.intent",
        ),
        "canonical four-kind AETHER-AIR taxonomy changed",
    )
    require(
        "REPORT_HEADING" not in aether_air.__all__
        and "REPORT_END" not in aether_air.__all__,
        "report constants leaked into AETHER-AIR package API",
    )


def test_integrated_b_through_h_lineage() -> None:
    sys.path.insert(0, str(PACKAGE_DIRECTORY))
    try:
        from aether_air import (
            AetherAirRepresentation,
            AetherBehaviorIntent,
            AetherEvidence,
            AetherIntentParameter,
            AetherIntentTrace,
            AetherPredecessorReference,
            normalize_aether_air_snapshot,
            construct_aether_air_snapshot,
            project_validated_aether_air,
            render_aether_air_downstream_projection_report,
            validate_aether_air_transformation,
        )
    finally:
        sys.path.pop(0)

    parameter = AetherIntentParameter("mode", "stable")
    intent = AetherBehaviorIntent(
        "behavior.intent",
        "preserve continuity",
        (parameter,),
    )
    representation = AetherAirRepresentation((intent,))
    predecessor = AetherPredecessorReference(
        "narrative",
        "character",
        ("story.apex", "Traveler"),
    )
    evidence = AetherEvidence(
        "trace",
        (("claim", "continuity"),),
        ("source:story.apex",),
    )
    trace = AetherIntentTrace(predecessor, intent, (evidence,))
    snapshot = construct_aether_air_snapshot(
        representation,
        traces=(trace,),
    )
    transformation = normalize_aether_air_snapshot(
        snapshot,
        representation=representation,
        traces=(trace,),
        provenance=("normalization:integration",),
    )
    receipt = validate_aether_air_transformation(transformation)
    projection = project_validated_aether_air(
        receipt,
        consumer="optimized-air",
        provenance=("projection:integration",),
    )
    report = render_aether_air_downstream_projection_report(projection)

    require(snapshot.representation is representation, "D replaced B representation identity")
    require(snapshot.traces[0] is trace, "D replaced C trace identity")
    require(trace.predecessor is predecessor, "C predecessor identity was replaced")
    require(trace.intent is intent, "C intent identity was replaced")
    require(trace.evidence[0] is evidence, "C evidence identity was replaced")
    require(transformation.source is snapshot, "E replaced D source snapshot")
    require(
        transformation.result.representation is representation
        and transformation.result.traces[0] is trace,
        "E replaced explicit canonical target objects",
    )
    require(receipt.transformation is transformation, "F replaced E transformation")
    require(receipt.source_receipt.snapshot is snapshot, "F replaced source snapshot")
    require(
        receipt.result_receipt.snapshot is transformation.result,
        "F replaced result snapshot",
    )
    require(projection.validation is receipt, "G replaced F validation receipt")
    require(
        "CONSUMER\noptimized-air" in report
        and "VALIDATION\ntransformation" in report
        and "operation=normalization" in report
        and 'predecessor=narrative:character:["story.apex","Traveler"]' in report
        and "intent_index=1" in report
        and "END AETHER-AIR DOWNSTREAM PROJECTION REPORT" in report,
        "H failed to expose deterministic integrated AETHER-AIR lineage",
    )


def test_p11_9a_isolated_regression() -> None:
    run_isolated_branch_smoke(
        branch="p11.9a-aether-air-2-interstitial-architecture-audit",
        freeze_tag="afp-p11.9a-freeze",
        smoke_name=PREDECESSOR_SMOKES[0],
    )


def test_p11_9_b_through_h_regression() -> None:
    for name in CURRENT_BRANCH_SMOKES:
        run_smoke(PACKAGE_DIRECTORY / name)


def test_frozen_p11_8h_compatibility() -> None:
    run_isolated_branch_smoke(
        branch="p11.8h-final-integration-regression-freeze",
        freeze_tag="afp-p11.8h-freeze",
        smoke_name="p11_8h_final_semantic_lattice_integration_regression_freeze_smoke_test.py",
    )


def test_non_operational_production_boundary() -> None:
    forbidden_roots = {
        "air",
        "authority",
        "effects",
        "runtime",
        "tooling",
        "tools",
        "language_server",
        "semantic_lattice",
        "importlib",
        "subprocess",
    }
    for relative in AETHER_PRODUCTION_FILES:
        source = (ROOT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", 1)[0])
        require(
            not (roots & forbidden_roots),
            f"operational/predecessor import leaked into {relative}: "
            + repr(sorted(roots & forbidden_roots)),
        )

    reporting = (PACKAGE_DIRECTORY / "aether_air" / "reporting.py").read_text(
        encoding="utf-8"
    )
    projection = (PACKAGE_DIRECTORY / "aether_air" / "projection.py").read_text(
        encoding="utf-8"
    )
    require(
        "validate_aether_air_snapshot(" not in reporting
        and "validate_aether_air_transformation(" not in reporting
        and "construct_aether_air_snapshot(" not in reporting
        and "project_validated_aether_air(" not in reporting,
        "H reporting gained validation, construction, or reprojection behavior",
    )
    require(
        "compile(" not in projection
        and "exec(" not in projection
        and "eval(" not in projection,
        "G projection gained executable behavior",
    )


def main() -> None:
    before = repository_status()
    test_stage_freeze_chain_and_branch()
    test_frozen_production_surface_is_unchanged()
    test_predecessor_artifact_inventory()
    test_public_surface_exactness()
    test_integrated_b_through_h_lineage()
    test_p11_9a_isolated_regression()
    test_p11_9_b_through_h_regression()
    test_frozen_p11_8h_compatibility()
    test_non_operational_production_boundary()
    after = repository_status()
    require(before == after, "P11.9I integration audit mutated repository status")

    print("AFP-P11.9I final AETHER-AIR 2.0 integration regression audit passed.")
    print("P11.9 A-H annotated freeze chain and exact H ancestry: PASS")
    print("Frozen eight-file AETHER-AIR production surface unchanged: PASS")
    print("Eight predecessor smoke and document families preserved: PASS")
    print("Exact package public surface, record shapes, and four-kind taxonomy: PASS")
    print("Integrated B->C->D->E->F->G->H identity and traceability lineage: PASS")
    print("P11.9A canonical isolated architecture regression: PASS")
    print("P11.9B-H full regression suite: PASS")
    print("Frozen P11.8H predecessor compatibility regression: PASS")
    print("Non-operational runtime/tooling/backend/P11.10 ownership boundary: PASS")
    print("Repository no-op final integration boundary: PASS")


if __name__ == "__main__":
    main()
