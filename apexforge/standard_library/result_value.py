"""Passive AFP-P10.6 structured-result runtime value.

The value model is deliberately isolated from ``runtime`` package imports so
standard-library initialization cannot enter runtime validation recursively.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from standard_library.diagnostic_value import RuntimeDiagnostic
from standard_library.random_value import RuntimeRandom
from standard_library.time_value import RuntimeTime
from standard_library.type_info_value import RuntimeTypeInfo
from type_system.model import (
    BOOL,
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


def _value_matches_type(value: Any, value_type: ApexType) -> bool:
    if value_type is INT:
        return type(value) is int
    if value_type is FLOAT:
        return type(value) is float
    if value_type is BOOL:
        return type(value) is bool
    if value_type is STRING:
        return type(value) is str
    if value_type is DIAGNOSTIC:
        return type(value) is RuntimeDiagnostic
    if value_type is TIME:
        return type(value) is RuntimeTime
    if value_type is RANDOM:
        return type(value) is RuntimeRandom
    if value_type is TYPE_INFO:
        return type(value) is RuntimeTypeInfo
    return False


@dataclass(frozen=True)
class RuntimeResult:
    """One immutable success value or deterministic failure description."""

    payload_type: ApexType
    ok: bool
    value: Any = None
    error_code: str = ""
    error_message: str = ""

    def __post_init__(self) -> None:
        payload_type = resolve_builtin_type(self.payload_type)
        if payload_type in {VOID, RESULT}:
            raise ValueError(
                "RuntimeResult payload_type must be a concrete non-result "
                "ApexForge value type."
            )
        object.__setattr__(self, "payload_type", payload_type)

        if type(self.ok) is not bool:
            raise TypeError("RuntimeResult.ok must be bool.")
        if type(self.error_code) is not str:
            raise TypeError("RuntimeResult.error_code must be string.")
        if type(self.error_message) is not str:
            raise TypeError("RuntimeResult.error_message must be string.")

        if self.ok:
            if not _value_matches_type(self.value, payload_type):
                raise TypeError(
                    "Successful RuntimeResult value must exactly match "
                    f"{payload_type}; received {type(self.value).__name__}."
                )
            if self.error_code or self.error_message:
                raise ValueError(
                    "Successful RuntimeResult cannot contain failure data."
                )
            return

        if self.value is not None:
            raise ValueError("Failed RuntimeResult cannot contain a value.")
        if not self.error_code:
            raise ValueError(
                "Failed RuntimeResult requires a non-empty error_code."
            )
        if not self.error_code.isidentifier():
            raise ValueError(
                "RuntimeResult.error_code must be an identifier-like string."
            )
        if not self.error_message:
            raise ValueError(
                "Failed RuntimeResult requires a non-empty error_message."
            )

    @classmethod
    def success(
        cls,
        payload_type: ApexType,
        value: Any,
    ) -> "RuntimeResult":
        return cls(
            payload_type=payload_type,
            ok=True,
            value=value,
        )

    @classmethod
    def failure(
        cls,
        payload_type: ApexType,
        *,
        code: str,
        message: str,
    ) -> "RuntimeResult":
        return cls(
            payload_type=payload_type,
            ok=False,
            error_code=code,
            error_message=message,
        )

    @property
    def is_error(self) -> bool:
        return not self.ok


__all__ = ("RuntimeResult",)