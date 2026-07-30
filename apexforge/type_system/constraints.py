"""Canonical AFP-P9.4 generic constraint capabilities.

Constraints are compile-time type capabilities. They never become runtime
values and they do not introduce implicit conversions or subtyping between
ApexForge's frozen built-in types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from type_system.model import ApexType, FLOAT, INT


@dataclass(frozen=True, order=True)
class ApexTypeConstraint:
    """One immutable language-level generic capability."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError(
                "ApexTypeConstraint.name must be a non-empty string."
            )
        if not self.name.isidentifier():
            raise ValueError(
                f"Constraint name {self.name!r} is not a valid identifier."
            )
        if type(self.description) is not str:
            raise TypeError(
                "ApexTypeConstraint.description must be a string."
            )

    def __str__(self) -> str:
        return self.name


NUMERIC = ApexTypeConstraint(
    name="numeric",
    description=(
        "Supports ApexForge numeric unary, arithmetic, remainder, and "
        "ordering operators without implicit conversion."
    ),
)

_BUILTIN_CONSTRAINTS = {
    NUMERIC.name: NUMERIC,
}

ConstraintLike = Union[str, ApexTypeConstraint]


def resolve_type_constraint(value: ConstraintLike) -> ApexTypeConstraint:
    """Resolve one canonical built-in generic constraint."""

    if isinstance(value, ApexTypeConstraint):
        canonical = _BUILTIN_CONSTRAINTS.get(value.name)
        if canonical is value:
            return value
        if canonical == value:
            return canonical
        raise ValueError(
            f"Unknown ApexForge type constraint {value.name!r}."
        )

    if type(value) is not str:
        raise TypeError(
            "ApexForge type constraints must be names or "
            "ApexTypeConstraint values."
        )

    try:
        return _BUILTIN_CONSTRAINTS[value]
    except KeyError as exc:
        raise ValueError(
            f"Unknown ApexForge type constraint {value!r}."
        ) from exc


def is_type_constraint(value: object) -> bool:
    try:
        resolve_type_constraint(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True


def builtin_type_satisfies_constraint(
    value_type: ApexType,
    constraint: ConstraintLike,
) -> bool:
    """Return whether one frozen built-in type has a capability."""

    resolved_constraint = resolve_type_constraint(constraint)

    if resolved_constraint is NUMERIC:
        return value_type in {INT, FLOAT}

    return False


__all__ = (
    "ApexTypeConstraint",
    "ConstraintLike",
    "NUMERIC",
    "builtin_type_satisfies_constraint",
    "is_type_constraint",
    "resolve_type_constraint",
)