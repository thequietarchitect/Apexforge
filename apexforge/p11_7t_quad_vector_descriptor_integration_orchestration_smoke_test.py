"""P11.7T canonical descriptor integration orchestration smoke test."""

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
    from quad_vector.descriptor_integration import (
        QuadVectorDescriptorIntegrationOrchestration,
        orchestrate_quad_vector_descriptor_integration,
    )
    from quad_vector.binding import bind_quad_vector_descriptors
    from quad_vector.canonicalization import canonicalize_quad_vector_descriptor
    from quad_vector.discovery import (
        QuadVectorDiscoveryCandidate,
        QuadVectorDiscoverySource,
    )
    from quad_vector.integration import (
        QuadVectorIntegrationInput,
        QuadVectorIntegrationRequest,
        QuadVectorIntegrationSource,
        adapt_quad_vector_integration_request,
    )
    from quad_vector.model import (
        QuadVectorContribution,
        QuadVectorLane,
        QuadVectorResourceBudget,
    )
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.registration import register_quad_vector_descriptors
    from quad_vector.validation import validate_quad_vector_descriptor

    candidate = QuadVectorDiscoveryCandidate(
        source=QuadVectorDiscoverySource.EXPLICIT,
        source_identity="source:explicit:integration",
        descriptor_identity="descriptor:IntegrationVector",
        descriptor_reference="inline:IntegrationVector",
        order=0,
    )
    descriptor_text = (
        '{"canonical_id":"quad.module:IntegrationVector",'
        '"version":"1.0",'
        '"kind":"vector_operator",'
        '"accepted_inputs":["quad.input"],'
        '"produced_outputs":["quad.vector"],'
        '"eligible_vectors":["+X"],'
        '"dependencies":[],'
        '"determinism_contract":"pure-deterministic",'
        '"authority_requirements":["quad.vector.read"],'
        '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
        '"implementation_reference":"python:quad_plugins.integrationvector"}'
    )

    parsed = parse_quad_vector_descriptor(candidate, descriptor_text)
    validated = validate_quad_vector_descriptor(parsed)
    canonical = canonicalize_quad_vector_descriptor(validated)
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )
    registration = register_quad_vector_descriptors((canonical,), budget=budget)
    binding = bind_quad_vector_descriptors(registration)

    request = QuadVectorIntegrationRequest(
        source=QuadVectorIntegrationSource.RUNTIME,
        source_identity="runtime:integration-smoke",
        facts=(("quad.input", 5),),
        authorities=("quad.vector.read",),
        max_invocations=1,
    )
    integration_input = adapt_quad_vector_integration_request(request)
    require(
        type(integration_input) is QuadVectorIntegrationInput,
        "integration adapter returned the wrong input type",
    )

    calls = []

    def run_vector(inputs, dependencies, execution_context):
        calls.append("vector")
        return {
            "quad.vector": (
                QuadVectorContribution(
                    lane=QuadVectorLane.POSITIVE_X,
                    magnitude=inputs["quad.input"] + 2,
                    order=0,
                    provenance=("emitted:integration-vector",),
                ),
            )
        }

    implementations = {
        "python:quad_plugins.integrationvector": run_vector,
    }

    result = orchestrate_quad_vector_descriptor_integration(
        binding,
        integration_input=integration_input,
        implementations=implementations,
        budget=budget,
    )

    require(
        type(result) is QuadVectorDescriptorIntegrationOrchestration,
        "descriptor integration orchestration returned the wrong snapshot type",
    )
    require(
        result.integration_input is integration_input,
        "integration-input provenance identity was not preserved",
    )
    require(
        result.descriptor_orchestration.binding is binding,
        "descriptor-binding provenance identity was not preserved",
    )
    require(
        tuple(calls) == ("vector",),
        "descriptor integration orchestration executed the provider more than once",
    )
    require(
        (result.descriptor_orchestration.orchestration.resultant.x,
         result.descriptor_orchestration.orchestration.resultant.y) == (7, 0),
        "descriptor integration orchestration changed canonical resultant semantics",
    )
    require(
        result.response.resultant
        is result.descriptor_orchestration.orchestration.resultant,
        "integration response did not preserve resultant object identity",
    )
    require(
        result.response.source is integration_input.source
        and result.response.source_identity == integration_input.source_identity,
        "integration source provenance was not preserved",
    )
    require(
        result.response.payload == (("x", 7), ("y", 0)),
        "canonical integration response payload changed",
    )
    require(
        result.response.provenance
        == result.descriptor_orchestration.orchestration.resultant.provenance,
        "canonical integration response provenance changed",
    )

    first = result
    calls.clear()
    repeated = orchestrate_quad_vector_descriptor_integration(
        binding,
        integration_input=integration_input,
        implementations=implementations,
        budget=budget,
    )
    require(
        tuple(calls) == ("vector",),
        "repeated descriptor integration orchestration changed single-pass invocation semantics",
     )
    require(
        repeated.descriptor_orchestration.orchestration
        == first.descriptor_orchestration.orchestration
        and repeated.response == first.response,
        "repeated descriptor integration orchestration is not deterministic",
    )

    expect(
        TypeError,
        lambda: orchestrate_quad_vector_descriptor_integration(
            binding,
            integration_input=request,
            implementations=implementations,
            budget=budget,
        ),
        "non-integration-input state crossed the P11.7T adapter boundary",
    )
    expect(
        FrozenInstanceError,
        lambda: setattr(result, "integration_input", integration_input),
        "descriptor integration orchestration snapshot became mutable",
    )

    for item in (
        result,
        result.descriptor_orchestration,
        result.descriptor_orchestration.orchestration,
        result.response,
    ):
        require(
            not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "P11.7T integration orchestration leaked loader/import/Codex privilege",
        )

    print("Single-pass descriptor-binding-to-integration-response orchestration: PASS")
    print("Frozen P11.7S descriptor engine-orchestration reuse: PASS")
    print("Frozen P11.7H integration adapter reuse: PASS")
    print("Integration-input/binding/resultant provenance identity preservation: PASS")
    print("Canonical resultant-to-integration-response semantics preservation: PASS")
    print("Deterministic repeated descriptor integration orchestration: PASS")
    print("Immutable descriptor-integration snapshot boundary: PASS")
    print("P11.7T loader/import/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
