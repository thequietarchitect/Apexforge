"""P11.9D deterministic AETHER-AIR interstitial construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .model import AetherAirRepresentation
from .records import AetherIntentTrace


@dataclass(frozen=True)
class AetherAirSnapshot:
    """Immutable deterministic composition of AETHER-AIR representation and traces."""

    representation: AetherAirRepresentation
    traces: Tuple[AetherIntentTrace, ...] = ()

    def __post_init__(self) -> None:
        if type(self.representation) is not AetherAirRepresentation:
            raise TypeError(
                "representation must be an exact AetherAirRepresentation"
            )
        if type(self.traces) is not tuple:
            raise TypeError("traces must be an exact tuple")
        if any(type(item) is not AetherIntentTrace for item in self.traces):
            raise TypeError(
                "traces must contain exact AetherIntentTrace values"
            )


def construct_aether_air_snapshot(
    representation: AetherAirRepresentation,
    *,
    traces: Tuple[AetherIntentTrace, ...] = (),
) -> AetherAirSnapshot:
    """Compose explicit canonical inputs without sorting, validating, or executing."""

    return AetherAirSnapshot(
        representation=representation,
        traces=traces,
    )


__all__ = (
    "AetherAirSnapshot",
    "construct_aether_air_snapshot",
)
