"""AFP-P9.6 linked generic-specialization closure.

This module discovers every *closed* generic specialization referenced by a
linked AIR program. It expands specialized generic function bodies
transitively, deduplicates repeated call sites, records deterministic caller to
callee dependencies, and leaves runtime execution type-erased.

The closure is conservative: every concrete non-generic function and every
program-level AIR expression is treated as a root, whether or not a particular
runtime path is eventually taken.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Iterable, Mapping, Optional

from air.expressions import (
    AIRBinaryExpression,
    AIRCallExpression,
    AIRExpression,
    AIRUnaryExpression,
)
from air.functions import (
    AIRFunction,
    AIRFunctionReturn,
    AIRFunctionWhen,
    AIRLocalBinding,
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
from type_system.specialization import (
    GenericInstantiationTable,
    GenericSpecialization,
)
from type_system.substitution import GenericSubstitution


@dataclass(frozen=True, order=True)
class GenericSpecializationDependency:
    """One deterministic call-graph edge in the specialization closure."""

    caller: str
    callee: str

    def __post_init__(self) -> None:
        if type(self.caller) is not str or not self.caller:
            raise ValueError(
                "GenericSpecializationDependency.caller must be a "
                "non-empty string."
            )
        if type(self.callee) is not str or not self.callee:
            raise ValueError(
                "GenericSpecializationDependency.callee must be a "
                "non-empty string."
            )


@dataclass(frozen=True)
class GenericSpecializationManifest:
    """Canonical closed-specialization table plus dependency edges."""

    table: GenericInstantiationTable = GenericInstantiationTable()
    dependencies: tuple[GenericSpecializationDependency, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.table, GenericInstantiationTable):
            raise TypeError(
                "GenericSpecializationManifest.table must be "
                "GenericInstantiationTable."
            )
        if type(self.dependencies) is not tuple:
            raise TypeError(
                "GenericSpecializationManifest.dependencies must be a tuple."
            )

        normalized: set[GenericSpecializationDependency] = set()
        for dependency in self.dependencies:
            if not isinstance(
                dependency,
                GenericSpecializationDependency,
            ):
                raise TypeError(
                    "GenericSpecializationManifest dependencies must be "
                    "GenericSpecializationDependency values."
                )
            normalized.add(dependency)

        object.__setattr__(
            self,
            "dependencies",
            tuple(sorted(normalized)),
        )

    @property
    def records(self) -> tuple[GenericSpecialization, ...]:
        return self.table.records

    @property
    def canonical_ids(self) -> tuple[str, ...]:
        return tuple(
            record.canonical_id
            for record in self.table.records
        )

    def dependencies_from(
        self,
        caller: str,
    ) -> tuple[GenericSpecializationDependency, ...]:
        return tuple(
            dependency
            for dependency in self.dependencies
            if dependency.caller == caller
        )

    def __len__(self) -> int:
        return len(self.table)


class LinkedSpecializationCollector:
    """Discover the transitive closed generic closure of linked AIR."""

    def __init__(
        self,
        functions: Iterable[AIRFunction],
    ) -> None:
        ordered = tuple(functions)
        for index, function in enumerate(ordered):
            if not isinstance(function, AIRFunction):
                raise TypeError(
                    "LinkedSpecializationCollector functions must be "
                    f"AIRFunction values; item[{index}] was "
                    f"{type(function).__name__}."
                )

        self._functions = tuple(
            sorted(
                ordered,
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
                raise ValueError(
                    f"Duplicate linked function name {function.name!r}."
                )
            self._functions_by_name[function.name] = function

            for target in (function.name, function.id):
                existing = self._functions_by_target.get(target)
                if existing is not None and existing is not function:
                    raise ValueError(
                        f"Ambiguous linked function target {target!r}."
                    )
                self._functions_by_target[target] = function

        canonical_signatures = signatures_from_air_functions(
            self._functions
        )
        self._signatures: dict[str, FunctionSignature] = {}
        for function in self._functions:
            signature = canonical_signatures[function.name]
            self._signatures[function.name] = signature
            self._signatures[function.id] = signature

        self._table = GenericInstantiationTable()
        self._dependencies: set[
            GenericSpecializationDependency
        ] = set()
        self._visited_contexts: set[str] = set()

    def collect(
        self,
        *,
        program: Optional[object] = None,
    ) -> GenericSpecializationManifest:
        """Collect all specializations from concrete functions and program AIR."""

        # Every non-generic function is a conservative concrete root.
        for function in self._functions:
            signature = self._signatures[function.name]
            if signature.type_parameters:
                continue
            self._scan_function(
                function,
                substitution=GenericSubstitution(),
                context=function.id,
            )

        if program is not None:
            state_identifiers = self._program_identifier_types(program)
            for index, expression in enumerate(
                self._iter_program_expression_roots(program)
            ):
                self._scan_expression(
                    expression,
                    identifiers=state_identifiers,
                    substitution=GenericSubstitution(),
                    caller=f"program:expression:{index}",
                )

        return GenericSpecializationManifest(
            table=self._table,
            dependencies=tuple(self._dependencies),
        )

    def _program_identifier_types(
        self,
        program: object,
    ) -> dict[str, Optional[TypeIdentity]]:
        identifiers: dict[str, Optional[TypeIdentity]] = {}

        for state in tuple(getattr(program, "states", ()) or ()):
            state_id = getattr(state, "id", None)
            value_type = getattr(state, "value_type", None)
            if not isinstance(state_id, str) or not state_id:
                continue

            normalized = (
                None
                if value_type is None
                else resolve_type(value_type)
            )
            identifiers[state_id] = normalized

            # Compiled identifiers generally use the source-facing suffix.
            if ":" in state_id:
                identifiers.setdefault(
                    state_id.rsplit(":", 1)[-1],
                    normalized,
                )

        return identifiers

    def _iter_program_expression_roots(
        self,
        program: object,
    ) -> Iterable[AIRExpression]:
        """Yield top-level expression roots while excluding function bodies."""

        seen: set[int] = set()

        def walk(value: object) -> Iterable[AIRExpression]:
            if value is None:
                return

            if isinstance(value, AIRFunction):
                return

            if isinstance(value, AIRExpression):
                yield value
                return

            value_id = id(value)
            if value_id in seen:
                return

            if isinstance(value, (tuple, list)):
                seen.add(value_id)
                for item in value:
                    yield from walk(item)
                return

            if isinstance(value, dict):
                seen.add(value_id)
                for key in sorted(value, key=repr):
                    yield from walk(value[key])
                return

            if is_dataclass(value):
                seen.add(value_id)
                for field in fields(value):
                    if field.name == "functions":
                        continue
                    yield from walk(getattr(value, field.name))

        yield from walk(program)

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

    def _project_expression(
        self,
        expression: AIRExpression,
        substitution: GenericSubstitution,
    ) -> AIRExpression:
        if isinstance(expression, AIRUnaryExpression):
            return AIRUnaryExpression(
                operator=expression.operator,
                operand=self._project_expression(
                    expression.operand,
                    substitution,
                ),
            )

        if isinstance(expression, AIRBinaryExpression):
            return AIRBinaryExpression(
                left=self._project_expression(
                    expression.left,
                    substitution,
                ),
                operator=expression.operator,
                right=self._project_expression(
                    expression.right,
                    substitution,
                ),
            )

        if isinstance(expression, AIRCallExpression):
            return AIRCallExpression(
                target=expression.target,
                arguments=tuple(
                    self._project_expression(argument, substitution)
                    for argument in expression.arguments
                ),
                type_arguments=tuple(
                    self._project_type(value_type, substitution)
                    for value_type in tuple(
                        getattr(expression, "type_arguments", ()) or ()
                    )
                ),
            )

        return expression

    def _project_identifier_types(
        self,
        identifiers: Mapping[str, Optional[GenericTypeLike]],
        substitution: GenericSubstitution,
    ) -> dict[str, Optional[TypeIdentity]]:
        return {
            name: (
                None
                if value_type is None
                else self._project_type(value_type, substitution)
            )
            for name, value_type in identifiers.items()
        }

    def _scan_expression(
        self,
        expression: AIRExpression,
        *,
        identifiers: Mapping[str, Optional[GenericTypeLike]],
        substitution: GenericSubstitution,
        caller: str,
    ) -> TypeIdentity:
        projected_identifiers = self._project_identifier_types(
            identifiers,
            substitution,
        )
        projected = self._project_expression(
            expression,
            substitution,
        )

        if isinstance(projected, AIRUnaryExpression):
            self._scan_expression(
                projected.operand,
                identifiers=projected_identifiers,
                substitution=GenericSubstitution(),
                caller=caller,
            )

        elif isinstance(projected, AIRBinaryExpression):
            self._scan_expression(
                projected.left,
                identifiers=projected_identifiers,
                substitution=GenericSubstitution(),
                caller=caller,
            )
            self._scan_expression(
                projected.right,
                identifiers=projected_identifiers,
                substitution=GenericSubstitution(),
                caller=caller,
            )

        elif isinstance(projected, AIRCallExpression):
            argument_types = tuple(
                self._scan_expression(
                    argument,
                    identifiers=projected_identifiers,
                    substitution=GenericSubstitution(),
                    caller=caller,
                )
                for argument in projected.arguments
            )
            signature = self._signatures.get(projected.target)
            if signature is None:
                raise TypeInferenceError(
                    code="APX-TYPE-005",
                    message=f"Unknown function {projected.target!r}.",
                )

            if signature.type_parameters:
                specialization = resolve_call_specialization(
                    signature,
                    argument_types,
                    explicit_type_arguments=tuple(
                        getattr(projected, "type_arguments", ()) or ()
                    ),
                    target=signature.name,
                    require_complete=True,
                    require_closed=True,
                )
                self._register_specialization(
                    specialization,
                    caller=caller,
                )

        # Reuse the canonical P8/P9 type checker after all call-site metadata
        # has been projected into the current specialization context.
        return infer_expression_type(
            projected,
            identifiers=projected_identifiers,
            functions=self._signatures,
        )

    def _register_specialization(
        self,
        specialization: GenericSpecialization,
        *,
        caller: str,
    ) -> None:
        self._table = self._table.register(specialization)
        self._dependencies.add(
            GenericSpecializationDependency(
                caller=caller,
                callee=specialization.canonical_id,
            )
        )

        target_function = self._functions_by_name.get(
            specialization.key.target
        )
        if target_function is None:
            raise TypeInferenceError(
                code="APX-TYPE-005",
                message=(
                    "Specialization references unknown linked function "
                    f"{specialization.key.target!r}."
                ),
            )

        substitution = GenericSubstitution(
            tuple(
                zip(
                    tuple(
                        getattr(
                            target_function,
                            "type_parameters",
                            (),
                        )
                        or ()
                    ),
                    specialization.type_arguments,
                )
            )
        )
        self._scan_function(
            target_function,
            substitution=substitution,
            context=specialization.canonical_id,
        )

    def _scan_function(
        self,
        function: AIRFunction,
        *,
        substitution: GenericSubstitution,
        context: str,
    ) -> None:
        if context in self._visited_contexts:
            return
        self._visited_contexts.add(context)

        identifiers: dict[str, Optional[TypeIdentity]] = {}
        for parameter in function.parameters:
            identifiers[parameter.name] = (
                None
                if parameter.value_type is None
                else self._project_type(
                    parameter.value_type,
                    substitution,
                )
            )

        body = tuple(getattr(function, "body", ()) or ())
        if body:
            self._scan_statement_block(
                body,
                identifiers=identifiers,
                substitution=substitution,
                caller=context,
            )
            return

        # Legacy P7 projection: locals followed by one return expression.
        for binding in tuple(
            getattr(function, "local_bindings", ()) or ()
        ):
            value_type = self._scan_expression(
                binding.expression,
                identifiers=identifiers,
                substitution=substitution,
                caller=context,
            )
            identifiers[binding.name] = value_type

        return_expression = getattr(
            function,
            "return_expression",
            None,
        )
        if return_expression is not None:
            self._scan_expression(
                return_expression,
                identifiers=identifiers,
                substitution=substitution,
                caller=context,
            )

    def _scan_statement_block(
        self,
        statements: tuple[object, ...],
        *,
        identifiers: dict[str, Optional[TypeIdentity]],
        substitution: GenericSubstitution,
        caller: str,
    ) -> None:
        for statement in statements:
            if isinstance(statement, AIRLocalBinding):
                value_type = self._scan_expression(
                    statement.expression,
                    identifiers=identifiers,
                    substitution=substitution,
                    caller=caller,
                )
                identifiers[statement.name] = value_type
                continue

            if isinstance(statement, AIRFunctionReturn):
                self._scan_expression(
                    statement.expression,
                    identifiers=identifiers,
                    substitution=substitution,
                    caller=caller,
                )
                continue

            if isinstance(statement, AIRFunctionWhen):
                self._scan_expression(
                    statement.condition,
                    identifiers=identifiers,
                    substitution=substitution,
                    caller=caller,
                )
                self._scan_statement_block(
                    tuple(statement.actions),
                    identifiers=dict(identifiers),
                    substitution=substitution,
                    caller=caller,
                )
                self._scan_statement_block(
                    tuple(statement.otherwise_actions),
                    identifiers=dict(identifiers),
                    substitution=substitution,
                    caller=caller,
                )
                continue

            # Future pure-function statements may contain expressions. Scan
            # their expression roots conservatively without assigning locals.
            for expression in self._iter_object_expression_roots(statement):
                self._scan_expression(
                    expression,
                    identifiers=identifiers,
                    substitution=substitution,
                    caller=caller,
                )

    def _iter_object_expression_roots(
        self,
        value: object,
    ) -> Iterable[AIRExpression]:
        if isinstance(value, AIRExpression):
            yield value
            return

        if isinstance(value, (tuple, list)):
            for item in value:
                yield from self._iter_object_expression_roots(item)
            return

        if is_dataclass(value):
            for field in fields(value):
                yield from self._iter_object_expression_roots(
                    getattr(value, field.name)
                )


def collect_linked_specializations(
    program: object,
) -> GenericSpecializationManifest:
    """Build the deterministic generic closure for one linked AIR program."""

    functions = tuple(getattr(program, "functions", ()) or ())
    return LinkedSpecializationCollector(functions).collect(
        program=program,
    )


__all__ = (
    "GenericSpecializationDependency",
    "GenericSpecializationManifest",
    "LinkedSpecializationCollector",
    "collect_linked_specializations",
)