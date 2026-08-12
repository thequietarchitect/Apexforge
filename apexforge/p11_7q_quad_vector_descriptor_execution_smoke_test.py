"""P11.7Q canonical descriptor execution smoke."""

from dataclasses import FrozenInstanceError


def require(value, message):
    if not value:
        raise AssertionError(message)


def expect(error_type, callback):
    try:
        callback()
    except error_type:
        return
    raise AssertionError("expected " + error_type.__name__)


def main():
    from quad_vector.descriptor_execution import (
        QuadVectorDescriptorExecution,
        execute_quad_vector_descriptors,
    )
    from quad_vector.binding import bind_quad_vector_descriptors
    from quad_vector.canonicalization import canonicalize_quad_vector_descriptor
    from quad_vector.discovery import QuadVectorDiscoveryCandidate, QuadVectorDiscoverySource
    from quad_vector.execution import QuadVectorExecutionContext, QuadVectorExecutionRecord
    from quad_vector.model import QuadVectorResourceBudget
    from quad_vector.parsing import parse_quad_vector_descriptor
    from quad_vector.registration import register_quad_vector_descriptors
    from quad_vector.validation import validate_quad_vector_descriptor

    def make(name, order, accepted, produced, dependencies=()):
        canonical_id = "quad.module:" + name
        candidate = QuadVectorDiscoveryCandidate(
            source=QuadVectorDiscoverySource.MANIFEST,
            source_identity="source:manifest:quad-vector",
            descriptor_identity="descriptor:" + name,
            descriptor_reference="quad-vector.json#" + name,
            order=order,
        )
        arr = lambda values: ",".join('"' + value + '"' for value in values)
        text = (
            '{"canonical_id":"' + canonical_id + '","version":"1.0","kind":"function",'
            '"accepted_inputs":[' + arr(accepted) + '],"produced_outputs":[' + arr(produced) + '],'
            '"eligible_vectors":["+X","-X","+Y","-Y"],"dependencies":[' + arr(dependencies) + '],'
            '"determinism_contract":"pure-deterministic","authority_requirements":["quad.vector.read"],'
            '"resource_budget":{"max_modules":8,"max_contributions":32,"max_iterations":64},'
            '"implementation_reference":"python:quad_plugins.' + name.lower() + '"}'
        )
        return canonicalize_quad_vector_descriptor(
            validate_quad_vector_descriptor(parse_quad_vector_descriptor(candidate, text))
        )

    base = make("BaseVelocity", 0, ("quad.input",), ("quad.base",))
    adaptive = make(
        "AdaptiveBalance",
        1,
        ("quad.base",),
        ("quad.result",),
        ("quad.module:BaseVelocity",),
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=64,
        max_iterations=128,
    )
    registration = register_quad_vector_descriptors((adaptive, base), budget=budget)
    binding = bind_quad_vector_descriptors(registration)
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
    result = execute_quad_vector_descriptors(
        binding,
        implementations=implementations,
        context=context,
    )

    require(type(result) is QuadVectorDescriptorExecution, "wrong execution snapshot type")
    require(result.binding is binding, "binding provenance changed")
    require(
        type(result.records) is tuple
        and all(type(item) is QuadVectorExecutionRecord for item in result.records),
        "execution record boundary changed",
    )
    require(
        tuple(item.spec.canonical_id for item in result.records)
        == ("quad.module:BaseVelocity", "quad.module:AdaptiveBalance"),
        "dependency execution order changed",
    )
    require(
        result.records[0].spec is base.spec and result.records[1].spec is adaptive.spec,
        "canonical spec identity changed",
    )
    require(
        result.records[0].outputs == (("quad.base", 4),)
        and result.records[1].outputs == (("quad.result", 8),),
        "declared outputs changed",
    )
    require(
        tuple(calls) == ("base", "adaptive"),
        "implementation invocation order changed",
    )

    repeated = execute_quad_vector_descriptors(
        binding,
        implementations=implementations,
        context=context,
    )
    require(repeated.records == result.records and repeated.binding is binding, "execution not deterministic")

    expect(
        TypeError,
        lambda: execute_quad_vector_descriptors(
            object(),
            implementations=implementations,
            context=context,
        ),
    )
    restricted = QuadVectorExecutionContext(
        authorities=(),
        inputs=(("quad.input", 3),),
        max_invocations=2,
    )
    expect(
        PermissionError,
        lambda: execute_quad_vector_descriptors(
            binding,
            implementations=implementations,
            context=restricted,
        ),
    )
    expect(FrozenInstanceError, lambda: setattr(result, "binding", binding))

    for item in (result, result.binding) + result.records:
        require(
            not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex"),
            "loader/import/Codex privilege leaked",
        )

    print("Descriptor-binding provenance preservation through execution: PASS")
    print("Existing deterministic P11.7F execution-engine reuse: PASS")
    print("Dependency-order canonical spec identity preservation: PASS")
    print("Declared-output execution semantics preservation: PASS")
    print("Deterministic repeated descriptor execution: PASS")
    print("Existing execution authority boundary reuse: PASS")
    print("Immutable descriptor-execution snapshot boundary: PASS")
    print("P11.7Q loader/import/Codex privilege exclusion: PASS")


if __name__ == "__main__":
    main()
