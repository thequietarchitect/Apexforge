"""Passive AFP-P10.11 safe type-information runtime value.

``RuntimeTypeInfo`` exposes only canonical ApexForge type identity. It does not
retain Python classes, modules, source locations, memory addresses, callable
objects, or mutable runtime handles.
"""

from __future__ import annotations

from dataclasses import dataclass

from type_system.model import (
    BOOL,
    COLLECTION,
    DIAGNOSTIC,
    FLOAT,
    INT,
    RANDOM,
    RESULT,
    STRING,
    TIME,
    VOID,
    ApexType,
    BUILTIN_TYPES,
    resolve_builtin_type,
)


_PRIMITIVE_TYPES = frozenset((INT, BOOL, STRING, FLOAT))
_NUMERIC_TYPES = frozenset((INT, FLOAT))
_CONTAINER_TYPES = frozenset((RESULT, COLLECTION))


@dataclass(frozen=True)
class RuntimeTypeInfo:
    """One immutable reference to a canonical ApexForge built-in type."""

    value_type: ApexType

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value_type",
            resolve_builtin_type(self.value_type),
        )

    @property
    def name(self) -> str:
        return self.value_type.name

    @property
    def order(self) -> int:
        return BUILTIN_TYPES.index(self.value_type)

    @property
    def is_primitive(self) -> bool:
        return self.value_type in _PRIMITIVE_TYPES

    @property
    def is_numeric(self) -> bool:
        return self.value_type in _NUMERIC_TYPES

    @property
    def is_container(self) -> bool:
        return self.value_type in _CONTAINER_TYPES

    @property
    def is_void(self) -> bool:
        return self.value_type is VOID

    @property
    def is_opaque(self) -> bool:
        return not self.is_primitive and not self.is_void

    @property
    def is_runtime_value(self) -> bool:
        return not self.is_void

    def render(self) -> str:
        return self.name


__all__ = ("RuntimeTypeInfo",)