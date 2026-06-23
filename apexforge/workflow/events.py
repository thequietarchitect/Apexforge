"""Workflow event definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowEvent:
    name: str
    source: str


SENTINEL_OBSERVATION = WorkflowEvent(
    name="SentinelObservation",
    source="Sentinel",
)

AEGIS_VALIDATION = WorkflowEvent(
    name="AegisValidation",
    source="AEGIS",
)

GRAVITAS_RESPONSE = WorkflowEvent(
    name="Response",
    source="Gravitas",
)