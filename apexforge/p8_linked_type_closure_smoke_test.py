"""AFP-P8.6 linked-program type-closure smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBinaryExpression,
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
)
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRFunctionWhen,
    AIRParameter,
)
from air.linker import link_programs
from air.model import (
    AIRProgram,
    StateAssignment,
    StateDefinition,
)
from air.types import AIR_VERSION
from causality.model import CausalDecision, CausalPath
from language.validation.runtime_validator import (
    InvalidValueError,
    RuntimeValidator,
)
from type_system.model import BOOL, INT, STRING


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_invalid(
    program: AIRProgram,
    expected_fragment: str,
) -> InvalidValueError:
    try:
        RuntimeValidator().validate(
            program
        )
    except InvalidValueError as error:
        require(
            expected_fragment in str(error),
            (
                f"linked type diagnostic omitted "
                f"{expected_fragment!r}: {error}"
            ),
        )
        return error

    raise AssertionError(
        "linked program unexpectedly passed type closure"
    )


def function_unit(
    function: AIRFunction,
) -> AIRProgram:
    return AIRProgram(
        version=AIR_VERSION,
        states=(),
        events=(),
        authority_checks=(),
        causal_decisions=(),
        directives=(),
        requirements=(),
        functions=(function,),
    )


def typed_increment() -> AIRFunction:
    expression = AIRBinaryExpression(
        left=AIRIdentifierReference(
            name="value"
        ),
        operator="+",
        right=AIRIntegerLiteral(
            value=1
        ),
    )
    return AIRFunction(
        id="function:increment",
        name="increment",
        parameters=(
            AIRParameter(
                name="value",
                value_type=INT,
            ),
        ),
        return_expression=expression,
        body=(
            AIRFunctionReturn(
                expression=expression
            ),
        ),
        return_type=INT,
    )


def main() -> None:
    increment = typed_increment()

    doubled_call = AIRCallExpression(
        target="increment",
        arguments=(
            AIRIdentifierReference(
                name="value"
            ),
        ),
    )
    valid_wrapper = AIRFunction(
        id="function:wrapper",
        name="wrapper",
        parameters=(
            AIRParameter(
                name="value",
                value_type=INT,
            ),
        ),
        return_expression=doubled_call,
        body=(
            AIRFunctionReturn(
                expression=doubled_call
            ),
        ),
        return_type=INT,
    )

    valid_linked = link_programs(
        function_unit(increment),
        function_unit(valid_wrapper),
    )
    verified = RuntimeValidator().validate(
        valid_linked
    )
    require(
        verified.program is valid_linked,
        "valid linked typed program identity changed",
    )

    wrong_argument_call = AIRCallExpression(
        target="increment",
        arguments=(
            AIRIdentifierReference(
                name="flag"
            ),
        ),
    )
    wrong_argument = AIRFunction(
        id="function:wrong_argument",
        name="wrong_argument",
        parameters=(
            AIRParameter(
                name="flag",
                value_type=BOOL,
            ),
        ),
        return_expression=wrong_argument_call,
        body=(
            AIRFunctionReturn(
                expression=wrong_argument_call
            ),
        ),
        return_type=INT,
    )
    require_invalid(
        link_programs(
            function_unit(increment),
            function_unit(wrong_argument),
        ),
        "expects int; received bool",
    )

    text_expression = AIRStringLiteral(
        value="ready"
    )
    text_value = AIRFunction(
        id="function:text_value",
        name="text_value",
        parameters=(),
        return_expression=text_expression,
        body=(
            AIRFunctionReturn(
                expression=text_expression
            ),
        ),
        return_type=STRING,
    )
    text_call = AIRCallExpression(
        target="text_value",
        arguments=(),
    )
    wrong_return = AIRFunction(
        id="function:wrong_return",
        name="wrong_return",
        parameters=(),
        return_expression=text_call,
        body=(
            AIRFunctionReturn(
                expression=text_call
            ),
        ),
        return_type=INT,
    )
    require_invalid(
        link_programs(
            function_unit(text_value),
            function_unit(wrong_return),
        ),
        "declares return type int, but returns string",
    )

    count_expression = AIRIntegerLiteral(
        value=1
    )
    count = AIRFunction(
        id="function:count",
        name="count",
        parameters=(),
        return_expression=count_expression,
        body=(
            AIRFunctionReturn(
                expression=count_expression
            ),
        ),
        return_type=INT,
    )
    condition_call = AIRCallExpression(
        target="count",
        arguments=(),
    )
    wrong_condition = AIRFunction(
        id="function:wrong_condition",
        name="wrong_condition",
        parameters=(),
        return_expression=AIRIntegerLiteral(
            value=0
        ),
        body=(
            AIRFunctionWhen(
                condition=condition_call,
                actions=(
                    AIRFunctionReturn(
                        expression=AIRIntegerLiteral(
                            value=1
                        )
                    ),
                ),
                otherwise_actions=(
                    AIRFunctionReturn(
                        expression=AIRIntegerLiteral(
                            value=0
                        )
                    ),
                ),
            ),
        ),
        return_type=INT,
    )
    require_invalid(
        link_programs(
            function_unit(count),
            function_unit(wrong_condition),
        ),
        "condition requires bool; received int",
    )

    bad_assignment = StateAssignment(
        state="state:enabled",
        operation="set_bool",
        value=AIRCallExpression(
            target="count",
            arguments=(),
        ),
    )
    directive_unit = AIRProgram(
        version=AIR_VERSION,
        states=(
            StateDefinition(
                id="state:enabled",
                initial=AIRBooleanLiteral(
                    value=False
                ),
                value_type=BOOL,
            ),
        ),
        events=(),
        authority_checks=(),
        causal_decisions=(
            CausalDecision(
                id="cause:update",
                cause="update",
                policy="max_weight",
                paths=(
                    CausalPath(
                        id="path:primary",
                        weight=10,
                        assignments=(
                            bad_assignment,
                        ),
                        emits=(),
                        invocations=(),
                        effects=(),
                        rationale="",
                        actions=(
                            bad_assignment,
                        ),
                    ),
                ),
            ),
        ),
        directives=(),
        requirements=(),
    )
    require_invalid(
        link_programs(
            function_unit(count),
            directive_unit,
        ),
        "set_bool",
    )

    legacy_expression = AIRBinaryExpression(
        left=AIRIdentifierReference(
            name="value"
        ),
        operator="+",
        right=AIRIntegerLiteral(
            value=1
        ),
    )
    legacy = AIRFunction(
        id="function:legacy",
        name="legacy",
        parameters=(
            AIRParameter(
                name="value",
                value_type=None,
            ),
        ),
        return_expression=legacy_expression,
        body=(
            AIRFunctionReturn(
                expression=legacy_expression
            ),
        ),
        return_type=None,
    )
    RuntimeValidator().validate(
        function_unit(legacy)
    )

    print("AFP-P8.6 linked-program type-closure smoke test passed.")
    print("Cross-unit typed calls: PASS")
    print("Linked argument checking: PASS")
    print("Linked return checking: PASS")
    print("Linked condition checking: PASS")
    print("Directive call-result checking: PASS")
    print("Canonical signature aliases: PASS")
    print("Legacy P7 type neutrality: PASS")


if __name__ == "__main__":
    main()