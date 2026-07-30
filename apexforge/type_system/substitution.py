"""Immutable AFP-P9 generic type substitutions.

A substitution binds function-scoped ``ApexTypeVariable`` identities to the
exact type identities inferred at one call site. Bindings are deterministic,
immutable, and never introduce implicit conversions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    TypeIdentity,
    resolve_type,
)


class GenericSubstitutionConflict(ValueError):
    """Raised when one type variable receives incompatible inferred types."""

    def __init__(
        self,
        *,
        variable: ApexTypeVariable,
        existing: TypeIdentity,
        incoming: TypeIdentity,
    ) -> None:
        self.variable = variable
        self.existing = existing
        self.incoming = incoming
        super().__init__(
            f"Generic type {variable} is already bound to {existing}; "
            f"received incompatible {incoming}."
        )


@dataclass(frozen=True)
class GenericSubstitution:
    """One immutable, insertion-ordered generic substitution environment."""

    bindings: tuple[tuple[ApexTypeVariable, TypeIdentity], ...] = ()

    def __post_init__(self) -> None:
        if type(self.bindings) is not tuple:
            raise TypeError(
                "GenericSubstitution.bindings must be a tuple; "
                f"received {type(self.bindings).__name__}."
            )

        normalized: list[tuple[ApexTypeVariable, TypeIdentity]] = []
        seen: dict[ApexTypeVariable, TypeIdentity] = {}

        for binding in self.bindings:
            if type(binding) is not tuple or len(binding) != 2:
                raise TypeError(
                    "Each generic substitution binding must be a "
                    "(type_variable, type_identity) tuple."
                )

            variable, value_type = binding

            if not isinstance(variable, ApexTypeVariable):
                raise TypeError(
                    "Generic substitution keys must be ApexTypeVariable values."
                )

            resolved = resolve_type(value_type)
            existing = seen.get(variable)

            if existing is not None:
                if existing is not resolved:
                    raise GenericSubstitutionConflict(
                        variable=variable,
                        existing=existing,
                        incoming=resolved,
                    )
                continue

            seen[variable] = resolved
            normalized.append((variable, resolved))

        object.__setattr__(
            self,
            "bindings",
            tuple(normalized),
        )

    def contains(self, variable: ApexTypeVariable) -> bool:
        return any(
            existing is variable
            for existing, _ in self.bindings
        )

    def get(
        self,
        variable: ApexTypeVariable,
    ) -> Optional[TypeIdentity]:
        for existing, value_type in self.bindings:
            if existing is variable:
                return value_type
        return None

    def bind(
        self,
        variable: ApexTypeVariable,
        value_type: GenericTypeLike,
    ) -> "GenericSubstitution":
        if not isinstance(variable, ApexTypeVariable):
            raise TypeError(
                "GenericSubstitution.bind requires an ApexTypeVariable key."
            )

        resolved = resolve_type(value_type)
        existing = self.get(variable)

        if existing is not None:
            if existing is not resolved:
                raise GenericSubstitutionConflict(
                    variable=variable,
                    existing=existing,
                    incoming=resolved,
                )
            return self

        return type(self)(
            self.bindings + ((variable, resolved),)
        )

    def resolve(
        self,
        value_type: GenericTypeLike,
    ) -> TypeIdentity:
        resolved = resolve_type(value_type)

        if not isinstance(resolved, ApexTypeVariable):
            return resolved

        replacement = self.get(resolved)
        if replacement is None or replacement is resolved:
            return resolved

        # Follow a short substitution chain while defending against malformed
        # cyclic hand-authored environments.
        visited: set[int] = {id(resolved)}
        current = replacement

        while isinstance(current, ApexTypeVariable):
            if id(current) in visited:
                return current
            visited.add(id(current))

            nested = self.get(current)
            if nested is None or nested is current:
                return current
            current = nested

        return current

    def unresolved(
        self,
        variables: Iterable[ApexTypeVariable],
    ) -> tuple[ApexTypeVariable, ...]:
        return tuple(
            variable
            for variable in tuple(variables)
            if not self.contains(variable)
        )

    def as_mapping(
        self,
    ) -> dict[ApexTypeVariable, TypeIdentity]:
        return dict(self.bindings)


__all__ = (
    "GenericSubstitution",
    "GenericSubstitutionConflict",
)