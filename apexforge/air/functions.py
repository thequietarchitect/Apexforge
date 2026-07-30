"""Passive AIR models for AFP-P7 pure-function control flow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from air.expressions import AIRExpression
from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    is_type_variable,
    resolve_type,
)


@dataclass(frozen=True, order=True)
class AIRParameter:
    name: str
    # ``None`` preserves the meaning of legacy P7 source that supplied no
    # parameter annotation. Typed P8 parameters are normalized canonically.
    value_type: Optional[GenericTypeLike] = None

    def __post_init__(self) -> None:
        if self.value_type is None:
            return

        object.__setattr__(
            self,
            "value_type",
            resolve_type(self.value_type),
        )


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
    # Appended so every P7 positional constructor remains source-compatible.
    # ``None`` means the legacy source supplied no return annotation.
    return_type: Optional[GenericTypeLike] = None
    # Appended so every P7/P8 positional constructor remains compatible.
    type_parameters: tuple[ApexTypeVariable, ...] = ()

    def __post_init__(self) -> None:
        normalized_parameters = tuple(self.type_parameters)
        seen: set[str] = set()
        for parameter in normalized_parameters:
            if not is_type_variable(parameter):
                raise TypeError(
                    "AIRFunction.type_parameters must contain "
                    "ApexTypeVariable values."
                )
            if parameter.name in seen:
                raise ValueError(
                    f"Duplicate AIR generic type parameter {parameter.name!r}."
                )
            seen.add(parameter.name)

        object.__setattr__(
            self,
            "type_parameters",
            normalized_parameters,
        )

        if self.return_type is not None:
            object.__setattr__(
                self,
                "return_type",
                resolve_type(self.return_type),
            )


__all__ = (
    "AIRFunction",
    "AIRFunctionReturn",
    "AIRFunctionWhen",
    "AIRLocalBinding",
    "AIRParameter",
)