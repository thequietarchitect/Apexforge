"""Canonical ApexForge type identities.

This module defines language-level type identity only.

Parsing, type checking, conversion policy, AIR verification, runtime storage,
and host-language coercion do not belong here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Tuple, Union


@dataclass(frozen=True, order=True)
class ApexType:
    """Canonical structural identity for an ApexForge type.

    ``arguments`` remains empty throughout AFP-P8. It provides a stable
    extension point for applied generic types during AFP-P9 without requiring
    the built-in type representation to be replaced.
    """

    name: str
    arguments: Tuple["ApexType", ...] = ()

    def __post_init__(self) -> None:
        if type(self.name) is not str:
            raise TypeError(
                "ApexType.name must be a string; "
                f"received {type(self.name).__name__}."
            )

        if not self.name:
            raise ValueError("ApexType.name cannot be empty.")

        if not self.name.isidentifier():
            raise ValueError(
                "ApexType.name must be a valid identifier; "
                f"received {self.name!r}."
            )

        if type(self.arguments) is not tuple:
            raise TypeError(
                "ApexType.arguments must be a tuple; "
                f"received {type(self.arguments).__name__}."
            )

        for index, argument in enumerate(self.arguments):
            if not isinstance(argument, ApexType):
                raise TypeError(
                    "Every ApexType argument must be an ApexType; "
                    f"argument {index} received "
                    f"{type(argument).__name__}."
                )

    def __str__(self) -> str:
        if not self.arguments:
            return self.name

        rendered_arguments = ", ".join(
            str(argument)
            for argument in self.arguments
        )
        return f"{self.name}<{rendered_arguments}>"


# AFP-P8 canonical built-in type objects.
INT: Final[ApexType] = ApexType("int")
BOOL: Final[ApexType] = ApexType("bool")
STRING: Final[ApexType] = ApexType("string")
FLOAT: Final[ApexType] = ApexType("float")
VOID: Final[ApexType] = ApexType("void")


BUILTIN_TYPES: Final[Tuple[ApexType, ...]] = (
    INT,
    BOOL,
    STRING,
    FLOAT,
    VOID,
)


BUILTIN_TYPES_BY_NAME: Final[Mapping[str, ApexType]] = MappingProxyType(
    {
        apex_type.name: apex_type
        for apex_type in BUILTIN_TYPES
    }
)


TypeLike = Union[str, ApexType]


def resolve_builtin_type(
    value: TypeLike,
) -> ApexType:
    """Return the canonical built-in type represented by ``value``.

    A newly constructed ``ApexType("int")`` is normalized to the shared
    ``INT`` object. Applied types are deliberately rejected here because
    generic resolution belongs to AFP-P9.
    """

    if type(value) is str:
        name = value
    elif isinstance(value, ApexType):
        if value.arguments:
            raise ValueError(
                "Applied type cannot be resolved as an AFP-P8 built-in: "
                f"{value}."
            )
        name = value.name
    else:
        raise TypeError(
            "ApexForge type resolution requires a string or ApexType; "
            f"received {type(value).__name__}."
        )

    resolved = BUILTIN_TYPES_BY_NAME.get(name)
    if resolved is None:
        supported = ", ".join(
            apex_type.name
            for apex_type in BUILTIN_TYPES
        )
        raise ValueError(
            f"Unknown ApexForge built-in type {name!r}. "
            f"Supported types: {supported}."
        )

    return resolved


def is_builtin_type(
    value: object,
) -> bool:
    """Return whether ``value`` identifies an AFP-P8 built-in type."""

    try:
        resolve_builtin_type(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False

    return True


def is_void_type(
    value: object,
) -> bool:
    """Return whether ``value`` resolves to the canonical void type."""

    try:
        return resolve_builtin_type(value) is VOID  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


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