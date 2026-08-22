"""P11.14G RED contract for the minimal immutable agent plan."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "6dfd6004869dfd8e23c3bc1647d78574e66889ab"
PREDECESSOR_TAG = "afp-p11-14f-freeze"
EXPECTED_BRANCH = "p11-14g-minimal-immutable-agent-plan-effect-intents"

FROZEN_HASHES = {
    "apexforge/agents/__init__.py":
        "7EA62141AC47C0DC6B2B78952CA2EE29F0E03A7FF8B929C89C1FDEEE3CC23E3D",
    "apexforge/agents/model.py":
        "C602EE903A2E45008B6BB9181F77E3DC75E7060A44B64C2B3360A7E33C59928A",
    "apexforge/agents/catalog.py":
        "8BCF6363F5D9B8D3897A410112577F2F7A2DE57CE369E45E61246983D895F8B3",
    "apexforge/agents/resolution.py":
        "FB17DEDDCB2B215C520F1D9D0A28ADA6978CE04374171C0481230BB438316000",
    "apexforge/agents/character_binding.py":
        "635644E7D1D45E17738BF8A1EC076819BAE7A232B43A9891FBD1B7E4AAF88E58",
    "apexforge/p11_14f_first_operative_agent_contract_architecture_boundary_smoke_test.py":
        "9D77BC7C825AC1CD49E4824B6614195A59D8B644DE5791C5A75200E30AAE58B8",
    "docs/p11/P11_14F_FIRST_OPERATIVE_AGENT_CONTRACT_ARCHITECTURE_BOUNDARY.md":
        "950DCBE25B9FA8B44B445253F055EE83BBDFD938947DAF0557AF52B566D47BB1",
    "apexforge/effects/model.py":
        "7EECE7187CD964AAEAEC35BA633CDFFF31FFE6E6C07FD96E91D9638E3B43737A",
    "apexforge/runtime/state.py":
        "2B5EBA312E110E58DF7CCA75CD9A9F19683F5F70EEB864DF93CEDAAFB8F0DA11",
    "apexforge/runtime/engine.py":
        "C4B110B6445724602404C93A76AD86D255B25ECB6F9FACC15398455C0C680978",
    "apexforge/workflow/air_runner.py":
        "2DD571E331674BFAC8F25216878072E4BD38D66E8891FECBAC293F64DE9EFE29",
    "apexforge/workflow/directive_engine.py":
        "99B836574565F629F247C99248EBC2F9AA11412888CA2D4FEB8735CEF4C12BD2",
    "apexforge/authority/model.py":
        "E9951B62200E704F3CBEFAF97DB0AD9A242F650F285E7AAD3F8738A6C6B82E44",
    "apexforge/authority/registry.py":
        "A13880538539EBE1F9E6E75634364091F267D0119CBFA836AE24E327D11D35F3",
    "apexforge/authority/validator.py":
        "1B3C2432B3B9652B3C418312469BA706484D7A837F871320ED8D481394B84AB9",
    "apexforge/authorization/role_resolver.py":
        "363AC017FA7F56F8A857DFF5DF52414A50B5CFAC6AFD8102C87D8F01046BB0EC",
    "apexforge/air/model.py":
        "BD3B125094933A3CD40DC44DCA4E432786D8275949B5078E9DF620D64FABEE64",
    "apexforge/causality/model.py":
        "9503A3902A7AC0BE692027ED855F0C0A57B8644DDC0D6B129220FAD18BBA36A5",
    "apexforge/tooling/cli.py":
        "F1A36F9FC043A6175E22830F49273D45856A4FB88F28F1C2FE2AFCDA9B74EDEC",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
}


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


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()


def expect_type_error(fn, message: str) -> None:
    try:
        fn()
    except TypeError:
        return
    raise AssertionError(message)


def expect_value_error(fn, message: str) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(message)


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14F freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14F freeze is not ancestor of P11.14G",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14G branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    from agents.model import AgentDefinition, AgentIdentity
    from effects.model import EffectIntent

    planning = importlib.import_module("agents.planning")
    AgentPlan = planning.AgentPlan

    require(
        tuple(getattr(planning, "__all__", ())) == ("AgentPlan",),
        "agents.planning exports changed",
    )
    require(dataclasses.is_dataclass(AgentPlan), "AgentPlan is not a dataclass")
    params = getattr(AgentPlan, "__dataclass_params__")
    require(params.frozen is True, "AgentPlan is not frozen")
    require(params.order is False, "AgentPlan unexpectedly has ordering")
    require(
        tuple(field.name for field in dataclasses.fields(AgentPlan))
        == ("definition", "effect_intents"),
        "AgentPlan field shape changed",
    )

    definition = AgentDefinition(AgentIdentity("agent.operator"))
    first = EffectIntent("effect.first", "host.message")
    second = EffectIntent("effect.second", "host.message")
    plan = AgentPlan(definition, (first, second))

    require(plan.definition is definition, "AgentDefinition identity was not preserved")
    require(
        type(plan.effect_intents) is tuple,
        "AgentPlan.effect_intents must remain an exact tuple",
    )
    require(plan.effect_intents == (first, second), "authored effect order changed")
    require(plan.effect_intents[0] is first, "first EffectIntent identity was lost")
    require(plan.effect_intents[1] is second, "second EffectIntent identity was lost")

    empty = AgentPlan(definition)
    require(empty.effect_intents == (), "empty plan must be valid")

    equivalent_first = EffectIntent("effect.first", "host.message")
    equivalent_second = EffectIntent("effect.second", "host.message")
    equivalent_plan = AgentPlan(
        definition,
        (equivalent_first, equivalent_second),
    )
    require(plan == equivalent_plan, "AgentPlan value equality changed")
    require(hash(plan) == hash(equivalent_plan), "AgentPlan hashing changed")

    try:
        plan.effect_intents = ()
    except dataclasses.FrozenInstanceError:
        pass
    else:
        raise AssertionError("AgentPlan became mutable")

    for bad in (None, definition.identity, True, 1, "agent.operator", object()):
        expect_type_error(
            lambda bad=bad: AgentPlan(bad, ()),
            "invalid AgentPlan.definition accepted: {!r}".format(bad),
        )

    for bad in (None, [], [first], "effects", True, 1):
        expect_type_error(
            lambda bad=bad: AgentPlan(definition, bad),
            "non-tuple effect_intents accepted: {!r}".format(bad),
        )

    for bad in (None, True, 1, "effect.first", object()):
        expect_type_error(
            lambda bad=bad: AgentPlan(definition, (bad,)),
            "non-EffectIntent item accepted: {!r}".format(bad),
        )

    duplicate_id_a = EffectIntent("effect.duplicate", "host.message")
    duplicate_id_b = EffectIntent("effect.duplicate", "host.other")
    expect_value_error(
        lambda: AgentPlan(definition, (duplicate_id_a, duplicate_id_b)),
        "duplicate EffectIntent.id values were accepted",
    )

    same_payload_a = EffectIntent("effect.a", "host.message")
    same_payload_b = EffectIntent("effect.b", "host.message")
    distinct_ids = AgentPlan(definition, (same_payload_a, same_payload_b))
    require(
        distinct_ids.effect_intents == (same_payload_a, same_payload_b),
        "distinct effect IDs with equal semantic payload were rejected",
    )

    agents_package = importlib.import_module("agents")
    require(
        tuple(getattr(agents_package, "__all__", ())) == (),
        "agents top-level exports changed",
    )
    require(
        not hasattr(agents_package, "AgentPlan"),
        "AgentPlan was prematurely re-exported",
    )

    require(
        not hasattr(planning, "AgentAction"),
        "AgentAction was introduced prematurely",
    )
    for forbidden in (
        "AgentPlanner",
        "build_agent_plan",
        "AgentExecutor",
        "execute_agent_plan",
        "AgentToolRequest",
        "AgentRuntime",
        "AgentSession",
    ):
        require(
            not hasattr(planning, forbidden),
            "deferred planning/runtime surface leaked: {}".format(forbidden),
        )

    print("P11_14F_FREEZE_ANCESTRY=PASS")
    print("P11_14G_PRIMARY_OWNER=agents.planning")
    print("AGENT_PLAN_FIELDS=definition,effect_intents")
    print("AGENT_PLAN_IMMUTABLE=PASS")
    print("AGENT_DEFINITION_OBJECT_IDENTITY=PRESERVED")
    print("EFFECT_INTENT_OBJECT_IDENTITIES=PRESERVED")
    print("EFFECT_INTENT_AUTHORED_ORDER=PRESERVED")
    print("EMPTY_AGENT_PLAN=VALID")
    print("DUPLICATE_EFFECT_INTENT_IDS=REJECTED")
    print("DISTINCT_IDS_EQUAL_PAYLOAD=ALLOWED")
    print("AGENT_ACTION=DEFERRED")
    print("HOST_EFFECT_REQUEST_OWNER=effects.model.EffectIntent")
    print("PLANNER_EXECUTOR_TOOL_RUNTIME_SESSION=NONE")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14G_MINIMAL_IMMUTABLE_AGENT_PLAN_EFFECT_INTENTS=PASS")
    print("P11_14G_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())