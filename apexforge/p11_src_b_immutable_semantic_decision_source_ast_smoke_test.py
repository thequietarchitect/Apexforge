"""P11-SRC-B immutable semantic-decision source AST smoke test."""

from dataclasses import FrozenInstanceError
from pathlib import Path
import inspect

from language.lexer import KEYWORDS
from language.source import SourcePosition, SourceSpan
from language.semantic_decision_source import (
    SemanticDecisionSourceCandidate,
    SemanticDecisionSourceConvergence,
    SemanticDecisionSourceDeclaration,
    SemanticDecisionSourceDocument,
    SemanticDecisionSourceIdentifier,
    SemanticDecisionSourceIncompatibility,
    SemanticDecisionSourceParadoxElevation,
    SemanticDecisionSourceScalar,
)


PROPOSED_SOURCE_WORDS = (
    "decision",
    "candidate",
    "converge",
    "using",
    "incompatible",
    "paradox",
    "elevate",
)


def _position(offset: int, column: int) -> SourcePosition:
    signature = inspect.signature(SourcePosition)
    values = {}
    for name in signature.parameters:
        if name in {"offset", "index"}:
            values[name] = offset
        elif name == "line":
            values[name] = 1
        elif name == "column":
            values[name] = column
        else:
            raise AssertionError(f"Unsupported SourcePosition field {name!r}.")
    return SourcePosition(**values)


def _span(start: int = 0, end: int = 1) -> SourceSpan:
    return SourceSpan(
        source_name="decision.apex",
        start=_position(start, start + 1),
        end=_position(end, end + 1),
    )


def _expect(error_type: type, action) -> None:
    try:
        action()
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__}.")


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    decision_name = SemanticDecisionSourceIdentifier("BridgeAction", _span())
    keep_open = SemanticDecisionSourceIdentifier("KeepOpen", _span(2, 3))
    destroy = SemanticDecisionSourceIdentifier("Destroy", _span(4, 5))

    condition = SemanticDecisionSourceScalar(
        "expression",
        "evacuationActive and routeOpen",
        _span(6, 7),
    )
    candidate_keep = SemanticDecisionSourceCandidate(
        keyword_span=_span(8, 9),
        name=keep_open,
        span=_span(8, 12),
        when_keyword_span=_span(10, 11),
        condition=condition,
    )
    candidate_destroy = SemanticDecisionSourceCandidate(
        keyword_span=_span(13, 14),
        name=destroy,
        span=_span(13, 15),
    )

    incompatibility = SemanticDecisionSourceIncompatibility(
        keyword_span=_span(16, 17),
        left=keep_open,
        right=destroy,
        span=_span(16, 20),
    )

    policy = SemanticDecisionSourceScalar(
        "string",
        "rank.explicit-order",
        _span(21, 22),
    )
    convergence = SemanticDecisionSourceConvergence(
        keyword_span=_span(23, 24),
        using_keyword_span=_span(25, 26),
        policy=policy,
        candidates=(keep_open, destroy),
        span=_span(23, 30),
    )

    paradox = SemanticDecisionSourceParadoxElevation(
        paradox_keyword_span=_span(31, 32),
        elevate_keyword_span=_span(33, 34),
        span=_span(31, 40),
        when_keyword_span=_span(35, 36),
        condition=SemanticDecisionSourceScalar(
            "identifier",
            "unresolved",
            _span(37, 38),
        ),
        requires_keyword_span=_span(39, 40),
        requirement=SemanticDecisionSourceScalar(
            "identifier",
            "information_loss",
            _span(41, 42),
        ),
    )

    declaration = SemanticDecisionSourceDeclaration(
        keyword_span=_span(43, 44),
        name=decision_name,
        candidates=(candidate_keep, candidate_destroy),
        incompatibilities=(incompatibility,),
        convergence=convergence,
        paradox_elevation=paradox,
        span=_span(43, 60),
    )
    document = SemanticDecisionSourceDocument(
        decisions=(declaration,),
        span=_span(0, 60),
    )

    assert document.decisions == (declaration,)
    assert declaration.candidates == (candidate_keep, candidate_destroy)
    assert declaration.incompatibilities == (incompatibility,)
    assert declaration.convergence is convergence
    assert declaration.paradox_elevation is paradox
    assert candidate_keep.condition is condition
    assert convergence.candidates == (keep_open, destroy)
    assert convergence.policy.text == "rank.explicit-order"
    assert paradox.condition is not None
    assert paradox.condition.text == "unresolved"
    assert paradox.requirement is not None
    assert paradox.requirement.text == "information_loss"

    _expect(
        FrozenInstanceError,
        lambda: setattr(decision_name, "text", "Changed"),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceIdentifier(" BridgeAction", _span()),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceScalar("boolean", "yes", _span()),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceScalar("unsupported", "x", _span()),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceCandidate(
            keyword_span=_span(),
            name=keep_open,
            span=_span(),
            when_keyword_span=_span(),
            condition=None,
        ),
    )
    _expect(
        TypeError,
        lambda: SemanticDecisionSourceConvergence(
            keyword_span=_span(),
            using_keyword_span=_span(),
            policy=policy,
            candidates=[keep_open],
            span=_span(),
        ),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceConvergence(
            keyword_span=_span(),
            using_keyword_span=_span(),
            policy=policy,
            candidates=(),
            span=_span(),
        ),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceParadoxElevation(
            paradox_keyword_span=_span(),
            elevate_keyword_span=_span(),
            span=_span(),
            requires_keyword_span=_span(),
            requirement=None,
        ),
    )
    _expect(
        TypeError,
        lambda: SemanticDecisionSourceDeclaration(
            keyword_span=_span(),
            name=decision_name,
            candidates=[candidate_keep],
            incompatibilities=(),
            span=_span(),
        ),
    )
    _expect(
        ValueError,
        lambda: SemanticDecisionSourceDocument(
            decisions=(),
            span=_span(),
        ),
    )

    assert all(word not in KEYWORDS for word in PROPOSED_SOURCE_WORDS)
    assert not (root / "apexforge/language/semantic_decision_parser.py").exists()
    assert not (root / "apexforge/language/semantic_decision_lowering.py").exists()

    print("P11_SRC_B_IMMUTABLE_SOURCE_AST=PASS")
    print("SOURCE_PROVENANCE=PASS")
    print("FROZEN_RECORDS=PASS")
    print("EXACT_TUPLE_CONTRACTS=PASS")
    print("OPTIONAL_PAIR_INVARIANTS=PASS")
    print("LEXER_MUTATION=NONE")
    print("PARSER_MUTATION=NONE")
    print("LOWERING_MUTATION=NONE")
    print("SEMANTIC_EXECUTION=NONE")


if __name__ == "__main__":
    main()