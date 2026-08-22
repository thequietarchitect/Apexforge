"""P11.14D agent / narrative-character binding contract test."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "99dc17eb8225b2a07ed552293471747afc770903"
PREDECESSOR_TAG = "afp-p11-14c-freeze"
EXPECTED_BRANCH = "p11-14d-agent-narrative-character-binding"

FROZEN_HASHES = {
    "apexforge/agents/__init__.py":
        "7EA62141AC47C0DC6B2B78952CA2EE29F0E03A7FF8B929C89C1FDEEE3CC23E3D",
    "apexforge/agents/model.py":
        "C602EE903A2E45008B6BB9181F77E3DC75E7060A44B64C2B3360A7E33C59928A",
    "apexforge/agents/catalog.py":
        "8BCF6363F5D9B8D3897A410112577F2F7A2DE57CE369E45E61246983D895F8B3",
    "apexforge/agents/resolution.py":
        "FB17DEDDCB2B215C520F1D9D0A28ADA6978CE04374171C0481230BB438316000",
    "apexforge/p11_14c_immutable_professional_archetype_catalog_resolution_smoke_test.py":
        "C86C22527E944B301B9D652BBE56B1541FBC3DA08631A9AC6D2A01EE3B7FCE50",
    "docs/p11/P11_14C_IMMUTABLE_PROFESSIONAL_ARCHETYPE_CATALOG_RESOLUTION.md":
        "DBA21D379DA299E18707CD14F53527D274517BE333AB74885CB214FADABDBB79",
    "apexforge/language/narrative_model.py":
        "CEA560E3277C2340A66BF7423D46B29386589BB4CD21D3AA1DCE0FE7F648FC8D",
    "apexforge/rich_documents/projections.py":
        "743DCB144EC58F1BB0C2CE47B76F579E5E5C2B788633570441417D89CFB87C83",
    "apexforge/tam/production.py":
        "B9C8BA1E3EA1515633B2A777F425BDDB9004DCB5E6C6F5B55B9F54EF4C7F9651",
    "apexforge/runtime/narrative_binding.py":
        "E5369F1D56FC23077EDB568DE1192DA8A494DF4CE243D2F59E1245E01E645CDD",
    "apexforge/air/model.py":
        "BD3B125094933A3CD40DC44DCA4E432786D8275949B5078E9DF620D64FABEE64",
    "apexforge/role/registry.py":
        "06040B2D8A4C0443FDA000528843CB7091D22AD550FAB8F9AB6155808CFFE0F7",
    "apexforge/authorization/role_resolver.py":
        "363AC017FA7F56F8A857DFF5DF52414A50B5CFAC6AFD8102C87D8F01046BB0EC",
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


def assert_predecessor() -> None:
    resolved = git("rev-parse", "{}^{{commit}}".format(PREDECESSOR_TAG))
    require(resolved.returncode == 0, resolved.stderr.strip())
    require(resolved.stdout.strip() == BASELINE, "P11.14C freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14C freeze is not ancestor of P11.14D",
    )
    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14D branch changed")


def assert_frozen_hashes() -> None:
    for relative, expected in FROZEN_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))


def assert_binding_contract(binding_module, model_module, narrative_module) -> None:
    require(
        tuple(getattr(binding_module, "__all__", ())) == ("AgentCharacterBinding",),
        "agents.character_binding exports changed",
    )

    Binding = binding_module.AgentCharacterBinding
    AgentDefinition = model_module.AgentDefinition
    AgentIdentity = model_module.AgentIdentity
    NarrativeIdentity = narrative_module.NarrativeIdentity
    NarrativeCharacter = narrative_module.NarrativeCharacter

    require(dataclasses.is_dataclass(Binding), "binding is not a dataclass")
    params = getattr(Binding, "__dataclass_params__")
    require(params.frozen is True, "binding is mutable")
    require(params.order is False, "binding unexpectedly gained ordering")
    require(
        tuple(field.name for field in dataclasses.fields(Binding))
        == ("definition", "character"),
        "binding field shape changed",
    )

    agent_identity = AgentIdentity("agent.hero")
    definition = AgentDefinition(
        agent_identity,
        ("professional.engineer",),
    )
    character_identity = NarrativeIdentity("character", ("hero",))
    character = NarrativeCharacter(character_identity)

    require(definition.identity is agent_identity, "agent identity was not preserved")
    require(character.identity is character_identity, "character identity was not preserved")

    binding = Binding(definition, character)
    require(binding.definition is definition, "definition object identity lost")
    require(binding.character is character, "character object identity lost")
    require(binding.definition.identity is agent_identity, "nested agent identity lost")
    require(binding.character.identity is character_identity, "nested character identity lost")

    equivalent = Binding(definition, character)
    require(binding == equivalent, "binding equality changed")
    require(hash(binding) == hash(equivalent), "binding hashing changed")

    for field, value in (
        ("definition", AgentDefinition(AgentIdentity("agent.other"))),
        ("character", NarrativeCharacter(NarrativeIdentity("character", ("other",)))),
    ):
        try:
            setattr(binding, field, value)
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise AssertionError("binding became mutable")

    for bad in (None, agent_identity, True, "agent.hero", object()):
        try:
            Binding(bad, character)
        except TypeError:
            pass
        else:
            raise AssertionError("binding accepted invalid definition {!r}".format(bad))

    for bad in (None, character_identity, True, "hero", object()):
        try:
            Binding(definition, bad)
        except TypeError:
            pass
        else:
            raise AssertionError("binding accepted invalid character {!r}".format(bad))

    # Character-kind validation remains narrative-owned.
    try:
        NarrativeCharacter(NarrativeIdentity("scene", ("hero",)))
    except ValueError:
        pass
    else:
        raise AssertionError("NarrativeCharacter character-kind invariant changed")

    # Archetype resolution is explicitly orthogonal: no resolved object is required.
    unresolved_definition = AgentDefinition(
        AgentIdentity("agent.unresolved"),
        ("professional.unknown",),
    )
    unresolved_binding = Binding(
        unresolved_definition,
        NarrativeCharacter(NarrativeIdentity("character", ("unresolved",))),
    )
    require(
        unresolved_binding.definition is unresolved_definition,
        "binding unexpectedly requires archetype resolution",
    )


def assert_package_boundary() -> None:
    package = importlib.import_module("agents")
    require(tuple(getattr(package, "__all__", ())) == (), "agents.__all__ changed")
    require(
        not hasattr(package, "AgentCharacterBinding"),
        "agents prematurely exports AgentCharacterBinding",
    )


def main() -> int:
    assert_predecessor()
    assert_frozen_hashes()

    model_module = importlib.import_module("agents.model")
    narrative_module = importlib.import_module("language.narrative_model")
    binding_module = importlib.import_module("agents.character_binding")

    assert_binding_contract(binding_module, model_module, narrative_module)
    assert_package_boundary()

    print("P11_14C_FREEZE_ANCESTRY=PASS")
    print("P11_14D_PRIMARY_OWNER=agents.character_binding")
    print("AGENT_CHARACTER_BINDING_FIELDS=definition,character")
    print("AGENT_CHARACTER_BINDING_IMMUTABLE=PASS")
    print("AGENT_DEFINITION_OBJECT_IDENTITY=PRESERVED")
    print("NARRATIVE_CHARACTER_OBJECT_IDENTITY=PRESERVED")
    print("NESTED_IDENTITY_OBJECTS=PRESERVED")
    print("CHARACTER_KIND_VALIDATION_OWNER=language.narrative_model")
    print("ARCHETYPE_RESOLUTION_DEPENDENCY=NONE")
    print("BINDING_REGISTRY_RESOLVER=NONE")
    print("CROSS_RECORD_MULTIPLICITY=DEFERRED")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("RUNTIME_AIR_ROLE_AUTHORIZATION_TOOLING_CACHE_TAM_TAP_INTEGRATION=NONE")
    print("P11_14D_AGENT_NARRATIVE_CHARACTER_BINDING=PASS")
    print("P11_14D_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())