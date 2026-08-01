"""AFP-P10.1 standard-library registry and pure built-ins smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRFloatLiteral,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.validation.runtime_validator import (
    RuntimeValidator,
    UndefinedReferenceError,
)
from runtime.engine import RuntimeEngine, RuntimeExpressionError
from runtime.state import StateSnapshot
from standard_library import (
    DEFAULT_STANDARD_LIBRARY,
    P10_STANDARD_LIBRARY_VERSION,
    BuiltinFunction,
    StandardLibraryRegistry,
)
from type_system.inference import FunctionSignature
from type_system.model import BOOL, INT


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
    raise AssertionError(
        f"source unexpectedly compiled; expected {code}: {source!r}"
    )


def runtime_index(program):
    index = {}
    for function in program.functions:
        index[function.id] = function
        index[function.name] = function
    return index


def evaluate_call(engine, program, target, *arguments):
    return engine._evaluate_expression(
        AIRCallExpression(
            target=target,
            arguments=tuple(arguments),
        ),
        StateSnapshot(),
        functions=runtime_index(program),
    )


def main() -> None:
    registry = DEFAULT_STANDARD_LIBRARY
    require(
        P10_STANDARD_LIBRARY_VERSION == "10.12",
        "P10.4 standard-library API version changed",
    )
    require(
        all(
            name in registry.names
            for name in (
                "bool_not",
                "float_abs",
                "int_abs",
                "string_contains",
                "string_length",
            )
        ),
        f"P10.1 core entries disappeared: {registry.names}",
    )
    require(
        registry.get("stdlib:int_abs")
        is registry.get("int_abs"),
        "canonical standard-library lookup changed",
    )
    require(
        tuple(registry.signatures()) == registry.names,
        "signature order differs from registry order",
    )
    require(
        all(entry.purity == "pure" for entry in registry.entries),
        "P10.1 registry admitted a non-pure function",
    )

    int_program = compile_source(
        """
        function NormalizeInt(value : int) : int {
            return int_abs(value)
        }
        """
    )
    float_program = compile_source(
        """
        function NormalizeFloat(value : float) : float {
            return float_abs(value)
        }
        """
    )
    length_program = compile_source(
        """
        function TextSize(value : string) : int {
            return string_length(value)
        }
        """
    )
    contains_program = compile_source(
        """
        function HasText(value : string, fragment : string) : bool {
            return string_contains(value, fragment)
        }
        """
    )
    flip_program = compile_source(
        """
        function Flip(value : bool) : bool {
            return bool_not(value)
        }
        """
    )

    linked = link_programs(
        int_program,
        float_program,
        length_program,
        contains_program,
        flip_program,
    )
    verified = RuntimeValidator().validate(linked)
    require(verified.program is linked, "linked standard-library program failed")

    engine = RuntimeEngine()
    require(
        evaluate_call(
            engine,
            linked,
            "NormalizeInt",
            AIRIntegerLiteral(-17),
        )
        == 17,
        "int_abs runtime result changed",
    )
    float_result = engine._evaluate_expression(
        AIRCallExpression(
            target="NormalizeFloat",
            arguments=(AIRFloatLiteral(-2.5),),
        ),
        StateSnapshot(),
        functions=runtime_index(linked),
    )
    require(
        type(float_result) is float and float_result == 2.5,
        "float_abs runtime result changed",
    )
    require(
        evaluate_call(
            engine,
            linked,
            "TextSize",
            AIRStringLiteral("ApexForge"),
        )
        == 9,
        "string_length runtime result changed",
    )
    require(
        evaluate_call(
            engine,
            linked,
            "HasText",
            AIRStringLiteral("ApexForge"),
            AIRStringLiteral("Forge"),
        )
        is True,
        "string_contains runtime result changed",
    )
    require(
        evaluate_call(
            engine,
            linked,
            "Flip",
            AIRBooleanLiteral(True),
        )
        is False,
        "bool_not runtime result changed",
    )

    require_compile_error(
        """
        function BadType() : int {
            return int_abs("wrong")
        }
        """,
        "APX-TYPE-008",
    )
    require_compile_error(
        """
        function int_abs(value : int) : int {
            return value
        }
        """,
        "APX-COMPILE-015",
    )

    unknown_program = compile_source(
        """
        function UnknownUse() : int {
            return not_in_stdlib(1)
        }
        """
    )
    try:
        RuntimeValidator().validate(unknown_program)
    except UndefinedReferenceError as error:
        require(
            "not_in_stdlib" in str(error),
            "unknown-function diagnostic omitted its target",
        )
    else:
        raise AssertionError("unknown function unexpectedly validated")

    try:
        engine._evaluate_expression(
            AIRCallExpression(
                target="int_abs",
                arguments=(AIRBooleanLiteral(True),),
            ),
            StateSnapshot(),
            functions={},
        )
    except RuntimeExpressionError as error:
        require(
            "APX-STDLIB-002" in str(error),
            "runtime built-in type failure used the wrong diagnostic",
        )
    else:
        raise AssertionError("malformed built-in call unexpectedly executed")

    duplicate = BuiltinFunction(
        name="int_abs",
        signature=FunctionSignature(
            name="int_abs",
            parameter_types=(INT,),
            return_type=INT,
        ),
        implementation=lambda value: value,
    )
    try:
        StandardLibraryRegistry(
            registry.entries + (duplicate,)
        )
    except ValueError as error:
        require(
            "Duplicate standard-library function" in str(error),
            "duplicate registry diagnostic changed",
        )
    else:
        raise AssertionError("duplicate built-in unexpectedly registered")

    bad_return = BuiltinFunction(
        name="bad_return",
        signature=FunctionSignature(
            name="bad_return",
            parameter_types=(),
            return_type=BOOL,
        ),
        implementation=lambda: 1,
    )
    try:
        bad_return.invoke(())
    except Exception as error:
        require(
            "APX-STDLIB-004" in str(error),
            "built-in return contract used the wrong diagnostic",
        )
    else:
        raise AssertionError("invalid built-in return unexpectedly passed")

    print("AFP-P10.1 standard-library foundation smoke test passed.")
    print("Canonical immutable registry: PASS")
    print("Deterministic expanded-library ordering: PASS")
    print("Automatic compiler signatures: PASS")
    print("Linked validator integration: PASS")
    print("Pure runtime dispatch: PASS")
    print("Integer built-in execution: PASS")
    print("Float built-in execution: PASS")
    print("String built-in execution: PASS")
    print("Boolean built-in execution: PASS")
    print("Compile-time argument checking: PASS")
    print("Reserved-name protection: PASS")
    print("Unknown-call rejection: PASS")
    print("Runtime argument contracts: PASS")
    print("Runtime return contracts: PASS")
    print("Duplicate registration rejection: PASS")


if __name__ == "__main__":
    main()
