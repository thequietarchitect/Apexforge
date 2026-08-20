"""P11.9D deterministic AETHER-AIR interstitial construction smoke test."""

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
    from aether_air.construction import (
        AetherAirSnapshot,
        construct_aether_air_snapshot,
    )
    from aether_air.model import (
        AetherAirRepresentation,
        AetherBehaviorIntent,
        AetherIntentParameter,
    )
    from aether_air.records import (
        AetherEvidence,
        AetherIntentTrace,
        AetherPredecessorReference,
    )

    behavior_a = AetherBehaviorIntent(
        kind_id="behavior.intent",
        intent="preserve traveler continuity",
        parameters=(AetherIntentParameter("mode", "observed"),),
    )
    behavior_b = AetherBehaviorIntent(
        kind_id="projection.intent",
        intent="preserve downstream projection intent",
    )
    representation = AetherAirRepresentation(behaviors=(behavior_a, behavior_b))

    predecessor_a = AetherPredecessorReference(
        source_domain="narrative",
        source_kind="character",
        source_identity=("character", "Traveler"),
    )
    predecessor_b = AetherPredecessorReference(
        source_domain="air",
        source_kind="directive",
        source_identity=("directive:GateDirective",),
    )
    evidence_a = AetherEvidence(
        kind="observed",
        facts=(("classification", "continuity"),),
        provenance=("narrative:Traveler",),
    )
    evidence_b = AetherEvidence(
        kind="observed",
        facts=(("classification", "projection"),),
        provenance=("air:directive:GateDirective",),
    )
    trace_a = AetherIntentTrace(
        predecessor=predecessor_a,
        intent=behavior_a,
        evidence=(evidence_a,),
    )
    trace_b = AetherIntentTrace(
        predecessor=predecessor_b,
        intent=behavior_b,
        evidence=(evidence_b,),
    )
    traces = (trace_a, trace_b)

    snapshot = construct_aether_air_snapshot(
        representation,
        traces=traces,
    )

    require(
        type(snapshot) is AetherAirSnapshot
        and snapshot.representation is representation
        and snapshot.traces is traces
        and snapshot.traces[0] is trace_a
        and snapshot.traces[0].predecessor is predecessor_a
        and snapshot.traces[0].intent is behavior_a
        and snapshot.traces[0].evidence[0] is evidence_a,
        "construction changed supplied canonical object identity",
    )
    print("Exact P11.9B/P11.9C object identity composition: PASS")

    require(
        snapshot.traces == (trace_a, trace_b),
        "construction changed trace encounter order",
    )
    print("Deterministic trace encounter-order construction preservation: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(snapshot, "traces", ()),
        "AETHER-AIR snapshot became mutable",
    )
    raises(
        TypeError,
        lambda: AetherAirSnapshot(representation, traces=[trace_a]),
        "mutable trace container accepted",
    )
    print("Frozen exact-tuple AETHER-AIR snapshot boundary: PASS")

    orphan_intent = AetherBehaviorIntent(
        kind_id="constraint.intent",
        intent="preserve externally validated constraint intent",
    )
    orphan_trace = AetherIntentTrace(
        predecessor=predecessor_a,
        intent=orphan_intent,
    )
    deferred = construct_aether_air_snapshot(
        representation,
        traces=(trace_a, orphan_trace, trace_a),
    )
    require(
        deferred.traces == (trace_a, orphan_trace, trace_a),
        "P11.9D silently deduplicated or closure-validated traces",
    )
    print("P11.9F collision/closure validation boundary preserved: PASS")

    fields = tuple(AetherAirSnapshot.__dataclass_fields__)
    require(
        fields == ("representation", "traces"),
        "P11.9D snapshot shape expanded beyond representation/traces",
    )
    print("Minimal deterministic snapshot composition surface: PASS")

    for name in (
        "execute",
        "run",
        "bind",
        "resolve",
        "select",
        "rank",
        "grant",
        "deny",
        "evaluate",
        "synchronize",
        "normalize",
        "transform",
        "project",
        "lower",
        "compile",
        "emit",
        "generate",
        "discover",
        "scan",
        "load",
        "import_module",
        "adapt",
    ):
        require(
            not hasattr(snapshot, name),
            "operative or later-stage behavior leaked into P11.9D snapshot: " + name,
        )
    print("Passive non-operative explicit-input construction boundary: PASS")

    require(
        tuple(AetherAirRepresentation.__dataclass_fields__) == ("behaviors",)
        and tuple(AetherBehaviorIntent.__dataclass_fields__)
        == ("kind_id", "intent", "parameters")
        and tuple(AetherPredecessorReference.__dataclass_fields__)
        == ("source_domain", "source_kind", "source_identity")
        and tuple(AetherEvidence.__dataclass_fields__) == ("kind", "facts", "provenance")
        and tuple(AetherIntentTrace.__dataclass_fields__)
        == ("predecessor", "intent", "evidence"),
        "frozen P11.9B/P11.9C record shapes changed",
    )
    print("Frozen P11.9B/P11.9C record-shape preservation: PASS")

    require(
        not hasattr(snapshot, "validation")
        and not hasattr(snapshot, "collisions")
        and not hasattr(snapshot, "closure")
        and not hasattr(snapshot, "backend")
        and not hasattr(snapshot, "optimized_air")
        and not hasattr(snapshot, "paradox_elevation"),
        "P11.9E/F/G/P11.10 ownership boundary was preempted",
    )
    print("P11.9E/F/G and P11.10 ownership boundaries preserved: PASS")


if __name__ == "__main__":
    main()
