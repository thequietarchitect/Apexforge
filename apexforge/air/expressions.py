"""ApexForge AIR expression definitions."""

from __future__ import annotations

from dataclasses import dataclass


class AIRExpression:
    """Base class for verified, runtime-evaluable AIR expressions."""

    pass


@dataclass(frozen=True)
class AIRIntegerLiteral(AIRExpression):
    value: int


@dataclass(frozen=True)
class AIRStringLiteral(AIRExpression):
    value: str


@dataclass(frozen=True)
class AIRBooleanLiteral(AIRExpression):
    value: bool


@dataclass(frozen=True)
class AIRIdentifierReference(AIRExpression):
    name: str


@dataclass(frozen=True)
class AIRUnaryExpression(AIRExpression):
    operator: str
    operand: AIRExpression


@dataclass(frozen=True)
class AIRBinaryExpression(AIRExpression):
    left: AIRExpression
    operator: str
    right: AIRExpression