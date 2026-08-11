"""Deterministic Rotor-Ring convergence for the P11.7 Quad-Vector Engine.

P11.7D resolves an already-synchronized four-lane stream into the passive
immutable ResultantVector boundary. Module binding, execution, registry
orchestration, and authoring adapters remain outside this slice.
"""

from __future__ import annotations

from .model import QuadVectorLane, ResultantVector
from .synchronizer import QuadVectorSynchronization


def resolve_quad_vector_synchronization(
    synchronization: QuadVectorSynchronization,
) -> ResultantVector:
    """Resolve one synchronization snapshot into a deterministic resultant.

    Contributions are consumed exactly in synchronized order. Lane identity
    supplies the sign of each magnitude:
    +X adds to x, -X subtracts from x, +Y adds to y, and -Y subtracts from y.
    Provenance is flattened in the same synchronized order so the resultant
    remains explainable without mutating or reordering its source records.
    """

    if type(synchronization) is not QuadVectorSynchronization:
        raise TypeError(
            "synchronization must be an exact QuadVectorSynchronization"
        )

    x = 0
    y = 0
    provenance = []

    for contribution in synchronization.synchronized_contributions:
        if contribution.lane is QuadVectorLane.POSITIVE_X:
            x += contribution.magnitude
        elif contribution.lane is QuadVectorLane.NEGATIVE_X:
            x -= contribution.magnitude
        elif contribution.lane is QuadVectorLane.POSITIVE_Y:
            y += contribution.magnitude
        elif contribution.lane is QuadVectorLane.NEGATIVE_Y:
            y -= contribution.magnitude
        else:
            raise TypeError("synchronized contribution has a non-canonical lane")

        provenance.extend(contribution.provenance)

    return ResultantVector(
        x=x,
        y=y,
        contributions=synchronization.synchronized_contributions,
        provenance=tuple(provenance),
    )


__all__ = ("resolve_quad_vector_synchronization",)
