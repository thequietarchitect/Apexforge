"""P11.14P agent operative core completion architecture boundary."""

from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "a62c1271e1567087e7eeef026f4876a11fc43742"
PREDECESSOR_TAG = "afp-p11-14o-freeze"
EXPECTED_BRANCH = "p11-14p-agent-operative-core-completion-architecture-boundary"

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
    "apexforge/agents/execution.py":
        "34572E70633600FFB417502B3D3D1B6AAE8D6704F9FE3C12B2CF4DA890818C4C",
    "apexforge/effects/__init__.py":
        "68E982EB2AEF937F57114EDAA8D36C27F8D2357A763D3EA0EE933CAFCC2A2839",
    "apexforge/effects/model.py":
        "7EECE7187CD964AAEAEC35BA633CDFFF31FFE6E6C07FD96E91D9638E3B43737A",
    "apexforge/effects/host_execution.py":
        "AC9C7834861E83E91504F327B3102C3DB850A994B292049F2F777E32C4EE2A61",
    "apexforge/p11_14n_agent_plan_host_effect_consumption_successor_architecture_boundary_smoke_test.py":
        "1E3FCA202E8DE26474BCEFE34AFC55FBDFAFFE6B261B34F43E4B470AE3D16159",
    "docs/p11/P11_14N_AGENT_PLAN_HOST_EFFECT_CONSUMPTION_SUCCESSOR_ARCHITECTURE_BOUNDARY.md":
        "1C2AF57FDF1288A43C7F190A3ECBFF5EE922056D196C9451CA074AEC0B35FE69",
    "apexforge/p11_14o_agent_plan_host_effect_execution_composition_smoke_test.py":
        "F586C3DE8B017CFE249D1CF70EA0CF3D3EA26E9FA180661638F7876C6E867DA3",
    "docs/p11/P11_14O_AGENT_PLAN_HOST_EFFECT_EXECUTION_COMPOSITION.md":
        "1DE15AA947311DB5C9D8CCECE1E23D5299AAB8726CDA13B98016C9D547F1DA7A",
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


def production_python_files() -> tuple[str, ...]:
    agents = ROOT / "apexforge" / "agents"
    return tuple(
        sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in agents.glob("*.py")
        )
    )


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14O freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14O freeze is not ancestor of P11.14P",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14P branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    agents = importlib.import_module("agents")
    require(
        tuple(getattr(agents, "__all__", ())) == (),
        "agents package exports changed",
    )

    execution = importlib.import_module("agents.execution")
    require(
        tuple(getattr(execution, "__all__", ())) == ("execute_agent_plan",),
        "O execution export changed",
    )

    agent_files = production_python_files()
    require(
        "apexforge/agents/execution.py" in agent_files,
        "frozen O execution production file missing",
    )

    combined_agents = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8", errors="replace")
        for relative in agent_files
    )

    for forbidden in (
        "AgentContext",
        "AgentInvocation",
        "AgentExecutionContext",
        "AgentExecutionRecord",
        "AgentExecutionEvidence",
        "AgentExecutionResult",
        "AgentExecutor",
        "AgentRuntime",
        "AgentSession",
        "AgentAction",
        "AgentTool",
        "AgentProvider",
        "AgentCapability",
    ):
        require(
            forbidden not in combined_agents,
            "deferred agent surface unexpectedly exists: {}".format(forbidden),
        )

    for relative in (
        "apexforge/runtime/engine.py",
        "apexforge/runtime/state.py",
        "apexforge/workflow/air_runner.py",
        "apexforge/workflow/directive_engine.py",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        require(
            "execute_agent_plan" not in text,
            "{} acquired automatic agent execution integration".format(relative),
        )
        require(
            "agents.execution" not in text,
            "{} acquired agents.execution dependency".format(relative),
        )
        require(
            "execute_host_effect" not in text,
            "{} acquired automatic host execution integration".format(relative),
        )

    runtime = (
        ROOT / "apexforge" / "runtime" / "engine.py"
    ).read_text(encoding="utf-8")
    require(
        "queued host effect intent without executing it" in runtime,
        "AIR runtime host-effect non-execution invariant changed",
    )

    authority_and_agents = "\n".join(
        (
            ROOT / "apexforge" / "agents" / name
        ).read_text(encoding="utf-8", errors="replace")
        for name in (
            "__init__.py",
            "model.py",
            "catalog.py",
            "resolution.py",
            "character_binding.py",
            "planning.py",
            "plan_projection.py",
            "execution.py",
        )
    )
    for forbidden in (
        "AIRPrincipal",
        "AuthorityCheck",
        "AuthorityGrant",
        "authorize_principal",
        "authorize_principal_capabilities",
        "principal_id",
        "agent_id",
    ):
        require(
            forbidden not in authority_and_agents,
            "authorization bridge leaked into agents: {}".format(forbidden),
        )

    execution_source = (
        ROOT / "apexforge" / "agents" / "execution.py"
    ).read_text(encoding="utf-8")
    require(
        "project_agent_plan_effect_intents(plan)" in execution_source,
        "O no longer composes through frozen J",
    )
    require(
        "execute_host_effect(effect_intent, handler)" in execution_source,
        "O no longer composes through frozen M",
    )

    host_source = (
        ROOT / "apexforge" / "effects" / "host_execution.py"
    ).read_text(encoding="utf-8")
    require(
        "class HostEffectExecutionRecord" in host_source,
        "frozen M execution record missing",
    )
    require(
        "intent: EffectIntent" in host_source,
        "M execution record contract changed",
    )

    print("P11_14O_FREEZE_ANCESTRY=PASS")
    print("P11_14P_ARCHITECTURE_ONLY=PASS")
    print("P11_14P_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_14P_SUCCESSOR_PRODUCTION_STAGE=NONE")
    print("P11_14Q_PRODUCTION_CONTRACT=NOT_JUSTIFIED")
    print("P11_14_TERMINAL_PRODUCTION_STAGE=P11.14O")
    print("P11_14_OPERATIVE_CORE=COMPLETE")
    print("AGENT_EXECUTION_ATTRIBUTION_WRAPPER=DEFERRED_UNTIL_CONSUMER")
    print("AGENT_CHARACTER_EXECUTION_CONTEXT=NOT_REQUIRED")
    print("AGENT_ARCHETYPE_EXECUTION_CONTEXT=NOT_REQUIRED")
    print("AGENT_IDENTITY_PRINCIPAL_BRIDGE=DEFERRED")
    print("AUTHORIZATION=EXTERNAL_PRE_EXECUTION")
    print("RUNTIME_WORKFLOW_AUTOMATIC_EXECUTION=FORBIDDEN")
    print("AGENT_ACTION=DEFERRED")
    print("AGENT_EXECUTOR_RUNTIME_SESSION_TOOLS_PROVIDERS=DEFERRED")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14P_AGENT_OPERATIVE_CORE_COMPLETION_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_14P_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())