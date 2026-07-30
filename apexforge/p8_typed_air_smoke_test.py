"""AFP-P8.3 typed AST-to-AIR propagation smoke test."""

from __future__ import annotations

from air.expressions import AIRIntegerLiteral
from air.functions import AIRFunction, AIRParameter
from air.model import StateDefinition
from language.compiler import compile_source
from type_system.model import BOOL, INT, STRING


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    typed_directive = compile_source(
        "directive Profile { "
        "state count : int = 1 "
        "state enabled : bool = true "
        'state label : string = "ready" '
        "}"
    )

    require(
        tuple(state.value_type for state in typed_directive.states)
        == (INT, BOOL, STRING),
        "typed state identities were not propagated into AIR",
    )

    typed_function_program = compile_source(
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
        len(typed_function_program.functions) == 1,
        "typed function AIR was not produced",
    )

    typed_function = typed_function_program.functions[0]

    require(
        tuple(
            parameter.value_type
            for parameter in typed_function.parameters
        )
        == (BOOL, STRING),
        "typed parameter identities were not propagated into AIR",
    )
    require(
        typed_function.return_type is STRING,
        "typed return identity was not propagated into AIR",
    )

    legacy_directive = compile_source(
        "directive Legacy { "
        "state count = 0 "
        "}"
    )
    require(
        legacy_directive.states[0].value_type is INT,
        "legacy state did not retain canonical INT semantics",
    )

    legacy_function_program = compile_source(
        "function identity(value) { "
        "return value "
        "}"
    )
    legacy_function = legacy_function_program.functions[0]

    require(
        legacy_function.parameters[0].value_type is None,
        "legacy parameter received an invented AIR type",
    )
    require(
        legacy_function.return_type is None,
        "legacy function received an invented AIR return type",
    )

    direct_state = StateDefinition(
        id="state:direct",
        initial=AIRIntegerLiteral(value=1),
        value_type="int",
    )
    require(
        direct_state.value_type is INT,
        "string state type was not normalized canonically",
    )

    legacy_placeholder_state = StateDefinition(
        id="state:legacy-placeholder",
        initial=AIRIntegerLiteral(value=1),
        value_type="AIRExpression",
    )
    require(
        legacy_placeholder_state.value_type is INT,
        "pre-P8 state placeholder was not normalized compatibly",
    )

    direct_parameter = AIRParameter(
        name="flag",
        value_type="bool",
    )
    require(
        direct_parameter.value_type is BOOL,
        "string parameter type was not normalized canonically",
    )

    direct_function = AIRFunction(
        id="function:direct",
        name="direct",
        parameters=(direct_parameter,),
        return_expression=AIRIntegerLiteral(value=1),
        return_type="string",
    )
    require(
        direct_function.return_type is STRING,
        "string function return type was not normalized canonically",
    )

    print("AFP-P8.3 typed AIR propagation smoke test passed.")
    print("Typed state AIR propagation: PASS")
    print("Typed parameter AIR propagation: PASS")
    print("Typed return AIR propagation: PASS")
    print("Legacy state compatibility: PASS")
    print("Legacy function annotation neutrality: PASS")
    print("Direct AIR canonicalization: PASS")


if __name__ == "__main__":
    main()