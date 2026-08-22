"""P11.14E successor-semantics architecture-boundary smoke test."""

from __future__ import annotations

import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "12915a4082f709c0a398a1c110438451616139c3"
PREDECESSOR_TAG = "afp-p11-14d-freeze"
EXPECTED_BRANCH = "p11-14e-agent-successor-semantics-architecture-boundary"

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
    "apexforge/p11_14d_agent_narrative_character_binding_smoke_test.py":
        "2768E8722740CEFED3F84777ACE22AEBF92F463FC43988E65496C357719F86C7",
    "docs/p11/P11_14D_AGENT_NARRATIVE_CHARACTER_BINDING.md":
        "30EE520DEFB5D973E0D6E4965FE110773A8A73ABF32A0F7A8E4C967EDCED7605",
    "apexforge/language/narrative_model.py":
        "CEA560E3277C2340A66BF7423D46B29386589BB4CD21D3AA1DCE0FE7F648FC8D",
    "apexforge/rich_documents/projections.py":
        "743DCB144EC58F1BB0C2CE47B76F579E5E5C2B788633570441417D89CFB87C83",
    "apexforge/runtime/narrative_binding.py":
        "E5369F1D56FC23077EDB568DE1192DA8A494DF4CE243D2F59E1245E01E645CDD",
    "apexforge/tam/production.py":
        "B9C8BA1E3EA1515633B2A777F425BDDB9004DCB5E6C6F5B55B9F54EF4C7F9651",
    "apexforge/air/model.py":
        "BD3B125094933A3CD40DC44DCA4E432786D8275949B5078E9DF620D64FABEE64",
    "apexforge/authority/registry.py":
        "A13880538539EBE1F9E6E75634364091F267D0119CBFA836AE24E327D11D35F3",
    "apexforge/authority/validator.py":
        "1B3C2432B3B9652B3C418312469BA706484D7A837F871320ED8D481394B84AB9",
    "apexforge/role/registry.py":
        "06040B2D8A4C0443FDA000528843CB7091D22AD550FAB8F9AB6155808CFFE0F7",
    "apexforge/authorization/role_resolver.py":
        "363AC017FA7F56F8A857DFF5DF52414A50B5CFAC6AFD8102C87D8F01046BB0EC",
    "apexforge/governance/conflicts.py":
        "C0B4A6B3B936A444F57ACAC776D2C367245C84DC87620A3C0F339BD2DDB17317",
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
}

FORBIDDEN_SUCCESSOR_NAMES = (
    "AgentCapability",
    "AgentCapabilityDescriptor",
    "AgentCapabilityProfile",
    "AgentPolicy",
    "AgentPolicyDescriptor",
    "AgentPolicyProfile",
    "AgentSkill",
    "AgentCompetency",
    "AgentTrait",
    "AgentBehaviorProfile",
    "AgentConstraintProfile",
    "AgentProfessionalProfile",
    "AgentSemanticProfile",
    "AgentDeclarationProfile",
    "AgentBindingSet",
    "AgentPlan",
    "AgentPlanner",
    "AgentAction",
    "AgentExecutor",
    "AgentRuntime",
    "AgentSession",
    "AgentTool",
    "ToolCall",
    "ToolInvocation",
    "MultiAgent",
    "Delegation",
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
    require(resolved.stdout.strip() == BASELINE, "P11.14D freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14D freeze is not ancestor of P11.14E",
    )

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14E branch changed")

    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))

    agents_dir = ROOT / "apexforge" / "agents"
    actual_agent_files = {path.name for path in agents_dir.glob("*.py")}
    require(
        actual_agent_files == EXPECTED_AGENT_FILES,
        "P11.14E unexpectedly changed the production agent module set: {!r}".format(
            sorted(actual_agent_files)
        ),
    )

    package = importlib.import_module("agents")
    require(tuple(getattr(package, "__all__", ())) == (), "agents.__all__ changed")

    production_text = "\n".join(
        (agents_dir / name).read_text(encoding="utf-8")
        for name in sorted(EXPECTED_AGENT_FILES)
    )
    for name in FORBIDDEN_SUCCESSOR_NAMES:
        require(name not in production_text, "deferred successor leaked: {}".format(name))

    authority_registry = (ROOT / "apexforge" / "authority" / "registry.py").read_text(
        encoding="utf-8"
    )
    authority_validator = (ROOT / "apexforge" / "authority" / "validator.py").read_text(
        encoding="utf-8"
    )
    require(
        "resolve_capabilities" in authority_registry,
        "authority capability-resolution ownership changed",
    )
    require(
        "authorize_principal_capabilities" in authority_validator,
        "authority capability-authorization ownership changed",
    )

    print("P11_14D_FREEZE_ANCESTRY=PASS")
    print("P11_14E_ARCHITECTURE_ONLY=PASS")
    print("P11_14E_PRODUCTION_FILE_CHANGES=NONE")
    print("CAPABILITY_VOCABULARY_OWNER=AUTHORITY_AUTHORIZATION")
    print("AGENT_CAPABILITY_TYPES=DEFERRED_PROHIBITED_IN_E")
    print("AGENT_POLICY_TYPES=DEFERRED_PROHIBITED_IN_E")
    print("PROFESSIONAL_ARCHETYPE_CLASSIFICATION=SUFFICIENT_CURRENT_BOUNDARY")
    print("SKILL_COMPETENCY_TRAIT_ONTOLOGY=DEFERRED_NO_CONSUMER")
    print("BINDING_MULTIPLICITY=DEFERRED")
    print("PLANNER_ACTION_TOOL_RUNTIME_SESSION=DEFERRED")
    print("P11_14F_NEXT=FIRST_OPERATIVE_AGENT_CONTRACT_ARCHITECTURE_AUDIT")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("P11_14E_AGENT_SUCCESSOR_SEMANTICS_ARCHITECTURE_BOUNDARY=PASS")
    print("P11_14E_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())