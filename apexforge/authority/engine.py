from dataclasses import dataclass
from typing import Protocol

from authority.model import AuthorityGrant


class AuthorityPolicy(Protocol):
    def allows(self, check) -> bool:
        ...


@dataclass(frozen=True)
class AuthorityEngine:
    grants: tuple[AuthorityGrant, ...]

    @classmethod
    def from_grants(cls, grants: tuple[AuthorityGrant, ...]):
        return cls(grants=grants)

    def check(
        self,
        principal: str,
        capability: str,
        resource: str = "",
    ) -> bool:
        for grant in self.grants:
            if grant.name == principal:
                return capability in grant.capabilities

        return False

    def allows(self, check) -> bool:
        return self.check(
            principal=check.principal,
            capability=check.capability,
            resource=getattr(check, "resource", ""),
        )