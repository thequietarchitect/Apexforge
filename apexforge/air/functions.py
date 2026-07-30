"""Passive AIR models for AFP-P7 pure-function control flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

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
class AIRFunctionReturn:
    """Return one expression from a pure function body."""

    expression: AIRExpression


@dataclass(frozen=True)
class AIRFunctionWhen:
    """Pure function conditional with lexically scoped branch bodies."""

    condition: AIRExpression
    actions: tuple[object, ...]
    otherwise_actions: tuple[object, ...] = ()


@dataclass(frozen=True)
class AIRFunction:
    id: str
    name: str
    parameters: tuple[AIRParameter, ...]
    # Legacy P7.1 projection retained for compatibility. New runtimes prefer
    # ``body`` whenever it is non-empty.
    return_expression: Optional[AIRExpression]
    order: int = 0
    local_bindings: tuple[AIRLocalBinding, ...] = ()
    body: tuple[object, ...] = ()


__all__ = (
    "AIRFunction",
    "AIRFunctionReturn",
    "AIRFunctionWhen",
    "AIRLocalBinding",
    "AIRParameter",
)