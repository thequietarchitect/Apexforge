"""P11.14M explicit reusable host-effect execution seam smoke test."""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "26bbd97cf749ca84abca722eb7e3119bcecb3458"
PREDECESSOR_TAG = "afp-p11-14l-freeze"
EXPECTED_BRANCH = "p11-14m-explicit-reusable-host-effect-execution-seam"


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
    require(resolved.stdout.strip() == BASELINE, "P11.14L freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14L freeze is not ancestor of P11.14M",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14M branch changed")

    from effects.model import EffectIntent

    effects = importlib.import_module("effects")
    require(
        tuple(getattr(effects, "__all__", ())) == ("EffectIntent",),
        "effects top-level exports changed",
    )
    require(
        not hasattr(effects, "HostEffectExecutionRecord"),
        "HostEffectExecutionRecord must not be top-level re-exported",
    )
    require(
        not hasattr(effects, "execute_host_effect"),
        "execute_host_effect must not be top-level re-exported",
    )

    host_execution = importlib.import_module("effects.host_execution")

    require(
        tuple(getattr(host_execution, "__all__", ()))
        == ("HostEffectExecutionRecord", "execute_host_effect"),
        "effects.host_execution exports changed",
    )

    record_type = host_execution.HostEffectExecutionRecord
    execute = host_execution.execute_host_effect

    require(dataclasses.is_dataclass(record_type), "record must be a dataclass")
    params = getattr(record_type, "__dataclass_params__", None)
    require(params is not None and params.frozen, "record must be frozen")

    fields = dataclasses.fields(record_type)
    require(len(fields) == 1, "record must contain exactly one field")
    require(fields[0].name == "intent", "record field must be intent")

    signature = inspect.signature(execute)
    require(
        tuple(signature.parameters) == ("intent", "handler"),
        "execute_host_effect signature changed",
    )

    intent = EffectIntent("effect.m.success", "host.test")
    calls = []

    def handler(received):
        calls.append(received)
        return {"ignored": True}

    record = execute(intent, handler)

    require(len(calls) == 1, "handler must be called exactly once")
    require(calls[0] is intent, "handler must receive exact intent identity")
    require(type(record) is record_type, "execution must return exact record type")
    require(record.intent is intent, "record must preserve exact intent identity")

    try:
        record.intent = EffectIntent("effect.m.other", "host.test")
    except (dataclasses.FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("HostEffectExecutionRecord must be immutable")

    for bad in (
        None,
        (),
        [],
        {},
        True,
        1,
        "effect",
        object(),
    ):
        try:
            execute(bad, handler)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "execute_host_effect accepted non-exact EffectIntent: {!r}".format(
                    bad
                )
            )

        try:
            record_type(bad)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "HostEffectExecutionRecord accepted non-exact EffectIntent: {!r}".format(
                    bad
                )
            )

    for bad_handler in (
        None,
        (),
        [],
        {},
        True,
        1,
        "handler",
        object(),
    ):
        try:
            execute(intent, bad_handler)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "execute_host_effect accepted non-callable handler: {!r}".format(
                    bad_handler
                )
            )

    class MarkerFailure(RuntimeError):
        pass

    marker = MarkerFailure("exact marker")
    failed_calls = []

    def failing_handler(received):
        failed_calls.append(received)
        raise marker

    try:
        execute(intent, failing_handler)
    except MarkerFailure as error:
        require(error is marker, "handler exception identity changed")
    else:
        raise AssertionError("handler exception did not propagate")

    require(len(failed_calls) == 1, "failing handler was retried")
    require(
        failed_calls[0] is intent,
        "failing handler did not receive exact intent identity",
    )

    require(
        not hasattr(host_execution, "execute_host_effects"),
        "batch host-effect execution must remain deferred",
    )

    for forbidden in (
        "EffectHandlerRegistry",
        "EffectRegistry",
        "HostEffectRegistry",
        "HostEffectExecutionResult",
        "HostEffectExecutionReceipt",
        "AgentExecutor",
        "AgentRuntime",
        "AgentSession",
        "AgentAction",
    ):
        require(
            not hasattr(host_execution, forbidden),
            "deferred production surface leaked: {}".format(forbidden),
        )

    print("P11_14L_FREEZE_ANCESTRY=PASS")
    print("P11_14M_PRIMARY_OWNER=effects.host_execution")
    print("P11_14M_RECORD=HostEffectExecutionRecord")
    print("P11_14M_FUNCTION=execute_host_effect")
    print("HOST_EFFECT_INPUT=EXACT_EFFECT_INTENT")
    print("HANDLER=CALLER_SUPPLIED_CALLABLE")
    print("HANDLER_INVOCATION_COUNT=EXACTLY_ONE")
    print("HANDLER_RECEIVES_EXACT_INTENT_IDENTITY=PASS")
    print("EXECUTION_RECORD_INTENT_IDENTITY=PRESERVED")
    print("EXECUTION_RECORD=FROZEN_ONE_FIELD")
    print("HANDLER_RETURN_PAYLOAD=IGNORED")
    print("HANDLER_EXCEPTION_IDENTITY=PROPAGATED")
    print("HANDLER_RETRY=NONE")
    print("EFFECT_TYPE_REGISTRY_DISPATCH=NONE")
    print("BATCH_EXECUTION=DEFERRED")
    print("AUTHORIZATION_RUNTIME_WORKFLOW_AGENTS_TOOLS_PROVIDERS=NONE")
    print("EFFECTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED")
    print("P11_14M_EXPLICIT_REUSABLE_HOST_EFFECT_EXECUTION_SEAM=PASS")
    print("P11_14M_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())