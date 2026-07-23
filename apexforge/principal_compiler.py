# principal_compiler.py

from air.model import AIRPrincipal, PrincipalAuthority
from language.parser import PrincipalNode


def compile_principal(node: PrincipalNode) -> AIRPrincipal:
    return AIRPrincipal(
        name=node.name,
        authorities=tuple(
            PrincipalAuthority(name=authority.name)
            for authority in node.authorities
        ),
    )