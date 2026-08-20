"""P11.9H AETHER-AIR reporting, tooling compatibility, and traceability smoke test."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
REPORTING_PATH = ROOT / "apexforge" / "aether_air" / "reporting.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(exc_type, operation, message):
    try:
        operation()
    except exc_type:
        return
    raise AssertionError(message)


def git(*arguments):
    completed = subprocess.run(
        ("git",) + arguments,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def main():
    from aether_air import (
        AetherAirRepresentation,
        AetherBehaviorIntent,
        AetherBehaviorKind,
        AetherEvidence,
        AetherIntentParameter,
        AetherIntentTrace,
        AetherPredecessorReference,
        construct_aether_air_snapshot,
        normalize_aether_air_snapshot,
        project_validated_aether_air,
        render_aether_air_downstream_projection_report,
        validate_aether_air_snapshot,
        validate_aether_air_transformation,
    )

    before_status = git("status", "--porcelain=v1")

    empty_snapshot = construct_aether_air_snapshot(AetherAirRepresentation())
    empty_receipt = validate_aether_air_snapshot(empty_snapshot)
    empty_projection = project_validated_aether_air(
        empty_receipt,
        consumer="optimized-air",
    )
    empty_report = render_aether_air_downstream_projection_report(empty_projection)
    expected_lines = [
        "APEXFORGE AETHER-AIR DOWNSTREAM PROJECTION REPORT",
        "CONSUMER",
        "optimized-air",
        "PROJECTION PROVENANCE",
        "<none>",
        "VALIDATION",
        "snapshot",
        "BEHAVIORS",
        "<none>",
        "TRACES",
        "<none>",
        "EXTENSION KINDS",
        "<none>",
        "VALIDATION PROVENANCE",
        "<none>",
        "CHECKS",
    ]
    expected_lines.extend(
        f"{index}. {value}"
        for index, value in enumerate(empty_receipt.checks, 1)
    )
    expected_lines.append("END AETHER-AIR DOWNSTREAM PROJECTION REPORT")
    expected = "\n".join(expected_lines)
    require(empty_report == expected, "canonical empty projection report changed")
    require(type(empty_report) is str, "projection report is not an exact str")
    require(not empty_report.endswith("\n"), "projection report gained trailing newline")
    require(
        all(line == line.rstrip() for line in empty_report.splitlines()),
        "projection report contains trailing whitespace",
    )
    require(
        render_aether_air_downstream_projection_report(empty_projection) == empty_report,
        "projection reporting is nondeterministic",
    )
    print("Exact deterministic empty downstream-projection report: PASS")

    core = AetherBehaviorIntent(
        "behavior.intent",
        "preserve continuity",
        (AetherIntentParameter("mode", "stable"),),
    )
    extension = AetherBehaviorIntent(
        "extension.audit",
        "record passive audit",
    )
    predecessor = AetherPredecessorReference(
        "narrative",
        "character",
        ("character", "Traveler"),
    )
    evidence = AetherEvidence(
        "observed",
        (("classification", "continuity"),),
        ("source:story",),
    )
    trace = AetherIntentTrace(predecessor, core, (evidence,))
    rich_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core, extension)),
        traces=(trace,),
    )
    rich_receipt = validate_aether_air_snapshot(
        rich_snapshot,
        extension_kinds=(AetherBehaviorKind("extension.audit"),),
    )
    rich_projection = project_validated_aether_air(
        rich_receipt,
        consumer="native-backend",
        provenance=("projection:caller", "projection:trace"),
    )
    rich_report = render_aether_air_downstream_projection_report(rich_projection)
    require(
        '1. kind=behavior.intent; intent="preserve continuity"; parameters=[["mode","stable"]]' in rich_report
        and '2. kind=extension.audit; intent="record passive audit"; parameters=[]' in rich_report,
        "behavior intent or parameter encounter-order projection changed",
    )
    require(
        '1. predecessor=narrative:character:["character","Traveler"]; intent_index=1' in rich_report
        and 'evidence 1. kind=observed; facts=[["classification","continuity"]]; provenance=["source:story"]' in rich_report,
        "trace predecessor/evidence traceability projection changed",
    )
    require(
        "PROJECTION PROVENANCE\n1. projection:caller\n2. projection:trace" in rich_report
        and "EXTENSION KINDS\n1. extension.audit" in rich_report
        and "VALIDATION PROVENANCE\n1. source:story" in rich_report,
        "projection/extension/validation provenance encounter order changed",
    )
    print("Ordered behavior, trace, evidence, extension, and provenance traceability: PASS")

    normalization = normalize_aether_air_snapshot(
        rich_snapshot,
        representation=rich_snapshot.representation,
        traces=rich_snapshot.traces,
        provenance=("normalization:test",),
    )
    transformation_receipt = validate_aether_air_transformation(
        normalization,
        extension_kinds=(AetherBehaviorKind("extension.audit"),),
    )
    transformation_projection = project_validated_aether_air(
        transformation_receipt,
        consumer="optimized-air",
        provenance=("projection:transformation",),
    )
    transformation_report = render_aether_air_downstream_projection_report(
        transformation_projection
    )
    require(
        "VALIDATION\ntransformation" in transformation_report
        and "TRANSFORMATION\noperation=normalization" in transformation_report
        and "TRANSFORMATION PROVENANCE\n1. normalization:test" in transformation_report
        and "SOURCE SNAPSHOT" in transformation_report
        and "RESULT SNAPSHOT" in transformation_report
        and "TRANSFORMATION CHECKS" in transformation_report,
        "transformation lineage traceability report changed",
    )
    require(
        transformation_projection.validation is transformation_receipt
        and transformation_receipt.transformation is normalization,
        "reporting replaced frozen transformation lineage",
    )
    print("Transformation source/result lineage and provenance visibility: PASS")

    raises(
        TypeError,
        lambda: render_aether_air_downstream_projection_report(object()),
        "reporter accepted an arbitrary non-projection object",
    )
    raises(
        TypeError,
        lambda: render_aether_air_downstream_projection_report(rich_receipt),
        "reporter accepted a standalone F validation receipt",
    )
    raises(
        TypeError,
        lambda: render_aether_air_downstream_projection_report(rich_snapshot),
        "reporter accepted a raw AETHER-AIR snapshot",
    )
    print("Exact frozen G-projection type boundary: PASS")

    source = REPORTING_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    require(not public_classes, "reporting introduced a public report model class")
    require(
        public_functions == {"render_aether_air_downstream_projection_report"},
        "P11.9H public reporting function surface expanded",
    )
    forbidden_calls = {
        "validate_aether_air_snapshot",
        "validate_aether_air_transformation",
        "construct_aether_air_snapshot",
        "transform_aether_air_snapshot",
        "normalize_aether_air_snapshot",
        "project_validated_aether_air",
        "compile",
        "exec",
        "eval",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(
        not (called_names & forbidden_calls),
        "reporting revalidated, reconstructed, reprojected, transformed, or executed state",
    )
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    require(
        not (
            imported_roots
            & {
                "runtime",
                "tooling",
                "tools",
                "language_server",
                "air",
                "authority",
                "effects",
                "semantic_lattice",
            }
        ),
        "AETHER-AIR reporting imported an operational/tooling/predecessor domain",
    )
    print("Pure observational reporting with no revalidation or reprojection: PASS")

    import aether_air
    require(
        "render_aether_air_downstream_projection_report" in aether_air.__all__,
        "AETHER-AIR projection reporter is not a package export",
    )
    require(
        "REPORT_HEADING" not in aether_air.__all__
        and "REPORT_END" not in aether_air.__all__,
        "report constants leaked into package-level public API",
    )
    print("Single package-level reporter with report constants contained: PASS")

    frozen_aether = git(
        "diff",
        "--name-only",
        "afp-p11.9g-freeze",
        "--",
        "apexforge/aether_air/model.py",
        "apexforge/aether_air/records.py",
        "apexforge/aether_air/construction.py",
        "apexforge/aether_air/transformation.py",
        "apexforge/aether_air/validation.py",
        "apexforge/aether_air/projection.py",
    )
    require(frozen_aether == "", "P11.9H modified frozen P11.9B-G production files")
    print("Frozen P11.9B/P11.9C/P11.9D/P11.9E/P11.9F/P11.9G surfaces preserved: PASS")

    frozen_tooling = git(
        "diff",
        "--name-only",
        "afp-p11.9g-freeze",
        "--",
        "apexforge/apexforge_cli.py",
        "apexforge/tooling",
        "apexforge/tools",
        "apexforge/language_server",
        "apexforge/semantic_lattice",
    )
    require(
        frozen_tooling == "",
        "P11.9H modified an existing CLI/editor/tooling/reporting surface",
    )
    print("Existing CLI, editor, tooling, and reporter surfaces remain untouched: PASS")

    require(
        all(
            name not in public_functions
            for name in (
                "lower",
                "optimize",
                "compile",
                "emit",
                "serialize",
                "execute",
                "select_backend",
                "choose_branch",
                "converge",
                "paradox_elevation",
            )
        ),
        "downstream or P11.10 authority leaked into reporting surface",
    )
    print("Downstream execution and P11.10 semantic boundaries preserved: PASS")

    after_status = git("status", "--porcelain=v1")
    require(before_status == after_status, "report rendering mutated repository status")
    print("Repository no-op reporting compatibility boundary: PASS")


if __name__ == "__main__":
    main()
