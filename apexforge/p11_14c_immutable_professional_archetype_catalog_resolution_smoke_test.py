"""P11.14C immutable archetype catalog and resolution contract test."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apexforge"))

BASELINE = "eae088afaece010acf5a43957ae7131053c77f30"
PREDECESSOR_TAG = "afp-p11-14b-freeze"
EXPECTED_BRANCH = "p11-14c-immutable-professional-archetype-catalog-resolution"

FROZEN_P11_14B_HASHES = {
    "apexforge/agents/__init__.py":
        "7EA62141AC47C0DC6B2B78952CA2EE29F0E03A7FF8B929C89C1FDEEE3CC23E3D",
    "apexforge/agents/model.py":
        "C602EE903A2E45008B6BB9181F77E3DC75E7060A44B64C2B3360A7E33C59928A",
    "apexforge/p11_14b_minimal_immutable_agent_domain_model_smoke_test.py":
        "D2529EF742E5962FC5E6738087708385BD095AC59B1B6A07722B241343073D7F",
    "docs/p11/P11_14B_MINIMAL_IMMUTABLE_AGENT_DOMAIN_MODEL.md":
        "FC22057EC7A9C5167712A4586D2E60FC5E0D4AC056C96A24B573349DED517014",
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
    require(resolved.stdout.strip() == BASELINE, "P11.14B freeze target changed")
    require(
        git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.14B freeze is not ancestor of P11.14C",
    )
    branch = git("branch", "--show-current")
    require(branch.returncode == 0, branch.stderr.strip())
    require(branch.stdout.strip() == EXPECTED_BRANCH, "P11.14C branch changed")


def assert_frozen_p11_14b() -> None:
    for relative, expected in FROZEN_P11_14B_HASHES.items():
        require(sha256(relative) == expected, "{} changed".format(relative))


def assert_catalog_contract(catalog_module, model_module) -> None:
    require(
        tuple(getattr(catalog_module, "__all__", ()))
        == ("ProfessionalArchetypeCatalog",),
        "agents.catalog exports changed",
    )
    Catalog = catalog_module.ProfessionalArchetypeCatalog
    Archetype = model_module.ProfessionalArchetype

    require(dataclasses.is_dataclass(Catalog), "catalog is not a dataclass")
    require(getattr(Catalog, "__dataclass_params__").frozen, "catalog is mutable")
    require(
        tuple(field.name for field in dataclasses.fields(Catalog))
        == ("archetypes",),
        "catalog field shape changed",
    )

    engineer = Archetype("professional.engineer")
    researcher = Archetype("professional.researcher")
    authored = (engineer, researcher)
    catalog = Catalog(authored)

    require(catalog.archetypes is authored, "catalog rewrote authored tuple")
    require(catalog.resolve("professional.engineer") is engineer, "catalog identity lost")
    require(catalog.resolve("professional.researcher") is researcher, "catalog order lost")
    require(Catalog().archetypes == (), "empty catalog changed")

    for bad in (None, [], [engineer], "professional.engineer"):
        try:
            Catalog(bad)
        except TypeError:
            pass
        else:
            raise AssertionError("catalog accepted invalid archetypes {!r}".format(bad))

    for bad in ((None,), (engineer, object())):
        try:
            Catalog(bad)
        except TypeError:
            pass
        else:
            raise AssertionError("catalog accepted invalid item tuple {!r}".format(bad))

    try:
        Catalog((engineer, Archetype("professional.engineer")))
    except ValueError:
        pass
    else:
        raise AssertionError("catalog accepted duplicate canonical IDs")

    for bad in (None, True, 1, "", " ", " professional.engineer", "professional.engineer "):
        try:
            catalog.resolve(bad)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("catalog.resolve accepted invalid ID {!r}".format(bad))

    try:
        catalog.resolve("professional.unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown archetype did not fail explicitly")


def assert_resolution_contract(resolution_module, catalog_module, model_module) -> None:
    expected_exports = (
        "AgentArchetypeResolution",
        "resolve_agent_archetypes",
    )
    require(
        tuple(getattr(resolution_module, "__all__", ())) == expected_exports,
        "agents.resolution exports changed",
    )

    Resolution = resolution_module.AgentArchetypeResolution
    resolve = resolution_module.resolve_agent_archetypes
    Catalog = catalog_module.ProfessionalArchetypeCatalog
    AgentIdentity = model_module.AgentIdentity
    Archetype = model_module.ProfessionalArchetype
    AgentDefinition = model_module.AgentDefinition

    require(dataclasses.is_dataclass(Resolution), "resolution is not a dataclass")
    require(
        getattr(Resolution, "__dataclass_params__").frozen,
        "resolution is mutable",
    )
    require(
        tuple(field.name for field in dataclasses.fields(Resolution))
        == ("definition", "archetypes"),
        "resolution field shape changed",
    )

    engineer = Archetype("professional.engineer")
    researcher = Archetype("professional.researcher")
    catalog = Catalog((engineer, researcher))
    definition = AgentDefinition(
        AgentIdentity("agent.alpha"),
        ("professional.researcher", "professional.engineer"),
    )
    result = resolve(definition, catalog)

    require(result.definition is definition, "definition identity not preserved")
    require(
        result.archetypes == (researcher, engineer),
        "resolution order changed",
    )
    require(result.archetypes[0] is researcher, "canonical object identity lost")
    require(result.archetypes[1] is engineer, "canonical object identity lost")

    empty_definition = AgentDefinition(AgentIdentity("agent.empty"))
    empty_result = resolve(empty_definition, catalog)
    require(empty_result.definition is empty_definition, "empty definition identity lost")
    require(empty_result.archetypes == (), "empty archetypes did not resolve empty")

    for bad_definition in (None, "agent.alpha", True):
        try:
            resolve(bad_definition, catalog)
        except TypeError:
            pass
        else:
            raise AssertionError("resolver accepted invalid definition")

    for bad_catalog in (None, (), True):
        try:
            resolve(definition, bad_catalog)
        except TypeError:
            pass
        else:
            raise AssertionError("resolver accepted invalid catalog")

    missing = AgentDefinition(
        AgentIdentity("agent.missing"),
        ("professional.unknown",),
    )
    try:
        resolve(missing, catalog)
    except ValueError:
        pass
    else:
        raise AssertionError("resolver silently accepted unknown archetype")

    try:
        Resolution(definition, (engineer, researcher))
    except ValueError:
        pass
    else:
        raise AssertionError("resolution accepted archetypes in wrong ID order")

    try:
        Resolution(definition, (researcher,))
    except ValueError:
        pass
    else:
        raise AssertionError("resolution accepted wrong archetype count")

    try:
        Resolution(definition, [researcher, engineer])
    except TypeError:
        pass
    else:
        raise AssertionError("resolution accepted non-tuple archetypes")


def assert_package_boundary() -> None:
    package = importlib.import_module("agents")
    require(tuple(getattr(package, "__all__", ())) == (), "agents.__all__ changed")
    for name in (
        "ProfessionalArchetypeCatalog",
        "AgentArchetypeResolution",
        "resolve_agent_archetypes",
    ):
        require(not hasattr(package, name), "agents prematurely exports {}".format(name))


def main() -> int:
    assert_predecessor()
    assert_frozen_p11_14b()

    model_module = importlib.import_module("agents.model")
    catalog_module = importlib.import_module("agents.catalog")
    resolution_module = importlib.import_module("agents.resolution")

    assert_catalog_contract(catalog_module, model_module)
    assert_resolution_contract(resolution_module, catalog_module, model_module)
    assert_package_boundary()

    print("P11_14B_FREEZE_ANCESTRY=PASS")
    print("P11_14C_PRIMARY_OWNER=agents.catalog")
    print("P11_14C_SECONDARY_OWNER=agents.resolution")
    print("CATALOG_FIELDS=archetypes")
    print("CATALOG_IMMUTABLE=PASS")
    print("CATALOG_ORDER=AUTHORED_ORDER_PRESERVED")
    print("CATALOG_OBJECT_IDENTITY=PRESERVED")
    print("DUPLICATE_ARCHETYPE_CANONICAL_IDS=REJECTED")
    print("UNKNOWN_ARCHETYPE_RESOLUTION=EXPLICIT_VALUE_ERROR")
    print("RESOLUTION_FIELDS=definition,archetypes")
    print("AGENT_DEFINITION_BYTE_API_FROZEN=PASS")
    print("RESOLUTION_AGENT_ID_ORDER=PRESERVED")
    print("RESOLUTION_CANONICAL_OBJECT_IDENTITY=PRESERVED")
    print("EMPTY_AGENT_ARCHETYPE_RESOLUTION=EMPTY")
    print("CHARACTER_BINDING=DEFERRED_P11_14D")
    print("AGENTS_PACKAGE_TOP_LEVEL_EXPORTS=UNCHANGED_EMPTY")
    print("AIR_AUTHORIZATION_RUNTIME_TOOLING_CACHE_TAM_TAP_INTEGRATION=NONE")
    print("P11_14C_IMMUTABLE_ARCHETYPE_CATALOG_RESOLUTION=PASS")
    print("P11_14C_EXIT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())