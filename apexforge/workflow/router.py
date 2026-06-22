"""Workflow event router for ApexForge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Route:
    event: str
    target: str


class WorkflowRouter:
    def __init__(self, routes: Tuple[Route, ...]) -> None:
        self.routes: Dict[str, str] = {
            route.event: route.target
            for route in routes
        }

    def target_for(self, event: str) -> str | None:
        return self.routes.get(event)


GOVERNANCE_ROUTES = (
    Route("SentinelObservation", "AEGIS"),
    Route("AegisValidation", "Gravitas"),
)