"""AFP-P10.9 deterministic random utilities smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
)
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    P10_STANDARD_LIBRARY_VERSION,
    RANDOM_BUILTINS,
    RuntimeCollection,
    RuntimeRandom,
    RuntimeResult,
    SPLITMIX64_GAMMA,
    UINT64_MASK,
    UINT64_MODULUS,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.lowering import lower_linked_generics
from type_system.model import (
    COLLECTION,
    RANDOM,
    RESULT,
    TIME,
    is_builtin_type,
    resolve_builtin_type,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call(name: str, *arguments):
    return DEFAULT_STANDARD_LIBRARY.invoke(name, tuple(arguments))


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.12", "version changed")
    require(len(RANDOM_BUILTINS) == 14, "random built-in count changed")
    require(UINT64_MODULUS == 1 << 64, "u64 modulus changed")
    require(UINT64_MASK == (1 << 64) - 1, "u64 mask changed")
    require(
        SPLITMIX64_GAMMA == 0x9E3779B97F4A7C15,
        "SplitMix64 gamma changed",
    )
    require(
        resolve_builtin_type("random") is RANDOM,
        "random type did not resolve",
    )
    require(is_builtin_type("random"), "random type not registered")

    expected_names = {
        "random_from_seed",
        "random_state",
        "random_advance",
        "random_advance_by",
        "result_random_or",
        "random_u64",
        "random_int_between",
        "random_float_unit",
        "random_bool",
        "random_chance",
        "random_collection_index",
        "random_shuffle",
        "random_fork",
        "random_equal",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "random registry entries are incomplete",
    )

    zero = call("random_from_seed", 0)
    zero_again = call("random_from_seed", 0)
    require(type(zero) is RuntimeRandom, "seed did not return RuntimeRandom")
    require(zero == zero_again, "equal seeds produced unequal streams")
    require(call("random_state", zero) == 0, "seed state changed")
    require(
        call("random_u64", zero) == 16294208416658607535,
        "first SplitMix64 reference vector changed",
    )

    next_zero = call("random_advance", zero)
    require(
        call("random_state", next_zero) == SPLITMIX64_GAMMA,
        "single stream advance changed",
    )
    require(
        call("random_u64", next_zero) == 7960286522194355700,
        "second SplitMix64 reference vector changed",
    )
    require(
        call("random_state", zero) == 0,
        "random operation mutated its input stream",
    )

    two_steps = call(
        "result_random_or",
        call("random_advance_by", zero, 2),
        zero,
    )
    require(
        two_steps == call("random_advance", next_zero),
        "advance_by disagreed with repeated advance",
    )
    negative_advance = call("random_advance_by", zero, -1)
    require(
        negative_advance.is_error
        and negative_advance.payload_type is RANDOM
        and negative_advance.error_code == "NEGATIVE_RANDOM_ADVANCE",
        "negative stream advance was not contained",
    )
    huge_advance = call("random_advance_by", zero, UINT64_MODULUS)
    require(
        huge_advance.is_error
        and huge_advance.error_code == "RANDOM_ADVANCE_TOO_LARGE",
        "oversized stream advance was not contained",
    )
    require(
        call("result_random_or", negative_advance, next_zero) is next_zero,
        "random fallback extraction changed",
    )

    negative_seed = call("random_from_seed", -1)
    require(
        call("random_state", negative_seed) == UINT64_MASK,
        "negative seed normalization changed",
    )

    die = call("random_int_between", zero, 1, 6)
    require(
        type(die) is RuntimeResult
        and die.ok
        and die.payload_type.name == "int"
        and die.value == 2,
        "inclusive deterministic integer draw changed",
    )
    require(
        call("random_int_between", zero, 6, 1).error_code
        == "INVALID_RANDOM_RANGE",
        "inverted integer range did not fail",
    )
    require(
        call(
            "random_int_between",
            zero,
            0,
            UINT64_MODULUS,
        ).error_code
        == "RANDOM_RANGE_TOO_WIDE",
        "oversized integer range did not fail",
    )

    unit = call("random_float_unit", zero)
    require(type(unit) is float, "unit draw did not return float")
    require(0.0 <= unit < 1.0, "unit draw escaped [0, 1)")
    require(
        unit == 0.8833108082136426,
        "unit-float reference vector changed",
    )
    require(call("random_bool", zero) is True, "boolean draw changed")

    impossible = call("random_chance", zero, 0, 7)
    certain = call("random_chance", zero, 7, 7)
    half = call("random_chance", zero, 1, 2)
    require(impossible.ok and impossible.value is False, "zero chance changed")
    require(certain.ok and certain.value is True, "certain chance changed")
    require(half.ok and half.value is False, "half chance vector changed")
    require(
        call("random_chance", zero, 1, 0).error_code
        == "INVALID_RANDOM_DENOMINATOR",
        "zero denominator did not fail",
    )
    require(
        call("random_chance", zero, 8, 7).error_code
        == "INVALID_RANDOM_NUMERATOR",
        "invalid chance numerator did not fail",
    )

    values = RuntimeCollection.from_values((0, 1, 2, 3, 4))
    index_result = call("random_collection_index", zero, values)
    require(
        index_result.ok
        and index_result.value == 0,
        "collection-index reference vector changed",
    )
    empty = RuntimeCollection(values.element_type, ())
    require(
        call("random_collection_index", zero, empty).error_code
        == "EMPTY_RANDOM_COLLECTION",
        "empty collection choice did not fail",
    )

    shuffled = call("random_shuffle", zero, values)
    shuffled_again = call("random_shuffle", zero, values)
    require(
        type(shuffled) is RuntimeCollection
        and shuffled.element_type is values.element_type,
        "shuffle lost collection type",
    )
    require(
        shuffled.values == (2, 3, 1, 4, 0),
        "Fisher-Yates reference permutation changed",
    )
    require(shuffled == shuffled_again, "shuffle was not deterministic")
    require(
        tuple(sorted(shuffled.values)) == values.values,
        "shuffle changed collection membership",
    )

    fork_42 = call("random_fork", zero, 42)
    fork_42_again = call("random_fork", zero, 42)
    fork_43 = call("random_fork", zero, 43)
    require(
        fork_42 == fork_42_again,
        "equal fork IDs produced unequal streams",
    )
    require(
        fork_42 != fork_43,
        "different fork IDs collapsed to one stream",
    )
    require(
        call("random_equal", fork_42, fork_42_again) is True,
        "random_equal rejected equal states",
    )
    require(
        call("random_equal", fork_42, fork_43) is False,
        "random_equal accepted unequal states",
    )

    try:
        zero.state = 1
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("RuntimeRandom was mutable")

    preserved = call("identity", zero)
    require(preserved is zero, "identity did not preserve random state")
    chosen = call("choose", True, zero, next_zero)
    require(chosen is zero, "choose did not transport random state")

    random_collection = call("collection_single", zero)
    require(
        type(random_collection) is RuntimeCollection
        and random_collection.element_type is RANDOM
        and random_collection.values == (zero,),
        "random state did not travel through immutable collection",
    )
    random_result = call("random_advance_by", zero, 3)
    require(
        type(random_result) is RuntimeResult
        and random_result.ok
        and random_result.payload_type is RANDOM
        and type(random_result.value) is RuntimeRandom,
        "random state did not travel through structured result",
    )

    seed_program = compile_source(
        """
        function Seed(value : int) : random {
            return random_from_seed(value)
        }
        """
    )
    roll_program = compile_source(
        """
        function Roll(value : random) : int {
            return result_int_or(
                random_int_between(value, 1, 6),
                0
            )
        }
        """
    )
    keep_program = compile_source(
        """
        function KeepRandom(value : random) : collection {
            return collection_single(identity(value))
        }
        """
    )
    fork_program = compile_source(
        """
        function ForkRandom(value : random, stream : int) : random {
            return random_fork(value, stream)
        }
        """
    )
    linked = link_programs(
        seed_program,
        roll_program,
        keep_program,
        fork_program,
    )
    RuntimeValidator().validate(linked)

    host_signatures = DEFAULT_STANDARD_LIBRARY.signatures()
    host_generic_targets = tuple(
        entry.name
        for entry in DEFAULT_STANDARD_LIBRARY.entries
        if entry.is_generic
    )
    manifest = collect_linked_specializations(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    require(
        "identity<random>" in manifest.canonical_ids,
        "random identity specialization missing",
    )
    require(
        "collection_single<random>" in manifest.canonical_ids,
        "random collection specialization missing",
    )

    lowered = lower_linked_generics(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    RuntimeValidator().validate(lowered.program)
    audit = audit_lowered_generics(lowered)
    require(audit.closed, "lowered random generic closure is open")
    require(
        lowered.specialized_functions == (),
        "host random generics emitted AIR functions",
    )

    engine = RuntimeEngine()
    functions = runtime_index(lowered.program)
    compiled_random = engine._evaluate_expression(
        AIRCallExpression(
            target="Seed",
            arguments=(AIRIntegerLiteral(0),),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        type(compiled_random) is RuntimeRandom
        and compiled_random == zero,
        "compiled random seed dispatch failed",
    )
    compiled_roll = engine._evaluate_expression(
        AIRCallExpression(
            target="Roll",
            arguments=(compiled_random,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(compiled_roll == 2, "compiled random integer draw failed")
    compiled_collection = engine._evaluate_expression(
        AIRCallExpression(
            target="KeepRandom",
            arguments=(compiled_random,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_collection.element_type is RANDOM
        and compiled_collection.values == (compiled_random,),
        "compiled generic random transport failed",
    )
    compiled_fork = engine._evaluate_expression(
        AIRCallExpression(
            target="ForkRandom",
            arguments=(compiled_random, AIRIntegerLiteral(42)),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_fork == fork_42,
        "compiled random fork dispatch failed",
    )

    require(RESULT is not RANDOM, "random collapsed into result type")
    require(COLLECTION is not RANDOM, "random collapsed into collection type")
    require(TIME is not RANDOM, "random collapsed into time type")

    print("AFP-P10.9 deterministic random utilities smoke test passed.")
    print("Canonical opaque random type: PASS")
    print("Fixed SplitMix64 reference vectors: PASS")
    print("Explicit immutable stream advancement: PASS")
    print("Unbiased integer and collection sampling: PASS")
    print("Deterministic boolean, chance, fork, and shuffle: PASS")
    print("Result and collection transport: PASS")
    print("Host-generic closure and lowering: PASS")
    print("Compiled runtime dispatch: PASS")


if __name__ == "__main__":
    main()