"""AFP-P10.12 final standard-library contract audit and freeze manifest.

The audit is host-side verification metadata. It does not add a language-level
built-in, alter runtime execution, or expose Python implementation objects to
ApexForge programs.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Optional

from standard_library.core import (
    DEFAULT_STANDARD_LIBRARY,
    STANDARD_LIBRARY_GROUPS,
)
from standard_library.model import BuiltinFunction
from standard_library.registry import StandardLibraryRegistry
from type_system.generics import ApexTypeVariable
from type_system.model import (
    BUILTIN_TYPES,
    BUILTIN_TYPES_BY_NAME,
    VOID,
    ApexType,
)


P10_STANDARD_LIBRARY_VERSION = "10.12"


P10_SLICE_NAMES = (
    "P10.1 Registry and Pure Built-in Foundation",
    "P10.2 Numeric Utilities",
    "P10.3 String Utilities",
    "P10.4 Boolean and Conversion Utilities",
    "P10.5 Generic Value Utilities",
    "P10.5A Host-Generic Lowering Boundary",
    "P10.6 Structured Results and Safe Parsing",
    "P10.7 Immutable Collection Utilities",
    "P10.8 Deterministic UTC Time Utilities",
    "P10.9 Deterministic Random Utilities",
    "P10.10 Structured Diagnostic Utilities",
    "P10.11 Safe Reflection and Introspection",
    "P10.12 Final Integration, Contract Audit, and Freeze",
)


P10_PUBLIC_MODULES = (
    "standard_library.booleans",
    "standard_library.collection_value",
    "standard_library.collections",
    "standard_library.conversions",
    "standard_library.core",
    "standard_library.diagnostic_value",
    "standard_library.diagnostics",
    "standard_library.freeze",
    "standard_library.generic_values",
    "standard_library.model",
    "standard_library.numeric",
    "standard_library.random_value",
    "standard_library.randoms",
    "standard_library.reflection",
    "standard_library.registry",
    "standard_library.result_value",
    "standard_library.results",
    "standard_library.strings",
    "standard_library.time_value",
    "standard_library.times",
    "standard_library.type_info_value",
)


@dataclass(frozen=True)
class P10FreezeManifest:
    """One immutable declaration of the final AFP-P10 public contract."""

    phase: str
    designation: str
    version: str
    slices: tuple[str, ...]
    public_modules: tuple[str, ...]
    group_count: int
    builtin_count: int
    builtin_type_count: int
    contract_sha256: str
    status: str

    def __post_init__(self) -> None:
        if self.phase != "AFP-P10":
            raise ValueError("P10FreezeManifest.phase must be 'AFP-P10'.")
        if self.designation != "Pure Standard Library":
            raise ValueError(
                "P10FreezeManifest.designation must be "
                "'Pure Standard Library'."
            )
        if self.version != P10_STANDARD_LIBRARY_VERSION:
            raise ValueError(
                "P10FreezeManifest.version must match the active P10 API."
            )
        if type(self.slices) is not tuple or len(self.slices) != 13:
            raise ValueError(
                "P10 freeze manifest requires exactly thirteen named slices."
            )
        if type(self.public_modules) is not tuple or not self.public_modules:
            raise ValueError("P10 freeze manifest requires public modules.")
        if type(self.group_count) is not int or self.group_count <= 0:
            raise ValueError("P10 freeze group_count must be positive.")
        if type(self.builtin_count) is not int or self.builtin_count <= 0:
            raise ValueError("P10 freeze builtin_count must be positive.")
        if (
            type(self.builtin_type_count) is not int
            or self.builtin_type_count <= 0
        ):
            raise ValueError(
                "P10 freeze builtin_type_count must be positive."
            )
        if (
            type(self.contract_sha256) is not str
            or len(self.contract_sha256) != 64
            or any(
                character not in "0123456789abcdef"
                for character in self.contract_sha256
            )
        ):
            raise ValueError(
                "P10 freeze contract_sha256 must be lowercase SHA-256 hex."
            )
        if self.status != "FREEZE CANDIDATE":
            raise ValueError(
                "P10FreezeManifest.status must be 'FREEZE CANDIDATE'."
            )


@dataclass(frozen=True)
class P10StandardLibraryAudit:
    """Deterministic measurements from one successful contract audit."""

    group_count: int
    builtin_count: int
    generic_builtin_count: int
    signature_count: int
    canonical_id_count: int
    builtin_type_count: int
    contract_sha256: str

    @property
    def closed(self) -> bool:
        return (
            self.builtin_count == self.signature_count
            and self.builtin_count == self.canonical_id_count
        )


def _has_control_character(value: str) -> bool:
    return any(
        ord(character) < 32 or ord(character) == 127
        for character in value
    )


def _require_contract_identifier(value: str, *, owner: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{owner} must be a non-empty string.")
    if not value.isidentifier() or value.lower() != value:
        raise ValueError(
            f"{owner} must be a lowercase identifier; received {value!r}."
        )


def _type_payload(value: object) -> dict[str, Any]:
    if isinstance(value, ApexType):
        return {
            "kind": "builtin",
            "name": value.name,
        }
    if isinstance(value, ApexTypeVariable):
        return {
            "kind": "variable",
            "name": value.name,
            "owner": value.owner,
            "constraints": tuple(
                constraint.name
                for constraint in value.constraints
            ),
        }
    raise TypeError(
        "P10 contract received unsupported type metadata "
        f"{type(value).__name__}."
    )


def standard_library_contract_payload(
    registry: StandardLibraryRegistry = DEFAULT_STANDARD_LIBRARY,
    groups: tuple[tuple[str, tuple[BuiltinFunction, ...]], ...] = (
        STANDARD_LIBRARY_GROUPS
    ),
) -> dict[str, Any]:
    """Return a JSON-compatible deterministic public-contract description."""

    if not isinstance(registry, StandardLibraryRegistry):
        raise TypeError(
            "standard_library_contract_payload requires "
            "StandardLibraryRegistry."
        )
    if type(groups) is not tuple:
        raise TypeError("P10 standard-library groups must be a tuple.")

    group_payload = []
    for group_name, entries in groups:
        if type(entries) is not tuple:
            raise TypeError(
                f"P10 standard-library group {group_name!r} must be a tuple."
            )
        group_payload.append(
            {
                "name": group_name,
                "builtins": tuple(
                    {
                        "name": entry.name,
                        "canonical_id": entry.canonical_id,
                        "parameters": tuple(
                            _type_payload(value_type)
                            for value_type in entry.signature.parameter_types
                        ),
                        "return": _type_payload(
                            entry.signature.return_type
                        ),
                        "type_parameters": tuple(
                            _type_payload(type_parameter)
                            for type_parameter in (
                                entry.signature.type_parameters
                            )
                        ),
                        "purity": entry.purity,
                        "documentation": entry.documentation,
                        "implementation_module": (
                            entry.implementation.__module__
                        ),
                        "implementation_name": (
                            entry.implementation.__qualname__
                        ),
                    }
                    for entry in entries
                ),
            }
        )

    return {
        "phase": "AFP-P10",
        "designation": "Pure Standard Library",
        "version": P10_STANDARD_LIBRARY_VERSION,
        "builtin_types": tuple(
            value_type.name
            for value_type in BUILTIN_TYPES
        ),
        "groups": tuple(group_payload),
        "registry_names": registry.names,
        "registry_canonical_ids": registry.canonical_ids,
    }


def standard_library_contract_sha256(
    registry: StandardLibraryRegistry = DEFAULT_STANDARD_LIBRARY,
    groups: tuple[tuple[str, tuple[BuiltinFunction, ...]], ...] = (
        STANDARD_LIBRARY_GROUPS
    ),
) -> str:
    """Return the canonical SHA-256 digest for one P10 contract."""

    payload = standard_library_contract_payload(registry, groups)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _iter_signature_types(entry: BuiltinFunction) -> Iterable[object]:
    yield from entry.signature.parameter_types
    yield entry.signature.return_type


def audit_standard_library(
    registry: StandardLibraryRegistry = DEFAULT_STANDARD_LIBRARY,
    groups: tuple[tuple[str, tuple[BuiltinFunction, ...]], ...] = (
        STANDARD_LIBRARY_GROUPS
    ),
    *,
    expected_sha256: Optional[str] = None,
) -> P10StandardLibraryAudit:
    """Require the closed, deterministic AFP-P10.12 public contract."""

    if not isinstance(registry, StandardLibraryRegistry):
        raise TypeError(
            "audit_standard_library requires StandardLibraryRegistry."
        )
    if type(groups) is not tuple:
        raise TypeError("P10 standard-library groups must be a tuple.")

    group_names: set[str] = set()
    flattened: list[BuiltinFunction] = []
    owned_names: dict[str, str] = {}

    for group_index, group in enumerate(groups):
        if type(group) is not tuple or len(group) != 2:
            raise ValueError(
                f"P10 standard-library group[{group_index}] must be "
                "a (name, entries) pair."
            )
        group_name, entries = group
        _require_contract_identifier(
            group_name,
            owner=f"P10 standard-library group[{group_index}] name",
        )
        if group_name in group_names:
            raise ValueError(
                f"Duplicate P10 standard-library group {group_name!r}."
            )
        group_names.add(group_name)

        if type(entries) is not tuple or not entries:
            raise ValueError(
                f"P10 standard-library group {group_name!r} must contain "
                "a non-empty tuple of built-ins."
            )

        for entry_index, entry in enumerate(entries):
            if not isinstance(entry, BuiltinFunction):
                raise TypeError(
                    f"P10 group {group_name!r} entry[{entry_index}] must "
                    "be BuiltinFunction."
                )
            _require_contract_identifier(
                entry.name,
                owner=(
                    f"P10 group {group_name!r} entry[{entry_index}] name"
                ),
            )
            previous_owner = owned_names.get(entry.name)
            if previous_owner is not None:
                raise ValueError(
                    f"P10 built-in {entry.name!r} belongs to both "
                    f"{previous_owner!r} and {group_name!r}."
                )
            owned_names[entry.name] = group_name
            flattened.append(entry)

            if entry.signature.name != entry.name:
                raise ValueError(
                    f"P10 built-in {entry.name!r} signature name changed."
                )
            if entry.canonical_id != f"stdlib:{entry.name}":
                raise ValueError(
                    f"P10 built-in {entry.name!r} canonical ID changed."
                )
            if entry.purity != "pure":
                raise ValueError(
                    f"P10 built-in {entry.name!r} is not pure."
                )
            if not entry.documentation.strip():
                raise ValueError(
                    f"P10 built-in {entry.name!r} lacks documentation."
                )
            if _has_control_character(entry.documentation):
                raise ValueError(
                    f"P10 built-in {entry.name!r} documentation contains "
                    "a control character."
                )
            if entry.signature.return_type is None:
                raise ValueError(
                    f"P10 built-in {entry.name!r} has no return type."
                )
            if any(
                parameter_type is None or parameter_type is VOID
                for parameter_type in entry.signature.parameter_types
            ):
                raise ValueError(
                    f"P10 built-in {entry.name!r} contains an invalid "
                    "parameter type."
                )
            if not callable(entry.implementation):
                raise ValueError(
                    f"P10 built-in {entry.name!r} implementation is not "
                    "callable."
                )

            declared_ids = {
                id(type_parameter)
                for type_parameter in entry.signature.type_parameters
            }
            referenced_ids = {
                id(value_type)
                for value_type in _iter_signature_types(entry)
                if isinstance(value_type, ApexTypeVariable)
            }
            if declared_ids != referenced_ids:
                raise ValueError(
                    f"P10 generic built-in {entry.name!r} type-parameter "
                    "declaration and use differ."
                )

    flattened_tuple = tuple(flattened)
    expected_entries = tuple(
        sorted(flattened_tuple, key=lambda entry: entry.name)
    )
    if registry.entries != expected_entries:
        raise ValueError(
            "P10 registry entries do not exactly match the declared groups."
        )
    if registry.names != tuple(entry.name for entry in expected_entries):
        raise ValueError("P10 registry name index changed.")
    if registry.canonical_ids != tuple(
        entry.canonical_id
        for entry in expected_entries
    ):
        raise ValueError("P10 registry canonical-ID index changed.")
    if tuple(registry.signatures()) != registry.names:
        raise ValueError("P10 registry signature ordering changed.")

    if tuple(BUILTIN_TYPES_BY_NAME) != tuple(
        value_type.name
        for value_type in BUILTIN_TYPES
    ):
        raise ValueError("P10 built-in type index order changed.")
    if tuple(BUILTIN_TYPES_BY_NAME.values()) != BUILTIN_TYPES:
        raise ValueError("P10 built-in type index identities changed.")

    if len(groups) != P10_FREEZE_CANDIDATE.group_count:
        raise ValueError(
            "P10 standard-library group count differs from the freeze manifest."
        )
    if len(registry.entries) != P10_FREEZE_CANDIDATE.builtin_count:
        raise ValueError(
            "P10 standard-library built-in count differs from the freeze manifest."
        )
    if len(BUILTIN_TYPES) != P10_FREEZE_CANDIDATE.builtin_type_count:
        raise ValueError(
            "P10 built-in type count differs from the freeze manifest."
        )

    digest = standard_library_contract_sha256(registry, groups)
    required_digest = (
        P10_FREEZE_CANDIDATE.contract_sha256
        if expected_sha256 is None
        else expected_sha256
    )
    if digest != required_digest:
        raise ValueError(
            "P10 standard-library contract fingerprint changed; "
            f"expected {required_digest}, received {digest}."
        )

    audit = P10StandardLibraryAudit(
        group_count=len(groups),
        builtin_count=len(registry.entries),
        generic_builtin_count=sum(
            1
            for entry in registry.entries
            if entry.is_generic
        ),
        signature_count=len(registry.signatures()),
        canonical_id_count=len(registry.canonical_ids),
        builtin_type_count=len(BUILTIN_TYPES),
        contract_sha256=digest,
    )
    if not audit.closed:
        raise ValueError("P10 standard-library contract is not closed.")
    return audit


# Filled with the canonical digest after the contract payload is defined.
P10_FREEZE_CANDIDATE = P10FreezeManifest(
    phase="AFP-P10",
    designation="Pure Standard Library",
    version=P10_STANDARD_LIBRARY_VERSION,
    slices=P10_SLICE_NAMES,
    public_modules=P10_PUBLIC_MODULES,
    group_count=12,
    builtin_count=134,
    builtin_type_count=11,
    contract_sha256=(
        "602ccca69afc0f4452a3f90d98b0fb88"
        "34ce3ede1dab3637e443c398153b059e"
    ),
    status="FREEZE CANDIDATE",
)


__all__ = (
    "P10FreezeManifest",
    "P10StandardLibraryAudit",
    "P10_FREEZE_CANDIDATE",
    "P10_PUBLIC_MODULES",
    "P10_SLICE_NAMES",
    "P10_STANDARD_LIBRARY_VERSION",
    "audit_standard_library",
    "standard_library_contract_payload",
    "standard_library_contract_sha256",
)