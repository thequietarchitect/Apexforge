"""AETHER-AIR 2.0 interstitial semantic representation."""

from .construction import (
    AetherAirSnapshot,
    construct_aether_air_snapshot,
)
from .model import (
    CORE_AETHER_BEHAVIOR_KINDS,
    AetherAirRepresentation,
    AetherBehaviorIntent,
    AetherBehaviorKind,
    AetherIntentParameter,
)
from .records import (
    AetherEvidence,
    AetherIntentTrace,
    AetherPredecessorReference,
)

__all__ = (
    "AetherBehaviorKind",
    "AetherIntentParameter",
    "AetherBehaviorIntent",
    "AetherAirRepresentation",
    "CORE_AETHER_BEHAVIOR_KINDS",
    "AetherPredecessorReference",
    "AetherEvidence",
    "AetherIntentTrace",
    "AetherAirSnapshot",
    "construct_aether_air_snapshot",
)
