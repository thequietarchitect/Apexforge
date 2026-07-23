from air.model import AIRRoleAuthority, AIRRole

from language.parser import RoleNode

def compile_role(
    node: RoleNode,
) -> AIRRole:
    return AIRRole(
        name=node.name,
        authorities=tuple(
            AIRRoleAuthority(
                name=authority.name,
            )
            for authority in node.authorities
        ),
    )