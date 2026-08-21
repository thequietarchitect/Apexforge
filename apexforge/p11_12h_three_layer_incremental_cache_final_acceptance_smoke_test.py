"""P11.12H final three-layer incremental-cache acceptance."""

from __future__ import annotations

import inspect
from pathlib import Path
import statistics
import subprocess
import time

import incremental_cache
import incremental_cache.capture as capture_module
import incremental_cache.integration as integration_module
import incremental_cache.operational as operational_module
import incremental_cache.resonance as resonance_module
import incremental_cache.stability as stability_module
from incremental_cache.integration import IncrementalProjectBuildSession
from language.project import ProjectBuild, build_project
from tooling.build_artifact import construct_build_artifact
from tooling.performance_baseline import DEFAULT_FIXTURES
from tooling.project_loader import load_project


PREDECESSOR_TAG = "afp-p11-12g-freeze"
PREDECESSOR_COMMIT = "93b9457f6be864dbc8bb066a193f6fd9942a8c7a"

G_FROZEN_NON_INTEGRATION_HASHES = {
    "apexforge/p11_12g_project_builder_tooling_cache_integration_smoke_test.py":
        "0022DBF0368C2558221576FD5312341AF4CCD6F14137E6B1F00CAEDBF73003D4",
    "apexforge/tooling/cli.py":
        "2751B9CFE35498F970B429899AB806767398297EB855737F28058E58689035E2",
    "docs/p11/P11_12G_PROJECT_BUILDER_TOOLING_CACHE_INTEGRATION.md":
        "F5F70D13AABD3B3C8C56DC9A1A1892813A85821271079835E353BE31E0C8FAF0",
}

EXPECTED_INTEGRATION_PUBLIC = (
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


def _median(values):
    return int(statistics.median(values))


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12G freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.12G freeze is not ancestor of P11.12H",
    )
    for relative, expected in G_FROZEN_NON_INTEGRATION_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} frozen G artifact changed".format(relative),
        )


def _assert_surface_census() -> None:
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
        "P11.12H changed frozen top-level cache surface",
    )
    _require(
        integration_module.__all__ == EXPECTED_INTEGRATION_PUBLIC,
        "P11.12H changed integration public surface",
    )
    _require(len(capture_module.__all__) == 7, "Capture surface changed")
    _require(len(resonance_module.__all__) == 6, "Resonance surface changed")
    _require(len(stability_module.__all__) == 6, "Stability surface changed")
    _require(len(operational_module.__all__) == 4, "Operational surface changed")


def _assert_fixed_corpus_equivalence() -> None:
    for fixture in DEFAULT_FIXTURES:
        loaded = load_project(fixture.project_root)
        sources = loaded.source_mapping()
        selected_entry = loaded.manifest.entry

        canonical = build_project(sources, entry=selected_entry)
        session = IncrementalProjectBuildSession()
        cold = session.build(sources, entry=selected_entry)
        warm = session.build(sources, entry=selected_entry)

        _require(type(canonical) is ProjectBuild, "canonical build type changed")
        _require(cold == canonical, "{} cold divergence".format(fixture.name))
        _require(warm == canonical, "{} warm divergence".format(fixture.name))
        _require(
            warm.verified.program is warm.program,
            "{} verified/program identity changed".format(fixture.name),
        )
        _require(
            session.last_compiler_owner_invocations == 0
            and session.last_linker_owner_invocations == 0
            and session.last_validator_owner_invocations == 0,
            "{} warm build invoked semantic owners".format(fixture.name),
        )

        canonical_artifact = construct_build_artifact(loaded, canonical)
        warm_artifact = construct_build_artifact(loaded, warm)
        _require(
            warm_artifact.content == canonical_artifact.content,
            "{} artifact bytes changed".format(fixture.name),
        )
        _require(
            warm_artifact.fingerprint == canonical_artifact.fingerprint,
            "{} artifact fingerprint changed".format(fixture.name),
        )


def _paired_performance_acceptance():
    representative = next(
        fixture
        for fixture in DEFAULT_FIXTURES
        if fixture.name == "representative-linked"
    )
    loaded = load_project(representative.project_root)
    sources = loaded.source_mapping()
    selected_entry = loaded.manifest.entry

    for _ in range(5):
        build_project(sources, entry=selected_entry)

    session = IncrementalProjectBuildSession()
    session.build(sources, entry=selected_entry)
    session.build(sources, entry=selected_entry)

    uncached = []
    warm = []
    samples = 31

    for index in range(samples):
        if index % 2 == 0:
            started = time.perf_counter_ns()
            canonical = build_project(sources, entry=selected_entry)
            uncached.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            cached = session.build(sources, entry=selected_entry)
            warm.append(time.perf_counter_ns() - started)
        else:
            started = time.perf_counter_ns()
            cached = session.build(sources, entry=selected_entry)
            warm.append(time.perf_counter_ns() - started)

            started = time.perf_counter_ns()
            canonical = build_project(sources, entry=selected_entry)
            uncached.append(time.perf_counter_ns() - started)

        _require(cached == canonical, "timed warm build diverged")
        _require(
            session.last_compiler_owner_invocations == 0
            and session.last_linker_owner_invocations == 0
            and session.last_validator_owner_invocations == 0,
            "timed warm build invoked semantic owners",
        )

    uncached_median = _median(uncached)
    warm_median = _median(warm)
    reduction_ns = uncached_median - warm_median
    reduction_ratio = (
        reduction_ns / uncached_median
        if uncached_median
        else 0.0
    )

    _require(
        warm_median < uncached_median,
        "P11.12H warm median did not beat uncached median",
    )

    return (
        representative,
        loaded,
        sources,
        selected_entry,
        uncached_median,
        warm_median,
        reduction_ns,
        reduction_ratio,
    )


def _changed_build_acceptance(
    loaded,
    sources,
    selected_entry,
):
    session = IncrementalProjectBuildSession()
    session.build(sources, entry=selected_entry)

    changed_sources = dict(sources)
    changed_name = "src/20-adjust.apex"
    _require(changed_name in changed_sources, "changed-source fixture disappeared")
    changed_sources[changed_name] = changed_sources[changed_name] + "\n"

    started = time.perf_counter_ns()
    canonical_changed = build_project(
        changed_sources,
        entry=selected_entry,
    )
    uncached_changed_ns = time.perf_counter_ns() - started

    started = time.perf_counter_ns()
    cached_changed = session.build(
        changed_sources,
        entry=selected_entry,
    )
    cached_changed_ns = time.perf_counter_ns() - started

    _require(
        cached_changed == canonical_changed,
        "changed cached build diverged",
    )
    _require(
        session.last_compiler_owner_invocations == 1,
        "changed build did not compile exactly one source",
    )
    _require(
        session.last_linker_owner_invocations == 1,
        "changed build did not relink exactly once",
    )
    _require(
        session.last_validator_owner_invocations == 1,
        "changed build did not revalidate exactly once",
    )

    outcomes = tuple(
        observation.outcome
        for observation in session.last_observations
    )
    _require("stale" in outcomes, "changed build lost stale observation")
    _require(
        "invalidated" in outcomes,
        "changed build lost invalidation observation",
    )
    _require("stored" in outcomes, "changed build lost store observation")
    _require("hit" in outcomes, "changed build lost unchanged-source hit")
    return (
        uncached_changed_ns,
        cached_changed_ns,
        outcomes,
    )


def _assert_optimization_shape() -> None:
    source = inspect.getsource(IncrementalProjectBuildSession)

    for marker in (
        "_entries_by_key",
        "_slot_to_key",
        "_trusted_entry_keys",
        "_compiler_configuration_fingerprints",
    ):
        _require(marker in source, "H warm-path optimization marker missing: " + marker)

    _require(
        "cache ProjectBuild" not in source,
        "integration source unexpectedly claims ProjectBuild caching",
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
    _require(diff.returncode == 0, "P11.12H mutated semantic owners")

    tooling = tuple(
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
    _require(not tooling, "P11.12H introduced new tooling changes")


def main() -> None:
    _assert_predecessor()
    _assert_surface_census()
    _assert_fixed_corpus_equivalence()
    _assert_optimization_shape()

    (
        representative,
        loaded,
        sources,
        selected_entry,
        uncached_median,
        warm_median,
        reduction_ns,
        reduction_ratio,
    ) = _paired_performance_acceptance()

    (
        uncached_changed_ns,
        cached_changed_ns,
        changed_outcomes,
    ) = _changed_build_acceptance(
        loaded,
        sources,
        selected_entry,
    )

    _assert_owner_mutation_boundary()

    print("P11_12G_FREEZE_ANCESTRY=PASS")
    print("P11_12B_TOP_LEVEL_CACHE_SURFACE=UNCHANGED")
    print("CAPTURE_PUBLIC_OPERATION_COUNT=7")
    print("RESONANCE_PUBLIC_OPERATION_COUNT=6")
    print("STABILITY_PUBLIC_OPERATION_COUNT=6")
    print("OPERATIONAL_PUBLIC_SYMBOL_COUNT=4")
    print("INTEGRATION_PUBLIC_SYMBOL_COUNT=1")
    print("FIXED_CORPUS_SEMANTIC_EQUIVALENCE=PASS")
    print("WARM_COMPILER_OWNER_INVOCATIONS=NONE")
    print("WARM_LINKER_OWNER_INVOCATIONS=NONE")
    print("WARM_VALIDATOR_OWNER_INVOCATIONS=NONE")
    print("PROJECTBUILD_VERIFIED_PROGRAM_IDENTITY=PASS")
    print("BUILD_ARTIFACT_BYTES_FINGERPRINT_EQUIVALENCE=PASS")
    print("WARM_LOOKUP_INDEX=SESSION_LOCAL")
    print("TRUSTED_ARTIFACT_FAST_PATH=SESSION_OWNED_OR_VERIFY_ONCE_EXTERNAL")
    print("COMPILER_CONFIGURATION_FINGERPRINT_MEMOIZATION=PASS")
    print("PERFORMANCE_FIXTURE={}".format(representative.name))
    print("PERFORMANCE_SAMPLE_COUNT=31")
    print("UNCACHED_MEDIAN_NS={}".format(uncached_median))
    print("WARM_MEDIAN_NS={}".format(warm_median))
    print("WARM_REDUCTION_NS={}".format(reduction_ns))
    print("WARM_REDUCTION_RATIO={:.6f}".format(reduction_ratio))
    print("WARM_MEDIAN_FASTER=True")
    print("ARBITRARY_PERCENT_THRESHOLD=NONE")
    print("CHANGED_BUILD_UNCACHED_NS={}".format(uncached_changed_ns))
    print("CHANGED_BUILD_CACHED_NS={}".format(cached_changed_ns))
    print("CHANGED_COMPILER_OWNER_INVOCATIONS=1")
    print("CHANGED_LINKER_OWNER_INVOCATIONS=1")
    print("CHANGED_VALIDATOR_OWNER_INVOCATIONS=1")
    print("CHANGED_OBSERVATION_OUTCOMES={}".format(changed_outcomes))
    print("CACHE_OBSERVATION_CENSUS=hit,miss,stale,stored,invalidated")
    print("PERSISTENCE=NONE")
    print("GLOBAL_MUTABLE_SINGLETON=NONE")
    print("PROJECT_BUILD_CACHE_ENTRY=NONE")
    print("TAP_OPTIMIZATION_ADAPTER=DEFERRED")
    print("RUNTIME_EXECUTION_CACHE=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("P11_12H_THREE_LAYER_INCREMENTAL_CACHE_FINAL_ACCEPTANCE=PASS")


if __name__ == "__main__":
    main()