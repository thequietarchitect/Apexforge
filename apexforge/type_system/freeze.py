"""AFP-P9 freeze manifest and deterministic lowered-AIR audit."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Iterable

from air.expressions import AIRCallExpression, AIRExpression
from air.functions import AIRFunction
from type_system.generics import ApexTypeVariable
from type_system.lowering import GenericLoweringResult


@dataclass(frozen=True)
class P9FreezeManifest:
    phase: str
    designation: str
    slices: tuple[str, ...]
    public_modules: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        if self.phase != "AFP-P9":
            raise ValueError("P9FreezeManifest.phase must be 'AFP-P9'.")
        if not self.designation:
            raise ValueError("P9FreezeManifest.designation cannot be empty.")
        if type(self.slices) is not tuple or len(self.slices) != 8:
            raise ValueError("P9 freeze manifest requires exactly eight slices.")
        if type(self.public_modules) is not tuple or not self.public_modules:
            raise ValueError("P9 freeze manifest requires public modules.")
        if not self.status:
            raise ValueError("P9FreezeManifest.status cannot be empty.")


@dataclass(frozen=True)
class P9FreezeAudit:
    specialization_count: int
    concrete_function_count: int
    executable_function_count: int
    rewritten_call_count: int
    preserved_generic_count: int

    @property
    def closed(self) -> bool:
        return self.specialization_count == self.concrete_function_count


P9_FREEZE_CANDIDATE = P9FreezeManifest(
    phase="AFP-P9",
    designation="Generics",
    slices=(
        "P9.1 Generic Declarations",
        "P9.2 Call-Site Inference and Substitution",
        "P9.3 Explicit Type Arguments",
        "P9.4 Generic Constraints",
        "P9.5 Specialization Records",
        "P9.6 Linked Specialization Closure",
        "P9.7 Deterministic Generic Lowering",
        "P9.8 Final Integration and Freeze",
    ),
    public_modules=(
        "type_system.constraints",
        "type_system.generics",
        "type_system.substitution",
        "type_system.inference",
        "type_system.specialization",
        "type_system.closure",
        "type_system.lowering",
        "type_system.p9",
    ),
    status="FREEZE CANDIDATE",
)


def _iter_expressions(value: object) -> Iterable[AIRExpression]:
    if value is None:
        return
    if isinstance(value, AIRExpression):
        yield value
        if is_dataclass(value):
            for field in fields(value):
                yield from _iter_expressions(getattr(value, field.name))
        return
    if isinstance(value, AIRFunction):
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from _iter_expressions(item)
        return
    if isinstance(value, dict):
        for key in sorted(value, key=repr):
            yield from _iter_expressions(value[key])
        return
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "functions":
                continue
            yield from _iter_expressions(getattr(value, field.name))


def _function_expressions(function: AIRFunction) -> Iterable[AIRExpression]:
    yield from _iter_expressions(getattr(function, "return_expression", None))
    yield from _iter_expressions(tuple(getattr(function, "local_bindings", ()) or ()))
    yield from _iter_expressions(tuple(getattr(function, "body", ()) or ()))


def _assert_concrete_type(value: object, *, owner: str) -> None:
    if isinstance(value, ApexTypeVariable):
        raise ValueError(f"{owner} retains unresolved type variable {value}.")


def audit_lowered_generics(result: GenericLoweringResult) -> P9FreezeAudit:
    """Require a closed, executable P9 lowering result.

    Source generic declarations may remain for traceability. Every executable
    function and program-level call must be concrete and must contain no
    explicit generic type-argument metadata after lowering.
    """

    if not isinstance(result, GenericLoweringResult):
        raise TypeError("audit_lowered_generics requires GenericLoweringResult.")

    if any(not record.is_closed for record in result.manifest.records):
        raise ValueError("P9 specialization manifest contains an open record.")

    concrete_by_id = {
        function.id: function
        for function in result.specialized_functions
    }
    concrete_by_name = {
        function.name: function
        for function in result.specialized_functions
    }

    if len(concrete_by_id) != len(result.specialized_functions):
        raise ValueError("P9 lowering emitted duplicate specialized function IDs.")
    if len(concrete_by_name) != len(result.specialized_functions):
        raise ValueError("P9 lowering emitted duplicate specialized names.")

    for binding in result.bindings:
        function = concrete_by_id.get(binding.function_id)
        if function is None or function.name != binding.function_name:
            raise ValueError(
                f"P9 lowering binding {binding.canonical_id!r} has no concrete function."
            )

    generic_names = {
        function.name
        for function in result.functions
        if tuple(getattr(function, "type_parameters", ()) or ())
    }
    generic_ids = {
        function.id
        for function in result.functions
        if tuple(getattr(function, "type_parameters", ()) or ())
    }

    executable = tuple(
        function
        for function in result.functions
        if not tuple(getattr(function, "type_parameters", ()) or ())
    )
    rewritten_calls = 0

    for function in executable:
        for index, parameter in enumerate(function.parameters):
            _assert_concrete_type(
                parameter.value_type,
                owner=f"Function {function.id!r} parameter[{index}]",
            )
        _assert_concrete_type(
            function.return_type,
            owner=f"Function {function.id!r} return",
        )

        for expression in _function_expressions(function):
            if not isinstance(expression, AIRCallExpression):
                continue
            rewritten_calls += 1
            if tuple(getattr(expression, "type_arguments", ()) or ()):
                raise ValueError(
                    f"Executable function {function.id!r} retains explicit type arguments."
                )
            if expression.target in generic_names or expression.target in generic_ids:
                raise ValueError(
                    f"Executable function {function.id!r} still targets generic "
                    f"declaration {expression.target!r}."
                )

    program_calls = 0
    for expression in _iter_expressions(result.program):
        if not isinstance(expression, AIRCallExpression):
            continue
        program_calls += 1
        if tuple(getattr(expression, "type_arguments", ()) or ()):
            raise ValueError("Lowered program-level call retains type arguments.")
        if expression.target in generic_names or expression.target in generic_ids:
            raise ValueError(
                f"Lowered program-level call still targets {expression.target!r}."
            )

    audit = P9FreezeAudit(
        specialization_count=len(result.manifest.records),
        concrete_function_count=len(result.specialized_functions),
        executable_function_count=len(executable),
        rewritten_call_count=rewritten_calls + program_calls,
        preserved_generic_count=len(generic_names),
    )
    if not audit.closed:
        raise ValueError(
            "P9 lowering specialization count does not match concrete function count."
        )
    return audit


__all__ = (
    "P9FreezeAudit",
    "P9FreezeManifest",
    "P9_FREEZE_CANDIDATE",
    "audit_lowered_generics",
)