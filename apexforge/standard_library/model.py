"""Canonical AFP-P10 standard-library callable models.

P10.5 extends the pure host-backed built-in model to admit function-scoped
generic type variables. Generic signatures remain compile-time identities;
runtime invocation reconstructs an exact substitution from explicit metadata
and/or actual values, then verifies every argument and return value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from type_system.generics import (
    ApexTypeVariable,
    TypeIdentity,
    resolve_type,
    type_satisfies_constraints,
)
from type_system.inference import FunctionSignature
from standard_library.collection_value import RuntimeCollection
from standard_library.diagnostic_value import RuntimeDiagnostic
from standard_library.random_value import RuntimeRandom
from standard_library.result_value import RuntimeResult
from standard_library.time_value import RuntimeTime
from standard_library.type_info_value import RuntimeTypeInfo
from type_system.model import (
    BOOL,
    COLLECTION,
    DIAGNOSTIC,
    FLOAT,
    INT,
    RESULT,
    RANDOM,
    STRING,
    TIME,
    TYPE_INFO,
    VOID,
    ApexType,
)


class StandardLibraryInvocationError(RuntimeError):
    """Deterministic failure while invoking one standard-library function."""

    def __init__(self, *, code: str, message: str) -> None:
        if type(code) is not str or not code:
            raise ValueError(
                "StandardLibraryInvocationError.code must be non-empty."
            )
        if type(message) is not str or not message:
            raise ValueError(
                "StandardLibraryInvocationError.message must be non-empty."
            )
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


def _runtime_apex_type(value: Any) -> TypeIdentity | None:
    """Project one exact Python primitive into its ApexForge type identity."""

    if type(value) is int:
        return INT
    if type(value) is float:
        return FLOAT
    if type(value) is bool:
        return BOOL
    if type(value) is str:
        return STRING
    if type(value) is RuntimeResult:
        return RESULT
    if type(value) is RuntimeCollection:
        return COLLECTION
    if type(value) is RuntimeDiagnostic:
        return DIAGNOSTIC
    if type(value) is RuntimeTime:
        return TIME
    if type(value) is RuntimeRandom:
        return RANDOM
    if type(value) is RuntimeTypeInfo:
        return TYPE_INFO
    if value is None:
        return VOID
    return None


def _runtime_type_matches(value: Any, value_type: ApexType) -> bool:
    """Use exact Python identities so ``bool`` never masquerades as ``int``."""

    return _runtime_apex_type(value) is value_type


@dataclass(frozen=True)
class BuiltinFunction:
    """One immutable, pure standard-library function declaration."""

    name: str
    signature: FunctionSignature
    implementation: Callable[..., Any] = field(
        repr=False,
        compare=False,
    )
    documentation: str = ""
    purity: str = "pure"

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name.strip():
            raise ValueError("BuiltinFunction.name must be a non-empty string.")
        normalized_name = self.name.strip()
        object.__setattr__(self, "name", normalized_name)

        if not isinstance(self.signature, FunctionSignature):
            raise TypeError(
                "BuiltinFunction.signature must be FunctionSignature."
            )
        if self.signature.name != normalized_name:
            raise ValueError(
                "BuiltinFunction name must match signature.name; "
                f"received {normalized_name!r} and "
                f"{self.signature.name!r}."
            )
        if self.signature.return_type is None:
            raise ValueError(
                f"Standard-library function {normalized_name!r} requires "
                "a declared return type."
            )

        for index, parameter_type in enumerate(
            self.signature.parameter_types
        ):
            if parameter_type is None:
                raise ValueError(
                    f"Standard-library function {normalized_name!r} "
                    f"parameter[{index}] requires a declared type."
                )
            if parameter_type is VOID:
                raise ValueError(
                    f"Standard-library function {normalized_name!r} "
                    f"parameter[{index}] cannot use void."
                )
            if not isinstance(
                parameter_type,
                (ApexType, ApexTypeVariable),
            ):
                raise ValueError(
                    f"Standard-library function {normalized_name!r} "
                    f"parameter[{index}] has invalid type metadata."
                )

        if not isinstance(
            self.signature.return_type,
            (ApexType, ApexTypeVariable),
        ):
            raise ValueError(
                f"Standard-library function {normalized_name!r} contains "
                "invalid return type metadata."
            )

        if not callable(self.implementation):
            raise TypeError(
                "BuiltinFunction.implementation must be callable."
            )
        if self.purity != "pure":
            raise ValueError(
                "AFP-P10 admits only pure standard-library functions."
            )
        if type(self.documentation) is not str:
            raise TypeError("BuiltinFunction.documentation must be a string.")

    @property
    def canonical_id(self) -> str:
        return f"stdlib:{self.name}"

    @property
    def is_generic(self) -> bool:
        return bool(self.signature.type_parameters)

    def _runtime_substitution(
        self,
        arguments: tuple[Any, ...],
        type_arguments: tuple[object, ...],
    ) -> dict[ApexTypeVariable, ApexType]:
        """Build one exact runtime substitution for a generic invocation."""

        declared = self.signature.type_parameters
        bindings: dict[ApexTypeVariable, ApexType] = {}

        if type(type_arguments) is not tuple:
            raise TypeError(
                "BuiltinFunction.invoke type_arguments must be a tuple."
            )

        if type_arguments:
            if not declared:
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-009",
                    message=(
                        f"Standard-library function {self.name!r} is not "
                        "generic and cannot receive type arguments."
                    ),
                )
            if len(type_arguments) != len(declared):
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-009",
                    message=(
                        f"Generic standard-library function {self.name!r} "
                        f"expects {len(declared)} type argument(s); "
                        f"received {len(type_arguments)}."
                    ),
                )

            for variable, raw_type in zip(declared, type_arguments):
                try:
                    value_type = resolve_type(raw_type)
                except (TypeError, ValueError) as exc:
                    raise StandardLibraryInvocationError(
                        code="APX-STDLIB-009",
                        message=(
                            f"Generic standard-library function {self.name!r} "
                            f"received an invalid explicit type argument for "
                            f"{variable}."
                        ),
                    ) from exc

                # Open caller-owned variables are runtime-erased. Their exact
                # concrete identity is reconstructed from the actual value.
                if isinstance(value_type, ApexTypeVariable):
                    continue
                if value_type is VOID:
                    raise StandardLibraryInvocationError(
                        code="APX-STDLIB-009",
                        message=(
                            f"Generic standard-library function {self.name!r} "
                            f"cannot bind {variable} to void."
                        ),
                    )
                if not type_satisfies_constraints(
                    value_type,
                    variable.constraints,
                ):
                    raise StandardLibraryInvocationError(
                        code="APX-STDLIB-009",
                        message=(
                            f"Type argument {value_type} does not satisfy "
                            f"the constraints of {variable} in "
                            f"{self.name!r}."
                        ),
                    )
                bindings[variable] = value_type

        for index, (value, expected_type) in enumerate(
            zip(arguments, self.signature.parameter_types)
        ):
            actual_type = _runtime_apex_type(value)
            if actual_type is None or actual_type is VOID:
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-002",
                    message=(
                        f"Standard-library function {self.name!r} "
                        f"argument {index} has unsupported runtime type "
                        f"{type(value).__name__}."
                    ),
                )

            if isinstance(expected_type, ApexType):
                if actual_type is not expected_type:
                    raise StandardLibraryInvocationError(
                        code="APX-STDLIB-002",
                        message=(
                            f"Standard-library function {self.name!r} "
                            f"argument {index} expects {expected_type}; "
                            f"received {actual_type}."
                        ),
                    )
                continue

            if not isinstance(expected_type, ApexTypeVariable):
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-004",
                    message=(
                        f"Standard-library function {self.name!r} contains "
                        f"invalid parameter type metadata at index {index}."
                    ),
                )

            existing = bindings.get(expected_type)
            if existing is None:
                if not type_satisfies_constraints(
                    actual_type,
                    expected_type.constraints,
                ):
                    raise StandardLibraryInvocationError(
                        code="APX-STDLIB-009",
                        message=(
                            f"Runtime type {actual_type} does not satisfy "
                            f"the constraints of {expected_type} in "
                            f"{self.name!r}."
                        ),
                    )
                bindings[expected_type] = actual_type
            elif existing is not actual_type:
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-002",
                    message=(
                        f"Generic standard-library function {self.name!r} "
                        f"binds {expected_type} to {existing}, but argument "
                        f"{index} has type {actual_type}."
                    ),
                )

        return bindings

    def invoke(
        self,
        arguments: tuple[Any, ...],
        *,
        type_arguments: tuple[object, ...] = (),
    ) -> Any:
        """Invoke after exact arity, generic, argument, and return checks."""

        if type(arguments) is not tuple:
            raise TypeError(
                "BuiltinFunction.invoke arguments must be a tuple."
            )

        expected_types = self.signature.parameter_types
        if len(arguments) != len(expected_types):
            raise StandardLibraryInvocationError(
                code="APX-STDLIB-001",
                message=(
                    f"Standard-library function {self.name!r} expects "
                    f"{len(expected_types)} argument(s); "
                    f"received {len(arguments)}."
                ),
            )

        bindings = self._runtime_substitution(
            arguments,
            type_arguments,
        )

        try:
            result = self.implementation(*arguments)
        except StandardLibraryInvocationError:
            raise
        except Exception as exc:
            raise StandardLibraryInvocationError(
                code="APX-STDLIB-003",
                message=(
                    f"Standard-library function {self.name!r} failed: "
                    f"{type(exc).__name__}: {exc}"
                ),
            ) from exc

        return_type = self.signature.return_type
        expected_return: ApexType | None

        if isinstance(return_type, ApexTypeVariable):
            expected_return = bindings.get(return_type)
            if expected_return is None:
                raise StandardLibraryInvocationError(
                    code="APX-STDLIB-009",
                    message=(
                        f"Generic standard-library function {self.name!r} "
                        f"could not resolve return type {return_type}."
                    ),
                )
        elif isinstance(return_type, ApexType):
            expected_return = return_type
        else:
            expected_return = None

        if expected_return is None:
            raise StandardLibraryInvocationError(
                code="APX-STDLIB-004",
                message=(
                    f"Standard-library function {self.name!r} contains "
                    "invalid return type metadata."
                ),
            )
        if not _runtime_type_matches(result, expected_return):
            actual = _runtime_apex_type(result)
            actual_name = (
                str(actual)
                if actual is not None
                else type(result).__name__
            )
            raise StandardLibraryInvocationError(
                code="APX-STDLIB-004",
                message=(
                    f"Standard-library function {self.name!r} promised "
                    f"{expected_return} but produced {actual_name}."
                ),
            )

        return result


__all__ = (
    "BuiltinFunction",
    "StandardLibraryInvocationError",
)