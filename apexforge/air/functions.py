"""Passive AIR models for AFP-P7 pure functions and local bindings."""

from __future__ import annotations

from dataclasses import dataclass

from air.expressions import AIRExpression


@dataclass(frozen=True, order=True)
class AIRParameter:
    name: str


@dataclass(frozen=True)
class AIRLocalBinding:
    """One ordered immutable local binding inside a pure function."""

    name: str
    expression: AIRExpression


@dataclass(frozen=True)
class AIRFunction:
    id: str
    name: str
    parameters: tuple[AIRParameter, ...]
    return_expression: AIRExpression
    order: int = 0
    # Added after existing fields so AFP-P7.1 constructors remain compatible.
    local_bindings: tuple[AIRLocalBinding, ...] = ()


__all__ = (
    "AIRFunction",
    "AIRLocalBinding",
    "AIRParameter",
)