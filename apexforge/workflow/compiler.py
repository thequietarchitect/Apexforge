"""Direct lowering for parsed workflow declarations."""

from air.model import AIRWorkflow, AIRWorkflowInvocation
from language.parser import WorkflowNode


def compile_workflow(node: WorkflowNode) -> AIRWorkflow:
    return AIRWorkflow(
        id=f"workflow:{node.name}",
        name=node.name,
        invocations=tuple(
            AIRWorkflowInvocation(target=invocation.target)
            for invocation in node.invocations
        ),
    )
