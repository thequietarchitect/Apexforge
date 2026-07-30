"""Canonical AFP-P9 generic type identities.

This module extends the frozen AFP-P8 built-in type model without changing its
semantics. Generic type variables are declaration-scoped symbolic identities;
they are not runtime values and are not implicitly interchangeable with any
built-in type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from type_system.constraints import (
    ApexTypeConstraint,
    ConstraintLike,
    builtin_type_satisfies_constraint,
    resolve_type_constraint,
)
from type_system.model import ApexType, TypeLike, is_builtin_type, resolve_builtin_type


@dataclass(frozen=True, order=True)
class ApexTypeVariable:
    """One immutable function-scoped generic type parameter."""

    name: str
    owner: str
    # Appended so AFP-P9.1 through P9.3 constructors remain compatible.
    constraints: tuple[ConstraintLike, ...] = ()

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise ValueError("ApexTypeVariable.name must be a non-empty string.")
        if not self.name.isidentifier():
            raise ValueError(
                f"ApexTypeVariable name {self.name!r} is not a valid identifier."
            )
        if type(self.owner) is not str or not self.owner:
            raise ValueError("ApexTypeVariable.owner must be a non-empty string.")
        if is_builtin_type(self.name):
            raise ValueError(
                f"Generic type parameter {self.name!r} cannot shadow a built-in type."
            )
        if type(self.constraints) is not tuple:
            raise TypeError(
                "ApexTypeVariable.constraints must be a tuple; "
                f"received {type(self.constraints).__name__}."
            )

        normalized: list[ApexTypeConstraint] = []
        seen: set[str] = set()
        for constraint in self.constraints:
            resolved = resolve_type_constraint(constraint)
            if resolved.name in seen:
                raise ValueError(
                    f"Generic type parameter {self.name!r} declares duplicate "
                    f"constraint {resolved.name!r}."
                )
            normalized.append(resolved)
            seen.add(resolved.name)

        object.__setattr__(self, "constraints", tuple(normalized))

    def __str__(self) -> str:
        return self.name


TypeIdentity = Union[ApexType, ApexTypeVariable]
GenericTypeLike = Union[TypeLike, ApexTypeVariable]


def resolve_type(value: GenericTypeLike) -> TypeIdentity:
    """Resolve a built-in type or preserve a canonical type variable."""

    if isinstance(value, ApexTypeVariable):
        return value
    return resolve_builtin_type(value)


def is_type_variable(value: object) -> bool:
    return isinstance(value, ApexTypeVariable)


def type_satisfies_constraint(
    value_type: GenericTypeLike,
    constraint: ConstraintLike,
) -> bool:
    """Return whether a built-in or generic identity proves a capability."""

    resolved_type = resolve_type(value_type)
    resolved_constraint = resolve_type_constraint(constraint)

    if isinstance(resolved_type, ApexTypeVariable):
        return any(
            declared is resolved_constraint
            for declared in resolved_type.constraints
        )

    return builtin_type_satisfies_constraint(
        resolved_type,
        resolved_constraint,
    )


def type_satisfies_constraints(
    value_type: GenericTypeLike,
    constraints: tuple[ConstraintLike, ...],
) -> bool:
    return all(
        type_satisfies_constraint(value_type, constraint)
        for constraint in constraints
    )


__all__ = (
    "ApexTypeVariable",
    "GenericTypeLike",
    "TypeIdentity",
    "is_type_variable",
    "resolve_type",
    "type_satisfies_constraint",
    "type_satisfies_constraints",
)