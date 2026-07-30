"""AFP-P8.2 typed source-syntax smoke test."""

from __future__ import annotations

from language.lexer import lex
import language.parser as parser_module
from type_system.model import BOOL, INT, STRING


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def qualified_type_name(value: object) -> str:
    """Return a useful module-qualified runtime type name for failures."""

    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


def require_parse_error(
    source: str,
    expected_code: str,
) -> parser_module.ParseError:
    try:
        parser_module.parse(source)
    except parser_module.ParseError as error:
        require(
            error.diagnostic.code == expected_code,
            (
                f"expected diagnostic {expected_code}, "
                f"received {error.diagnostic.code}"
            ),
        )
        return error

    raise AssertionError(
        f"source unexpectedly parsed successfully: {source!r}"
    )


def main() -> None:
    tokens = lex("state health : int = 100")
    require(
        any(token.kind == "COLON" for token in tokens),
        "colon was not tokenized",
    )

    typed_state_program = parser_module.parse(
        "directive Vitality { "
        "state health : int = 100 "
        "}"
    )
    require(
        isinstance(
            typed_state_program,
            parser_module.DirectiveNode,
        ),
        (
            "typed directive returned unexpected node type: "
            f"{qualified_type_name(typed_state_program)}"
        ),
    )
    require(
        len(typed_state_program.states) == 1,
        "typed state was not retained",
    )

    typed_state = typed_state_program.states[0]
    require(
        typed_state.type_annotation is not None,
        "typed state lost its annotation",
    )
    require(
        typed_state.type_annotation.apex_type is INT,
        "typed state did not use canonical INT",
    )
    require(
        typed_state.type_annotation.name == "int",
        "typed state name projection is incorrect",
    )

    typed_function = parser_module.parse(
        "function Choose("
        "flag : bool, "
        "name : string"
        ") : string { "
        "when flag { "
        "return name "
        "} otherwise { "
        'return "none" '
        "} "
        "}"
    )
    require(
        isinstance(
            typed_function,
            parser_module.FunctionNode,
        ),
        (
            "typed function returned unexpected node type: "
            f"{qualified_type_name(typed_function)}"
        ),
    )
    require(
        len(typed_function.parameters) == 2,
        "typed function parameter count changed",
    )

    first_parameter = typed_function.parameters[0]
    second_parameter = typed_function.parameters[1]

    require(
        first_parameter.type_annotation is not None,
        "first parameter lost its type annotation",
    )
    require(
        first_parameter.type_annotation.apex_type is BOOL,
        "first parameter did not use canonical BOOL",
    )
    require(
        second_parameter.type_annotation is not None,
        "second parameter lost its type annotation",
    )
    require(
        second_parameter.type_annotation.apex_type is STRING,
        "second parameter did not use canonical STRING",
    )
    require(
        typed_function.return_type is not None,
        "function return type was not retained",
    )
    require(
        typed_function.return_type.apex_type is STRING,
        "function return type did not use canonical STRING",
    )

    legacy_state_program = parser_module.parse(
        "directive Legacy { "
        "state count = 0 "
        "}"
    )
    require(
        isinstance(
            legacy_state_program,
            parser_module.DirectiveNode,
        ),
        (
            "legacy directive returned unexpected node type: "
            f"{qualified_type_name(legacy_state_program)}"
        ),
    )
    legacy_state = legacy_state_program.states[0]
    require(
        legacy_state.type_annotation is None,
        "legacy state received an invented annotation",
    )

    legacy_function = parser_module.parse(
        "function identity(value) { "
        "return value "
        "}"
    )
    require(
        isinstance(
            legacy_function,
            parser_module.FunctionNode,
        ),
        (
            "legacy function returned unexpected node type: "
            f"{qualified_type_name(legacy_function)}"
        ),
    )
    require(
        legacy_function.parameters[0].type_annotation is None,
        "legacy parameter received an invented annotation",
    )
    require(
        legacy_function.return_type is None,
        "legacy function received an invented return type",
    )

    unknown_state_error = require_parse_error(
        "directive Bad { "
        "state value : decimal = 0 "
        "}",
        "APX-PARSE-008",
    )
    require(
        "decimal" in unknown_state_error.diagnostic.message,
        "unknown state type diagnostic omitted the type name",
    )

    unknown_parameter_error = require_parse_error(
        "function Bad(value : number) : int { "
        "return value "
        "}",
        "APX-PARSE-008",
    )
    require(
        "number" in unknown_parameter_error.diagnostic.message,
        "unknown parameter type diagnostic omitted the type name",
    )

    unknown_return_error = require_parse_error(
        "function Bad(value : int) : result { "
        "return value "
        "}",
        "APX-PARSE-008",
    )
    require(
        "result" in unknown_return_error.diagnostic.message,
        "unknown return type diagnostic omitted the type name",
    )

    print("AFP-P8.2 typed source-syntax smoke test passed.")
    print("Colon tokenization: PASS")
    print("Typed state parsing: PASS")
    print("Typed parameter parsing: PASS")
    print("Typed return parsing: PASS")
    print("Canonical AST type identity: PASS")
    print("P7 source compatibility: PASS")
    print("Unknown type diagnostics: PASS")


if __name__ == "__main__":
    main()