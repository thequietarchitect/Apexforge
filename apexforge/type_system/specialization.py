"""Canonical AFP-P9.5 generic specialization records.

A specialization records one generic function together with the exact type
arguments resolved for a call site. Records are compile-time identities only;
ApexForge continues to execute generic functions through the existing erased
P7 call-frame runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    TypeIdentity,
    resolve_type,
)


def _encode_type_identity(value_type: TypeIdentity) -> str:
    """Encode one type identity without collapsing declaration ownership."""

    if isinstance(value_type, ApexTypeVariable):
        return f"{value_type.owner}::{value_type.name}"
    return value_type.name


@dataclass(frozen=True, order=True)
class GenericSpecializationKey:
    """Stable key for one generic function/type-argument combination."""

    target: str
    type_arguments: tuple[GenericTypeLike, ...]

    def __post_init__(self) -> None:
        if type(self.target) is not str or not self.target:
            raise ValueError(
                "GenericSpecializationKey.target must be a non-empty string."
            )
        if type(self.type_arguments) is not tuple:
            raise TypeError(
                "GenericSpecializationKey.type_arguments must be a tuple; "
                f"received {type(self.type_arguments).__name__}."
            )
        if not self.type_arguments:
            raise ValueError(
                "GenericSpecializationKey requires at least one type argument."
            )

        object.__setattr__(
            self,
            "type_arguments",
            tuple(resolve_type(value_type) for value_type in self.type_arguments),
        )

    @property
    def canonical_id(self) -> str:
        encoded = ",".join(
            _encode_type_identity(value_type)
            for value_type in self.type_arguments
        )
        return f"{self.target}<{encoded}>"

    @property
    def is_closed(self) -> bool:
        return not any(
            isinstance(value_type, ApexTypeVariable)
            for value_type in self.type_arguments
        )

    def __str__(self) -> str:
        return self.canonical_id


@dataclass(frozen=True)
class GenericSpecialization:
    """One immutable resolved generic signature projection."""

    key: GenericSpecializationKey
    parameter_types: tuple[Optional[GenericTypeLike], ...]
    return_type: Optional[GenericTypeLike]

    def __post_init__(self) -> None:
        if not isinstance(self.key, GenericSpecializationKey):
            raise TypeError(
                "GenericSpecialization.key must be GenericSpecializationKey."
            )
        if type(self.parameter_types) is not tuple:
            raise TypeError(
                "GenericSpecialization.parameter_types must be a tuple; "
                f"received {type(self.parameter_types).__name__}."
            )

        object.__setattr__(
            self,
            "parameter_types",
            tuple(
                None if value_type is None else resolve_type(value_type)
                for value_type in self.parameter_types
            ),
        )
        object.__setattr__(
            self,
            "return_type",
            None if self.return_type is None else resolve_type(self.return_type),
        )

    @property
    def canonical_id(self) -> str:
        return self.key.canonical_id

    @property
    def type_arguments(self) -> tuple[TypeIdentity, ...]:
        return self.key.type_arguments

    @property
    def is_closed(self) -> bool:
        if not self.key.is_closed:
            return False
        if any(
            isinstance(value_type, ApexTypeVariable)
            for value_type in self.parameter_types
            if value_type is not None
        ):
            return False
        return not isinstance(self.return_type, ApexTypeVariable)


class OpenGenericSpecializationError(ValueError):
    """Raised when an open specialization is placed in an instantiation table."""


class GenericSpecializationConflict(ValueError):
    """Raised when one canonical key is paired with conflicting projections."""


@dataclass(frozen=True)
class GenericInstantiationTable:
    """Immutable, canonical-order table of closed generic specializations."""

    records: tuple[GenericSpecialization, ...] = ()

    def __post_init__(self) -> None:
        if type(self.records) is not tuple:
            raise TypeError(
                "GenericInstantiationTable.records must be a tuple; "
                f"received {type(self.records).__name__}."
            )

        by_id: dict[str, GenericSpecialization] = {}
        for record in self.records:
            if not isinstance(record, GenericSpecialization):
                raise TypeError(
                    "GenericInstantiationTable records must be "
                    "GenericSpecialization values."
                )
            if not record.is_closed:
                raise OpenGenericSpecializationError(
                    f"Open specialization {record.canonical_id!r} cannot be "
                    "registered as a concrete instantiation."
                )

            existing = by_id.get(record.canonical_id)
            if existing is not None and existing != record:
                raise GenericSpecializationConflict(
                    f"Specialization key {record.canonical_id!r} has "
                    "conflicting signature projections."
                )
            by_id[record.canonical_id] = record

        object.__setattr__(
            self,
            "records",
            tuple(by_id[key] for key in sorted(by_id)),
        )

    def register(
        self,
        record: GenericSpecialization,
    ) -> "GenericInstantiationTable":
        if not isinstance(record, GenericSpecialization):
            raise TypeError(
                "GenericInstantiationTable.register requires "
                "GenericSpecialization."
            )

        for existing in self.records:
            if existing.canonical_id != record.canonical_id:
                continue
            if existing != record:
                raise GenericSpecializationConflict(
                    f"Specialization key {record.canonical_id!r} has "
                    "conflicting signature projections."
                )
            return self

        return type(self)(self.records + (record,))

    def get(self, canonical_id: str) -> Optional[GenericSpecialization]:
        if type(canonical_id) is not str or not canonical_id:
            raise ValueError("canonical_id must be a non-empty string.")

        for record in self.records:
            if record.canonical_id == canonical_id:
                return record
        return None

    def __len__(self) -> int:
        return len(self.records)


__all__ = (
    "GenericInstantiationTable",
    "GenericSpecialization",
    "GenericSpecializationConflict",
    "GenericSpecializationKey",
    "OpenGenericSpecializationError",
)