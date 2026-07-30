"""AFP-P10.2 deterministic numeric standard-library functions.

This module extends the pure P10 registry with exact integer and float
utilities. It introduces no implicit conversion, mutation, I/O, time access,
randomness, or other host effect.
"""

from __future__ import annotations

import math

from standard_library.model import (
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from type_system.inference import FunctionSignature
from type_system.model import BOOL, FLOAT, INT


def _domain_error(function_name: str, message: str) -> None:
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-005",
        message=(
            f"Standard-library function {function_name!r} received "
            f"an invalid numeric domain: {message}"
        ),
    )


def _int_min(left: int, right: int) -> int:
    return left if left <= right else right


def _int_max(left: int, right: int) -> int:
    return left if left >= right else right


def _int_clamp(value: int, lower: int, upper: int) -> int:
    if lower > upper:
        _domain_error(
            "int_clamp",
            f"lower bound {lower} exceeds upper bound {upper}.",
        )
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def _int_sign(value: int) -> int:
    if value < 0:
        return -1
    if value > 0:
        return 1
    return 0


def _int_is_even(value: int) -> bool:
    return value % 2 == 0


def _int_is_odd(value: int) -> bool:
    return value % 2 != 0


def _require_ordered_float(function_name: str, *values: float) -> None:
    for index, value in enumerate(values):
        if math.isnan(value):
            _domain_error(
                function_name,
                f"argument {index} is NaN and cannot be ordered.",
            )


def _float_min(left: float, right: float) -> float:
    _require_ordered_float("float_min", left, right)
    return left if left <= right else right


def _float_max(left: float, right: float) -> float:
    _require_ordered_float("float_max", left, right)
    return left if left >= right else right


def _float_clamp(value: float, lower: float, upper: float) -> float:
    _require_ordered_float("float_clamp", value, lower, upper)
    if lower > upper:
        _domain_error(
            "float_clamp",
            f"lower bound {lower} exceeds upper bound {upper}.",
        )
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def _float_sign(value: float) -> int:
    _require_ordered_float("float_sign", value)
    if value < 0.0:
        return -1
    if value > 0.0:
        return 1
    return 0


def _float_is_finite(value: float) -> bool:
    return math.isfinite(value)


NUMERIC_BUILTINS = (
    BuiltinFunction(
        name="int_min",
        signature=FunctionSignature(
            name="int_min",
            parameter_types=(INT, INT),
            return_type=INT,
        ),
        implementation=_int_min,
        documentation="Return the lesser of two exact ints.",
    ),
    BuiltinFunction(
        name="int_max",
        signature=FunctionSignature(
            name="int_max",
            parameter_types=(INT, INT),
            return_type=INT,
        ),
        implementation=_int_max,
        documentation="Return the greater of two exact ints.",
    ),
    BuiltinFunction(
        name="int_clamp",
        signature=FunctionSignature(
            name="int_clamp",
            parameter_types=(INT, INT, INT),
            return_type=INT,
        ),
        implementation=_int_clamp,
        documentation=(
            "Clamp an int to inclusive lower and upper bounds; lower must "
            "not exceed upper."
        ),
    ),
    BuiltinFunction(
        name="int_sign",
        signature=FunctionSignature(
            name="int_sign",
            parameter_types=(INT,),
            return_type=INT,
        ),
        implementation=_int_sign,
        documentation="Return -1, 0, or 1 according to an int's sign.",
    ),
    BuiltinFunction(
        name="int_is_even",
        signature=FunctionSignature(
            name="int_is_even",
            parameter_types=(INT,),
            return_type=BOOL,
        ),
        implementation=_int_is_even,
        documentation="Return whether an int is evenly divisible by two.",
    ),
    BuiltinFunction(
        name="int_is_odd",
        signature=FunctionSignature(
            name="int_is_odd",
            parameter_types=(INT,),
            return_type=BOOL,
        ),
        implementation=_int_is_odd,
        documentation="Return whether an int is not evenly divisible by two.",
    ),
    BuiltinFunction(
        name="float_min",
        signature=FunctionSignature(
            name="float_min",
            parameter_types=(FLOAT, FLOAT),
            return_type=FLOAT,
        ),
        implementation=_float_min,
        documentation="Return the lesser of two ordered floats.",
    ),
    BuiltinFunction(
        name="float_max",
        signature=FunctionSignature(
            name="float_max",
            parameter_types=(FLOAT, FLOAT),
            return_type=FLOAT,
        ),
        implementation=_float_max,
        documentation="Return the greater of two ordered floats.",
    ),
    BuiltinFunction(
        name="float_clamp",
        signature=FunctionSignature(
            name="float_clamp",
            parameter_types=(FLOAT, FLOAT, FLOAT),
            return_type=FLOAT,
        ),
        implementation=_float_clamp,
        documentation=(
            "Clamp an ordered float to inclusive bounds; lower must not "
            "exceed upper."
        ),
    ),
    BuiltinFunction(
        name="float_sign",
        signature=FunctionSignature(
            name="float_sign",
            parameter_types=(FLOAT,),
            return_type=INT,
        ),
        implementation=_float_sign,
        documentation="Return -1, 0, or 1 according to a float's sign.",
    ),
    BuiltinFunction(
        name="float_is_finite",
        signature=FunctionSignature(
            name="float_is_finite",
            parameter_types=(FLOAT,),
            return_type=BOOL,
        ),
        implementation=_float_is_finite,
        documentation="Return whether a float is neither infinite nor NaN.",
    ),
)


__all__ = ("NUMERIC_BUILTINS",)