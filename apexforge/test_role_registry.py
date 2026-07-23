from air.model import AIRRole, AIRRoleAuthority
from role.registry import (
    DuplicateRoleError,
    RoleRegistry,
    UnknownRoleError,
)


registry = RoleRegistry()

investigator = AIRRole(
    name="Investigator",
    authorities=(
        AIRRoleAuthority(name="Sentinel"),
        AIRRoleAuthority(name="Auditor"),
    ),
)

auditor = AIRRole(
    name="Auditor",
    authorities=(
        AIRRoleAuthority(name="ReadRecords"),
    ),
)

bulk_registry = RoleRegistry()

bulk_registry.register_all(
    (
        investigator,
        auditor,
    )
)

assert len(bulk_registry) == 2
assert bulk_registry.get("Investigator") is investigator
assert bulk_registry.get("Auditor") is auditor


# Registration

registry.register(investigator)

assert len(registry) == 1
assert registry.contains("Investigator")
assert not registry.contains("Administrator")


# Retrieval

retrieved = registry.get("Investigator")

assert retrieved is investigator
assert retrieved.name == "Investigator"
assert tuple(
    authority.name
    for authority in retrieved.authorities
) == (
    "Sentinel",
    "Auditor",
)


# Complete registry view

assert registry.all() == (
    investigator,
)


# Duplicate-role rejection

try:
    registry.register(investigator)
except DuplicateRoleError as exc:
    assert "Investigator" in str(exc)
else:
    raise AssertionError(
        "Expected DuplicateRoleError."
    )


# Unknown-role rejection

try:
    registry.get("Administrator")
except UnknownRoleError as exc:
    assert "Administrator" in str(exc)
else:
    raise AssertionError(
        "Expected UnknownRoleError."
    )


print("ROLE REGISTRY TEST PASSED")
print(bulk_registry)