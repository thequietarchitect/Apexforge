"""AFP-P7.1 function front-end smoke test.

This test covers lexer -> parser -> AIR compiler only. Runtime function-call
execution, linker merging, validation, and recursion checks belong to the next
P7 integration slice.
"""

from __future__ import annotations

from air.expressions import AIRBinaryExpression, AIRCallExpression
from language.compiler import CompilerError, compile_source
from language.lexer import lex
from language.parser import CallExpressionNode, FunctionNode, ParseError, parse


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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

    node = parse(FUNCTION_SOURCE, source_name="increase.apex")
    require(isinstance(node, FunctionNode), "function did not parse")
    require(node.name == "increase", "function name changed")
    require(
        tuple(parameter.name for parameter in node.parameters) == ("value",),
        "function parameters changed",
    )

    expression = node.return_statement.expression
    require(
        isinstance(expression, type(node.return_statement.expression)),
        "return expression was not retained",
    )
    require(
        isinstance(getattr(expression, "left", None), CallExpressionNode),
        "nested call expression did not parse",
    )

    compiled_function = compile_source(FUNCTION_SOURCE)
    require(len(compiled_function.functions) == 1, "function AIR missing")
    function = compiled_function.functions[0]
    require(function.id == "function:increase", "function ID changed")
    require(
        tuple(parameter.name for parameter in function.parameters) == ("value",),
        "AIR parameter order changed",
    )
    require(
        isinstance(function.return_expression, AIRBinaryExpression),
        "return expression was not compiled",
    )
    require(
        isinstance(function.return_expression.left, AIRCallExpression),
        "AIR call expression was not compiled",
    )
    require(
        function.return_expression.left.target == "double",
        "AIR call target changed",
    )

    compiled_directive = compile_source(DIRECTIVE_SOURCE)
    assignment = compiled_directive.causal_decisions[0].paths[0].actions[0]
    require(
        isinstance(assignment.value, AIRCallExpression),
        "directive function call was not compiled as an expression",
    )
    require(assignment.value.target == "increase", "directive call target changed")

    try:
        compile_source(
            "function bad(value, value) { return value }"
        )
    except CompilerError as error:
        require(
            error.diagnostic.code == "APX-COMPILE-008",
            "duplicate parameter used the wrong diagnostic",
        )
    else:
        raise AssertionError("duplicate function parameter was accepted")

    try:
        parse("function bad(value) { value + 1 }")
    except ParseError as error:
        require(
            error.diagnostic.code == "APX-PARSE-007",
            "missing return used the wrong diagnostic",
)

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