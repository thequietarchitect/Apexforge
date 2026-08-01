"""Pure AFP-P10.7 immutable collection utilities."""

from __future__ import annotations

from typing import Any

from standard_library.collection_value import (
    MAX_COLLECTION_LENGTH,
    RuntimeCollection,
    runtime_value_type,
)
from standard_library.model import (
    BuiltinFunction,
    StandardLibraryInvocationError,
)
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature
from type_system.model import BOOL, COLLECTION, INT, STRING


_SINGLE_T = ApexTypeVariable(
    name="T",
    owner="function:collection_single",
)
_PAIR_T = ApexTypeVariable(
    name="T",
    owner="function:collection_pair",
)
_REPEAT_T = ApexTypeVariable(
    name="T",
    owner="function:collection_repeat",
)
_APPEND_T = ApexTypeVariable(
    name="T",
    owner="function:collection_append",
)
_PREPEND_T = ApexTypeVariable(
    name="T",
    owner="function:collection_prepend",
)
_CONTAINS_T = ApexTypeVariable(
    name="T",
    owner="function:collection_contains",
)
_COUNT_T = ApexTypeVariable(
    name="T",
    owner="function:collection_count",
)
_GET_OR_T = ApexTypeVariable(
    name="T",
    owner="function:collection_get_or",
)
_FIRST_OR_T = ApexTypeVariable(
    name="T",
    owner="function:collection_first_or",
)
_LAST_OR_T = ApexTypeVariable(
    name="T",
    owner="function:collection_last_or",
)


def _limit_failure(operation: str, size: int) -> None:
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-010",
        message=(
            f"Collection operation {operation!r} would produce {size} "
            f"elements; the limit is {MAX_COLLECTION_LENGTH}."
        ),
    )


def _type_failure(
    operation: str,
    expected: RuntimeCollection,
    value: Any,
) -> None:
    actual = runtime_value_type(value)
    actual_name = (
        actual.name
        if actual is not None
        else type(value).__name__
    )
    raise StandardLibraryInvocationError(
        code="APX-STDLIB-011",
        message=(
            f"Collection operation {operation!r} requires element type "
            f"{expected.element_type}; received {actual_name}."
        ),
    )


def _require_element(
    operation: str,
    collection: RuntimeCollection,
    value: Any,
) -> None:
    if runtime_value_type(value) is not collection.element_type:
        _type_failure(operation, collection, value)


def _collection_single(value: Any) -> RuntimeCollection:
    value_type = runtime_value_type(value)
    if value_type is None:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-011",
            message=(
                "collection_single received an unsupported runtime value "
                f"of type {type(value).__name__}."
            ),
        )
    return RuntimeCollection(value_type, (value,))


def _collection_pair(first: Any, second: Any) -> RuntimeCollection:
    first_type = runtime_value_type(first)
    second_type = runtime_value_type(second)
    if first_type is None or second_type is not first_type:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-011",
            message=(
                "collection_pair requires two values with the same exact "
                "supported type."
            ),
        )
    return RuntimeCollection(first_type, (first, second))


def _collection_repeat(value: Any, count: int) -> RuntimeCollection:
    value_type = runtime_value_type(value)
    if value_type is None:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-011",
            message=(
                "collection_repeat received an unsupported runtime value "
                f"of type {type(value).__name__}."
            ),
        )
    if count < 0:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-012",
            message="collection_repeat count cannot be negative.",
        )
    if count > MAX_COLLECTION_LENGTH:
        _limit_failure("collection_repeat", count)
    return RuntimeCollection(value_type, (value,) * count)


def _collection_length(values: RuntimeCollection) -> int:
    return values.length


def _collection_is_empty(values: RuntimeCollection) -> bool:
    return values.is_empty


def _collection_element_type(values: RuntimeCollection) -> str:
    return values.element_type.name


def _collection_append(
    values: RuntimeCollection,
    value: Any,
) -> RuntimeCollection:
    _require_element("collection_append", values, value)
    size = values.length + 1
    if size > MAX_COLLECTION_LENGTH:
        _limit_failure("collection_append", size)
    return RuntimeCollection(
        values.element_type,
        values.values + (value,),
    )


def _collection_prepend(
    value: Any,
    values: RuntimeCollection,
) -> RuntimeCollection:
    _require_element("collection_prepend", values, value)
    size = values.length + 1
    if size > MAX_COLLECTION_LENGTH:
        _limit_failure("collection_prepend", size)
    return RuntimeCollection(
        values.element_type,
        (value,) + values.values,
    )


def _collection_concat(
    left: RuntimeCollection,
    right: RuntimeCollection,
) -> RuntimeCollection:
    if left.element_type is not right.element_type:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-011",
            message=(
                "collection_concat requires matching exact element types; "
                f"received {left.element_type} and {right.element_type}."
            ),
        )
    size = left.length + right.length
    if size > MAX_COLLECTION_LENGTH:
        _limit_failure("collection_concat", size)
    return RuntimeCollection(
        left.element_type,
        left.values + right.values,
    )


def _collection_contains(
    values: RuntimeCollection,
    value: Any,
) -> bool:
    _require_element("collection_contains", values, value)
    return value in values.values


def _collection_count(
    values: RuntimeCollection,
    value: Any,
) -> int:
    _require_element("collection_count", values, value)
    return values.values.count(value)


def _collection_get_or(
    values: RuntimeCollection,
    index: int,
    fallback: Any,
) -> Any:
    _require_element("collection_get_or", values, fallback)
    if 0 <= index < values.length:
        return values.values[index]
    return fallback


def _collection_first_or(
    values: RuntimeCollection,
    fallback: Any,
) -> Any:
    _require_element("collection_first_or", values, fallback)
    return values.values[0] if values.values else fallback


def _collection_last_or(
    values: RuntimeCollection,
    fallback: Any,
) -> Any:
    _require_element("collection_last_or", values, fallback)
    return values.values[-1] if values.values else fallback


def _collection_slice(
    values: RuntimeCollection,
    start: int,
    end: int,
) -> RuntimeCollection:
    if start < 0 or end < 0 or start > end or end > values.length:
        raise StandardLibraryInvocationError(
            code="APX-STDLIB-012",
            message=(
                "collection_slice requires 0 <= start <= end <= length; "
                f"received start={start}, end={end}, length={values.length}."
            ),
        )
    return RuntimeCollection(
        values.element_type,
        values.values[start:end],
    )


def _collection_reverse(
    values: RuntimeCollection,
) -> RuntimeCollection:
    return RuntimeCollection(
        values.element_type,
        tuple(reversed(values.values)),
    )


COLLECTION_BUILTINS = (
    BuiltinFunction(
        name="collection_single",
        signature=FunctionSignature(
            name="collection_single",
            parameter_types=(_SINGLE_T,),
            return_type=COLLECTION,
            type_parameters=(_SINGLE_T,),
        ),
        implementation=_collection_single,
        documentation="Create a one-element immutable collection.",
    ),
    BuiltinFunction(
        name="collection_pair",
        signature=FunctionSignature(
            name="collection_pair",
            parameter_types=(_PAIR_T, _PAIR_T),
            return_type=COLLECTION,
            type_parameters=(_PAIR_T,),
        ),
        implementation=_collection_pair,
        documentation="Create an immutable collection from two equal-type values.",
    ),
    BuiltinFunction(
        name="collection_repeat",
        signature=FunctionSignature(
            name="collection_repeat",
            parameter_types=(_REPEAT_T, INT),
            return_type=COLLECTION,
            type_parameters=(_REPEAT_T,),
        ),
        implementation=_collection_repeat,
        documentation="Repeat one value into a bounded immutable collection.",
    ),
    BuiltinFunction(
        name="collection_length",
        signature=FunctionSignature(
            name="collection_length",
            parameter_types=(COLLECTION,),
            return_type=INT,
        ),
        implementation=_collection_length,
        documentation="Return the number of collection elements.",
    ),
    BuiltinFunction(
        name="collection_is_empty",
        signature=FunctionSignature(
            name="collection_is_empty",
            parameter_types=(COLLECTION,),
            return_type=BOOL,
        ),
        implementation=_collection_is_empty,
        documentation="Return whether a collection has no elements.",
    ),
    BuiltinFunction(
        name="collection_element_type",
        signature=FunctionSignature(
            name="collection_element_type",
            parameter_types=(COLLECTION,),
            return_type=STRING,
        ),
        implementation=_collection_element_type,
        documentation="Return the retained exact element type name.",
    ),
    BuiltinFunction(
        name="collection_append",
        signature=FunctionSignature(
            name="collection_append",
            parameter_types=(COLLECTION, _APPEND_T),
            return_type=COLLECTION,
            type_parameters=(_APPEND_T,),
        ),
        implementation=_collection_append,
        documentation="Return a collection with one value appended.",
    ),
    BuiltinFunction(
        name="collection_prepend",
        signature=FunctionSignature(
            name="collection_prepend",
            parameter_types=(_PREPEND_T, COLLECTION),
            return_type=COLLECTION,
            type_parameters=(_PREPEND_T,),
        ),
        implementation=_collection_prepend,
        documentation="Return a collection with one value prepended.",
    ),
    BuiltinFunction(
        name="collection_concat",
        signature=FunctionSignature(
            name="collection_concat",
            parameter_types=(COLLECTION, COLLECTION),
            return_type=COLLECTION,
        ),
        implementation=_collection_concat,
        documentation="Concatenate collections with matching element types.",
    ),
    BuiltinFunction(
        name="collection_contains",
        signature=FunctionSignature(
            name="collection_contains",
            parameter_types=(COLLECTION, _CONTAINS_T),
            return_type=BOOL,
            type_parameters=(_CONTAINS_T,),
        ),
        implementation=_collection_contains,
        documentation="Return whether an equal value occurs in the collection.",
    ),
    BuiltinFunction(
        name="collection_count",
        signature=FunctionSignature(
            name="collection_count",
            parameter_types=(COLLECTION, _COUNT_T),
            return_type=INT,
            type_parameters=(_COUNT_T,),
        ),
        implementation=_collection_count,
        documentation="Count equal occurrences of a value.",
    ),
    BuiltinFunction(
        name="collection_get_or",
        signature=FunctionSignature(
            name="collection_get_or",
            parameter_types=(COLLECTION, INT, _GET_OR_T),
            return_type=_GET_OR_T,
            type_parameters=(_GET_OR_T,),
        ),
        implementation=_collection_get_or,
        documentation="Return an indexed value or the fallback.",
    ),
    BuiltinFunction(
        name="collection_first_or",
        signature=FunctionSignature(
            name="collection_first_or",
            parameter_types=(COLLECTION, _FIRST_OR_T),
            return_type=_FIRST_OR_T,
            type_parameters=(_FIRST_OR_T,),
        ),
        implementation=_collection_first_or,
        documentation="Return the first value or the fallback.",
    ),
    BuiltinFunction(
        name="collection_last_or",
        signature=FunctionSignature(
            name="collection_last_or",
            parameter_types=(COLLECTION, _LAST_OR_T),
            return_type=_LAST_OR_T,
            type_parameters=(_LAST_OR_T,),
        ),
        implementation=_collection_last_or,
        documentation="Return the last value or the fallback.",
    ),
    BuiltinFunction(
        name="collection_slice",
        signature=FunctionSignature(
            name="collection_slice",
            parameter_types=(COLLECTION, INT, INT),
            return_type=COLLECTION,
        ),
        implementation=_collection_slice,
        documentation="Return a strict half-open immutable slice.",
    ),
    BuiltinFunction(
        name="collection_reverse",
        signature=FunctionSignature(
            name="collection_reverse",
            parameter_types=(COLLECTION,),
            return_type=COLLECTION,
        ),
        implementation=_collection_reverse,
        documentation="Return a collection with reversed order.",
    ),
)


__all__ = (
    "COLLECTION_BUILTINS",
    "MAX_COLLECTION_LENGTH",
)