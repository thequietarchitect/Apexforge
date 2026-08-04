from air.model import AIRAuthority
from language.parser import AuthorityNode


def compile_authority(node: AuthorityNode) -> AIRAuthority:
    return AIRAuthority(
        id=f"authority:{node.name}",
        name=node.name,
        capabilities=tuple(
            capability.name for capability in node.capabilities
        ),
        inherits=(node.extends,) if node.extends is not None else (),
    )
