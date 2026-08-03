"""Immutable project declaration-ownership metadata."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from language.source import SourceSpan


_DECLARATION_PREFIXES = {
    "directive": "directive:",
    "function": "function:",
}
_SHORT_NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _require_query(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    if not value.strip():
        raise ValueError(f"{label} cannot be blank.")
    return value


@dataclass(frozen=True)
class ProjectDeclarationOwner:
    """One physical owner of a current canonical project declaration."""

    kind: str
    air_id: str
    source_name: str
    module_name: Optional[str]
    span: SourceSpan

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str):
            raise TypeError("ProjectDeclarationOwner.kind must be a string.")
        if self.kind not in _DECLARATION_PREFIXES:
            raise ValueError(
                "ProjectDeclarationOwner.kind must be 'directive' or 'function'."
            )

        if not isinstance(self.air_id, str):
            raise TypeError("ProjectDeclarationOwner.air_id must be a string.")
        if not self.air_id or self.air_id != self.air_id.strip():
            raise ValueError(
                "ProjectDeclarationOwner.air_id must be a non-empty canonical ID."
            )

        prefix = _DECLARATION_PREFIXES[self.kind]
        short_name = self.air_id[len(prefix):] if self.air_id.startswith(prefix) else ""
        if _SHORT_NAME_PATTERN.fullmatch(short_name) is None:
            raise ValueError(
                f"A {self.kind} owner requires a canonical {prefix!r} AIR ID."
            )

        if not isinstance(self.source_name, str):
            raise TypeError("ProjectDeclarationOwner.source_name must be a string.")
        if not self.source_name.strip():
            raise ValueError("ProjectDeclarationOwner.source_name cannot be blank.")

        if self.module_name is not None:
            if not isinstance(self.module_name, str):
                raise TypeError(
                    "ProjectDeclarationOwner.module_name must be a string or None."
                )
            if not self.module_name.strip():
                raise ValueError("ProjectDeclarationOwner.module_name cannot be blank.")

        if not isinstance(self.span, SourceSpan):
            raise TypeError("ProjectDeclarationOwner.span must be SourceSpan.")
        if self.span.source_name != self.source_name:
            raise ValueError(
                "ProjectDeclarationOwner.span must belong to its physical source."
            )


@dataclass(frozen=True)
class ProjectDeclarationOwnership:
    """Canonical immutable declaration-owner collection for one project."""

    declarations: tuple[ProjectDeclarationOwner, ...] = ()

    def __post_init__(self) -> None:
        declarations = tuple(self.declarations)
        if any(
            not isinstance(declaration, ProjectDeclarationOwner)
            for declaration in declarations
        ):
            raise TypeError(
                "ProjectDeclarationOwnership.declarations must contain "
                "ProjectDeclarationOwner values."
            )

        object.__setattr__(
            self,
            "declarations",
            tuple(
                sorted(
                    declarations,
                    key=lambda declaration: (
                        declaration.air_id,
                        declaration.source_name.casefold(),
                        declaration.source_name,
                        declaration.span.start.offset,
                        declaration.span.end.offset,
                        declaration.kind,
                        declaration.module_name is not None,
                        declaration.module_name or "",
                    ),
                )
            ),
        )

    def for_source(self, source_name: str) -> tuple[ProjectDeclarationOwner, ...]:
        selected = _require_query(source_name, label="Source name")
        return tuple(
            declaration
            for declaration in self.declarations
            if declaration.source_name == selected
        )

    def for_module(self, module_name: str) -> tuple[ProjectDeclarationOwner, ...]:
        selected = _require_query(module_name, label="Module name")
        return tuple(
            declaration
            for declaration in self.declarations
            if declaration.module_name == selected
        )

    def find_all(self, air_id: str) -> tuple[ProjectDeclarationOwner, ...]:
        selected = _require_query(air_id, label="AIR ID")
        return tuple(
            declaration
            for declaration in self.declarations
            if declaration.air_id == selected
        )


__all__ = (
    "ProjectDeclarationOwner",
    "ProjectDeclarationOwnership",
)
