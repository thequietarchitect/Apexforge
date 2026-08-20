"""P11-SRC-G project and language-server semantic-decision compatibility."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from language.diagnostics import BuildDiagnostic, diagnostics_from_exception
from language.semantic_decision_analysis import analyze_semantic_decision_source
from language.semantic_decision_project_analysis import (
    SemanticDecisionProjectAnalysis,
    SemanticDecisionProjectAnalysisError,
    analyze_semantic_decision_project_sources,
)
from language_server.diagnostics import analyze_document
from tooling.cli import EXIT_CHECK, EXIT_SUCCESS, main


SOURCE_A = """\
decision AlphaDecision {
    candidate Keep
    candidate Change
    converge using "rank.explicit-order" {
        Keep
        Change
    }
}
"""

SOURCE_B = """\
decision BetaDecision {
    candidate Left
    candidate Right
    converge using "compose.all-admissible" {
        Left
        Right
    }
}
"""

DUPLICATE_A = """\
decision Duplicate {
    candidate A
}
"""

DUPLICATE_B = """\
decision Duplicate {
    candidate B
}
"""

INVALID_DECISION = """\
decision Broken {
    candidate
}
"""

AIR_SOURCE = "directive AirMain {}\n"

NARRATIVE_SOURCE = """\
story LspStory {
    character Hero
    scene Start
    scene End
    choice Decide {
        scene Start
        path "Continue" {
            destination End
        }
    }
    timeline Main {
        scenes [Start, End]
    }
}
"""


def _require_raises(exc_type, operation, message):
    try:
        operation()
    except exc_type as error:
        return error
    raise AssertionError(message)


def _write_project(root, name, records):
    root.mkdir(parents=True, exist_ok=True)
    source_names = []
    for source_name, source in records:
        source_names.append(source_name)
        (root / source_name).write_text(source, encoding="utf-8")
    (root / "apexforge.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "name": name,
                "sources": source_names,
                "entry": None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _invoke(arguments):
    stdout = StringIO()
    stderr = StringIO()
    code = main(
        tuple(arguments),
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def main_test():
    assert SemanticDecisionProjectAnalysis.__dataclass_params__.frozen is True

    direct_a = analyze_semantic_decision_source(
        SOURCE_A,
        source_name="a.apex",
    )
    direct_b = analyze_semantic_decision_source(
        SOURCE_B,
        source_name="b.apex",
    )
    project = analyze_semantic_decision_project_sources(
        (
            ("a.apex", SOURCE_A),
            ("b.apex", SOURCE_B),
        )
    )
    assert type(project) is SemanticDecisionProjectAnalysis
    assert project.source_analyses == (direct_a, direct_b)
    assert tuple(
        decision.identity
        for analysis in project.source_analyses
        for decision in analysis.semantic_bridge.decisions
    ) == ("AlphaDecision", "BetaDecision")

    _require_raises(
        FrozenInstanceError,
        lambda: setattr(project, "source_analyses", (direct_a,)),
        "semantic-decision project analysis is mutable",
    )

    duplicate_error = _require_raises(
        SemanticDecisionProjectAnalysisError,
        lambda: analyze_semantic_decision_project_sources(
            (
                ("a.apex", DUPLICATE_A),
                ("b.apex", DUPLICATE_B),
            )
        ),
        "cross-source duplicate decision identity was accepted",
    )
    assert type(duplicate_error.diagnostic) is BuildDiagnostic
    assert duplicate_error.diagnostic.severity == "error"
    assert duplicate_error.diagnostic.code == "APX-SEMANTIC-DECISION-PROJECT"
    assert duplicate_error.diagnostic.stage == "link"
    assert duplicate_error.diagnostic.span is not None
    assert duplicate_error.diagnostic.span.source_name == "b.apex"
    assert len(duplicate_error.diagnostic.related_spans) == 1
    assert duplicate_error.diagnostic.related_spans[0].source_name == "a.apex"
    assert diagnostics_from_exception(duplicate_error) == (
        duplicate_error.diagnostic,
    )

    with TemporaryDirectory(prefix="apexforge-src-g-project-") as temporary:
        root = Path(temporary)
        valid_root = root / "valid"
        duplicate_root = root / "duplicate"

        _write_project(
            valid_root,
            "SemanticDecisionProject",
            (
                ("a.apex", SOURCE_A),
                ("b.apex", SOURCE_B),
            ),
        )
        _write_project(
            duplicate_root,
            "DuplicateSemanticDecisionProject",
            (
                ("a.apex", DUPLICATE_A),
                ("b.apex", DUPLICATE_B),
            ),
        )

        valid_check = _invoke(("check", str(valid_root)))
        assert valid_check == (
            EXIT_SUCCESS,
            "ApexForge check passed: SemanticDecisionProject (2 source(s)).\n",
            "",
        )

        duplicate_check = _invoke(("check", str(duplicate_root)))
        assert duplicate_check[0] == EXIT_CHECK
        assert duplicate_check[1] == ""
        assert "APX-SEMANTIC-DECISION-PROJECT" in duplicate_check[2]
        assert "Duplicate semantic-decision identity" in duplicate_check[2]
        assert "b.apex" in duplicate_check[2]

    valid_uri = "file:///workspace/valid-decision.apex"
    invalid_uri = "file:///workspace/invalid-decision.apex"
    air_uri = "file:///workspace/air.apex"
    narrative_uri = "file:///workspace/story.apex"

    assert analyze_document(valid_uri, SOURCE_A) == ()

    invalid_diagnostics = analyze_document(
        invalid_uri,
        INVALID_DECISION,
        include_related_information=True,
    )
    repeated_invalid_diagnostics = analyze_document(
        invalid_uri,
        INVALID_DECISION,
        include_related_information=True,
    )
    assert invalid_diagnostics == repeated_invalid_diagnostics
    assert len(invalid_diagnostics) == 1
    assert invalid_diagnostics[0].get("code") == (
        "APX-SEMANTIC-DECISION-SYNTAX"
    )

    assert analyze_document(air_uri, AIR_SOURCE) == ()
    assert analyze_document(narrative_uri, NARRATIVE_SOURCE) == ()

    print("P11_SRC_F_PROJECT_COMPOSITION_REUSE=PASS")
    print("P11_SRC_G_PROJECT_ANALYSIS=PASS")
    print("MANIFEST_ORDER_PRESERVED=PASS")
    print("PROJECT_ANALYSIS_IMMUTABLE=PASS")
    print("CROSS_SOURCE_IDENTITY_UNIQUENESS=PASS")
    print("CROSS_SOURCE_RELATED_SPAN=PASS")
    print("CLI_PROJECT_DUPLICATE_REJECTION=PASS")
    print("LSP_SEMANTIC_DECISION_VALID=PASS")
    print("LSP_SEMANTIC_DECISION_DIAGNOSTIC=PASS")
    print("LSP_DIAGNOSTIC_DETERMINISM=PASS")
    print("LSP_AIR_ROUTING_PRESERVED=PASS")
    print("LSP_NARRATIVE_ROUTING_PRESERVED=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ASSESSMENT=NONE")
    print("P11_10_VALIDATION=NONE")
    print("RUNTIME_EXECUTION=NONE")


if __name__ == "__main__":
    main_test()