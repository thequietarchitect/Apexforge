"""P11.8G semantic lattice reporting and tooling compatibility smoke test."""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess

from semantic_lattice import (
    CORE_SEMANTIC_LATTICE_AXES,
    ParametricSemanticLattice,
    SemanticLatticeAuthoringProposal,
    SemanticLatticeAuthoringSource,
    SemanticLatticeAxis,
    SemanticLatticeEvidence,
    SemanticLatticeParameter,
    SemanticLatticeRelationship,
    SemanticLatticeSubjectReference,
    construct_semantic_lattice_snapshot,
    render_semantic_lattice_authoring_validation_report,
    render_semantic_lattice_validation_report,
    validate_codex_semantic_lattice_proposal,
    validate_semantic_lattice_snapshot,
)


PACKAGE_DIRECTORY = Path(__file__).resolve().parent
ROOT = PACKAGE_DIRECTORY.parent
REPORTING_PATH = PACKAGE_DIRECTORY / "semantic_lattice" / "reporting.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(expected_type, operation, message: str) -> None:
    try:
        operation()
    except expected_type:
        return
    except Exception as error:
        raise AssertionError(
            f"{message}: expected {expected_type.__name__}, received {type(error).__name__}"
        ) from error
    raise AssertionError(message)


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git",) + arguments,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def base_snapshot_receipt():
    lattice = ParametricSemanticLattice()
    snapshot = construct_semantic_lattice_snapshot(lattice)
    return validate_semantic_lattice_snapshot(snapshot)


def rich_snapshot_receipt():
    extension = SemanticLatticeAxis("reporting.presentation")
    lattice = ParametricSemanticLattice(
        axes=CORE_SEMANTIC_LATTICE_AXES + (extension,),
        parameters=(
            SemanticLatticeParameter("continuity", "mode", "preserve"),
            SemanticLatticeParameter(
                "reporting.presentation",
                "palette",
                ("secondary", "advisory"),
            ),
        ),
    )
    source = SemanticLatticeSubjectReference(
        source_domain="narrative",
        source_kind="character",
        source_identity=("story.apex", "Guide"),
    )
    target = SemanticLatticeSubjectReference(
        source_domain="air",
        source_kind="directive",
        source_identity=("directive:Main",),
    )
    evidence = SemanticLatticeEvidence(
        kind="trace",
        facts=(("claim", "advisory"), ("weight", 3)),
        provenance=("codex:proposal", "source:story.apex"),
    )
    relationship = SemanticLatticeRelationship(
        source=source,
        relation="references",
        target=target,
        evidence=(evidence,),
    )
    snapshot = construct_semantic_lattice_snapshot(
        lattice,
        subjects=(source, target),
        relationships=(relationship,),
    )
    return validate_semantic_lattice_snapshot(snapshot)


def test_exact_empty_projection() -> None:
    receipt = base_snapshot_receipt()
    report = render_semantic_lattice_validation_report(receipt)
    expected_lines = [
        "APEXFORGE SEMANTIC LATTICE REPORT",
        "AXES",
    ]
    expected_lines.extend(
        f"{index}. {axis.canonical_id}"
        for index, axis in enumerate(CORE_SEMANTIC_LATTICE_AXES, 1)
    )
    expected_lines.extend(
        (
            "PARAMETERS",
            "<none>",
            "SUBJECTS",
            "<none>",
            "RELATIONSHIPS",
            "<none>",
            "EXTENSION AXES",
            "<none>",
            "PROVENANCE",
            "<none>",
            "CHECKS",
        )
    )
    expected_lines.extend(
        f"{index}. {value}" for index, value in enumerate(receipt.checks, 1)
    )
    expected_lines.append("END SEMANTIC LATTICE REPORT")
    expected = "\n".join(expected_lines)
    require(report == expected, "canonical empty semantic lattice report changed")
    require(type(report) is str, "semantic lattice report is not an exact str")
    require(not report.endswith("\n"), "semantic lattice report gained a trailing newline")
    require(
        all(line == line.rstrip() for line in report.splitlines()),
        "semantic lattice report contains trailing whitespace",
    )


def test_rich_ordered_projection() -> None:
    receipt = rich_snapshot_receipt()
    before = (
        receipt.snapshot.lattice.axes,
        receipt.snapshot.lattice.parameters,
        receipt.snapshot.subjects,
        receipt.snapshot.relationships,
        receipt.extension_axis_ids,
        receipt.provenance,
        receipt.checks,
    )
    first = render_semantic_lattice_validation_report(receipt)
    second = render_semantic_lattice_validation_report(receipt)
    after = (
        receipt.snapshot.lattice.axes,
        receipt.snapshot.lattice.parameters,
        receipt.snapshot.subjects,
        receipt.snapshot.relationships,
        receipt.extension_axis_ids,
        receipt.provenance,
        receipt.checks,
    )
    require(first == second, "semantic lattice report is nondeterministic")
    require(before == after, "semantic lattice reporting mutated validated products")
    require(
        "1. axis=continuity; key=mode; value=\"preserve\"" in first,
        "parameter encounter order/value projection changed",
    )
    require(
        "2. axis=reporting.presentation; key=palette; value=[\"secondary\",\"advisory\"]"
        in first,
        "extension parameter projection changed",
    )
    require(
        '1. narrative:character:["story.apex","Guide"]' in first
        and '2. air:directive:["directive:Main"]' in first,
        "subject identity projection changed",
    )
    require(
        "relation=references" in first
        and "kind=trace" in first
        and "codex:proposal" in first,
        "relationship evidence/provenance projection changed",
    )
    require(
        "EXTENSION AXES\n1. reporting.presentation" in first,
        "extension-axis receipt projection changed",
    )
    provenance_lines = first.split("PROVENANCE\n", 1)[1].split("\nCHECKS", 1)[0]
    require(
        provenance_lines.splitlines()
        == ["1. codex:proposal", "2. source:story.apex"],
        "provenance encounter order changed",
    )


def test_exact_type_boundaries() -> None:
    require_raises(
        TypeError,
        lambda: render_semantic_lattice_validation_report(object()),
        "snapshot reporter accepted a non-receipt value",
    )
    require_raises(
        TypeError,
        lambda: render_semantic_lattice_authoring_validation_report(object()),
        "authoring reporter accepted a non-receipt value",
    )


def test_codex_authoring_visibility_without_privilege() -> None:
    proposal = SemanticLatticeAuthoringProposal(
        source=SemanticLatticeAuthoringSource.ADVISORY,
        author_identity="codex-agent",
        provider_identity="codex",
        lattice=ParametricSemanticLattice(),
    )
    receipt = validate_codex_semantic_lattice_proposal(proposal)
    before = (receipt.proposal, receipt.snapshot_receipt)
    first = render_semantic_lattice_authoring_validation_report(receipt)
    second = render_semantic_lattice_authoring_validation_report(receipt)
    after = (receipt.proposal, receipt.snapshot_receipt)
    require(first == second, "authoring report is nondeterministic")
    require(before == after, "authoring reporting mutated proposal or validation receipt")
    require(
        first.startswith(
            "APEXFORGE SEMANTIC LATTICE AUTHORING REPORT\n"
            "source=advisory\n"
            "author_identity=codex-agent\n"
            "provider_identity=codex\n"
            "APEXFORGE SEMANTIC LATTICE REPORT\n"
        ),
        "Codex advisory provenance is not visibly projected",
    )
    require(
        first.endswith("END SEMANTIC LATTICE AUTHORING REPORT"),
        "authoring report end marker changed",
    )


def test_pure_observational_reporting_surface() -> None:
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
    require(not public_classes, "reporting introduced a public mutable/report model class")
    require(
        public_functions
        == {
            "render_semantic_lattice_authoring_validation_report",
            "render_semantic_lattice_validation_report",
        },
        "semantic lattice reporting public function surface changed",
    )
    forbidden_calls = {
        "validate_semantic_lattice_snapshot",
        "validate_semantic_lattice_authoring_proposal",
        "validate_codex_semantic_lattice_proposal",
        "construct_semantic_lattice_snapshot",
        "adapt_semantic_lattice_authoring_proposal",
        "adapt_codex_semantic_lattice_proposal",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(
        not (called_names & forbidden_calls),
        "reporting revalidates, reconstructs, or adapts semantic lattice state",
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
            }
        ),
        "semantic lattice reporting imported an operational/tooling domain",
    )


def test_existing_tooling_surfaces_untouched() -> None:
    changed = git(
        "diff",
        "--name-only",
        "HEAD",
        "--",
        "apexforge/apexforge_cli.py",
        "apexforge/runtime",
        "apexforge/tooling",
        "apexforge/tools",
        "apexforge/language_server",
        "apexforge/language/diagnostics.py",
    )
    require(changed == "", "P11.8G modified a frozen existing tooling/reporting surface")


def test_package_export_boundary() -> None:
    import semantic_lattice

    exported = set(semantic_lattice.__all__)
    require(
        "render_semantic_lattice_validation_report" in exported
        and "render_semantic_lattice_authoring_validation_report" in exported,
        "semantic lattice reporting functions are not package exports",
    )
    require(
        "REPORT_HEADING" not in exported
        and "REPORT_END" not in exported
        and "AUTHORING_REPORT_HEADING" not in exported
        and "AUTHORING_REPORT_END" not in exported,
        "report constants leaked into package-level public API",
    )


def main() -> None:
    before = git("status", "--porcelain=v1")
    test_exact_empty_projection()
    test_rich_ordered_projection()
    test_exact_type_boundaries()
    test_codex_authoring_visibility_without_privilege()
    test_pure_observational_reporting_surface()
    test_existing_tooling_surfaces_untouched()
    test_package_export_boundary()
    after = git("status", "--porcelain=v1")
    require(before == after, "P11.8G smoke test mutated repository status")
    print("AFP-P11.8G semantic lattice reporting/tooling compatibility smoke test passed.")
    print("Exact deterministic validated-lattice report and empty markers: PASS")
    print("Ordered axes, parameters, subjects, relationships, evidence, and provenance projection: PASS")
    print("Exact reporting receipt type boundaries: PASS")
    print("Codex advisory author/provider provenance visibility without privilege: PASS")
    print("No revalidation, reconstruction, adaptation, mutation, execution, or authority: PASS")
    print("Frozen CLI, runtime, tooling, editor, and existing reporter surfaces untouched: PASS")
    print("Package export boundary with report constants contained: PASS")
    print("Repository no-op reporting compatibility boundary: PASS")


if __name__ == "__main__":
    main()
