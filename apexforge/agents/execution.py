"""Explicit AgentPlan host-effect execution composition for P11.14O."""

from __future__ import annotations

from typing import Callable, Tuple

from effects.host_execution import (
    HostEffectExecutionRecord,
    execute_host_effect,
)
from effects.model import EffectIntent

from .plan_projection import project_agent_plan_effect_intents
from .planning import AgentPlan


def execute_agent_plan(
    plan: AgentPlan,
    handler: Callable[[EffectIntent], None],
) -> Tuple[HostEffectExecutionRecord, ...]:
    """Execute one agent plan through the frozen projection and host seam."""

    effect_intents = project_agent_plan_effect_intents(plan)

    if not callable(handler):
        raise TypeError("execute_agent_plan handler must be callable")

    records = []
    for effect_intent in effect_intents:
        records.append(execute_host_effect(effect_intent, handler))

    return tuple(records)


__all__ = ("execute_agent_plan",)