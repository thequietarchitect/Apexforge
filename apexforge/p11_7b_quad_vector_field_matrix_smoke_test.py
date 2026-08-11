"""P11.7B Quad-Vector Field Matrix red-gate smoke test."""

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
    from quad_vector.field_matrix import (
        QuadVectorFieldMatrix,
        generate_quad_vector_field_matrix,
    )

    stimulus = QuadVectorInput(
        identity="quad.field-matrix:test",
        facts=(("mode", "routing-only"),),
    )
    contributions = (
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_X,
            magnitude=3,
            order=0,
            provenance=("source:nx-0",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_Y,
            magnitude=5,
            order=1,
            provenance=("source:py-1",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=7,
            order=2,
            provenance=("source:px-2",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.NEGATIVE_Y,
            magnitude=4,
            order=3,
            provenance=("source:ny-3",),
        ),
        QuadVectorContribution(
            lane=QuadVectorLane.POSITIVE_X,
            magnitude=9,
            order=4,
            provenance=("source:px-4",),
        ),
    )
    budget = QuadVectorResourceBudget(
        max_modules=8,
        max_contributions=5,
        max_iterations=16,
    )

    matrix = generate_quad_vector_field_matrix(
        stimulus=stimulus,
        contributions=contributions,
        budget=budget,
    )

    require(type(matrix) is QuadVectorFieldMatrix, "field-matrix factory returned the wrong exact type")
    require(matrix.stimulus is stimulus, "field matrix did not preserve the canonical stimulus envelope")
    require(
        matrix.lane_order
        == (
            QuadVectorLane.POSITIVE_X,
            QuadVectorLane.NEGATIVE_X,
            QuadVectorLane.POSITIVE_Y,
            QuadVectorLane.NEGATIVE_Y,
        ),
        "motor-derived canonical lane order changed",
    )
    require(
        matrix.lane_contributions(QuadVectorLane.POSITIVE_X)
        == (contributions[2], contributions[4]),
        "+X routing did not preserve encounter order",
    )
    require(
        matrix.lane_contributions(QuadVectorLane.NEGATIVE_X)
        == (contributions[0],),
        "-X routing changed",
    )
    require(
        matrix.lane_contributions(QuadVectorLane.POSITIVE_Y)
        == (contributions[1],),
        "+Y routing changed",
   )
    require(
        matrix.lane_contributions(QuadVectorLane.NEGATIVE_Y)
        == (contributions[3],),
        "-Y routing changed",
   )
    require(
        matrix.contribution_count == len(contributions),
        "field-matrix contribution accounting changed",
    )

    expect_error(
        FrozenInstanceError,
        lambda: setattr(matrix, "contribution_count", 999),
        "field matrix became mutable",
    )
    expect_error(
        ValueError,
        lambda: generate_quad_vector_field_matrix(
            stimulus=stimulus,
            contributions=contributions,
            budget=QuadVectorResourceBudget(
                max_modules=8,
                max_contributions=4,
                max_iterations=16,
            ),
        ),
        "field matrix accepted contributions beyond its canonical resource budget",
    )
    expect_error(
        TypeError,
        lambda: matrix.lane_contributions("+X"),
        "field matrix accepted a non-canonical lane token",
   )

    require(not hasattr(matrix, "synchronize"), "P11.7B field matrix gained synchronization behavior")
    require(not hasattr(matrix, "resolve"), "P11.7B field matrix gained resolution behavior")
    require(not hasattr(matrix, "execute"), "P11.7B field matrix gained execution behavior")

    print("Canonical +X/-X/+Y/-Y field routing: PASS")
    print("Encounter-order preservation within lanes: PASS")
    print("Field-matrix resource-budget boundary: PASS")
    print("Immutable motor-derived Field Matrix boundary: PASS")
    print("P11.7B synchronization/resolution exclusion: PASS")


if __name__ == "__main__":
    main()
