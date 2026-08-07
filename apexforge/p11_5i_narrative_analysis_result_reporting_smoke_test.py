"""Executable P11.5I-B narrative analysis result reporting contract."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from language.narrative_analysis import analyze_narrative_source
from tools.narrative_report import render_narrative_analysis_report


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5h-freeze"
EXPECTED_HEAD = "f9af32adb5cf56a5d78f6bcd59ed4ecc70c933c1"
EXPECTED_BRANCH = "p11.5i-narrative-analysis-result-reporting"

AUDIT_PATHS = {
    "apexforge/p11_5i_narrative_analysis_result_reporting_architecture_audit_smoke_test.py",
    "docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/tools/narrative_report.py",
    "apexforge/p11_5i_narrative_analysis_result_reporting_smoke_test.py",
    "docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS

EMPTY_SOURCE = "story Empty {}"

RICH_SOURCE = "\n".join(
    (
        "story ReportStory {",
        "    character Ada",
        "    character Ada",
        "    scene Arrival",
        "    dialogue Warning {",
        "        scene Arrival",
        "        speaker Ada",
        "        participants [MissingWitness, MissingWitness]",
        "    }",
        "    narrative_state Facts {",
        "        fact Ada.ready = true",
        "        fact Ada.ready = false",
        "    }",
        "    continuity Memory {",
        '        require Ada: "Ada remembers."',
        "    }",
        "}",
    )
)

EXPECTED_EMPTY_REPORT = "\n".join(
    (
        "ApexForge Narrative Analysis Report",
        "",
        "SOURCE SUMMARY",
        "  source: empty.apex",
        "  story: Empty",
        "  start: empty.apex:1:1",
        "  characters: 0",
        "  scenes: 0",
        "  dialogues: 0",
        "  choices: 0",
        "  perspectives: 0",
        "  timelines: 0",
        "  narrative-states: 0",
        "  continuities: 0",
        "",
        "SEMANTIC SUMMARY",
        "  story: story:Empty",
        "  characters (0): (none)",
        "  scenes (0): (none)",
        "  dialogues (0): (none)",
        "  choices (0): (none)",
        "  perspectives (0): (none)",
        "  timelines (0): (none)",
        "  narrative-states (0): (none)",
        "  continuities (0): (none)",
        "",
        "GRAPH NODES",
        "  0: story:Empty [declared]",
        "",
        "GRAPH EDGES",
        "  (none)",
        "",
        "VALIDATION FINDINGS",
        "  (none)",
    )
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


def require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def test_frozen_baseline_and_exact_reviewed_ownership() -> None:
    require(
        git("branch", "--show-current").strip() == EXPECTED_BRANCH,
        "P11.5I-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5I-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5H controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5H controlling freeze resolves incorrectly",
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
        "reviewed P11.5I candidate path set changed",
    )


def test_public_api_exact_empty_report_and_type_boundary() -> None:
    import tools.narrative_report as report_module

    require(
        report_module.__all__
        == ("render_narrative_analysis_report",),
        "P11.5I-B public exports changed",
    )

    analysis = analyze_narrative_source(
        EMPTY_SOURCE,
        source_name="empty.apex",
    )
    report = render_narrative_analysis_report(analysis)

    require(
        type(report) is str,
        "narrative report is not an exact str",
    )
    require(
        report == EXPECTED_EMPTY_REPORT,
        "canonical empty narrative report changed",
    )
    require(
        not report.endswith("\n"),
        "narrative report gained a trailing newline",
    )
    require(
        all(line == line.rstrip() for line in report.splitlines()),
        "narrative report contains trailing whitespace",
    )

    require_raises(
        TypeError,
        lambda: render_narrative_analysis_report(object()),
        "narrative reporter accepted a non-analysis value",
    )


def test_rich_projection_order_duplicates_and_evidence() -> None:
    analysis = analyze_narrative_source(
        RICH_SOURCE,
        source_name="report.apex",
    )
    report = render_narrative_analysis_report(analysis)
    lines = report.splitlines()

    require(
        "  characters (2): character:Ada, character:Ada" in lines,
        "semantic duplicate declaration order changed",
    )

    graph_node_lines = [
        line
        for line in lines
        if line.startswith("  ")
        and ": " in line
        and (
            "[declared]" in line
            or "[referenced-only]" in line
        )
    ]
    expected_node_lines = [
        f"  {index}: {node.identity.kind}:"
        f"{'.'.join(node.identity.path)} "
        f"[{'declared' if node.declared else 'referenced-only'}]"
        for index, node in enumerate(analysis.semantic_graph.nodes)
    ]
    require(
        graph_node_lines == expected_node_lines,
        "graph node order or identity display changed",
    )

    edge_headers = [
        line
        for line in lines
        if line.startswith("  ")
        and " -> " in line
    ]
    expected_edge_headers = [
        f"  {index}: {edge.relation} "
        f"{edge.source.kind}:{'.'.join(edge.source.path)} -> "
        f"{edge.target.kind}:{'.'.join(edge.target.path)}"
        for index, edge in enumerate(analysis.semantic_graph.edges)
    ]
    require(
        edge_headers == expected_edge_headers,
        "graph edge order or identity display changed",
    )

    require(
        report.count("character:MissingWitness [referenced-only]") == 1,
        "referenced-only identity projection changed",
    )

    finding_headers = [
        line
        for line in lines
        if line.startswith("  ")
        and ": " in line
        and any(
            line.endswith(classification)
            for classification in (
                "duplicate_declaration",
                "referenced_only_identity",
                "conflicting_state_value",
                "temporal_cycle",
                "repeated_relation_evidence",
                "continuity_assertion_cluster",
                "perspective_cluster",
            )
        )
    ]
    expected_finding_headers = [
        f"  {index}: {finding.classification}"
        for index, finding in enumerate(
            analysis.validation_report.findings
        )
    ]
    require(
        finding_headers == expected_finding_headers,
        "validation finding order changed",
    )

    require(
        "    evidence: (none)" in lines
        or any(
            line.startswith("    evidence: ")
            and line != "    evidence: (none)"
            for line in lines
        ),
        "finding or edge evidence projection is missing",
    )
    require(
        "    node-indexes: (none)" in lines
        or any(
            line.startswith("    node-indexes: ")
            and line != "    node-indexes: (none)"
            for line in lines
        ),
        "finding node-index projection is missing",
    )
    require(
        "    edge-indexes: (none)" in lines
        or any(
            line.startswith("    edge-indexes: ")
            and line != "    edge-indexes: (none)"
            for line in lines
        ),
        "finding edge-index projection is missing",
    )


def test_determinism_and_no_mutation() -> None:
    analysis = analyze_narrative_source(
        RICH_SOURCE,
        source_name="report.apex",
    )
    preserved = analyze_narrative_source(
        RICH_SOURCE,
        source_name="report.apex",
    )

    first = render_narrative_analysis_report(analysis)
    second = render_narrative_analysis_report(analysis)

    require(first == second, "narrative report is nondeterministic")
    require(
        analysis == preserved,
        "narrative reporting mutated the analysis products",
    )


def test_pure_reporting_boundary_and_frozen_predecessor() -> None:
    module_path = PACKAGE_DIRECTORY / "tools" / "narrative_report.py"
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)

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
        public_classes == set(),
        "unexpected public narrative reporting class exposed",
    )
    require(
        public_functions == {"render_narrative_analysis_report"},
        "unexpected public narrative reporting function exposed",
    )

    forbidden = (
        "analyze_narrative_source",
        "parse_narrative_source",
        "lower_narrative_source",
        "build_narrative_semantic_graph",
        "validate_narrative_semantic_graph",
        "BuildDiagnostic",
        "DiagnosticError",
        "json",
        "open(",
        "write_text",
        "write_bytes",
        "language.compiler",
        "language.project",
        "runtime.",
        "tooling.cli",
        "air.",
        "artifact",
    )
    require(
        all(marker not in text for marker in forbidden),
        "reporter escaped its pure observational boundary",
    )

    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_lowering.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/narrative_analysis.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
        "apexforge/tools/runtime_report.py",
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
    test_frozen_baseline_and_exact_reviewed_ownership()
    test_public_api_exact_empty_report_and_type_boundary()
    test_rich_projection_order_duplicates_and_evidence()
    test_determinism_and_no_mutation()
    test_pure_reporting_boundary_and_frozen_predecessor()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5I-B smoke test mutated repository status")

    print("AFP-P11.5I-B narrative analysis result reporting smoke test passed.")
    print("P11.5H annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Dedicated pure reporting API and exact input/output types: PASS")
    print("Exact canonical report and empty markers: PASS")
    print("Source and semantic summaries with duplicate preservation: PASS")
    print("Graph node, edge, and ordered evidence projection: PASS")
    print("Validation finding, index, identity, and evidence projection: PASS")
    print("Deterministic rendering with no mutation or re-analysis: PASS")
    print("No serialization, diagnostic conversion, CLI, compiler, project, runtime, AIR, artifact, or editor integration: PASS")
    print("Frozen P11.5H and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
