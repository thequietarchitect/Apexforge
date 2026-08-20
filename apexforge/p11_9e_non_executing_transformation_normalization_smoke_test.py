"""P11.9E non-executing transformation and normalization smoke test."""

from dataclasses import FrozenInstanceError, fields


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
    from aether_air.transformation import (
        AetherAirTransformation,
        normalize_aether_air_snapshot,
        transform_aether_air_snapshot,
    )

    source_intent = AetherBehaviorIntent(
        "behavior.intent",
        "preserve gate state",
        (AetherIntentParameter("mode", "stable"),),
    )
    source_representation = AetherAirRepresentation((source_intent,))
    predecessor = AetherPredecessorReference(
        "narrative",
        "character",
        ("character", "Traveler"),
    )
    source_evidence = AetherEvidence(
        "observed",
        (("state", "stable"),),
        ("narrative:Traveler",),
    )
    source_trace = AetherIntentTrace(
        predecessor,
        source_intent,
        (source_evidence,),
    )
    source_traces = (source_trace,)
    source = construct_aether_air_snapshot(
        source_representation,
        traces=source_traces,
    )

    target_intent = AetherBehaviorIntent(
        "transformation.intent",
        "preserve explicit canonical restatement",
        (AetherIntentParameter("mode", "normalized"),),
    )
    target_representation = AetherAirRepresentation((target_intent,))
    target_evidence = AetherEvidence(
        "transformed",
        (("reason", "explicit-restatement"),),
        ("p11.9e:test",),
    )
    target_trace = AetherIntentTrace(
        predecessor,
        target_intent,
        (target_evidence,),
    )
    target_traces = (target_trace,)
    provenance = ("p11.9e:test", "caller:explicit")

    transformed = transform_aether_air_snapshot(
        source,
        operation="explicit-restatement",
        representation=target_representation,
        traces=target_traces,
        provenance=provenance,
    )

    require(
        transformed.source is source
        and transformed.result is not source
        and transformed.result.representation is target_representation
        and transformed.result.traces is target_traces
        and transformed.provenance is provenance,
        "transformation did not preserve exact source/target/provenance identities",
    )
    print("Explicit source/result/provenance identity lineage: PASS")

    require(
        source.representation is source_representation
        and source.traces is source_traces
        and source.representation.behaviors == (source_intent,),
        "transformation mutated the source snapshot",
    )
    print("Fresh result with immutable source preservation: PASS")

    normalization_provenance = ("p11.9e:normalization",)
    normalized = normalize_aether_air_snapshot(
        source,
        representation=source_representation,
        traces=source_traces,
        provenance=normalization_provenance,
    )
    require(
        normalized.operation == "normalization"
        and normalized.source is source
        and normalized.result is not source
        and normalized.result.representation is source_representation
        and normalized.result.traces is source_traces
        and normalized.provenance is normalization_provenance,
        "normalization changed explicit canonical-restatement contract",
    )
    print("Explicit normalization restatement without implicit rewrite: PASS")

    extension = transform_aether_air_snapshot(
        source,
        operation="extension.vendor-pass",
        representation=target_representation,
        traces=target_traces,
    )
    require(
        extension.operation == "extension.vendor-pass",
        "open passive transformation-operation extension boundary changed",
    )
    raises(
        ValueError,
        lambda: transform_aether_air_snapshot(
            source,
            operation=" bad-operation ",
            representation=target_representation,
            traces=target_traces,
        ),
        "untrimmed transformation operation was accepted",
    )
    raises(
        TypeError,
        lambda: transform_aether_air_snapshot(
            source,
            operation="bad-provenance",
            representation=target_representation,
            traces=target_traces,
            provenance=["mutable"],
        ),
        "mutable provenance container was accepted",
    )
    print("Open passive operation labels and exact provenance contract: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(transformed, "operation", "changed"),
        "AetherAirTransformation became mutable",
    )
    require(
        tuple(field.name for field in fields(AetherAirTransformation))
        == ("operation", "source", "result", "provenance"),
        "AetherAirTransformation field surface changed",
    )
    print("Frozen minimal transformation-record boundary: PASS")

    detached_intent = AetherBehaviorIntent("behavior.intent", "detached intent")
    detached_trace = AetherIntentTrace(predecessor, detached_intent)
    deferred = transform_aether_air_snapshot(
        source,
        operation="validation-deferred",
        representation=target_representation,
        traces=(target_trace, target_trace, detached_trace),
    )
    require(
        deferred.result.traces == (target_trace, target_trace, detached_trace),
        "P11.9E silently deduplicated or closure-validated traces",
    )
    print("P11.9F collision/closure validation boundary preserved: PASS")

    for value in (transformed, transformed.result, normalized):
        for name in (
            "execute",
            "run",
            "bind",
            "resolve",
            "select",
            "rank",
            "grant",
            "deny",
            "synchronize",
            "lower",
            "compile",
            "emit",
            "load",
            "import_module",
            "mutate",
        ):
            require(
                not hasattr(value, name),
                "operative behavior leaked into P11.9E: " + name,
            )
    print("Passive non-operative transformation boundary: PASS")

    require(
        tuple(field.name for field in fields(AetherAirRepresentation)) == ("behaviors",)
        and tuple(field.name for field in fields(AetherBehaviorIntent))
        == ("kind_id", "intent", "parameters")
        and tuple(field.name for field in fields(AetherPredecessorReference))
        == ("source_domain", "source_kind", "source_identity")
        and tuple(field.name for field in fields(AetherEvidence))
        == ("kind", "facts", "provenance")
        and tuple(field.name for field in fields(AetherIntentTrace))
        == ("predecessor", "intent", "evidence")
        and tuple(field.name for field in fields(AetherAirSnapshot))
        == ("representation", "traces"),
        "frozen P11.9B/C/D record shapes changed",
    )
    print("Frozen P11.9B/P11.9C/P11.9D record-shape preservation: PASS")

    for value in (transformed, normalized):
        require(
            not hasattr(value, "project")
            and not hasattr(value, "converge")
            and not hasattr(value, "evaluate_condition")
            and not hasattr(value, "paradox_elevate")
            and not hasattr(value, "generate_backend"),
            "P11.9G or P11.10 behavior leaked into transformation contract",
        )
    print("P11.9G downstream and P11.10 semantic boundaries preserved: PASS")


if __name__ == "__main__":
    main()
