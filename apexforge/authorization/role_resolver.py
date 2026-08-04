"""Resolve a principal's direct and role-inherited authorities."""

from __future__ import annotations

from air.model import AIRPrincipal, PrincipalAuthority
from role.registry import RoleRegistry, UnknownRoleError


class AuthorityResolutionError(Exception):
    """Base exception for effective-authority resolution failures."""


class PrincipalUnknownRoleError(AuthorityResolutionError):
    """Raised when a principal references an unregistered role."""


def resolve_effective_authorities(
    principal: AIRPrincipal,
    role_registry: RoleRegistry,
) -> tuple[PrincipalAuthority, ...]:
    """
    Return the principal's direct and role-inherited authorities.

    Authority names are deduplicated while preserving first-seen order.

    Resolution order:
        1. Direct principal authorities.
        2. Authorities inherited from roles, in declared role order.
    """

    resolved: list[PrincipalAuthority] = []
    seen_names: set[str] = set()

    def add_authority(name: str) -> None:
        canonical = name.casefold()

        if canonical in seen_names:
            return

        seen_names.add(canonical)
        resolved.append(
            PrincipalAuthority(
                name=name,
            )
        )

    # Direct authorities take precedence in ordering.

    for authority in principal.authorities:
        add_authority(authority.name)

    # Add authorities inherited through roles.

    for role_name in principal.roles:
        try:
            role = role_registry.get(role_name)
        except UnknownRoleError as exc:
            raise PrincipalUnknownRoleError(
                f"Principal '{principal.name}' references "
                f"unknown role '{role_name}'."
            ) from exc

        for authority in role.authorities:
            add_authority(authority.name)

    return tuple(resolved)