"""P11.7H canonical Quad-Vector integration-adapter red-gate smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def expect_error(error_type, callback, message: str) -> None:
    try:
        callback()
    except error_type:
        return
    raise AssertionError(message)


def main() -> None:
    from quad_vector.execution import QuadVectorExecutionContext
    from quad_vector.model import QuadVectorInput, ResultantVector
    from quad_vector.integration import (
        QuadVectorIntegrationInput,
        QuadVectorIntegrationRequest,
        QuadVectorIntegrationResponse,
        QuadVectorIntegrationSource,
        adapt_quad_vector_integration_request,
        adapt_quad_vector_integration_result,
    )

    require(
        tuple(item.value for item in QuadVectorIntegrationSource)
        == ("air", "runtime", "narrative", "tooling"),
        "canonical integration source order changed",
    )

    sources = (
        QuadVectorIntegrationSource.AIR,
        QuadVectorIntegrationSource.RUNTIME,
        QuadVectorIntegrationSource.NARRATIVE,
        QuadVectorIntegrationSource.TOOLING,
    )
    adapted_inputs = []

    for index, source in enumerate(sources):
        request = QuadVectorIntegrationRequest(
            source=source,
            source_identity=f"source:{source.value}:{index}",
            facts=(("quad.input", index + 1), ("quad.mode", source.value)),
            authorities=("quad.vector.read",),
            max_invocations=4,
        )
        adapted = adapt_quad_vector_integration_request(request)
        adapted_inputs.append(adapted)

        require(
            type(adapted) is QuadVectorIntegrationInput,
            "integration request adapter returned a non-canonical input snapshot",
        )
        require(adapted.source is source, "integration source identity changed")
        require(
            adapted.source_identity == request.source_identity,
            "integration source identity text changed",
        )
        require(
            type(adapted.stimulus) is QuadVectorInput,
            "integration adapter did not produce a canonical QuadVectorInput",
        )
        require(
            adapted.stimulus.identity == request.source_identity,
            "integration adapter changed canonical stimulus identity",
        )
        require(
            adapted.stimulus.facts == request.facts,
            "integration adapter changed source facts",
        )
        require(
            type(adapted.context) is QuadVectorExecutionContext,
            "integration adapter did not produce a canonical execution context",
        )
        require(
            adapted.context.inputs == request.facts,
            "integration adapter changed execution-context inputs",
        )
        require(
            adapted.context.authorities == request.authorities,
            "integration adapter changed declared authorities",
        )
        require(
            adapted.context.max_invocations == request.max_invocations,
            "integration adapter changed invocation budget",
        )

    expect_error(
        ValueError,
        lambda: QuadVectorIntegrationRequest(
            source=QuadVectorIntegrationSource.AIR,
            source_identity="source:duplicate-facts",
            facts=(("quad.input", 1), ("quad.input", 2)),
            authorities=("quad.vector.read",),
            max_invocations=1,
        ),
        "integration request accepted duplicate fact keys",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorIntegrationRequest(
            source=QuadVectorIntegrationSource.RUNTIME,
            source_identity="source:duplicate-authority",
            facts=(("quad.input", 1),),
            authorities=("quad.vector.read", "quad.vector.read"),
            max_invocations=1,
        ),
        "integration request accepted duplicate authorities",
    )

    selected = adapted_inputs[2]
    resultant = ResultantVector(
        x=10,
        y=-4,
        contributions=(),
        provenance=(
            "quad.module:BaseVelocity@1.0",
            "quad.module:VectorEmitter@1.0",
            "emit:+x",
        ),
    )
    response = adapt_quad_vector_integration_result(selected, resultant)

    require(
        type(response) is QuadVectorIntegrationResponse,
        "result adapter returned a non-canonical response snapshot",
    )
    require(
        response.source is QuadVectorIntegrationSource.NARRATIVE,
        "result adapter changed integration source",
    )
    require(
        response.source_identity == selected.source_identity,
        "result adapter changed source identity",
    )
    require(
        response.resultant is resultant,
        "result adapter did not preserve canonical resultant object",
    )
    require(
        response.payload == (("x", 10), ("y", -4)),
        "result adapter changed canonical coordinate payload",
    )
    require(
        response.provenance == resultant.provenance,
        "result adapter changed resultant provenance",
   )

    expect_error(
        TypeError,
        lambda: adapt_quad_vector_integration_result(selected, object()),
        "result adapter accepted a non-canonical resultant",
    )
    expect_error(
        TypeError,
        lambda: adapt_quad_vector_integration_request(object()),
        "request adapter accepted a non-canonical integration request",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(selected, "source_identity", "mutated"),
        "integration input snapshot became mutable",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(response, "payload", ()),
        "integration response snapshot became mutable",
    )

    for item in (selected, response):
        require(
            not hasattr(item, "execute")
            and not hasattr(item, "orchestrate")
            and not hasattr(item, "load")
            and not hasattr(item, "import_module")
            and not hasattr(item, "codex")
            and not hasattr(item, "run_cli"),
            "P11.7H integration snapshot gained engine, loader, Codex, or CLI authority",
        )

    print("Canonical AIR/runtime/narrative/tooling source adapter taxonomy: PASS")
    print("Lossless source-to-QuadVectorInput translation: PASS")
    print("Execution-context authority/budget translation: PASS")
    print("Integration request identity/fact validation: PASS")
    print("Resultant-to-canonical integration response translation: PASS")
    print("Resultant provenance/payload preservation: PASS")
    print("Immutable integration snapshot boundary: PASS")
    print("P11.7H engine/loader/Codex/CLI authority exclusion: PASS")


if __name__ == "__main__":
    main()
