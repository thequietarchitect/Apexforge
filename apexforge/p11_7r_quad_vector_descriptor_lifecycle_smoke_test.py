"""P11.7R canonical Quad-Vector descriptor lifecycle smoke test."""

from dataclasses import FrozenInstanceError


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def expect(error_type, callback, message):
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main():
    from quad_vector.lifecycle import (
        QuadVectorDescriptorLifecycle,
        run_quad_vector_descriptor_lifecycle,
    )
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
    )
    from quad_vector.execution import QuadVectorExecutionContext
    from quad_vector.model import QuadVectorResourceBudget

    base_candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:BaseVelocity",
        descriptor_reference="quad-vector.json#BaseVelocity",
        order=0,
    )
    adaptive_candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:AdaptiveBalance",
        descriptor_reference="quad-vector.json#AdaptiveBalance",
        order=1,
    )

    base_text = (
        '{"canonical_id":"quad.module:BaseVelocity",'
        '"version":"1.0",'
        '"kind":"function",'
        '"accepted_inputs":["quad.input"],'
        '"produced_outputs":["quad.base"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":[],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.basevelocity"}'
    )
    adaptive_text = (
        '{"canonical_id":"quad.module:AdaptiveBalance",'
        '"version":"1.0",'
        '"kind":"function",'
        '"accepted_inputs":["quad.base"],'
        '"produced_outputs":["quad.result"],'
        '"eligible_vectors":["+X","-X","+Y","-Y"],'
        '"dependencies":["quad.module:BaseVelocity"],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.adaptivebalance"}'
    )

    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )
    context = QuadVectorExecutionContext(
        authorities=("quad.vector.read",),
        inputs=(("quad.input", 3),),
        max_invocations=2,
    )

    calls = []

    def run_base(inputs, dependencies, execution_context):
        calls.append("base")
        return {"quad.base": inputs["quad.input"] + 1}

    def run_adaptive(inputs, dependencies, execution_context):
        calls.append("adaptive")
        return {"quad.result": inputs["quad.base"] * 2}

    implementations = {
        "python:quad_plugins.basevelocity": run_base,
        "python:quad_plugins.adaptivebalance": run_adaptive,
    }

    result = run_quad_vector_descriptor_lifecycle(
        (adaptive_candidate, base_candidate),
        descriptor_texts=(
            ("descriptor:AdaptiveBalance", adaptive_text),
            ("descriptor:BaseVelocity", base_text),
        ),
        budget=budget,
        implementations=implementations,
        context=context,
    )

    require(
        type(result) is QuadVectorDescriptorLifecycle,
        "lifecycle returned the wrong snapshot type",
    )
    require(
        result.inventory.candidates == (base_candidate, adaptive_candidate),
        "lifecycle did not reuse deterministic discovery ordering",
    )
    require(
        tuple(item.candidate for item in result.parsed)
        == (base_candidate, adaptive_candidate),
        "parse stage lost discovered candidate identity/order",
    )
    require(
        tuple(item.parsed for item in result.validated) == result.parsed,
        "validation stage lost parsed descriptor identity/order",
    )
    require(
        tuple(item.validated for item in result.canonicalized) == result.validated,
        "canonicalization stage lost validated descriptor identity/order",
    )
    require(
        result.registration.canonical_descriptors == result.canonicalized,
        "registration stage lost canonical descriptor identity/order",
    )
    require(
        result.binding.registration is result.registration,
        "binding stage lost registration provenance identity",
    )
    require(
        result.execution.binding is result.binding,
        "execution stage lost binding provenance identity",
    )
    require(
        tuple(record.spec.canonical_id for record in result.execution.records)
        == ("quad.module:BaseVelocity", "quad.module:AdaptiveBalance"),
        "dependency-order execution changed across lifecycle orchestration",
    )
    require(
        result.execution.records[0].outputs == (("quad.base", 4),)
        and result.execution.records[1].outputs == (("quad.result", 8),),
        "lifecycle changed declared execution outputs",
    )
    require(tuple(calls) == ("base", "adaptive"), "lifecycle invocation order changed")

    repeated = run_quad_vector_descriptor_lifecycle(
        (adaptive_candidate, base_candidate),
        descriptor_texts=(
            ("descriptor:AdaptiveBalance", adaptive_text),
            ("descriptor:BaseVelocity", base_text),
        ),
        budget=budget,
        implementations=implementations,
        context=context,
    )
    require(
        repeated.execution.records == result.execution.records,
        "repeated lifecycle orchestration is not deterministic",
    )

    expect(
        ValueError,
        lambda: run_quad_vector_descriptor_lifecycle(
            (base_candidate, adaptive_candidate),
            descriptor_texts=(("descriptor:BaseVelocity", base_text),),
            budget=budget,
            implementations=implementations,
            context=context,
        ),
        "missing descriptor text was accepted",
    )
    expect(
        ValueError,
        lambda: run_quad_vector_descriptor_lifecycle(
            (base_candidate,),
            descriptor_texts=(
                ("descriptor:BaseVelocity", base_text),
                ("descriptor:BaseVelocity", base_text),
            ),
            budget=budget,
            implementations=implementations,
            context=context,
        ),
        "duplicate descriptor text identity was accepted",
    )
    expect(
        TypeError,
        lambda: run_quad_vector_descriptor_lifecycle(
            [base_candidate],
            descriptor_texts=(("descriptor:BaseVelocity", base_text),),
            budget=budget,
            implementations=implementations,
            context=context,
        ),
        "non-tuple candidate collection was accepted",
    )
    expect(
        FrozenInstanceError,
        lambda: setattr(result, "inventory", result.inventory),
        "lifecycle snapshot became mutable",
    )

    for item in (
        result,
        result.inventory,
        result.registration,
        result.binding,
        result.execution,
    ):
        require(
            not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7R lifecycle leaked loader/import/Codex privilege",
        )

    print("Deterministic Discover-to-Execute lifecycle composition: PASS")
    print("Cross-stage descriptor provenance/object-identity preservation: PASS")
    print("Existing parse/validate/canonicalize/register/bind/execute contract reuse: PASS")
    print("Dependency-order execution and declared-output preservation: PASS")
    print("Caller-supplied descriptor-text exact coverage validation: PASS")
    print("Deterministic repeated canonical descriptor lifecycle: PASS")
    print("Immutable lifecycle snapshot boundary: PASS")
    print("P11.7R loader/import/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
