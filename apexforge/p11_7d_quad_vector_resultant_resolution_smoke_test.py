"""P11.7D Quad-Vector resultant-resolution red-gate smoke test."""

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
    from quad_vector.field_matrix import generate_quad_vector_field_matrix
    from quad_vector.model import (
        QuadVectorContribution,
        QuadVectorInput,
        QuadVectorLane,
        QuadVectorResourceBudget,
        ResultantVector,
    )
    from quad_vector.resolver import resolve_quad_vector_synchronization
    from quad_vector.synchronizer import synchronize_quad_vector_field_matrix

    stimulus = QuadVectorInput(
        identity="quad.resultant:test",
        facts=(("mode", "rotor-ring-convergence"),),
    )
    contributions = (
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=10,
            order=0,
            provenance=("source:px-0",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_X,
            magnitude=3,
            order=0,
            provenance=("source:nx-0",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_Y,
            magnitude=7,
            order=1,
            provenance=("source:py-1",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_Y,
            magnitude=2,
            order=1,
            provenance=("source:ny-1",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=4,
            order=2,
            provenance=("source:px-2",),
        ),
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=16,
        max_iterations=8,
    )
    matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=contributions,
        budget=budget,
    )
    synchronization = synchronize_quad_vector_field_matrix(matrix)
    resultant = resolve_quad_vector_synchronization(synchronization)

    require(
        type(resultant) is ResultantVector,
        "resolver returned the wrong exact resultant type",
    )
    require(
        (resultant.x, resultant.y) == (11, 5),
        "signed +X/-X/+Y/-Y convergence changed",
    )
    require(
        resultant.contributions == synchronization.synchronized_contributions,
        "resultant lost the exact synchronized contribution sequence",
    )
    require(
        resultant.provenance
        == (
            "source:px-0",
            "source:nx-0",
            "source:py-1",
            "source:ny-1",
            "source:px-2",
        ),
        "resultant provenance is not deterministic synchronized-order provenance",
    )

    repeat = resolve_quad_vector_synchronization(synchronization)
    require(
        repeat == resultant,
        "identical synchronization input did not produce an identical resultant",
    )
    require(
        repeat is not resultant,
        "resolver reused a prior resultant instance instead of producing a fresh immutable value",
    )

    balanced_matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=(
            QuadVectorContribution(
                lane=QuadVectorLane.POSITIVE_X,
                magnitude=6,
                order=0,
                provenance=("source:balance-px",),
            ),
            QuadVectorContribution(
                lane=QuadVectorLane.NEGATIVE_X,
                magnitude=6,
                order=0,
                provenance=("source:balance-nx",),
            ),
            QuadVectorContribution(
                lane=QuadVectorLane.POSITIVE_Y,
                magnitude=9,
                order=1,
                provenance=("source:balance-py",),
            ),
            QuadVectorContribution(
                lane=QuadVectorLane.NEGATIVE_Y,
                magnitude=9,
                order=1,
                provenance=("source:balance-ny",),
            ),
        ),
        budget=budget,
    )
    balanced = resolve_quad_vector_synchronization(
        synchronize_quad_vector_field_matrix(balanced_matrix)
    )
    require(
        (balanced.x, balanced.y) == (0, 0),
        "balanced opposing lanes did not converge to the neutral resultant",
    )

    empty_matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=(),
        budget=budget,
    )
    empty = resolve_quad_vector_synchronization(
        synchronize_quad_vector_field_matrix(empty_matrix)
    )
    require(
        (empty.x, empty.y, empty.contributions, empty.provenance) == (0, 0, (), ()),
        "empty synchronization did not resolve to the canonical neutral resultant",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(resultant, "x", 999),
        "resultant boundary became mutable",
    )
    expect_error(
        TypeError,
        lambda: resolve_quad_vector_synchronization(matrix),
        "resolver accepted an unsynchronized Field Matrix",
    )

    require(
        not hasattr(resultant, "execute"),
        "P11.7D resultant gained execution behavior",
    )
    require(
        not hasattr(resultant, "bind"),
        "P11.7D resultant gained module-binding behavior",
    )

    print("Signed +X/-X/+Y/-Y Rotor-Ring convergence: PASS")
    print("Deterministic synchronized-order provenance preservation: PASS")
    print("Repeatable resultant resolution: PASS")
    print("Balanced and empty neutral-resultant semantics: PASS")
    print("Immutable ResultantVector boundary: PASS")
    print("P11.7D synchronized-input enforcement: PASS")
    print("P11.7D module execution/binding exclusion: PASS")


if __name__ == "__main__":
    main()
