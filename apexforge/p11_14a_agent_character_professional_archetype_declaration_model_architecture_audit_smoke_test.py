"""P11.14A agent/character/professional-archetype architecture audit gate."""

from __future__ import annotations

import dataclasses
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "32a440e46dd903fe91b115f6e36ec2fca45d3026"
FREEZE_TAG = "afp-p11-13f-freeze"
EXPECTED_BRANCH = (
    "p11-14a-agent-character-professional-archetype-"
    "declaration-model-architecture-audit"
)
DOC = (
    ROOT
    / "docs"
    / "p11"
    / "P11_14A_AGENT_CHARACTER_PROFESSIONAL_ARCHETYPE_"
      "DECLARATION_MODEL_ARCHITECTURE_AUDIT.md"
)
SELF = Path(__file__).resolve()

FROZEN_HASHES = {
    "apexforge/tooling/cli.py":
        "F1A36F9FC043A6175E22830F49273D45856A4FB88F28F1C2FE2AFCDA9B74EDEC",
    "apexforge/tooling/build_artifact.py":
        "FBB3B49E85D549705AF5BD0ED0459063DCEAB4487A65E68BAF24E6DD6972B76B",
    "apexforge/rich_documents/project_build.py":
        "31C7A3A3F1737ED326C0EACF9B1CA3E2B2F4AF41D56C88C9E5B3E3B21A29AB7F",
    "apexforge/rich_documents/model.py":
        "8D9ED5088A30B10C15ACD55DF135DE03707FCABE06A808F5FAE336274DD35BC9",
    "apexforge/language/narrative_model.py":
        "CEA560E3277C2340A66BF7423D46B29386589BB4CD21D3AA1DCE0FE7F648FC8D",
    "apexforge/role/registry.py":
        "06040B2D8A4C0443FDA000528843CB7091D22AD550FAB8F9AB6155808CFFE0F7",
    "apexforge/governance/conflicts.py":
        "C0B4A6B3B936A444F57ACAC776D2C367245C84DC87620A3C0F339BD2DDB17317",
    "apexforge/tooling/project_manifest.py":
        "6937C2043DA085479FDA6DF04E4572A49351940322ECFCD8C0FA33A1744130D8",
    "apexforge/tooling/project_loader.py":
        "BFBBA1376580CE25FDB30E03187E64BF159E172859BBCE5B01520813BFD4A1B2",
    "apexforge/language/project.py":
        "84B20EBE48A47C6019C176E52E4F7B2B1D479B2BAC67E1911ED8234A16847E21",
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


def assert_predecessor() -> None:
    resolved = git("rev-parse", "{}^{{commit}}".format(FREEZE_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.13F freeze target changed")
    ancestor = git("merge-base", "--is-ancestor", FREEZE_TAG, "HEAD")
    require(ancestor.returncode == 0, "P11.13F is not an ancestor of P11.14A")

    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14A branch changed")


def assert_frozen_owners() -> None:
    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))


def assert_existing_semantic_boundaries() -> None:
    from language.narrative_model import NarrativeCharacter
    from role.registry import RoleRegistry

    require(dataclasses.is_dataclass(NarrativeCharacter), "NarrativeCharacter moved")
    require(
        getattr(NarrativeCharacter, "__dataclass_params__").frozen,
        "NarrativeCharacter became mutable",
    )
    require(
        tuple(field.name for field in dataclasses.fields(NarrativeCharacter))
        == ("identity",),
        "NarrativeCharacter frozen field shape changed",
    )

    role_source = (ROOT / "apexforge" / "role" / "registry.py").read_text(
        encoding="utf-8"
    )
    require("AIRRole" in role_source, "RoleRegistry no longer stores AIRRole")
    require("authorit" in (
        ROOT / "apexforge" / "authorization" / "role_resolver.py"
    ).read_text(encoding="utf-8").lower(), "role authority semantics moved")
    require(RoleRegistry.__module__ == "role.registry", "RoleRegistry owner moved")


def assert_agent_namespace_is_unclaimed() -> None:
    require(not (ROOT / "apexforge" / "agents").exists(), "agents package already exists")

    needles = (
        "class Agent",
        "AgentDefinition",
        "AgentPlanner",
        "AgentAction",
        "AgentRuntime",
        "ToolCall",
        "ProfessionalArchetype",
        "MultiAgent",
    )
    production = []
    for path in (ROOT / "apexforge").rglob("*.py"):
        if path == SELF or path.name.endswith("_smoke_test.py"):
            continue
        production.append(path.read_text(encoding="utf-8"))

    joined = "\n".join(production)
    for needle in needles:
        require(needle not in joined, "agent namespace collision: {}".format(needle))


def assert_audit_contract() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = (
        "Agent is a new domain",
        "NarrativeCharacter remains narrative-owned",
        "Professional archetype is not an AIR role",
        "Declaration is not permission",
        "P11.14A is non-executing",
        "No language grammar in P11.14A",
        "P11.14B should define the smallest immutable agent-domain model",
    )
    for value in required:
        require(value in text, "audit contract missing: {}".format(value))


def assert_artifact_set() -> None:
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    require(status.returncode == 0, status.stderr.strip())
    paths = tuple(
        line[3:].replace("\\", "/")
        for line in status.stdout.splitlines()
        if line.strip()
    )
    expected = {
        "apexforge/"
        "p11_14a_agent_character_professional_archetype_"
        "declaration_model_architecture_audit_smoke_test.py",
        "docs/p11/"
        "P11_14A_AGENT_CHARACTER_PROFESSIONAL_ARCHETYPE_"
        "DECLARATION_MODEL_ARCHITECTURE_AUDIT.md",
    }
    require(set(paths) == expected, "P11.14A artifact set changed: {!r}".format(paths))


def main() -> int:
    assert_predecessor()
    assert_frozen_owners()
    assert_existing_semantic_boundaries()
    assert_agent_namespace_is_unclaimed()
    assert_audit_contract()
    assert_artifact_set()

    print("P11_13F_FREEZE_ANCESTRY=PASS")
    print("P11_14A_PRIMARY_OWNER=ARCHITECTURE_AUDIT_ONLY")
    print("AGENT_DOMAIN_OWNER=NEW_SUCCESSOR_OWNER_REQUIRED")
    print("NARRATIVE_CHARACTER_OWNER=FROZEN_REFERENCE_ONLY")
    print("PROFESSIONAL_ARCHETYPE_AIR_ROLE_REUSE=REJECTED")
    print("PROFESSIONAL_ARCHETYPE_AUTHORITY_SEMANTICS=NONE")
    print("AGENT_DECLARATION_PERMISSION_GRANT=NONE")
    print("AGENT_PLANNING=DEFERRED")
    print("AGENT_ACTION_EXECUTION=DEFERRED")
    print("AGENT_TOOL_CALLS=DEFERRED")
    print("AGENT_RUNTIME_SESSION=DEFERRED")
    print("MULTI_AGENT_COORDINATION=DEFERRED")
    print("LANGUAGE_GRAMMAR_MUTATION=NONE")
    print("PROJECT_TOOLING_ARTIFACT_INTEGRATION=NONE")
    print("CACHE_TAM_TAP_INTEGRATION=NONE")
    print("FROZEN_PREDECESSOR_OWNERS=PASS")
    print("P11_14A_ARTIFACT_SET=AUDIT_TEST_AND_DOCUMENT_ONLY")
    print("P11_14A_AGENT_CHARACTER_PROFESSIONAL_ARCHETYPE_ARCHITECTURE_AUDIT=PASS")
    print("P11_14A_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())