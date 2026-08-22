"""P11.14B minimal immutable agent-domain model contract smoke test."""

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

BASELINE = "b7ac9468441749a8237517ca0dcb38acd0bbbbae"
PREDECESSOR_TAG = "afp-p11-14a-freeze"
EXPECTED_BRANCH = "p11-14b-minimal-immutable-agent-domain-model"

MODEL_FIELDS = {
    "AgentIdentity": ("canonical_id",),
    "ProfessionalArchetype": ("canonical_id",),
    "AgentDefinition": ("identity", "archetype_ids"),
}
MODEL_EXPORTS = (
    "AgentIdentity",
    "ProfessionalArchetype",
    "AgentDefinition",
)

FROZEN_REFERENCE_HASHES = {
    "apexforge/language/narrative_model.py":
        "CEA560E3277C2340A66BF7423D46B29386589BB4CD21D3AA1DCE0FE7F648FC8D",
    "apexforge/air/model.py":
        "BD3B125094933A3CD40DC44DCA4E432786D8275949B5078E9DF620D64FABEE64",
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
    "apexforge/tooling/project_manifest.py":
        "6937C2043DA085479FDA6DF04E4572A49351940322ECFCD8C0FA33A1744130D8",
    "apexforge/tooling/project_loader.py":
        "BFBBA1376580CE25FDB30E03187E64BF159E172859BBCE5B01520813BFD4A1B2",
    "apexforge/language/project.py":
        "84B20EBE48A47C6019C176E52E4F7B2B1D479B2BAC67E1911ED8234A16847E21",
    "apexforge/rich_documents/model.py":
        "8D9ED5088A30B10C15ACD55DF135DE03707FCABE06A808F5FAE336274DD35BC9",
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
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14A freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14A freeze is not ancestor of P11.14B",
    )
    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14B branch changed")


def assert_frozen_reference_owners() -> None:
    for relative, expected in FROZEN_REFERENCE_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))


def assert_model_contract(module) -> None:
    require(
        tuple(getattr(module, "__all__", ())) == MODEL_EXPORTS,
        "agents.model export surface changed",
    )

    AgentIdentity = module.AgentIdentity
    ProfessionalArchetype = module.ProfessionalArchetype
    AgentDefinition = module.AgentDefinition

    for cls in (AgentIdentity, ProfessionalArchetype, AgentDefinition):
        require(dataclasses.is_dataclass(cls), "{} is not a dataclass".format(cls.__name__))
        require(
            getattr(cls, "__dataclass_params__").frozen,
            "{} must be frozen".format(cls.__name__),
        )
        require(
            tuple(field.name for field in dataclasses.fields(cls))
            == MODEL_FIELDS[cls.__name__],
            "{} field shape changed".format(cls.__name__),
        )

    identity = AgentIdentity("agent.alpha")
    archetype = ProfessionalArchetype("professional.engineer")
    definition = AgentDefinition(
        identity=identity,
        archetype_ids=("professional.engineer", "professional.researcher"),
    )

    require(definition.identity is identity, "AgentDefinition identity object not preserved")
    require(
        definition.archetype_ids
        == ("professional.engineer", "professional.researcher"),
        "AgentDefinition archetype order changed",
    )
    require(archetype.canonical_id == "professional.engineer", "archetype ID changed")

    for cls in (AgentIdentity, ProfessionalArchetype):
        for bad in (None, True, 1, 1.0, "", " ", " x", "x "):
            try:
                cls(bad)
            except (TypeError, ValueError):
                pass
            else:
                raise AssertionError("{} accepted invalid canonical_id {!r}".format(
                    cls.__name__, bad
                ))

    for bad_identity in (None, "agent.alpha", True):
        try:
            AgentDefinition(bad_identity)
        except TypeError:
            pass
        else:
            raise AssertionError(
                "AgentDefinition accepted non-AgentIdentity {!r}".format(bad_identity)
            )

    bad_archetype_values = (
        [],
        ["professional.engineer"],
        ("",),
        (" ",),
        (" professional.engineer",),
        ("professional.engineer ",),
        (True,),
        (1,),
    )
    for bad in bad_archetype_values:
        try:
            AgentDefinition(identity, bad)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(
                "AgentDefinition accepted invalid archetype_ids {!r}".format(bad)
            )

    try:
        AgentDefinition(
            identity,
            ("professional.engineer", "professional.engineer"),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("AgentDefinition accepted duplicate archetype IDs")

    require(
        AgentDefinition(identity).archetype_ids == (),
        "AgentDefinition empty archetype tuple default changed",
    )


def assert_package_surface() -> None:
    package = importlib.import_module("agents")
    require(
        tuple(getattr(package, "__all__", ())) == (),
        "agents package must remain module-local in P11.14B",
    )
    for name in MODEL_EXPORTS:
        require(
            not hasattr(package, name),
            "agents package prematurely exports {}".format(name),
        )


def main() -> int:
    assert_predecessor()
    assert_frozen_reference_owners()

    module = importlib.import_module("agents.model")
    assert_model_contract(module)
    assert_package_surface()

    print("P11_14A_FREEZE_ANCESTRY=PASS")
    print("P11_14B_PRIMARY_OWNER=agents.model")
    print("AGENT_IDENTITY_FIELDS=canonical_id")
    print("PROFESSIONAL_ARCHETYPE_FIELDS=canonical_id")
    print("AGENT_DEFINITION_FIELDS=identity,archetype_ids")
    print("AGENT_MODEL_IMMUTABLE=PASS")
    print("ARCHETYPE_REFERENCE_MODE=IDENTITY_IDS")
    print("ARCHETYPE_ORDER=DECLARATION_ORDER_PRESERVED")
    print("DUPLICATE_ARCHETYPE_IDS=REJECTED")
    print("EMPTY_ARCHETYPE_IDS=ALLOWED")
    print("NARRATIVE_CHARACTER_BINDING=DEFERRED")
    print("AIR_ROLE_AUTHORITY_REUSE=NONE")
    print("AGENT_PLANNING_ACTION_TOOL_RUNTIME=NONE")
    print("LANGUAGE_GRAMMAR_MUTATION=NONE")
    print("PROJECT_TOOLING_ARTIFACT_INTEGRATION=NONE")
    print("CACHE_TAM_TAP_INTEGRATION=NONE")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("FROZEN_REFERENCE_OWNERS=PASS")
    print("P11_14B_MINIMAL_IMMUTABLE_AGENT_DOMAIN_MODEL=PASS")
    print("P11_14B_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())