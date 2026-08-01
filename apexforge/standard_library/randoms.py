"""Pure AFP-P10.9 deterministic random utilities."""

from __future__ import annotations

from standard_library.collection_value import RuntimeCollection
from standard_library.model import BuiltinFunction
from standard_library.random_value import (
    RuntimeRandom,
    UINT64_MASK,
    UINT64_MODULUS,
)
from standard_library.result_value import RuntimeResult
from type_system.inference import FunctionSignature
from type_system.model import (
    BOOL,
    COLLECTION,
    FLOAT,
    INT,
    RANDOM,
    RESULT,
)


def _random_success(value: RuntimeRandom) -> RuntimeResult:
    return RuntimeResult.success(RANDOM, value)


def _int_success(value: int) -> RuntimeResult:
    return RuntimeResult.success(INT, value)


def _bool_success(value: bool) -> RuntimeResult:
    return RuntimeResult.success(BOOL, value)


def _random_failure(code: str, message: str) -> RuntimeResult:
    return RuntimeResult.failure(
        RANDOM,
        code=code,
        message=message,
    )


def _int_failure(code: str, message: str) -> RuntimeResult:
    return RuntimeResult.failure(
        INT,
        code=code,
        message=message,
    )


def _bool_failure(code: str, message: str) -> RuntimeResult:
    return RuntimeResult.failure(
        BOOL,
        code=code,
        message=message,
    )


def _uniform_below(
    value: RuntimeRandom,
    bound: int,
) -> tuple[int, RuntimeRandom]:
    """Return an unbiased value in ``[0, bound)`` and the next local state."""

    if not 1 <= bound <= UINT64_MODULUS:
        raise ValueError("bound must be within 1 through 2^64.")

    limit = UINT64_MODULUS - (UINT64_MODULUS % bound)
    probe = value

    while True:
        sample = probe.sample_u64()
        next_probe = probe.advanced()
        if sample < limit:
            return sample % bound, next_probe
        probe = next_probe


def _random_from_seed(seed: int) -> RuntimeRandom:
    return RuntimeRandom.from_seed(seed)


def _random_state(value: RuntimeRandom) -> int:
    return value.state


def _random_advance(value: RuntimeRandom) -> RuntimeRandom:
    return value.advanced()


def _random_advance_by(
    value: RuntimeRandom,
    steps: int,
) -> RuntimeResult:
    if steps < 0:
        return _random_failure(
            "NEGATIVE_RANDOM_ADVANCE",
            "Random stream advance count cannot be negative.",
        )
    if steps > UINT64_MASK:
        return _random_failure(
            "RANDOM_ADVANCE_TOO_LARGE",
            "Random stream advance count cannot exceed 2^64 - 1.",
        )
    return _random_success(value.advanced(steps))


def _result_random_or(
    value: RuntimeResult,
    fallback: RuntimeRandom,
) -> RuntimeRandom:
    if value.ok and value.payload_type is RANDOM:
        return value.value
    return fallback


def _random_u64(value: RuntimeRandom) -> int:
    return value.sample_u64()


def _random_int_between(
    value: RuntimeRandom,
    minimum: int,
    maximum: int,
) -> RuntimeResult:
    if minimum > maximum:
        return _int_failure(
            "INVALID_RANDOM_RANGE",
            "Random integer minimum cannot exceed maximum.",
        )

    span = maximum - minimum + 1
    if span > UINT64_MODULUS:
        return _int_failure(
            "RANDOM_RANGE_TOO_WIDE",
            "Random integer range cannot exceed 2^64 distinct values.",
        )

    offset, _ = _uniform_below(value, span)
    return _int_success(minimum + offset)


def _random_float_unit(value: RuntimeRandom) -> float:
    # The upper 53 bits map exactly into IEEE-754 binary64's unit interval.
    return (value.sample_u64() >> 11) / float(1 << 53)


def _random_bool(value: RuntimeRandom) -> bool:
    return bool(value.sample_u64() & 1)


def _random_chance(
    value: RuntimeRandom,
    numerator: int,
    denominator: int,
) -> RuntimeResult:
    if denominator <= 0:
        return _bool_failure(
            "INVALID_RANDOM_DENOMINATOR",
            "Random chance denominator must be positive.",
        )
    if numerator < 0 or numerator > denominator:
        return _bool_failure(
            "INVALID_RANDOM_NUMERATOR",
            "Random chance numerator must satisfy 0 <= numerator <= denominator.",
        )
    if denominator > UINT64_MODULUS:
        return _bool_failure(
            "RANDOM_DENOMINATOR_TOO_WIDE",
            "Random chance denominator cannot exceed 2^64.",
        )
    if numerator == 0:
        return _bool_success(False)
    if numerator == denominator:
        return _bool_success(True)

    draw, _ = _uniform_below(value, denominator)
    return _bool_success(draw < numerator)


def _random_collection_index(
    value: RuntimeRandom,
    collection: RuntimeCollection,
) -> RuntimeResult:
    if collection.is_empty:
        return _int_failure(
            "EMPTY_RANDOM_COLLECTION",
            "Cannot choose an index from an empty collection.",
        )

    index, _ = _uniform_below(value, collection.length)
    return _int_success(index)


def _random_shuffle(
    value: RuntimeRandom,
    collection: RuntimeCollection,
) -> RuntimeCollection:
    if collection.length < 2:
        return collection

    items = list(collection.values)
    probe = value

    for upper in range(len(items) - 1, 0, -1):
        index, probe = _uniform_below(probe, upper + 1)
        items[upper], items[index] = items[index], items[upper]

    return RuntimeCollection(
        collection.element_type,
        tuple(items),
    )


def _random_fork(
    value: RuntimeRandom,
    stream: int,
) -> RuntimeRandom:
    return value.fork(stream)


def _random_equal(
    left: RuntimeRandom,
    right: RuntimeRandom,
) -> bool:
    return left == right


RANDOM_BUILTINS = (
    BuiltinFunction(
        name="random_from_seed",
        signature=FunctionSignature(
            name="random_from_seed",
            parameter_types=(INT,),
            return_type=RANDOM,
        ),
        implementation=_random_from_seed,
        documentation="Create an immutable deterministic random stream.",
    ),
    BuiltinFunction(
        name="random_state",
        signature=FunctionSignature(
            name="random_state",
            parameter_types=(RANDOM,),
            return_type=INT,
        ),
        implementation=_random_state,
        documentation="Return the unsigned 64-bit stream state.",
    ),
    BuiltinFunction(
        name="random_advance",
        signature=FunctionSignature(
            name="random_advance",
            parameter_types=(RANDOM,),
            return_type=RANDOM,
        ),
        implementation=_random_advance,
        documentation="Advance a stream by one deterministic position.",
    ),
    BuiltinFunction(
        name="random_advance_by",
        signature=FunctionSignature(
            name="random_advance_by",
            parameter_types=(RANDOM, INT),
            return_type=RESULT,
        ),
        implementation=_random_advance_by,
        documentation="Safely advance a stream by a non-negative count.",
    ),
    BuiltinFunction(
        name="result_random_or",
        signature=FunctionSignature(
            name="result_random_or",
            parameter_types=(RESULT, RANDOM),
            return_type=RANDOM,
        ),
        implementation=_result_random_or,
        documentation="Extract a successful random stream or use a fallback.",
    ),
    BuiltinFunction(
        name="random_u64",
        signature=FunctionSignature(
            name="random_u64",
            parameter_types=(RANDOM,),
            return_type=INT,
        ),
        implementation=_random_u64,
        documentation="Return the deterministic unsigned 64-bit sample.",
    ),
    BuiltinFunction(
        name="random_int_between",
        signature=FunctionSignature(
            name="random_int_between",
            parameter_types=(RANDOM, INT, INT),
            return_type=RESULT,
        ),
        implementation=_random_int_between,
        documentation="Return an unbiased inclusive integer-range result.",
    ),
    BuiltinFunction(
        name="random_float_unit",
        signature=FunctionSignature(
            name="random_float_unit",
            parameter_types=(RANDOM,),
            return_type=FLOAT,
        ),
        implementation=_random_float_unit,
        documentation="Return a deterministic binary64 value in [0, 1).",
    ),
    BuiltinFunction(
        name="random_bool",
        signature=FunctionSignature(
            name="random_bool",
            parameter_types=(RANDOM,),
            return_type=BOOL,
        ),
        implementation=_random_bool,
        documentation="Return one deterministic boolean sample.",
    ),
    BuiltinFunction(
        name="random_chance",
        signature=FunctionSignature(
            name="random_chance",
            parameter_types=(RANDOM, INT, INT),
            return_type=RESULT,
        ),
        implementation=_random_chance,
        documentation="Evaluate an exact numerator-over-denominator chance.",
    ),
    BuiltinFunction(
        name="random_collection_index",
        signature=FunctionSignature(
            name="random_collection_index",
            parameter_types=(RANDOM, COLLECTION),
            return_type=RESULT,
        ),
        implementation=_random_collection_index,
        documentation="Choose a deterministic valid collection index.",
    ),
    BuiltinFunction(
        name="random_shuffle",
        signature=FunctionSignature(
            name="random_shuffle",
            parameter_types=(RANDOM, COLLECTION),
            return_type=COLLECTION,
        ),
        implementation=_random_shuffle,
        documentation="Return a deterministic Fisher-Yates permutation.",
    ),
    BuiltinFunction(
        name="random_fork",
        signature=FunctionSignature(
            name="random_fork",
            parameter_types=(RANDOM, INT),
            return_type=RANDOM,
        ),
        implementation=_random_fork,
        documentation="Derive a deterministic child stream by stream ID.",
    ),
    BuiltinFunction(
        name="random_equal",
        signature=FunctionSignature(
            name="random_equal",
            parameter_types=(RANDOM, RANDOM),
            return_type=BOOL,
        ),
        implementation=_random_equal,
        documentation="Return whether two random stream states are equal.",
    ),
)


__all__ = ("RANDOM_BUILTINS",)