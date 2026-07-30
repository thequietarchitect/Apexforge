"""Canonical AFP-P8 expression type inference over AIR.

This module determines the language-level type produced by an AIR expression.
It does not parse source, evaluate expressions, perform implicit conversions,
or mutate AIR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, TYPE_CHECKING

from air.expressions import (
    AIRBinaryExpression,
    AIRBooleanLiteral,
    AIRCallExpression,
    AIRExpression,
    AIRFloatLiteral,
    AIRIdentifierReference,
    AIRIntegerLiteral,
    AIRStringLiteral,
    AIRUnaryExpression,
)
from type_system.model import (
    ApexType,
    BOOL,
    FLOAT,
    INT,
    STRING,
    TypeLike,
    VOID,
    resolve_builtin_type,
)


if TYPE_CHECKING:
    from air.functions import AIRFunction


class TypeInferenceError(ValueError):
    """Deterministic AFP-P8 expression type-inference failure."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
    ) -> None:
        if type(code) is not str or not code:
            raise ValueError("TypeInferenceError.code must be a non-empty string.")
        if type(message) is not str or not message:
            raise ValueError(
                "TypeInferenceError.message must be a non-empty string."
            )

        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass(frozen=True)
class FunctionSignature:
    """One immutable callable type signature."""

    name: str
    parameter_types: tuple[Optional[TypeLike], ...]
    return_type: Optional[TypeLike]

    def __post_init__(self) -> None:
        if type(self.name) is not str:
            raise TypeError(
                "FunctionSignature.name must be a string; "
                f"received {type(self.name).__name__}."
            )
        if not self.name:
            raise ValueError("FunctionSignature.name cannot be empty.")
        if type(self.parameter_types) is not tuple:
            raise TypeError(
                "FunctionSignature.parameter_types must be a tuple; "
                f"received {type(self.parameter_types).__name__}."
            )

        normalized_parameters: list[Optional[ApexType]] = []
        for parameter_type in self.parameter_types:
            normalized_parameters.append(
                None
                if parameter_type is None
                else resolve_builtin_type(parameter_type)
            )

        normalized_return = (
            None
            if self.return_type is None
            else resolve_builtin_type(self.return_type)
        )

        object.__setattr__(
            self,
            "parameter_types",
            tuple(normalized_parameters),
        )
        object.__setattr__(
            self,
            "return_type",
            normalized_return,
        )

    @classmethod
    def from_air_function(
        cls,
        function: "AIRFunction",
    ) -> "FunctionSignature":
        """Project one AIR function into its immutable type signature."""

        return cls(
            name=function.name,
            parameter_types=tuple(
                parameter.value_type
                for parameter in function.parameters
            ),
            return_type=function.return_type,
        )


def signatures_from_air_functions(
    functions: Iterable["AIRFunction"],
) -> dict[str, FunctionSignature]:
    """Build a deterministic name-to-signature map from AIR functions."""

    signatures: dict[str, FunctionSignature] = {}

    for function in tuple(functions):
        signature = FunctionSignature.from_air_function(function)

        if signature.name in signatures:
            raise ValueError(
                "Duplicate AIR function signature "
                f"{signature.name!r}."
            )

        signatures[signature.name] = signature

    return signatures


def _normalize_identifier_types(
    identifiers: Mapping[str, Optional[TypeLike]],
) -> dict[str, Optional[ApexType]]:
    normalized: dict[str, Optional[ApexType]] = {}

    for name, value_type in identifiers.items():
        if type(name) is not str or not name:
            raise ValueError(
                "Identifier type mappings require non-empty string names."
            )

        normalized[name] = (
            None
            if value_type is None
            else resolve_builtin_type(value_type)
        )

    return normalized


def _raise(
    code: str,
    message: str,
) -> None:
    raise TypeInferenceError(
        code=code,
        message=message,
    )


def _require_same_numeric_type(
    *,
    operator: str,
    left_type: ApexType,
    right_type: ApexType,
) -> ApexType:
    numeric_types = (INT, FLOAT)

    if (
        left_type in numeric_types
        and right_type is left_type
    ):
        return left_type

    _raise(
        "APX-TYPE-004",
        (
            f"Binary operator {operator!r} requires matching numeric "
            f"operands; received {left_type} and {right_type}."
        ),
    )
    raise AssertionError("unreachable")


def infer_expression_type(
    expression: AIRExpression,
    *,
    identifiers: Optional[Mapping[str, Optional[TypeLike]]] = None,
    functions: Optional[Mapping[str, FunctionSignature]] = None,
) -> ApexType:
    """Infer the canonical type produced by one AIR expression.

    AFP-P8 performs no implicit conversions. Numeric operands must therefore
    have the same canonical type.
    """

    normalized_identifiers = _normalize_identifier_types(identifiers or {})
    normalized_functions = dict(functions or {})

    for name, signature in normalized_functions.items():
        if type(name) is not str or not name:
            raise ValueError(
                "Function signature mappings require non-empty string names."
            )
        if not isinstance(signature, FunctionSignature):
            raise TypeError(
                "Function signature mappings require FunctionSignature values; "
                f"{name!r} received {type(signature).__name__}."
            )

    return _infer_expression_type(
        expression,
        identifiers=normalized_identifiers,
        functions=normalized_functions,
    )


def _infer_expression_type(
    expression: AIRExpression,
    *,
    identifiers: Mapping[str, Optional[ApexType]],
    functions: Mapping[str, FunctionSignature],
) -> ApexType:
    if isinstance(expression, AIRIntegerLiteral):
        return INT

    if isinstance(expression, AIRFloatLiteral):
        return FLOAT

    if isinstance(expression, AIRStringLiteral):
        return STRING

    if isinstance(expression, AIRBooleanLiteral):
        return BOOL

    if isinstance(expression, AIRIdentifierReference):
        if expression.name not in identifiers:
            _raise(
                "APX-TYPE-001",
                f"Unknown identifier {expression.name!r}.",
            )

        value_type = identifiers[expression.name]
        if value_type is None:
            _raise(
                "APX-TYPE-002",
                (
                    f"Identifier {expression.name!r} has no declared or "
                    "inferred type."
                ),
            )

        return value_type

    if isinstance(expression, AIRUnaryExpression):
        operand_type = _infer_expression_type(
            expression.operand,
            identifiers=identifiers,
            functions=functions,
        )

        if expression.operator in {"+", "-"}:
            if operand_type in {INT, FLOAT}:
                return operand_type

            _raise(
                "APX-TYPE-003",
                (
                    f"Unary operator {expression.operator!r} requires a "
                    f"numeric operand; received {operand_type}."
                ),
            )

        if expression.operator == "not":
            if operand_type is BOOL:
                return BOOL

            _raise(
                "APX-TYPE-003",
                (
                    "Unary operator 'not' requires bool; "
                    f"received {operand_type}."
                ),
            )

        _raise(
            "APX-TYPE-003",
            f"Unsupported unary operator {expression.operator!r}.",
        )

    if isinstance(expression, AIRBinaryExpression):
        left_type = _infer_expression_type(
            expression.left,
            identifiers=identifiers,
            functions=functions,
        )
        right_type = _infer_expression_type(
            expression.right,
            identifiers=identifiers,
            functions=functions,
        )
        operator = expression.operator

        # ApexForge has historically supported message-oriented
        # concatenation whenever either operand of ``+`` is a string.
        # Preserve that source and runtime contract while rejecting void.
        if (
            operator == "+"
            and (
                left_type is STRING
                or right_type is STRING
            )
        ):
            if (
                left_type is VOID
                or right_type is VOID
            ):
                _raise(
                    "APX-TYPE-004",
                    (
                        "Binary operator '+' cannot concatenate void; "
                        f"received {left_type} and {right_type}."
                    ),
                )

            return STRING

        if operator in {"+", "-", "*", "/", "%"}:
            return _require_same_numeric_type(
                operator=operator,
                left_type=left_type,
                right_type=right_type,
            )

        if operator in {"<", "<=", ">", ">="}:
            _require_same_numeric_type(
                operator=operator,
                left_type=left_type,
                right_type=right_type,
            )
            return BOOL

        if operator in {"and", "or"}:
            if left_type is BOOL and right_type is BOOL:
                return BOOL

            _raise(
                "APX-TYPE-004",
                (
                    f"Binary operator {operator!r} requires bool operands; "
                    f"received {left_type} and {right_type}."
                ),
            )

        if operator in {"==", "!="}:
            if (
                left_type is right_type
                and left_type is not VOID
            ):
                return BOOL

            _raise(
                "APX-TYPE-004",
                (
                    f"Binary operator {operator!r} requires matching "
                    f"non-void operands; received {left_type} and "
                    f"{right_type}."
                ),
            )

        _raise(
            "APX-TYPE-004",
            f"Unsupported binary operator {operator!r}.",
        )

    if isinstance(expression, AIRCallExpression):
        signature = functions.get(expression.target)

        if signature is None:
            _raise(
                "APX-TYPE-005",
                f"Unknown function {expression.target!r}.",
            )

        if len(expression.arguments) != len(signature.parameter_types):
            _raise(
                "APX-TYPE-006",
                (
                    f"Function {expression.target!r} expects "
                    f"{len(signature.parameter_types)} argument(s); "
                    f"received {len(expression.arguments)}."
                ),
            )

        for index, (argument, expected_type) in enumerate(
            zip(
                expression.arguments,
                signature.parameter_types,
            )
        ):
            if expected_type is None:
                _raise(
                    "APX-TYPE-007",
                    (
                        f"Function {expression.target!r} parameter "
                        f"{index} has no declared type."
                    ),
                )

            actual_type = _infer_expression_type(
                argument,
                identifiers=identifiers,
                functions=functions,
            )

            if actual_type is not expected_type:
                _raise(
                    "APX-TYPE-008",
                    (
                        f"Function {expression.target!r} argument {index} "
                        f"expects {expected_type}; received {actual_type}."
                    ),
                )

        if signature.return_type is None:
            _raise(
                "APX-TYPE-009",
                (
                    f"Function {expression.target!r} has no declared "
                    "return type."
                ),
            )

        return signature.return_type

    _raise(
        "APX-TYPE-010",
        (
            "Unsupported AIR expression "
            f"{type(expression).__module__}.{type(expression).__name__}."
        ),
    )
    raise AssertionError("unreachable")


def infer_expression_type_partial(
    expression: object,
    *,
    identifiers: Mapping[str, Optional[TypeLike]] = {},
    functions: Mapping[str, FunctionSignature] = {},
    require_complete_arguments: bool = False,
) -> Optional[ApexType]:
    """Infer an AIR expression while preserving legacy unknown types.

    ``None`` represents a type that cannot be determined because a legacy
    identifier or function signature is untyped. Known operator and call
    mismatches still raise ``TypeInferenceError``.
    """

    normalized_identifiers = _normalize_identifier_types(
        identifiers
    )
    normalized_functions = dict(functions)

    for name, signature in normalized_functions.items():
        if type(name) is not str or not name:
            raise ValueError(
                "Function signature mappings require non-empty string names."
            )
        if not isinstance(
            signature,
            FunctionSignature,
        ):
            raise TypeError(
                "Function signature mappings require FunctionSignature values; "
                f"{name!r} received {type(signature).__name__}."
            )

    return _infer_expression_type_partial(
        expression,
        identifiers=normalized_identifiers,
        functions=normalized_functions,
        require_complete_arguments=require_complete_arguments,
    )


def _infer_expression_type_partial(
    expression: object,
    *,
    identifiers: Mapping[str, Optional[ApexType]],
    functions: Mapping[str, FunctionSignature],
    require_complete_arguments: bool,
) -> Optional[ApexType]:
    if type(expression) is int:
        return INT
    if type(expression) is bool:
        return BOOL
    if type(expression) is str:
        return STRING
    if type(expression) is float:
        return FLOAT

    if isinstance(
        expression,
        AIRIntegerLiteral,
    ):
        return INT

    if isinstance(
        expression,
        AIRFloatLiteral,
    ):
        return FLOAT

    if isinstance(
        expression,
        AIRStringLiteral,
    ):
        return STRING

    if isinstance(
        expression,
        AIRBooleanLiteral,
    ):
        return BOOL

    if isinstance(
        expression,
        AIRIdentifierReference,
    ):
        if expression.name not in identifiers:
            _raise(
                "APX-TYPE-001",
                f"Unknown identifier {expression.name!r}.",
            )

        return identifiers[
            expression.name
        ]

    if isinstance(
        expression,
        AIRUnaryExpression,
    ):
        operand_type = _infer_expression_type_partial(
            expression.operand,
            identifiers=identifiers,
            functions=functions,
            require_complete_arguments=require_complete_arguments,
        )

        if operand_type is None:
            return None

        if expression.operator in {
            "+",
            "-",
        }:
            if operand_type in {
                INT,
                FLOAT,
            }:
                return operand_type

            _raise(
                "APX-TYPE-003",
                (
                    f"Unary operator {expression.operator!r} requires a "
                    f"numeric operand; received {operand_type}."
                ),
            )

        if expression.operator == "not":
            if operand_type is BOOL:
                return BOOL

            _raise(
                "APX-TYPE-003",
                (
                    "Unary operator 'not' requires bool; "
                    f"received {operand_type}."
                ),
            )

        _raise(
            "APX-TYPE-003",
            f"Unsupported unary operator {expression.operator!r}.",
        )

    if isinstance(
        expression,
        AIRBinaryExpression,
    ):
        left_type = _infer_expression_type_partial(
            expression.left,
            identifiers=identifiers,
            functions=functions,
            require_complete_arguments=require_complete_arguments,
        )
        right_type = _infer_expression_type_partial(
            expression.right,
            identifiers=identifiers,
            functions=functions,
            require_complete_arguments=require_complete_arguments,
        )
        operator = expression.operator

        if (
            left_type is None
            or right_type is None
        ):
            return None

        if (
            operator == "+"
            and (
                left_type is STRING
                or right_type is STRING
            )
        ):
            if (
                left_type is VOID
                or right_type is VOID
            ):
                _raise(
                    "APX-TYPE-004",
                    (
                        "Binary operator '+' cannot concatenate void; "
                        f"received {left_type} and {right_type}."
                    ),
                )

            return STRING

        if operator in {
            "+",
            "-",
            "*",
            "/",
            "%",
        }:
            return _require_same_numeric_type(
                operator=operator,
                left_type=left_type,
                right_type=right_type,
            )

        if operator in {
            "<",
            "<=",
            ">",
            ">=",
        }:
            _require_same_numeric_type(
                operator=operator,
                left_type=left_type,
                right_type=right_type,
            )
            return BOOL

        if operator in {
            "and",
            "or",
        }:
            if (
                left_type is BOOL
                and right_type is BOOL
            ):
                return BOOL

            _raise(
                "APX-TYPE-004",
                (
                    f"Binary operator {operator!r} requires bool operands; "
                    f"received {left_type} and {right_type}."
                ),
            )

        if operator in {
            "==",
            "!=",
        }:
            if (
                left_type is right_type
                and left_type is not VOID
            ):
                return BOOL

            _raise(
                "APX-TYPE-004",
                (
                    f"Binary operator {operator!r} requires matching "
                    f"non-void operands; received {left_type} and "
                    f"{right_type}."
                ),
            )

        _raise(
            "APX-TYPE-004",
            f"Unsupported binary operator {operator!r}.",
        )

    if isinstance(
        expression,
        AIRCallExpression,
    ):
        signature = functions.get(
            expression.target
        )

        if signature is None:
            _raise(
                "APX-TYPE-005",
                f"Unknown function {expression.target!r}.",
            )

        if len(expression.arguments) != len(
            signature.parameter_types
        ):
            _raise(
                "APX-TYPE-006",
                (
                    f"Function {expression.target!r} expects "
                    f"{len(signature.parameter_types)} argument(s); "
                    f"received {len(expression.arguments)}."
                ),
            )

        for index, (
            argument,
            expected_type,
        ) in enumerate(
            zip(
                expression.arguments,
                signature.parameter_types,
            )
        ):
            actual_type = _infer_expression_type_partial(
                argument,
                identifiers=identifiers,
                functions=functions,
                require_complete_arguments=require_complete_arguments,
            )

            if (
                expected_type is not None
                and actual_type is not None
                and actual_type is not expected_type
            ):
                _raise(
                    "APX-TYPE-008",
                    (
                        f"Function {expression.target!r} argument {index} "
                        f"expects {expected_type}; received {actual_type}."
                    ),
                )

            if (
                require_complete_arguments
                and expected_type is not None
                and actual_type is None
            ):
                _raise(
                    "APX-TYPE-014",
                    (
                        f"Function {expression.target!r} argument {index} "
                        f"must resolve to {expected_type}, but its type "
                        "is unknown."
                    ),
                )

        return signature.return_type

    _raise(
        "APX-TYPE-010",
        (
            "Unsupported AIR expression "
            f"{type(expression).__module__}.{type(expression).__name__}."
        ),
    )
    raise AssertionError("unreachable")


__all__ = (
    "FunctionSignature",
    "TypeInferenceError",
    "infer_expression_type",
    "infer_expression_type_partial",
    "signatures_from_air_functions",
)