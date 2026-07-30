"""AFP-P9.1 generic type-parameter and declaration smoke test."""

from __future__ import annotations

from air.expressions import AIRCallExpression, AIRIntegerLiteral
from air.functions import AIRFunction, AIRFunctionReturn, AIRParameter
from language.compiler import CompilerError, compile_source
from language.parser import FunctionNode, ParseError, parse
from language.validation.runtime_validator import (
    RuntimeValidator,
    UndefinedReferenceError,
)
from type_system.generics import ApexTypeVariable, is_type_variable
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type,
)
from type_system.model import INT


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_parse_error(source: str, code: str) -> ParseError:
    try:
        parse(source)
    except ParseError as error:
        require(
            error.diagnostic.code == code,
            f"expected {code}, received {error.diagnostic.code}",
        )
        return error
    raise AssertionError(f"source unexpectedly parsed: {source!r}")


def require_type_error(operation, code: str) -> TypeInferenceError:
    try:
        operation()
    except TypeInferenceError as error:
        require(
            error.code == code,
            f"expected {code}, received {error.code}",
        )
        return error
    raise AssertionError("generic call unexpectedly inferred")


def require_compile_error(source: str, code: str) -> CompilerError:
    try:
        compile_source(source)
    except CompilerError as error:
        require(
            error.diagnostic.code == code,
            f"expected {code}, received {error.diagnostic.code}",
        )
        return error
    raise AssertionError(f"source unexpectedly compiled: {source!r}")


def main() -> None:
    source = """
    function Identity<T>(value : T) : T {
        return value
    }
    """
    node = parse(source)
    require(isinstance(node, FunctionNode), "generic function did not parse")
    require(len(node.type_parameters) == 1, "generic parameter count changed")

    variable = node.type_parameters[0].apex_type
    require(is_type_variable(variable), "AST type parameter is not canonical")
    require(variable.name == "T", "generic parameter name changed")
    require(variable.owner == "function:Identity", "generic owner changed")
    require(
        node.parameters[0].type_annotation.apex_type is variable,
        "parameter annotation lost generic identity",
    )
    require(
        node.return_type.apex_type is variable,
        "return annotation lost generic identity",
    )

    program = compile_source(source)
    function = program.functions[0]
    require(len(function.type_parameters) == 1, "AIR generic list changed")
    air_variable = function.type_parameters[0]
    require(air_variable.name == "T", "AIR generic name changed")
    require(air_variable.owner == "function:Identity", "AIR generic owner changed")
    require(
        function.parameters[0].value_type is air_variable,
        "AIR parameter lost generic identity",
    )
    require(
        function.return_type is air_variable,
        "AIR return lost generic identity",
    )

    signature = FunctionSignature.from_air_function(function)
    require(
        signature.type_parameters == (air_variable,),
        "signature generic list changed",
    )
    require(
        signature.parameter_types == (air_variable,),
        "signature parameter changed",
    )
    require(signature.return_type is air_variable, "signature return changed")

    verified = RuntimeValidator().validate(program)
    require(verified.program is program, "generic validation replaced program")

    require(
        infer_expression_type(
            AIRCallExpression(
                target="Identity",
                arguments=(AIRIntegerLiteral(1),),
            ),
            functions={
                "Identity": signature,
            },
        )
        is INT,
        "P9.2 call inference changed the generic declaration identity",
    )

    pair = parse(
        "function First<T, U>(first : T, second : U) : T { return first }"
    )
    require(
        tuple(item.name for item in pair.type_parameters) == ("T", "U"),
        "multiple generic parameter order changed",
    )
    require(
        pair.parameters[0].type_annotation.apex_type
        is pair.type_parameters[0].apex_type,
        "first generic binding changed",
    )
    require(
        pair.parameters[1].type_annotation.apex_type
        is pair.type_parameters[1].apex_type,
        "second generic binding changed",
    )

    require_parse_error(
        "function Empty<>(value : int) : int { return value }",
        "APX-PARSE-009",
    )
    require_parse_error(
        "function Duplicate<T, T>(value : T) : T { return value }",
        "APX-PARSE-009",
    )
    require_parse_error(
        "function Shadow<int>(value : int) : int { return value }",
        "APX-PARSE-010",
    )
    require_parse_error(
        "function Trailing<T,>(value : T) : T { return value }",
        "APX-PARSE-011",
    )
    require_parse_error(
        "function Unknown(value : T) : T { return value }",
        "APX-PARSE-008",
    )

    require_compile_error(
        "function Add<T>(left : T, right : T) : T { return left + right }",
        "APX-TYPE-004",
    )

    legacy = compile_source(
        "function Increment(value : int) : int { return value + 1 }"
    ).functions[0]
    require(legacy.type_parameters == (), "P8 function gained generic metadata")
    require(legacy.parameters[0].value_type is INT, "P8 parameter type changed")
    require(legacy.return_type is INT, "P8 return type changed")

    rogue = ApexTypeVariable(name="T", owner="function:Rogue")
    malformed = AIRFunction(
        id="function:Broken",
        name="Broken",
        parameters=(AIRParameter(name="value", value_type=rogue),),
        return_expression=None,
        body=(AIRFunctionReturn(expression=program.functions[0].body[0].expression),),
        return_type=rogue,
        type_parameters=(),
    )
    malformed_program = type(program)(
        version=program.version,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        authorities=(),
        principals=(),
        roles=(),
        functions=(malformed,),
    )
    try:
        RuntimeValidator().validate(malformed_program)
    except UndefinedReferenceError:
        pass
    else:
        raise AssertionError("validator accepted undeclared AIR type variable")

    print("AFP-P9.1 generic declaration smoke test passed.")
    print("Generic function syntax: PASS")
    print("Canonical type-variable identity: PASS")
    print("Generic AST-to-AIR propagation: PASS")
    print("Function signature projection: PASS")
    print("P9.2 declaration integration: PASS")
    print("Multiple type parameters: PASS")
    print("Generic scope diagnostics: PASS")
    print("Unconstrained operator rejection: PASS")
    print("Malformed AIR generic rejection: PASS")
    print("P8 compatibility: PASS")


if __name__ == "__main__":
    main()