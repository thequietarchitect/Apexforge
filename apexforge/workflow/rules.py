"""Workflow context rules for ApexForge directive chaining."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from workflow.context import WorkflowContext


@dataclass(frozen=True)
class ContextRule:
    name: str
    requires: Tuple[str, ...]
    produces: Tuple[str, ...]

    def is_satisfied(self, context: WorkflowContext) -> bool:
        return all(key in context.states for key in self.requires)


SENTINEL_RULE = ContextRule(
    name="Sentinel",
    requires=(),
    produces=("state:Awareness",),
)

AEGIS_RULE = ContextRule(
    name="AEGIS",
    requires=("state:Awareness",),
    produces=("state:Integrity",),
)

GRAVITAS_RULE = ContextRule(
    name="Gravitas",
    requires=("state:Awareness", "state:Integrity"),
    produces=("state:Vigilance",),
)


GOVERNANCE_RULES = {
    "Sentinel": SENTINEL_RULE,
    "AEGIS": AEGIS_RULE,
    "Gravitas": GRAVITAS_RULE,
}