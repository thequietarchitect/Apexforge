from language.compiler import compile_node, compile_source
from language.parser import parse
from air.model import AIRProgram

source = """
role Investigator {
    authority Sentinel
    authority Auditor
}
"""

result = compile_source(source)

assert isinstance(result, AIRProgram)
assert len(result.roles) == 1
role = result.roles[0]
assert role.name == "Investigator"
assert tuple(
    authority.name
    for authority in role.authorities
) == (
    "Sentinel",
    "Auditor",
)

print("ROLE COMPILER DISPATCH TEST PASSED")
