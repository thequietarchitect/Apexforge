"""P11.14L host-effect execution ownership/contract architecture boundary."""

from __future__ import annotations

import ast
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "1de4ef6e763d016983969ec9160005d89b53b8d4"
PREDECESSOR_TAG = "afp-p11-14k-freeze"
EXPECTED_BRANCH = (
    "p11-14l-host-effect-execution-seam-ownership-contract-architecture-boundary"
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
    "apexforge/p11_14j_pure_agent_plan_effect_intent_projection_smoke_test.py":
        "DB2ABB3FB5AE72EBADD694EC77381ADB124375CE77EF0858F0CD3FC701B91698",
    "docs/p11/P11_14J_PURE_AGENT_PLAN_EFFECT_INTENT_PROJECTION.md":
        "C12D1BFDC66D21D1A7C4DE98133B15B94796A11D64A8AE3F53A42B30E0F2EA67",
    "apexforge/p11_14k_projected_effect_handoff_execution_successor_architecture_boundary_smoke_test.py":
        "934087C2C83E842708EC4E818DEEB9ABE93928F1B6EE561547C3DC36BBD657B2",
    "docs/p11/P11_14K_PROJECTED_EFFECT_HANDOFF_EXECUTION_SUCCESSOR_ARCHITECTURE_BOUNDARY.md":
        "DC072B050A149A9A01F8B3B6B258B84AF47DDAC708B78444CB1F042986394FEA",
    "apexforge/effects/__init__.py":
        "68E982EB2AEF937F57114EDAA8D36C27F8D2357A763D3EA0EE933CAFCC2A2839",
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


def production_python_files():
    for path in (ROOT / "apexforge").rglob("*.py"):
        if path.parent == ROOT / "apexforge" and path.name.startswith("p11_"):
            continue
        yield path


def main() -> int:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14K freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14K freeze is not ancestor of P11.14L",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14L branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    effects_dir = ROOT / "apexforge" / "effects"
    require(
        {path.name for path in effects_dir.glob("*.py")}
        == {"__init__.py", "model.py"},
        "P11.14L must not create an effects execution module",
    )
    require(
        not (effects_dir / "host_execution.py").exists(),
        "effects.host_execution must remain absent during L",
    )

    effects = importlib.import_module("effects")
    require(
        tuple(getattr(effects, "__all__", ())) == ("EffectIntent",),
        "effects package exports changed",
    )

    model_text = (
        ROOT / "apexforge" / "effects" / "model.py"
    ).read_text(encoding="utf-8")
    require(
        "must never execute host effects" in model_text,
        "EffectIntent passive/AIR-runtime boundary changed",
    )

    runtime_text = (
        ROOT / "apexforge" / "runtime" / "engine.py"
    ).read_text(encoding="utf-8")
    require(
        "queued host effect intent without executing it" in runtime_text,
        "runtime queued-host-effect boundary changed",
    )

    for forbidden_import in (
        "effects.host_execution",
        "from effects import execute_host_effect",
        "from effects.host_execution import",
    ):
        require(
            forbidden_import not in runtime_text,
            "AIR runtime acquired host-execution dependency",
        )

    executor_names = {
        "execute_effect",
        "execute_effects",
        "apply_effect",
        "apply_effects",
        "dispatch_effect",
        "dispatch_effects",
        "handle_effect",
        "handle_effects",
        "execute_host_effect",
        "execute_host_effects",
    }
    discovered = []
    for path in production_python_files():
        tree = ast.parse(
            path.read_text(encoding="utf-8", errors="replace"),
            filename=str(path),
        )
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in executor_names
            ):
                discovered.append(
                    "{}:{}".format(path.relative_to(ROOT), node.name)
                )
    require(
        not discovered,
        "host-effect executor unexpectedly exists before M: {!r}".format(
            discovered
        ),
    )

    dispatch_comparisons = []
    for path in production_python_files():
        tree = ast.parse(
            path.read_text(encoding="utf-8", errors="replace"),
            filename=str(path),
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            candidates = [node.left] + list(node.comparators)
            if any(
                isinstance(candidate, ast.Attribute)
                and candidate.attr == "effect_type"
                for candidate in candidates
            ):
                dispatch_comparisons.append(
                    "{}:{}".format(path.relative_to(ROOT), node.lineno)
                )
    require(
        not dispatch_comparisons,
        "effect_type dispatch taxonomy unexpectedly exists: {!r}".format(
            dispatch_comparisons
        ),
    )

    agents_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "apexforge" / "agents").glob("*.py")
    )
    for forbidden in (
        "HostEffectExecutionRecord",
        "execute_host_effect",
        "AgentExecutor",
        "AgentRuntime",
        "AgentSession",
        "AgentAction",
    ):
        require(
            forbidden not in agents_text,
            "agent domain acquired host execution surface: {}".format(forbidden),
        )

    validator_text = (
        ROOT / "apexforge" / "authority" / "validator.py"
    ).read_text(encoding="utf-8")
    require(
        "def authorize_principal_capabilities(" in validator_text,
        "authorization ownership changed",
    )

    state_text = (
        ROOT / "apexforge" / "runtime" / "state.py"
    ).read_text(encoding="utf-8")
    require("class StateDelta" in state_text, "StateDelta ownership changed")
    require(
        "effects: Tuple[EffectIntent, ...] = ()" in state_text,
        "StateDelta effects contract changed",
    )

    print("P11_14K_FREEZE_ANCESTRY=PASS")
    print("P11_14L_ARCHITECTURE_ONLY=PASS")
    print("P11_14L_PRODUCTION_FILE_CHANGES=NONE")
    print("P11_14M_OWNER=effects.host_execution")
    print("P11_14M_PRIMITIVE_INPUT=ONE_EXACT_EFFECT_INTENT")
    print("P11_14M_HANDLER=CALLER_SUPPLIED_CALLABLE")
    print("P11_14M_RECORD=HostEffectExecutionRecord")
    print("P11_14M_FUNCTION=execute_host_effect")
    print("HANDLER_RECEIVES_EXACT_INTENT_IDENTITY=REQUIRED")
    print("EXECUTION_RECORD_PRESERVES_EXACT_INTENT_IDENTITY=REQUIRED")
    print("HANDLER_EXCEPTION=PROPAGATE_UNCHANGED")
    print("HANDLER_RETRY=NONE")
    print("EFFECT_TYPE_REGISTRY_DISPATCH=DEFERRED")
    print("BATCH_EXECUTION=DEFERRED")
    print("DRY_RUN_PREVIEW=DEFERRED")
    print("AUTHORIZATION=EXTERNAL_PRE_EXECUTION")
    print("AIR_RUNTIME_HOST_EFFECT_EXECUTION=FORBIDDEN")
    print("STATE_DELTA=RUNTIME_OWNED_UNTOUCHED")
    print("TOOLS_PROVIDERS_CONCRETE_HANDLERS=DEFERRED")
    print("EFFECTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED")
    print("P11_14L_HOST_EFFECT_EXECUTION_SEAM_OWNERSHIP_CONTRACT_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_14L_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())