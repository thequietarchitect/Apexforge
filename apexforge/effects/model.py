"""Passive host-effect descriptions.

The AIR runtime may return these intents but must never execute host effects
inside the deterministic runtime engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from air.model import Fact, sort_facts


@dataclass(frozen=True)
class EffectIntent:
    """A declarative request for an optional host-side effect."""

    id: str
    effect_type: str
    facts: Tuple[Fact, ...] = ()

    def __post_init__(
        self,
    ) -> None:
        if not isinstance(
            self.id,
            str,
        ) or not self.id:
            raise ValueError(
                "EffectIntent id must be a non-empty string."
            )

        if not isinstance(
            self.effect_type,
            str,
        ) or not self.effect_type:
            raise ValueError(
                "EffectIntent effect_type must be a non-empty string."
            )

        object.__setattr__(
            self,
            "facts",
            sort_facts(
                self.facts
            ),
        )