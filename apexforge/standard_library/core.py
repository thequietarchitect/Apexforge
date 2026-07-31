"""AFP-P10 pure standard-library composition.

AFP-P10.12 makes the composition order explicit so the final contract audit can
prove that every public built-in belongs to exactly one slice and that the
canonical registry contains no hidden or duplicated entries.
"""

from __future__ import annotations

from standard_library.booleans import BOOLEAN_BUILTINS
from standard_library.collections import COLLECTION_BUILTINS
from standard_library.conversions import CONVERSION_BUILTINS
from standard_library.diagnostics import DIAGNOSTIC_BUILTINS
from standard_library.generic_values import GENERIC_VALUE_BUILTINS
from standard_library.model import BuiltinFunction
from standard_library.numeric import NUMERIC_BUILTINS
from standard_library.randoms import RANDOM_BUILTINS
from standard_library.reflection import REFLECTION_BUILTINS
from standard_library.registry import StandardLibraryRegistry
from standard_library.results import RESULT_BUILTINS
from standard_library.strings import STRING_BUILTINS
from standard_library.times import TIME_BUILTINS
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


# The tuple order is part of the frozen P10 contract. Registry lookup remains
# name-sorted, while this structure preserves slice ownership and composition.
STANDARD_LIBRARY_GROUPS = (
    ("core", CORE_BUILTINS),
    ("numeric", NUMERIC_BUILTINS),
    ("strings", STRING_BUILTINS),
    ("booleans", BOOLEAN_BUILTINS),
    ("conversions", CONVERSION_BUILTINS),
    ("generic_values", GENERIC_VALUE_BUILTINS),
    ("results", RESULT_BUILTINS),
    ("collections", COLLECTION_BUILTINS),
    ("time", TIME_BUILTINS),
    ("random", RANDOM_BUILTINS),
    ("diagnostics", DIAGNOSTIC_BUILTINS),
    ("reflection", REFLECTION_BUILTINS),
)


ALL_STANDARD_LIBRARY_BUILTINS = tuple(
    entry
    for _, entries in STANDARD_LIBRARY_GROUPS
    for entry in entries
)


DEFAULT_STANDARD_LIBRARY = StandardLibraryRegistry(
    ALL_STANDARD_LIBRARY_BUILTINS
)


__all__ = (
    "ALL_STANDARD_LIBRARY_BUILTINS",
    "BOOLEAN_BUILTINS",
    "COLLECTION_BUILTINS",
    "CONVERSION_BUILTINS",
    "CORE_BUILTINS",
    "DEFAULT_STANDARD_LIBRARY",
    "DIAGNOSTIC_BUILTINS",
    "GENERIC_VALUE_BUILTINS",
    "NUMERIC_BUILTINS",
    "RANDOM_BUILTINS",
    "REFLECTION_BUILTINS",
    "RESULT_BUILTINS",
    "STANDARD_LIBRARY_GROUPS",
    "STRING_BUILTINS",
    "TIME_BUILTINS",
)