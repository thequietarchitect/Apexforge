"""P11.9E non-executing AETHER-AIR transformation and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .construction import AetherAirSnapshot, construct_aether_air_snapshot
from .model import AetherAirRepresentation
from .records import AetherIntentTrace


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


@dataclass(frozen=True)
class AetherAirTransformation:
    """Immutable passive lineage from one AETHER-AIR snapshot to another."""

    operation: str
    source: AetherAirSnapshot
    result: AetherAirSnapshot
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _text(self.operation, "AetherAirTransformation.operation")
        if type(self.source) is not AetherAirSnapshot:
            raise TypeError("source must be an exact AetherAirSnapshot")
        if type(self.result) is not AetherAirSnapshot:
            raise TypeError("result must be an exact AetherAirSnapshot")
        if type(self.provenance) is not tuple:
            raise TypeError("provenance must be an exact tuple")
        for index, item in enumerate(self.provenance):
            _text(item, f"AetherAirTransformation.provenance[{index}]")


def transform_aether_air_snapshot(
    source: AetherAirSnapshot,
    *,
    operation: str,
    representation: AetherAirRepresentation,
    traces: Tuple[AetherIntentTrace, ...] = (),
    provenance: Tuple[str, ...] = (),
) -> AetherAirTransformation:
    """Record an explicit non-executing transformation into a fresh snapshot."""

    result = construct_aether_air_snapshot(
        representation,
        traces=traces,
    )
    return AetherAirTransformation(
        operation=operation,
        source=source,
        result=result,
        provenance=provenance,
    )


def normalize_aether_air_snapshot(
    source: AetherAirSnapshot,
    *,
    representation: AetherAirRepresentation,
    traces: Tuple[AetherIntentTrace, ...] = (),
    provenance: Tuple[str, ...] = (),
) -> AetherAirTransformation:
    """Record an explicit canonical restatement without implicit rewriting."""

    return transform_aether_air_snapshot(
        source,
        operation="normalization",
        representation=representation,
        traces=traces,
        provenance=provenance,
    )


__all__ = (
    "AetherAirTransformation",
    "transform_aether_air_snapshot",
    "normalize_aether_air_snapshot",
)
