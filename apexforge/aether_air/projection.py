"""P11.9G explicit passive downstream projection boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union

from .validation import (
    AetherAirTransformationValidationReceipt,
    AetherAirValidationReceipt,
)


AetherAirValidation = Union[
    AetherAirValidationReceipt,
    AetherAirTransformationValidationReceipt,
]


def _require_validation(value: object) -> None:
    if type(value) not in (
        AetherAirValidationReceipt,
        AetherAirTransformationValidationReceipt,
    ):
        raise TypeError(
            "validation must be an exact AetherAirValidationReceipt or "
            "AetherAirTransformationValidationReceipt"
)


def _require_text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _require_provenance(value: object) -> None:
    if type(value) is not tuple:
        raise TypeError("provenance must be an exact tuple")
    for index, item in enumerate(value):
        _require_text(item, f"provenance[{index}]")


@dataclass(frozen=True)
class AetherAirDownstreamProjection:
    """Immutable passive handoff of validated AETHER-AIR toward a named consumer."""

    validation: AetherAirValidation
    consumer: str
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_validation(self.validation)
        _require_text(self.consumer, "consumer")
        _require_provenance(self.provenance)


def project_validated_aether_air(
    validation: AetherAirValidation,
    *,
    consumer: str,
    provenance: Tuple[str, ...] = (),
) -> AetherAirDownstreamProjection:
    """Record an explicit downstream handoff without lowering or execution."""

    return AetherAirDownstreamProjection(
        validation=validation,
        consumer=consumer,
        provenance=provenance,
    )


__all__ = (
    "AetherAirDownstreamProjection",
    "project_validated_aether_air",
)
