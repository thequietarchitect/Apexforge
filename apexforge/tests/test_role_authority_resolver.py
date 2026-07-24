"""Tests for principal role-authority resolution."""

from air.model import (
    AIRPrincipal,
    AIRRole,
    AIRRoleAuthority,
    PrincipalAuthority,
)
from authorization.role_resolver import (
    PrincipalUnknownRoleError,
    resolve_effective_authorities,
)
from role.registry import RoleRegistry


def authority_names(authorities):
    return tuple(
        authority.name
        for authority in authorities
    )


# ---------------------------------------------------------
# Registry setup
# ---------------------------------------------------------

role_registry = RoleRegistry()

role_registry.register(
    AIRRole(
        name="Investigator",
        authorities=(
            AIRRoleAuthority(name="Sentinel"),
            AIRRoleAuthority(name="Auditor"),
        ),
    )
)

role_registry.register(
    AIRRole(
        name="Administrator",
        authorities=(
            AIRRoleAuthority(name="SystemControl"),
            AIRRoleAuthority(name="Auditor"),
        ),
    )
)


# ---------------------------------------------------------
# Test 1: direct authorities only
# ---------------------------------------------------------

direct_only = AIRPrincipal(
    name="Alice",
    roles=(),
    authorities=(
        PrincipalAuthority(name="EmergencyOverride"),
        PrincipalAuthority(name="RecordAccess"),
    ),
)

resolved = resolve_effective_authorities(
    direct_only,
    role_registry,
)

assert authority_names(resolved) == (
    "EmergencyOverride",
    "RecordAccess",
)


# ---------------------------------------------------------
# Test 2: role authorities only
# ---------------------------------------------------------

roles_only = AIRPrincipal(
    name="Bob",
    roles=(
        "Investigator",
    ),
    authorities=(),
)

resolved = resolve_effective_authorities(
    roles_only,
    role_registry,
)

assert authority_names(resolved) == (
    "Sentinel",
    "Auditor",
)


# ---------------------------------------------------------
# Test 3: direct and inherited authorities
# ---------------------------------------------------------

mixed = AIRPrincipal(
    name="Carol",
    roles=(
        "Investigator",
    ),
    authorities=(
        PrincipalAuthority(name="EmergencyOverride"),
    ),
)

resolved = resolve_effective_authorities(
    mixed,
    role_registry,
)

assert authority_names(resolved) == (
    "EmergencyOverride",
    "Sentinel",
    "Auditor",
)


# ---------------------------------------------------------
# Test 4: multiple roles
# ---------------------------------------------------------

multiple_roles = AIRPrincipal(
    name="Darius",
    roles=(
        "Investigator",
        "Administrator",
    ),
    authorities=(),
)

resolved = resolve_effective_authorities(
    multiple_roles,
    role_registry,
)

assert authority_names(resolved) == (
    "Sentinel",
    "Auditor",
    "SystemControl",
)


# ---------------------------------------------------------
# Test 5: duplicate authority deduplication
# ---------------------------------------------------------

duplicate_authority = AIRPrincipal(
    name="Elena",
    roles=(
        "Investigator",
        "Administrator",
    ),
    authorities=(
        PrincipalAuthority(name="Auditor"),
    ),
)

resolved = resolve_effective_authorities(
    duplicate_authority,
    role_registry,
)

assert authority_names(resolved) == (
    "Auditor",
    "Sentinel",
    "SystemControl",
)

assert authority_names(resolved).count("Auditor") == 1


# ---------------------------------------------------------
# Test 6: empty principal
# ---------------------------------------------------------

empty_principal = AIRPrincipal(
    name="Guest",
    roles=(),
    authorities=(),
)

resolved = resolve_effective_authorities(
    empty_principal,
    role_registry,
)

assert resolved == ()


# ---------------------------------------------------------
# Test 7: unknown role rejection
# ---------------------------------------------------------

unknown_role_principal = AIRPrincipal(
    name="Frank",
    roles=(
        "NonexistentRole",
    ),
    authorities=(),
)

try:
    resolve_effective_authorities(
        unknown_role_principal,
        role_registry,
    )
except PrincipalUnknownRoleError as exc:
    message = str(exc)

    assert "Frank" in message
    assert "NonexistentRole" in message
else:
    raise AssertionError(
        "Expected PrincipalUnknownRoleError."
    )


print("ROLE AUTHORITY RESOLVER TESTS PASSED")