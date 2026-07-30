"""AFP-P10.4 Boolean and explicit-conversion standard-library smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRFloatLiteral,
    AIRIntegerLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine, RuntimeExpressionError
from runtime.state import StateSnapshot
from standard_library import (
    BOOLEAN_BUILTINS,
    CONVERSION_BUILTINS,
    CORE_BUILTINS,
    DEFAULT_STANDARD_LIBRARY,
    MAX_INT_STRING_DIGITS,
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
    require(len(BOOLEAN_BUILTINS) == 4, "P10.4 Boolean count changed")
    require(len(CONVERSION_BUILTINS) == 4, "P10.4 conversion count changed")
    require(MAX_INT_STRING_DIGITS == 4_096, "int string ceiling changed")

    groups = tuple(
        {entry.name for entry in entries}
        for entries in (
            CORE_BUILTINS,
            NUMERIC_BUILTINS,
            STRING_BUILTINS,
            BOOLEAN_BUILTINS,
            CONVERSION_BUILTINS,
        )
    )
    for left_index, left in enumerate(groups):
        for right in groups[left_index + 1:]:
            require(left.isdisjoint(right), "standard-library group collision")
    require(
        DEFAULT_STANDARD_LIBRARY.names
        == tuple(sorted(DEFAULT_STANDARD_LIBRARY.names)),
        "P10.4 registry order is not canonical",
    )

    linked = link_programs(
        *(
            compile_source(source)
            for source in (
                """
                function And(left : bool, right : bool) : bool {
                    return bool_and(left, right)
                }
                """,
                """
                function Or(left : bool, right : bool) : bool {
                    return bool_or(left, right)
                }
                """,
                """
                function Xor(left : bool, right : bool) : bool {
                    return bool_xor(left, right)
                }
                """,
                """
                function Implies(left : bool, right : bool) : bool {
                    return bool_implies(left, right)
                }
                """,
                """
                function ToFloat(value : int) : float {
                    return int_to_float(value)
                }
                """,
                """
                function IntText(value : int) : string {
                    return int_to_string(value)
                }
                """,
                """
                function FloatText(value : float) : string {
                    return float_to_string(value)
                }
                """,
                """
                function BoolText(value : bool) : string {
                    return bool_to_string(value)
                }
                """,
            )
        )
    )
    RuntimeValidator().validate(linked)
    engine = RuntimeEngine()

    truth = (False, True)
    for left in truth:
        for right in truth:
            left_air = AIRBooleanLiteral(left)
            right_air = AIRBooleanLiteral(right)
            require(
                evaluate(engine, linked, "And", left_air, right_air)
                is (left and right),
                "bool_and truth table changed",
            )
            require(
                evaluate(engine, linked, "Or", left_air, right_air)
                is (left or right),
                "bool_or truth table changed",
            )
            require(
                evaluate(engine, linked, "Xor", left_air, right_air)
                is (left != right),
                "bool_xor truth table changed",
            )
            require(
                evaluate(engine, linked, "Implies", left_air, right_air)
                is ((not left) or right),
                "bool_implies truth table changed",
            )

    float_value = evaluate(engine, linked, "ToFloat", AIRIntegerLiteral(5))
    require(type(float_value) is float and float_value == 5.0, "int_to_float")
    require(
        evaluate(engine, linked, "IntText", AIRIntegerLiteral(-42)) == "-42",
        "int_to_string",
    )
    require(
        evaluate(engine, linked, "FloatText", AIRFloatLiteral(1.5)) == "1.5",
        "float_to_string finite",
    )
    require(
        evaluate(engine, linked, "FloatText", AIRFloatLiteral(-0.0)) == "-0.0",
        "float_to_string negative zero",
    )
    require(
        evaluate(engine, linked, "BoolText", AIRBooleanLiteral(True)) == "true",
        "bool_to_string true",
    )
    require(
        evaluate(engine, linked, "BoolText", AIRBooleanLiteral(False)) == "false",
        "bool_to_string false",
    )

    require(
        DEFAULT_STANDARD_LIBRARY.invoke("float_to_string", (float("nan"),))
        == "nan",
        "NaN spelling changed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke("float_to_string", (float("inf"),))
        == "inf",
        "positive infinity spelling changed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.invoke("float_to_string", (float("-inf"),))
        == "-inf",
        "negative infinity spelling changed",
    )

    # Explicit conversion may round, but no implicit int-to-float path exists.
    rounded = DEFAULT_STANDARD_LIBRARY.invoke(
        "int_to_float",
        (9_007_199_254_740_993,),
    )
    require(
        type(rounded) is float and rounded == 9_007_199_254_740_992.0,
        "explicit binary64 rounding contract changed",
    )
    require_compile_error(
        """
        function Bad(value : int) : float {
            return value
        }
        """,
        "APX-TYPE-011",
    )
    require_compile_error(
        """
        function BadBool(value : int) : bool {
            return bool_and(value, true)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function int_to_float(value : int) : float {
            return 0.0
        }
        """,
        "APX-COMPILE-015",
    )

    require_runtime_error(
        lambda: engine._evaluate_expression(
            AIRCallExpression(
                target="bool_and",
                arguments=(AIRIntegerLiteral(1), AIRBooleanLiteral(True)),
            ),
            StateSnapshot(),
            functions={},
        ),
        "APX-STDLIB-002",
    )

    try:
        DEFAULT_STANDARD_LIBRARY.invoke(
            "int_to_float",
            (10 ** 10_000,),
        )
    except Exception as error:
        require("APX-STDLIB-008" in str(error), "wrong overflow diagnostic")
    else:
        raise AssertionError("overflowing int_to_float unexpectedly passed")

    try:
        DEFAULT_STANDARD_LIBRARY.invoke(
            "int_to_string",
            (10 ** MAX_INT_STRING_DIGITS,),
        )
    except Exception as error:
        require("APX-STDLIB-008" in str(error), "wrong digit-limit diagnostic")
    else:
        raise AssertionError("oversized int_to_string unexpectedly passed")

    print("AFP-P10.4 Boolean and conversion standard-library smoke test passed.")
    print("Prior library preservation: PASS")
    print("Canonical Boolean and conversion ordering: PASS")
    print("Automatic compiler signatures: PASS")
    print("Linked validation: PASS")
    print("Boolean truth tables: PASS")
    print("Explicit int-to-float conversion: PASS")
    print("Canonical int text conversion: PASS")
    print("Canonical float text conversion: PASS")
    print("Canonical bool text conversion: PASS")
    print("Special float spellings: PASS")
    print("Explicit rounding contract: PASS")
    print("No implicit numeric conversion: PASS")
    print("Exact Boolean argument typing: PASS")
    print("Reserved conversion names: PASS")
    print("Deterministic conversion-domain errors: PASS")
    print("Pure runtime dispatch: PASS")


if __name__ == "__main__":
    main()
