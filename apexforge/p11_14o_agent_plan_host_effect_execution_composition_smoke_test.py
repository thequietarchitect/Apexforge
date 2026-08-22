"""P11.14O agent plan host-effect execution composition smoke test."""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "f9471def8fa9b3f6cbbc39bb9b4743838d624e46"
PREDECESSOR_TAG = "afp-p11-14n-freeze"
EXPECTED_BRANCH = "p11-14o-agent-plan-host-effect-execution-composition"


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


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14N freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14N freeze is not ancestor of P11.14O",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14O branch changed")

    from agents.model import AgentDefinition, AgentIdentity
    from agents.planning import AgentPlan
    from effects.host_execution import HostEffectExecutionRecord
    from effects.model import EffectIntent

    agents = importlib.import_module("agents")
    require(
        tuple(getattr(agents, "__all__", ())) == (),
        "agents top-level exports changed",
    )
    require(
        not hasattr(agents, "execute_agent_plan"),
        "execute_agent_plan must not be top-level re-exported",
    )

    execution = importlib.import_module("agents.execution")

    require(
        tuple(getattr(execution, "__all__", ())) == ("execute_agent_plan",),
        "agents.execution exports changed",
    )

    execute = execution.execute_agent_plan
    signature = inspect.signature(execute)
    require(
        tuple(signature.parameters) == ("plan", "handler"),
        "execute_agent_plan signature changed",
    )

    definition = AgentDefinition(identity=AgentIdentity("agent.o"))
    first = EffectIntent("effect.o.first", "host.first")
    second = EffectIntent("effect.o.second", "host.second")
    third = EffectIntent("effect.o.third", "host.third")
    plan = AgentPlan(
        definition=definition,
        effect_intents=(first, second, third),
    )

    original_projection = execution.project_agent_plan_effect_intents
    original_host_execute = execution.execute_host_effect

    projection_calls = []
    projected = plan.effect_intents

    def projection_probe(value):
        projection_calls.append(value)
        require(value is plan, "projection did not receive exact plan identity")
        return projected

    host_calls = []
    handler_calls = []

    def handler(intent):
        handler_calls.append(intent)
        return {"ignored": intent.id}

    def host_probe(intent, supplied_handler):
        host_calls.append((intent, supplied_handler))
        require(
            supplied_handler is handler,
            "same handler identity was not supplied to M",
        )
        return HostEffectExecutionRecord(intent=intent)

    execution.project_agent_plan_effect_intents = projection_probe
    execution.execute_host_effect = host_probe
    try:
        records = execute(plan, handler)
    finally:
        execution.project_agent_plan_effect_intents = original_projection
        execution.execute_host_effect = original_host_execute

    require(
        projection_calls == [plan],
        "J projection must be called exactly once",
    )
    require(
        tuple(item[0] for item in host_calls) == projected,
        "M calls must preserve projected order and identity",
    )
    require(
        all(item[1] is handler for item in host_calls),
        "handler identity changed across M calls",
    )
    require(type(records) is tuple, "result must be exact tuple")
    require(
        len(records) == len(projected),
        "result must contain one record per projected intent",
    )
    require(
        all(type(record) is HostEffectExecutionRecord for record in records),
        "result must contain exact HostEffectExecutionRecord values",
    )
    require(
        tuple(record.intent for record in records) == projected,
        "record intents must preserve projected order",
    )
    require(
        all(record.intent is intent for record, intent in zip(records, projected)),
        "record intent identities changed",
    )

    empty = AgentPlan(definition=definition)
    empty_handler_calls = []

    def empty_handler(intent):
        empty_handler_calls.append(intent)

    empty_result = execute(empty, empty_handler)
    require(type(empty_result) is tuple, "empty result must be exact tuple")
    require(empty_result == (), "empty plan must return empty tuple")
    require(empty_handler_calls == [], "empty plan must not invoke handler")

    invalid_empty_host_calls = []

    def impossible_host_probe(intent, supplied_handler):
        invalid_empty_host_calls.append((intent, supplied_handler))
        raise AssertionError("host execution must not begin for invalid handler")

    execution.execute_host_effect = impossible_host_probe
    try:
        try:
            execute(empty, None)
        except TypeError:
            pass
        else:
            raise AssertionError("non-callable handler accepted for empty plan")
    finally:
        execution.execute_host_effect = original_host_execute

    require(
        invalid_empty_host_calls == [],
        "host execution began before handler validation",
    )

    class AgentPlanSubclass(AgentPlan):
        pass

    subclass_plan = AgentPlanSubclass(
        definition=definition,
        effect_intents=(first,),
    )
    try:
        execute(subclass_plan, handler)
    except TypeError:
        pass
    else:
        raise AssertionError("AgentPlan subclass accepted")

    class MarkerFailure(RuntimeError):
        pass

    marker = MarkerFailure("exact failure")
    attempted = []

    def failing_handler(intent):
        attempted.append(intent)
        if intent is second:
            raise marker

    try:
        execute(plan, failing_handler)
    except MarkerFailure as error:
        require(error is marker, "handler exception identity changed")
    else:
        raise AssertionError("handler exception did not propagate")

    require(
        attempted == [first, second],
        "failure must stop later intents without retry",
    )

    for forbidden in (
        "AgentExecutor",
        "AgentExecutionAdapter",
        "AgentExecutionResult",
        "AgentRuntime",
        "AgentSession",
        "AgentAction",
        "execute_host_effects",
    ):
        require(
            not hasattr(execution, forbidden),
            "deferred surface leaked: {}".format(forbidden),
        )

    print("P11_14N_FREEZE_ANCESTRY=PASS")
    print("P11_14O_OWNER=agents.execution")
    print("P11_14O_FUNCTION=execute_agent_plan")
    print("P11_14O_INPUT=EXACT_AGENT_PLAN")
    print("P11_14O_PROJECTION_CALLS=EXACTLY_ONE")
    print("P11_14O_HANDLER=ONE_CALLER_SUPPLIED_CALLABLE")
    print("P11_14O_HOST_PRIMITIVE=FROZEN_M_EXECUTE_HOST_EFFECT")
    print("P11_14O_EXECUTION_ORDER=PROJECTED_AUTHORED_ORDER")
    print("P11_14O_RETURN=ORDERED_HOST_EFFECT_EXECUTION_RECORD_TUPLE")
    print("P11_14O_RECORD_INTENT_IDENTITY=PRESERVED")
    print("P11_14O_EMPTY_PLAN=EXACT_EMPTY_TUPLE")
    print("P11_14O_EMPTY_PLAN_HANDLER_CALLS=ZERO")
    print("P11_14O_INVALID_HANDLER_BEFORE_HOST_EXECUTION=PASS")
    print("P11_14O_FAILURE_EXCEPTION_IDENTITY=PROPAGATED")
    print("P11_14O_FAILURE_LATER_INTENTS=NOT_ATTEMPTED")
    print("P11_14O_RETRY=NONE")
    print("P11_14O_ROLLBACK=NONE")
    print("P11_14O_AGENT_EXECUTOR_CLASS=DEFERRED")
    print("P11_14O_AGENT_ACTION=DEFERRED")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14O_AGENT_PLAN_HOST_EFFECT_EXECUTION_COMPOSITION=PASS")
    print("P11_14O_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())