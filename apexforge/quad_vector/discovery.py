"""Passive canonical module discovery for the P11.7 Quad-Vector Engine.

P11.7K inventories opaque module descriptor references without parsing,
canonicalizing, registering, binding, executing, importing, or loading module
implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class QuadVectorDiscoverySource(Enum):
    """Canonical passive discovery-source taxonomy."""

    MANIFEST = "manifest"
    DIRECTORY = "directory"
    EXPLICIT = "explicit"


def _require_text(value: object, *, owner: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{owner} must be a non-empty string")
    return value


@dataclass(frozen=True)
class QuadVectorDiscoveryCandidate:
    """Immutable opaque descriptor candidate discovered without evaluation."""

    source: QuadVectorDiscoverySource
    source_identity: str
    descriptor_identity: str
    descriptor_reference: str
    order: int

    def __post_init__(self) -> None:
        if type(self.source) is not QuadVectorDiscoverySource:
            raise TypeError("source must be an exact QuadVectorDiscoverySource")
        _require_text(self.source_identity, owner="source_identity")
        _require_text(self.descriptor_identity, owner="descriptor_identity")
        _require_text(self.descriptor_reference, owner="descriptor_reference")
        if type(self.order) is not int or self.order < 0:
            raise ValueError("order must be a non-negative int")


@dataclass(frozen=True)
class QuadVectorDiscoveryInventory:
    """Immutable deterministically ordered passive discovery inventory."""

    candidates: Tuple[QuadVectorDiscoveryCandidate, ...]

    def __post_init__(self) -> None:
        if type(self.candidates) is not tuple:
            raise TypeError("candidates must be a tuple")
        for candidate in self.candidates:
            if type(candidate) is not QuadVectorDiscoveryCandidate:
                raise TypeError(
                    "candidates must contain exact QuadVectorDiscoveryCandidate values"
                )
        descriptor_ids = tuple(
            candidate.descriptor_identity for candidate in self.candidates
        )
        if len(set(descriptor_ids)) != len(descriptor_ids):
            raise ValueError("descriptor_identity values must be unique")


def discover_quad_vector_modules(
    candidates: Tuple[QuadVectorDiscoveryCandidate, ...],
) -> QuadVectorDiscoveryInventory:
    """Validate and deterministically inventory opaque discovery candidates."""

    if type(candidates) is not tuple:
        raise TypeError("candidates must be a tuple")
    for candidate in candidates:
        if type(candidate) is not QuadVectorDiscoveryCandidate:
            raise TypeError(
                "candidates must contain exact QuadVectorDiscoveryCandidate values"
            )

    descriptor_ids = tuple(candidate.descriptor_identity for candidate in candidates)
    if len(set(descriptor_ids)) != len(descriptor_ids):
        raise ValueError("descriptor_identity values must be unique")

    indexed = tuple(enumerate(candidates))
    ordered = tuple(
        candidate
        for _, candidate in sorted(
            indexed,
            key=lambda item: (item[1].order, item[0]),
         )
    )
    return QuadVectorDiscoveryInventory(candidates=ordered)


__all__ = (
    "QuadVectorDiscoveryCandidate",
    "QuadVectorDiscoveryInventory",
    "QuadVectorDiscoverySource",
    "discover_quad_vector_modules",
)
