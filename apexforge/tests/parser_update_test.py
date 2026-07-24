"""Parser test for principal role references."""

from language.parser import (
    PrincipalAuthorityNode,
    PrincipalNode,
    PrincipalRoleNode,
    parse,
)


source = """
principal Alice {
    role Investigator
    role Auditor

    authority EmergencyOverride
    authority RecordAccess
}
"""

node = parse(source)


# Principal type and name

assert isinstance(node, PrincipalNode)
assert node.name == "Alice"


# Role references

assert node.roles == (
    PrincipalRoleNode(
        name="Investigator",
    ),
    PrincipalRoleNode(
        name="Auditor",
    ),
)

assert tuple(
    role.name
    for role in node.roles
) == (
    "Investigator",
    "Auditor",
)


# Direct authorities

assert node.authorities == (
    PrincipalAuthorityNode(
        name="EmergencyOverride",
    ),
    PrincipalAuthorityNode(
        name="RecordAccess",
    ),
)

assert tuple(
    authority.name
    for authority in node.authorities
) == (
    "EmergencyOverride",
    "RecordAccess",
)


print("PRINCIPAL ROLE PARSER TEST PASSED")