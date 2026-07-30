"""Passive AIR models for AFP-P7 pure functions."""

from __future__ import annotations

from dataclasses import dataclass

from air.expressions import AIRExpression


@dataclass(frozen=True, order=True)
class AIRParameter:
    name: str


@dataclass(frozen=True)
class AIRFunction:
    id: str
    name: str
    parameters: tuple[AIRParameter, ...]
    return_expression: AIRExpression
    order: int = 0