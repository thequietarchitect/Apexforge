"""Immutable declared-identity metadata for successful project builds."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from language.source import SourceSpan


_DECLARATION_PREFIXES = {
    "directive": "directive:",
    "function": "function:",
}
_DECLARED_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_MODULE_NAME_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*"
    r"(?:\.[A-Za-z_][A-Za-z0-9_]*)*\Z"
)


def _require_query(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    if not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    return value


def _require_kind(value: object) -> str:
    kind = _require_query(value, label="Declaration kind")
    if kind not in _DECLARATION_PREFIXES:
        raise ValueError("Declaration kind must be 'directive' or 'function'.")
    return kind


@dataclass(frozen=True)
class ProjectDeclaredIdentity:
    """One passive identity record for a successful project declaration."""

    kind: str
    declared_name: str
    current_air_id: str
    source_name: str
    module_name: Optional[str]
    qualified_display_name: str
    span: SourceSpan

    def __post_init__(self) -> None:
        kind = _require_kind(self.kind)

        if not isinstance(self.declared_name, str):
            raise TypeError("ProjectDeclaredIdentity.declared_name must be a string.")
        if _DECLARED_NAME_PATTERN.fullmatch(self.declared_name) is None:
            raise ValueError(
                "ProjectDeclaredIdentity.declared_name must be an ApexForge identifier."
            )

        if not isinstance(self.current_air_id, str):
            raise TypeError("ProjectDeclaredIdentity.current_air_id must be a string.")
        expected_air_id = f"{_DECLARATION_PREFIXES[kind]}{self.declared_name}"
        if self.current_air_id != expected_air_id:
            raise ValueError(
                "ProjectDeclaredIdentity.current_air_id must preserve the current "
                f"{kind} AIR ID {expected_air_id!r}."
            )

        if not isinstance(self.source_name, str):
            raise TypeError("ProjectDeclaredIdentity.source_name must be a string.")
        if not self.source_name.strip():
            raise ValueError("ProjectDeclaredIdentity.source_name cannot be blank.")

        if self.module_name is not None:
            if not isinstance(self.module_name, str):
                raise TypeError(
                    "ProjectDeclaredIdentity.module_name must be a string or None."
                )
            if _MODULE_NAME_PATTERN.fullmatch(self.module_name) is None:
                raise ValueError(
                    "ProjectDeclaredIdentity.module_name must be a valid ApexForge "
                    "module name."
                )

        if not isinstance(self.qualified_display_name, str):
            raise TypeError(
                "ProjectDeclaredIdentity.qualified_display_name must be a string."
            )
        expected_display_name = (
            self.declared_name
            if self.module_name is None
            else f"{self.module_name}.{self.declared_name}"
        )
        if self.qualified_display_name != expected_display_name:
            raise ValueError(
                "ProjectDeclaredIdentity.qualified_display_name must be the exact "
                "non-resolving declaration display projection."
            )

        if not isinstance(self.span, SourceSpan):
            raise TypeError("ProjectDeclaredIdentity.span must be SourceSpan.")
        if self.span.source_name != self.source_name:
            raise ValueError(
                "ProjectDeclaredIdentity.span must belong to its physical source."
            )


@dataclass(frozen=True)
class ProjectIdentityIndex:
    """Canonical immutable collection of declared-identity metadata."""

    identities: tuple[ProjectDeclaredIdentity, ...] = ()

    def __post_init__(self) -> None:
        identities = tuple(self.identities)
        if any(
            not isinstance(identity, ProjectDeclaredIdentity)
            for identity in identities
        ):
            raise TypeError(
                "ProjectIdentityIndex.identities must contain "
                "ProjectDeclaredIdentity values."
            )

        object.__setattr__(
            self,
            "identities",
            tuple(
                sorted(
                    identities,
                    key=lambda identity: (
                        identity.current_air_id,
                        identity.source_name.casefold(),
                        identity.source_name,
                        identity.span.start.offset,
                        identity.span.end.offset,
                        identity.kind,
                        identity.module_name is not None,
                        identity.module_name or "",
                        identity.declared_name,
                        identity.qualified_display_name,
                    ),
                )
            ),
        )

    def for_source(self, source_name: str) -> tuple[ProjectDeclaredIdentity, ...]:
        selected = _require_query(source_name, label="Source name")
        return tuple(
            identity
            for identity in self.identities
            if identity.source_name == selected
        )

    def for_module(self, module_name: str) -> tuple[ProjectDeclaredIdentity, ...]:
        selected = _require_query(module_name, label="Module name")
        return tuple(
            identity
            for identity in self.identities
            if identity.module_name == selected
        )

    def find_all(
        self,
        kind: str,
        declared_name: str,
    ) -> tuple[ProjectDeclaredIdentity, ...]:
        selected_kind = _require_kind(kind)
        selected_name = _require_query(declared_name, label="Declared name")
        return tuple(
            identity
            for identity in self.identities
            if identity.kind == selected_kind
            and identity.declared_name == selected_name
        )

    def find_current_air_id(
        self,
        current_air_id: str,
    ) -> tuple[ProjectDeclaredIdentity, ...]:
        selected = _require_query(current_air_id, label="Current AIR ID")
        return tuple(
            identity
            for identity in self.identities
            if identity.current_air_id == selected
        )

    def find_qualified_display_name(
        self,
        qualified_display_name: str,
    ) -> tuple[ProjectDeclaredIdentity, ...]:
        selected = _require_query(
            qualified_display_name,
            label="Qualified display name",
        )
        return tuple(
            identity
            for identity in self.identities
            if identity.qualified_display_name == selected
        )


__all__ = (
    "ProjectDeclaredIdentity",
    "ProjectIdentityIndex",
)
