from language.parser import parse
from authority.compiler import compile_authority

node = parse(
    "authority Sentinel { capability Observe capability Investigate }"
)

grant = compile_authority(node)

print(grant)