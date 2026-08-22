"""Pure projection from a frozen agent plan for P11.14J."""

from __future__ import annotations

from typing import Tuple

from effects.model import EffectIntent

from .planning import AgentPlan


def project_agent_plan_effect_intents(
    plan: AgentPlan,
) -> Tuple[EffectIntent, ...]:
    """Return the exact ordered effect-intent tuple carried by one AgentPlan."""

    if type(plan) is not AgentPlan:
        raise TypeError(
            "project_agent_plan_effect_intents requires an exact AgentPlan"
        )

    return plan.effect_intents


__all__ = ("project_agent_plan_effect_intents",)