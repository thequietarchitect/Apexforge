"""AFP-P9.3 explicit generic type-argument smoke test."""
from __future__ import annotations

from air.expressions import AIRCallExpression, AIRIntegerLiteral, AIRStringLiteral
from air.linker import link_programs
from language.compiler import CompilerError, compile_source
from language.lexer import lex
from language.parser import CallExpressionNode, FunctionNode, ParseError, parse
from language.validation.runtime_validator import RuntimeValidator
from runtime.engine import RuntimeEngine
from runtime.state import StateSnapshot
from type_system.generics import ApexTypeVariable
from type_system.inference import FunctionSignature, TypeInferenceError, infer_expression_type
from type_system.model import INT, STRING


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_parse_error(source: str, code: str) -> ParseError:
    try:
        parse(source)
    except ParseError as error:
        require(error.diagnostic.code == code, f"expected {code}, received {error.diagnostic.code}: {error}")
        return error
    raise AssertionError(f"source unexpectedly parsed: {source!r}")


def require_type_error(operation, code: str) -> TypeInferenceError:
    try:
        operation()
    except TypeInferenceError as error:
        require(error.code == code, f"expected {code}, received {error.code}: {error}")
        return error
    raise AssertionError(f"operation unexpectedly passed; expected {code}")


def require_compile_error(source: str, *, signatures: dict[str, FunctionSignature], code: str) -> CompilerError:
    try:
        compile_source(source, function_signatures=signatures)
    except CompilerError as error:
        require(error.diagnostic.code == code, f"expected {code}, received {error.diagnostic.code}: {error}")
        return error
    raise AssertionError(f"source unexpectedly compiled: {source!r}")


def main() -> None:
    tokens = lex("function Use() : int { return Identity<int>(10) }")
    require(any(token.kind == "LT" for token in tokens), "explicit call '<' token disappeared")
    require(any(token.kind == "GT" for token in tokens), "explicit call '>' token disappeared")

    parsed = parse("function Use() : int { return Identity<int>(10) }")
    require(isinstance(parsed, FunctionNode), "explicit call source did not parse as FunctionNode")
    call = parsed.return_statement.expression
    require(isinstance(call, CallExpressionNode), "explicit call did not produce CallExpressionNode")
    require(len(call.type_arguments) == 1, "explicit AST type-argument count changed")
    require(call.type_arguments[0].apex_type is INT, "explicit AST type argument did not use canonical INT")

    identity_program = compile_source("function Identity<T>(value : T) : T { return value }")
    identity_signature = FunctionSignature.from_air_function(identity_program.functions[0])
    use_program = compile_source(
        "function Use() : int { return Identity<int>(10) }",
        function_signatures={"Identity": identity_signature},
    )
    air_call = use_program.functions[0].return_expression
    require(isinstance(air_call, AIRCallExpression), "explicit call did not compile to AIRCallExpression")
    require(air_call.type_arguments == (INT,), "explicit AIR type arguments changed")
    require(infer_expression_type(air_call, functions={"Identity": identity_signature}) is INT, "explicit int return substitution failed")
    require(
        infer_expression_type(
            AIRCallExpression(target="Identity", arguments=(AIRStringLiteral("ready"),), type_arguments=(STRING,)),
            functions={"Identity": identity_signature},
        ) is STRING,
        "explicit string substitution failed",
    )
    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(target="Identity", arguments=(AIRStringLiteral("wrong"),), type_arguments=(INT,)),
            functions={"Identity": identity_signature},
        ),
        "APX-TYPE-008",
    )

    first_program = compile_source("function First<T, U>(first : T, second : U) : T { return first }")
    first_signature = FunctionSignature.from_air_function(first_program.functions[0])
    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(target="First", arguments=(AIRIntegerLiteral(1), AIRStringLiteral("two")), type_arguments=(INT,)),
            functions={"First": first_signature},
        ),
        "APX-TYPE-020",
    )

    plain_signature = FunctionSignature(name="Plain", parameter_types=(), return_type=INT)
    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(target="Plain", arguments=(), type_arguments=(INT,)),
            functions={"Plain": plain_signature},
        ),
        "APX-TYPE-019",
    )

    maker_variable = ApexTypeVariable(name="T", owner="function:Make")
    maker_signature = FunctionSignature(
        name="Make", parameter_types=(), return_type=maker_variable,
        type_parameters=(maker_variable,),
    )
    require(
        infer_expression_type(
            AIRCallExpression(target="Make", arguments=(), type_arguments=(STRING,)),
            functions={"Make": maker_signature},
        ) is STRING,
        "explicit type argument did not resolve uninferable return T",
    )

    echo_program = compile_source(
        "function Echo<T>(value : T) : T { return Identity<T>(value) }",
        function_signatures={"Identity": identity_signature},
    )
    echo = echo_program.functions[0]
    require(echo.return_expression.type_arguments == (echo.type_parameters[0],), "generic-to-generic explicit type identity changed")

    linked = link_programs(identity_program, echo_program, use_program)
    RuntimeValidator().validate(linked)

    require_compile_error(
        'function Bad() : int { return Identity<int>("wrong") }',
        signatures={"Identity": identity_signature}, code="APX-TYPE-008",
    )
    require_parse_error("function Bad() : int { return Identity<>(1) }", "APX-PARSE-012")
    require_parse_error("function Bad() : int { return Identity<int,>(1) }", "APX-PARSE-013")
    require_parse_error("function Bad() : int { return Identity<decimal>(1) }", "APX-PARSE-008")

    function_index = {function.id: function for function in linked.functions}
    runtime_value = RuntimeEngine()._evaluate_expression(
        AIRCallExpression(target="Identity", arguments=(AIRIntegerLiteral(42),), type_arguments=(INT,)),
        StateSnapshot(), functions=function_index,
    )
    require(runtime_value == 42, "explicit runtime call did not preserve erased execution")

    inferred_use = compile_source(
        "function InferredUse() : int { return Identity(10) }",
        function_signatures={"Identity": identity_signature},
    )
    require(inferred_use.functions[0].return_type is INT, "P9.2 inferred calls changed after explicit arguments")

    print("AFP-P9.3 explicit generic type-argument smoke test passed.")
    print("Explicit call tokenization: PASS")
    print("Explicit call AST: PASS")
    print("Explicit AIR propagation: PASS")
    print("Built-in type substitution: PASS")
    print("Explicit value-argument checking: PASS")
    print("Type-argument arity checking: PASS")
    print("Non-generic rejection: PASS")
    print("Uninferable return resolution: PASS")
    print("Generic-to-generic explicit calls: PASS")
    print("Linked explicit validation: PASS")
    print("Malformed explicit syntax diagnostics: PASS")
    print("Runtime type erasure: PASS")
    print("P9.2 inference compatibility: PASS")


if __name__ == "__main__":
    main()