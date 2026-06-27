from authority.model import AuthorityGrant
from language.parser import AuthorityNode


def compile_authority(node: AuthorityNode) -> AuthorityGrant:
   return AuthorityGrant(
        name=node.name,
        capabilities=tuple(
            capability.name for capability in node.capabilities
        ),
    extends=node.extends,
)