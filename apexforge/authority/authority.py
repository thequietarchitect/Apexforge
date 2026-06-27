"""Explicit authority policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Tuple

from air.types import as_tuple
from authority import AuthorityCheck, AuthorityGrant


class AuthorityPolicy(Protocol):
    def allows(self, check: AuthorityCheck) -> bool:
        ...


@dataclass(frozen=True)
class AuthorityEngine:
    grants: Tuple[AuthorityGrant, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", tuple(sorted(as_tuple(self.grants))))

    @classmethod
    def from_grants(cls, grants: Iterable[AuthorityGrant]) -> "AuthorityEngine":
        return cls(tuple(grants))

    def allows(self, check: AuthorityCheck) -> bool:
        return any(
            grant.n == check.principal
            and grant.capability == check.capability
            and grant.resource == check.resource
            for grant in self.grants
        )