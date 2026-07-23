"""Runtime registry for compiled ApexForge roles."""

from __future__ import annotations

from air.model import AIRRole


class RoleRegistryError(Exception):
    """Base exception for role-registry failures."""


class DuplicateRoleError(RoleRegistryError):
    """Raised when a role name is registered more than once."""


class UnknownRoleError(RoleRegistryError):
    """Raised when a requested role is not registered."""


class RoleRegistry:
    """Stores compiled roles by their unique names."""

    def __init__(self) -> None:
        self._roles: dict[str, AIRRole] = {}

    def register(self, role: AIRRole) -> None:
        if role.name in self._roles:
            raise DuplicateRoleError(
                f"Role '{role.name}' is already registered."
            )

        self._roles[role.name] = role

    def register_all(
        self,
        roles: tuple[AIRRole, ...],
    ) -> None:
        for role in roles:
            self.register(role)

    def get(self, name: str) -> AIRRole:
        try:
            return self._roles[name]
        except KeyError as exc:
            raise UnknownRoleError(
                f"Role '{name}' is not registered."
            ) from exc

    def contains(self, name: str) -> bool:
        return name in self._roles

    def all(self) -> tuple[AIRRole, ...]:
        return tuple(self._roles.values())

    def __len__(self) -> int:
        return len(self._roles)