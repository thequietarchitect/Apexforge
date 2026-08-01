"""Passive AFP-P10.7 immutable collection runtime value.

The value model is isolated from ``runtime`` package imports so standard-library
initialization remains acyclic. Collections retain one exact element type even
when empty and store values in an immutable tuple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from standard_library.diagnostic_value import RuntimeDiagnostic
from standard_library.random_value import RuntimeRandom
from standard_library.result_value import RuntimeResult
from standard_library.time_value import RuntimeTime
from standard_library.type_info_value import RuntimeTypeInfo
from type_system.model import (
    BOOL,
    COLLECTION,
    DIAGNOSTIC,
    FLOAT,
    INT,
    RESULT,
    RANDOM,
    STRING,
    TIME,
    TYPE_INFO,
    VOID,
    ApexType,
    resolve_builtin_type,
)


MAX_COLLECTION_LENGTH = 4096


def runtime_value_type(value: Any) -> ApexType | None:
    """Project one exact supported runtime value to its ApexForge type."""

    if type(value) is int:
        return INT
    if type(value) is float:
        return FLOAT
    if type(value) is bool:
        return BOOL
    if type(value) is str:
        return STRING
    if type(value) is RuntimeResult:
        return RESULT
    if type(value) is RuntimeDiagnostic:
        return DIAGNOSTIC
    if type(value) is RuntimeCollection:
        return COLLECTION
    if type(value) is RuntimeTime:
        return TIME
    if type(value) is RuntimeRandom:
        return RANDOM
    if type(value) is RuntimeTypeInfo:
        return TYPE_INFO
    return None


def value_matches_type(value: Any, value_type: ApexType) -> bool:
    """Return whether ``value`` exactly matches one non-void built-in type."""

    return runtime_value_type(value) is value_type


@dataclass(frozen=True)
class RuntimeCollection:
    """One immutable, homogeneous collection with a retained element type."""

    element_type: ApexType
    values: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        element_type = resolve_builtin_type(self.element_type)
        if element_type is VOID:
            raise ValueError(
                "RuntimeCollection.element_type cannot be void."
            )
        object.__setattr__(self, "element_type", element_type)

        if type(self.values) is not tuple:
            raise TypeError("RuntimeCollection.values must be a tuple.")
        if len(self.values) > MAX_COLLECTION_LENGTH:
            raise ValueError(
                "RuntimeCollection exceeds the 4096-element limit."
            )

        for index, value in enumerate(self.values):
            if not value_matches_type(value, element_type):
                actual = runtime_value_type(value)
                actual_name = (
                    actual.name
                    if actual is not None
                    else type(value).__name__
                )
                raise TypeError(
                    "RuntimeCollection values must exactly match "
                    f"{element_type}; item[{index}] was {actual_name}."
                )

    @classmethod
    def from_values(
        cls,
        values: Iterable[Any],
        *,
        element_type: ApexType | None = None,
    ) -> "RuntimeCollection":
        """Construct from values, inferring the exact type when non-empty."""

        if isinstance(values, (str, bytes)):
            raise TypeError(
                "RuntimeCollection.from_values requires an iterable of values, "
                "not text."
            )
        items = tuple(values)
        resolved = element_type

        if resolved is None:
            if not items:
                raise ValueError(
                    "An empty RuntimeCollection requires element_type."
                )
            resolved = runtime_value_type(items[0])
            if resolved is None or resolved is VOID:
                raise TypeError(
                    "RuntimeCollection received an unsupported element type."
                )

        return cls(
            element_type=resolve_builtin_type(resolved),
            values=items,
        )

    @property
    def length(self) -> int:
        return len(self.values)

    @property
    def is_empty(self) -> bool:
        return not self.values


__all__ = (
    "MAX_COLLECTION_LENGTH",
    "RuntimeCollection",
    "runtime_value_type",
    "value_matches_type",
)