"""P11.7E canonical Quad-Vector module registry/binding red-gate smoke test."""

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
    from quad_vector.registry import (
        QuadVectorModuleBinding,
        QuadVectorModuleRegistry,
        bind_quad_vector_modules,
        register_quad_vector_modules,
    )

    budget = QuadVectorResourceBudget(
        max_modules=4,
        max_contributions=32,
        max_iterations=32,
    )

    base = QuadVectorModuleSpec(
        canonical_id="quad.module:BaseVelocity",
        version="1.0",
        kind=QuadVectorModuleKind.FUNCTION,
        accepted_inputs=("quad.input",),
        produced_outputs=("quad.contribution",),
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
        accepted_inputs=("quad.contribution",),
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
        accepted_inputs=("quad.contribution",),
        produced_outputs=("quad.weight",),
        eligible_vectors=(
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        dependencies=(),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.balance_weight",
    )
    resolver = QuadVectorModuleSpec(
        canonical_id="quad.module:WeightedConsensus",
        version="1.0",
        kind=QuadVectorModuleKind.RESOLVER,
        accepted_inputs=("quad.weight", "quad.eligibility"),
        produced_outputs=("quad.resultant",),
        eligible_vectors=(
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        dependencies=(
            "quad.module:HighPressure",
            "quad.module:BalanceWeight",
        ),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=budget,
        implementation_reference="python:quad_plugins.weighted_consensus",
    )

    # Intentionally declared out of dependency order. Registration preserves
    # authored order; binding establishes a deterministic dependency order.
    authored = (resolver, conditional, base, weighting)
    registry = register_quad_vector_modules(authored, budget=budget)

    require(
        type(registry) is QuadVectorModuleRegistry,
        "registry factory returned the wrong exact type",
   )
    require(registry.specs == authored, "registry did not preserve canonical authored registration order")
    require(registry.module_count == 4, "registry module accounting changed")
    require(
        registry.lookup("quad.module:BaseVelocity") is base,
        "registry lookup did not preserve exact canonical specification identity",
    )
    require(registry.lookup("quad.module:missing") is None, "registry lookup returned a value for an unknown canonical identity")

    bindings = bind_quad_vector_modules(registry)
    require(
        tuple(type(binding) for binding in bindings) == (QuadVectorModuleBinding,) * 4,
        "binding produced a non-canonical binding type",
    )
    require(
        tuple(binding.spec.canonical_id for binding in bindings)
        == (
            "quad.module:BaseVelocity",
            "quad.module:HighPressure",
            "quad.module:BalanceWeight",
            "quad.module:WeightedConsensus",
        ),
        "dependency binding order is not deterministic",
   )
    require(bindings[1].dependencies == (bindings[0],), "conditional dependency did not bind to the canonical base module")
    require(
        tuple(item.spec.canonical_id for item in bindings[3].dependencies)
        == ("quad.module:HighPressure", "quad.module:BalanceWeight"),
        "resolver dependencies did not preserve declared dependency order",
   )

    expect_error(
        ValueError,
        lambda: register_quad_vector_modules(
            (
                base,
                QuadVectorModuleSpec(
                    canonical_id="quad.module:BaseVelocity",
                    version="2.0",
                    kind=QuadVectorModuleKind.FUNCTION,
                    determinism_contract="pure-deterministic",
                    implementation_reference="python:quad_plugins.base_velocity_v2",
                ),
            ),
            budget=budget,
        ),
        "registry accepted a canonical identity collision",
    )
    expect_error(
        ValueError,
        lambda: register_quad_vector_modules(
            (
                QuadVectorModuleSpec(
                    canonical_id="quad.module:Orphan",
                    version="1.0",
                    kind=QuadVectorModuleKind.FUNCTION,
                    dependencies=("quad.module:Missing",),
                    determinism_contract="pure-deterministic",
                    implementation_reference="python:quad_plugins.orphan",
                ),
            ),
            budget=budget,
        ),
        "registry accepted an unresolved dependency",
    )

    cycle_a = QuadVectorModuleSpec(
        canonical_id="quad.module:CycleA",
        version="1.0",
        kind=QuadVectorModuleKind.FUNCTION,
        dependencies=("quad.module:CycleB",),
        determinism_contract="pure-deterministic",
        implementation_reference="python:quad_plugins.cycle_a",
    )
    cycle_b = QuadVectorModuleSpec(
        canonical_id="quad.module:CycleB",
        version="1.0",
        kind=QuadVectorModuleKind.CONDITIONAL,
        dependencies=("quad.module:CycleA",),
        determinism_contract="pure-deterministic",
        implementation_reference="python:quad_plugins.cycle_b",
    )
    cycle_registry = register_quad_vector_modules((cycle_a, cycle_b), budget=budget)
    expect_error(
        ValueError,
        lambda: bind_quad_vector_modules(cycle_registry),
        "binding accepted a dependency cycle",
    )

    expect_error(
        ValueError,
        lambda: register_quad_vector_modules(
            authored,
            budget=QuadVectorResourceBudget(
                max_modules=3,
                max_contributions=32,
                max_iterations=32,
            ),
        ),
        "registry accepted modules beyond the canonical resource budget",
   )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(registry, "specs", ()),
        "canonical module registry snapshot became mutable",
   )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(bindings[0], "spec", resolver),
        "canonical module binding became mutable",
   )

    require(
        all(
            not hasattr(binding, name)
            for binding in bindings
            for name in ("execute", "run", "invoke", "call")
        ),
        "P11.7E binding gained module-execution behavior",
    )

    print("Canonical modular registry authored-order preservation: PASS")
    print("Canonical identity collision and dependency validation: PASS")
    print("Deterministic dependency binding order: PASS")
    print("Declared dependency-order preservation: PASS")
    print("Dependency-cycle rejection: PASS")
    print("Registry module-budget boundary: PASS")
    print("Immutable registry/binding snapshot boundary: PASS")
    print("P11.7E module-execution exclusion: PASS")


if __name__ == "__main__":
    main()
