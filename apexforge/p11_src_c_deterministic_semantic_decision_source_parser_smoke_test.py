"""P11-SRC-C deterministic semantic-decision source parser smoke test."""

from dataclasses import FrozenInstanceError
from pathlib import Path

from language.lexer import KEYWORDS
from language.narrative_parser import is_narrative_source_document
from language.semantic_decision_parser import (
    SemanticDecisionSourceParseError,
    is_semantic_decision_source_document,
    parse_semantic_decision_source,
)
from language.semantic_decision_source import (
    SemanticDecisionSourceCandidate,
    SemanticDecisionSourceDocument,
)


SOURCE = """\
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

decision Secondary {
    candidate Wait
    converge using "select.explicit-order" {
        Wait
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
    root = Path(__file__).resolve().parents[1]

    assert is_semantic_decision_source_document(SOURCE) is True
    assert is_semantic_decision_source_document(" \n\t" + SOURCE) is True
    assert is_semantic_decision_source_document("decisionary X {}") is False
    assert is_semantic_decision_source_document("directive Main {}") is False
    assert is_semantic_decision_source_document("story Demo {}") is False
    assert is_narrative_source_document(SOURCE) is False

    first = parse_semantic_decision_source(
        SOURCE,
        source_name="decision.apex",
    )
    second = parse_semantic_decision_source(
        SOURCE,
        source_name="decision.apex",
    )

    assert type(first) is SemanticDecisionSourceDocument
    assert first == second
    assert first.span.source_name == "decision.apex"
    assert first.span.start.offset == 0
    assert first.span.end.offset == len(SOURCE)
    assert tuple(item.name.text for item in first.decisions) == (
        "BridgeAction",
        "Secondary",
    )

    bridge = first.decisions[0]
    assert tuple(item.name.text for item in bridge.candidates) == (
        "KeepOpen",
        "Destroy",
    )
    assert bridge.candidates[0].condition is not None
    assert bridge.candidates[0].condition.kind == "expression"
    assert bridge.candidates[0].condition.text == (
        "evacuationActive and routeOpen"
    )
    assert bridge.candidates[0].condition.span.source_name == "decision.apex"
    assert bridge.candidates[1].condition is None

    assert len(bridge.incompatibilities) == 1
    assert bridge.incompatibilities[0].left.text == "KeepOpen"
    assert bridge.incompatibilities[0].right.text == "Destroy"

    assert bridge.convergence is not None
    assert bridge.convergence.policy.kind == "string"
    assert bridge.convergence.policy.text == "rank.explicit-order"
    assert tuple(
        item.text for item in bridge.convergence.candidates
    ) == ("KeepOpen", "Destroy")

    assert bridge.paradox_elevation is not None
    assert bridge.paradox_elevation.condition is not None
    assert bridge.paradox_elevation.condition.kind == "identifier"
    assert bridge.paradox_elevation.condition.text == "unresolved"
    assert bridge.paradox_elevation.requirement is not None
    assert bridge.paradox_elevation.requirement.text == "information_loss"

    secondary = first.decisions[1]
    assert tuple(item.name.text for item in secondary.candidates) == ("Wait",)
    assert secondary.convergence is not None
    assert secondary.convergence.policy.text == "select.explicit-order"
    assert secondary.paradox_elevation is None

    error = _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            "decision Broken {\n    incompatible A B\n}\n",
            source_name="broken.apex",
        ),
    )
    assert error.diagnostic.code == "APX-SEMANTIC-DECISION-SYNTAX"
    assert error.diagnostic.stage == "parse"
    assert error.diagnostic.span is not None
    assert error.diagnostic.span.source_name == "broken.apex"

    _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            "decision Broken {\n    converge using \"rank.explicit-order\" {\n    }\n}\n"
        ),
    )
    _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            "decision Broken {\n    candidate A when\n}\n"
        ),
    )
    _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            "decision Broken {\n    converge using \"x\" { A }\n"
            "    converge using \"y\" { A }\n}\n"
        ),
    )
    _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            "decision Broken {\n    unknown A\n}\n"
        ),
    )
    _expect(
        SemanticDecisionSourceParseError,
        lambda: parse_semantic_decision_source(
            'decision Broken {\n candidate A\n converge using "unterminated {\n}\n'
        ),
    )

    _expect(TypeError, lambda: is_semantic_decision_source_document(None))
    _expect(TypeError, lambda: parse_semantic_decision_source(None))
    _expect(
        TypeError,
        lambda: parse_semantic_decision_source(SOURCE, source_name=None),
    )

    for word in (
        "decision",
        "candidate",
        "converge",
        "using",
        "incompatible",
        "paradox",
        "elevate",
    ):
        assert word not in KEYWORDS

    assert not (root / "apexforge/language/semantic_decision_lowering.py").exists()

    _expect(
        FrozenInstanceError,
        lambda: setattr(bridge.name, "text", "Changed"),
    )
    _expect(
        TypeError,
        lambda: SemanticDecisionSourceDocument(
            decisions=[bridge],
            span=first.span,
        ),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceCandidate(
            keyword_span=bridge.candidates[0].keyword_span,
            name=bridge.candidates[0].name,
            span=bridge.candidates[0].span,
            when_keyword_span=bridge.candidates[0].when_keyword_span,
            condition=None,
        ),
    )
    assert type(first.decisions) is tuple
    assert type(bridge.candidates) is tuple

    print("P11_SRC_B_CAPABILITY_REGRESSION=PASS")
    print("P11_SRC_C_DETERMINISTIC_SOURCE_PARSER=PASS")
    print("DOCUMENT_RECOGNITION=PASS")
    print("MULTI_DECISION_ORDER=PASS")
    print("CANDIDATE_ORDER=PASS")
    print("CONVERGENCE_ORDER=PASS")
    print("PARADOX_SOURCE_STRUCTURE=PASS")
    print("SOURCE_SPANS=PASS")
    print("DETERMINISTIC_REPEAT_PARSE=PASS")
    print("MALFORMED_SYNTAX_REJECTION=PASS")
    print("AIR_CLASSIFICATION_ISOLATION=PASS")
    print("NARRATIVE_CLASSIFICATION_ISOLATION=PASS")
    print("LEXER_MUTATION=NONE")
    print("LOWERING_MUTATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")


if __name__ == "__main__":
    main()