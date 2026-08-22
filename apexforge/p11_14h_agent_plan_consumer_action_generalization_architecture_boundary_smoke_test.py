"""P11.14H agent-plan consumer/action-generalization architecture boundary."""

from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "5bb5dad8886c0896a06332d2055f2bb58309e31d"
PREDECESSOR_TAG = "afp-p11-14g-freeze"
EXPECTED_BRANCH = "p11-14h-agent-plan-consumer-action-generalization-architecture-boundary"

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
    "apexforge/p11_14g_minimal_immutable_agent_plan_effect_intents_smoke_test.py":
        "568359CC05A1CA745D0FA83EA280317905462787930F5AD027021A0EAB429D7A",
    "docs/p11/P11_14G_MINIMAL_IMMUTABLE_AGENT_PLAN_EFFECT_INTENTS.md":
        "A54DF5B8115AF3585A00AC591A16A42ADE4445878234538F83AE5A8083817DF2",
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

EXPECTED_AGENT_FILES = {
    "__init__.py",
    "model.py",
    "catalog.py",
    "resolution.py",
    "character_binding.py",
    "planning.py",
}

FORBIDDEN_SUCCESSOR_NAMES = (
    "AgentAction",
    "AgentToolRequest",
    "AgentToolCall",
    "AgentToolInvocation",
    "AgentDirectiveRequest",
    "AgentMessage",
    "AgentObservation",
    "AgentDecision",
    "AgentStateChange",
    "AgentEvent",
    "AgentInvocation",
    "AgentOperation",
    "AgentWorkItem",
    "AgentPlanResult",
    "AgentPlanReceipt",
    "AgentExecutionResult",
    "AgentExecutionReceipt",
    "AgentExecutor",
    "AgentRuntime",
    "AgentSession",
)


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
    require(resolved.stdout.strip() == BASELINE, "P11.14G freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14G freeze is not ancestor of P11.14H",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14H branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    agents_dir = ROOT / "apexforge" / "agents"
    actual_agent_files = {path.name for path in agents_dir.glob("*.py")}
    require(
        actual_agent_files == EXPECTED_AGENT_FILES,
        "P11.14H unexpectedly changed production agent module set: {!r}".format(
            sorted(actual_agent_files)
        ),
    )

    package = importlib.import_module("agents")
    require(tuple(getattr(package, "__all__", ())) == (), "agents.__all__ changed")

    planning = importlib.import_module("agents.planning")
    require(
        tuple(getattr(planning, "__all__", ())) == ("AgentPlan",),
        "agents.planning exports changed",
    )
    require(hasattr(planning, "AgentPlan"), "AgentPlan disappeared")

    production_text = "\n".join(
        (agents_dir / name).read_text(encoding="utf-8")
        for name in sorted(EXPECTED_AGENT_FILES)
    )
    for name in FORBIDDEN_SUCCESSOR_NAMES:
        require(
            name not in production_text,
            "premature successor type leaked: {}".format(name),
        )

    effects_model = importlib.import_module("effects.model")
    require(hasattr(effects_model, "EffectIntent"), "EffectIntent ownership changed")

    authority_model = importlib.import_module("authority.model")
    require(hasattr(authority_model, "AuthorityCheck"), "AuthorityCheck ownership changed")
    require(hasattr(authority_model, "AuthorityGrant"), "AuthorityGrant ownership changed")

    authority_validator_text = (
        ROOT / "apexforge" / "authority" / "validator.py"
    ).read_text(encoding="utf-8")
    require(
        "authorize_principal_capabilities" in authority_validator_text,
        "authority capability-authorization ownership changed",
    )

    runtime_engine_text = (
        ROOT / "apexforge" / "runtime" / "engine.py"
    ).read_text(encoding="utf-8")
    require(
        "RuntimeEngine.execute requires VerifiedAIRProgram" in runtime_engine_text,
        "runtime execution boundary changed",
    )

    print("P11_14G_FREEZE_ANCESTRY=PASS")
    print("P11_14H_ARCHITECTURE_ONLY=PASS")
    print("P11_14H_PRODUCTION_FILE_CHANGES=NONE")
    print("AGENT_PLAN_CONSUMER=ABSENT")
    print("SECOND_AGENT_OPERATION_KIND=ABSENT")
    print("AGENT_ACTION=DEFERRED")
    print("AGENT_PLAN=BYTE_API_FROZEN")
    print("FUTURE_PLAN_CONSUMER_IDENTITY=EXACT_AGENT_PLAN")
    print("AUTHORIZATION=DOWNSTREAM_EXTERNAL")
    print("HOST_EFFECT_EXECUTION=OUTSIDE_AGENTS")
    print("TOOL_REQUEST=DEFERRED")
    print("RESULT_RECEIPT_TRACE=DEFERRED")
    print("P11_14I_NEXT=PLAN_CONSUMPTION_EXECUTION_ADAPTER_ARCHITECTURE_AUDIT")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14H_AGENT_PLAN_CONSUMER_ACTION_GENERALIZATION_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_14H_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())