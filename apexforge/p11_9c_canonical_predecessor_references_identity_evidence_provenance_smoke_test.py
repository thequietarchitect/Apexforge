"""P11.9C canonical predecessor-reference/evidence/provenance smoke test."""

from dataclasses import FrozenInstanceError


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(exc_type, fn, message):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(message)


def main():
    from air.model import AIRDirective
    from authority.model import Principal
    from language.narrative_model import NarrativeIdentity
    from quad_vector.model import QuadVectorInput, ResultantVector
    from aether_air.model import AetherAirRepresentation, AetherBehaviorIntent
    from aether_air.records import (
        AetherEvidence,
        AetherIntentTrace,
        AetherPredecessorReference,
    )

    narrative_identity = NarrativeIdentity(kind="character", path=("Traveler",))
    directive = AIRDirective(
        id="directive:GateDirective",
        name="GateDirective",
        principal="traveler-principal",
        authority_checks=(),
        causal_decisions=(),
    )
    principal = Principal(id="traveler-principal")
    quad_input = QuadVectorInput(identity="quad.input:gate")
    resultant = ResultantVector(
        x=10,
        y=4,
        provenance=("quad.input:gate",),
    )

    narrative = AetherPredecessorReference(
        source_domain="narrative",
        source_kind=narrative_identity.kind,
        source_identity=(narrative_identity.kind,) + narrative_identity.path,
    )
    air = AetherPredecessorReference(
        source_domain="air",
        source_kind="directive",
        source_identity=(directive.id,),
    )
    authority = AetherPredecessorReference(
        source_domain="authority",
        source_kind="principal",
        source_identity=(principal.id,),
    )
    quad = AetherPredecessorReference(
        source_domain="quad_vector",
        source_kind="input",
        source_identity=(quad_input.identity,),
    )

    require(
        narrative.source_identity == ("character", "Traveler")
        and air.source_identity == (directive.id,)
        and authority.source_identity == (principal.id,)
        and quad.source_identity == (quad_input.identity,),
        "predecessor canonical identity components changed",
    )
    print("Canonical predecessor identity reference preservation: PASS")

    intent = AetherBehaviorIntent(
        kind_id="behavior.intent",
        intent="preserve gate traversal intent",
    )
    evidence = AetherEvidence(
        kind="observed",
        facts=(
            ("classification", "continuity"),
            ("resultant_coordinates", (resultant.x, resultant.y)),
            ("stable", True),
        ),
        provenance=resultant.provenance,
    )
    trace = AetherIntentTrace(
        predecessor=narrative,
        intent=intent,
        evidence=(evidence,),
    )
    require(
        trace.predecessor is narrative
        and trace.intent is intent
        and trace.evidence[0] is evidence,
        "intent trace lost exact supplied record identity",
    )
    print("Exact predecessor/intent/evidence object preservation: PASS")

    require(
        "identity" not in ResultantVector.__dataclass_fields__
        and evidence.facts[1][1] == (10, 4)
        and evidence.provenance == resultant.provenance,
        "resultant evidence gained a fabricated canonical identity",
    )
    print("Resultant evidence without fabricated identity: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(narrative, "source_kind", "changed"),
        "predecessor reference became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(evidence, "facts", ()),
        "evidence became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(trace, "intent", AetherBehaviorIntent("behavior.intent", "changed")),
        "intent trace became mutable",
    )
    print("Frozen predecessor/evidence/intent-trace boundary: PASS")

    raises(
        TypeError,
        lambda: AetherPredecessorReference("air", "directive", ["mutable"]),
        "mutable predecessor identity container accepted",
    )
    raises(
        TypeError,
        lambda: AetherEvidence("bad", facts=(("value", {"mutable": 1}),)),
        "mutable evidence value accepted",
    )
    raises(
        TypeError,
        lambda: AetherIntentTrace(narrative, intent, evidence=[evidence]),
        "mutable evidence collection accepted",
    )
    print("Recursively immutable trace-evidence contract: PASS")

    duplicate = AetherIntentTrace(
        predecessor=air,
        intent=intent,
        evidence=(
            AetherEvidence("first", provenance=("encounter:1",)),
            AetherEvidence("second", provenance=("encounter:2",)),
        ),
    )
    require(
        tuple(item.kind for item in duplicate.evidence) == ("first", "second"),
        "evidence encounter order changed",
    )
    print("Deterministic trace/evidence encounter-order preservation: PASS")

    for name in (
        "execute",
        "run",
        "bind",
        "resolve",
        "select",
        "rank",
        "grant",
        "deny",
        "validate",
        "synchronize",
        "evaluate",
        "normalize",
        "transform",
        "project",
        "lower",
        "compile",
        "emit",
        "generate",
        "load",
        "import_module",
    ):
        require(
            not hasattr(trace, name)
            and not hasattr(narrative, name)
            and not hasattr(evidence, name),
            "operative behavior leaked into P11.9C records: " + name,
        )
    print("Passive non-operative AETHER-AIR trace boundary: PASS")

    predecessor_fields = AetherPredecessorReference.__dataclass_fields__
    trace_fields = AetherIntentTrace.__dataclass_fields__
    require(
        tuple(predecessor_fields) == ("source_domain", "source_kind", "source_identity")
        and tuple(trace_fields) == ("predecessor", "intent", "evidence")
        and "relation" not in trace_fields,
        "P11.9C trace shape changed or gained general relationship semantics",
    )
    print("Narrow predecessor-to-intent trace topology: PASS")

    representation = AetherAirRepresentation(behaviors=(intent,))
    require(
        tuple(AetherAirRepresentation.__dataclass_fields__) == ("behaviors",)
        and not hasattr(representation, "traces")
        and not hasattr(representation, "sources")
        and not hasattr(representation, "evidence"),
        "P11.9D construction/composition boundary was preempted",
    )
    print("P11.9D deterministic construction/composition boundary preserved: PASS")


if __name__ == "__main__":
    main()
