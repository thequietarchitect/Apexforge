"""P11.7C Quad-Vector synchronization red-gate smoke test."""

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
    )
    from quad_vector.synchronizer import (
        QuadVectorSynchronization,
        QuadVectorSynchronizationPhase,
        synchronize_quad_vector_field_matrix,
    )

    stimulus = QuadVectorInput(
        identity="quad.synchronization:test",
        facts=(("mode", "phase-alignment"),),
    )
    contributions = (
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_Y,
            magnitude=8,
            order=2,
            provenance=("source:ny-2a",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=3,
            order=0,
            provenance=("source:px-0",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_X,
            magnitude=4,
            order=1,
            provenance=("source:nx-1",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_Y,
            magnitude=5,
            order=1,
            provenance=("source:py-1",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=6,
            order=1,
            provenance=("source:px-1a",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=7,
            order=1,
            provenance=("source:px-1b",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_Y,
            magnitude=9,
            order=2,
            provenance=("source:ny-2b",),
        ),
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=16,
        max_iterations=3,
    )
    matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=contributions,
        budget=budget,
    )

    synchronized = synchronize_quad_vector_field_matrix(matrix)

    require(
        type(synchronized) is QuadVectorSynchronization,
        "synchronizer returned the wrong exact type",
    )
    require(
        synchronized.field_matrix is matrix,
        "synchronization did not preserve the exact source Field Matrix",
    )
    require(
        synchronized.phase_count == 3,
        "synchronization phase accounting changed",
    )
    require(
        tuple(phase.order for phase in synchronized.phases) == (0, 1, 2),
        "synchronization phase order is not deterministic ascending order",
    )
    require(
        all(type(phase) is QuadVectorSynchronizationPhase for phase in synchronized.phases),
        "synchronization phases returned a non-canonical phase type",
    )

    phase_zero, phase_one, phase_two = synchronized.phases
    require(
        phase_zero.contributions == (contributions[1],),
        "phase zero contribution alignment changed",
    )
    require(
        phase_one.contributions
        == (
            contributions[4],
            contributions[5],
            contributions[2],
            contributions[3],
        ),
        "equal-order contributions did not use canonical lane order with encounter preservation",
    )
    require(
        phase_two.contributions == (contributions[0], contributions[6]),
        "same-lane encounter order changed during synchronization",
    )

    require(
        synchronized.synchronized_contributions
        == (
            contributions[1],
            contributions[4],
            contributions[5],
            contributions[2],
            contributions[3],
            contributions[0],
            contributions[6],
        ),
        "canonical synchronized contribution sequence changed",
   )
    require(
        tuple(item.magnitude for item in synchronized.synchronized_contributions)
        == (3, 6, 7, 4, 5, 8, 9),
        "synchronization transformed contribution magnitudes",
    )
    require(
        tuple(item.provenance for item in synchronized.synchronized_contributions)
        == (
            ("source:px-0",),
            ("source:px-1a",),
            ("source:px-1b",),
            ("source:nx-1",),
            ("source:py-1",),
            ("source:ny-2a",),
            ("source:ny-2b",),
        ),
        "synchronization transformed provenance",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(synchronized, "phase_count", 99),
        "synchronization snapshot became mutable",
    )
    expect_error(
        FrozenInstanceError,
        lambda: setattr(phase_one, "order", 99),
        "synchronization phase became mutable",
    )

    over_budget_matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=(
            QuadVectorContribution(
                lane=QuadVectorLane.POSITIVE_X,
                magnitude=1,
                order=0,
                provenance=("source:0",),
            ),
            QuadVectorContribution(
                lane=QuadVectorLane.NEGATIVE_X,
                magnitude=1,
                order=1,
                provenance=("source:1",),
            ),
            QuadVectorContribution(
                lane=QuadVectorLane.POSITIVE_Y,
                magnitude=1,
                order=2,
                provenance=("source:2",),
            ),
        ),
        budget=QuadVectorResourceBudget(
            max_modules=8,
            max_contributions=8,
            max_iterations=2,
        ),
    )
    expect_error(
        ValueError,
        lambda: synchronize_quad_vector_field_matrix(over_budget_matrix),
        "synchronizer accepted more phases than the canonical iteration budget",
    )

    require(
        not hasattr(synchronized, "resolve"),
        "P11.7C synchronization gained resultant-resolution behavior",
    )
    require(
        not hasattr(synchronized, "execute"),
        "P11.7C synchronization gained execution behavior",
   )

    print("Deterministic ascending synchronization phases: PASS")
    print("Canonical +X/-X/+Y/-Y tie alignment: PASS")
    print("Same-lane encounter-order preservation: PASS")
    print("Synchronization magnitude/provenance preservation: PASS")
    print("Synchronization iteration-budget boundary: PASS")
    print("Immutable synchronization snapshot boundary: PASS")
    print("P11.7C resultant-resolution/execution exclusion: PASS")


if __name__ == "__main__":
    main()
