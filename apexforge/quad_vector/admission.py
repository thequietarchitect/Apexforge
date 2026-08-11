"""Canonical module admission boundary for the P11.7 Quad-Vector Engine.

P11.7J admits validated authored-module snapshots into the frozen canonical
registry without binding, executing, discovering, importing, or loading module
implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .authoring.adapter import QuadVectorAuthoredModule
from .model import QuadVectorResourceBudget
from .registry import QuadVectorModuleRegistry, register_quad_vector_modules


@dataclass(frozen=True)
class QuadVectorModuleAdmission:
    """Immutable snapshot of authored modules admitted to a canonical registry."""

    authored_modules: Tuple[QuadVectorAuthoredModule, ...]
    registry: QuadVectorModuleRegistry

    def __post_init__(self) -> None:
        if type(self.authored_modules) is not tuple:
            raise TypeError("authored_modules must be a tuple")
        for authored in self.authored_modules:
            if type(authored) is not QuadVectorAuthoredModule:
                raise TypeError(
                    "authored_modules must contain exact QuadVectorAuthoredModule values"
                )
        if type(self.registry) is not QuadVectorModuleRegistry:
            raise TypeError("registry must be an exact QuadVectorModuleRegistry")
        expected_specs = tuple(authored.spec for authored in self.authored_modules)
        if self.registry.specs != expected_specs:
            raise ValueError(
                "registry specs must preserve authored module order and specification identity"
            )
        if any(
            registry_spec is not authored.spec
            for authored, registry_spec in zip(
                self.authored_modules,
                self.registry.specs,
            )
        ):
            raise ValueError(
                "registry specs must preserve authored specification object identity"
            )


def admit_quad_vector_modules(
    authored_modules: Tuple[QuadVectorAuthoredModule, ...],
    *,
    budget: QuadVectorResourceBudget,
) -> QuadVectorModuleAdmission:
    """Admit exact authored snapshots through the frozen registry validator."""

    if type(authored_modules) is not tuple:
        raise TypeError("authored_modules must be a tuple")
    for authored in authored_modules:
        if type(authored) is not QuadVectorAuthoredModule:
            raise TypeError(
                "authored_modules must contain exact QuadVectorAuthoredModule values"
            )
    if type(budget) is not QuadVectorResourceBudget:
        raise TypeError("budget must be an exact QuadVectorResourceBudget")

    specs = tuple(authored.spec for authored in authored_modules)
    registry = register_quad_vector_modules(specs, budget=budget)
    return QuadVectorModuleAdmission(
        authored_modules=authored_modules,
        registry=registry,
    )


__all__ = (
    "QuadVectorModuleAdmission",
    "admit_quad_vector_modules",
)
