"""AFP-P10 pure standard-library composition."""

from __future__ import annotations

from standard_library.booleans import BOOLEAN_BUILTINS
from standard_library.conversions import CONVERSION_BUILTINS
from standard_library.generic_values import GENERIC_VALUE_BUILTINS
from standard_library.model import BuiltinFunction
from standard_library.numeric import NUMERIC_BUILTINS
from standard_library.registry import StandardLibraryRegistry
from standard_library.strings import STRING_BUILTINS
from type_system.inference import FunctionSignature
from type_system.model import BOOL, FLOAT, INT, STRING


def _int_abs(value: int) -> int:
    return abs(value)


def _float_abs(value: float) -> float:
    return abs(value)


def _string_length(value: str) -> int:
    # ApexForge defines length as the Python/Unicode code-point count.
    return len(value)


def _string_contains(value: str, fragment: str) -> bool:
    return fragment in value


def _bool_not(value: bool) -> bool:
    return not value


CORE_BUILTINS = (
    BuiltinFunction(
        name="int_abs",
        signature=FunctionSignature(
            name="int_abs",
            parameter_types=(INT,),
            return_type=INT,
        ),
        implementation=_int_abs,
        documentation="Return the absolute value of one int.",
    ),
    BuiltinFunction(
        name="float_abs",
        signature=FunctionSignature(
            name="float_abs",
            parameter_types=(FLOAT,),
            return_type=FLOAT,
        ),
        implementation=_float_abs,
        documentation="Return the absolute value of one float.",
    ),
    BuiltinFunction(
        name="string_length",
        signature=FunctionSignature(
            name="string_length",
            parameter_types=(STRING,),
            return_type=INT,
        ),
        implementation=_string_length,
        documentation="Return a string's Unicode code-point count.",
    ),
    BuiltinFunction(
        name="string_contains",
        signature=FunctionSignature(
            name="string_contains",
            parameter_types=(STRING, STRING),
            return_type=BOOL,
        ),
        implementation=_string_contains,
        documentation="Return whether a string contains a fragment.",
    ),
    BuiltinFunction(
        name="bool_not",
        signature=FunctionSignature(
            name="bool_not",
            parameter_types=(BOOL,),
            return_type=BOOL,
        ),
        implementation=_bool_not,
        documentation="Return the logical inverse of one bool.",
    ),
)


DEFAULT_STANDARD_LIBRARY = StandardLibraryRegistry(
    CORE_BUILTINS
    + NUMERIC_BUILTINS
    + STRING_BUILTINS
    + BOOLEAN_BUILTINS
    + CONVERSION_BUILTINS
    + GENERIC_VALUE_BUILTINS
)


__all__ = (
    "CORE_BUILTINS",
    "DEFAULT_STANDARD_LIBRARY",
    "GENERIC_VALUE_BUILTINS",
)