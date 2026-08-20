"""P11-SRC-F real .apex semantic-decision compile/analysis acceptance."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory

from language.narrative_parser import is_narrative_source_document
from language.semantic_decision_analysis import (
    SemanticDecisionSourceAnalysis,
    analyze_semantic_decision_source,
)
from language.semantic_decision_lowering import (
    LoweredSemanticDecisionDocument,
    SemanticDecisionSourceLoweringError,
    lower_semantic_decision_source,
)
from language.semantic_decision_parser import (
    SemanticDecisionSourceParseError,
    is_semantic_decision_source_document,
    parse_semantic_decision_source,
)
from language.semantic_decision_source import SemanticDecisionSourceDocument
from language.semantic_decision_source_validation import (
    SemanticDecisionSourceValidationError,
    validate_semantic_decision_source_bridge,
)
from semantic_decision import (
    AdvancedCondition,
    CandidateAlternative,
    ConvergencePolicy,
    ParadoxIncompatibilityEvidence,
)


VALID_SOURCE = """\
decision BridgeAction {
    candidate KeepOpen when evacuationActive and routeOpen
    candidate Destroy

    incompatible KeepOpen, Destroy

    converge using "rank.explicit-order" {
        KeepOpen
        Destroy
    }

    paradox elevate
        when unresolved
        requires information_loss
}

decision ComposeAction {
    candidate Left
    candidate Right
    converge using "compose.all-admissible" {
        Left
        Right
    }
}
"""


def _expect(error_type: type, action) -> Exception:
    try:
        action()
    except error_type as error:
        return error
    raise AssertionError(f"Expected {error_type.__name__}.")


def main() -> None:
    with TemporaryDirectory() as directory:
        source_path = Path(directory) / "semantic-decision.apex"
        with source_path.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(VALID_SOURCE)
        source_text = source_path.read_text(encoding="utf-8")

        assert source_path.suffix == ".apex"
        assert is_semantic_decision_source_document(source_text)
        assert not is_narrative_source_document(source_text)

        first = analyze_semantic_decision_source(
            source_text,
            source_name=str(source_path),
        )
        second = analyze_semantic_decision_source(
            source_text,
            source_name=str(source_path),
        )

        assert type(first) is SemanticDecisionSourceAnalysis
        assert first == second
        assert type(first.source_document) is SemanticDecisionSourceDocument
        assert type(first.semantic_bridge) is LoweredSemanticDecisionDocument
        assert first.source_document.span.source_name == str(source_path)
        assert first.semantic_bridge.span.source_name == str(source_path)

        assert tuple(
            item.name.text
            for item in first.source_document.decisions
        ) == ("BridgeAction", "ComposeAction")
        assert tuple(
            item.identity
            for item in first.semantic_bridge.decisions
        ) == ("BridgeAction", "ComposeAction")

        bridge = first.semantic_bridge.decisions[0]
        assert tuple(
            item.candidate.identity
            for item in bridge.candidates
        ) == ("KeepOpen", "Destroy")
        assert type(bridge.candidates[0].candidate) is CandidateAlternative
        assert type(bridge.candidates[0].condition) is AdvancedCondition
        assert bridge.candidates[0].condition.payload == (
            "evacuationActive and routeOpen"
        )
        assert type(bridge.policy) is ConvergencePolicy
        assert bridge.policy.identity == "rank.explicit-order"
        assert bridge.policy.parameters == (
            ("order", ("KeepOpen", "Destroy")),
        )
        assert len(bridge.incompatibilities) == 1
        assert (
            type(bridge.incompatibilities[0])
            is ParadoxIncompatibilityEvidence
        )

        # Direct-stage equivalence: the composed API must be exactly C -> D -> E.
        parsed = parse_semantic_decision_source(
            source_text,
            source_name=str(source_path),
        )
        lowered = lower_semantic_decision_source(parsed)
        validated = validate_semantic_decision_source_bridge(lowered)
        assert validated is lowered
        assert first.source_document == parsed
        assert first.semantic_bridge == lowered

    # Parse diagnostics pass through unchanged.
    parse_error = _expect(
        SemanticDecisionSourceParseError,
        lambda: analyze_semantic_decision_source(
            "decision Broken { candidate",
            source_name="parse-error.apex",
        ),
    )
    assert parse_error.diagnostic.stage == "parse"
    assert parse_error.diagnostic.span.source_name == "parse-error.apex"

    # Lowering diagnostics pass through unchanged.
    lowering_error = _expect(
        SemanticDecisionSourceLoweringError,
        lambda: analyze_semantic_decision_source(
            """\
decision Broken {
    candidate A
    converge using "rank.explicit-order" {
        Missing
    }
}
""",
            source_name="lowering-error.apex",
        ),
    )
    assert lowering_error.diagnostic.stage == "compile"
    assert lowering_error.diagnostic.span.source_name == "lowering-error.apex"

    # E validation diagnostics pass through unchanged.
    validation_error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: analyze_semantic_decision_source(
            """\
decision Duplicate {
    candidate A
}
decision Duplicate {
    candidate B
}
""",
            source_name="validation-error.apex",
        ),
    )
    assert validation_error.diagnostic.stage == "compile"
    assert (
        validation_error.diagnostic.span.source_name
        == "validation-error.apex"
    )

    analysis = analyze_semantic_decision_source(
        VALID_SOURCE,
        source_name="immutable.apex",
    )
    _expect(
        FrozenInstanceError,
        lambda: setattr(analysis, "semantic_bridge", object()),
    )
    _expect(
        TypeError,
        lambda: SemanticDecisionSourceAnalysis(
            object(),
            analysis.semantic_bridge,
        ),
    )
    _expect(
        TypeError,
        lambda: SemanticDecisionSourceAnalysis(
            analysis.source_document,
            object(),
        ),
    )

    # Source-family isolation remains explicit at the opt-in analysis boundary.
    assert not is_semantic_decision_source_document("story Example {}")
    assert is_narrative_source_document("story Example {}")
    assert not is_semantic_decision_source_document(
        "directive Main {}"
    )

    # F composes existing source stages only; it does not add operative semantics.
    assert not hasattr(analysis, "resolution")
    assert not hasattr(analysis.semantic_bridge, "resolution")
    assert not hasattr(analysis.semantic_bridge, "assessment")
    assert not hasattr(analysis.semantic_bridge, "elevated_state")
    assert not hasattr(analysis.semantic_bridge, "projection")

    print("P11_SRC_E_CAPABILITY_REGRESSION=PASS")
    print("P11_SRC_F_REAL_APEX_ANALYSIS=PASS")
    print("REAL_APEX_FILE_ACCEPTANCE=PASS")
    print("PARSE_LOWER_VALIDATE_COMPOSITION=PASS")
    print("DIRECT_STAGE_EQUIVALENCE=PASS")
    print("SOURCE_NAME_PROVENANCE=PASS")
    print("DETERMINISTIC_REPEAT_ANALYSIS=PASS")
    print("PARSE_DIAGNOSTIC_PROPAGATION=PASS")
    print("LOWERING_DIAGNOSTIC_PROPAGATION=PASS")
    print("VALIDATION_DIAGNOSTIC_PROPAGATION=PASS")
    print("AIR_SOURCE_FAMILY_ISOLATION=PASS")
    print("NARRATIVE_SOURCE_FAMILY_ISOLATION=PASS")
    print("P11_10_OBJECT_REUSE=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ASSESSMENT=NONE")
    print("P11_10_VALIDATION=NONE")
    print("CLI_TOOLING_INTEGRATION=NONE")
    print("PROJECT_COMPILER_ROUTING_MUTATION=NONE")
    print("RUNTIME_EXECUTION=NONE")


if __name__ == "__main__":
    main()