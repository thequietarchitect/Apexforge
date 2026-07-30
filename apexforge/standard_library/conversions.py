"""AFP-P10.4 explicit, deterministic conversion functions.

Conversions are never inserted implicitly. ``int_to_float`` uses the host's
IEEE-754 binary64 conversion and therefore may round; values outside the
finite float domain are rejected. Text conversions have canonical spellings.
"""

from __future__ import annotations

import math

from standard_library.model import (
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from type_system.inference import FunctionSignature
from type_system.model import BOOL, FLOAT, INT, STRING


MAX_INT_STRING_DIGITS = 4_096


def _conversion_error(function_name: str, message: str) -> None:
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-008",
        message=(
            f"Standard-library function {function_name!r} received "
            f"an invalid conversion domain: {message}"
        ),
    )


def _decimal_digit_count(value: int) -> int:
    magnitude = abs(value)
    if magnitude == 0:
        return 1

    # Integer-only correction around a logarithmic estimate. The estimate can
    # be off by one but the power-of-ten comparisons make the result exact.
    estimate = int((magnitude.bit_length() - 1) * 0.3010299956639812) + 1
    if magnitude >= 10 ** estimate:
        estimate += 1
    elif magnitude < 10 ** (estimate - 1):
        estimate -= 1
    return estimate


def _int_to_float(value: int) -> float:
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        _conversion_error(
            "int_to_float",
            f"int cannot be represented in the finite float domain: {exc}",
        )
    if not math.isfinite(result):
        _conversion_error(
            "int_to_float",
            "int conversion produced a non-finite float.",
        )
    return result


def _int_to_string(value: int) -> str:
    digits = _decimal_digit_count(value)
    if digits > MAX_INT_STRING_DIGITS:
        _conversion_error(
            "int_to_string",
            f"decimal digit count {digits} exceeds the limit of "
            f"{MAX_INT_STRING_DIGITS}.",
        )
    try:
        return str(value)
    except ValueError as exc:
        _conversion_error(
            "int_to_string",
            f"runtime rejected decimal conversion: {exc}",
        )


def _float_to_string(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if value == math.inf:
        return "inf"
    if value == -math.inf:
        return "-inf"
    # Python's repr is the shortest round-trippable binary64 representation.
    # It preserves integral float spelling (1.0) and negative zero (-0.0).
    return repr(value)


def _bool_to_string(value: bool) -> str:
    return "true" if value else "false"


CONVERSION_BUILTINS = (
    BuiltinFunction(
        name="int_to_float",
        signature=FunctionSignature(
            name="int_to_float",
            parameter_types=(INT,),
            return_type=FLOAT,
        ),
        implementation=_int_to_float,
        documentation=(
            "Explicitly convert an int to finite float; precision may round."
        ),
    ),
    BuiltinFunction(
        name="int_to_string",
        signature=FunctionSignature(
            name="int_to_string",
            parameter_types=(INT,),
            return_type=STRING,
        ),
        implementation=_int_to_string,
        documentation="Return the canonical base-10 spelling of an int.",
    ),
    BuiltinFunction(
        name="float_to_string",
        signature=FunctionSignature(
            name="float_to_string",
            parameter_types=(FLOAT,),
            return_type=STRING,
        ),
        implementation=_float_to_string,
        documentation=(
            "Return the shortest round-trippable float spelling; special "
            "values use nan, inf, and -inf."
        ),
    ),
    BuiltinFunction(
        name="bool_to_string",
        signature=FunctionSignature(
            name="bool_to_string",
            parameter_types=(BOOL,),
            return_type=STRING,
        ),
        implementation=_bool_to_string,
        documentation="Return true or false in canonical lowercase form.",
    ),
)


__all__ = (
    "CONVERSION_BUILTINS",
    "MAX_INT_STRING_DIGITS",
)