"""Passive canonical module contracts for the P11.7 Quad-Vector Engine.

P11.7A defines immutable module metadata only. Discovery, registration, binding,
and execution behavior are intentionally outside this architecture slice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

from .model import QuadVectorLane, QuadVectorResourceBudget


class QuadVectorModuleKind(Enum):
    """Canonical modular component kinds in deterministic declaration order."""

    FUNCTION = "function"
    CONDITIONAL = "conditional"
    RESOLVER = "resolver"
    WEIGHTING_RULE = "weighting_rule"
    VECTOR_OPERATOR = "vector_operator"
    SYNCHRONIZER = "synchronizer"


def _require_text(value: str, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string")
    return value


def _require_text_tuple(value: Tuple[str, ...], *, owner: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{owner} must be a tuple")
    if any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{owner} entries must be non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{owner} must not contain duplicates")


@dataclass(frozen=True)
class QuadVectorModuleSpec:
    """Immutable validated description of one installable Quad-Vector component."""

    canonical_id: str
    version: str
    kind: QuadVectorModuleKind
    determinism_contract: str
    implementation_reference: str
    accepted_inputs: Tuple[str, ...] = ()
    produced_outputs: Tuple[str, ...] = ()
    eligible_vectors: Tuple[QuadVectorLane, ...] = ()
    dependencies: Tuple[str, ...] = ()
    authority_requirements: Tuple[str, ...] = ()
    resource_budget: QuadVectorResourceBudget = field(
        default_factory=QuadVectorResourceBudget
    )

    def __post_init__(self) -> None:
        _require_text(self.canonical_id, owner="canonical_id")
        _require_text(self.version, owner="version")
        if type(self.kind) is not QuadVectorModuleKind:
            raise TypeError("kind must be an exact QuadVectorModuleKind")
        _require_text(self.determinism_contract, owner="determinism_contract")
        _require_text(self.implementation_reference, owner="implementation_reference")
        _require_text_tuple(self.accepted_inputs, owner="accepted_inputs")
        _require_text_tuple(self.produced_outputs, owner="produced_outputs")
        _require_text_tuple(self.dependencies, owner="dependencies")
        _require_text_tuple(self.authority_requirements, owner="authority_requirements")

        if type(self.eligible_vectors) is not tuple:
            raise TypeError("eligible_vectors must be a tuple")
        if any(type(vector) is not QuadVectorLane for vector in self.eligible_vectors):
            raise TypeError("eligible_vectors must contain exact QuadVectorLane values")
        if len(set(self.eligible_vectors)) != len(self.eligible_vectors):
            raise ValueError("eligible_vectors must not contain duplicates")

        if type(self.resource_budget) is not QuadVectorResourceBudget:
            raise TypeError("resource_budget must be an exact QuadVectorResourceBudget")


__all__ = (
    "QuadVectorModuleKind",
    "QuadVectorModuleSpec",
)
