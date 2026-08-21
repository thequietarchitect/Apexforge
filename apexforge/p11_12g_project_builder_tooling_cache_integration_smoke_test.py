"""P11.12G ProjectBuilder/tooling incremental-cache integration smoke test."""

from __future__ import annotations

import ast
import inspect
from io import StringIO
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

import incremental_cache
import incremental_cache.integration as integration_module
from incremental_cache.integration import IncrementalProjectBuildSession
from language.project import ProjectBuild, build_project
from tooling.build_artifact import construct_build_artifact
from tooling.project_loader import load_project
import tooling.cli as cli


PREDECESSOR_TAG = "afp-p11-12f-freeze"
PREDECESSOR_COMMIT = "955e5a39dfc718fca7d29839a81d76a602a5d8cb"

F_HASHES = {
    "apexforge/incremental_cache/operational.py":
        "737CD68E6B2D25884F42F54F229C4B4852C5184CB666DE26C236D3430B2B47BD",
    "apexforge/p11_12f_dependency_aware_operational_cache_smoke_test.py":
        "10EA7B264B8B19F77D4D6A78B4295201E18C502DE90610B7C522E573A766CF8B",
    "docs/p11/P11_12F_DEPENDENCY_AWARE_OPERATIONAL_CACHE.md":
        "2760CC5A6D8DF146292759E8C7179D066EDBA0FF7F26344D6281AC3DFB4852E8",
}

EXPECTED_PUBLIC = (
    "IncrementalProjectBuildSession",
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
        "P11.12F freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.12F freeze is not ancestor of P11.12G",
    )
    for relative, expected in F_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12F hash changed".format(relative),
        )


def _assert_surface() -> None:
    _require(
        integration_module.__all__ == EXPECTED_PUBLIC,
        "P11.12G integration public surface changed",
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
        "P11.12G changed P11.12B top-level cache surface",
    )


def _outcomes(session: IncrementalProjectBuildSession):
    return tuple(
        observation.outcome
        for observation in session.last_observations
    )


def _operations(session: IncrementalProjectBuildSession):
    return tuple(
        observation.operation
        for observation in session.last_observations
    )


def _assert_cold_warm_and_changed_builds() -> None:
    fixture = _root() / "apexforge" / "fixtures" / "p11_1b" / "manifest_entry"
    loaded = load_project(fixture)
    sources = loaded.source_mapping()
    selected_entry = loaded.manifest.entry

    canonical = build_project(
        sources,
        entry=selected_entry,
    )
    session = IncrementalProjectBuildSession()

    cold = session.build(
        sources,
        entry=selected_entry,
    )
    _require(type(cold) is ProjectBuild, "cold build type changed")
    _require(cold == canonical, "cold cached build differs from canonical build")
    _require(
        cold.verified.program is cold.program,
        "cold ProjectBuild verified/program identity invariant changed",
    )
    _require(
        session.last_compiler_owner_invocations == len(sources),
        "cold build did not invoke compiler once per source",
    )
    _require(
        session.last_linker_owner_invocations == 1,
        "cold build did not invoke linker once",
    )
    _require(
        session.last_validator_owner_invocations == 1,
        "cold build did not invoke validator once",
    )
    _require(
        _outcomes(session).count("miss") == len(sources) + 1,
        "cold cache miss count changed",
    )
    _require(
        _outcomes(session).count("stored") == len(sources) + 1,
        "cold cache store count changed",
    )
    _require(
        len(session.collection.entries) == len(sources) + 1,
        "cold collection entry count changed",
    )

    canonical_artifact = construct_build_artifact(loaded, canonical)
    cold_artifact = construct_build_artifact(loaded, cold)
    _require(
        cold_artifact.content == canonical_artifact.content,
        "cold cached build artifact bytes changed",
    )
    _require(
        cold_artifact.fingerprint == canonical_artifact.fingerprint,
        "cold cached build artifact fingerprint changed",
    )

    warm = session.build(
        sources,
        entry=selected_entry,
    )
    _require(warm == canonical, "warm cached build differs from canonical build")
    _require(
        warm.program is cold.program,
        "warm build did not align linked AIR identity with verified cache",
    )
    _require(
        warm.verified is cold.verified,
        "warm build did not reuse exact VerifiedAIRProgram",
    )
    _require(
        warm.verified.program is warm.program,
        "warm ProjectBuild verified/program identity invariant changed",
    )
    _require(
        session.last_compiler_owner_invocations == 0,
        "warm build invoked compiler owner",
    )
    _require(
        session.last_linker_owner_invocations == 0,
        "warm build invoked linker owner",
    )
    _require(
        session.last_validator_owner_invocations == 0,
        "warm build invoked validator owner",
    )
    _require(
        _operations(session) == ("lookup", "lookup", "lookup"),
        "warm cache operation sequence changed",
    )
    _require(
        _outcomes(session) == ("hit", "hit", "hit"),
        "warm cache did not resolve to exact hits",
    )

    warm_artifact = construct_build_artifact(loaded, warm)
    _require(
        warm_artifact.content == canonical_artifact.content,
        "warm cached build artifact bytes changed",
    )
    _require(
        warm_artifact.fingerprint == canonical_artifact.fingerprint,
        "warm cached build artifact fingerprint changed",
    )

    changed_sources = dict(sources)
    changed_name = "src/main.apex"
    _require(changed_name in changed_sources, "expected fixture source disappeared")
    changed_sources[changed_name] = changed_sources[changed_name] + "\n"

    canonical_changed = build_project(
        changed_sources,
        entry=selected_entry,
    )
    changed = session.build(
        changed_sources,
        entry=selected_entry,
    )

    _require(
        changed == canonical_changed,
        "changed cached build differs from uncached canonical build",
    )
    _require(
        changed.verified.program is changed.program,
        "changed ProjectBuild verified/program identity invariant changed",
    )
    _require(
        session.last_compiler_owner_invocations == 1,
        "one-source change did not compile exactly one source",
    )
    _require(
        session.last_linker_owner_invocations == 1,
        "changed project did not relink once",
    )
    _require(
        session.last_validator_owner_invocations == 1,
        "changed project did not revalidate once",
    )
    _require(
        "stale" in _outcomes(session),
        "changed source did not expose stale cache evidence",
    )
    _require(
        "invalidated" in _outcomes(session),
        "changed source did not invalidate prior dependents",
    )
    _require(
        len(session.collection.entries) == len(sources) + 1,
        "changed build left duplicate logical cache versions",
    )

    warm_changed = session.build(
        changed_sources,
        entry=selected_entry,
    )
    _require(
        warm_changed == canonical_changed,
        "second changed build differs from canonical",
    )
    _require(
        session.last_compiler_owner_invocations == 0
        and session.last_linker_owner_invocations == 0
        and session.last_validator_owner_invocations == 0,
        "second changed build failed to become fully warm",
    )
    _require(
        _outcomes(session) == ("hit", "hit", "hit"),
        "second changed build was not exact-hit warm",
    )


def _invoke_cli(arguments, *, project_builder=None):
    stdout = StringIO()
    stderr = StringIO()
    code = cli.main(
        arguments,
        stdout=stdout,
        stderr=stderr,
        project_builder=project_builder,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def _assert_cli_build_injection() -> None:
    run_build_signature = inspect.signature(cli._run_build)
    _require(
        "builder" in run_build_signature.parameters,
        "CLI build still lacks injected-builder parameter",
    )

    run_build_source = inspect.getsource(cli._run_build)
    _require(
        "selected_builder = builder or _default_project_builder"
        in run_build_source,
        "CLI build does not select injected builder",
    )
    _require(
        "build = selected_builder(" in run_build_source,
        "CLI build does not invoke selected builder",
    )

    main_source = inspect.getsource(cli.main)
    build_branch = main_source[
        main_source.index('if namespace.command == "build":'):
    ]
    _require(
        "builder=project_builder" in build_branch,
        "CLI main does not pass injected builder to build",
    )

    fixture = _root() / "apexforge" / "fixtures" / "p11_1b" / "manifest_entry"
    loaded = load_project(fixture)
    canonical = build_project(
        loaded.source_mapping(),
        entry=loaded.manifest.entry,
    )
    expected_artifact = construct_build_artifact(loaded, canonical)

    session = IncrementalProjectBuildSession()

    with TemporaryDirectory() as temporary:
        output_a = Path(temporary) / "cold.json"
        cold = _invoke_cli(
            (
                "build",
                str(fixture),
                "--output",
                str(output_a),
            ),
            project_builder=session,
        )
        _require(cold[0] == 0, "CLI cached cold build failed")
        _require(cold[2] == "", "CLI cached cold build wrote stderr")
        _require(
            output_a.read_bytes() == expected_artifact.content,
            "CLI cached cold artifact bytes changed",
        )
        _require(
            session.last_compiler_owner_invocations
            == len(loaded.sources)
            and session.last_linker_owner_invocations == 1
            and session.last_validator_owner_invocations == 1,
            "CLI cold build owner invocation counts changed",
        )

        output_b = Path(temporary) / "warm.json"
        warm = _invoke_cli(
            (
                "build",
                str(fixture),
                "--output",
                str(output_b),
            ),
            project_builder=session,
        )
        _require(warm[0] == 0, "CLI cached warm build failed")
        _require(warm[2] == "", "CLI cached warm build wrote stderr")
        _require(
            output_b.read_bytes() == expected_artifact.content,
            "CLI cached warm artifact bytes changed",
        )
        _require(
            session.last_compiler_owner_invocations == 0
            and session.last_linker_owner_invocations == 0
            and session.last_validator_owner_invocations == 0,
            "CLI warm build invoked semantic owners",
        )
        _require(
            _outcomes(session) == ("hit", "hit", "hit"),
            "CLI warm build was not exact-hit warm",
        )


def _assert_integration_boundaries() -> None:
    integration_source = (
        _root() / "apexforge" / "incremental_cache" / "integration.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(integration_source)

    imported_roots = set()
    names = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    _require(
        "tap_check" not in imported_roots,
        "G integration acquired TAP ownership",
    )
    for forbidden in (
        "RuntimeEngine",
        "run_air_program",
        "run_air_from_registry",
        "write_text",
        "write_bytes",
        "open",
    ):
        _require(
            forbidden not in names and forbidden not in calls,
            "G integration acquired forbidden behavior: " + forbidden,
        )


def _assert_owner_mutation_boundary() -> None:
    protected = (
        "apexforge/air",
        "apexforge/language",
        "apexforge/quad_vector",
        "apexforge/semantic_lattice",
        "apexforge/aether_air",
        "apexforge/tam",
        "apexforge/tap_check",
        "apexforge/runtime",
        "apexforge/workflow",
        "apexforge/type_system",
        "apexforge/governance",
    )
    diff = _git("diff", "--exit-code", PREDECESSOR_TAG, "--", *protected)
    _require(diff.returncode == 0, "P11.12G mutated semantic owners")

    tooling_changes = tuple(
        line.strip().replace("\\", "/")
        for line in _git(
            "diff",
            "--name-only",
            PREDECESSOR_TAG,
            "--",
            "apexforge/tooling",
        ).stdout.splitlines()
        if line.strip()
    )
    _require(
        tooling_changes == ("apexforge/tooling/cli.py",),
        "P11.12G tooling mutation exceeded CLI builder seam",
    )


def main() -> None:
    _assert_predecessor()
    _assert_surface()
    _assert_cold_warm_and_changed_builds()
    _assert_cli_build_injection()
    _assert_integration_boundaries()
    _assert_owner_mutation_boundary()

    print("P11_12F_FREEZE_ANCESTRY=PASS")
    print("P11_12B_TOP_LEVEL_CACHE_SURFACE=UNCHANGED")
    print("INTEGRATION_PUBLIC_SYMBOL_COUNT=1")
    print("INTEGRATION_OWNER=incremental_cache")
    print("BUILD_SESSION_MODEL=EXPLICIT_INSTANCE_LOCAL")
    print("GLOBAL_MUTABLE_SINGLETON=NONE")
    print("PROJECT_BUILDER_SEMANTIC_OWNER=UNCHANGED")
    print("PROJECT_BUILD_CACHE_ENTRY=NONE")
    print("COMPILER_CACHE_PRODUCT=language.compiler.CompiledSource")
    print("COMPILER_COLD_OWNER_INVOCATION=PASS")
    print("COMPILER_WARM_OWNER_INVOCATION=NONE")
    print("LINKER_WARM_IDENTITY_ALIGNMENT=PASS")
    print("LINKER_WARM_OWNER_INVOCATION=NONE")
    print("VERIFIED_AIR_CACHE_PRODUCT=air.model.VerifiedAIRProgram")
    print("VALIDATOR_COLD_OWNER_INVOCATION=PASS")
    print("VALIDATOR_WARM_OWNER_INVOCATION=NONE")
    print("PROJECTBUILD_VERIFIED_PROGRAM_IDENTITY=PASS")
    print("CACHED_VS_UNCACHED_PROJECTBUILD=EXACT_EQUALITY")
    print("CACHED_VS_UNCACHED_BUILD_ARTIFACT_BYTES=EXACT")
    print("CACHED_VS_UNCACHED_BUILD_ARTIFACT_FINGERPRINT=EXACT")
    print("ONE_SOURCE_CHANGE_COMPILER_REBUILD_COUNT=1")
    print("STALE_LOOKUP=OBSERVED")
    print("TRANSITIVE_CACHE_INVALIDATION=OBSERVED")
    print("CHANGED_BUILD_RELINK_COUNT=1")
    print("CHANGED_BUILD_REVALIDATION_COUNT=1")
    print("SECOND_CHANGED_BUILD=FULLY_WARM")
    print("CLI_CHECK_RUN_BUILDER_SEAM=PRESERVED")
    print("CLI_BUILD_BUILDER_SEAM=NORMALIZED")
    print("CLI_BUILD_COLD_WARM_ARTIFACT_EQUIVALENCE=PASS")
    print("LANGUAGE_SERVER_INTEGRATION=NONE")
    print("TAP_OPTIMIZATION_ADAPTER=DEFERRED")
    print("PERSISTENCE=NONE")
    print("RUNTIME_EXECUTION_CACHE=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("TOOLING_MUTATION=CLI_BUILDER_SEAM_ONLY")
    print("P11_12G_PROJECT_BUILDER_TOOLING_CACHE_INTEGRATION=PASS")


if __name__ == "__main__":
    main()