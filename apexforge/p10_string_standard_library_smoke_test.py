"""AFP-P10.3 deterministic string standard-library smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRCallExpression,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine, RuntimeExpressionError
from runtime.state import StateSnapshot
from standard_library import (
    CORE_BUILTINS,
    DEFAULT_STANDARD_LIBRARY,
    MAX_STRING_RESULT_CODE_POINTS,
    NUMERIC_BUILTINS,
    P10_STANDARD_LIBRARY_VERSION,
    STRING_BUILTINS,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def evaluate(engine, program, target, *arguments):
    return engine._evaluate_expression(
        AIRCallExpression(target=target, arguments=tuple(arguments)),
        StateSnapshot(),
        functions=runtime_index(program),
    )


def require_compile_error(source: str, code: str) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        require(
            error.diagnostic.code == code,
            f"expected {code}, received {error.diagnostic.code}: {error}",
        )
        return error
    raise AssertionError(
        f"source unexpectedly compiled; expected {code}: {source!r}"
    )


def require_runtime_error(operation, code: str) -> RuntimeExpressionError:
    try:
        operation()
    except RuntimeExpressionError as error:
        require(code in str(error), f"expected {code}, received: {error}")
        return error
    raise AssertionError(f"operation unexpectedly passed; expected {code}")


def main() -> None:
    require(P10_STANDARD_LIBRARY_VERSION == "10.5", "version changed")
    require(len(CORE_BUILTINS) == 5, "P10.1 core count changed")
    require(len(NUMERIC_BUILTINS) == 11, "P10.2 numeric count changed")
    require(len(STRING_BUILTINS) == 10, "P10.3 string count changed")
    require(
        MAX_STRING_RESULT_CODE_POINTS == 1_000_000,
        "string result ceiling changed",
    )

    groups = (
        {entry.name for entry in CORE_BUILTINS},
        {entry.name for entry in NUMERIC_BUILTINS},
        {entry.name for entry in STRING_BUILTINS},
    )
    require(groups[0].isdisjoint(groups[1]), "core/numeric collision")
    require(groups[0].isdisjoint(groups[2]), "core/string collision")
    require(groups[1].isdisjoint(groups[2]), "numeric/string collision")
    require(
        DEFAULT_STANDARD_LIBRARY.names
        == tuple(sorted(DEFAULT_STANDARD_LIBRARY.names)),
        "expanded registry order is not canonical",
    )

    sources = (
        """
        function Empty(value : string) : bool {
            return string_is_empty(value)
        }
        """,
        """
        function Starts(value : string, prefix : string) : bool {
            return string_starts_with(value, prefix)
        }
        """,
        """
        function Ends(value : string, suffix : string) : bool {
            return string_ends_with(value, suffix)
        }
        """,
        """
        function FirstIndex(value : string, fragment : string) : int {
            return string_index_of(value, fragment)
        }
        """,
        """
        function LastIndex(value : string, fragment : string) : int {
            return string_last_index_of(value, fragment)
        }
        """,
        """
        function CharAt(value : string, index : int) : string {
            return string_char_at(value, index)
        }
        """,
        """
        function Slice(value : string, start : int, end : int) : string {
            return string_slice(value, start, end)
        }
        """,
        """
        function Join(left : string, right : string) : string {
            return string_concat(left, right)
        }
        """,
        """
        function Repeat(value : string, count : int) : string {
            return string_repeat(value, count)
        }
        """,
        """
        function Replace(value : string, target : string, replacement : string) : string {
            return string_replace(value, target, replacement)
        }
        """,
    )
    linked = link_programs(*(compile_source(source) for source in sources))
    RuntimeValidator().validate(linked)
    engine = RuntimeEngine()

    require(evaluate(engine, linked, "Empty", AIRStringLiteral("")) is True, "empty")
    require(evaluate(engine, linked, "Empty", AIRStringLiteral("x")) is False, "nonempty")
    require(evaluate(engine, linked, "Starts", AIRStringLiteral("ApexForge"), AIRStringLiteral("Apex")) is True, "starts")
    require(evaluate(engine, linked, "Ends", AIRStringLiteral("ApexForge"), AIRStringLiteral("Forge")) is True, "ends")
    require(evaluate(engine, linked, "FirstIndex", AIRStringLiteral("forge-forge"), AIRStringLiteral("forge")) == 0, "first index")
    require(evaluate(engine, linked, "FirstIndex", AIRStringLiteral("ApexForge"), AIRStringLiteral("missing")) == -1, "missing index")
    require(evaluate(engine, linked, "LastIndex", AIRStringLiteral("forge-forge"), AIRStringLiteral("forge")) == 6, "last index")
    require(evaluate(engine, linked, "CharAt", AIRStringLiteral("Apex💨"), AIRIntegerLiteral(4)) == "💨", "unicode char")
    require(evaluate(engine, linked, "Slice", AIRStringLiteral("ApexForge"), AIRIntegerLiteral(4), AIRIntegerLiteral(9)) == "Forge", "slice")
    require(evaluate(engine, linked, "Join", AIRStringLiteral("Apex"), AIRStringLiteral("Forge")) == "ApexForge", "concat")
    require(evaluate(engine, linked, "Repeat", AIRStringLiteral("ha"), AIRIntegerLiteral(3)) == "hahaha", "repeat")
    require(evaluate(engine, linked, "Replace", AIRStringLiteral("red-red"), AIRStringLiteral("red"), AIRStringLiteral("blue")) == "blue-blue", "replace")

    require_compile_error(
        """
        function BadIndex(value : string) : string {
            return string_char_at(value, true)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function string_slice(value : string, start : int, end : int) : string {
            return value
        }
        """,
        "APX-COMPILE-015",
    )

    require_runtime_error(
        lambda: engine._evaluate_expression(
            AIRCallExpression(target="string_char_at", arguments=(AIRStringLiteral("abc"), AIRIntegerLiteral(3))),
            StateSnapshot(),
            functions={},
        ),
        "APX-STDLIB-006",
    )
    require_runtime_error(
        lambda: engine._evaluate_expression(
            AIRCallExpression(target="string_slice", arguments=(AIRStringLiteral("abc"), AIRIntegerLiteral(2), AIRIntegerLiteral(1))),
            StateSnapshot(),
            functions={},
        ),
        "APX-STDLIB-006",
    )
    require_runtime_error(
        lambda: engine._evaluate_expression(
            AIRCallExpression(target="string_repeat", arguments=(AIRStringLiteral("abc"), AIRIntegerLiteral(-1))),
            StateSnapshot(),
            functions={},
        ),
        "APX-STDLIB-006",
    )
    require_runtime_error(
        lambda: engine._evaluate_expression(
            AIRCallExpression(target="string_replace", arguments=(AIRStringLiteral("abc"), AIRStringLiteral(""), AIRStringLiteral("x"))),
            StateSnapshot(),
            functions={},
        ),
        "APX-STDLIB-006",
    )

    try:
        DEFAULT_STANDARD_LIBRARY.invoke(
            "string_repeat",
            ("ab", MAX_STRING_RESULT_CODE_POINTS),
        )
    except Exception as error:
        require("APX-STDLIB-007" in str(error), "wrong result-limit diagnostic")
    else:
        raise AssertionError("oversized string result unexpectedly passed")

    require(DEFAULT_STANDARD_LIBRARY.invoke("string_index_of", ("abc", "")) == 0, "empty search")
    require(DEFAULT_STANDARD_LIBRARY.invoke("string_repeat", ("abc", 0)) == "", "zero repeat")

    print("AFP-P10.3 string standard-library smoke test passed.")
    print("Core and numeric preservation: PASS")
    print("Canonical string registry ordering: PASS")
    print("Automatic string compiler signatures: PASS")
    print("Linked string validation: PASS")
    print("String inspection functions: PASS")
    print("Code-point index functions: PASS")
    print("Half-open slicing: PASS")
    print("Concatenation and repetition: PASS")
    print("Deterministic replacement: PASS")
    print("Exact index typing: PASS")
    print("Reserved string names: PASS")
    print("String domain diagnostics: PASS")
    print("String allocation ceiling: PASS")
    print("Pure runtime dispatch: PASS")


if __name__ == "__main__":
    main()
