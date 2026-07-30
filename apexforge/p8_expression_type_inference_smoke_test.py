"""AFP-P8.4A AIR expression type-inference smoke test."""

from __future__ import annotations

from air.expressions import (
    AIRBinaryExpression,
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
    AIRUnaryExpression,
)
from air.functions import AIRFunction, AIRParameter
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type,
    signatures_from_air_functions,
)
from type_system.model import BOOL, FLOAT, INT, STRING, VOID


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def require_type_error(
    operation,
    expected_code: str,
) -> TypeInferenceError:
    try:
        operation()
    except TypeInferenceError as error:
        require(
            error.code == expected_code,
            (
                f"expected type diagnostic {expected_code}, "
                f"received {error.code}: {error.message}"
            ),
        )
        return error

    raise AssertionError(
        f"expected type diagnostic {expected_code}, but none was raised"
    )


def main() -> None:
    require(
        infer_expression_type(AIRIntegerLiteral(value=7)) is INT,
        "integer literal did not infer INT",
    )
    require(
        infer_expression_type(AIRBooleanLiteral(value=True)) is BOOL,
        "Boolean literal did not infer BOOL",
    )
    require(
        infer_expression_type(AIRStringLiteral(value="ready")) is STRING,
        "string literal did not infer STRING",
    )

    identifiers = {
        "count": INT,
        "enabled": BOOL,
        "label": STRING,
        "ratio": FLOAT,
        "legacy": None,
    }

    require(
        infer_expression_type(
            AIRIdentifierReference(name="ratio"),
            identifiers=identifiers,
        )
        is FLOAT,
        "annotated float identifier did not infer FLOAT",
    )

    require(
        infer_expression_type(
            AIRUnaryExpression(
                operator="-",
                operand=AIRIdentifierReference(name="ratio"),
            ),
            identifiers=identifiers,
        )
        is FLOAT,
        "numeric unary expression did not preserve operand type",
    )

    require(
        infer_expression_type(
            AIRUnaryExpression(
                operator="not",
                operand=AIRIdentifierReference(name="enabled"),
            ),
            identifiers=identifiers,
        )
        is BOOL,
        "Boolean unary expression did not infer BOOL",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRIdentifierReference(name="count"),
                operator="+",
                right=AIRIntegerLiteral(value=1),
            ),
            identifiers=identifiers,
        )
        is INT,
        "integer arithmetic did not infer INT",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRIdentifierReference(name="ratio"),
                operator="*",
                right=AIRIdentifierReference(name="ratio"),
            ),
            identifiers=identifiers,
        )
        is FLOAT,
        "float arithmetic did not infer FLOAT",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRStringLiteral(value="Count: "),
                operator="+",
                right=AIRIntegerLiteral(value=1),
            ),
        )
        is STRING,
        "message-oriented string concatenation did not infer STRING",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRIdentifierReference(name="count"),
                operator=">=",
                right=AIRIntegerLiteral(value=0),
            ),
            identifiers=identifiers,
        )
        is BOOL,
        "numeric comparison did not infer BOOL",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRIdentifierReference(name="enabled"),
                operator="and",
                right=AIRBooleanLiteral(value=True),
            ),
            identifiers=identifiers,
        )
        is BOOL,
        "Boolean conjunction did not infer BOOL",
    )

    require(
        infer_expression_type(
            AIRBinaryExpression(
                left=AIRIdentifierReference(name="label"),
                operator="==",
                right=AIRStringLiteral(value="ready"),
            ),
            identifiers=identifiers,
        )
        is BOOL,
        "same-type equality did not infer BOOL",
    )

    choose_signature = FunctionSignature(
        name="choose",
        parameter_types=(BOOL, STRING),
        return_type=STRING,
    )
    no_result_signature = FunctionSignature(
        name="no_result",
        parameter_types=(),
        return_type=VOID,
    )
    functions = {
        "choose": choose_signature,
        "no_result": no_result_signature,
    }

    require(
        infer_expression_type(
            AIRCallExpression(
                target="choose",
                arguments=(
                    AIRBooleanLiteral(value=True),
                    AIRStringLiteral(value="selected"),
                ),
            ),
            functions=functions,
        )
        is STRING,
        "typed function call did not infer its return type",
    )

    require(
        infer_expression_type(
            AIRCallExpression(
                target="no_result",
                arguments=(),
            ),
            functions=functions,
        )
        is VOID,
        "void function call did not infer VOID",
    )

    air_function = AIRFunction(
        id="function:increment",
        name="increment",
        parameters=(
            AIRParameter(
                name="value",
                value_type=INT,
            ),
        ),
        return_expression=AIRIntegerLiteral(value=1),
        return_type=INT,
    )
    projected = signatures_from_air_functions((air_function,))
    require(
        projected["increment"].parameter_types == (INT,),
        "AIR parameter signature projection changed",
    )
    require(
        projected["increment"].return_type is INT,
        "AIR return signature projection changed",
    )

    unknown_identifier = require_type_error(
        lambda: infer_expression_type(
            AIRIdentifierReference(name="missing"),
            identifiers=identifiers,
        ),
        "APX-TYPE-001",
    )
    require(
        "missing" in unknown_identifier.message,
        "unknown identifier diagnostic omitted its name",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRIdentifierReference(name="legacy"),
            identifiers=identifiers,
        ),
        "APX-TYPE-002",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRUnaryExpression(
                operator="-",
                operand=AIRStringLiteral(value="wrong"),
            )
        ),
        "APX-TYPE-003",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRBinaryExpression(
                left=AIRIntegerLiteral(value=1),
                operator="+",
                right=AIRIdentifierReference(name="ratio"),
            ),
            identifiers=identifiers,
        ),
        "APX-TYPE-004",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(
                target="missing",
                arguments=(),
            ),
            functions=functions,
        ),
        "APX-TYPE-005",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(
                target="choose",
                arguments=(AIRBooleanLiteral(value=True),),
            ),
            functions=functions,
        ),
        "APX-TYPE-006",
    )

    legacy_parameter_signature = FunctionSignature(
        name="legacy_parameter",
        parameter_types=(None,),
        return_type=INT,
    )
    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(
                target="legacy_parameter",
                arguments=(AIRIntegerLiteral(value=1),),
            ),
            functions={
                "legacy_parameter": legacy_parameter_signature,
            },
        ),
        "APX-TYPE-007",
    )

    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(
                target="choose",
                arguments=(
                    AIRIntegerLiteral(value=1),
                    AIRStringLiteral(value="wrong"),
                ),
            ),
            functions=functions,
        ),
        "APX-TYPE-008",
    )

    legacy_return_signature = FunctionSignature(
        name="legacy_return",
        parameter_types=(),
        return_type=None,
    )
    require_type_error(
        lambda: infer_expression_type(
            AIRCallExpression(
                target="legacy_return",
                arguments=(),
            ),
            functions={
                "legacy_return": legacy_return_signature,
            },
        ),
        "APX-TYPE-009",
    )

    print("AFP-P8.4A AIR expression type-inference smoke test passed.")
    print("Literal type inference: PASS")
    print("Identifier type inference: PASS")
    print("Unary operator rules: PASS")
    print("Binary operator rules: PASS")
    print("Message-oriented concatenation: PASS")
    print("Function-call inference: PASS")
    print("AIR signature projection: PASS")
    print("Deterministic type diagnostics: PASS")
    print("No implicit numeric conversion: PASS")


if __name__ == "__main__":
    main()