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
from .transformation import (
    AetherAirTransformation,
    normalize_aether_air_snapshot,
    transform_aether_air_snapshot,
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
    "AetherAirTransformation",
    "transform_aether_air_snapshot",
    "normalize_aether_air_snapshot",
)
