"""Deterministic four-lane field routing for the P11.7 Quad-Vector Engine.

P11.7B introduces routing only. Synchronization, resultant resolution, module
execution, and runtime orchestration remain outside this slice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .model import (
    QuadVectorContribution,
    QuadVectorInput,
    QuadVectorLane,
    QuadVectorResourceBudget,
)


_CANONICAL_LANE_ORDER = (
    QuadVectorLane.POSITIVE_X,
    QuadVectorLane.NEGATIVE_X,
    QuadVectorLane.POSITIVE_Y,
    QuadVectorLane.NEGATIVE_Y,
)


@dataclass(frozen=True)
class QuadVectorFieldMatrix:
    """Immutable routing snapshot across the four canonical vector lanes."""

    stimulus: QuadVectorInput
    contributions: Tuple[QuadVectorContribution, ...]
    budget: QuadVectorResourceBudget
    lane_order: Tuple[QuadVectorLane, ...] = field(
        init=False,
        default=_CANONICAL_LANE_ORDER,
    )
    contribution_count: int = field(init=False)

    def __post_init__(self) -> None:
        if type(self.stimulus) is not QuadVectorInput:
            raise TypeError("stimulus must be an exact QuadVectorInput")
        if type(self.contributions) is not tuple:
            raise TypeError("contributions must be a tuple")
        if any(
            type(contribution) is not QuadVectorContribution
            for contribution in self.contributions
        ):
            raise TypeError(
                "contributions must contain exact QuadVectorContribution values"
            )
        if type(self.budget) is not QuadVectorResourceBudget:
            raise TypeError("budget must be an exact QuadVectorResourceBudget")
        if len(self.contributions) > self.budget.max_contributions:
            raise ValueError(
                "field matrix contribution count exceeds resource budget"
            )
        object.__setattr__(self, "contribution_count", len(self.contributions))

    def lane_contributions(
        self,
        lane: QuadVectorLane,
    ) -> Tuple[QuadVectorContribution, ...]:
        """Return one lane in original encounter order without transforming it."""

        if type(lane) is not QuadVectorLane:
            raise TypeError("lane must be an exact QuadVectorLane")
        return tuple(
            contribution
            for contribution in self.contributions
            if contribution.lane is lane
        )


def generate_quad_vector_field_matrix(
    *,
    stimulus: QuadVectorInput,
    contributions: Tuple[QuadVectorContribution, ...],
    budget: QuadVectorResourceBudget,
) -> QuadVectorFieldMatrix:
    """Create a validated immutable routing snapshot.

    Generation in P11.7B means canonical lane routing only; it does not
    synchronize, weight, resolve, bind, or execute contributions.
    """

    return QuadVectorFieldMatrix(
        stimulus=stimulus,
        contributions=contributions,
        budget=budget,
    )


__all__ = (
    "QuadVectorFieldMatrix",
    "generate_quad_vector_field_matrix",
)
