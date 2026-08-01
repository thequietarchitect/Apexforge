"""AFP-P10.2 deterministic numeric standard-library smoke test."""

from __future__ import annotations

from air.expressions import (
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
    CORE_BUILTINS,
    DEFAULT_STANDARD_LIBRARY,
    NUMERIC_BUILTINS,
    P10_STANDARD_LIBRARY_VERSION,
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
        AIRCallExpression(
            target=target,
            arguments=tuple(arguments),
        ),
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


def main() -> None:
    require(
        P10_STANDARD_LIBRARY_VERSION == "10.12",
        "P10.4 public version changed",
    )
    require(
        len(CORE_BUILTINS) == 5,
        "P10.1 core built-in count changed",
    )
    require(
        len(NUMERIC_BUILTINS) == 11,
        "P10.2 numeric built-in count changed",
    )
    require(
        DEFAULT_STANDARD_LIBRARY.names
        == tuple(sorted(DEFAULT_STANDARD_LIBRARY.names)),
        "numeric registry order is not canonical",
    )
    require(
        set(entry.name for entry in CORE_BUILTINS).isdisjoint(
            entry.name for entry in NUMERIC_BUILTINS
        ),
        "numeric built-ins collide with the P10.1 core",
    )

    linked = link_programs(
        *(
            compile_source(source)
            for source in (
                """
                function BoundInt(value : int) : int {
                    return int_clamp(value, 0, 10)
                }
                """,
                """
                function SmallerInt(left : int, right : int) : int {
                    return int_min(left, right)
                }
                """,
                """
                function LargerInt(left : int, right : int) : int {
                    return int_max(left, right)
                }
                """,
                """
                function IntSign(value : int) : int {
                    return int_sign(value)
                }
                """,
                """
                function Even(value : int) : bool {
                    return int_is_even(value)
                }
                """,
                """
                function Odd(value : int) : bool {
                    return int_is_odd(value)
                }
                """,
                """
                function BoundFloat(value : float) : float {
                    return float_clamp(value, 0.0, 10.0)
                }
                """,
                """
                function SmallerFloat(left : float, right : float) : float {
                    return float_min(left, right)
                }
                """,
                """
                function LargerFloat(left : float, right : float) : float {
                    return float_max(left, right)
                }
                """,
                """
                function FloatSign(value : float) : int {
                    return float_sign(value)
                }
                """,
                """
                function Finite(value : float) : bool {
                    return float_is_finite(value)
                }
                """,
            )
        )
    )
    RuntimeValidator().validate(linked)

    engine = RuntimeEngine()
    require(
        evaluate(engine, linked, "BoundInt", AIRIntegerLiteral(-5)) == 0,
        "int_clamp lower result changed",
    )
    require(
        evaluate(engine, linked, "BoundInt", AIRIntegerLiteral(15)) == 10,
        "int_clamp upper result changed",
    )
    require(
        evaluate(engine, linked, "BoundInt", AIRIntegerLiteral(7)) == 7,
        "int_clamp interior result changed",
    )
    require(
        evaluate(
            engine,
            linked,
            "SmallerInt",
            AIRIntegerLiteral(7),
            AIRIntegerLiteral(3),
        )
        == 3,
        "int_min result changed",
    )
    require(
        evaluate(
            engine,
            linked,
            "LargerInt",
            AIRIntegerLiteral(7),
            AIRIntegerLiteral(3),
        )
        == 7,
        "int_max result changed",
    )
    require(
        evaluate(engine, linked, "IntSign", AIRIntegerLiteral(-9)) == -1,
        "negative int_sign result changed",
    )
    require(
        evaluate(engine, linked, "IntSign", AIRIntegerLiteral(0)) == 0,
        "zero int_sign result changed",
    )
    require(
        evaluate(engine, linked, "IntSign", AIRIntegerLiteral(9)) == 1,
        "positive int_sign result changed",
    )
    require(
        evaluate(engine, linked, "Even", AIRIntegerLiteral(8)) is True,
        "int_is_even result changed",
    )
    require(
        evaluate(engine, linked, "Odd", AIRIntegerLiteral(9)) is True,
        "int_is_odd result changed",
    )

    bounded_float = evaluate(
        engine,
        linked,
        "BoundFloat",
        AIRFloatLiteral(12.5),
    )
    require(
        type(bounded_float) is float and bounded_float == 10.0,
        "float_clamp result changed",
    )
    require(
        evaluate(
            engine,
            linked,
            "SmallerFloat",
            AIRFloatLiteral(1.5),
            AIRFloatLiteral(2.5),
        )
        == 1.5,
        "float_min result changed",
    )
    require(
        evaluate(
            engine,
            linked,
            "LargerFloat",
            AIRFloatLiteral(1.5),
            AIRFloatLiteral(2.5),
        )
        == 2.5,
        "float_max result changed",
    )
    require(
        evaluate(engine, linked, "FloatSign", AIRFloatLiteral(-0.25)) == -1,
        "float_sign result changed",
    )
    require(
        evaluate(engine, linked, "Finite", AIRFloatLiteral(1.0)) is True,
        "float_is_finite result changed",
    )

    require_compile_error(
        """
        function BadNumericType() : int {
            return int_min(1, 2.0)
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function int_clamp(value : int, lower : int, upper : int) : int {
            return value
        }
        """,
        "APX-COMPILE-015",
    )

    try:
        engine._evaluate_expression(
            AIRCallExpression(
                target="int_clamp",
                arguments=(
                    AIRIntegerLiteral(5),
                    AIRIntegerLiteral(10),
                    AIRIntegerLiteral(0),
                ),
            ),
            StateSnapshot(),
            functions={},
        )
    except RuntimeExpressionError as error:
        require(
            "APX-STDLIB-005" in str(error),
            "invalid int clamp bounds used the wrong diagnostic",
        )
    else:
        raise AssertionError("invalid int clamp bounds unexpectedly passed")

    nan = float("nan")
    try:
        DEFAULT_STANDARD_LIBRARY.invoke(
            "float_min",
            (nan, 1.0),
        )
    except Exception as error:
        require(
            "APX-STDLIB-005" in str(error),
            "unordered float domain used the wrong diagnostic",
        )
    else:
        raise AssertionError("NaN ordering unexpectedly passed")

    require(
        DEFAULT_STANDARD_LIBRARY.invoke(
            "float_is_finite",
            (float("inf"),),
        )
        is False,
        "float_is_finite infinity result changed",
    )

    print("AFP-P10.2 numeric standard-library smoke test passed.")
    print("Core registry preservation: PASS")
    print("Canonical numeric registry ordering: PASS")
    print("Automatic numeric compiler signatures: PASS")
    print("Linked numeric validation: PASS")
    print("Integer min/max/clamp: PASS")
    print("Integer sign/parity: PASS")
    print("Float min/max/clamp: PASS")
    print("Float sign/finite inspection: PASS")
    print("Exact int/float separation: PASS")
    print("Reserved numeric names: PASS")
    print("Deterministic numeric domain errors: PASS")
    print("Pure runtime dispatch: PASS")


if __name__ == "__main__":
    main()
