"""Executable P11.5H-B opt-in narrative analysis pipeline contract."""

from __future__ import annotations

import ast
import subprocess
from dataclasses import FrozenInstanceError
from pathlib import Path

import language.narrative_analysis as analysis_module
from language.narrative_analysis import (
    NarrativeSourceAnalysis,
    analyze_narrative_source,
)
from language.narrative_graph import (
    NarrativeSemanticGraph,
    build_narrative_semantic_graph,
)
from language.narrative_lowering import (
    NarrativeSemanticLoweringError,
    lower_narrative_source,
)
from language.narrative_model import NarrativeStory
from language.narrative_parser import (
    NarrativeSourceParseError,
    parse_narrative_source,
)
from language.narrative_source import NarrativeSourceDocument
from language.narrative_validation import (
    NarrativeValidationReport,
    validate_narrative_semantic_graph,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIRECTORY = REPOSITORY_ROOT / "apexforge"
BASELINE_TAG = "afp-p11.5g-freeze"
EXPECTED_HEAD = "6afe6a3a8e3842a27bbaba99aaef379485a31c5b"
EXPECTED_BRANCH = "p11.5h-opt-in-narrative-analysis-pipeline"

AUDIT_PATHS = {
    "apexforge/p11_5h_opt_in_narrative_analysis_pipeline_architecture_audit_smoke_test.py",
    "docs/p11/P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_ARCHITECTURE_AUDIT.md",
}
IMPLEMENTATION_PATHS = {
    "apexforge/language/narrative_analysis.py",
    "apexforge/p11_5h_opt_in_narrative_analysis_pipeline_smoke_test.py",
    "docs/p11/P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_CONTRACT.md",
}
REVIEWED_PATHS = AUDIT_PATHS | IMPLEMENTATION_PATHS

VALID_SOURCE = "\n".join(
    (
        "story PipelineStory {",
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

LOWERING_FAILURE_SOURCE = (
    'story PipelineStory { choice C { scene S path " bad " '
    '{ destination S } } }'
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
        "P11.5H-B is running on an unexpected branch",
    )
    require(
        git("rev-parse", "HEAD").strip() == EXPECTED_HEAD,
        "P11.5H-B predecessor HEAD changed",
    )
    require(
        git("cat-file", "-t", BASELINE_TAG).strip() == "tag",
        "P11.5G controlling freeze is not annotated",
    )
    require(
        git("rev-parse", f"{BASELINE_TAG}^{{}}").strip() == EXPECTED_HEAD,
        "P11.5G controlling freeze resolves incorrectly",
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
        "reviewed P11.5H candidate path set changed",
    )


def test_public_api_and_result_invariants() -> None:
    require(
        analysis_module.__all__
        == (
            "NarrativeSourceAnalysis",
            "analyze_narrative_source",
        ),
        "P11.5H-B public exports changed",
    )

    analysis = analyze_narrative_source(
        VALID_SOURCE,
        source_name="pipeline.apex",
    )
    require(
        type(analysis) is NarrativeSourceAnalysis,
        "pipeline did not return exact NarrativeSourceAnalysis",
    )
    require(
        type(analysis.source_document) is NarrativeSourceDocument,
        "pipeline source product type changed",
    )
    require(
        type(analysis.semantic_story) is NarrativeStory,
        "pipeline semantic product type changed",
    )
    require(
        type(analysis.semantic_graph) is NarrativeSemanticGraph,
        "pipeline graph product type changed",
    )
    require(
        type(analysis.validation_report) is NarrativeValidationReport,
        "pipeline validation product type changed",
    )

    require_raises(
        TypeError,
        lambda: NarrativeSourceAnalysis(
            object(),
            analysis.semantic_story,
            analysis.semantic_graph,
            analysis.validation_report,
        ),
        "analysis result accepted a non-source product",
    )

    other = analyze_narrative_source("story Other {}", source_name="other.apex")
    require_raises(
        ValueError,
        lambda: NarrativeSourceAnalysis(
            analysis.source_document,
            analysis.semantic_story,
            other.semantic_graph,
            analysis.validation_report,
        ),
        "analysis result accepted a mismatched graph identity",
    )

    require_raises(
        FrozenInstanceError,
        lambda: setattr(analysis, "semantic_story", other.semantic_story),
        "analysis result is not immutable",
    )


def test_exact_products_determinism_and_passive_findings() -> None:
    first = analyze_narrative_source(
        VALID_SOURCE,
        source_name="pipeline.apex",
    )
    second = analyze_narrative_source(
        VALID_SOURCE,
        source_name="pipeline.apex",
    )
    require(first == second, "pipeline result is nondeterministic")

    source_document = parse_narrative_source(
        VALID_SOURCE,
        source_name="pipeline.apex",
    )
    semantic_story = lower_narrative_source(source_document)
    semantic_graph = build_narrative_semantic_graph(semantic_story)
    validation_report = validate_narrative_semantic_graph(
        semantic_graph
    )

    require(
        first.source_document == source_document,
        "pipeline replaced or reinterpreted the parser product",
    )
    require(
        first.semantic_story == semantic_story,
        "pipeline replaced or reinterpreted the lowering product",
    )
    require(
        first.semantic_graph == semantic_graph,
        "pipeline replaced or reinterpreted the graph product",
    )
    require(
        first.validation_report == validation_report,
        "pipeline replaced or reinterpreted the validation product",
    )

    classifications = {
        finding.classification
        for finding in first.validation_report.findings
    }
    require(
        {
            "duplicate_declaration",
            "referenced_only_identity",
            "conflicting_state_value",
        }
        <= classifications,
        "expected passive validation findings were not returned",
    )


def test_deterministic_stage_order() -> None:
    originals = (
        analysis_module.parse_narrative_source,
        analysis_module.lower_narrative_source,
        analysis_module.build_narrative_semantic_graph,
        analysis_module.validate_narrative_semantic_graph,
    )
    events: list[str] = []

    def parse_stage(source, *, source_name="<memory>"):
        events.append("parse")
        return originals[0](source, source_name=source_name)

    def lower_stage(document):
        events.append("lower")
        return originals[1](document)

    def graph_stage(story):
        events.append("graph")
        return originals[2](story)

    def validate_stage(graph):
        events.append("validate")
        return originals[3](graph)

    try:
        analysis_module.parse_narrative_source = parse_stage
        analysis_module.lower_narrative_source = lower_stage
        analysis_module.build_narrative_semantic_graph = graph_stage
        analysis_module.validate_narrative_semantic_graph = validate_stage
        analyze_narrative_source(VALID_SOURCE)
    finally:
        (
            analysis_module.parse_narrative_source,
            analysis_module.lower_narrative_source,
            analysis_module.build_narrative_semantic_graph,
            analysis_module.validate_narrative_semantic_graph,
        ) = originals

    require(
        events == ["parse", "lower", "graph", "validate"],
        "pipeline stage order changed",
    )


def test_unchanged_error_propagation_and_short_circuiting() -> None:
    invalid_source = "story Broken {"
    direct_parse_error = require_raises(
        NarrativeSourceParseError,
        lambda: parse_narrative_source(
            invalid_source,
            source_name="broken.apex",
        ),
        "direct parser did not reject invalid source",
    )
    pipeline_parse_error = require_raises(
        NarrativeSourceParseError,
        lambda: analyze_narrative_source(
            invalid_source,
            source_name="broken.apex",
        ),
        "pipeline did not propagate parser failure",
    )
    require(
        type(pipeline_parse_error) is type(direct_parse_error)
        and pipeline_parse_error.diagnostic
        == direct_parse_error.diagnostic,
        "pipeline changed the parser exception or diagnostic",
    )

    lowering_document = parse_narrative_source(
        LOWERING_FAILURE_SOURCE,
        source_name="lowering.apex",
    )
    direct_lowering_error = require_raises(
        NarrativeSemanticLoweringError,
        lambda: lower_narrative_source(lowering_document),
        "direct lowerer did not reject unrepresentable source",
    )
    pipeline_lowering_error = require_raises(
        NarrativeSemanticLoweringError,
        lambda: analyze_narrative_source(
            LOWERING_FAILURE_SOURCE,
            source_name="lowering.apex",
        ),
        "pipeline did not propagate lowering failure",
    )
    require(
        type(pipeline_lowering_error) is type(direct_lowering_error)
        and pipeline_lowering_error.diagnostic
        == direct_lowering_error.diagnostic,
        "pipeline changed the lowering exception or diagnostic",
    )

    originals = (
        analysis_module.parse_narrative_source,
        analysis_module.lower_narrative_source,
        analysis_module.build_narrative_semantic_graph,
        analysis_module.validate_narrative_semantic_graph,
    )
    events: list[str] = []

    def parse_failure_stage(source, *, source_name="<memory>"):
        events.append("parse")
        return originals[0](source, source_name=source_name)

    def forbidden_lower(document):
        events.append("lower")
        raise AssertionError("lowering ran after parser failure")

    def forbidden_graph(story):
        events.append("graph")
        raise AssertionError("graph ran after parser failure")

    def forbidden_validate(graph):
        events.append("validate")
        raise AssertionError("validation ran after parser failure")

    try:
        analysis_module.parse_narrative_source = parse_failure_stage
        analysis_module.lower_narrative_source = forbidden_lower
        analysis_module.build_narrative_semantic_graph = forbidden_graph
        analysis_module.validate_narrative_semantic_graph = forbidden_validate
        require_raises(
            NarrativeSourceParseError,
            lambda: analyze_narrative_source(invalid_source),
            "patched pipeline did not propagate parser failure",
        )
    finally:
        (
            analysis_module.parse_narrative_source,
            analysis_module.lower_narrative_source,
            analysis_module.build_narrative_semantic_graph,
            analysis_module.validate_narrative_semantic_graph,
        ) = originals

    require(
        events == ["parse"],
        "pipeline did not stop after parser failure",
    )


def test_dedicated_boundary_and_frozen_predecessor() -> None:
    module_path = PACKAGE_DIRECTORY / "language" / "narrative_analysis.py"
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
        public_classes == {"NarrativeSourceAnalysis"},
        "unexpected public analysis class exposed",
    )
    require(
        public_functions == {"analyze_narrative_source"},
        "unexpected public analysis function exposed",
    )

    forbidden = (
        "language.compiler",
        "language.project",
        "language.lexer",
        "language.parser",
        "runtime.",
        "tooling.cli",
        "air.",
        "artifact",
        "BuildDiagnostic",
        "DiagnosticError",
    )
    require(
        all(marker not in text for marker in forbidden),
        "analysis module escaped its opt-in composition boundary",
    )

    for relative in (
        "apexforge/language/narrative_source.py",
        "apexforge/language/narrative_parser.py",
        "apexforge/language/narrative_model.py",
        "apexforge/language/narrative_lowering.py",
        "apexforge/language/narrative_graph.py",
        "apexforge/language/narrative_validation.py",
        "apexforge/language/source.py",
        "apexforge/language/diagnostics.py",
        "apexforge/language/lexer.py",
        "apexforge/language/parser.py",
        "apexforge/language/compiler.py",
        "apexforge/language/project.py",
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
    test_public_api_and_result_invariants()
    test_exact_products_determinism_and_passive_findings()
    test_deterministic_stage_order()
    test_unchanged_error_propagation_and_short_circuiting()
    test_dedicated_boundary_and_frozen_predecessor()
    after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    require(before == after, "P11.5H-B smoke test mutated repository status")

    print("AFP-P11.5H-B opt-in narrative analysis pipeline smoke test passed.")
    print("P11.5G annotated freeze and exact predecessor HEAD: PASS")
    print("Exact five-file reviewed candidate ownership: PASS")
    print("Dedicated analysis public API and immutable four-product result: PASS")
    print("Exact parser, lowerer, graph, and validation products retained: PASS")
    print("Deterministic parse -> lower -> graph -> validate order: PASS")
    print("Unchanged parser and lowering exception propagation: PASS")
    print("Failure short-circuiting before later stages: PASS")
    print("Passive validation findings returned without diagnostic conversion: PASS")
    print("No compiler, project, runtime, CLI, AIR, artifact, or editor integration: PASS")
    print("Frozen P11.5G and operational baseline preservation: PASS")
    print("Repository no-op boundary: PASS")


if __name__ == "__main__":
    main()
