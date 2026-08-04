# principal_compiler.py

from air.model import Principal, PrincipalAuthority
from language.parser import PrincipalNode


def compile_principal(node: PrincipalNode) -> Principal:
    return Principal(
        id=f"principal:{node.name}",
        display_name=node.name,
        roles=tuple(
            role.name for role in node.roles
        ),
        authorities=tuple(
            PrincipalAuthority(name=authority.name)
            for authority in node.authorities
        ),
    )
