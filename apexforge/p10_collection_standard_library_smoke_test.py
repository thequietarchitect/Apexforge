"""AFP-P10.7 immutable collection utilities smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    COLLECTION_BUILTINS,
    DEFAULT_STANDARD_LIBRARY,
    MAX_COLLECTION_LENGTH,
    P10_STANDARD_LIBRARY_VERSION,
    RuntimeCollection,
    RuntimeResult,
    StandardLibraryInvocationError,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.lowering import lower_linked_generics
from type_system.model import (
    COLLECTION,
    INT,
    RESULT,
    is_builtin_type,
    resolve_builtin_type,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def call(name: str, *arguments):
    return DEFAULT_STANDARD_LIBRARY.invoke(name, tuple(arguments))


def require_invocation_error(
    name: str,
    arguments: tuple[object, ...],
    code: str,
) -> StandardLibraryInvocationError:
    try:
        DEFAULT_STANDARD_LIBRARY.invoke(name, arguments)
    except StandardLibraryInvocationError as error:
        require(
            error.code == code,
            f"expected {code}, received {error.code}: {error}",
        )
        return error
    raise AssertionError(
        f"{name}{arguments!r} unexpectedly succeeded"
    )


def require_compile_error(source: str) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        return error
    raise AssertionError(f"source unexpectedly compiled: {source!r}")


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.12", "version changed")
    require(len(COLLECTION_BUILTINS) == 16, "collection built-in count changed")
    require(MAX_COLLECTION_LENGTH == 4096, "collection limit changed")
    require(
        resolve_builtin_type("collection") is COLLECTION,
        "collection type did not resolve",
    )
    require(is_builtin_type("collection"), "collection type not registered")

    expected_names = {
        "collection_single",
        "collection_pair",
        "collection_repeat",
        "collection_length",
        "collection_is_empty",
        "collection_element_type",
        "collection_append",
        "collection_prepend",
        "collection_concat",
        "collection_contains",
        "collection_count",
        "collection_get_or",
        "collection_first_or",
        "collection_last_or",
        "collection_slice",
        "collection_reverse",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "collection registry entries are incomplete",
    )

    single = call("collection_single", 2)
    require(type(single) is RuntimeCollection, "single did not return collection")
    require(single.element_type is INT, "single element type changed")
    require(single.values == (2,), "single contents changed")

    pair = call("collection_pair", 2, 3)
    require(pair.values == (2, 3), "pair contents changed")
    repeated = call("collection_repeat", 4, 3)
    require(repeated.values == (4, 4, 4), "repeat contents changed")
    empty = call("collection_repeat", 4, 0)
    require(empty.values == (), "typed empty collection changed")
    require(empty.element_type is INT, "empty collection lost element type")
    require(call("collection_is_empty", empty) is True, "empty query failed")
    require(call("collection_length", pair) == 2, "length failed")
    require(
        call("collection_element_type", pair) == "int",
        "element type query failed",
    )

    appended = call("collection_append", pair, 5)
    prepended = call("collection_prepend", 1, appended)
    require(pair.values == (2, 3), "append mutated its input")
    require(appended.values == (2, 3, 5), "append result changed")
    require(prepended.values == (1, 2, 3, 5), "prepend result changed")

    concatenated = call(
        "collection_concat",
        pair,
        call("collection_pair", 4, 5),
    )
    require(
        concatenated.values == (2, 3, 4, 5),
        "concat contents changed",
    )
    require(
        call("collection_contains", concatenated, 3) is True,
        "contains failed",
    )
    require(
        call(
            "collection_count",
            call("collection_repeat", 7, 3),
            7,
        )
        == 3,
        "count failed",
    )
    require(
        call("collection_get_or", concatenated, 2, 99) == 4,
        "indexed access failed",
    )
    require(
        call("collection_get_or", concatenated, -1, 99) == 99,
        "negative index should use fallback",
    )
    require(
        call("collection_get_or", concatenated, 99, 88) == 88,
        "large index should use fallback",
    )
    require(
        call("collection_first_or", empty, 11) == 11,
        "empty first fallback failed",
    )
    require(
        call("collection_last_or", concatenated, 11) == 5,
        "last access failed",
    )
    require(
        call("collection_slice", concatenated, 1, 3).values == (3, 4),
        "strict slice failed",
    )
    require(
        call("collection_reverse", concatenated).values == (5, 4, 3, 2),
        "reverse failed",
    )

    parsed = call("string_to_int", "42")
    require(type(parsed) is RuntimeResult and parsed.ok, "result fixture failed")
    result_collection = call("collection_single", parsed)
    result_fallback = call("string_to_int", "0")
    recovered = call(
        "collection_get_or",
        result_collection,
        0,
        result_fallback,
    )
    require(
        type(recovered) is RuntimeResult
        and recovered.payload_type is INT
        and recovered.value == 42,
        "result values did not travel through collections",
    )

    nested = call("collection_single", pair)
    nested_fallback = call("collection_single", 0)
    require(
        call("collection_get_or", nested, 0, nested_fallback) == pair,
        "nested collection transport failed",
    )

    require_invocation_error(
        "collection_append",
        (pair, "wrong"),
        "APX-STDLIB-011",
    )
    require_invocation_error(
        "collection_concat",
        (pair, call("collection_single", "wrong")),
        "APX-STDLIB-011",
    )
    require_invocation_error(
        "collection_repeat",
        (1, -1),
        "APX-STDLIB-012",
    )
    require_invocation_error(
        "collection_slice",
        (pair, 0, 3),
        "APX-STDLIB-012",
    )
    require_invocation_error(
        "collection_repeat",
        (1, MAX_COLLECTION_LENGTH + 1),
        "APX-STDLIB-010",
    )

    build_program = compile_source(
        """
        function Build(value : int) : collection {
            return collection_repeat(value, 3)
        }
        """
    )
    read_program = compile_source(
        """
        function Read(
            values : collection,
            index : int,
            fallback : int
        ) : int {
            return collection_get_or(values, index, fallback)
        }
        """
    )
    preserve_program = compile_source(
        """
        function Preserve(values : collection) : collection {
            return identity(values)
        }
        """
    )
    result_transport_program = compile_source(
        """
        function ParseOnly(text : string) : collection {
            return collection_single(string_to_int(text))
        }
        """
    )
    linked = link_programs(
        build_program,
        read_program,
        preserve_program,
        result_transport_program,
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
        "collection_get_or<int>" in manifest.canonical_ids,
        "get_or host specialization missing",
    )
    require(
        "collection_repeat<int>" in manifest.canonical_ids,
        "repeat host specialization missing",
    )
    require(
        "collection_single<result>" in manifest.canonical_ids,
        "result collection specialization missing",
    )
    require(
        "identity<collection>" in manifest.canonical_ids,
        "collection identity specialization missing",
    )

    lowered = lower_linked_generics(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    RuntimeValidator().validate(lowered.program)
    audit = audit_lowered_generics(lowered)
    require(audit.closed, "lowered collection generic closure is open")
    require(
        lowered.specialized_functions == (),
        "host collection generics emitted AIR functions",
    )

    engine = RuntimeEngine()
    functions = runtime_index(lowered.program)
    built = engine._evaluate_expression(
        AIRCallExpression(
            target="Build",
            arguments=(AIRIntegerLiteral(6),),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        type(built) is RuntimeCollection
        and built.values == (6, 6, 6),
        "compiled collection construction failed",
    )
    read = engine._evaluate_expression(
        AIRCallExpression(
            target="Read",
            arguments=(
                AIRCallExpression(
                    target="Build",
                    arguments=(AIRIntegerLiteral(8),),
                ),
                AIRIntegerLiteral(1),
                AIRIntegerLiteral(0),
            ),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(read == 8, "compiled collection access failed")
    parsed_values = engine._evaluate_expression(
        AIRCallExpression(
            target="ParseOnly",
            arguments=(AIRStringLiteral("17"),),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        parsed_values.element_type is RESULT
        and parsed_values.values[0].value == 17,
        "compiled result collection failed",
    )

    mismatch = require_compile_error(
        """
        function Bad() : collection {
            return collection_pair(1, "wrong")
        }
        """
    )
    require(
        mismatch.diagnostic.code.startswith("APX-TYPE-"),
        f"unexpected mismatch diagnostic: {mismatch}",
    )
    reserved = require_compile_error(
        """
        function collection_single(value : int) : collection {
            return value
        }
        """
    )
    require(
        reserved.diagnostic.code == "APX-COMPILE-015",
        f"reserved-name diagnostic changed: {reserved}",
    )

    print("AFP-P10.7 immutable collection utilities smoke test passed.")
    print("Canonical opaque collection type: PASS")
    print("Immutable homogeneous runtime values: PASS")
    print("Typed empty collections: PASS")
    print("Bounded construction and concatenation: PASS")
    print("Safe fallback access: PASS")
    print("Strict slicing and deterministic errors: PASS")
    print("Nested result and collection transport: PASS")
    print("Host-generic closure and lowering: PASS")
    print("Compiled runtime dispatch: PASS")


if __name__ == "__main__":
    main()