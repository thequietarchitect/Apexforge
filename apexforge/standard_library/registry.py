"""Immutable deterministic AFP-P10 standard-library registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional

from standard_library.model import BuiltinFunction
from type_system.inference import FunctionSignature


@dataclass(frozen=True)
class StandardLibraryRegistry:
    """Canonical name-indexed collection of pure built-in functions."""

    entries: tuple[BuiltinFunction, ...] = ()

    def __post_init__(self) -> None:
        if type(self.entries) is not tuple:
            raise TypeError(
                "StandardLibraryRegistry.entries must be a tuple."
            )

        normalized = tuple(sorted(self.entries, key=lambda entry: entry.name))
        seen: set[str] = set()
        for entry in normalized:
            if not isinstance(entry, BuiltinFunction):
                raise TypeError(
                    "StandardLibraryRegistry entries must be "
                    "BuiltinFunction values."
                )
            if entry.name in seen:
                raise ValueError(
                    f"Duplicate standard-library function {entry.name!r}."
                )
            seen.add(entry.name)

        object.__setattr__(self, "entries", normalized)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(entry.name for entry in self.entries)

    @property
    def canonical_ids(self) -> tuple[str, ...]:
        return tuple(entry.canonical_id for entry in self.entries)

    def _plain_name(self, reference: str) -> str:
        if type(reference) is not str or not reference.strip():
            raise ValueError(
                "Standard-library references must be non-empty strings."
            )
        normalized = reference.strip()
        if normalized.startswith("stdlib:"):
            return normalized[len("stdlib:"):]
        return normalized

    def get(self, reference: str) -> Optional[BuiltinFunction]:
        name = self._plain_name(reference)
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

    def require(self, reference: str) -> BuiltinFunction:
        entry = self.get(reference)
        if entry is None:
            raise KeyError(
                f"Unknown standard-library function {reference!r}."
            )
        return entry

    def contains(self, reference: str) -> bool:
        return self.get(reference) is not None

    def signatures(self) -> dict[str, FunctionSignature]:
        """Return a fresh deterministic plain-name signature mapping."""

        return {
            entry.name: entry.signature
            for entry in self.entries
        }

    def invoke(
        self,
        reference: str,
        arguments: tuple[Any, ...],
        *,
        type_arguments: tuple[object, ...] = (),
    ) -> Any:
        return self.require(reference).invoke(
            arguments,
            type_arguments=type_arguments,
        )

    def with_entries(
        self,
        entries: Iterable[BuiltinFunction],
    ) -> "StandardLibraryRegistry":
        return type(self)(
            self.entries + tuple(entries)
        )

    def merge_external_signatures(
        self,
        external: Optional[Mapping[str, FunctionSignature]],
    ) -> dict[str, FunctionSignature]:
        """Merge external user signatures without permitting shadowing."""

        merged = self.signatures()
        if external is None:
            return merged

        for name, signature in dict(external).items():
            if type(name) is not str or not name:
                raise ValueError(
                    "Function signature mappings require non-empty "
                    "string names."
                )
            if not isinstance(signature, FunctionSignature):
                raise TypeError(
                    "Function signature mappings require FunctionSignature "
                    f"values; {name!r} received "
                    f"{type(signature).__name__}."
                )
            if name != signature.name:
                raise ValueError(
                    "Function signature mapping key must match "
                    f"signature.name; received key {name!r} for "
                    f"{signature.name!r}."
                )
            if self.contains(name):
                raise ValueError(
                    f"External function signature {name!r} collides with "
                    "a reserved standard-library function."
                )
            if name in merged:
                raise ValueError(
                    f"Duplicate external function signature {name!r}."
                )
            merged[name] = signature

        return merged


__all__ = ("StandardLibraryRegistry",)