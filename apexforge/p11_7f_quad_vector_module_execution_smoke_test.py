"""P11.7F canonical Quad-Vector module-execution red-gate smoke test."""

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
    from quad_vector.model import QuadVectorLane, QuadVectorResourceBudget
    from quad_vector.module import QuadVectorModuleKind, QuadVectorModuleSpec
    from quad_vector.registry import bind_quad_vector_modules, register_quad_vector_modules
    from quad_vector.execution import (
        QuadVectorExecutionContext,
        QuadVectorExecutionRecord,
        execute_quad_vector_bindings,
    )

    budget = QuadVectorResourceBudget(
        max_modules=4,
        max_contributions=16,
        max_iterations=8,
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
        canonical_id="quad.module:BalanceWeb",
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
        dependencies=("quad.module:BaseVelocity", "quad.module:HighPressure"),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.balance_weight",
    )

    registry = register_quad_vector_modules(
        (weighting, conditional, base),
        budget=budget,
    )
    bindings = bind_quad_vector_modules(registry)

    calls = []

    def base_velocity(inputs, dependencies, context):
        require(inputs == {"quad.input": 6}, "function received undeclared or altered inputs")
        require(dependencies == (), "base function unexpectedly received dependencies")
        calls.append("quad.module:BaseVelocity")
        return {"quad.velocity": inputs["quad.input"] * 2}

    def high_pressure(inputs, dependencies, context):
        require(inputs == {"quad.velocity": 12}, "conditional did not receive declared dependency output")
        require(tuple(item.spec.canonical_id for item in dependencies) == ("quad.module:BaseVelocity",), "conditional dependency order changed")
        calls.append("quad.module:HighPressure")
        return {"quad.eligibility": inputs["quad.velocity"] >= 10}

    def balance_weight(inputs, dependencies, context):
        require(inputs == {"quad.velocity": 12, "quad.eligibility": True}, "weighting rule did not receive declared inputs")
        require(
            tuple(item.spec.canonical_id for item in dependencies)
            == ("quad.module:BaseVelocity", "quad.module:HighPressure"),
            "weighting dependency order changed",
        )
        calls.append("quad.module:BalanceWeb")
        return {"quad.weight": inputs["quad.velocity"] if inputs["quad.eligibility"] else 0}

    implementations = {
        "python:quad_plugins.base_velocity": base_velocity,
        "python:quad_plugins.high_pressure": high_pressure,
        "python:quad_plugins.balance_weight": balance_weight,
    }
    context = QuadVectorExecutionContext(
        authorities=("quad.vector.read",),
        inputs=(("quad.input", 6),),
        max_invocations=3,
    )

    records = execute_quad_vector_bindings(
        bindings,
        implementations=implementations,
        context=context,
    )

    require(
        tuple(type(record) for record in records) == (QuadVectorExecutionRecord,) * 3,
        "execution returned a non-canonical record type",
    )
    require(
        tuple(record.spec.canonical_id for record in records)
        == (
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
            "quad.module:BalanceWeb",
        ),
        "execution did not preserve deterministic bound dependency order",
    )
    require(
        tuple(calls)
        == (
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
            "quad.module:BalanceWeb",
        ),
        "implementation invocation order changed",
    )
    require(records[0].outputs == (("quad.velocity", 12),), "function output canonicalization changed")
    require(records[1].outputs == (("quad.eligibility", True),), "conditional output canonicalization changed")
    require(records[2].outputs == (("quad.weight", 12),), "weighting output canonicalization changed")
    require(
        records[2].provenance
        == (
            "quad.module:BaseVelocity@1.0",
            "quad.module:HighPressure@1.0",
            "quad.module:BalanceWeb@1.0",
        ),
        "execution provenance chain changed",
    )

    expect_error(
        PermissionError,
        lambda: execute_quad_vector_bindings(
            bindings,
            implementations=implementations,
            context=QuadVectorExecutionContext(
                authorities=(),
                inputs=(("quad.input", 6),),
                max_invocations=3,
            ),
        ),
        "module execution bypassed declared authority requirements",
    )
    expect_error(
        ValueError,
        lambda: execute_quad_vector_bindings(
            bindings,
            implementations={
                "python:quad_plugins.base_velocity": base_velocity,
                "python:quad_plugins.high_pressure": high_pressure,
            },
            context=context,
        ),
        "execution silently loaded or accepted a missing implementation",
    )
    expect_error(
        ValueError,
        lambda: execute_quad_vector_bindings(
            bindings,
            implementations=implementations,
            context=QuadVectorExecutionContext(
                authorities=("quad.vector.read",),
                inputs=(("quad.input", 6),),
                max_invocations=2,
            ),
        ),
        "execution exceeded its invocation budget",
    )

    bad_impl = dict(implementations)
    bad_impl["python:quad_plugins.high_pressure"] = lambda inputs, dependencies, context: {
        "undeclared.output": True
    }
    expect_error(
        ValueError,
        lambda: execute_quad_vector_bindings(
            bindings,
            implementations=bad_impl,
            context=context,
        ),
        "module execution accepted an undeclared output",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(context, "max_invocations", 99),
        "execution context became mutable",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(records[0], "outputs", ()),
        "execution record became mutable",
    )

    require(
        not hasattr(records[0], "load")
        and not hasattr(records[0], "import_module")
        and not hasattr(records[0], "codex"),
        "P11.7F execution record gained hidden loader or Codex authority",
    )

    print("Bound-module-only execution enforcement: PASS")
    print("Deterministic dependency-order module invocation: PASS")
    print("Declared-input/output execution contract: PASS")
    print("Explicit implementation-provider boundary: PASS")
    print("Authority and invocation-budget enforcement: PASS")
    print("Deterministic execution provenance: PASS")
    print("Immutable execution context/record boundary: PASS")
    print("P11.7F Codex/runtime-loader privilege exclusion: PASS")


if __name__ == "__main__":
    main()
