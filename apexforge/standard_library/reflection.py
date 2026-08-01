"""Safe AFP-P10.11 reflection and introspection utilities.

This module exposes canonical ApexForge value-type metadata only. It does not
expose Python implementation objects, source files, memory addresses, dynamic
imports, dynamic invocation, or mutable runtime internals.
"""

from __future__ import annotations

from typing import Any

from standard_library.collection_value import RuntimeCollection
from standard_library.diagnostic_value import RuntimeDiagnostic
from standard_library.model import BuiltinFunction
from standard_library.random_value import RuntimeRandom
from standard_library.result_value import RuntimeResult
from standard_library.time_value import RuntimeTime
from standard_library.type_info_value import RuntimeTypeInfo
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature
from type_system.model import (
    BOOL,
    BUILTIN_TYPES,
    COLLECTION,
    DIAGNOSTIC,
    FLOAT,
    INT,
    RANDOM,
    RESULT,
    STRING,
    TIME,
    TYPE_INFO,
    VOID,
    ApexType,
    resolve_builtin_type,
)


_TYPE_OF_T = ApexTypeVariable(
    name="T",
    owner="function:type_of",
)

_TYPE_MATCHES_T = ApexTypeVariable(
    name="T",
    owner="function:type_matches",
)


def _runtime_value_type(value: Any) -> ApexType:
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
    if type(value) is RuntimeCollection:
        return COLLECTION
    if type(value) is RuntimeTime:
        return TIME
    if type(value) is RuntimeRandom:
        return RANDOM
    if type(value) is RuntimeDiagnostic:
        return DIAGNOSTIC
    if type(value) is RuntimeTypeInfo:
        return TYPE_INFO
    raise TypeError(
        "Safe reflection received an unsupported runtime value type "
        f"{type(value).__name__}."
    )


def _type_of(value: Any) -> RuntimeTypeInfo:
    return RuntimeTypeInfo(_runtime_value_type(value))


def _type_matches(
    value: Any,
    expected: RuntimeTypeInfo,
) -> bool:
    return _runtime_value_type(value) is expected.value_type


def _type_from_name(value: str) -> RuntimeResult:
    try:
        resolved = resolve_builtin_type(value)
    except (TypeError, ValueError):
        return RuntimeResult.failure(
            TYPE_INFO,
            code="UNKNOWN_TYPE",
            message=f"Unknown ApexForge built-in type {value!r}.",
        )
    return RuntimeResult.success(
        TYPE_INFO,
        RuntimeTypeInfo(resolved),
    )


def _result_type_info_or(
    value: RuntimeResult,
    fallback: RuntimeTypeInfo,
) -> RuntimeTypeInfo:
    if value.ok and value.payload_type is TYPE_INFO:
        return value.value
    return fallback


def _type_name(value: RuntimeTypeInfo) -> str:
    return value.name


def _type_equal(
    left: RuntimeTypeInfo,
    right: RuntimeTypeInfo,
) -> bool:
    return left.value_type is right.value_type


def _type_compare(
    left: RuntimeTypeInfo,
    right: RuntimeTypeInfo,
) -> int:
    if left.order < right.order:
        return -1
    if left.order > right.order:
        return 1
    return 0


def _type_is_primitive(value: RuntimeTypeInfo) -> bool:
    return value.is_primitive


def _type_is_numeric(value: RuntimeTypeInfo) -> bool:
    return value.is_numeric


def _type_is_opaque(value: RuntimeTypeInfo) -> bool:
    return value.is_opaque


def _type_is_container(value: RuntimeTypeInfo) -> bool:
    return value.is_container


def _type_is_void(value: RuntimeTypeInfo) -> bool:
    return value.is_void


def _type_is_runtime_value(value: RuntimeTypeInfo) -> bool:
    return value.is_runtime_value


def _type_builtin_count() -> int:
    return len(BUILTIN_TYPES)


def _type_builtin_at(
    index: int,
    fallback: RuntimeTypeInfo,
) -> RuntimeTypeInfo:
    if index < 0 or index >= len(BUILTIN_TYPES):
        return fallback
    return RuntimeTypeInfo(BUILTIN_TYPES[index])


def _type_builtin_names() -> RuntimeCollection:
    return RuntimeCollection(
        element_type=STRING,
        values=tuple(value_type.name for value_type in BUILTIN_TYPES),
    )


def _type_collection_element(
    value: RuntimeCollection,
) -> RuntimeTypeInfo:
    return RuntimeTypeInfo(value.element_type)


def _type_result_payload(
    value: RuntimeResult,
) -> RuntimeTypeInfo:
    return RuntimeTypeInfo(value.payload_type)


REFLECTION_BUILTINS = (
    BuiltinFunction(
        name="type_of",
        signature=FunctionSignature(
            name="type_of",
            parameter_types=(_TYPE_OF_T,),
            return_type=TYPE_INFO,
            type_parameters=(_TYPE_OF_T,),
        ),
        implementation=_type_of,
        documentation="Return safe canonical type metadata for one value.",
    ),
    BuiltinFunction(
        name="type_matches",
        signature=FunctionSignature(
            name="type_matches",
            parameter_types=(_TYPE_MATCHES_T, TYPE_INFO),
            return_type=BOOL,
            type_parameters=(_TYPE_MATCHES_T,),
        ),
        implementation=_type_matches,
        documentation="Compare one value's exact type with type metadata.",
    ),
    BuiltinFunction(
        name="type_from_name",
        signature=FunctionSignature(
            name="type_from_name",
            parameter_types=(STRING,),
            return_type=RESULT,
        ),
        implementation=_type_from_name,
        documentation="Resolve a built-in type name into structured metadata.",
    ),
    BuiltinFunction(
        name="result_type_info_or",
        signature=FunctionSignature(
            name="result_type_info_or",
            parameter_types=(RESULT, TYPE_INFO),
            return_type=TYPE_INFO,
        ),
        implementation=_result_type_info_or,
        documentation="Extract type metadata from a result or use fallback.",
    ),
    BuiltinFunction(
        name="type_name",
        signature=FunctionSignature(
            name="type_name",
            parameter_types=(TYPE_INFO,),
            return_type=STRING,
        ),
        implementation=_type_name,
        documentation="Return the canonical source spelling of a type.",
    ),
    BuiltinFunction(
        name="type_equal",
        signature=FunctionSignature(
            name="type_equal",
            parameter_types=(TYPE_INFO, TYPE_INFO),
            return_type=BOOL,
        ),
        implementation=_type_equal,
        documentation="Compare two canonical type identities.",
    ),
    BuiltinFunction(
        name="type_compare",
        signature=FunctionSignature(
            name="type_compare",
            parameter_types=(TYPE_INFO, TYPE_INFO),
            return_type=INT,
        ),
        implementation=_type_compare,
        documentation="Compare types by canonical built-in declaration order.",
    ),
    BuiltinFunction(
        name="type_is_primitive",
        signature=FunctionSignature(
            name="type_is_primitive",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_primitive,
        documentation="Return whether a type is an AFP-P8 primitive.",
    ),
    BuiltinFunction(
        name="type_is_numeric",
        signature=FunctionSignature(
            name="type_is_numeric",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_numeric,
        documentation="Return whether a type is int or float.",
    ),
    BuiltinFunction(
        name="type_is_opaque",
        signature=FunctionSignature(
            name="type_is_opaque",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_opaque,
        documentation="Return whether a type is a non-primitive value type.",
    ),
    BuiltinFunction(
        name="type_is_container",
        signature=FunctionSignature(
            name="type_is_container",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_container,
        documentation="Return whether a type is result or collection.",
    ),
    BuiltinFunction(
        name="type_is_void",
        signature=FunctionSignature(
            name="type_is_void",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_void,
        documentation="Return whether metadata represents void.",
    ),
    BuiltinFunction(
        name="type_is_runtime_value",
        signature=FunctionSignature(
            name="type_is_runtime_value",
            parameter_types=(TYPE_INFO,),
            return_type=BOOL,
        ),
        implementation=_type_is_runtime_value,
        documentation="Return whether a type may have a runtime value.",
    ),
    BuiltinFunction(
        name="type_builtin_count",
        signature=FunctionSignature(
            name="type_builtin_count",
            parameter_types=(),
            return_type=INT,
        ),
        implementation=_type_builtin_count,
        documentation="Return the number of canonical built-in types.",
    ),
    BuiltinFunction(
        name="type_builtin_at",
        signature=FunctionSignature(
            name="type_builtin_at",
            parameter_types=(INT, TYPE_INFO),
            return_type=TYPE_INFO,
        ),
        implementation=_type_builtin_at,
        documentation="Return a built-in type by index or the fallback.",
    ),
    BuiltinFunction(
        name="type_builtin_names",
        signature=FunctionSignature(
            name="type_builtin_names",
            parameter_types=(),
            return_type=COLLECTION,
        ),
        implementation=_type_builtin_names,
        documentation="Return all built-in type names in canonical order.",
    ),
    BuiltinFunction(
        name="type_collection_element",
        signature=FunctionSignature(
            name="type_collection_element",
            parameter_types=(COLLECTION,),
            return_type=TYPE_INFO,
        ),
        implementation=_type_collection_element,
        documentation="Return a collection's retained element type.",
    ),
    BuiltinFunction(
        name="type_result_payload",
        signature=FunctionSignature(
            name="type_result_payload",
            parameter_types=(RESULT,),
            return_type=TYPE_INFO,
        ),
        implementation=_type_result_payload,
        documentation="Return a result's declared payload type.",
    ),
)


__all__ = ("REFLECTION_BUILTINS",)