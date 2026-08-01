"""Pure AFP-P10.6 structured-result and safe parsing utilities."""

from __future__ import annotations

import math
import re

from standard_library.model import BuiltinFunction
from standard_library.result_value import RuntimeResult
from type_system.inference import FunctionSignature
from type_system.model import BOOL, FLOAT, INT, RESULT, STRING, ApexType


MAX_PARSE_INPUT_CODE_POINTS = 4096
MAX_INT_PARSE_DIGITS = 4096

_INT_PATTERN = re.compile(r"[+-]?[0-9]+\Z")
_FLOAT_PATTERN = re.compile(
    r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))"
    r"(?:[eE][+-]?[0-9]+)?\Z"
)
_SPECIAL_FLOATS = {
    "nan": float("nan"),
    "inf": float("inf"),
    "+inf": float("inf"),
    "-inf": float("-inf"),
}


def _failure(
    payload_type: ApexType,
    code: str,
    message: str,
) -> RuntimeResult:
    return RuntimeResult.failure(
        payload_type,
        code=code,
        message=message,
    )


def _string_to_int(value: str) -> RuntimeResult:
    if not value:
        return _failure(
            INT,
            "EMPTY_INPUT",
            "Cannot parse int from an empty string.",
        )
    if len(value) > MAX_PARSE_INPUT_CODE_POINTS:
        return _failure(
            INT,
            "INPUT_TOO_LONG",
            "Int parse input exceeds the 4096-code-point limit.",
        )
    if _INT_PATTERN.fullmatch(value) is None:
        return _failure(
            INT,
            "INVALID_INT",
            "Int text must contain an optional sign followed by ASCII digits.",
        )

    digits = value[1:] if value[0] in "+-" else value
    if len(digits) > MAX_INT_PARSE_DIGITS:
        return _failure(
            INT,
            "INPUT_TOO_LONG",
            "Int text exceeds the 4096-digit limit.",
        )

    try:
        parsed = int(value, 10)
    except (ValueError, OverflowError) as exc:
        return _failure(
            INT,
            "HOST_PARSE_FAILURE",
            f"Host int parser rejected validated text: {type(exc).__name__}.",
        )
    return RuntimeResult.success(INT, parsed)


def _string_to_float(value: str) -> RuntimeResult:
    if not value:
        return _failure(
            FLOAT,
            "EMPTY_INPUT",
            "Cannot parse float from an empty string.",
        )
    if len(value) > MAX_PARSE_INPUT_CODE_POINTS:
        return _failure(
            FLOAT,
            "INPUT_TOO_LONG",
            "Float parse input exceeds the 4096-code-point limit.",
        )

    if value in _SPECIAL_FLOATS:
        return RuntimeResult.success(FLOAT, _SPECIAL_FLOATS[value])

    if _FLOAT_PATTERN.fullmatch(value) is None:
        return _failure(
            FLOAT,
            "INVALID_FLOAT",
            "Float text must use decimal or exponent syntax without whitespace.",
        )

    try:
        parsed = float(value)
    except (ValueError, OverflowError) as exc:
        return _failure(
            FLOAT,
            "HOST_PARSE_FAILURE",
            f"Host float parser rejected validated text: {type(exc).__name__}.",
        )

    if math.isinf(parsed):
        return _failure(
            FLOAT,
            "FLOAT_OVERFLOW",
            "Finite float text overflowed the binary64 range.",
        )

    return RuntimeResult.success(FLOAT, parsed)


def _result_is_ok(value: RuntimeResult) -> bool:
    return value.ok


def _result_is_error(value: RuntimeResult) -> bool:
    return value.is_error


def _result_error_code(value: RuntimeResult) -> str:
    return value.error_code


def _result_error_message(value: RuntimeResult) -> str:
    return value.error_message


def _result_payload_type(value: RuntimeResult) -> str:
    return value.payload_type.name


def _result_int_or(value: RuntimeResult, fallback: int) -> int:
    if value.ok and value.payload_type is INT:
        return value.value
    return fallback


def _result_float_or(value: RuntimeResult, fallback: float) -> float:
    if value.ok and value.payload_type is FLOAT:
        return value.value
    return fallback


RESULT_BUILTINS = (
    BuiltinFunction(
        name="string_to_int",
        signature=FunctionSignature(
            name="string_to_int",
            parameter_types=(STRING,),
            return_type=RESULT,
        ),
        implementation=_string_to_int,
        documentation="Safely parse exact ASCII integer text into result.",
    ),
    BuiltinFunction(
        name="string_to_float",
        signature=FunctionSignature(
            name="string_to_float",
            parameter_types=(STRING,),
            return_type=RESULT,
        ),
        implementation=_string_to_float,
        documentation="Safely parse binary64 float text into result.",
    ),
    BuiltinFunction(
        name="result_is_ok",
        signature=FunctionSignature(
            name="result_is_ok",
            parameter_types=(RESULT,),
            return_type=BOOL,
        ),
        implementation=_result_is_ok,
        documentation="Return whether a structured result contains success.",
    ),
    BuiltinFunction(
        name="result_is_error",
        signature=FunctionSignature(
            name="result_is_error",
            parameter_types=(RESULT,),
            return_type=BOOL,
        ),
        implementation=_result_is_error,
        documentation="Return whether a structured result contains failure.",
    ),
    BuiltinFunction(
        name="result_error_code",
        signature=FunctionSignature(
            name="result_error_code",
            parameter_types=(RESULT,),
            return_type=STRING,
        ),
        implementation=_result_error_code,
        documentation="Return a failure code, or empty string on success.",
    ),
    BuiltinFunction(
        name="result_error_message",
        signature=FunctionSignature(
            name="result_error_message",
            parameter_types=(RESULT,),
            return_type=STRING,
        ),
        implementation=_result_error_message,
        documentation="Return a failure message, or empty string on success.",
    ),
    BuiltinFunction(
        name="result_payload_type",
        signature=FunctionSignature(
            name="result_payload_type",
            parameter_types=(RESULT,),
            return_type=STRING,
        ),
        implementation=_result_payload_type,
        documentation="Return the intended exact payload type name.",
    ),
    BuiltinFunction(
        name="result_int_or",
        signature=FunctionSignature(
            name="result_int_or",
            parameter_types=(RESULT, INT),
            return_type=INT,
        ),
        implementation=_result_int_or,
        documentation="Extract a successful int or return the fallback.",
    ),
    BuiltinFunction(
        name="result_float_or",
        signature=FunctionSignature(
            name="result_float_or",
            parameter_types=(RESULT, FLOAT),
            return_type=FLOAT,
        ),
        implementation=_result_float_or,
        documentation="Extract a successful float or return the fallback.",
    ),
)


__all__ = (
    "MAX_INT_PARSE_DIGITS",
    "MAX_PARSE_INPUT_CODE_POINTS",
    "RESULT_BUILTINS",
)
