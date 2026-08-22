"""P11.14J RED contract for pure AgentPlan effect-intent projection."""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "cac40ce8b6ad3a5ca603a078f3c14cadedeeee1d"
PREDECESSOR_TAG = "afp-p11-14i-freeze"
EXPECTED_BRANCH = "p11-14j-pure-agent-plan-effect-intent-projection"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git",) + args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def expect_type_error(fn, message: str) -> None:
    try:
        fn()
    except TypeError:
        return
    raise AssertionError(message)


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14I freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14I freeze is not ancestor of P11.14J",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14J branch changed")

    from agents.model import AgentDefinition, AgentIdentity
    from agents.planning import AgentPlan
    from effects.model import EffectIntent

    projection = importlib.import_module("agents.plan_projection")
    project_agent_plan_effect_intents = (
        projection.project_agent_plan_effect_intents
    )

    require(
        tuple(getattr(projection, "__all__", ()))
        == ("project_agent_plan_effect_intents",),
        "agents.plan_projection exports changed",
    )

    signature = inspect.signature(project_agent_plan_effect_intents)
    require(
        tuple(signature.parameters) == ("plan",),
        "projection function parameter shape changed",
    )

    definition = AgentDefinition(AgentIdentity("agent.projector"))
    first = EffectIntent("effect.project.first", "host.message")
    second = EffectIntent("effect.project.second", "host.message")
    plan = AgentPlan(definition, (first, second))

    projected = project_agent_plan_effect_intents(plan)

    require(
        type(projected) is tuple,
        "projection result must be an exact tuple",
    )
    require(
        projected is plan.effect_intents,
        "projection must preserve exact plan.effect_intents tuple identity",
    )
    require(
        projected[0] is first and projected[1] is second,
        "projection must preserve exact EffectIntent identities",
    )
    require(
        projected == (first, second),
        "projection must preserve authored order",
    )

    empty_plan = AgentPlan(definition)
    empty_projected = project_agent_plan_effect_intents(empty_plan)
    require(
        empty_projected is empty_plan.effect_intents,
        "empty projection must preserve exact tuple identity",
    )
    require(empty_projected == (), "empty plan projection must be valid")

    for bad in (
        None,
        definition,
        definition.identity,
        first,
        (first, second),
        [],
        {},
        True,
        1,
        "agent.projector",
        object(),
    ):
        expect_type_error(
            lambda bad=bad: project_agent_plan_effect_intents(bad),
            "non-exact AgentPlan accepted: {!r}".format(bad),
        )

    agents = importlib.import_module("agents")
    require(
        tuple(getattr(agents, "__all__", ())) == (),
        "agents top-level exports changed",
    )
    require(
        not hasattr(agents, "project_agent_plan_effect_intents"),
        "projection function was prematurely re-exported",
    )

    for forbidden in (
        "AgentAction",
        "AgentPlanExecutionRequest",
        "AgentPlanConsumptionRequest",
        "AgentPlanProjection",
        "AgentPlanHandoff",
        "AgentPlanResult",
        "AgentPlanReceipt",
        "AgentExecutionResult",
        "AgentExecutionReceipt",
        "AgentExecutor",
    ):
        require(
            not hasattr(projection, forbidden),
            "deferred surface leaked: {}".format(forbidden),
        )

    require(
        not (ROOT / "apexforge" / "agents" / "execution.py").exists(),
        "agents.execution must remain deferred",
    )

    source = (ROOT / "apexforge" / "agents" / "plan_projection.py").read_text(
        encoding="utf-8"
    )

    for forbidden_text in (
        "RuntimeEngine",
        "StateDelta",
        "authorize_principal",
        "authorize_principal_capabilities",
        "AuthorityCheck",
        "AuthorityGrant",
        "tooling",
        "workflow",
        "provider",
        "subprocess",
        "socket",
        "requests",
        "open(",
    ):
        require(
            forbidden_text not in source,
            "operative/deferred dependency leaked: {}".format(forbidden_text),
        )

    print("P11_14I_FREEZE_ANCESTRY=PASS")
    print("P11_14J_PRIMARY_OWNER=agents.plan_projection")
    print("P11_14J_FUNCTION=project_agent_plan_effect_intents")
    print("PROJECTION_INPUT=EXACT_AGENT_PLAN")
    print("PROJECTION_OUTPUT=EXACT_PLAN_EFFECT_INTENTS_TUPLE")
    print("PROJECTION_TUPLE_IDENTITY=PRESERVED")
    print("EFFECT_INTENT_OBJECT_IDENTITIES=PRESERVED")
    print("EFFECT_INTENT_AUTHORED_ORDER=PRESERVED")
    print("EMPTY_AGENT_PLAN_PROJECTION=VALID")
    print("REQUEST_WRAPPER=NONE")
    print("RESULT_RECEIPT_TRACE=NONE")
    print("AUTHORIZATION_RUNTIME_WORKFLOW_TOOLS=NONE")
    print("AGENTS_EXECUTION=DEFERRED")
    print("AGENT_ACTION=DEFERRED")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14J_PURE_AGENT_PLAN_EFFECT_INTENT_PROJECTION=PASS")
    print("P11_14J_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())