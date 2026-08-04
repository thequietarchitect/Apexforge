from __future__ import annotations
from typing import Optional

from air.model import AIRAuthority


class AuthorityRegistryError(Exception):
    """Base exception for authority-registry failures."""


class DuplicateAuthorityError(AuthorityRegistryError):
    """Raised when a canonical authority name is registered twice."""


class AuthorityInheritanceError(AuthorityRegistryError):
    pass


class UnknownAuthorityError(AuthorityRegistryError):
    """Raised when an authority is not registered."""


class AuthorityRegistry:
    def __init__(self):
        self._authorities: dict[str, AIRAuthority] = {}

    def register(self, authority: AIRAuthority) -> None:
        key = authority.name.casefold()

        if key in self._authorities:
            raise DuplicateAuthorityError(
                f"Authority '{key}' is already registered."
            )

        self._authorities[key] = authority

    def get(self, name: str) -> Optional[AIRAuthority]:
        return self._authorities.get(name.casefold())

    def resolve_capabilities(
        self,
        authority_name: str,
        active_path: set[str] | None = None,
    ) -> set[str]:
        if active_path is None:
            active_path = set()

        key = authority_name.casefold()

        if key in active_path:
            raise AuthorityInheritanceError(
                f"Authority inheritance cycle detected at "
                f"'{authority_name}'."
            )

        authority = self.get(authority_name)

        if authority is None:
            raise UnknownAuthorityError(
                f"Unknown authority '{authority_name}'."
            )

        next_path = active_path | {key}

        resolved = set(authority.capabilities)

        for inherited_authority in authority.inherits:
            resolved.update(
                self.resolve_capabilities(
                    authority_name=inherited_authority,
                    active_path=next_path,
                )
            )

        return resolved

    def has_capability(self, authority_name: str, capability: str) -> bool:
        return capability in self.resolve_capabilities(authority_name)

    def list_authorities(self) -> tuple[str, ...]:
        return tuple(self._authorities.keys())
