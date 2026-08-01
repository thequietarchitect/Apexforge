"""AFP-P10.8 deterministic UTC time utilities smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    MAX_TIME_TEXT_CODE_POINTS,
    MAX_UNIX_MILLISECONDS,
    MIN_UNIX_MILLISECONDS,
    P10_STANDARD_LIBRARY_VERSION,
    RuntimeCollection,
    RuntimeResult,
    RuntimeTime,
    TIME_BUILTINS,
    UNIX_EPOCH,
)
from type_system.closure import collect_linked_specializations
from type_system.freeze import audit_lowered_generics
from type_system.lowering import lower_linked_generics
from type_system.model import (
    COLLECTION,
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
    require(len(TIME_BUILTINS) == 20, "time built-in count changed")
    require(MAX_TIME_TEXT_CODE_POINTS == 64, "time text limit changed")
    require(
        resolve_builtin_type("time") is TIME,
        "time type did not resolve",
    )
    require(is_builtin_type("time"), "time type not registered")

    expected_names = {
        "time_unix_epoch",
        "time_from_unix_milliseconds",
        "time_from_utc",
        "time_parse_iso_utc",
        "result_time_or",
        "time_to_unix_milliseconds",
        "time_to_iso_utc",
        "time_year",
        "time_month",
        "time_day",
        "time_hour",
        "time_minute",
        "time_second",
        "time_millisecond",
        "time_add_milliseconds",
        "time_add_seconds",
        "time_difference_milliseconds",
        "time_compare",
        "time_before",
        "time_after",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "time registry entries are incomplete",
    )

    epoch = call("time_unix_epoch")
    require(type(epoch) is RuntimeTime, "epoch did not return RuntimeTime")
    require(epoch is UNIX_EPOCH, "epoch singleton identity changed")
    require(
        call("time_to_iso_utc", epoch) == "1970-01-01T00:00:00.000Z",
        "epoch ISO rendering changed",
    )
    require(
        call("time_to_unix_milliseconds", epoch) == 0,
        "epoch milliseconds changed",
    )

    before_epoch_result = call("time_from_unix_milliseconds", -1)
    require(
        type(before_epoch_result) is RuntimeResult
        and before_epoch_result.ok
        and before_epoch_result.payload_type is TIME,
        "negative Unix-millisecond construction failed",
    )
    before_epoch = call("result_time_or", before_epoch_result, epoch)
    require(
        call("time_to_iso_utc", before_epoch)
        == "1969-12-31T23:59:59.999Z",
        "negative Unix-millisecond rendering changed",
    )

    leap_result = call(
        "time_from_utc",
        2024,
        2,
        29,
        23,
        59,
        58,
        7,
    )
    require(leap_result.ok, "valid leap-day construction failed")
    leap = call("result_time_or", leap_result, epoch)
    require(
        call("time_to_iso_utc", leap)
        == "2024-02-29T23:59:58.007Z",
        "UTC field construction changed",
    )
    require(call("time_year", leap) == 2024, "year extraction failed")
    require(call("time_month", leap) == 2, "month extraction failed")
    require(call("time_day", leap) == 29, "day extraction failed")
    require(call("time_hour", leap) == 23, "hour extraction failed")
    require(call("time_minute", leap) == 59, "minute extraction failed")
    require(call("time_second", leap) == 58, "second extraction failed")
    require(call("time_millisecond", leap) == 7, "millisecond extraction failed")

    invalid_day = call(
        "time_from_utc",
        2023,
        2,
        29,
        0,
        0,
        0,
        0,
    )
    require(
        invalid_day.is_error
        and invalid_day.error_code == "INVALID_TIME_COMPONENT",
        "invalid calendar fields did not return structured failure",
    )

    parsed = call(
        "time_parse_iso_utc",
        "2000-01-02T03:04:05.006Z",
    )
    require(parsed.ok and parsed.payload_type is TIME, "strict parse failed")
    parsed_time = call("result_time_or", parsed, epoch)
    require(
        call("time_to_iso_utc", parsed_time)
        == "2000-01-02T03:04:05.006Z",
        "strict parse round trip changed",
    )
    require(
        call("time_parse_iso_utc", "2000-01-02T03:04:05Z").error_code
        == "INVALID_TIME_FORMAT",
        "missing milliseconds parsed unexpectedly",
    )
    require(
        call(
            "time_parse_iso_utc",
            "2000-01-02T03:04:05.006+00:00",
        ).error_code
        == "INVALID_TIME_FORMAT",
        "offset syntax parsed unexpectedly",
    )
    require(
        call("time_parse_iso_utc", " " * 65).error_code
        == "TIME_INPUT_TOO_LONG",
        "time text limit was not enforced",
    )

    plus_second_result = call("time_add_seconds", epoch, 1)
    plus_second = call("result_time_or", plus_second_result, epoch)
    require(
        call("time_to_iso_utc", plus_second)
        == "1970-01-01T00:00:01.000Z",
        "second addition failed",
    )
    plus_millisecond = call(
        "result_time_or",
        call("time_add_milliseconds", plus_second, 250),
        epoch,
    )
    require(
        call("time_difference_milliseconds", plus_millisecond, epoch)
        == 1250,
        "millisecond difference failed",
    )
    require(
        call("time_compare", epoch, plus_second) == -1,
        "time comparison failed",
    )
    require(
        call("time_before", epoch, plus_second) is True,
        "time_before failed",
    )
    require(
        call("time_after", plus_second, epoch) is True,
        "time_after failed",
    )

    minimum = RuntimeTime(MIN_UNIX_MILLISECONDS)
    maximum = RuntimeTime(MAX_UNIX_MILLISECONDS)
    require(
        call("time_add_milliseconds", maximum, 1).error_code
        == "TIME_OVERFLOW",
        "upper-bound overflow was not contained",
    )
    require(
        call("time_add_milliseconds", minimum, -1).error_code
        == "TIME_OVERFLOW",
        "lower-bound overflow was not contained",
    )

    try:
        epoch.unix_milliseconds = 1
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("RuntimeTime was mutable")

    preserved = call("identity", parsed_time)
    require(preserved is parsed_time, "identity did not preserve time")
    chosen = call("choose", True, parsed_time, epoch)
    require(chosen is parsed_time, "choose did not transport time")

    time_collection = call("collection_single", parsed_time)
    require(
        type(time_collection) is RuntimeCollection
        and time_collection.element_type is TIME
        and time_collection.values == (parsed_time,),
        "time did not travel through immutable collection",
    )
    time_result = call("time_parse_iso_utc", "2025-01-01T00:00:00.000Z")
    require(
        type(time_result) is RuntimeResult
        and time_result.payload_type is TIME
        and time_result.ok,
        "time did not travel through structured result",
    )

    parse_program = compile_source(
        """
        function ParseOrEpoch(text : string) : time {
            return result_time_or(
                time_parse_iso_utc(text),
                time_unix_epoch()
            )
        }
        """
    )
    year_program = compile_source(
        """
        function ReadYear(value : time) : int {
            return time_year(value)
        }
        """
    )
    keep_program = compile_source(
        """
        function KeepTime(value : time) : collection {
            return collection_single(identity(value))
        }
        """
    )
    add_program = compile_source(
        """
        function AddSecond(value : time) : result {
            return time_add_seconds(value, 1)
        }
        """
    )
    linked = link_programs(
        parse_program,
        year_program,
        keep_program,
        add_program,
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
        "identity<time>" in manifest.canonical_ids,
        "time identity specialization missing",
    )
    require(
        "collection_single<time>" in manifest.canonical_ids,
        "time collection specialization missing",
    )

    lowered = lower_linked_generics(
        linked,
        external_signatures=host_signatures,
        host_generic_targets=host_generic_targets,
    )
    RuntimeValidator().validate(lowered.program)
    audit = audit_lowered_generics(lowered)
    require(audit.closed, "lowered time generic closure is open")
    require(
        lowered.specialized_functions == (),
        "host time generics emitted AIR functions",
    )

    engine = RuntimeEngine()
    functions = runtime_index(lowered.program)
    compiled_time = engine._evaluate_expression(
        AIRCallExpression(
            target="ParseOrEpoch",
            arguments=(
                AIRStringLiteral("2030-06-07T08:09:10.011Z"),
            ),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        type(compiled_time) is RuntimeTime
        and compiled_time.to_iso_utc()
        == "2030-06-07T08:09:10.011Z",
        "compiled time parsing failed",
    )
    compiled_year = engine._evaluate_expression(
        AIRCallExpression(
            target="ReadYear",
            arguments=(compiled_time,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(compiled_year == 2030, "compiled time field access failed")

    compiled_collection = engine._evaluate_expression(
        AIRCallExpression(
            target="KeepTime",
            arguments=(compiled_time,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_collection.element_type is TIME
        and compiled_collection.values == (compiled_time,),
        "compiled generic time transport failed",
    )
    compiled_add = engine._evaluate_expression(
        AIRCallExpression(
            target="AddSecond",
            arguments=(compiled_time,),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(
        compiled_add.ok
        and compiled_add.payload_type is TIME
        and compiled_add.value.to_iso_utc()
        == "2030-06-07T08:09:11.011Z",
        "compiled time arithmetic failed",
    )

    require(RESULT is not TIME, "time collapsed into result type")
    require(COLLECTION is not TIME, "time collapsed into collection type")

    print("AFP-P10.8 deterministic UTC time utilities smoke test passed.")
    print("Canonical opaque time type: PASS")
    print("Strict UTC construction and parsing: PASS")
    print("Millisecond-precision rendering: PASS")
    print("Bounded deterministic arithmetic: PASS")
    print("Comparison and field extraction: PASS")
    print("Result and collection transport: PASS")
    print("Host-generic closure and lowering: PASS")
    print("Compiled runtime dispatch: PASS")


if __name__ == "__main__":
    main()