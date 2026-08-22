"""Explicit reusable host-effect execution seam for P11.14M."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from effects.model import EffectIntent


@dataclass(frozen=True)
class HostEffectExecutionRecord:
    """Immutable evidence that one supplied host-effect handler returned."""

    intent: EffectIntent

    def __post_init__(self) -> None:
        if type(self.intent) is not EffectIntent:
            raise TypeError(
                "HostEffectExecutionRecord.intent must be an exact EffectIntent"
            )


def execute_host_effect(
    intent: EffectIntent,
    handler: Callable[[EffectIntent], None],
) -> HostEffectExecutionRecord:
    """Invoke one explicit caller-supplied host-effect handler exactly once."""

    if type(intent) is not EffectIntent:
        raise TypeError("execute_host_effect requires an exact EffectIntent")
    if not callable(handler):
        raise TypeError("execute_host_effect handler must be callable")

    handler(intent)

    return HostEffectExecutionRecord(intent=intent)


__all__ = (
    "HostEffectExecutionRecord",
    "execute_host_effect",
)