"""Passive canonical value models for the P11.7 Quad-Vector Engine.

P11.7A defines immutable records only.  It deliberately introduces no
generation, synchronization, resolution, registration, or execution behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple


class QuadVectorLane(Enum):
    """Canonical motor-derived lane order."""

    POSITIVE_X = "+X"
    NEGATIVE_X = "-X"
    POSITIVE_Y = "+Y"
    NEGATIVE_Y = "-Y"


def _require_non_negative_int(value: int, *, owner: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{owner} must be a non-negative int")
    return value


@dataclass(frozen=True)
class QuadVectorResourceBudget:
    """Passive bounded-execution budget carried into later engine slices."""

    max_modules: int = 64
    max_contributions: int = 256
    max_iterations: int = 1024

    def __post_init__(self) -> None:
        _require_non_negative_int(self.max_modules, owner="max_modules")
        _require_non_negative_int(
            self.max_contributions,
            owner="max_contributions",
        )
        _require_non_negative_int(self.max_iterations, owner="max_iterations")


@dataclass(frozen=True)
class QuadVectorInput:
    """Canonical immutable stimulus envelope."""

    identity: str
    facts: Tuple[Tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if type(self.identity) is not str or not self.identity.strip():
            raise ValueError("identity must be a non-empty string")
        if type(self.facts) is not tuple:
            raise TypeError("facts must be a tuple")


@dataclass(frozen=True)
class QuadVectorContribution:
    """One immutable contribution routed toward one canonical vector lane."""

    lane: QuadVectorLane
    magnitude: int
    order: int
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.lane) is not QuadVectorLane:
            raise TypeError("lane must be an exact QuadVectorLane")
        if type(self.magnitude) is not int:
            raise TypeError("magnitude must be an int")
        _require_non_negative_int(self.order, owner="order")
        if type(self.provenance) is not tuple:
            raise TypeError("provenance must be a tuple")
        if any(type(item) is not str or not item.strip() for item in self.provenance):
            raise ValueError("provenance entries must be non-empty strings")


@dataclass(frozen=True)
class ResultantVector:
    """Passive immutable resultant boundary.

    Resolution semantics are intentionally absent in P11.7A.
    """

    x: int = 0
    y: int = 0
    contributions: Tuple[QuadVectorContribution, ...] = ()
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.x) is not int or type(self.y) is not int:
            raise TypeError("resultant coordinates must be ints")
        if type(self.contributions) is not tuple:
            raise TypeError("contributions must be a tuple")
        if any(type(item) is not QuadVectorContribution for item in self.contributions):
            raise TypeError("contributions must contain exact QuadVectorContribution values")
        if type(self.provenance) is not tuple:
            raise TypeError("provenance must be a tuple")
        if any(type(item) is not str or not item.strip() for item in self.provenance):
            raise ValueError("provenance entries must be non-empty strings")


__all__ = (
    "QuadVectorContribution",
    "QuadVectorInput",
    "QuadVectorLane",
    "QuadVectorResourceBudget",
    "ResultantVector",
)
