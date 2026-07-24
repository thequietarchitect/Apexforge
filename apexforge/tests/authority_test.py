from language.parser import parse
from authority.compiler import compile_authority
from authority.registry import AuthorityRegistry


node = parse(
    "authority Sentinel { capability Observe capability Investigate }"
)

grant = compile_authority(node)

registry = AuthorityRegistry()
registry.register(grant)

print(registry.get("Sentinel"))
print(registry.has_capability("Sentinel", "Observe"))
print(registry.has_capability("Sentinel", "Execute"))
print(registry.list_authorities())