"""P11.9F AETHER-AIR validation, collision, closure, and extension smoke test."""

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
    from aether_air.construction import construct_aether_air_snapshot
    from aether_air.model import (
        AetherAirRepresentation,
        AetherBehaviorIntent,
        AetherBehaviorKind,
        AetherIntentParameter,
    )
    from aether_air.records import (
        AetherEvidence,
        AetherIntentTrace,
        AetherPredecessorReference,
    )
    from aether_air.transformation import (
        normalize_aether_air_snapshot,
        transform_aether_air_snapshot,
    )
    from aether_air.validation import (
        AetherAirTransformationValidationReceipt,
        AetherAirValidationReceipt,
        validate_aether_air_snapshot,
        validate_aether_air_transformation,
    )

    core = AetherBehaviorIntent(
        "behavior.intent",
        "preserve continuity",
        (AetherIntentParameter("mode", "stable"),),
    )
    extension = AetherBehaviorIntent(
        "extension.audit",
        "record passive audit",
    )
    representation = AetherAirRepresentation((core, extension))

    predecessor = AetherPredecessorReference(
        "narrative",
        "character",
        ("character", "Traveler"),
    )
    evidence = AetherEvidence(
        "observed",
        (("classification", "continuity"),),
        ("narrative:Traveler",),
    )
    core_trace = AetherIntentTrace(predecessor, core, (evidence,))
    extension_trace = AetherIntentTrace(predecessor, extension)
    snapshot = construct_aether_air_snapshot(
        representation,
        traces=(core_trace, extension_trace),
    )
    extension_kind = AetherBehaviorKind("extension.audit")

    receipt = validate_aether_air_snapshot(
        snapshot,
        extension_kinds=(extension_kind,),
    )
    require(
        type(receipt) is AetherAirValidationReceipt
        and receipt.snapshot is snapshot
        and receipt.extension_kind_ids == ("extension.audit",)
        and receipt.provenance == evidence.provenance
        and len(receipt.checks) == 8,
        "valid snapshot receipt changed canonical identity/order",
    )
    print("Immutable snapshot validation receipt and extension/provenance preservation: PASS")

    duplicate_behavior = construct_aether_air_snapshot(
        AetherAirRepresentation((core, core)),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(duplicate_behavior),
        "duplicate behavior intent was accepted",
    )
    print("Duplicate behavior-intent collision rejection: PASS")

    duplicate_trace = construct_aether_air_snapshot(
        AetherAirRepresentation((core,)),
        traces=(core_trace, core_trace),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(duplicate_trace),
        "duplicate intent trace was accepted",
    )
    print("Duplicate intent-trace collision rejection: PASS")

    detached_equal_intent = AetherBehaviorIntent(
        "behavior.intent",
        "preserve continuity",
        (AetherIntentParameter("mode", "stable"),),
    )
    dangling_trace = AetherIntentTrace(predecessor, detached_equal_intent, (evidence,))
    dangling_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core,)),
        traces=(dangling_trace,),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(dangling_snapshot),
        "trace closure accepted a detached equal intent object",
    )
    print("Exact trace-to-representation object closure validation: PASS")

    conflicting_predecessor = AetherPredecessorReference(
        "narrative",
        "scene",
        ("character", "Traveler"),
    )
    conflicting_trace = AetherIntentTrace(conflicting_predecessor, extension)
    conflict_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core, extension)),
        traces=(core_trace, conflicting_trace),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(
            conflict_snapshot,
            extension_kinds=(extension_kind,),
        ),
        "predecessor source-owned identity kind collision was accepted",
    )
    print("Predecessor source-identity kind collision rejection: PASS")

    repeated_evidence_trace = AetherIntentTrace(
        predecessor,
        core,
        (evidence, evidence),
    )
    repeated_evidence_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core,)),
        traces=(repeated_evidence_trace,),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(repeated_evidence_snapshot),
        "duplicate trace evidence was accepted",
    )
    duplicate_provenance_evidence = AetherEvidence(
        "observed",
        (),
        ("source:1", "source:1"),
    )
    duplicate_provenance_trace = AetherIntentTrace(
        predecessor,
        core,
        (duplicate_provenance_evidence,),
    )
    duplicate_provenance_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core,)),
        traces=(duplicate_provenance_trace,),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(duplicate_provenance_snapshot),
        "duplicate evidence provenance was accepted",
    )
    print("Trace evidence and provenance integrity validation: PASS")

    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(snapshot),
        "undeclared extension kind was accepted",
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(
            snapshot,
            extension_kinds=(
                extension_kind,
                AetherBehaviorKind("extension.audit"),
            ),
        ),
        "duplicate extension kind declaration was accepted",
    )
    raises(
        ValueError,
        lambda: validate_aether_air_snapshot(
            construct_aether_air_snapshot(AetherAirRepresentation((core,))),
            extension_kinds=(AetherBehaviorKind("behavior.intent"),),
        ),
        "extension declaration collided with core kind",
    )
    print("Extension-kind collision and closure validation: PASS")

    normalization = normalize_aether_air_snapshot(
        snapshot,
        representation=representation,
        traces=snapshot.traces,
        provenance=("normalization:test",),
    )
    normalization_receipt = validate_aether_air_transformation(
        normalization,
        extension_kinds=(extension_kind,),
    )
    require(
        type(normalization_receipt) is AetherAirTransformationValidationReceipt
        and normalization_receipt.transformation is normalization
        and normalization_receipt.source_receipt.snapshot is snapshot
        and normalization_receipt.result_receipt.snapshot is normalization.result,
        "normalization validation receipt changed transformation lineage",
    )

    changed_representation = AetherAirRepresentation(
        (
            AetherBehaviorIntent("behavior.intent", "changed continuity"),
            extension,
        )
    )
    changed_normalization = normalize_aether_air_snapshot(
        snapshot,
        representation=changed_representation,
        traces=(),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_transformation(
            changed_normalization,
            extension_kinds=(extension_kind,),
        ),
        "normalization source/result disagreement was accepted",
    )

    explicit_transform = transform_aether_air_snapshot(
        snapshot,
        operation="explicit.restatement",
        representation=changed_representation,
        traces=(),
    )
    transformed_receipt = validate_aether_air_transformation(
        explicit_transform,
        extension_kinds=(extension_kind,),
    )
    require(
        transformed_receipt.transformation is explicit_transform,
        "explicit non-normalization transformation was rejected or replaced",
    )
    print("Transformation source/result consistency and open-operation boundary: PASS")

    duplicate_transformation_provenance = transform_aether_air_snapshot(
        snapshot,
        operation="explicit.restatement",
        representation=representation,
        traces=snapshot.traces,
        provenance=("source:1", "source:1"),
    )
    raises(
        ValueError,
        lambda: validate_aether_air_transformation(
            duplicate_transformation_provenance,
            extension_kinds=(extension_kind,),
        ),
        "duplicate transformation provenance was accepted",
    )

    raises(
        FrozenInstanceError,
        lambda: setattr(receipt, "checks", ()),
        "snapshot validation receipt became mutable",
    )
    raises(
        FrozenInstanceError,
        lambda: setattr(normalization_receipt, "checks", ()),
        "transformation validation receipt became mutable",
    )
    for value in (receipt, normalization_receipt):
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
            "normalize",
            "transform",
            "lower",
            "compile",
            "emit",
            "load",
            "import_module",
            "mutate",
            "repair",
        ):
            require(
                not hasattr(value, name),
                "operative behavior leaked into validation receipt: " + name,
            )
    print("Immutable passive validation receipts with no repair/selection authority: PASS")

    import dataclasses
    import aether_air.model as model
    import aether_air.records as records
    import aether_air.construction as construction
    import aether_air.transformation as transformation

    require(
        tuple(field.name for field in dataclasses.fields(model.AetherAirRepresentation))
        == ("behaviors",)
        and tuple(field.name for field in dataclasses.fields(records.AetherIntentTrace))
        == ("predecessor", "intent", "evidence")
        and tuple(field.name for field in dataclasses.fields(construction.AetherAirSnapshot))
        == ("representation", "traces")
        and tuple(field.name for field in dataclasses.fields(transformation.AetherAirTransformation))
        == ("operation", "source", "result", "provenance"),
        "frozen B/C/D/E record shapes changed",
    )
    print("Frozen P11.9B/P11.9C/P11.9D/P11.9E record-shape preservation: PASS")

    for value in (receipt, normalization_receipt):
        for name in (
            "choose_branch",
            "evaluate_condition",
            "converge",
            "paradox_elevation",
            "project_backend",
            "generate_native",
        ):
            require(
                not hasattr(value, name),
                "P11.9G/P11.10 authority leaked into P11.9F: " + name,
            )
    print("P11.9G downstream and P11.10 semantic boundaries preserved: PASS")


if __name__ == "__main__":
    main()
