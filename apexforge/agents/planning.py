"""Minimal immutable agent planning model for P11.14G."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from effects.model import EffectIntent

from .model import AgentDefinition


@dataclass(frozen=True)
class AgentPlan:
    """Ordered passive host-effect intents owned by one AgentDefinition."""

    definition: AgentDefinition
    effect_intents: Tuple[EffectIntent, ...] = ()

    def __post_init__(self) -> None:
        if type(self.definition) is not AgentDefinition:
            raise TypeError(
                "AgentPlan.definition must be an exact AgentDefinition"
            )

        if type(self.effect_intents) is not tuple:
            raise TypeError(
                "AgentPlan.effect_intents must be an exact tuple"
            )

        seen_ids = set()
        for index, effect_intent in enumerate(self.effect_intents):
            if type(effect_intent) is not EffectIntent:
                raise TypeError(
                    "AgentPlan.effect_intents item {} must be an exact "
                    "EffectIntent".format(index)
                )

            effect_id = effect_intent.id
            if effect_id in seen_ids:
                raise ValueError(
                    "AgentPlan.effect_intents must not contain duplicate "
                    "EffectIntent.id values"
                )
            seen_ids.add(effect_id)


__all__ = ("AgentPlan",)