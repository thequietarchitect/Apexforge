"""Explicit ApexForge authority-policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, Tuple

from authority.model import AuthorityCheck, AuthorityGrant


class AuthorityPolicy(Protocol):
    """Runtime policy interface consumed by RuntimeEngine."""

    def allows(
        self,
        check: AuthorityCheck,
    ) -> bool:
        ...


@dataclass(frozen=True)
class AuthorityEngine:
    """Deterministic, deny-by-default authority engine."""

    grants: Tuple[AuthorityGrant, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "grants",
            tuple(sorted(tuple(self.grants))),
        )

    @classmethod
    def from_grants(
        cls,
        grants: Iterable[AuthorityGrant],
    ) -> "AuthorityEngine":
        return cls(
            grants=tuple(grants),
        )

    def check(
        self,
        principal: str,
        capability: str,
        resource: str = "",
    ) -> bool:
        for grant in self.grants:
            if grant.principal != principal:
                continue

            if grant.capability not in (
                capability,
                "*",
            ):
                continue

            if grant.resource not in (
                "",
                "*",
                resource,
            ):
                continue

            return True

        return False

    def allows(
        self,
        check: AuthorityCheck,
    ) -> bool:
        return self.check(
            principal=check.principal,
            capability=check.capability,
            resource=check.resource,
        )