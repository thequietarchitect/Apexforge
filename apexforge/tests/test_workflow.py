from authority.registry import AuthorityRegistry
from language.parser import parse
from workflow.air_registry import AirRegistry
from workflow.registry import PrincipalRegistry
from workflow.workflow_engine import WorkflowExecutionEngine

source = """
workflow Governance {
    invoke Sentinel
}
"""

workflow = parse(source)

registry = AirRegistry()
registry.discover("apexforge/directives")

sentinel = registry.resolve("sentinel")
authority_registry = AuthorityRegistry()
principal_registry = PrincipalRegistry()
principal_name = sentinel.principals[0].id

for authority in sentinel.authorities:
    authority_registry.register(authority)

principal_registry.register(sentinel.principals[0])

result = WorkflowExecutionEngine().execute(
    registry,
    workflow,
    authority_registry=authority_registry,
    principal_registry=principal_registry,
    principal_name=principal_name,
)

assert result.ok
assert result.name == "Governance"
assert tuple(name for name, _ in result.results) == (
    "sentinel",
)

root_result = result.results[0][1]
entered_directives = tuple(
    next(
        fact.value
        for fact in step.facts
        if fact.key == "directive"
    )
    for step in root_result.trace.steps
    if step.kind == "directive.start"
)

assert entered_directives == (
    "directive:Sentinel",
    "directive:AEGIS",
    "directive:Gravitas",
)

print(result.ok)
print(result.name)
print([name for name, _ in result.results])
