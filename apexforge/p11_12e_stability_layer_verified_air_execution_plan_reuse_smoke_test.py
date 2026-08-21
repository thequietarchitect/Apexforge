"""P11.12E Stability-layer verified-AIR/execution-plan reuse smoke test."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
import subprocess
from typing import Tuple

from aether_air.construction import AetherAirSnapshot
from air.model import AIRProgram, VerifiedAIRProgram
import incremental_cache
import incremental_cache.stability as stability_module
from incremental_cache import CacheEntry, cache_fingerprint
from incremental_cache.resonance import (
    resonance_fingerprint,
    resonance_input_fingerprint,
    reuse_or_produce_resonance,
)
from incremental_cache.stability import (
    reuse_or_produce_stability,
    stability_dependencies_fingerprint,
    stability_dependency,
    stability_fingerprint,
    stability_identity,
    stability_input_fingerprint,
)
from language.compiler import SourceMap
from language.modules import ModuleGraph, ProjectDocumentGraph
from language.project import ProjectBuild, build_project
from language.validation.runtime_validator import RuntimeValidator
from runtime.narrative_execution import NarrativeExecutionState
from tooling.build_artifact import CanonicalBuildArtifact
from tooling.project_loader import load_project
from workflow.air_runner import (
    RegistryExecutionPlan,
    build_registry_execution_plan,
)
from workflow.registry import DirectiveRegistry


PREDECESSOR_TAG = "afp-p11-12d-freeze"
PREDECESSOR_COMMIT = "d961e7b02f029c2df8fdba44d4db0387b567b9b5"

D_HASHES = {
    "apexforge/incremental_cache/resonance.py":
        "2982DE185AB6579AC8ED441111DDC2F84D4754508AEEADA91F8E915518510C2A",
    "apexforge/p11_12d_resonance_layer_owner_reuse_smoke_test.py":
        "20369D1B085C2B9A0AAD0A76CEE7FB3784732C49E807898A2B005BE95D6D39C8",
    "docs/p11/P11_12D_RESONANCE_LAYER_OWNER_REUSE.md":
        "E00310B7635B283BC45106819F15678E9E92C0708EA9B757937182FBE7036F42",
}

EXPECTED_PUBLIC = (
    "stability_input_fingerprint",
    "stability_fingerprint",
    "stability_dependency",
    "stability_dependencies_fingerprint",
    "stability_identity",
    "reuse_or_produce_stability",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ("git", *arguments),
        cwd=_root(),
        check=False,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12D freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.12D freeze is not ancestor of P11.12E",
    )
    for relative, expected in D_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12D hash changed".format(relative),
        )


def _assert_surface_and_taxonomy() -> None:
    _require(
        stability_module.__all__ == EXPECTED_PUBLIC,
        "Stability public surface changed",
    )
    _require(
        incremental_cache.__all__
        == (
            "CACHE_SCHEMA_VERSION",
            "CACHE_LAYER_IDS",
            "CACHE_FINGERPRINT_ALGORITHM",
            "CacheFingerprint",
            "CacheDependency",
            "CacheIdentity",
            "CacheEntry",
            "cache_fingerprint",
            "cache_identity_key",
        ),
        "P11.12E changed P11.12B top-level cache surface",
    )

    input_fp = cache_fingerprint(b"x")
    config_fp = cache_fingerprint(b"")

    for excluded in (
        AIRProgram,
        ProjectBuild,
        NarrativeExecutionState,
        CanonicalBuildArtifact,
        AetherAirSnapshot,
    ):
        try:
            stability_identity(
                excluded,
                subject="excluded",
                input_fingerprint=input_fp,
                configuration_fingerprint=config_fp,
            )
        except TypeError:
            pass
        else:
            raise AssertionError(
                "{} crossed into Stability".format(excluded.__name__)
            )

    for allowed in (
        VerifiedAIRProgram,
        RegistryExecutionPlan,
    ):
        identity = stability_identity(
            allowed,
            subject="allowed",
            input_fingerprint=input_fp,
            configuration_fingerprint=config_fp,
        )
        _require(
            identity.layer_id == "stability",
            "allowed Stability type received wrong layer",
        )


def _contract_fingerprint(owner: object) -> object:
    return stability_input_fingerprint(
        {
            "module": owner.__module__,
            "qualname": owner.__qualname__,
            "signature": str(inspect.signature(owner)),
            "source": inspect.getsource(owner),
        }
    )


def _assert_verified_air_reuse(
    build: ProjectBuild,
    dependencies,
) -> CacheEntry:
    program_fp = stability_input_fingerprint(build.program)
    validator_contract = _contract_fingerprint(RuntimeValidator.validate)

    calls = []

    def validate_owner():
        calls.append(True)
        return RuntimeValidator().validate(build.program)

    entry = reuse_or_produce_stability(
        VerifiedAIRProgram,
        subject="project:verified-air",
        input_fingerprint=program_fp,
        configuration_fingerprint=validator_contract,
        dependencies=dependencies,
        producer=validate_owner,
    )

    _require(calls == [True], "verified AIR producer did not run on miss")
    _require(
        type(entry.value) is VerifiedAIRProgram,
        "verified AIR entry has wrong value type",
    )
    _require(
        entry.value == build.verified,
        "cached verified AIR differs from ProjectBuilder result",
    )
    _require(
        entry.artifact_fingerprint == stability_fingerprint(entry.value),
        "verified AIR artifact fingerprint changed",
    )

    calls.clear()

    def forbidden_validator():
        calls.append(True)
        raise AssertionError("validator invoked during exact Stability hit")

    reused = reuse_or_produce_stability(
        VerifiedAIRProgram,
        subject="project:verified-air",
        input_fingerprint=program_fp,
        configuration_fingerprint=validator_contract,
        dependencies=dependencies,
        producer=forbidden_validator,
        cached=entry,
    )
    _require(reused is entry, "verified AIR exact hit was not reused")
    _require(not calls, "validator ran on verified AIR hit")

    changed_program_fp = stability_input_fingerprint(
        ("changed-program-contract", build.program)
    )
    miss = reuse_or_produce_stability(
        VerifiedAIRProgram,
        subject="project:verified-air",
        input_fingerprint=changed_program_fp,
        configuration_fingerprint=validator_contract,
        dependencies=dependencies,
        producer=validate_owner,
        cached=entry,
    )
    _require(miss is not entry, "changed verified input incorrectly reused")

    corrupt = CacheEntry(
        identity=entry.identity,
        artifact_fingerprint=cache_fingerprint(b"corrupt"),
        value=entry.value,
    )
    calls.clear()
    repaired = reuse_or_produce_stability(
        VerifiedAIRProgram,
        subject="project:verified-air",
        input_fingerprint=program_fp,
        configuration_fingerprint=validator_contract,
        dependencies=dependencies,
        producer=validate_owner,
        cached=corrupt,
    )
    _require(repaired is not corrupt, "corrupt verified AIR was reused")
    _require(calls == [True], "corrupt verified AIR did not re-run validator")

    return entry


def _registry_snapshot(
    registry: DirectiveRegistry,
) -> Tuple[tuple[str, object], ...]:
    return tuple(
        (name, registry.resolve(name))
        for name in registry.names()
    )


def _assert_execution_plan_reuse(
    build: ProjectBuild,
    root_name: str,
    dependencies,
) -> CacheEntry:
    registry = DirectiveRegistry()
    registry.register(root_name, build.program)

    registry_input = stability_input_fingerprint(
        {
            "root": root_name,
            "programs": _registry_snapshot(registry),
        }
    )
    plan_contract = _contract_fingerprint(build_registry_execution_plan)

    import workflow.air_runner as air_runner

    original_runtime = air_runner.RuntimeEngine

    class ForbiddenRuntimeEngine:
        def __init__(self, *args, **kwargs):
            raise AssertionError(
                "RuntimeEngine constructed during execution-plan production"
            )

    air_runner.RuntimeEngine = ForbiddenRuntimeEngine
    calls = []

    def plan_owner():
        calls.append(True)
        return build_registry_execution_plan(registry, root_name)

    try:
        entry = reuse_or_produce_stability(
            RegistryExecutionPlan,
            subject=root_name,
            input_fingerprint=registry_input,
            configuration_fingerprint=plan_contract,
            dependencies=dependencies,
            producer=plan_owner,
        )
    finally:
        air_runner.RuntimeEngine = original_runtime

    _require(calls == [True], "execution-plan producer did not run on miss")
    _require(
        type(entry.value) is RegistryExecutionPlan,
        "execution-plan entry has wrong value type",
    )
    _require(
        entry.value.entry_directive == build.entry_directive,
        "execution-plan entry directive differs from ProjectBuild entry",
    )
    _require(
        entry.artifact_fingerprint == stability_fingerprint(entry.value),
        "execution-plan artifact fingerprint changed",
    )

    calls.clear()

    def forbidden_plan():
        calls.append(True)
        raise AssertionError(
            "execution-plan owner invoked during exact Stability hit"
        )

    reused = reuse_or_produce_stability(
        RegistryExecutionPlan,
        subject=root_name,
        input_fingerprint=registry_input,
        configuration_fingerprint=plan_contract,
        dependencies=dependencies,
        producer=forbidden_plan,
        cached=entry,
    )
    _require(reused is entry, "execution-plan exact hit was not reused")
    _require(not calls, "execution-plan owner ran on exact hit")

    changed_subject = root_name + "-changed"
    changed_identity = stability_identity(
        RegistryExecutionPlan,
        subject=changed_subject,
        input_fingerprint=registry_input,
        configuration_fingerprint=plan_contract,
        dependencies=dependencies,
    )
    _require(
        changed_identity != entry.identity,
        "execution-plan root subject omitted from identity",
    )

    corrupt = CacheEntry(
        identity=entry.identity,
        artifact_fingerprint=cache_fingerprint(b"corrupt"),
        value=entry.value,
    )
    calls.clear()
    repaired = reuse_or_produce_stability(
        RegistryExecutionPlan,
        subject=root_name,
        input_fingerprint=registry_input,
        configuration_fingerprint=plan_contract,
        dependencies=dependencies,
        producer=plan_owner,
        cached=corrupt,
    )
    _require(repaired is not corrupt, "corrupt execution plan was reused")
    _require(calls == [True], "corrupt plan did not re-run owner producer")

    return entry


def _assert_real_stability_products() -> None:
    fixture = _root() / "apexforge" / "fixtures" / "p11_1b" / "manifest_entry"
    loaded = load_project(fixture)
    build_a = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    build_b = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )

    _require(build_a == build_b, "repeat ProjectBuild changed")
    _require(
        type(build_a.verified) is VerifiedAIRProgram,
        "ProjectBuilder verified owner changed",
    )
    _require(
        build_a.verified == build_b.verified,
        "repeat ProjectBuilder verified AIR changed",
    )

    empty_config = cache_fingerprint(b"")

    module_entry = reuse_or_produce_resonance(
        ModuleGraph,
        subject="project:stability-fixture",
        input_fingerprint=resonance_input_fingerprint(
            build_a.module_graph
        ),
        configuration_fingerprint=empty_config,
        producer=lambda: build_a.module_graph,
    )
    document_entry = reuse_or_produce_resonance(
        ProjectDocumentGraph,
        subject="project:stability-fixture",
        input_fingerprint=resonance_input_fingerprint(
            build_a.document_graph
        ),
        configuration_fingerprint=empty_config,
        producer=lambda: build_a.document_graph,
    )
    source_map_entry = reuse_or_produce_resonance(
        SourceMap,
        subject="project:stability-fixture",
        input_fingerprint=resonance_input_fingerprint(
            build_a.source_map
        ),
        configuration_fingerprint=empty_config,
        producer=lambda: build_a.source_map,
    )

    dependencies = (
        stability_dependency(module_entry),
        stability_dependency(document_entry),
        stability_dependency(source_map_entry),
    )

    _require(
        stability_dependencies_fingerprint(dependencies)
        == stability_dependencies_fingerprint(dependencies),
        "Stability dependency fingerprint is nondeterministic",
    )

    verified_entry = _assert_verified_air_reuse(
        build_a,
        dependencies,
    )

    root_name = loaded.manifest.entry
    _require(
        type(root_name) is str and bool(root_name),
        "fixture manifest entry is unavailable",
    )
    plan_dependencies = (
        *dependencies,
        stability_dependency(verified_entry),
    )
    plan_entry = _assert_execution_plan_reuse(
        build_a,
        root_name,
        plan_dependencies,
    )

    _require(
        resonance_fingerprint(module_entry.value)
        == module_entry.artifact_fingerprint,
        "Resonance predecessor integrity changed",
    )
    _require(
        verified_entry.identity.layer_id == "stability",
        "verified AIR layer changed",
    )
    _require(
        plan_entry.identity.layer_id == "stability",
        "execution-plan layer changed",
    )
    _require(
        verified_entry.identity.artifact_kind == "verified-air",
        "verified AIR kind changed",
    )
    _require(
        plan_entry.identity.artifact_kind == "execution-plan",
        "execution-plan kind changed",
    )


def _assert_no_surrogate_or_integration() -> None:
    source = (
        _root() / "apexforge" / "incremental_cache" / "stability.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    class_names = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    _require(not class_names, "Stability cache fabricated new owner classes")

    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    calls = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            calls.add(node.func.attr)

    for forbidden in (
        "ProjectBuilder",
        "build_project",
        "RuntimeEngine",
        "run_air_program",
        "run_air_from_registry",
        "NarrativeExecutionState",
        "CanonicalBuildArtifact",
        "AetherAirSnapshot",
    ):
        _require(
            forbidden not in names and forbidden not in calls,
            "Stability production acquired forbidden owner/integration: "
            + forbidden,
        )

    for forbidden in (
        "open",
        "write_bytes",
        "write_text",
    ):
        _require(
            forbidden not in calls,
            "Stability production acquired persistence behavior: "
            + forbidden,
        )


def _assert_owner_immutability() -> None:
    paths = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/tooling",
        "apexforge/type_system",
        "apexforge/governance",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *paths)
    _require(diff.returncode == 0, "P11.12E mutated semantic owners")


def main() -> None:
    _assert_predecessor()
    _assert_surface_and_taxonomy()
    _assert_real_stability_products()
    _assert_no_surrogate_or_integration()
    _assert_owner_immutability()

    print("P11_12D_FREEZE_ANCESTRY=PASS")
    print("P11_12B_TOP_LEVEL_CACHE_SURFACE=UNCHANGED")
    print("STABILITY_PUBLIC_OPERATION_COUNT=6")
    print("STABILITY_ALLOWED_OWNER_PRODUCT_COUNT=2")
    print("STABILITY_VERIFIED_AIR_OWNER=air.model.VerifiedAIRProgram")
    print("STABILITY_VERIFIED_AIR_PRODUCER=RuntimeValidator.validate")
    print("STABILITY_VERIFIED_AIR_REUSE=PASS")
    print("STABILITY_VERIFIED_AIR_OWNER_INVOCATION_ON_HIT=NONE")
    print("STABILITY_EXECUTION_PLAN_OWNER=workflow.air_runner.RegistryExecutionPlan")
    print("STABILITY_EXECUTION_PLAN_PRODUCER=build_registry_execution_plan")
    print("STABILITY_EXECUTION_PLAN_REUSE=PASS")
    print("STABILITY_EXECUTION_PLAN_OWNER_INVOCATION_ON_HIT=NONE")
    print("STABILITY_EXECUTION_PLAN_RUNTIME_ENGINE_CONSTRUCTION=NONE")
    print("STABILITY_CORRUPT_ENTRY_REUSE=REJECTED")
    print("PROJECT_BUILD_MIXED_LAYER_OBJECT=EXCLUDED")
    print("AIR_PROGRAM_DIRECT_STABILITY_ENTRY=EXCLUDED")
    print("NARRATIVE_EXECUTION_STATE_AS_CHECKPOINT=EXCLUDED")
    print("CANONICAL_BUILD_ARTIFACT_AS_OPTIMIZED_ARTIFACT=EXCLUDED")
    print("AETHER_AIR_RECLASSIFICATION=NONE")
    print("NEW_STABILITY_OWNER_CLASSES=NONE")
    print("GENERAL_CACHE_STORE=NONE")
    print("PERSISTENCE=NONE")
    print("PROJECT_BUILDER_INTEGRATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("P11_12E_STABILITY_LAYER_REUSE=PASS")


if __name__ == "__main__":
    main()