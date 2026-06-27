from language.parser import parse
from workflow.air_registry import AirRegistry
from workflow.workflow_engine import WorkflowExecutionEngine

source = """
workflow Governance {
    invoke Sentinel
}
"""

workflow = parse(source)

registry = AirRegistry()
registry.discover("apexforge/directives")

result = WorkflowExecutionEngine().execute(
    registry,
    workflow,
)

print(result.ok)
print(result.name)
print([name for name, _ in result.results])