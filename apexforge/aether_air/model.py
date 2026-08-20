"""P11.9B immutable AETHER-AIR 2.0 interstitial core model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _value(value: Any, field: str) -> None:
    if type(value) in (str, int, float, bool, type(None)):
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _value(item, f"{field}[{index}]")
        return
    raise TypeError(f"{field} must be an immutable scalar or tuple")


@dataclass(frozen=True)
class AetherBehaviorKind:
    canonical_id: str

    def __post_init__(self) -> None:
        _text(self.canonical_id, "AetherBehaviorKind.canonical_id")


CORE_AETHER_BEHAVIOR_KINDS: Tuple[AetherBehaviorKind, ...] = tuple(
    AetherBehaviorKind(kind_id)
    for kind_id in (
        "behavior.intent",
        "transformation.intent",
        "constraint.intent",
        "projection.intent",
    )
)


@dataclass(frozen=True)
class AetherIntentParameter:
    key: str
    value: Any

    def __post_init__(self) -> None:
        _text(self.key, "AetherIntentParameter.key")
        _value(self.value, "AetherIntentParameter.value")


@dataclass(frozen=True)
class AetherBehaviorIntent:
    kind_id: str
    intent: str
    parameters: Tuple[AetherIntentParameter, ...] = ()

    def __post_init__(self) -> None:
        _text(self.kind_id, "AetherBehaviorIntent.kind_id")
        _text(self.intent, "AetherBehaviorIntent.intent")
        if type(self.parameters) is not tuple:
            raise TypeError("behavior-intent parameters must be an exact tuple")
        if any(type(item) is not AetherIntentParameter for item in self.parameters):
            raise TypeError(
                "behavior-intent parameters must contain exact "
                "AetherIntentParameter values"
            )


@dataclass(frozen=True)
class AetherAirRepresentation:
    behaviors: Tuple[AetherBehaviorIntent, ...] = ()

    def __post_init__(self) -> None:
        if type(self.behaviors) is not tuple:
            raise TypeError("AETHER-AIR behaviors must be an exact tuple")
        if any(type(item) is not AetherBehaviorIntent for item in self.behaviors):
            raise TypeError(
                "AETHER-AIR behaviors must contain exact "
                "AetherBehaviorIntent values"
            )


__all__ = (
    "AetherBehaviorKind",
    "AetherIntentParameter",
    "AetherBehaviorIntent",
    "AetherAirRepresentation",
    "CORE_AETHER_BEHAVIOR_KINDS",
)
