"""P11.7A passive canonical Quad-Vector module-contract red-gate smoke test."""

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
    from quad_vector.module import (
        QuadVectorModuleKind,
        QuadVectorModuleSpec,
    )

    require(
        tuple(member.value for member in QuadVectorModuleKind)
        == (
            "function",
            "conditional",
            "resolver",
            "weighting_rule",
            "vector_operator",
            "synchronizer",
        ),
        "canonical Quad-Vector module-kind order changed",
    )

    spec = QuadVectorModuleSpec(
        canonical_id="quad.module:VelocityBias",
        version="1.0",
        kind=QuadVectorModuleKind.FUNCTION,
        accepted_inputs=("quad.input",),
        produced_outputs=("quad.contribution",),
        eligible_vectors=(QuadVectorLane.POSITIVE_X, QuadVectorLane.NEGATIVE_X),
        dependencies=("quad.module:BaseVelocity",),
        determinism_contract="pure-deterministic",
        authority_requirements=("quad.vector.read",),
        resource_budget=QuadVectorResourceBudget(
            max_modules=1,
            max_contributions=8,
            max_iterations=16,
        ),
        implementation_reference="python:quad_plugins.velocity_bias",
    )
    require(spec.canonical_id == "quad.module:VelocityBias", "canonical module identity changed")
    require(spec.version == "1.0", "canonical module version changed")
    require(spec.kind is QuadVectorModuleKind.FUNCTION, "canonical module kind changed")
    require(
        spec.eligible_vectors
        == (QuadVectorLane.POSITIVE_X, QuadVectorLane.NEGATIVE_X),
        "eligible-vector order changed",
    )
    require(
        spec.dependencies == ("quad.module:BaseVelocity",),
        "dependency inventory changed",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(spec, "version", "2.0"),
        "canonical module specification became mutable",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id=" ",
            version="1.0",
            kind=QuadVectorModuleKind.FUNCTION,
            determinism_contract="pure-deterministic",
            implementation_reference="python:x",
        ),
        "empty canonical module identity was accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:BadVersion",
            version=" ",
            kind=QuadVectorModuleKind.FUNCTION,
            determinism_contract="pure-deterministic",
            implementation_reference="python:x",
        ),
        "empty module version was accepted",
    )
    expect_error(
        TypeError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:BadKind",
            version="1.0",
            kind="function",
            determinism_contract="pure-deterministic",
            implementation_reference="python:x",
        ),
        "non-canonical module kind was accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:DuplicateDependency",
            version="1.0",
            kind=QuadVectorModuleKind.FUNCTION,
            dependencies=("quad.module:A", "quad.module:A"),
            determinism_contract="pure-deterministic",
            implementation_reference="python:x",
        ),
        "duplicate module dependency was accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:DuplicateLane",
            version="1.0",
            kind=QuadVectorModuleKind.CONDITIONAL,
            eligible_vectors=(QuadVectorLane.POSITIVE_Y, QuadVectorLane.POSITIVE_Y),
            determinism_contract="pure-deterministic",
            implementation_reference="python:x",
        ),
        "duplicate eligible vector lane was accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:NoDeterminism",
            version="1.0",
            kind=QuadVectorModuleKind.RESOLVER,
            determinism_contract=" ",
            implementation_reference="python:x",
        ),
        "empty determinism contract was accepted",
    )
    expect_error(
        ValueError,
        lambda: QuadVectorModuleSpec(
            canonical_id="quad.module:NoImplementation",
            version="1.0",
            kind=QuadVectorModuleKind.VECTOR_OPERATOR,
            determinism_contract="pure-deterministic",
            implementation_reference=" ",
        ),
        "empty implementation reference was accepted",
    )

    require(
        not hasattr(spec, "execute") and not hasattr(spec, "bind"),
        "P11.7A passive module specification gained execution behavior",
    )

    print("Canonical Quad-Vector module kinds: PASS")
    print("Immutable drag-and-drop module specification: PASS")
    print("Module identity/version/dependency validation: PASS")
    print("Vector eligibility and deterministic contract validation: PASS")
    print("P11.7A passive module execution boundary: PASS")


if __name__ == "__main__":
    main()
