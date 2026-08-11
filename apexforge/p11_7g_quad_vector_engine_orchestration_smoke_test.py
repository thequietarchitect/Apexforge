"""P11.7G canonical Quad-Vector engine-orchestration red-gate smoke test."""

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
    from quad_vector.model import (
        QuadVectorContribution,
        QuadVectorInput,
        QuadVectorLane,
        QuadVectorResourceBudget,
    )
    from quad_vector.module import QuadVectorModuleKind, QuadVectorModuleSpec
    from quad_vector.registry import (
        bind_quad_vector_modules,
        register_quad_vector_modules,
    )
    from quad_vector.execution import QuadVectorExecutionContext
    from quad_vector.orchestration import (
        QuadVectorOrchestrationResult,
        orchestrate_quad_vector_engine,
    )

    budget = QuadVectorResourceBudget(
        max_modules=4,
        max_contributions=8,
        max_iterations=4,
    )

    base = QuadVectorModuleSpec(
        canonical_id="quad.module:BaseVelocity",
        version="1.0",
        kind=QuadVectorModuleKind.FUNCTION,
        accepted_inputs=("quad.input",),
        produced_outputs=("quad.velocity",),
        eligible_vectors=(QuadVectorLane.POSITIVE_X, QuadVectorLane.NEGATIVE_X),
        dependencies=(),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.base_velocity",
    )
    conditional = QuadVectorModuleSpec(
        canonical_id="quad.module:HighPressure",
        version="1.0",
        kind=QuadVectorModuleKind.CONDITIONAL,
        accepted_inputs=("quad.velocity",),
        produced_outputs=("quad.eligibility",),
        eligible_vectors=(QuadVectorLane.POSITIVE_X, QuadVectorLane.NEGATIVE_X),
        dependencies=("quad.module:BaseVelocity",),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.high_pressure",
    )
    weighting = QuadVectorModuleSpec(
        canonical_id="quad.module:BalanceWeight",
        version="1.0",
        kind=QuadVectorModuleKind.WEIGHTING_RULE,
        accepted_inputs=("quad.velocity", "quad.eligibility"),
        produced_outputs=("quad.weight",),
        eligible_vectors=(
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        dependencies=(
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
        ),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.balance_weight",
    )
    emitter = QuadVectorModuleSpec(
        canonical_id="quad.module:VectorEmitter",
        version="1.0",
        kind=QuadVectorModuleKind.VECTOR_OPERATOR,
        accepted_inputs=("quad.weight",),
        produced_outputs=("quad.contributions",),
        eligible_vectors=(
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        dependencies=("quad.module:BalanceWeight",),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.vector_emitter",
    )

    registry = register_quad_vector_modules(
        (emitter, weighting, conditional, base),
        budget=budget,
    )
    bindings = bind_quad_vector_modules(registry)
    require(
        tuple(binding.spec.canonical_id for binding in bindings)
        == (
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
            "quad.module:BalanceWeight",
            "quad.module:VectorEmitter",
        ),
        "fixture binding order changed",
    )

    calls = []

    def base_velocity(inputs, dependencies, context):
        calls.append("quad.module:BaseVelocity")
        return {"quad.velocity": inputs["quad.input"] * 2}

    def high_pressure(inputs, dependencies, context):
        calls.append("quad.module:HighPressure")
        return {"quad.eligibility": inputs["quad.velocity"] >= 10}

    def balance_weight(inputs, dependencies, context):
        calls.append("quad.module:BalanceWeight")
        return {
            "quad.weight": inputs["quad.velocity"]
            if inputs["quad.eligibility"]
            else 0
        }

    def vector_emitter(inputs, dependencies, context):
        calls.append("quad.module:VectorEmitter")
        weight = inputs["quad.weight"]
        return {
            "quad.contributions": (
                QuadVectorContribution(
                    lane=QuadVectorLane.POSITIVE_X,
                    magnitude=weight,
                    order=0,
                    provenance=("emit:+x",),
                ),
                QuadVectorContribution(
                    lane=QuadVectorLane.NEGATIVE_X,
                    magnitude=2,
                    order=0,
                    provenance=("emit:-x",),
                ),
                QuadVectorContribution(
                    lane=QuadVectorLane.POSITIVE_Y,
                    magnitude=5,
                    order=1,
                    provenance=("emit:+y",),
                ),
                QuadVectorContribution(
                    lane=QuadVectorLane.NEGATIVE_Y,
                    magnitude=1,
                    order=1,
                    provenance=("emit:-y",),
                ),
            )
        }

    implementations = {
        "python:quad_plugins.base_velocity": base_velocity,
        "python:quad_plugins.high_pressure": high_pressure,
        "python:quad_plugins.balance_weight": balance_weight,
        "python:quad_plugins.vector_emitter": vector_emitter,
    }
    stimulus = QuadVectorInput(
        identity="quad.stimulus:orchestration-smoke",
        facts=(("quad.input", 6),),
    )
    context = QuadVectorExecutionContext(
        authorities=("quad.vector.read",),
        inputs=stimulus.facts,
        max_invocations=4,
    )

    result = orchestrate_quad_vector_engine(
        bindings,
        implementations=implementations,
        context=context,
        stimulus=stimulus,
        budget=budget,
    )

    require(
        type(result) is QuadVectorOrchestrationResult,
        "orchestration returned a non-canonical result type",
    )
    require(
        tuple(record.spec.canonical_id for record in result.execution_records)
        == tuple(binding.spec.canonical_id for binding in bindings),
        "orchestration changed deterministic module execution order",
    )
    require(
        tuple(calls)
        == (
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
            "quad.module:BalanceWeight",
            "quad.module:VectorEmitter",
        ),
        "orchestration changed implementation invocation order",
    )
    require(
        result.field_matrix.stimulus is stimulus,
        "orchestration did not preserve the canonical stimulus object",
    )
    require(
        result.field_matrix.contribution_count == 4,
        "execution-to-field bridge changed contribution count",
    )
    require(
        tuple(phase.order for phase in result.synchronization.phases) == (0, 1),
        "orchestration changed deterministic synchronization phases",
    )
    require(
        (result.resultant.x, result.resultant.y) == (10, 4),
        "orchestration changed canonical resultant resolution",
    )

    expected_chain = (
        "quad.module:BaseVelocity@1.0",
        "quad.module:HighPressure@1.0",
        "quad.module:BalanceWeight@1.0",
        "quad.module:VectorEmitter@1.0",
    )
    require(
        result.field_matrix.contributions[0].provenance
        == expected_chain + ("emit:+x",),
        "execution-to-vector provenance bridge changed",
    )
    require(
        result.resultant.provenance[:5]
        == expected_chain + ("emit:+x",),
        "resultant provenance did not originate in execution lineage",
    )

    small_budget = QuadVectorResourceBudget(
        max_modules=4,
        max_contributions=3,
        max_iterations=4,
    )
    expect_error(
        ValueError,
        lambda: orchestrate_quad_vector_engine(
            bindings,
            implementations=implementations,
            context=context,
            stimulus=stimulus,
            budget=small_budget,
        ),
        "orchestration bypassed the field-matrix contribution budget",
    )

    mismatched_context = QuadVectorExecutionContext(
        authorities=("quad.vector.read",),
        inputs=(("quad.input", 7),),
        max_invocations=4,
    )
    expect_error(
        ValueError,
        lambda: orchestrate_quad_vector_engine(
            bindings,
            implementations=implementations,
            context=mismatched_context,
            stimulus=stimulus,
            budget=budget,
        ),
        "orchestration accepted divergent stimulus/context inputs",
    )

    bad_implementations = dict(implementations)
    bad_implementations["python:quad_plugins.vector_emitter"] = (
        lambda inputs, dependencies, context: {
            "quad.contributions": ("not-a-contribution",)
        }
    )
    expect_error(
        TypeError,
        lambda: orchestrate_quad_vector_engine(
            bindings,
            implementations=bad_implementations,
            context=context,
            stimulus=stimulus,
            budget=budget,
        ),
        "orchestration accepted a non-canonical VECTOR_OPERATOR output",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(result, "resultant", None),
        "orchestration result became mutable",
    )
    require(
        not hasattr(result, "load")
        and not hasattr(result, "import_module")
        and not hasattr(result, "codex")
        and not hasattr(result, "run_cli"),
        "P11.7G orchestration gained host, loader, Codex, or CLI authority",
    )

    print("Canonical execution-to-field orchestration: PASS")
    print("Deterministic four-vector pipeline composition: PASS")
    print("Execution-to-contribution provenance bridge: PASS")
    print("Cross-pipeline resource-budget enforcement: PASS")
    print("Stimulus/context coherence boundary: PASS")
    print("VECTOR_OPERATOR output-type enforcement: PASS")
    print("Immutable orchestration-result boundary: PASS")
    print("P11.7G host/AIR/narrative/CLI integration exclusion: PASS")


if __name__ == "__main__":
    main()
