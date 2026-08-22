"""P11.14N agent plan host-effect consumption successor architecture boundary."""

from __future__ import annotations

import ast
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "4421984a8f5c43654eab9374516742a5b7333365"
PREDECESSOR_TAG = "afp-p11-14m-freeze"
EXPECTED_BRANCH = (
    "p11-14n-agent-plan-host-effect-consumption-successor-architecture-boundary"
)

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
    "apexforge/agents/planning.py":
        "6E157C3EA2831E7D226C858C5018B3DF7533957B9F456D2933DD8A8F53EB226A",
    "apexforge/agents/plan_projection.py":
        "5313A46B833FE914F34C940704FB6E2E75D4F964F6DAD46E36A5AC7366C75163",
    "apexforge/effects/__init__.py":
        "68E982EB2AEF937F57114EDAA8D36C27F8D2357A763D3EA0EE933CAFCC2A2839",
    "apexforge/effects/model.py":
        "7EECE7187CD964AAEAEC35BA633CDFFF31FFE6E6C07FD96E91D9638E3B43737A",
    "apexforge/effects/host_execution.py":
        "AC9C7834861E83E91504F327B3102C3DB850A994B292049F2F777E32C4EE2A61",
    "apexforge/p11_14j_pure_agent_plan_effect_intent_projection_smoke_test.py":
        "DB2ABB3FB5AE72EBADD694EC77381ADB124375CE77EF0858F0CD3FC701B91698",
    "docs/p11/P11_14J_PURE_AGENT_PLAN_EFFECT_INTENT_PROJECTION.md":
        "C12D1BFDC66D21D1A7C4DE98133B15B94796A11D64A8AE3F53A42B30E0F2EA67",
    "apexforge/p11_14k_projected_effect_handoff_execution_successor_architecture_boundary_smoke_test.py":
        "934087C2C83E842708EC4E818DEEB9ABE93928F1B6EE561547C3DC36BBD657B2",
    "docs/p11/P11_14K_PROJECTED_EFFECT_HANDOFF_EXECUTION_SUCCESSOR_ARCHITECTURE_BOUNDARY.md":
        "DC072B050A149A9A01F8B3B6B258B84AF47DDAC708B78444CB1F042986394FEA",
    "apexforge/p11_14l_host_effect_execution_seam_ownership_contract_architecture_boundary_smoke_test.py":
        "064BBF6CF33F98820156FF964F0D27CDFA812B2D9B59965DED6B79B60FC52274",
    "docs/p11/P11_14L_HOST_EFFECT_EXECUTION_SEAM_OWNERSHIP_CONTRACT_ARCHITECTURE_BOUNDARY.md":
        "D84FF006D577D037CD8A3120752609F861E2441DF48F9E56C2343A087FD51FBA",
    "apexforge/p11_14m_explicit_reusable_host_effect_execution_seam_smoke_test.py":
        "3806DC386484C6C2828FE11D10C2CC1F5B1766CA2950628B5B8D232FF94F0566",
    "docs/p11/P11_14M_EXPLICIT_REUSABLE_HOST_EFFECT_EXECUTION_SEAM.md":
        "480D02AED189ED26707FFDBA3A296EDD42CB11D6B130F8AC9F3314687320B880",
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
    "apexforge/authority/validator.py":
        "1B3C2432B3B9652B3C418312469BA706484D7A837F871320ED8D481394B84AB9",
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


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14M freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14M freeze is not ancestor of P11.14N",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14N branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    agents_dir = ROOT / "apexforge" / "agents"
    require(
        not (agents_dir / "execution.py").exists(),
        "agents.execution must remain absent during N",
    )

    agents = importlib.import_module("agents")
    require(
        tuple(getattr(agents, "__all__", ())) == (),
        "agents package exports changed",
    )

    planning = (
        ROOT / "apexforge" / "agents" / "planning.py"
    ).read_text(encoding="utf-8")
    require(
        "effect_intents: Tuple[EffectIntent, ...] = ()" in planning,
        "AgentPlan effect tuple contract changed",
    )

    projection = (
        ROOT / "apexforge" / "agents" / "plan_projection.py"
    ).read_text(encoding="utf-8")
    require(
        "return plan.effect_intents" in projection,
        "J exact projection boundary changed",
    )

    host = (
        ROOT / "apexforge" / "effects" / "host_execution.py"
    ).read_text(encoding="utf-8")
    require("def execute_host_effect(" in host, "M host primitive missing")
    require("handler(intent)" in host, "M handler invocation boundary changed")

    for relative in (
        "apexforge/runtime/engine.py",
        "apexforge/runtime/state.py",
        "apexforge/workflow/air_runner.py",
        "apexforge/workflow/directive_engine.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        require(
            "execute_agent_plan" not in text,
            "{} acquired agent execution integration".format(relative),
        )
        require(
            "agents.execution" not in text,
            "{} acquired agent execution dependency".format(relative),
        )

    runtime = (
        ROOT / "apexforge" / "runtime" / "engine.py"
    ).read_text(encoding="utf-8")
    require(
        "queued host effect intent without executing it" in runtime,
        "AIR runtime host-effect non-execution invariant changed",
    )

    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in agents_dir.glob("*.py")
    )
    for forbidden in (
        "AgentExecutor",
        "AgentExecutionAdapter",
        "AgentExecutionResult",
        "AgentRuntime",
        "AgentSession",
        "AgentAction",
    ):
        require(
            forbidden not in combined,
            "deferred agent surface unexpectedly exists: {}".format(forbidden),
        )

    print("P11_14M_FREEZE_ANCESTRY=PASS")
    print("P11_14N_ARCHITECTURE_ONLY=PASS")
    print("P11_14N_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_14O_OWNER=agents.execution")
    print("P11_14O_FUNCTION=execute_agent_plan")
    print("P11_14O_INPUT=EXACT_AGENT_PLAN")
    print("P11_14O_PROJECTION=FROZEN_J_MANDATORY")
    print("P11_14O_HANDLER=ONE_CALLER_SUPPLIED_CALLABLE")
    print("P11_14O_HOST_PRIMITIVE=FROZEN_M_EXECUTE_HOST_EFFECT")
    print("P11_14O_EXECUTION_ORDER=PROJECTED_AUTHORED_ORDER")
    print("P11_14O_RETURN=ORDERED_HOST_EFFECT_EXECUTION_RECORD_TUPLE")
    print("P11_14O_EMPTY_PLAN=EXACT_EMPTY_TUPLE")
    print("P11_14O_FAILURE=PROPAGATE_UNCHANGED_STOP_LATER_INTENTS")
    print("P11_14O_RETRY=NONE")
    print("P11_14O_ROLLBACK=NONE")
    print("P11_14O_AUTHORIZATION=EXTERNAL_PRE_EXECUTION")
    print("P11_14O_RUNTIME_WORKFLOW_INTEGRATION=NONE")
    print("P11_14O_AGENT_EXECUTOR_CLASS=DEFERRED")
    print("P11_14O_AGENT_ACTION=DEFERRED")
    print("P11_14O_EFFECT_TYPE_REGISTRY_BATCH_DRYRUN_TOOLS=DEFERRED")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14N_AGENT_PLAN_HOST_EFFECT_CONSUMPTION_SUCCESSOR_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_14N_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())