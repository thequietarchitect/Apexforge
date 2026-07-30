"""AFP-P8.7 float literal syntax and execution smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBinaryExpression,
    AIRFloatLiteral,
    AIRIntegerLiteral,
)
from language.compiler import CompilerError, compile_source
from language.lexer import LexError, lex
import language.parser as parser_module
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from type_system.inference import (
    TypeInferenceError,
    infer_expression_type,
)
from type_system.model import FLOAT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_lex_error(source: str) -> LexError:
    try:
        lex(source)
    except LexError as error:
        require(
            error.diagnostic.code == "APX-LEX-005",
            (
                "expected APX-LEX-005, received "
                f"{error.diagnostic.code}"
            ),
        )
        return error

    raise AssertionError(
        f"malformed decimal unexpectedly lexed: {source!r}"
    )


def require_compiler_error(source: str, code: str) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        require(
            error.diagnostic.code == code,
            (
                f"expected {code}, received "
                f"{error.diagnostic.code}"
            ),
        )
        return error

    raise AssertionError(
        f"invalid float source unexpectedly compiled: {source!r}"
    )


def main() -> None:
    tokens = lex("state ratio : float = 1.5")
    require(
        tuple(token.kind for token in tokens) == (
            "STATE",
            "IDENT",
            "COLON",
            "IDENT",
            "EQUAL",
            "FLOAT",
            "EOF",
        ),
        "float source token sequence changed",
    )
    require(
        tokens[5].value == "1.5",
        "float token text changed",
    )

    integer_tokens = lex("1 20 300")
    require(
        all(
            token.kind == "NUMBER"
            for token in integer_tokens[:-1]
        ),
        "integer literals were reclassified",
    )

    for malformed in (".5", "1.", "1.2.3"):
        require_lex_error(malformed)

    parsed_state = parser_module.parse(
        "directive Ratio { state value : float = 1.5 }"
    )
    state = parsed_state.states[0]
    require(
        isinstance(state.initial, parser_module.FloatLiteralNode),
        "float state initializer did not produce FloatLiteralNode",
    )
    require(
        state.initial.value == 1.5,
        "parsed float value changed",
    )
    require(
        state.type_annotation is not None
        and state.type_annotation.apex_type is FLOAT,
        "float state annotation lost canonical identity",
    )

    function_source = (
        "function Scale(value : float) : float { "
        "return value * 2.0 "
        "}"
    )
    parsed_function = parser_module.parse(function_source)
    require(
        isinstance(
            parsed_function.return_statement.expression,
            parser_module.BinaryExpressionNode,
        ),
        "float function expression did not parse",
    )
    require(
        isinstance(
            parsed_function.return_statement.expression.right,
            parser_module.FloatLiteralNode,
        ),
        "float operand did not remain a float AST literal",
    )

    compiled_state = compile_source(
        "directive Ratio { state value : float = 1.5 }"
    )
    initial = compiled_state.states[0].initial
    require(
        isinstance(initial, AIRFloatLiteral),
        "compiler did not produce AIRFloatLiteral",
    )
    require(
        infer_expression_type(initial) is FLOAT,
        "AIR float literal did not infer FLOAT",
    )
    RuntimeValidator().validate(compiled_state)

    compiled_function = compile_source(function_source)
    function = compiled_function.functions[0]
    require(
        function.return_type is FLOAT,
        "compiled float function lost return type",
    )
    require(
        isinstance(
            function.return_expression,
            AIRBinaryExpression,
        ),
        "compiled float function lost binary expression",
    )
    RuntimeValidator().validate(compiled_function)

    require_compiler_error(
        "function Bad(value : float) : float { "
        "return value + 1 "
        "}",
        "APX-TYPE-004",
    )

    try:
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRFloatLiteral(1.0),
                operator="+",
                right=AIRIntegerLiteral(1),
            )
        )
    except TypeInferenceError as error:
        require(
            error.code == "APX-TYPE-004",
            "mixed numeric AIR diagnostic changed",
        )
    else:
        raise AssertionError(
            "float/int AIR arithmetic gained an implicit conversion"
        )

    snapshot = StateSnapshot.from_program_initials(compiled_state)
    require(
        snapshot.get_float("value") == 1.5,
        "float source initializer did not enter runtime state",
    )

    runtime_value = RuntimeEngine()._evaluate_expression(
        AIRFloatLiteral(2.5),
        StateSnapshot(),
    )
    require(
        type(runtime_value) is float and runtime_value == 2.5,
        "runtime did not evaluate AIRFloatLiteral",
    )

    print("AFP-P8.7 float literal smoke test passed.")
    print("Decimal tokenization: PASS")
    print("Malformed decimal diagnostics: PASS")
    print("Float AST construction: PASS")
    print("Float AIR construction: PASS")
    print("Float inference: PASS")
    print("Float compiler checking: PASS")
    print("No implicit numeric conversion: PASS")
    print("Float validator support: PASS")
    print("Float runtime evaluation: PASS")


if __name__ == "__main__":
    main()