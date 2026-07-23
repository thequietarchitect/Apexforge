from language.compiler import compile_node, compile_source
from language.parser import parse
from air.model import AIRRole

source = """
role Investigator {
    authority Sentinel
    authority Auditor
}
"""

result = compile_source(source)

assert isinstance(result, AIRRole)
assert result.name == "Investigator"
assert tuple(
    authority.name
    for authority in result.authorities
) == (
    "Sentinel",
    "Auditor",
)

print("ROLE COMPILER DISPATCH TEST PASSED")