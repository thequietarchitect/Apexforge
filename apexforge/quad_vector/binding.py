"""Canonical descriptor binding adapter for the P11.7 Quad-Vector Engine.

P10.2P advances one exact descriptor registration through the existing
deterministic P11.7E registry binder. It preserves registration provenance and
does not execute, import, or load module implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .registration import QuadVectorDescriptorRegistration
from .registry import QuadVectorModuleBinding, bind_quad_vector_modules


@dataclass(frozen=True)
class QuadVectorDescriptorBinding:
    """Immutable provenance-bearing result of canonical descriptor binding."""

    registration: QuadVectorDescriptorRegistration
    bindings: Tuple[QuadVectorModuleBinding, ...]

    def __post_init__(self) -> None:
        if type(self.registration) is not QuadVectorDescriptorRegistration:
            raise TypeError(
                "registration must be an exact QuadVectorDescriptorRegistration"
            )
        if type(self.bindings) is not tuple:
            raise TypeError("bindings must be an exact tuple")
        if any(type(item) is not QuadVectorModuleBinding for item in self.bindings):
            raise TypeError(
                "bindings must contain exact QuadVectorModuleBinding values"
            )

        registry_specs = self.registration.registry.specs
        bound_specs = tuple(item.spec for item in self.bindings)
        if len(bound_specs) != len(registry_specs):
            raise ValueError(
                "bindings must contain every registered canonical module exactly once"
            )
        if set(id(spec) for spec in bound_specs) != set(id(spec) for spec in registry_specs):
            raise ValueError(
                "bindings must preserve registered canonical spec object identity"
            )


def bind_quad_vector_descriptors(
    registration: QuadVectorDescriptorRegistration,
) -> QuadVectorDescriptorBinding:
    """Bind one descriptor registration through the existing registry binder."""

    if type(registration) is not QuadVectorDescriptorRegistration:
        raise TypeError(
            "registration must be an exact QuadVectorDescriptorRegistration"
        )

    bindings = bind_quad_vector_modules(registration.registry)

    if type(bindings) is not tuple:
        raise TypeError("registry binder must return an exact tuple")

    return QuadVectorDescriptorBinding(
        registration=registration,
        bindings=bindings,
    )


__all__ = (
    "QuadVectorDescriptorBinding",
    "bind_quad_vector_descriptors",
)
