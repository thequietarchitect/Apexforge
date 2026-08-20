"""P11.9G explicit downstream projection-boundary smoke test."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
PROJECTION_PATH = ROOT / "apexforge" / "aether_air" / "projection.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises(exc_type, operation, message):
    try:
        operation()
    except exc_type:
        return
    raise AssertionError(message)


def git(*arguments):
    completed = subprocess.run(
        ("git",) + arguments,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def main():
    from aether_air import (
        AetherAirDownstreamProjection,
        AetherAirRepresentation,
        AetherBehaviorIntent,
        AetherEvidence,
        AetherIntentTrace,
        AetherPredecessorReference,
        construct_aether_air_snapshot,
        normalize_aether_air_snapshot,
        project_validated_aether_air,
        validate_aether_air_snapshot,
        validate_aether_air_transformation,
    )

    core = AetherBehaviorIntent(
        "behavior.intent",
        "preserve continuity",
    )
    predecessor = AetherPredecessorReference(
        "narrative",
        "character",
        ("character", "Traveler"),
    )
    evidence = AetherEvidence(
        "observed",
        (),
        ("source:story",),
    )
    trace = AetherIntentTrace(predecessor, core, (evidence,))
    snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((core,)),
        traces=(trace,),
    )
    receipt = validate_aether_air_snapshot(snapshot)

    projection = project_validated_aether_air(
        receipt,
        consumer="optimized-air",
        provenance=("projection:test",),
    )
    require(
        type(projection) is AetherAirDownstreamProjection
        and projection.validation is receipt
        and projection.consumer == "optimized-air"
        and projection.provenance == ("projection:test",),
        "snapshot projection changed receipt identity or explicit metadata",
    )
    print("Exact validated-snapshot receipt projection preservation: PASS")

    normalization = normalize_aether_air_snapshot(
        snapshot,
        representation=snapshot.representation,
        traces=snapshot.traces,
        provenance=("normalization:test",),
    )
    transformation_receipt = validate_aether_air_transformation(normalization)
    transformation_projection = project_validated_aether_air(
        transformation_receipt,
        consumer="native-backend",
        provenance=("projection:transformation",),
    )
    require(
        transformation_projection.validation is transformation_receipt
        and transformation_projection.validation.transformation is normalization
        and transformation_projection.consumer == "native-backend",
        "transformation validation lineage was reconstructed or replaced",
    )
    print("Exact validated-transformation receipt lineage preservation: PASS")

    raises(
        TypeError,
        lambda: project_validated_aether_air(
            snapshot,
            consumer="optimized-air",
        ),
        "projection accepted an unvalidated raw snapshot",
    )
    raises(
        TypeError,
        lambda: project_validated_aether_air(
            object(),
            consumer="optimized-air",
        ),
        "projection accepted an arbitrary non-receipt object",
    )
    raises(
        ValueError,
        lambda: project_validated_aether_air(
            receipt,
            consumer=" optimized-air",
        ),
        "projection accepted an untrimmed consumer label",
    )
    raises(
        TypeError,
        lambda: project_validated_aether_air(
            receipt,
            consumer="optimized-air",
            provenance=["projection:test"],
        ),
        "projection accepted non-tuple provenance",
    )
    print("Exact F-receipt and explicit projection metadata type boundary: PASS")

    projection_intent = AetherBehaviorIntent(
        "projection.intent",
        "prefer optimized air",
    )
    intent_snapshot = construct_aether_air_snapshot(
        AetherAirRepresentation((projection_intent,)),
    )
    intent_receipt = validate_aether_air_snapshot(intent_snapshot)
    explicit_consumer_projection = project_validated_aether_air(
        intent_receipt,
        consumer="native-backend",
    )
    require(
        explicit_consumer_projection.consumer == "native-backend"
        and explicit_consumer_projection.validation is intent_receipt,
        "projection.intent gained consumer inference or dispatch authority",
    )
    print("Projection-intent metadata remains non-dispatching: PASS")

    raises(
        FrozenInstanceError,
        lambda: setattr(projection, "consumer", "other"),
        "downstream projection became mutable",
    )
    require(
        tuple(field.name for field in fields(AetherAirDownstreamProjection))
        == ("validation", "consumer", "provenance"),
        "downstream projection record shape changed",
    )
    for name in (
        "execute",
        "run",
        "bind",
        "resolve",
        "select",
        "rank",
        "converge",
        "grant",
        "deny",
        "synchronize",
        "normalize",
        "transform",
        "lower",
        "optimize",
        "compile",
        "emit",
        "serialize",
        "load",
        "import_module",
        "mutate",
        "repair",
    ):
        require(
            not hasattr(projection, name),
            "operative behavior leaked into projection record: " + name,
        )
    print("Frozen passive three-field downstream projection boundary: PASS")

    source = PROJECTION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    public_classes = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }
    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    require(
        public_classes == {"AetherAirDownstreamProjection"}
        and public_functions == {"project_validated_aether_air"},
        "P11.9G public production surface expanded",
    )
    forbidden_calls = {
        "validate_aether_air_snapshot",
        "validate_aether_air_transformation",
        "construct_aether_air_snapshot",
        "transform_aether_air_snapshot",
        "normalize_aether_air_snapshot",
        "compile",
        "exec",
        "eval",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    require(
        not (called_names & forbidden_calls),
        "projection revalidated, reconstructed, transformed, or executed canonical state",
    )
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    require(
        not (
            imported_roots
            & {
                "air",
                "authority",
                "effects",
                "runtime",
                "tooling",
                "tools",
                "language_server",
                "semantic_lattice",
            }
        ),
        "projection imported a predecessor, runtime, tooling, or backend-adjacent domain",
    )
    print("No revalidation, reconstruction, lowering, execution, or backend integration: PASS")

    changed = git(
        "diff",
        "--name-only",
        "afp-p11.9f-freeze",
        "--",
        "apexforge/aether_air/model.py",
        "apexforge/aether_air/records.py",
        "apexforge/aether_air/construction.py",
        "apexforge/aether_air/transformation.py",
        "apexforge/aether_air/validation.py",
    )
    require(changed == "", "P11.9G modified frozen P11.9B-F production files")
    print("Frozen P11.9B/P11.9C/P11.9D/P11.9E/P11.9F surfaces preserved: PASS")

    lowered_names = {
        "OptimizedAir",
        "NativeBackend",
        "BackendArtifact",
        "ExecutableArtifact",
    }
    require(
        not (public_classes & lowered_names),
        "P11.9G manufactured a downstream executable/backend model",
    )
    print("Optimized-AIR/Native-Backend ownership remains downstream: PASS")

    forbidden_semantic_names = (
        "choose_branch",
        "select_branch",
        "resolve_condition",
        "evaluate_condition",
        "converge",
        "rank_intents",
        "paradox_elevation",
    )
    require(
        all(name not in source for name in forbidden_semantic_names),
        "P11.10 semantic authority leaked into P11.9G",
    )
    print("P11.10 condition/convergence/Paradox-Elevation boundary preserved: PASS")


if __name__ == "__main__":
    main()
