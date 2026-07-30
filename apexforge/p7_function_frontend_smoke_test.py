"""AFP-P7.1 function front-end smoke test.

This test covers lexer -> parser -> AIR compiler only. Runtime function-call
execution, linker merging, validation, and recursion checks belong to the next
P7 integration slice.
"""

from __future__ import annotations

import air.expressions as air_expressions
import language.compiler as compiler_module
from language.lexer import lex
import language.parser as parser_module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def qualified_type_name(value: object) -> str:
    """Return a useful module-qualified runtime type name for failures."""

    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


FUNCTION_SOURCE = """
function increase(value) {
    return double(value) + 1
}
"""

DIRECTIVE_SOURCE = """
directive Counter {
    state count = 3
    cause update {
        path normal @ 10 {
            set count = increase(count)
        }
    }
}
"""


def main() -> None:
    token_kinds = tuple(token.kind for token in lex(FUNCTION_SOURCE))
    require("FUNCTION" in token_kinds, "function keyword was not lexed")
    require("RETURN" in token_kinds, "return keyword was not lexed")
    require("LPAREN" in token_kinds, "left parenthesis was not lexed")
    require("RPAREN" in token_kinds, "right parenthesis was not lexed")

    node = parser_module.parse(
        FUNCTION_SOURCE,
        source_name="increase.apex",
    )
    require(
        isinstance(node, parser_module.FunctionNode),
        (
            "function returned unexpected node type: "
            f"{qualified_type_name(node)}"
        ),
    )
    require(node.name == "increase", "function name changed")
    require(
        tuple(parameter.name for parameter in node.parameters) == ("value",),
        "function parameters changed",
    )

    expression = node.return_statement.expression
    require(
        expression is not None,
        "return expression was not retained",
    )
    require(
        isinstance(
            getattr(expression, "left", None),
            parser_module.CallExpressionNode,
        ),
        (
            "nested call expression returned unexpected node type: "
            f"{qualified_type_name(getattr(expression, 'left', None))}"
        ),
    )

    compiled_function = compiler_module.compile_source(FUNCTION_SOURCE)
    require(len(compiled_function.functions) == 1, "function AIR missing")
    function = compiled_function.functions[0]
    require(function.id == "function:increase", "function ID changed")
    require(
        tuple(parameter.name for parameter in function.parameters) == ("value",),
        "AIR parameter order changed",
    )
    require(
        isinstance(
            function.return_expression,
            air_expressions.AIRBinaryExpression,
        ),
        (
            "return expression returned unexpected AIR type: "
            f"{qualified_type_name(function.return_expression)}"
        ),
    )
    require(
        isinstance(
            function.return_expression.left,
            air_expressions.AIRCallExpression,
        ),
        (
            "AIR call expression returned unexpected type: "
            f"{qualified_type_name(function.return_expression.left)}"
        ),
    )
    require(
        function.return_expression.left.target == "double",
        "AIR call target changed",
    )

    compiled_directive = compiler_module.compile_source(DIRECTIVE_SOURCE)
    assignment = compiled_directive.causal_decisions[0].paths[0].actions[0]
    require(
        isinstance(
            assignment.value,
            air_expressions.AIRCallExpression,
        ),
        (
            "directive function call returned unexpected AIR type: "
            f"{qualified_type_name(assignment.value)}"
        ),
    )
    require(
        assignment.value.target == "increase",
        "directive call target changed",
    )

    try:
        compiler_module.compile_source(
            "function bad(value, value) { return value }"
        )
    except compiler_module.CompilerError as error:
        require(
            error.diagnostic.code == "APX-COMPILE-008",
            "duplicate parameter used the wrong diagnostic",
        )
    else:
        raise AssertionError("duplicate function parameter was accepted")

    try:
        parser_module.parse("function bad(value) { value + 1 }")
    except parser_module.ParseError as error:
        require(
            error.diagnostic.code == "APX-PARSE-007",
            "missing return used the wrong diagnostic",
        )
    else:
        raise AssertionError("unsupported bare function statement was accepted")

    print("AFP-P7.1 function front-end smoke test passed.")
    print("Function keywords and commas: PASS")
    print("Function declaration parsing: PASS")
    print("Call-expression parsing: PASS")
    print("Function AIR compilation: PASS")
    print("Directive call-expression compilation: PASS")
    print("Duplicate parameter rejection: PASS")
    print("Required return rejection: PASS")


if __name__ == "__main__":
    main()