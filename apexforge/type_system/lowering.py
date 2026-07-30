"""AFP-P9.7 deterministic lowering of closed generic AIR.

The P9.6 closure identifies every closed generic specialization reachable from
linked AIR. This module materializes those records as concrete, parameter-free
AIR functions and rewrites executable call sites to the concrete targets.

Original generic declarations remain present for source traceability and
future tooling. Runtime execution can therefore use ordinary P7 call frames
without performing type inference or carrying explicit type arguments.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import re
from typing import Iterable, Mapping, Optional

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
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRFunctionWhen,
    AIRLocalBinding,
    AIRParameter,
)
from type_system.closure import (
    GenericSpecializationManifest,
    collect_linked_specializations,
)
from type_system.generics import (
    ApexTypeVariable,
    GenericTypeLike,
    TypeIdentity,
    resolve_type,
)
from type_system.inference import (
    FunctionSignature,
    TypeInferenceError,
    infer_expression_type,
    resolve_call_specialization,
    signatures_from_air_functions,
)
from type_system.specialization import GenericSpecialization
from type_system.substitution import GenericSubstitution


class GenericLoweringError(ValueError):
    """Deterministic failure raised while lowering generic AIR."""

    def __init__(self, *, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, order=True)
class LoweredSpecializationBinding:
    """Map one canonical specialization to its concrete AIR identity."""

    canonical_id: str
    function_id: str
    function_name: str

    def __post_init__(self) -> None:
        for owner, value in (
            ("canonical_id", self.canonical_id),
            ("function_id", self.function_id),
            ("function_name", self.function_name),
        ):
            if type(value) is not str or not value:
                raise ValueError(
                    f"LoweredSpecializationBinding.{owner} must be a "
                    "non-empty string."
                )


@dataclass(frozen=True)
class GenericLoweringResult:
    """Closed generic lowering output for one linked program."""

    manifest: GenericSpecializationManifest
    bindings: tuple[LoweredSpecializationBinding, ...]
    rewritten_functions: tuple[AIRFunction, ...]
    specialized_functions: tuple[AIRFunction, ...]
    functions: tuple[AIRFunction, ...]
    program: object

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, GenericSpecializationManifest):
            raise TypeError(
                "GenericLoweringResult.manifest must be "
                "GenericSpecializationManifest."
            )
        for owner, values, expected in (
            ("bindings", self.bindings, LoweredSpecializationBinding),
            ("rewritten_functions", self.rewritten_functions, AIRFunction),
            ("specialized_functions", self.specialized_functions, AIRFunction),
            ("functions", self.functions, AIRFunction),
        ):
            if type(values) is not tuple:
                raise TypeError(
                    f"GenericLoweringResult.{owner} must be a tuple."
                )
            if not all(isinstance(value, expected) for value in values):
                raise TypeError(
                    f"GenericLoweringResult.{owner} contains an invalid value."
                )

        normalized_bindings = tuple(sorted(set(self.bindings)))
        object.__setattr__(self, "bindings", normalized_bindings)

    @property
    def canonical_ids(self) -> tuple[str, ...]:
        return tuple(binding.canonical_id for binding in self.bindings)

    def binding_for(
        self,
        canonical_id: str,
    ) -> Optional[LoweredSpecializationBinding]:
        for binding in self.bindings:
            if binding.canonical_id == canonical_id:
                return binding
        return None

    def lowered_target(self, canonical_id: str) -> Optional[str]:
        binding = self.binding_for(canonical_id)
        return None if binding is None else binding.function_name


_SAFE_COMPONENT = re.compile(r"[^A-Za-z0-9_]+")


def _safe_component(value: str) -> str:
    cleaned = _SAFE_COMPONENT.sub("_", value).strip("_")
    return cleaned or "type"


def specialization_function_name(
    specialization: GenericSpecialization,
) -> str:
    """Return the stable concrete function name for one specialization."""

    if not isinstance(specialization, GenericSpecialization):
        raise TypeError(
            "specialization_function_name requires GenericSpecialization."
        )
    if not specialization.is_closed:
        raise GenericLoweringError(
            code="APX-LOWER-001",
            message=(
                f"Open specialization {specialization.canonical_id!r} cannot "
                "be lowered into a concrete AIR function."
            ),
        )

    target = _safe_component(specialization.key.target)
    type_part = "__".join(
        _safe_component(resolve_type(value_type).name)
        for value_type in specialization.type_arguments
    )
    digest = hashlib.sha256(
        specialization.canonical_id.encode("utf-8")
    ).hexdigest()[:10]
    return f"__apx_spec__{target}__{type_part}__{digest}"


def specialization_function_id(
    specialization: GenericSpecialization,
) -> str:
    return f"function:{specialization_function_name(specialization)}"


class LinkedGenericLowerer:
    """Materialize and rewrite the P9.6 closed specialization closure."""

    def __init__(self, program: object) -> None:
        functions = tuple(getattr(program, "functions", ()) or ())
        for index, function in enumerate(functions):
            if not isinstance(function, AIRFunction):
                raise TypeError(
                    "LinkedGenericLowerer program functions must be "
                    f"AIRFunction values; item[{index}] was "
                    f"{type(function).__name__}."
                )

        self._program = program
        self._functions = tuple(
            sorted(
                functions,
                key=lambda function: (
                    int(getattr(function, "order", 0)),
                    function.id,
                    function.name,
                ),
            )
        )
        self._functions_by_name: dict[str, AIRFunction] = {}
        self._functions_by_target: dict[str, AIRFunction] = {}
        for function in self._functions:
            if function.name in self._functions_by_name:
                raise GenericLoweringError(
                    code="APX-LOWER-002",
                    message=f"Duplicate linked function name {function.name!r}.",
                )
            self._functions_by_name[function.name] = function
            for target in (function.name, function.id):
                existing = self._functions_by_target.get(target)
                if existing is not None and existing is not function:
                    raise GenericLoweringError(
                        code="APX-LOWER-002",
                        message=f"Ambiguous linked function target {target!r}.",
                    )
                self._functions_by_target[target] = function

        canonical = signatures_from_air_functions(self._functions)
        self._signatures: dict[str, FunctionSignature] = {}
        for function in self._functions:
            signature = canonical[function.name]
            self._signatures[function.name] = signature
            self._signatures[function.id] = signature

        self._manifest = collect_linked_specializations(program)
        self._bindings = self._build_bindings(self._manifest.records)
        self._binding_by_canonical = {
            binding.canonical_id: binding for binding in self._bindings
        }
        self._specialization_by_canonical = {
            specialization.canonical_id: specialization
            for specialization in self._manifest.records
        }
        self._all_signatures = dict(self._signatures)
        for specialization in self._manifest.records:
            binding = self._binding_by_canonical[
                specialization.canonical_id
            ]
            lowered_signature = FunctionSignature(
                name=binding.function_name,
                parameter_types=specialization.parameter_types,
                return_type=specialization.return_type,
            )
            self._all_signatures[binding.function_name] = lowered_signature
            self._all_signatures[binding.function_id] = lowered_signature

    def _build_bindings(
        self,
        records: Iterable[GenericSpecialization],
    ) -> tuple[LoweredSpecializationBinding, ...]:
        occupied_names = {function.name for function in self._functions}
        occupied_ids = {function.id for function in self._functions}
        bindings: list[LoweredSpecializationBinding] = []

        for specialization in tuple(records):
            function_name = specialization_function_name(specialization)
            function_id = f"function:{function_name}"
            if function_name in occupied_names or function_id in occupied_ids:
                raise GenericLoweringError(
                    code="APX-LOWER-003",
                    message=(
                        "Concrete specialization identity collides with an "
                        f"existing function: {function_id!r}."
                    ),
                )
            occupied_names.add(function_name)
            occupied_ids.add(function_id)
            bindings.append(
                LoweredSpecializationBinding(
                    canonical_id=specialization.canonical_id,
                    function_id=function_id,
                    function_name=function_name,
                )
            )

        return tuple(sorted(bindings))

    def lower(self) -> GenericLoweringResult:
        rewritten: list[AIRFunction] = []
        original_generics: list[AIRFunction] = []

        for function in self._functions:
            if tuple(getattr(function, "type_parameters", ()) or ()):
                original_generics.append(function)
                continue
            rewritten.append(
                self._lower_function(
                    function,
                    substitution=GenericSubstitution(),
                    function_id=function.id,
                    function_name=function.name,
                    order=function.order,
                )
            )

        maximum_order = max(
            (int(getattr(function, "order", 0)) for function in self._functions),
            default=-1,
        )
        specialized: list[AIRFunction] = []
        for index, specialization in enumerate(
            self._manifest.records,
            start=1,
        ):
            source = self._functions_by_name.get(
                specialization.key.target
            )
            if source is None:
                raise GenericLoweringError(
                    code="APX-LOWER-004",
                    message=(
                        "Specialization references unknown generic function "
                        f"{specialization.key.target!r}."
                    ),
                )
            binding = self._binding_by_canonical[
                specialization.canonical_id
            ]
            type_parameters = tuple(
                getattr(source, "type_parameters", ()) or ()
            )
            if len(type_parameters) != len(specialization.type_arguments):
                raise GenericLoweringError(
                    code="APX-LOWER-005",
                    message=(
                        f"Specialization {specialization.canonical_id!r} does "
                        "not match its generic declaration arity."
                    ),
                )
            substitution = GenericSubstitution(
                tuple(zip(type_parameters, specialization.type_arguments))
            )
            specialized.append(
                self._lower_function(
                    source,
                    substitution=substitution,
                    function_id=binding.function_id,
                    function_name=binding.function_name,
                    order=maximum_order + index,
                )
            )

        combined = tuple(
            sorted(
                (*original_generics, *rewritten, *specialized),
                key=lambda function: (
                    int(getattr(function, "order", 0)),
                    function.id,
                    function.name,
                ),
            )
        )
        lowered_program = self._rewrite_program(combined)

        return GenericLoweringResult(
            manifest=self._manifest,
            bindings=self._bindings,
            rewritten_functions=tuple(rewritten),
            specialized_functions=tuple(specialized),
            functions=combined,
            program=lowered_program,
        )

    def _project_type(
        self,
        value_type: GenericTypeLike,
        substitution: GenericSubstitution,
    ) -> TypeIdentity:
        resolved = resolve_type(value_type)
        if (
            isinstance(resolved, ApexTypeVariable)
            and substitution.contains(resolved)
        ):
            return substitution.resolve(resolved)
        return resolved

    def _project_optional_type(
        self,
        value_type: Optional[GenericTypeLike],
        substitution: GenericSubstitution,
    ) -> Optional[TypeIdentity]:
        if value_type is None:
            return None
        return self._project_type(value_type, substitution)

    def _lower_function(
        self,
        function: AIRFunction,
        *,
        substitution: GenericSubstitution,
        function_id: str,
        function_name: str,
        order: int,
    ) -> AIRFunction:
        identifiers: dict[str, Optional[TypeIdentity]] = {}
        parameters: list[AIRParameter] = []
        for parameter in function.parameters:
            value_type = self._project_optional_type(
                parameter.value_type,
                substitution,
            )
            parameters.append(
                AIRParameter(
                    name=parameter.name,
                    value_type=value_type,
                )
            )
            identifiers[parameter.name] = value_type

        lowered_locals: list[AIRLocalBinding] = []
        local_identifiers = dict(identifiers)
        for binding in tuple(
            getattr(function, "local_bindings", ()) or ()
        ):
            expression, value_type = self._rewrite_expression(
                binding.expression,
                identifiers=local_identifiers,
                substitution=substitution,
            )
            lowered_locals.append(
                AIRLocalBinding(binding.name, expression)
            )
            local_identifiers[binding.name] = value_type

        return_expression = getattr(function, "return_expression", None)
        lowered_return_expression = None
        if return_expression is not None:
            lowered_return_expression, _ = self._rewrite_expression(
                return_expression,
                identifiers=local_identifiers,
                substitution=substitution,
            )

        lowered_body, _ = self._rewrite_statement_block(
            tuple(getattr(function, "body", ()) or ()),
            identifiers=dict(identifiers),
            substitution=substitution,
        )

        return AIRFunction(
            id=function_id,
            name=function_name,
            parameters=tuple(parameters),
            return_expression=lowered_return_expression,
            order=order,
            local_bindings=tuple(lowered_locals),
            body=lowered_body,
            return_type=self._project_optional_type(
                function.return_type,
                substitution,
            ),
            type_parameters=(),
        )

    def _rewrite_statement_block(
        self,
        statements: tuple[object, ...],
        *,
        identifiers: dict[str, Optional[TypeIdentity]],
        substitution: GenericSubstitution,
    ) -> tuple[tuple[object, ...], dict[str, Optional[TypeIdentity]]]:
        rewritten: list[object] = []
        active_identifiers = dict(identifiers)

        for statement in statements:
            if isinstance(statement, AIRLocalBinding):
                expression, value_type = self._rewrite_expression(
                    statement.expression,
                    identifiers=active_identifiers,
                    substitution=substitution,
                )
                rewritten.append(
                    AIRLocalBinding(statement.name, expression)
                )
                active_identifiers[statement.name] = value_type
                continue

            if isinstance(statement, AIRFunctionReturn):
                expression, _ = self._rewrite_expression(
                    statement.expression,
                    identifiers=active_identifiers,
                    substitution=substitution,
                )
                rewritten.append(AIRFunctionReturn(expression))
                continue

            if isinstance(statement, AIRFunctionWhen):
                condition, _ = self._rewrite_expression(
                    statement.condition,
                    identifiers=active_identifiers,
                    substitution=substitution,
                )
                actions, _ = self._rewrite_statement_block(
                    tuple(statement.actions),
                    identifiers=dict(active_identifiers),
                    substitution=substitution,
                )
                otherwise_actions, _ = self._rewrite_statement_block(
                    tuple(statement.otherwise_actions),
                    identifiers=dict(active_identifiers),
                    substitution=substitution,
                )
                rewritten.append(
                    AIRFunctionWhen(
                        condition=condition,
                        actions=actions,
                        otherwise_actions=otherwise_actions,
                    )
                )
                continue

            raise GenericLoweringError(
                code="APX-LOWER-006",
                message=(
                    "Unsupported pure-function statement during generic "
                    f"lowering: {type(statement).__module__}."
                    f"{type(statement).__name__}."
                ),
            )

        return tuple(rewritten), active_identifiers

    def _rewrite_expression(
        self,
        expression: AIRExpression,
        *,
        identifiers: Mapping[str, Optional[GenericTypeLike]],
        substitution: GenericSubstitution,
    ) -> tuple[AIRExpression, TypeIdentity]:
        projected_identifiers = {
            name: (
                None
                if value_type is None
                else self._project_type(value_type, substitution)
            )
            for name, value_type in identifiers.items()
        }

        if isinstance(
            expression,
            (
                AIRIntegerLiteral,
                AIRFloatLiteral,
                AIRStringLiteral,
                AIRBooleanLiteral,
                AIRIdentifierReference,
            ),
        ):
            value_type = infer_expression_type(
                expression,
                identifiers=projected_identifiers,
                functions=self._all_signatures,
            )
            return expression, value_type

        if isinstance(expression, AIRUnaryExpression):
            operand, _ = self._rewrite_expression(
                expression.operand,
                identifiers=projected_identifiers,
                substitution=substitution,
            )
            rewritten = AIRUnaryExpression(
                operator=expression.operator,
                operand=operand,
            )
            return rewritten, infer_expression_type(
                rewritten,
                identifiers=projected_identifiers,
                functions=self._all_signatures,
            )

        if isinstance(expression, AIRBinaryExpression):
            left, _ = self._rewrite_expression(
                expression.left,
                identifiers=projected_identifiers,
                substitution=substitution,
            )
            right, _ = self._rewrite_expression(
                expression.right,
                identifiers=projected_identifiers,
                substitution=substitution,
            )
            rewritten = AIRBinaryExpression(
                left=left,
                operator=expression.operator,
                right=right,
            )
            return rewritten, infer_expression_type(
                rewritten,
                identifiers=projected_identifiers,
                functions=self._all_signatures,
            )

        if isinstance(expression, AIRCallExpression):
            rewritten_arguments: list[AIRExpression] = []
            argument_types: list[TypeIdentity] = []
            for argument in expression.arguments:
                rewritten_argument, argument_type = self._rewrite_expression(
                    argument,
                    identifiers=projected_identifiers,
                    substitution=substitution,
                )
                rewritten_arguments.append(rewritten_argument)
                argument_types.append(argument_type)

            signature = self._signatures.get(expression.target)
            if signature is None:
                raise TypeInferenceError(
                    code="APX-TYPE-005",
                    message=f"Unknown function {expression.target!r}.",
                )

            target = expression.target
            explicit_type_arguments = tuple(
                self._project_type(value_type, substitution)
                for value_type in tuple(
                    getattr(expression, "type_arguments", ()) or ()
                )
            )
            if signature.type_parameters:
                specialization = resolve_call_specialization(
                    signature,
                    tuple(argument_types),
                    explicit_type_arguments=explicit_type_arguments,
                    target=signature.name,
                    require_complete=True,
                    require_closed=True,
                )
                binding = self._binding_by_canonical.get(
                    specialization.canonical_id
                )
                if binding is None:
                    raise GenericLoweringError(
                        code="APX-LOWER-007",
                        message=(
                            "Generic call resolved outside the collected "
                            f"specialization manifest: "
                            f"{specialization.canonical_id!r}."
                        ),
                    )
                target = binding.function_name

            rewritten = AIRCallExpression(
                target=target,
                arguments=tuple(rewritten_arguments),
                type_arguments=(),
            )
            return rewritten, infer_expression_type(
                rewritten,
                identifiers=projected_identifiers,
                functions=self._all_signatures,
            )

        raise GenericLoweringError(
            code="APX-LOWER-008",
            message=(
                "Unsupported AIR expression during generic lowering: "
                f"{type(expression).__module__}."
                f"{type(expression).__name__}."
            ),
        )

    def _program_identifier_types(
        self,
    ) -> dict[str, Optional[TypeIdentity]]:
        identifiers: dict[str, Optional[TypeIdentity]] = {}
        for state in tuple(getattr(self._program, "states", ()) or ()):
            state_id = getattr(state, "id", None)
            value_type = getattr(state, "value_type", None)
            if not isinstance(state_id, str) or not state_id:
                continue
            normalized = (
                None if value_type is None else resolve_type(value_type)
            )
            identifiers[state_id] = normalized
            if ":" in state_id:
                identifiers.setdefault(
                    state_id.rsplit(":", 1)[-1],
                    normalized,
                )
        return identifiers

    def _rewrite_program(
        self,
        functions: tuple[AIRFunction, ...],
    ) -> object:
        if not is_dataclass(self._program):
            return self._program

        identifiers = self._program_identifier_types()
        changes: dict[str, object] = {}
        for field in fields(self._program):
            if field.name == "functions":
                changes[field.name] = functions
                continue
            changes[field.name] = self._rewrite_program_value(
                getattr(self._program, field.name),
                identifiers=identifiers,
            )
        return replace(self._program, **changes)

    def _rewrite_program_value(
        self,
        value: object,
        *,
        identifiers: Mapping[str, Optional[TypeIdentity]],
    ) -> object:
        if isinstance(value, AIRFunction):
            return value
        if isinstance(value, AIRExpression):
            rewritten, _ = self._rewrite_expression(
                value,
                identifiers=identifiers,
                substitution=GenericSubstitution(),
            )
            return rewritten
        if isinstance(value, tuple):
            return tuple(
                self._rewrite_program_value(item, identifiers=identifiers)
                for item in value
            )
        if isinstance(value, list):
            return [
                self._rewrite_program_value(item, identifiers=identifiers)
                for item in value
            ]
        if isinstance(value, dict):
            return {
                key: self._rewrite_program_value(
                    item,
                    identifiers=identifiers,
                )
                for key, item in value.items()
            }
        if is_dataclass(value):
            changes = {
                field.name: self._rewrite_program_value(
                    getattr(value, field.name),
                    identifiers=identifiers,
                )
                for field in fields(value)
            }
            return replace(value, **changes)
        return value


def lower_linked_generics(program: object) -> GenericLoweringResult:
    """Lower the complete closed generic specialization closure."""

    return LinkedGenericLowerer(program).lower()


__all__ = (
    "GenericLoweringError",
    "GenericLoweringResult",
    "LinkedGenericLowerer",
    "LoweredSpecializationBinding",
    "lower_linked_generics",
    "specialization_function_id",
    "specialization_function_name",
)