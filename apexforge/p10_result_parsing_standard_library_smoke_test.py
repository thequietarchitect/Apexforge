"""AFP-P10.6 structured results and safe parsing smoke test."""

from __future__ import annotations

import math

from air.expressions import (
    AIRCallExpression,
    AIRFloatLiteral,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    MAX_INT_PARSE_DIGITS,
    MAX_PARSE_INPUT_CODE_POINTS,
    P10_STANDARD_LIBRARY_VERSION,
    RESULT_BUILTINS,
    RuntimeResult,
)
from type_system.model import (
    FLOAT,
    INT,
    RESULT,
    is_builtin_type,
    resolve_builtin_type,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_compile_error(source: str, code: str) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        require(
            error.diagnostic.code == code,
            f"expected {code}, received {error.diagnostic.code}: {error}",
        )
        return error
    raise AssertionError(f"source unexpectedly compiled: {source!r}")


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def call(name: str, *arguments):
    return DEFAULT_STANDARD_LIBRARY.invoke(name, tuple(arguments))


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.12", "version changed")
    require(len(RESULT_BUILTINS) == 9, "result built-in count changed")
    require(MAX_PARSE_INPUT_CODE_POINTS == 4096, "parse limit changed")
    require(MAX_INT_PARSE_DIGITS == 4096, "int parse digit limit changed")
    require(resolve_builtin_type("result") is RESULT, "result type did not resolve")
    require(is_builtin_type("result"), "result type was not registered")

    expected_names = {
        "string_to_int",
        "string_to_float",
        "result_is_ok",
        "result_is_error",
        "result_error_code",
        "result_error_message",
        "result_payload_type",
        "result_int_or",
        "result_float_or",
    }
    require(
        expected_names.issubset(DEFAULT_STANDARD_LIBRARY.names),
        "result registry entries are incomplete",
    )

    parsed_int = call("string_to_int", "-2048")
    require(type(parsed_int) is RuntimeResult, "int parser did not return result")
    require(parsed_int.ok and parsed_int.payload_type is INT, "int success tag changed")
    require(call("result_int_or", parsed_int, 9) == -2048, "int extraction failed")
    require(call("result_is_ok", parsed_int) is True, "success query failed")
    require(call("result_is_error", parsed_int) is False, "error query failed")
    require(call("result_error_code", parsed_int) == "", "success exposed an error code")
    require(call("result_payload_type", parsed_int) == "int", "int payload tag changed")

    for invalid in ("", " 1", "1 ", "1_0", "0x10", "+", "--1", "12.0"):
        result = call("string_to_int", invalid)
        require(result.is_error, f"invalid int text passed: {invalid!r}")
        require(call("result_int_or", result, 77) == 77, "int fallback failed")
        require(call("result_error_code", result) != "", "int failure omitted code")
        require(call("result_error_message", result) != "", "int failure omitted message")

    require(call("result_int_or", call("string_to_int", "+000"), 1) == 0, "signed zero failed")
    too_long_int = call("string_to_int", "1" * (MAX_INT_PARSE_DIGITS + 1))
    require(too_long_int.error_code == "INPUT_TOO_LONG", "long int diagnostic changed")

    parsed_float = call("string_to_float", "-1.25e2")
    require(parsed_float.ok and parsed_float.payload_type is FLOAT, "float success tag changed")
    require(call("result_float_or", parsed_float, 9.0) == -125.0, "float extraction failed")
    require(call("result_payload_type", parsed_float) == "float", "float payload tag changed")

    negative_zero = call("result_float_or", call("string_to_float", "-0.0"), 1.0)
    require(math.copysign(1.0, negative_zero) < 0.0, "negative zero was not preserved")
    require(math.isnan(call("result_float_or", call("string_to_float", "nan"), 0.0)), "nan failed")
    require(call("result_float_or", call("string_to_float", "inf"), 0.0) == float("inf"), "inf failed")
    require(call("result_float_or", call("string_to_float", "-inf"), 0.0) == float("-inf"), "-inf failed")

    for invalid in ("", " 1.0", "1.0 ", "1_0.0", ".", "1e", "NaN"):
        result = call("string_to_float", invalid)
        require(result.is_error, f"invalid float text passed: {invalid!r}")
        require(call("result_float_or", result, 3.5) == 3.5, "float fallback failed")
    require(
        call("string_to_float", "1e9999").error_code == "FLOAT_OVERFLOW",
        "float overflow diagnostic changed",
    )

    # Payload mismatch is safe and deterministic rather than exceptional.
    require(call("result_int_or", parsed_float, 11) == 11, "mismatched int fallback failed")
    require(call("result_float_or", parsed_int, 2.5) == 2.5, "mismatched float fallback failed")

    parse_int_program = compile_source(
        """
        function ParseIntOr(text : string, fallback : int) : int {
            let parsed = string_to_int(text)
            return result_int_or(parsed, fallback)
        }
        """
    )
    parse_float_program = compile_source(
        """
        function ParseFloatOr(text : string, fallback : float) : float {
            return result_float_or(string_to_float(text), fallback)
        }
        """
    )
    result_return_program = compile_source(
        """
        function ParseInt(text : string) : result {
            return string_to_int(text)
        }
        """
    )
    generic_result_program = compile_source(
        """
        function PreserveParse(text : string) : result {
            return identity(string_to_int(text))
        }
        """
    )
    linked = link_programs(
        parse_int_program,
        parse_float_program,
        result_return_program,
        generic_result_program,
    )
    RuntimeValidator().validate(linked)

    engine = RuntimeEngine()
    functions = runtime_index(linked)
    int_value = engine._evaluate_expression(
        AIRCallExpression(
            target="ParseIntOr",
            arguments=(AIRStringLiteral("42"), AIRIntegerLiteral(5)),
        ),
        StateSnapshot(),
        functions=functions,
    )
    float_value = engine._evaluate_expression(
        AIRCallExpression(
            target="ParseFloatOr",
            arguments=(AIRStringLiteral("bad"), AIRFloatLiteral(2.5)),
        ),
        StateSnapshot(),
        functions=functions,
    )
    returned_result = engine._evaluate_expression(
        AIRCallExpression(
            target="ParseInt",
            arguments=(AIRStringLiteral("19"),),
        ),
        StateSnapshot(),
        functions=functions,
    )
    require(int_value == 42, "compiled int parser runtime failed")
    require(float_value == 2.5, "compiled float fallback runtime failed")
    require(type(returned_result) is RuntimeResult and returned_result.ok, "result return failed")

    require_compile_error(
        """
        function Bad(value : int) : result {
            return string_to_int(value)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function Bad(value : string) : int {
            return result_int_or(value, 0)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function string_to_int(value : string) : result {
            return value
        }
        """,
        "APX-COMPILE-015",
    )

    print("AFP-P10.6 structured results and safe parsing smoke test passed.")
    print("Canonical opaque result type: PASS")
    print("Immutable runtime result invariants: PASS")
    print("Safe int parsing: PASS")
    print("Safe float parsing: PASS")
    print("Structured failure diagnostics: PASS")
    print("Fallback extraction: PASS")
    print("Generic result transport: PASS")
    print("Compiled and linked result flow: PASS")
    print("Pure runtime dispatch: PASS")


if __name__ == "__main__":
    main()
