"""Canonical AFP-P8/P9.5 expression type inference over AIR.

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
from type_system.constraints import NUMERIC
from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    TypeIdentity,
    resolve_type,
    type_satisfies_constraint,
)
from type_system.model import (
    ApexType,
    BOOL,
    FLOAT,
    INT,
    STRING,
    VOID,
    resolve_builtin_type,
)
from type_system.substitution import (
    GenericSubstitution,
    GenericSubstitutionConflict,
)
from type_system.specialization import (
    GenericSpecialization,
    GenericSpecializationKey,
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
    parameter_types: tuple[Optional[GenericTypeLike], ...]
    return_type: Optional[GenericTypeLike]
    type_parameters: tuple[ApexTypeVariable, ...] = ()

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

        normalized_parameters: list[Optional[TypeIdentity]] = []
        for parameter_type in self.parameter_types:
            normalized_parameters.append(
                None
                if parameter_type is None
                else resolve_type(parameter_type)
            )

        normalized_return = (
            None
            if self.return_type is None
            else resolve_type(self.return_type)
        )

        normalized_type_parameters = tuple(self.type_parameters)
        seen_type_parameters: set[str] = set()
        for type_parameter in normalized_type_parameters:
            if not isinstance(type_parameter, ApexTypeVariable):
                raise TypeError(
                    "FunctionSignature.type_parameters must contain "
                    "ApexTypeVariable values."
                )
            if type_parameter.name in seen_type_parameters:
                raise ValueError(
                    f"Duplicate function type parameter "
                    f"{type_parameter.name!r}."
                )
            if type_parameter.owner not in {
                self.name,
                f"function:{self.name}",
            }:
                raise ValueError(
                    f"Function signature {self.name!r} contains type "
                    f"parameter {type_parameter.name!r} owned by "
                    f"{type_parameter.owner!r}."
                )
            seen_type_parameters.add(type_parameter.name)

        declared_type_parameter_ids = {
            id(type_parameter)
            for type_parameter in normalized_type_parameters
        }
        for location, value_type in (
            *(
                (f"parameter[{index}]", parameter_type)
                for index, parameter_type in enumerate(normalized_parameters)
            ),
            ("return", normalized_return),
        ):
            if (
                isinstance(value_type, ApexTypeVariable)
                and id(value_type) not in declared_type_parameter_ids
            ):
                raise ValueError(
                    f"Function signature {self.name!r} {location} references "
                    f"undeclared generic type {value_type}."
                )

        object.__setattr__(
            self,
            "type_parameters",
            normalized_type_parameters,
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
            type_parameters=tuple(
                getattr(function, "type_parameters", ()) or ()
            ),
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
    identifiers: Mapping[str, Optional[GenericTypeLike]],
) -> dict[str, Optional[TypeIdentity]]:
    normalized: dict[str, Optional[TypeIdentity]] = {}

    for name, value_type in identifiers.items():
        if type(name) is not str or not name:
            raise ValueError(
                "Identifier type mappings require non-empty string names."
            )

        normalized[name] = (
            None
            if value_type is None
            else resolve_type(value_type)
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
    left_type: TypeIdentity,
    right_type: TypeIdentity,
) -> TypeIdentity:
    if (
        right_type is left_type
        and type_satisfies_constraint(left_type, NUMERIC)
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


def _validate_generic_binding_constraints(
    variable: ApexTypeVariable,
    value_type: TypeIdentity,
    *,
    target: str,
) -> None:
    for constraint in variable.constraints:
        if type_satisfies_constraint(value_type, constraint):
            continue

        _raise(
            "APX-TYPE-021",
            (
                f"Generic function {target!r} type parameter {variable} "
                f"requires constraint {constraint}; received {value_type}."
            ),
        )


def infer_explicit_call_substitution(
    signature: FunctionSignature,
    type_arguments: Iterable[GenericTypeLike],
    *,
    target: Optional[str] = None,
) -> GenericSubstitution:
    """Bind a complete explicit type-argument list to one generic signature."""

    if not isinstance(signature, FunctionSignature):
        raise TypeError(
            "infer_explicit_call_substitution requires FunctionSignature."
        )

    arguments = tuple(resolve_type(value_type) for value_type in tuple(type_arguments))
    call_name = target or signature.name

    if not signature.type_parameters:
        _raise(
            "APX-TYPE-019",
            (
                f"Function {call_name!r} is not generic and cannot receive "
                "explicit type arguments."
            ),
        )

    if len(arguments) != len(signature.type_parameters):
        _raise(
            "APX-TYPE-020",
            (
                f"Generic function {call_name!r} expects "
                f"{len(signature.type_parameters)} type argument(s); "
                f"received {len(arguments)}."
            ),
        )

    substitution = GenericSubstitution()
    for variable, value_type in zip(signature.type_parameters, arguments):
        if value_type is VOID:
            _raise(
                "APX-TYPE-018",
                (
                    f"Generic function {call_name!r} cannot bind "
                    f"{variable} to void."
                ),
            )
        _validate_generic_binding_constraints(
            variable,
            value_type,
            target=call_name,
        )
        substitution = substitution.bind(variable, value_type)
    return substitution


def _validate_substituted_call_arguments(
    signature: FunctionSignature,
    argument_types: tuple[Optional[TypeIdentity], ...],
    substitution: GenericSubstitution,
    *,
    target: str,
    require_complete: bool,
) -> None:
    """Check value arguments after generic parameters have been substituted."""

    for index, (actual_type, declared_type) in enumerate(
        zip(argument_types, signature.parameter_types)
    ):
        if declared_type is None:
            if require_complete:
                _raise(
                    "APX-TYPE-007",
                    f"Function {target!r} parameter {index} has no declared type.",
                )
            continue

        expected_type = (
            substitution.resolve(declared_type)
            if isinstance(declared_type, ApexTypeVariable)
            else declared_type
        )
        if isinstance(expected_type, ApexTypeVariable) and not substitution.contains(declared_type):
            if require_complete:
                _raise(
                    "APX-TYPE-017",
                    (
                        f"Generic function {target!r} could not resolve "
                        f"parameter type {declared_type}."
                    ),
                )
            continue
        if actual_type is None:
            if require_complete:
                _raise(
                    "APX-TYPE-014",
                    (
                        f"Function {target!r} argument {index} must resolve "
                        f"to {expected_type}, but its type is unknown."
                    ),
                )
            continue
        if actual_type is not expected_type:
            _raise(
                "APX-TYPE-008",
                (
                    f"Function {target!r} argument {index} expects "
                    f"{expected_type}; received {actual_type}."
                ),
            )


def infer_call_substitution(
    signature: FunctionSignature,
    argument_types: Iterable[Optional[TypeIdentity]],
    *,
    target: Optional[str] = None,
    require_complete: bool = True,
) -> GenericSubstitution:
    """Infer one generic call's immutable type-variable substitution.

    Concrete parameters retain AFP-P8 exact-type checking. A repeated generic
    parameter must infer the same exact type identity from every occurrence.
    """

    if not isinstance(signature, FunctionSignature):
        raise TypeError(
            "infer_call_substitution requires FunctionSignature."
        )

    arguments = tuple(argument_types)
    call_name = target or signature.name

    if len(arguments) != len(signature.parameter_types):
        _raise(
            "APX-TYPE-006",
            (
                f"Function {call_name!r} expects "
                f"{len(signature.parameter_types)} argument(s); "
                f"received {len(arguments)}."
            ),
        )

    substitution = GenericSubstitution()
    structurally_inferable = {
        parameter_type
        for parameter_type in signature.parameter_types
        if isinstance(parameter_type, ApexTypeVariable)
    }

    for index, (
        actual_type,
        expected_type,
    ) in enumerate(
        zip(
            arguments,
            signature.parameter_types,
        )
    ):
        if expected_type is None:
            if require_complete:
                _raise(
                    "APX-TYPE-007",
                    (
                        f"Function {call_name!r} parameter {index} "
                        "has no declared type."
                    ),
                )
            continue

        if isinstance(expected_type, ApexTypeVariable):
            if actual_type is None:
                if require_complete:
                    _raise(
                        "APX-TYPE-014",
                        (
                            f"Generic function {call_name!r} argument {index} "
                            f"must resolve in order to infer "
                            f"{expected_type}; its type is unknown."
                        ),
                    )
                continue

            if actual_type is VOID:
                _raise(
                    "APX-TYPE-018",
                    (
                        f"Generic function {call_name!r} cannot bind "
                        f"{expected_type} to void."
                    ),
                )

            _validate_generic_binding_constraints(
                expected_type,
                actual_type,
                target=call_name,
            )

            try:
                substitution = substitution.bind(
                    expected_type,
                    actual_type,
                )
            except GenericSubstitutionConflict as error:
                _raise(
                    "APX-TYPE-016",
                    (
                        f"Generic function {call_name!r} infers type "
                        f"parameter {expected_type} as both "
                        f"{error.existing} and {error.incoming}; "
                        f"conflict occurs at argument {index}."
                    ),
                )
            continue

        if actual_type is None:
            if require_complete:
                _raise(
                    "APX-TYPE-014",
                    (
                        f"Function {call_name!r} argument {index} "
                        f"must resolve to {expected_type}, but its type "
                        "is unknown."
                    ),
                )
            continue

        if actual_type is not expected_type:
            _raise(
                "APX-TYPE-008",
                (
                    f"Function {call_name!r} argument {index} "
                    f"expects {expected_type}; received {actual_type}."
                ),
            )

    # Without explicit type arguments, every declared variable must occur in
    # at least one parameter position. Otherwise no call-site evidence can
    # ever determine it.
    for type_parameter in signature.type_parameters:
        if type_parameter not in structurally_inferable:
            _raise(
                "APX-TYPE-017",
                (
                    f"Generic function {call_name!r} cannot infer type "
                    f"parameter {type_parameter} from its arguments."
                ),
            )

    if require_complete:
        unresolved = substitution.unresolved(
            signature.type_parameters
        )
        if unresolved:
            names = ", ".join(
                str(variable)
                for variable in unresolved
            )
            _raise(
                "APX-TYPE-017",
                (
                    f"Generic function {call_name!r} could not infer "
                    f"type parameter(s) {names}."
                ),
            )

    return substitution


def _resolve_call_return_type(
    signature: FunctionSignature,
    substitution: GenericSubstitution,
    *,
    target: str,
    allow_unresolved: bool,
) -> Optional[TypeIdentity]:
    return_type = signature.return_type

    if return_type is None:
        if allow_unresolved:
            return None
        _raise(
            "APX-TYPE-009",
            (
                f"Function {target!r} has no declared "
                "return type."
            ),
        )

    if isinstance(return_type, ApexTypeVariable):
        if not substitution.contains(return_type):
            if allow_unresolved:
                return None
            _raise(
                "APX-TYPE-017",
                (
                    f"Generic function {target!r} could not infer "
                    f"return type parameter {return_type}."
                ),
            )

        return substitution.resolve(
            return_type
        )

    return return_type


def resolve_call_specialization(
    signature: FunctionSignature,
    argument_types: Iterable[Optional[TypeIdentity]],
    *,
    explicit_type_arguments: Iterable[GenericTypeLike] = (),
    target: Optional[str] = None,
    require_complete: bool = True,
    require_closed: bool = False,
) -> GenericSpecialization:
    """Resolve one generic call into a canonical specialization record."""

    if not isinstance(signature, FunctionSignature):
        raise TypeError(
            "resolve_call_specialization requires FunctionSignature."
        )

    call_name = target or signature.name
    actual_types = tuple(argument_types)
    explicit_arguments = tuple(explicit_type_arguments)

    if not signature.type_parameters:
        if explicit_arguments:
            _raise(
                "APX-TYPE-019",
                (
                    f"Function {call_name!r} is not generic and cannot "
                    "receive explicit type arguments."
                ),
            )
        _raise(
            "APX-TYPE-022",
            (
                f"Function {call_name!r} is not generic and has no "
                "specialization identity."
            ),
        )

    if explicit_arguments:
        substitution = infer_explicit_call_substitution(
            signature,
            explicit_arguments,
            target=call_name,
        )
    else:
        substitution = infer_call_substitution(
            signature,
            actual_types,
            target=call_name,
            require_complete=require_complete,
        )

    _validate_substituted_call_arguments(
        signature,
        actual_types,
        substitution,
        target=call_name,
        require_complete=require_complete,
    )

    resolved_type_arguments: list[TypeIdentity] = []
    for type_parameter in signature.type_parameters:
        if substitution.contains(type_parameter):
            resolved_type_arguments.append(
                substitution.resolve(type_parameter)
            )
        else:
            resolved_type_arguments.append(type_parameter)

    resolved_parameters: list[Optional[TypeIdentity]] = []
    for parameter_type in signature.parameter_types:
        if parameter_type is None:
            resolved_parameters.append(None)
        elif isinstance(parameter_type, ApexTypeVariable):
            resolved_parameters.append(
                substitution.resolve(parameter_type)
                if substitution.contains(parameter_type)
                else parameter_type
            )
        else:
            resolved_parameters.append(parameter_type)

    resolved_return = _resolve_call_return_type(
        signature,
        substitution,
        target=call_name,
        allow_unresolved=not require_complete,
    )

    specialization = GenericSpecialization(
        key=GenericSpecializationKey(
            target=call_name,
            type_arguments=tuple(resolved_type_arguments),
        ),
        parameter_types=tuple(resolved_parameters),
        return_type=resolved_return,
    )

    if require_closed and not specialization.is_closed:
        _raise(
            "APX-TYPE-023",
            (
                f"Generic specialization {specialization.canonical_id!r} "
                "is open and cannot be instantiated until every type "
                "argument resolves to a built-in ApexForge type."
            ),
        )

    return specialization


def infer_expression_type(
    expression: AIRExpression,
    *,
    identifiers: Optional[Mapping[str, Optional[GenericTypeLike]]] = None,
    functions: Optional[Mapping[str, FunctionSignature]] = None,
) -> TypeIdentity:
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
    identifiers: Mapping[str, Optional[TypeIdentity]],
    functions: Mapping[str, FunctionSignature],
) -> TypeIdentity:
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
            if type_satisfies_constraint(operand_type, NUMERIC):
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
            _raise("APX-TYPE-005", f"Unknown function {expression.target!r}.")
        if len(expression.arguments) != len(signature.parameter_types):
            _raise(
                "APX-TYPE-006",
                (
                    f"Function {expression.target!r} expects "
                    f"{len(signature.parameter_types)} argument(s); "
                    f"received {len(expression.arguments)}."
                ),
            )
        argument_types = tuple(
            _infer_expression_type(argument, identifiers=identifiers, functions=functions)
            for argument in expression.arguments
        )
        explicit_type_arguments = tuple(getattr(expression, "type_arguments", ()) or ())
        if explicit_type_arguments or signature.type_parameters:
            specialization = resolve_call_specialization(
                signature,
                argument_types,
                explicit_type_arguments=explicit_type_arguments,
                target=expression.target,
                require_complete=True,
            )
            if specialization.return_type is None:
                raise AssertionError(
                    "strict generic specialization produced no return type"
                )
            return specialization.return_type
        for index, (actual_type, expected_type) in enumerate(
            zip(argument_types, signature.parameter_types)
        ):
            if expected_type is None:
                _raise(
                    "APX-TYPE-007",
                    f"Function {expression.target!r} parameter {index} has no declared type.",
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
                f"Function {expression.target!r} has no declared return type.",
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
    identifiers: Mapping[str, Optional[GenericTypeLike]] = {},
    functions: Mapping[str, FunctionSignature] = {},
    require_complete_arguments: bool = False,
) -> Optional[TypeIdentity]:
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
    identifiers: Mapping[str, Optional[TypeIdentity]],
    functions: Mapping[str, FunctionSignature],
    require_complete_arguments: bool,
) -> Optional[TypeIdentity]:
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
            if type_satisfies_constraint(
                operand_type,
                NUMERIC,
            ):
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
        signature = functions.get(expression.target)
        if signature is None:
            _raise("APX-TYPE-005", f"Unknown function {expression.target!r}.")
        if len(expression.arguments) != len(signature.parameter_types):
            _raise(
                "APX-TYPE-006",
                (
                    f"Function {expression.target!r} expects "
                    f"{len(signature.parameter_types)} argument(s); "
                    f"received {len(expression.arguments)}."
                ),
            )
        argument_types = tuple(
            _infer_expression_type_partial(
                argument, identifiers=identifiers, functions=functions,
                require_complete_arguments=require_complete_arguments,
            )
            for argument in expression.arguments
        )
        explicit_type_arguments = tuple(getattr(expression, "type_arguments", ()) or ())
        if explicit_type_arguments or signature.type_parameters:
            specialization = resolve_call_specialization(
                signature,
                argument_types,
                explicit_type_arguments=explicit_type_arguments,
                target=expression.target,
                require_complete=require_complete_arguments,
            )
            return specialization.return_type
        for index, (actual_type, expected_type) in enumerate(
            zip(argument_types, signature.parameter_types)
        ):
            if expected_type is not None and actual_type is not None and actual_type is not expected_type:
                _raise(
                    "APX-TYPE-008",
                    (
                        f"Function {expression.target!r} argument {index} "
                        f"expects {expected_type}; received {actual_type}."
                    ),
                )
            if require_complete_arguments and expected_type is not None and actual_type is None:
                _raise(
                    "APX-TYPE-014",
                    (
                        f"Function {expression.target!r} argument {index} must "
                        f"resolve to {expected_type}, but its type is unknown."
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
    "infer_call_substitution",
    "infer_explicit_call_substitution",
    "infer_expression_type",
    "infer_expression_type_partial",
    "resolve_call_specialization",
    "signatures_from_air_functions",
)