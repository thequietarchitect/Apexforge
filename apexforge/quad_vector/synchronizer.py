"""Deterministic phase alignment for the P11.7 Quad-Vector Engine.

P11.7C introduces synchronization only. Resultant resolution, module execution,
registry behavior, and runtime orchestration remain outside this slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .field_matrix import QuadVectorFieldMatrix
from .model import QuadVectorContribution, QuadVectorLane


_CANONICAL_LANE_ORDER = {
    QuadVectorLane.POSITIVE_X: 0,
    QuadVectorLane.NEGATIVE_X: 1,
    QuadVectorLane.POSITIVE_Y: 2,
    QuadVectorLane.NEGATIVE_Y: 3,
}


@dataclass(frozen=True)
class QuadVectorSynchronizationPhase:
    """One immutable synchronization phase for a shared contribution order."""

    order: int
    contributions: Tuple[QuadVectorContribution, ...]


@dataclass(frozen=True)
class QuadVectorSynchronization:
    """Immutable deterministic synchronization snapshot over a Field Matrix."""

    field_matrix: QuadVectorFieldMatrix
    phases: Tuple[QuadVectorSynchronizationPhase, ...]
    synchronized_contributions: Tuple[QuadVectorContribution, ...]

    @property
    def phase_count(self) -> int:
        return len(self.phases)


def _phase_contributions(
    field_matrix: QuadVectorFieldMatrix,
    order: int,
) -> Tuple[QuadVectorContribution, ...]:
    encountered = tuple(
        contribution
        for contribution in field_matrix.contributions
        if contribution.order == order
    )
    return tuple(
        sorted(
            encountered,
            key=lambda contribution: _CANONICAL_LANE_ORDER[contribution.lane],
        )
    )


def synchronize_quad_vector_field_matrix(
    field_matrix: QuadVectorFieldMatrix,
) -> QuadVectorSynchronization:
    """Align routed contributions by ascending phase and canonical lane order.

    Contributions are never transformed. Within a shared phase, canonical lane
    order is +X, -X, +Y, -Y; Python's stable ordering preserves encounter order
    for contributions already occupying the same lane.
    """

    if type(field_matrix) is not QuadVectorFieldMatrix:
        raise TypeError("field_matrix must be an exact QuadVectorFieldMatrix")

    phase_orders = tuple(sorted({item.order for item in field_matrix.contributions}))
    if len(phase_orders) > field_matrix.budget.max_iterations:
        raise ValueError(
            "synchronization phase count exceeds canonical iteration budget"
        )

    phases = tuple(
        QuadVectorSynchronizationPhase(
            order=order,
            contributions=_phase_contributions(field_matrix, order),
        )
        for order in phase_orders
    )
    synchronized_contributions = tuple(
        contribution
        for phase in phases
        for contribution in phase.contributions
    )

    return QuadVectorSynchronization(
        field_matrix=field_matrix,
        phases=phases,
        synchronized_contributions=synchronized_contributions,
    )


__all__ = (
    "QuadVectorSynchronization",
    "QuadVectorSynchronizationPhase",
    "synchronize_quad_vector_field_matrix",
)
