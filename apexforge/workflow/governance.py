"""Governance workflow: Sentinel -> AEGIS -> Gravitas."""

from __future__ import annotations

from examples.sentinel import run_sentinel_demo
from examples.aegis import run_aegis_demo
from examples.gravitas import run_gravitas_demo
from workflow.engine import WorkflowEngine, WorkflowStep
from workflow.registry import DirectiveRegistry

def run_governance_workflow():
    engine = WorkflowEngine()

    return engine.execute(
        "Governance Stack",
        (
            WorkflowStep("Sentinel", run_sentinel_demo),
            WorkflowStep("AEGIS", run_aegis_demo),
            WorkflowStep("Gravitas", run_gravitas_demo),
        ),
    )

from workflow.router import WorkflowRouter, GOVERNANCE_ROUTES

REGISTRY = DirectiveRegistry()

REGISTRY.register(
    "Sentinel",
    run_sentinel_demo,
)

REGISTRY.register(
    "AEGIS",
    run_aegis_demo,
)

REGISTRY.register(
    "Gravitas",
    run_gravitas_demo,
)


def run_routed_governance_workflow():
    router = WorkflowRouter(GOVERNANCE_ROUTES)

    context_steps = []
    current = "Sentinel"

    while current is not None:
        runner = REGISTRY.resolve(current)
        step_result = runner()
        temp_engine = WorkflowEngine()
        context_steps.append(
            WorkflowStep(
                current,
                lambda result=step_result: result,
            )
        )

        workflow_result = temp_engine.execute(
            "Routed Governance Stack",
            tuple(context_steps),
        )

        latest_event = workflow_result.latest_event()

        if latest_event is None:
            break

        current = router.target_for(latest_event)

    final_engine = WorkflowEngine()

    return final_engine.execute(
        "Routed Governance Stack",
        tuple(context_steps),
    )