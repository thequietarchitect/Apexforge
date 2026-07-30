"""ApexForge AIR expression definitions."""

from __future__ import annotations

from dataclasses import dataclass

from type_system.generics import GenericTypeLike, resolve_type


class AIRExpression:
    """Base class for verified, runtime-evaluable AIR expressions."""

    pass


@dataclass(frozen=True)
class AIRIntegerLiteral(AIRExpression):
    value: int


@dataclass(frozen=True)
class AIRFloatLiteral(AIRExpression):
    value: float


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


@dataclass(frozen=True)
class AIRCallExpression(AIRExpression):
    """A pure function call evaluated inside an immutable call frame."""

    target: str
    arguments: tuple[AIRExpression, ...] = ()
    # Runtime-erased metadata appended for constructor compatibility.
    type_arguments: tuple[GenericTypeLike, ...] = ()

    def __post_init__(self) -> None:
        if type(self.type_arguments) is not tuple:
            raise TypeError(
                "AIRCallExpression.type_arguments must be a tuple; "
                f"received {type(self.type_arguments).__name__}."
            )
        object.__setattr__(
            self,
            "type_arguments",
            tuple(resolve_type(value_type) for value_type in self.type_arguments),
        )