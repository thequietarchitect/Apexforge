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
from .projection import (
    AetherAirDownstreamProjection,
    project_validated_aether_air,
)
from .reporting import (
    render_aether_air_downstream_projection_report,
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
from .validation import (
    AetherAirTransformationValidationReceipt,
    AetherAirValidationReceipt,
    validate_aether_air_snapshot,
    validate_aether_air_transformation,
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
    "AetherAirValidationReceipt",
    "AetherAirTransformationValidationReceipt",
    "validate_aether_air_snapshot",
    "validate_aether_air_transformation",
    "AetherAirDownstreamProjection",
    "project_validated_aether_air",
    "render_aether_air_downstream_projection_report",
)
