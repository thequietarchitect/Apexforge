"""Pure AFP-P10.5 generic value utilities."""

from __future__ import annotations

from typing import Any

from standard_library.model import BuiltinFunction
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature
from type_system.model import BOOL


_IDENTITY_T = ApexTypeVariable(
    name="T",
    owner="function:identity",
)

_CHOOSE_T = ApexTypeVariable(
    name="T",
    owner="function:choose",
)

_FIRST_T = ApexTypeVariable(
    name="T",
    owner="function:first",
)
_FIRST_U = ApexTypeVariable(
    name="U",
    owner="function:first",
)

_SECOND_T = ApexTypeVariable(
    name="T",
    owner="function:second",
)
_SECOND_U = ApexTypeVariable(
    name="U",
    owner="function:second",
)


def _identity(value: Any) -> Any:
    return value


def _choose(
    condition: bool,
    when_true: Any,
    when_false: Any,
) -> Any:
    return when_true if condition else when_false


def _first(first: Any, second: Any) -> Any:
    del second
    return first


def _second(first: Any, second: Any) -> Any:
    del first
    return second


GENERIC_VALUE_BUILTINS = (
    BuiltinFunction(
        name="identity",
        signature=FunctionSignature(
            name="identity",
            parameter_types=(_IDENTITY_T,),
            return_type=_IDENTITY_T,
            type_parameters=(_IDENTITY_T,),
        ),
        implementation=_identity,
        documentation="Return one value without changing its exact type.",
    ),
    BuiltinFunction(
        name="choose",
        signature=FunctionSignature(
            name="choose",
            parameter_types=(BOOL, _CHOOSE_T, _CHOOSE_T),
            return_type=_CHOOSE_T,
            type_parameters=(_CHOOSE_T,),
        ),
        implementation=_choose,
        documentation=(
            "Eagerly select one of two values with the same exact type."
        ),
    ),
    BuiltinFunction(
        name="first",
        signature=FunctionSignature(
            name="first",
            parameter_types=(_FIRST_T, _FIRST_U),
            return_type=_FIRST_T,
            type_parameters=(_FIRST_T, _FIRST_U),
        ),
        implementation=_first,
        documentation="Return the first of two values.",
    ),
    BuiltinFunction(
        name="second",
        signature=FunctionSignature(
            name="second",
            parameter_types=(_SECOND_T, _SECOND_U),
            return_type=_SECOND_U,
            type_parameters=(_SECOND_T, _SECOND_U),
        ),
        implementation=_second,
        documentation="Return the second of two values.",
    ),
)


__all__ = ("GENERIC_VALUE_BUILTINS",)
