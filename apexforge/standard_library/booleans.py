"""AFP-P10.4 deterministic Boolean standard-library functions.

These are eager pure functions. ApexForge evaluates call arguments before
invocation, so they do not claim short-circuit operator semantics.
"""

from __future__ import annotations

from standard_library.model import BuiltinFunction
from type_system.inference import FunctionSignature
from type_system.model import BOOL


def _bool_and(left: bool, right: bool) -> bool:
    return left and right


def _bool_or(left: bool, right: bool) -> bool:
    return left or right


def _bool_xor(left: bool, right: bool) -> bool:
    return left is not right


def _bool_implies(left: bool, right: bool) -> bool:
    return (not left) or right


BOOLEAN_BUILTINS = (
    BuiltinFunction(
        name="bool_and",
        signature=FunctionSignature(
            name="bool_and",
            parameter_types=(BOOL, BOOL),
            return_type=BOOL,
        ),
        implementation=_bool_and,
        documentation=(
            "Return the eager logical conjunction of two bool values."
        ),
    ),
    BuiltinFunction(
        name="bool_or",
        signature=FunctionSignature(
            name="bool_or",
            parameter_types=(BOOL, BOOL),
            return_type=BOOL,
        ),
        implementation=_bool_or,
        documentation=(
            "Return the eager logical disjunction of two bool values."
        ),
    ),
    BuiltinFunction(
        name="bool_xor",
        signature=FunctionSignature(
            name="bool_xor",
            parameter_types=(BOOL, BOOL),
            return_type=BOOL,
        ),
        implementation=_bool_xor,
        documentation=(
            "Return whether exactly one of two bool values is true."
        ),
    ),
    BuiltinFunction(
        name="bool_implies",
        signature=FunctionSignature(
            name="bool_implies",
            parameter_types=(BOOL, BOOL),
            return_type=BOOL,
        ),
        implementation=_bool_implies,
        documentation=(
            "Return material implication: false only for true implies false."
        ),
    ),
)


__all__ = ("BOOLEAN_BUILTINS",)