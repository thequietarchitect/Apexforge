"""Authority model objects."""

from __future__ import annotations

from dataclasses import dataclass

from typing import Optional


@dataclass(frozen=True, order=True)
class Principal:
    id: str
    display_name: str = ""


@dataclass(frozen=True, order=True)
class AuthorityCheck:
    id: str
    principal: str
    capability: str
    resource: str

@dataclass(frozen=True)
class AuthorityGrant:
    name: str
    capabilities: tuple[str, ...]
    extends: Optional[str] = None