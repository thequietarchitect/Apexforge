"""Governance workflow: Sentinel -> AEGIS -> Gravitas."""

from __future__ import annotations

from examples.sentinel import run_sentinel_demo
from examples.aegis import run_aegis_demo
from examples.gravitas import run_gravitas_demo
from workflow.engine import WorkflowEngine, WorkflowStep

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

STEP_RUNNERS = {
    "Sentinel": run_sentinel_demo,
    "AEGIS": run_aegis_demo,
    "Gravitas": run_gravitas_demo,
}


def run_routed_governance_workflow():
    router = WorkflowRouter(GOVERNANCE_ROUTES)
    engine = WorkflowEngine()

    steps = []
    current = "Sentinel"

    while current:
        runner = STEP_RUNNERS[current]
        steps.append(WorkflowStep(current, runner))

        if current == "Sentinel":
            current = router.target_for("SentinelObservation")
        elif current == "AEGIS":
            current = router.target_for("AegisValidation")
        else:
            current = None

    return engine.execute(
        "Routed Governance Stack",
        tuple(steps),
    )