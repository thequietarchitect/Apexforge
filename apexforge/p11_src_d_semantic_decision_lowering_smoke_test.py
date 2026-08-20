"""P11-SRC-D deterministic semantic-decision lowering smoke test."""

from dataclasses import FrozenInstanceError
from pathlib import Path

from language.semantic_decision_lowering import (
    LoweredSemanticDecisionCandidate,
    LoweredSemanticDecisionDeclaration,
    LoweredSemanticDecisionDocument,
    SemanticDecisionSourceLoweringError,
    lower_semantic_decision_source,
)
from language.semantic_decision_parser import (
    is_semantic_decision_source_document,
    parse_semantic_decision_source,
)
from semantic_decision import (
    AdvancedCondition,
    CandidateAlternative,
    ConvergencePolicy,
    ParadoxIncompatibilityEvidence,
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

decision ComposeAction {
    candidate Left
    candidate Right
    converge using "compose.all-admissible" {
        Left
        Right
    }
}

decision ExtensionPolicyAction {
    candidate Alpha
    candidate Beta
    converge using "extension.custom-policy" {
        Beta
        Alpha
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

    assert is_semantic_decision_source_document(SOURCE)
    parsed = parse_semantic_decision_source(
        SOURCE,
        source_name="semantic-decision.apex",
    )
    first = lower_semantic_decision_source(parsed)
    second = lower_semantic_decision_source(parsed)

    assert type(first) is LoweredSemanticDecisionDocument
    assert first == second
    assert first.span is parsed.span
    assert tuple(item.identity for item in first.decisions) == (
        "BridgeAction",
        "ComposeAction",
        "ExtensionPolicyAction",
    )

    bridge = first.decisions[0]
    assert type(bridge) is LoweredSemanticDecisionDeclaration
    assert tuple(
        item.candidate.identity
        for item in bridge.candidates
    ) == ("KeepOpen", "Destroy")

    keep_open = bridge.candidates[0]
    destroy = bridge.candidates[1]
    assert type(keep_open) is LoweredSemanticDecisionCandidate
    assert type(keep_open.candidate) is CandidateAlternative
    assert keep_open.candidate.payload is None
    assert type(keep_open.condition) is AdvancedCondition
    assert keep_open.condition.condition_kind == "source.expression"
    assert keep_open.condition.payload == "evacuationActive and routeOpen"
    assert destroy.condition is None

    assert type(bridge.policy) is ConvergencePolicy
    assert bridge.policy.identity == "rank.explicit-order"
    assert bridge.policy.parameters == (
        ("order", ("KeepOpen", "Destroy")),
    )
    assert bridge.convergence_candidates == (
        keep_open.candidate,
        destroy.candidate,
    )

    assert len(bridge.incompatibilities) == 1
    incompatibility = bridge.incompatibilities[0]
    assert type(incompatibility) is ParadoxIncompatibilityEvidence
    assert incompatibility.left is keep_open.candidate
    assert incompatibility.right is destroy.candidate
    assert incompatibility.materially_incompatible is True

    assert bridge.paradox_requested is True
    assert type(bridge.paradox_condition) is AdvancedCondition
    assert bridge.paradox_condition.condition_kind == "source.identifier"
    assert bridge.paradox_condition.payload == "unresolved"
    assert type(bridge.paradox_requirement) is AdvancedCondition
    assert bridge.paradox_requirement.payload == "information_loss"

    compose = first.decisions[1]
    assert type(compose.policy) is ConvergencePolicy
    assert compose.policy.identity == "compose.all-admissible"
    assert compose.policy.parameters == ()
    assert tuple(
        item.identity
        for item in compose.convergence_candidates
    ) == ("Left", "Right")
    assert compose.paradox_requested is False
    assert compose.paradox_condition is None
    assert compose.paradox_requirement is None

    extension = first.decisions[2]
    assert type(extension.policy) is ConvergencePolicy
    assert extension.policy.identity == "extension.custom-policy"
    assert extension.policy.parameters == ()
    assert tuple(
        item.identity
        for item in extension.convergence_candidates
    ) == ("Beta", "Alpha")

    assert all(
        item
        for item in first.provenance
        if item.startswith("source:semantic-decision.apex:")
    )
    assert all(
        candidate.candidate.provenance
        for decision in first.decisions
        for candidate in decision.candidates
    )

    _expect(
        FrozenInstanceError,
        lambda: setattr(bridge, "identity", "Changed"),
    )
    _expect(
        TypeError,
        lambda: lower_semantic_decision_source(parsed.decisions[0]),
    )

    unknown = parse_semantic_decision_source(
        """\
decision Broken {
    candidate A
    converge using "rank.explicit-order" {
        Missing
    }
}
""",
        source_name="unknown.apex",
    )
    error = _expect(
        SemanticDecisionSourceLoweringError,
        lambda: lower_semantic_decision_source(unknown),
    )
    assert error.diagnostic.code == "APX-SEMANTIC-DECISION-LOWERING"
    assert error.diagnostic.stage == "compile"
    assert error.diagnostic.span is not None
    assert error.diagnostic.span.source_name == "unknown.apex"

    ambiguous = parse_semantic_decision_source(
        """\
decision Broken {
    candidate A
    candidate A
    converge using "rank.explicit-order" {
        A
    }
}
""",
        source_name="ambiguous.apex",
    )
    error = _expect(
        SemanticDecisionSourceLoweringError,
        lambda: lower_semantic_decision_source(ambiguous),
    )
    assert "ambiguous candidate" in error.diagnostic.message

    empty_policy = parse_semantic_decision_source(
        """\
decision Broken {
    candidate A
    converge using "" {
        A
    }
}
""",
        source_name="empty-policy.apex",
    )
    error = _expect(
        SemanticDecisionSourceLoweringError,
        lambda: lower_semantic_decision_source(empty_policy),
    )
    assert error.diagnostic.code == "APX-SEMANTIC-DECISION-LOWERING"

    # Forward regression: SRC-C parsing remains deterministic and source ordered.
    reparsed = parse_semantic_decision_source(
        SOURCE,
        source_name="semantic-decision.apex",
    )
    assert reparsed == parsed
    assert tuple(item.name.text for item in parsed.decisions) == (
        "BridgeAction",
        "ComposeAction",
        "ExtensionPolicyAction",
    )
    assert tuple(
        item.name.text
        for item in parsed.decisions[0].candidates
    ) == ("KeepOpen", "Destroy")
    assert parsed.decisions[0].convergence is not None
    assert tuple(
        item.text
        for item in parsed.decisions[0].convergence.candidates
    ) == ("KeepOpen", "Destroy")

    # D owns passive bridge construction only.
    assert not hasattr(first, "resolution")
    assert not hasattr(bridge, "convergence_set")
    assert not hasattr(bridge, "assessment")
    assert not hasattr(bridge, "elevated_state")
    assert not hasattr(bridge, "validation")

    assert (root / "apexforge/semantic_decision").is_dir()

    print("P11_SRC_C_CAPABILITY_REGRESSION=PASS")
    print("P11_SRC_D_SEMANTIC_DECISION_LOWERING=PASS")
    print("P11_10_OBJECT_REUSE=PASS")
    print("CANDIDATE_LOWERING=PASS")
    print("PASSIVE_CONDITION_LOWERING=PASS")
    print("EXPLICIT_ORDER_POLICY_ADAPTATION=PASS")
    print("COMPOSE_POLICY_PARAMETER_BOUNDARY=PASS")
    print("EXTENSION_POLICY_PRESERVATION=PASS")
    print("SOURCE_REFERENCE_BINDING=PASS")
    print("EXPLICIT_INCOMPATIBILITY_EVIDENCE=PASS")
    print("PARADOX_REQUEST_PRESERVATION=PASS")
    print("SOURCE_PROVENANCE=PASS")
    print("DETERMINISTIC_REPEAT_LOWERING=PASS")
    print("LOWERING_DIAGNOSTICS=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_SET_CONSTRUCTION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ASSESSMENT=NONE")
    print("PARADOX_ELEVATION=NONE")
    print("VALIDATION_PROJECTION_RUNTIME=NONE")


if __name__ == "__main__":
    main()