"""P11-SRC-E semantic-decision source diagnostics and invalid-form rejection."""

from dataclasses import replace

from language.semantic_decision_lowering import (
    lower_semantic_decision_source,
)
from language.semantic_decision_parser import parse_semantic_decision_source
from language.semantic_decision_source_validation import (
    SemanticDecisionSourceValidationError,
    validate_semantic_decision_source_bridge,
)
from semantic_decision import (
    CandidateAlternative,
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


def _bridge(source: str, source_name: str):
    return lower_semantic_decision_source(
        parse_semantic_decision_source(
            source,
            source_name=source_name,
        )
    )


def main() -> None:
    bridge = _bridge(VALID_SOURCE, "valid.apex")
    validated = validate_semantic_decision_source_bridge(bridge)
    assert validated is bridge

    # Duplicate document-level decision identities are invalid source structure.
    duplicate_decision = _bridge(
        """\
decision Same {
    candidate A
}
decision Same {
    candidate B
}
""",
        "duplicate-decision.apex",
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(duplicate_decision),
    )
    assert error.diagnostic.code == "APX-SEMANTIC-DECISION-SOURCE-VALIDATION"
    assert error.diagnostic.stage == "compile"
    assert error.diagnostic.span is not None
    assert error.diagnostic.span.source_name == "duplicate-decision.apex"
    assert "Duplicate semantic-decision identity" in error.diagnostic.message

    # A source decision must actually expose a choice surface.
    no_candidates = _bridge(
        """\
decision Empty {
}
""",
        "empty-decision.apex",
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(no_candidates),
    )
    assert "at least one candidate" in error.diagnostic.message

    # Candidate identity forms a source-local reference namespace.
    duplicate_candidate = _bridge(
        """\
decision DuplicateCandidate {
    candidate A
    candidate A
}
""",
        "duplicate-candidate.apex",
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(duplicate_candidate),
    )
    assert "duplicate candidate identity" in error.diagnostic.message

    # Manually malformed bridge policy/reference association is rejected.
    decision = bridge.decisions[0]
    no_policy = replace(decision, policy=None)
    malformed = replace(bridge, decisions=(no_policy,) + bridge.decisions[1:])
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(malformed),
    )
    assert "without a convergence policy" in error.diagnostic.message

    no_convergence_candidates = replace(decision, convergence_candidates=())
    malformed = replace(
        bridge,
        decisions=(no_convergence_candidates,) + bridge.decisions[1:],
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(malformed),
    )
    assert "without convergence candidate references" in error.diagnostic.message

    # Bridge relationships must preserve exact candidate object ownership.
    foreign = CandidateAlternative(identity="Foreign")
    foreign_convergence = replace(
        decision,
        convergence_candidates=(foreign,),
    )
    malformed = replace(
        bridge,
        decisions=(foreign_convergence,) + bridge.decisions[1:],
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(malformed),
    )
    assert "not owned by the decision" in error.diagnostic.message

    foreign_incompatibility = ParadoxIncompatibilityEvidence(
        left=decision.candidates[0].candidate,
        right=foreign,
        materially_incompatible=True,
    )
    malformed_decision = replace(
        decision,
        incompatibilities=(foreign_incompatibility,),
    )
    malformed = replace(
        bridge,
        decisions=(malformed_decision,) + bridge.decisions[1:],
    )
    error = _expect(
        SemanticDecisionSourceValidationError,
        lambda: validate_semantic_decision_source_bridge(malformed),
    )
    assert "not owned by the decision" in error.diagnostic.message

    # Extension policies remain source-valid; P11.10 decides operative support.
    extension = bridge.decisions[1]
    assert extension.policy is not None
    assert extension.policy.identity == "extension.custom-policy"
    assert validate_semantic_decision_source_bridge(bridge) is bridge

    # E intentionally does not reinterpret P11.10 unresolved/eligibility rules.
    preserved_semantic_edge_cases = _bridge(
        """\
decision DeferredSemantics {
    candidate A
    candidate B
    incompatible A, A
    converge using "rank.explicit-order" {
        A
        A
    }
    paradox elevate
        requires information_loss
}
""",
        "deferred-semantics.apex",
    )
    assert (
        validate_semantic_decision_source_bridge(
            preserved_semantic_edge_cases
        )
        is preserved_semantic_edge_cases
    )

    _expect(
        TypeError,
        lambda: validate_semantic_decision_source_bridge(
            bridge.decisions[0]
        ),
    )

    # Direct predecessor regression: D remains a deterministic source bridge.
    reparsed = parse_semantic_decision_source(
        VALID_SOURCE,
        source_name="valid.apex",
    )
    relowered = lower_semantic_decision_source(reparsed)
    assert relowered == bridge
    assert tuple(item.identity for item in relowered.decisions) == (
        "BridgeAction",
        "ExtensionPolicyAction",
    )
    assert tuple(
        item.candidate.identity
        for item in relowered.decisions[0].candidates
    ) == ("KeepOpen", "Destroy")
    assert relowered.decisions[0].policy is not None
    assert relowered.decisions[0].policy.parameters == (
        ("order", ("KeepOpen", "Destroy")),
    )

    print("P11_SRC_D_CAPABILITY_REGRESSION=PASS")
    print("P11_SRC_E_SOURCE_VALIDATION=PASS")
    print("IDENTITY_COLLISION_REJECTION=PASS")
    print("EMPTY_DECISION_REJECTION=PASS")
    print("CANDIDATE_COLLISION_REJECTION=PASS")
    print("BRIDGE_POLICY_REFERENCE_COHERENCE=PASS")
    print("EXACT_CANDIDATE_OWNERSHIP=PASS")
    print("EXTENSION_POLICY_PRESERVED=PASS")
    print("P11_10_EDGE_CASES_DEFERRED=PASS")
    print("VALIDATION_RETURNS_EXACT_BRIDGE=PASS")
    print("CONDITION_EVALUATION=NONE")
    print("CONVERGENCE_RESOLUTION=NONE")
    print("PARADOX_ELIGIBILITY_VALIDATION=NONE")
    print("P11_10_VALIDATION=NONE")
    print("PROJECTION_RUNTIME=NONE")


if __name__ == "__main__":
    main()