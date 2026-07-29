"""Canonical authority model objects.

This module owns principals, authority checks, and runtime authority grants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True, order=True)
class Principal:
    """A principal referenced by AIR directives and authority checks."""

    id: str
    display_name: str = ""
    roles: Tuple[str, ...] = ()
    authorities: Tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "roles",
            tuple(self.roles),
        )
        object.__setattr__(
            self,
            "authorities",
            tuple(self.authorities),
        )


@dataclass(frozen=True, order=True)
class AuthorityCheck:
    """A capability request that must be authorized before execution."""

    id: str
    principal: str
    capability: str
    resource: str


@dataclass(frozen=True, order=True)
class AuthorityGrant:
    """One explicit capability grant.

    An empty resource or ``"*"`` grants the capability for every resource.
    A capability of ``"*"`` grants every capability for the matched resource.
    """

    principal: str
    capability: str
    resource: str = ""