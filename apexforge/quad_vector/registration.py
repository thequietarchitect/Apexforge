"""Canonical descriptor registration adapter for the P11.7 Quad-Vector Engine.

P11.7O advances canonical descriptors into the existing immutable module
registry. It reuses the P11.7E registry contract and does not bind, execute,
import, or load module implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .canonicalization import QuadVectorCanonicalDescriptor
from .model import QuadVectorResourceBudget
from .registry import QuadVectorModuleRegistry, register_quad_vector_modules


@dataclass(frozen=True)
class QuadVectorDescriptorRegistration:
    """Immutable provenance-bearing result of canonical descriptor registration."""

    canonical_descriptors: Tuple[QuadVectorCanonicalDescriptor, ...]
    registry: QuadVectorModuleRegistry

    def __post_init__(self) -> None:
        if type(self.canonical_descriptors) is not tuple:
            raise TypeError("canonical_descriptors must be an exact tuple")
        if any(type(item) is not QuadVectorCanonicalDescriptor for item in self.canonical_descriptors):
            raise TypeError(
                "canonical_descriptors must contain exact QuadVectorCanonicalDescriptor values"
            )
        if type(self.registry) is not QuadVectorModuleRegistry:
            raise TypeError("registry must be an exact QuadVectorModuleRegistry")

        specs = tuple(item.spec for item in self.canonical_descriptors)
        if self.registry.specs != specs:
            raise ValueError(
                "registry specs must preserve canonical descriptor spec order"
            )
        if any(
            registered is not descriptor.spec
            for registered, descriptor in zip(
                self.registry.specs, self.canonical_descriptors
            )
        ):
            raise ValueError(
                "registry specs must preserve canonical descriptor spec identity"
            )


def register_quad_vector_descriptors(
    canonical_descriptors: Tuple[QuadVectorCanonicalDescriptor, ...],
    *,
    budget: QuadVectorResourceBudget,
) -> QuadVectorDescriptorRegistration:
    """Register canonical descriptors through the existing P11.7E registry."""

    if type(canonical_descriptors) is not tuple:
        raise TypeError("canonical_descriptors must be an exact tuple")
    if any(type(item) is not QuadVectorCanonicalDescriptor for item in canonical_descriptors):
        raise TypeError(
            "canonical_descriptors must contain exact QuadVectorCanonicalDescriptor values"
        )
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    specs = tuple(item.spec for item in canonical_descriptors)
    registry = register_quad_vector_modules(specs, budget=budget)

    if registry.budget is not budget:
        raise ValueError("registry must preserve the supplied resource budget identity")

    return QuadVectorDescriptorRegistration(
        canonical_descriptors=canonical_descriptors,
        registry=registry,
    )


__all__ = (
    "QuadVectorDescriptorRegistration",
    "register_quad_vector_descriptors",
)
