"""
ApexForge RBAC integration test.

Verifies:
- direct principal authorities;
- role-inherited authorities;
- mixed direct and inherited authorities;
- missing-authority rejection;
- unknown-role rejection.
"""

from air.model import (
    AIRPrincipal,
    AIRProgram,
    AIRRole,
    AIRRoleAuthority,
    PrincipalAuthority,
)

from authorization.role_resolver import (
    PrincipalUnknownRoleError,
)

from authority.validator import (
    PrincipalAuthorizationError,
    authorize_principal,
)

from role.registry import RoleRegistry


# ---------------------------------------------------------
# AIR program
# ---------------------------------------------------------

program = AIRProgram(
    version="0.2",
    states=(),
    events=(),
    authority_checks=(),
    causal_decisions=(),
    directives=(),
    requirements=(),
    authorities=(),
    principals=(),
    roles=(),
)


# ---------------------------------------------------------
# Role registry
# ---------------------------------------------------------

role_registry = RoleRegistry()

investigator_role = AIRRole(
    name="Investigator",
    authorities=(
        AIRRoleAuthority(name="Sentinel"),
        AIRRoleAuthority(name="Auditor"),
    ),
)

administrator_role = AIRRole(
    name="Administrator",
    authorities=(
        AIRRoleAuthority(name="EmergencyOverride"),
        AIRRoleAuthority(name="SystemControl"),
    ),
)

role_registry.register(investigator_role)
role_registry.register(administrator_role)

assert len(role_registry) == 2
assert role_registry.get("Investigator") is investigator_role
assert role_registry.get("Administrator") is administrator_role

print("Role registry initialized.")


# ---------------------------------------------------------
# Test 1: role-only principal
# ---------------------------------------------------------

alice = AIRPrincipal(
    name="Alice",
    roles=(
        "Investigator",
    ),
    authorities=(),
)

assert authorize_principal(
    principal=alice,
    authority=PrincipalAuthority(name="Sentinel"),
    role_registry=role_registry,
    program=program,
)

assert authorize_principal(
    principal=alice,
    authority=PrincipalAuthority(name="Auditor"),
    role_registry=role_registry,
    program=program,
)

print("Role-inherited authorization passed.")


# ---------------------------------------------------------
# Test 2: direct-authority-only principal
# ---------------------------------------------------------

bob = AIRPrincipal(
    name="Bob",
    roles=(),
    authorities=(
        PrincipalAuthority(name="EmergencyOverride"),
    ),
)

assert authorize_principal(
    principal=bob,
    authority=PrincipalAuthority(
        name="EmergencyOverride",
    ),
    role_registry=role_registry,
    program=program,
)

print("Direct authority authorization passed.")


# ---------------------------------------------------------
# Test 3: mixed direct and inherited authorities
# ---------------------------------------------------------

carol = AIRPrincipal(
    name="Carol",
    roles=(
        "Investigator",
    ),
    authorities=(
        PrincipalAuthority(name="EmergencyOverride"),
    ),
)

assert authorize_principal(
    principal=carol,
    authority=PrincipalAuthority(name="Sentinel"),
    role_registry=role_registry,
    program=program,
)

assert authorize_principal(
    principal=carol,
    authority=PrincipalAuthority(
        name="EmergencyOverride",
    ),
    role_registry=role_registry,
    program=program,
)

print("Mixed authority authorization passed.")


# ---------------------------------------------------------
# Test 4: multiple roles
# ---------------------------------------------------------

darius = AIRPrincipal(
    name="Darius",
    roles=(
        "Investigator",
        "Administrator",
    ),
    authorities=(),
)

assert authorize_principal(
    principal=darius,
    authority=PrincipalAuthority(name="Auditor"),
    role_registry=role_registry,
    program=program,
)

assert authorize_principal(
    principal=darius,
    authority=PrincipalAuthority(name="SystemControl"),
    role_registry=role_registry,
    program=program,
)

print("Multiple-role authorization passed.")


# ---------------------------------------------------------
# Test 5: missing authority
# ---------------------------------------------------------

try:
    authorize_principal(
        principal=alice,
        authority=PrincipalAuthority(name="SystemControl"),
        role_registry=role_registry,
        program=program,
    )

except PrincipalAuthorizationError as exc:
    message = str(exc)

    assert "Alice" in message
    assert "SystemControl" in message

    print("Missing authority correctly rejected.")

else:
    raise AssertionError(
        "Expected PrincipalAuthorizationError."
    )


# ---------------------------------------------------------
# Test 6: unknown role
# ---------------------------------------------------------

ghost = AIRPrincipal(
    name="Ghost",
    roles=(
        "GhostRole",
    ),
    authorities=(),
)

try:
    authorize_principal(
        principal=ghost,
        authority=PrincipalAuthority(name="Sentinel"),
        role_registry=role_registry,
        program=program,
    )

except PrincipalUnknownRoleError as exc:
    message = str(exc)

    assert "Ghost" in message
    assert "GhostRole" in message

    print("Unknown role correctly rejected.")

else:
    raise AssertionError(
        "Expected PrincipalUnknownRoleError."
    )


# ---------------------------------------------------------
# Test 7: empty principal
# ---------------------------------------------------------

guest = AIRPrincipal(
    name="Guest",
    roles=(),
    authorities=(),
)

try:
    authorize_principal(
        principal=guest,
        authority=PrincipalAuthority(name="Sentinel"),
        role_registry=role_registry,
        program=program,
    )

except PrincipalAuthorizationError:
    print("Empty principal correctly rejected.")

else:
    raise AssertionError(
        "Expected PrincipalAuthorizationError."
    )


print()
print("=" * 60)
print("APEXFORGE RBAC INTEGRATION TEST PASSED")
print("=" * 60)