"""AFP-P10.3 deterministic string standard-library functions.

ApexForge string indexing is zero-based and counts Unicode code points. Slices
use a half-open ``[start, end)`` interval. This module remains pure: it performs
no I/O, mutation, environment access, time access, randomness, or host effects.
"""

from __future__ import annotations

from standard_library.model import (
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from type_system.inference import FunctionSignature
from type_system.model import BOOL, INT, STRING


MAX_STRING_RESULT_CODE_POINTS = 1_000_000


def _domain_error(function_name: str, message: str) -> None:
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-006",
        message=(
            f"Standard-library function {function_name!r} received "
            f"an invalid string domain: {message}"
        ),
    )


def _result_limit_error(function_name: str, length: int) -> None:
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-007",
        message=(
            f"Standard-library function {function_name!r} would produce "
            f"{length} code points, exceeding the limit of "
            f"{MAX_STRING_RESULT_CODE_POINTS}."
        ),
    )


def _require_result_size(function_name: str, length: int) -> None:
    if length > MAX_STRING_RESULT_CODE_POINTS:
        _result_limit_error(function_name, length)


def _string_is_empty(value: str) -> bool:
    return value == ""


def _string_starts_with(value: str, prefix: str) -> bool:
    return value.startswith(prefix)


def _string_ends_with(value: str, suffix: str) -> bool:
    return value.endswith(suffix)


def _string_index_of(value: str, fragment: str) -> int:
    return value.find(fragment)


def _string_last_index_of(value: str, fragment: str) -> int:
    return value.rfind(fragment)


def _string_char_at(value: str, index: int) -> str:
    if index < 0 or index >= len(value):
        _domain_error(
            "string_char_at",
            f"index {index} is outside [0, {len(value)}).",
        )
    return value[index]


def _string_slice(value: str, start: int, end: int) -> str:
    length = len(value)
    if start < 0:
        _domain_error(
            "string_slice",
            f"start index {start} cannot be negative.",
        )
    if end < start:
        _domain_error(
            "string_slice",
            f"end index {end} precedes start index {start}.",
        )
    if end > length:
        _domain_error(
            "string_slice",
            f"end index {end} exceeds string length {length}.",
        )
    return value[start:end]


def _string_concat(left: str, right: str) -> str:
    result_length = len(left) + len(right)
    _require_result_size("string_concat", result_length)
    return left + right


def _string_repeat(value: str, count: int) -> str:
    if count < 0:
        _domain_error(
            "string_repeat",
            f"repeat count {count} cannot be negative.",
        )
    result_length = len(value) * count
    _require_result_size("string_repeat", result_length)
    return value * count


def _string_replace(value: str, target: str, replacement: str) -> str:
    if target == "":
        _domain_error(
            "string_replace",
            "target cannot be empty.",
        )
    occurrences = value.count(target)
    result_length = (
        len(value)
        + occurrences * (len(replacement) - len(target))
    )
    _require_result_size("string_replace", result_length)
    return value.replace(target, replacement)


STRING_BUILTINS = (
    BuiltinFunction(
        name="string_is_empty",
        signature=FunctionSignature(
            name="string_is_empty",
            parameter_types=(STRING,),
            return_type=BOOL,
        ),
        implementation=_string_is_empty,
        documentation="Return whether a string contains zero code points.",
    ),
    BuiltinFunction(
        name="string_starts_with",
        signature=FunctionSignature(
            name="string_starts_with",
            parameter_types=(STRING, STRING),
            return_type=BOOL,
        ),
        implementation=_string_starts_with,
        documentation="Return whether a string begins with a prefix.",
    ),
    BuiltinFunction(
        name="string_ends_with",
        signature=FunctionSignature(
            name="string_ends_with",
            parameter_types=(STRING, STRING),
            return_type=BOOL,
        ),
        implementation=_string_ends_with,
        documentation="Return whether a string ends with a suffix.",
    ),
    BuiltinFunction(
        name="string_index_of",
        signature=FunctionSignature(
            name="string_index_of",
            parameter_types=(STRING, STRING),
            return_type=INT,
        ),
        implementation=_string_index_of,
        documentation=(
            "Return the first code-point index of a fragment, or -1 when "
            "the fragment is absent."
        ),
    ),
    BuiltinFunction(
        name="string_last_index_of",
        signature=FunctionSignature(
            name="string_last_index_of",
            parameter_types=(STRING, STRING),
            return_type=INT,
        ),
        implementation=_string_last_index_of,
        documentation=(
            "Return the last code-point index of a fragment, or -1 when "
            "the fragment is absent."
        ),
    ),
    BuiltinFunction(
        name="string_char_at",
        signature=FunctionSignature(
            name="string_char_at",
            parameter_types=(STRING, INT),
            return_type=STRING,
        ),
        implementation=_string_char_at,
        documentation="Return the code point at one zero-based index.",
    ),
    BuiltinFunction(
        name="string_slice",
        signature=FunctionSignature(
            name="string_slice",
            parameter_types=(STRING, INT, INT),
            return_type=STRING,
        ),
        implementation=_string_slice,
        documentation=(
            "Return the half-open code-point slice [start, end); indices "
            "must satisfy 0 <= start <= end <= string_length(value)."
        ),
    ),
    BuiltinFunction(
        name="string_concat",
        signature=FunctionSignature(
            name="string_concat",
            parameter_types=(STRING, STRING),
            return_type=STRING,
        ),
        implementation=_string_concat,
        documentation="Concatenate two strings in left-to-right order.",
    ),
    BuiltinFunction(
        name="string_repeat",
        signature=FunctionSignature(
            name="string_repeat",
            parameter_types=(STRING, INT),
            return_type=STRING,
        ),
        implementation=_string_repeat,
        documentation="Repeat a string a non-negative number of times.",
    ),
    BuiltinFunction(
        name="string_replace",
        signature=FunctionSignature(
            name="string_replace",
            parameter_types=(STRING, STRING, STRING),
            return_type=STRING,
        ),
        implementation=_string_replace,
        documentation=(
            "Replace every non-overlapping target occurrence; target must "
            "not be empty."
        ),
    ),
)


__all__ = (
    "MAX_STRING_RESULT_CODE_POINTS",
    "STRING_BUILTINS",
)