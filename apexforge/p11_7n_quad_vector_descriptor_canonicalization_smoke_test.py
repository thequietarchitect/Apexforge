"""P11.7N canonical Quad-Vector descriptor canonicalization red-gate smoke test."""

from dataclasses import FrozenInstanceError


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect_error(error_type, callback, message):
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main():
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
    )
    from quad_vector.module import QuadVectorModuleKind, QuadVectorModuleSpec
    from quad_vector.model import QuadVectorLane
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.validation import validate_quad_vector_descriptor
    from quad_vector.canonicalization import (
        QuadVectorCanonicalDescriptor,
        canonicalize_quad_vector_descriptor,
    )

    candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:AdaptiveBalance",
        descriptor_reference="quad-vector.json#AdaptiveBalance",
        order=0,
    )
    text = (
        '{"canonical_id":"quad.module:AdaptiveBalance",'
        '"version":"1.0",'
        '"kind":"weighting_rule",'
        '"accepted_inputs":["quad.velocity","quad.eligibility"],'
        '"produced_outputs":["quad.weight"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":["quad.module:BaseVelocity"],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.adaptive_balance",'
        '"metadata":{"author":"architect"}}'
    )
    parsed = parse_quad_vector_descriptor(candidate, text)
    validated = validate_quad_vector_descriptor(parsed)
    canonicalized = canonicalize_quad_vector_descriptor(validated)

    require(
        type(canonicalized) is QuadVectorCanonicalDescriptor,
        "canonicalizer returned the wrong snapshot type",
    )
    require(
        canonicalized.validated is validated,
        "canonicalizer changed validated-descriptor identity",
    )
    require(
        type(canonicalized.spec) is QuadVectorModuleSpec,
        "canonicalizer did not produce an exact QuadVectorModuleSpec",
    )
    require(
        canonicalized.spec.canonical_id == validated.canonical_id
        and canonicalized.spec.version == validated.version
        and canonicalized.spec.kind is QuadVectorModuleKind.WEIGHTING_RULE,
        "canonical identity/version/kind translation changed semantics",
    )
    require(
        canonicalized.spec.accepted_inputs == validated.accepted_inputs
        and canonicalized.spec.produced_outputs == validated.produced_outputs
        and canonicalized.spec.dependencies == validated.dependencies
        and canonicalized.spec.authority_requirements == validated.authority_requirements,
        "canonical tuple fields changed during canonicalization",
    )
    require(
        canonicalized.spec.eligible_vectors
        == (
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        "canonical vector eligibility changed during canonicalization",
    )
    require(
        canonicalized.spec.determinism_contract == validated.determinism_contract
        and canonicalized.spec.implementation_reference == validated.implementation_reference,
        "canonical deterministic/implementation contract changed",
    )
    require(
        canonicalized.spec.resource_budget is validated.resource_budget,
        "canonicalization replaced the validated immutable resource budget",
    )

    repeated = canonicalize_quad_vector_descriptor(validated)
    require(
        repeated.spec == canonicalized.spec,
        "canonicalization is not deterministic",
    )
    require(
        repeated.validated is validated,
        "repeat canonicalization changed validated provenance identity",
    )

    expect_error(
        TypeError,
        lambda: canonicalize_quad_vector_descriptor(object()),
        "non-validated descriptor was accepted",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(canonicalized, "spec", canonicalized.spec),
        "canonical descriptor snapshot became mutable",
    )

    for item in (canonicalized, canonicalized.spec, canonicalized.validated):
        require(
            not hasattr(item, "register")
            and not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7N canonical snapshot gained downstream/runtime/loader/Codex authority",
        )

    print("Validated-descriptor provenance preservation through canonicalization: PASS")
    print("Exact immutable QuadVectorModuleSpec canonicalization: PASS")
    print("Canonical identity/version/kind field preservation: PASS")
    print("Canonical tuple/vector/resource field preservation: PASS")
    print("Deterministic repeated canonicalization: PASS")
    print("Exact validated-descriptor canonicalization boundary: PASS")
    print("Immutable canonical-descriptor snapshot boundary: PASS")
    print("P11.7N register/bind/execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
