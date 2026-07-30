"""Canonical ApexForge type-system declarations."""

from type_system.model import (
    ApexType,
    BOOL,
    BUILTIN_TYPES,
    BUILTIN_TYPES_BY_NAME,
    FLOAT,
    INT,
    STRING,
    TypeLike,
    VOID,
    is_builtin_type,
    is_void_type,
    resolve_builtin_type,
)


__all__ = (
    "ApexType",
    "BOOL",
    "BUILTIN_TYPES",
    "BUILTIN_TYPES_BY_NAME",
    "FLOAT",
    "INT",
    "STRING",
    "TypeLike",
    "VOID",
    "is_builtin_type",
    "is_void_type",
    "resolve_builtin_type",
)