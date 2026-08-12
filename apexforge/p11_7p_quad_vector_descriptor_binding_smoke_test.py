"""P11.7P canonical Quad-Vector descriptor binding red-gate smoke test."""

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
    from quad_vector.registration import (
        QuadVectorDescriptorRegistration,
        register_quad_vector_descriptors,
    )
    from quad_vector.registry import QuadVectorModuleBinding
    from quad_vector.validation import validate_quad_vector_descriptor
    from quad_vector.binding import (
        QuadVectorDescriptorBinding,
        bind_quad_vector_descriptors,
    )

    def canonicalize(identity, reference, order, canonical_id, dependencies=()):
        candidate = QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.MANIFEST,
            source_identity="source:manifest:quad-vector",
            descriptor_identity=identity,
            descriptor_reference=reference,
            order=order,
        )
        dependency_json = ",".join('"' + item + '"' for item in dependencies)
        text = (
            '{"canonical_id":"' + canonical_id + '",'
            '"version":"1.0",'
            '"kind":"function",'
            '"accepted_inputs":["quad.input"],'
            '"produced_outputs":["quad.output"],'
            '"eligible_vectors":["+X","-X","+Y","-Y"],'
            '"dependencies":[' + dependency_json + '],'
            '"determinism_contract":"pure-deterministic",'
            '"authority_requirements":["quad.vector.read"],'
            '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
            '"implementation_reference":"python:quad_plugins.' + identity.split(":")[-1].lower() + '"}'
        )
        parsed = parse_quad_vector_descriptor(candidate, text)
        validated = validate_quad_vector_descriptor(parsed)
        return canonicalize_quad_vector_descriptor(validated)

    base = canonicalize(
        "descriptor:BaseVelocity",
        "quad-vector.json#BaseVelocity",
        0,
        "quad.module:BaseVelocity",
    )
    adaptive = canonicalize(
        "descriptor:AdaptiveBalance",
        "quad-vector.json#AdaptiveBalance",
        1,
        "quad.module:AdaptiveBalance",
        ("quad.module:BaseVelocity",),
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )
    registration = register_quad_vector_descriptors(
        (adaptive, base),
        budget=budget,
    )
    bound = bind_quad_vector_descriptors(registration)

    require(
        type(bound) is QuadVectorDescriptorBinding,
        "binding returned the wrong snapshot type",
    )
    require(
        bound.registration is registration,
        "binding changed descriptor-registration provenance identity",
    )
    require(
        type(bound.bindings) is tuple
        and all(type(item) is QuadVectorModuleBinding for item in bound.bindings),
        "binding did not expose exact immutable QuadVectorModuleBinding values",
    )
    require(
        tuple(item.spec.canonical_id for item in bound.bindings)
        == ("quad.module:BaseVelocity", "quad.module:AdaptiveBalance"),
        "deterministic dependency binding order was not reused",
    )
    require(
        bound.bindings[0].spec is base.spec
        and bound.bindings[1].spec is adaptive.spec,
        "canonical spec identity was not preserved through binding",
    )
    repeated = bind_quad_vector_descriptors(registration)
    require(
        tuple(item.spec.canonical_id for item in repeated.bindings)
        == tuple(item.spec.canonical_id for item in bound.bindings),
        "repeated descriptor binding is not deterministic",
    )

    left = canonicalize(
        "descriptor:CycleLeft",
        "quad-vector.json#CycleLeft",
        0,
        "quad.module:CycleLeft",
        ("quad.module:CycleRight",),
    )
    right = canonicalize(
        "descriptor:CycleRight",
        "quad-vector.json#CycleRight",
        1,
        "quad.module:CycleRight",
        ("quad.module:CycleLeft",),
    )
    cycle_registration = register_quad_vector_descriptors(
        (left, right),
        budget=budget,
    )
    expect_error(
        ValueError,
        lambda: bind_quad_vector_descriptors(cycle_registration),
        "dependency cycle was not rejected through registry binder reuse",
    )
    expect_error(
        TypeError,
        lambda: bind_quad_vector_descriptors(object()),
        "non-registration input was accepted",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(bound, "registration", registration),
        "descriptor binding snapshot became mutable",
    )

    for item in (bound, bound.registration, bound.bindings[0], bound.bindings[1]):
        require(
            not hasattr(item, "execute")
            and not hasattr(item, "run")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7P binding snapshot gained execution/loader/Codex authority",
        )

    print("Registered-descriptor provenance preservation through binding: PASS")
    print("Existing deterministic registry binder reuse: PASS")
    print("Dependency-order canonical spec identity preservation: PASS")
    print("Deterministic repeated descriptor binding: PASS")
    print("Registry dependency-cycle rejection reuse: PASS")
    print("Exact descriptor-registration binding boundary: PASS")
    print("Immutable descriptor-binding snapshot boundary: PASS")
    print("P11.7P execution/loader/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
