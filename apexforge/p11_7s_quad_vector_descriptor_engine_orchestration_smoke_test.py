"""P11.7S Canonical Quad-Vector descriptor engine orchestration smoke test."""

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
    from quad_vector.descriptor_orchestration import (
        QuadVectorDescriptorOrchestration,
        orchestrate_quad_vector_descriptor_engine,
    )
    from quad_vector.binding import bind_quad_vector_descriptors
    from quad_vector.canonicalization import canonicalize_quad_vector_descriptor
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
        discover_quad_vector_modules,
    )
    from quad_vector.execution import QuadVectorExecutionContext
    from quad_vector.model import (
        QuadVectorContribution,
        QuadVectorInput,
        QuadVectorLane,
        QuadVectorResourceBudget,
    )
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.registration import register_quad_vector_descriptors
    from quad_vector.validation import validate_quad_vector_descriptor

    base_candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:BasePush",
        descriptor_reference="quad-vector.json#BasePush",
        order=0,
    )
    adaptive_candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.MANIFEST,
        source_identity="source:manifest:quad-vector",
        descriptor_identity="descriptor:AdaptivePush",
        descriptor_reference="quad-vector.json#AdaptivePush",
        order=1,
    )

    base_text = (
        '{"canonical_id":"quad.module:BasePush",'
        '"version":"1.0",'
        '"kind":"vector_operator",'
        '"accepted_inputs":["quad.input"],'
        '"produced_outputs":["quad.base"],'
        '"eligible_vectors":["+X"],'
        '"dependencies":[],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.basepush"}'
    )
    adaptive_text = (
        '{"canonical_id":"quad.module:AdaptivePush",'
        '"version":"1.0",'
        '"kind":"vector_operator",'
        '"accepted_inputs":["quad.base"],'
        '"produced_outputs":["quad.result"],'
        '"eligible_vectors":["+Y"],'
        '"dependencies":["quad.module:BasePush"],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.adaptivepush"}'
    )

    inventory = discover_quad_vector_modules((adaptive_candidate, base_candidate))
    parsed = tuple(
        parse_quad_vector_descriptor(
            candidate,
            {
                "descriptor:BasePush": base_text,
                "descriptor:AdaptivePush": adaptive_text,
            }[candidate.descriptor_identity],
        )
        for candidate in inventory.candidates
    )
    validated = tuple(validate_quad_vector_descriptor(item) for item in parsed)
    canonicalized = tuple(
        canonicalize_quad_vector_descriptor(item) for item in validated
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )
    registration = register_quad_vector_descriptors(
        canonicalized,
        budget=budget,
    )
    binding = bind_quad_vector_descriptors(registration)

    context = QuadVectorExecutionContext(
        authorities=("quad.vector.read",),
        inputs=(("quad.input", 2),),
        max_invocations=2,
    )
    stimulus = QuadVectorInput(
        identity="stimulus:descriptor-engine",
        facts=(("quad.input", 2),),
    )

    calls = []

    def run_base(inputs, dependencies, execution_context):
        calls.append("base")
        return {
            "quad.base": (
                QuadVectorContribution(
                    lane=QuadVectorLane.POSITIVE_X,
                    magnitude=3,
                    order=0,
                    provenance=("emitted:base",),
                ),
            )
        }

    def run_adaptive(inputs, dependencies, execution_context):
        calls.append("adaptive")
        return {
            "quad.result": (
                QuadVectorContribution(
                    lane=QuadVectorLane.POSITIVE_Y,
                    magnitude=inputs["quad.base"][0].magnitude + 1,
                    order=1,
                    provenance=("emitted:adaptive",),
                ),
            )
        }

    implementations = {
        "python:quad_plugins.basepush": run_base,
        "python:quad_plugins.adaptivepush": run_adaptive,
    }

    result = orchestrate_quad_vector_descriptor_engine(
        binding,
        implementations=implementations,
        context=context,
        stimulus=stimulus,
        budget=budget,
    )

    require(
        type(result) is QuadVectorDescriptorOrchestration,
        "descriptor engine orchestration returned the wrong snapshot type",
    )
    require(
        result.binding is binding,
        "descriptor binding provenance identity was not preserved",
    )
    require(
        tuple(record.spec for record in result.orchestration.execution_records)
        == tuple(item.spec for item in binding.bindings),
        "frozen descriptor binding/spec identity order was not preserved",
    )
    require(
        tuple(calls) == ("base", "adaptive"),
        "descriptor engine orchestration executed modules more than once or out of order",
    )
    require(
        (result.orchestration.resultant.x, result.orchestration.resultant.y) == (3, 4),
        "descriptor engine orchestration changed canonical resultant semantics",
    )
    require(
        len(result.orchestration.execution_records) == 2,
        "descriptor engine orchestration duplicated frozen execution records",
    )

    first_records = result.orchestration.execution_records
    calls.clear()
    repeated = orchestrate_quad_vector_descriptor_engine(
        binding,
        implementations=implementations,
        context=context,
        stimulus=stimulus,
        budget=budget,
    )
    require(
        tuple(calls) == ("base", "adaptive"),
        "repeated descriptor engine orchestration changed single-pass invocation order",
    )
    require(
        repeated.orchestration == result.orchestration,
        "repeated descriptor engine orchestration is not deterministic",
    )
    require(
        repeated.orchestration.execution_records == first_records,
        "repeated descriptor engine execution records changed",
    )

    expect(
        ValueError,
        lambda: orchestrate_quad_vector_descriptor_engine(
            binding,
            implementations=implementations,
            context=QuadVectorExecutionContext(
                authorities=("quad.vector.read",),
                inputs=(("quad.input", 99),),
                max_invocations=2,
            ),
            stimulus=stimulus,
            budget=budget,
        ),
        "stimulus/context mismatch crossed the frozen orchestration boundary",
    )
    expect(
        TypeError,
        lambda: orchestrate_quad_vector_descriptor_engine(
            binding.registration,
            implementations=implementations,
            context=context,
            stimulus=stimulus,
            budget=budget,
        ),
        "non-binding descriptor state was accepted by the orchestration adapter",
    )
    expect(
        FrozenInstanceError,
        lambda: setattr(result, "binding", binding),
        "descriptor orchestration snapshot became mutable",
    )

    for item in (result, result.orchestration):
        require(
            not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7S descriptor orchestration leaked loader/import/Codex privilege",
        )

    print("Single-pass descriptor-binding-to-resultant orchestration: PASS")
    print("Frozen P11.7G engine-orchestration reuse: PASS")
    print("Descriptor binding/spec provenance identity preservation: PASS")
    print("Deterministic dependency-order execution preservation: PASS")
    print("Canonical resultant semantics preservation: PASS")
    print("Stimulus/context coherence boundary reuse: PASS")
    print("Immutable descriptor-orchestration snapshot boundary: PASS")
    print("P11.7S loader/import/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
