"""P11.7O canonical Quad-Vector descriptor registration red-gate smoke test."""

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
    from quad_vector.canonicalization import canonicalize_quad_vector_descriptor
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
    )
    from quad_vector.model import QuadVectorResourceBudget
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.registry import QuadVectorModuleRegistry
    from quad_vector.validation import validate_quad_vector_descriptor
    from quad_vector.registration import (
        QuadVectorDescriptorRegistration,
        register_quad_vector_descriptors,
    )

    def canonicalize(identity, reference, order, body):
        candidate = QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.MANIFEST,
            source_identity="source:manifest:quad-vector",
            descriptor_identity=identity,
            descriptor_reference=reference,
            order=order,
        )
        parsed = parse_quad_vector_descriptor(candidate, body)
        validated = validate_quad_vector_descriptor(parsed)
        return canonicalize_quad_vector_descriptor(validated)

    base_text = (
        '{"canonical_id":"quad.module:BaseVelocity",'
        '"version":"1.0",'
        '"kind":"function",'
        '"accepted_inputs":["quad.velocity"],'
        '"produced_outputs":["quad.base_velocity"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":[],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.base_velocity"}'
    )
    adaptive_text = (
        '{"canonical_id":"quad.module:AdaptiveBalance",'
        '"version":"1.0",'
        '"kind":"weighting_rule",'
        '"accepted_inputs":["quad.base_velocity"],'
        '"produced_outputs":["quad.weight"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":["quad.module:BaseVelocity"],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.adaptive_balance"}'
    )

    base = canonicalize(
        "descriptor:BaseVelocity",
        "quad-vector.json#BaseVelocity",
        0,
        base_text,
    )
    adaptive = canonicalize(
        "descriptor:AdaptiveBalance",
        "quad-vector.json#AdaptiveBalance",
        1,
        adaptive_text,
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )

    registration = register_quad_vector_descriptors((base, adaptive), budget=budget)

    require(
        type(registration) is QuadVectorDescriptorRegistration,
        "registration returned the wrong snapshot type",
    )
    require(
        registration.canonical_descriptors == (base, adaptive),
        "canonical descriptor order changed during registration",
    )
    require(
        registration.canonical_descriptors[0] is base
        and registration.canonical_descriptors[1] is adaptive,
        "canonical descriptor object identity was not preserved",
    )
    require(
        type(registration.registry) is QuadVectorModuleRegistry,
        "registration did not reuse the canonical module registry",
    )
    require(
        registration.registry.specs == (base.spec, adaptive.spec),
        "registry spec order changed during descriptor registration",
    )
    require(
        registration.registry.specs[0] is base.spec
        and registration.registry.specs[1] is adaptive.spec,
        "registry did not preserve canonical spec identity",
    )
    require(
        registration.registry.budget is budget,
        "registry did not preserve the supplied resource budget",
    )

    repeated = register_quad_vector_descriptors((base, adaptive), budget=budget)
    require(
        repeated.registry.specs == registration.registry.specs,
        "repeated descriptor registration is not deterministic",
    )

    duplicate = canonicalize(
        "descriptor:BaseVelocityDuplicate",
        "quad-vector.json#BaseVelocityDuplicate",
        2,
        base_text.replace(
            "\"implementation_reference\":\"python:quad_plugins.base_velocity\"",
            "\"implementation_reference\":\"python:quad_plugins.base_velocity_duplicate\"",
        ),
    )
    expect_error(
        ValueError,
        lambda: register_quad_vector_descriptors((base, duplicate), budget=budget),
        "canonical identity collision was not rejected through registry reuse",
    )

    unresolved = canonicalize(
        "descriptor:Unresolved",
        "quad-vector.json#Unresolved",
        2,
        adaptive_text.replace(
            "\"canonical_id\":\"quad.module:AdaptiveBalance\"",
            "\"canonical_id\":\"quad.module:Unresolved\"",
        ).replace(
            "\"dependencies\":[\"quad.module:BaseVelocity\"]",
            "\"dependencies\":[\"quad.module:Missing\"]",
        ),
    )
    expect_error(
        ValueError,
        lambda: register_quad_vector_descriptors((base, unresolved), budget=budget),
        "unresolved dependency was not rejected through registry reuse",
    )

    small_budget = QuadVectorResourceBudget(
        max_modules=1,
        max_contributions=64,
        max_iterations=128,
    )
    expect_error(
        ValueError,
        lambda: register_quad_vector_descriptors((base, adaptive), budget=small_budget),
        "registry module-budget enforcement was bypassed",
    )
    expect_error(
        TypeError,
        lambda: register_quad_vector_descriptors([base, adaptive], budget=budget),
        "non-tuple canonical descriptor collection was accepted",
    )
    expect_error(
        TypeError,
        lambda: register_quad_vector_descriptors((base, object()), budget=budget),
        "non-canonical descriptor was accepted",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(registration, "registry", registration.registry),
        "descriptor registration snapshot became mutable",
    )

    for item in (
        registration,
        registration.registry,
        registration.canonical_descriptors[0],
        registration.canonical_descriptors[1],
    ):
        require(
            not hasattr(item, "bind")
            and not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7O registration snapshot gained binding/execution/loader/Codex authority",
        )

    print("Canonical descriptor authored-order preservation through registration: PASS")
    print("Canonical descriptor provenance/object-identity preservation: PASS")
    print("Existing QuadVectorModuleRegistry reuse: PASS")
    print("Canonical registry spec identity/order preservation: PASS")
    print("Registry collision/dependency validation reuse: PASS")
    print("Registry module-budget enforcement through descriptor registration: PASS")
    print("Exact immutable canonical-descriptor registration boundary: PASS")
    print("P11.7O binding/execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
