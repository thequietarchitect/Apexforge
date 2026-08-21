"""P11.12F dependency-aware operational cache/invalidation smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import ast
from pathlib import Path
import subprocess

import incremental_cache
import incremental_cache.operational as operational_module
from incremental_cache import (
    CACHE_SCHEMA_VERSION,
    CacheDependency,
    CacheEntry,
    CacheIdentity,
    cache_fingerprint,
)
from incremental_cache.operational import (
    CacheCollection,
    CacheObservation,
    affected_project_sources,
    cache_keys_for_subjects,
)
from language.project import build_project


PREDECESSOR_TAG = "afp-p11-12e-freeze"
PREDECESSOR_COMMIT = "a68888734c4e20ed8152f1d9c2e08cf76b27eba6"

E_HASHES = {
    "apexforge/incremental_cache/stability.py":
        "FCE07FFB1B483DB26F0735C3B9BBAF6C7E985865104D3B867CBF0410A87A76FB",
    "apexforge/p11_12e_stability_layer_verified_air_execution_plan_reuse_smoke_test.py":
        "28DE2D18465E2366AD007FD373279E431203E58F29BB6B142D4A654E50743868",
    "docs/p11/P11_12E_STABILITY_LAYER_VERIFIED_AIR_EXECUTION_PLAN_REUSE.md":
        "6E1F4C129E1F4703060A213116069309E3B75111EDCD1C43C1540F44F4EFDB2A",
}

EXPECTED_PUBLIC = (
    "CacheObservation",
    "CacheCollection",
    "cache_keys_for_subjects",
    "affected_project_sources",
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


def _require_raises(expected_type, operation, message: str):
    try:
        operation()
    except expected_type as error:
        return error
    raise AssertionError(message)


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12E freeze target changed",
    )
    _require(
        _git(
            "merge-base",
            "--is-ancestor",
            PREDECESSOR_TAG,
            "HEAD",
        ).returncode == 0,
        "P11.12E freeze is not ancestor of P11.12F",
    )
    for relative, expected in E_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12E hash changed".format(relative),
        )


def _assert_surface_and_immutability() -> None:
    _require(
        operational_module.__all__ == EXPECTED_PUBLIC,
        "P11.12F operational public surface changed",
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
        "P11.12F changed P11.12B top-level cache surface",
    )

    observation = CacheObservation(
        operation="lookup",
        outcome="miss",
        requested_cache_keys=("0" * 64,),
    )
    collection = CacheCollection()

    _require_raises(
        FrozenInstanceError,
        lambda: setattr(observation, "outcome", "hit"),
        "CacheObservation is mutable",
    )
    _require_raises(
        FrozenInstanceError,
        lambda: setattr(collection, "entries", ()),
        "CacheCollection is mutable",
    )

    _require_raises(
        ValueError,
        lambda: CacheObservation(
            operation="lookup",
            outcome="stored",
            requested_cache_keys=("0" * 64,),
        ),
        "invalid cache observation operation/outcome was accepted",
    )


def _identity(
    *,
    layer: str,
    kind: str,
    owner: str,
    subject: str,
    input_bytes: bytes,
    dependencies=(),
) -> CacheIdentity:
    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=layer,
        artifact_kind=kind,
        owner=owner,
        subject=subject,
        input_fingerprint=cache_fingerprint(input_bytes),
        configuration_fingerprint=cache_fingerprint(b"config"),
        dependencies=dependencies,
    )


def _entry(
    *,
    layer: str,
    kind: str,
    owner: str,
    subject: str,
    input_bytes: bytes,
    artifact_bytes: bytes,
    value,
    dependencies=(),
) -> CacheEntry:
    return CacheEntry(
        identity=_identity(
            layer=layer,
            kind=kind,
            owner=owner,
            subject=subject,
            input_bytes=input_bytes,
            dependencies=dependencies,
        ),
        artifact_fingerprint=cache_fingerprint(artifact_bytes),
        value=value,
    )


def _dependency(entry: CacheEntry) -> CacheDependency:
    return CacheDependency(
        cache_key=entry.cache_key,
        fingerprint=entry.artifact_fingerprint,
    )


def _assert_collection_store_lookup_invalidation() -> None:
    a = _entry(
        layer="capture",
        kind="document",
        owner="tooling.project_loader",
        subject="10-core.apex",
        input_bytes=b"core-v1",
        artifact_bytes=b"core-artifact",
        value=("core",),
    )
    b = _entry(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="10-core.apex",
        input_bytes=b"core-ast-v1",
        artifact_bytes=b"core-ast-artifact",
        value=("core-ast",),
        dependencies=(_dependency(a),),
    )
    c = _entry(
        layer="stability",
        kind="verified-air",
        owner="air.model",
        subject="project:demo",
        input_bytes=b"verified-v1",
        artifact_bytes=b"verified-artifact",
        value=("verified",),
        dependencies=(_dependency(b),),
    )

    collection = CacheCollection()
    collection, store_a = collection.store(a)
    collection, store_b = collection.store(b)
    collection, store_c = collection.store(c)

    _require(
        store_a.outcome == store_b.outcome == store_c.outcome == "stored",
        "cache store observation changed",
    )
    _require(
        collection.entries == (a, b, c),
        "cache collection stopped preserving deterministic insertion order",
    )
    _require(
        collection.keys() == (a.cache_key, b.cache_key, c.cache_key),
        "cache key order changed",
    )

    for expected in (a, b, c):
        hit, observation = collection.lookup(expected.identity)
        _require(hit is expected, "exact cache identity was not returned")
        _require(
            observation
            == CacheObservation(
                operation="lookup",
                outcome="hit",
                requested_cache_keys=(expected.cache_key,),
                affected_cache_keys=(expected.cache_key,),
            ),
            "cache hit observation changed",
        )

    same_collection, existing = collection.store(c)
    _require(
        same_collection is collection and existing.outcome == "existing",
        "idempotent existing store changed",
    )

    alternate_b_identity = _identity(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="10-core.apex",
        input_bytes=b"core-ast-v2",
        dependencies=(_dependency(a),),
    )
    stale_entry, stale = collection.lookup(alternate_b_identity)
    _require(stale_entry is None, "stale cache version became reusable")
    _require(stale.outcome == "stale", "stale cache slot was not observed")
    _require(
        stale.affected_cache_keys == (b.cache_key,),
        "stale observation lost resident key",
    )

    missing_identity = _identity(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="unseen.apex",
        input_bytes=b"unseen",
    )
    missing_entry, miss = collection.lookup(missing_identity)
    _require(missing_entry is None, "cache miss returned an entry")
    _require(miss.outcome == "miss", "cache miss observation changed")

    replacement_b = CacheEntry(
        identity=alternate_b_identity,
        artifact_fingerprint=cache_fingerprint(b"core-ast-artifact-v2"),
        value=("core-ast-v2",),
    )
    _require_raises(
        ValueError,
        lambda: collection.store(replacement_b),
        "logical-slot replacement bypassed explicit invalidation",
    )

    missing_dependency = CacheDependency(
        cache_key="1" * 64,
        fingerprint=cache_fingerprint(b"missing"),
    )
    missing_dep_entry = _entry(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="missing-dependency.apex",
        input_bytes=b"x",
        artifact_bytes=b"y",
        value=("x",),
        dependencies=(missing_dependency,),
    )
    _require_raises(
        ValueError,
        lambda: collection.store(missing_dep_entry),
        "missing cache dependency was accepted",
    )

    wrong_dependency = CacheDependency(
        cache_key=a.cache_key,
        fingerprint=cache_fingerprint(b"wrong-artifact"),
    )
    wrong_dep_entry = _entry(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="wrong-dependency.apex",
        input_bytes=b"x2",
        artifact_bytes=b"y2",
        value=("x2",),
        dependencies=(wrong_dependency,),
    )
    _require_raises(
        ValueError,
        lambda: collection.store(wrong_dep_entry),
        "dependency fingerprint mismatch was accepted",
    )

    subject_keys = cache_keys_for_subjects(
        collection,
        ("10-core.apex",),
    )
    _require(
        subject_keys == (a.cache_key, b.cache_key),
        "cache subject projection changed",
    )

    after_b, invalidated_b = collection.invalidate((b.cache_key,))
    _require(
        invalidated_b.affected_cache_keys == (b.cache_key, c.cache_key),
        "dependent invalidation closure/order changed",
    )
    _require(
        after_b.entries == (a,),
        "dependent invalidation removed wrong entries",
    )

    after_a, invalidated_a = collection.invalidate((a.cache_key,))
    _require(
        invalidated_a.affected_cache_keys
        == (a.cache_key, b.cache_key, c.cache_key),
        "transitive invalidation closure/order changed",
    )
    _require(after_a.entries == (), "full dependency invalidation did not empty cache")

    unchanged, noop = collection.invalidate(("f" * 64,))
    _require(
        unchanged is collection
        and noop.outcome == "noop"
        and noop.affected_cache_keys == (),
        "unknown invalidation seed changed collection",
    )

    repeated_a, repeated_observation = collection.invalidate((a.cache_key,))
    _require(
        repeated_a == after_a
        and repeated_observation == invalidated_a,
        "cache invalidation is nondeterministic",
    )


def _assert_constructor_invariants() -> None:
    dependency = _entry(
        layer="capture",
        kind="document",
        owner="tooling.project_loader",
        subject="dep.apex",
        input_bytes=b"dep",
        artifact_bytes=b"dep-artifact",
        value=("dep",),
    )
    dependent = _entry(
        layer="resonance",
        kind="ast",
        owner="language.parser",
        subject="dep.apex",
        input_bytes=b"ast",
        artifact_bytes=b"ast-artifact",
        value=("ast",),
        dependencies=(_dependency(dependency),),
    )

    _require_raises(
        ValueError,
        lambda: CacheCollection((dependent, dependency)),
        "collection accepted dependent before dependency",
    )
    _require_raises(
        ValueError,
        lambda: CacheCollection((dependency, dependency)),
        "collection accepted duplicate cache key",
    )


def _assert_project_source_invalidation_closure() -> None:
    sources = {
        "40-main.apex": (
            "module app.main\n"
            "import app.util\n"
            "import app.feature\n\n"
            "directive Main {}\n"
        ),
        "30-feature.apex": (
            "module app.feature\n"
            "import app.core\n\n"
            "directive Feature {}\n"
        ),
        "20-util.apex": (
            "module app.util\n"
            "import app.core\n\n"
            "directive Util {}\n"
        ),
        "10-core.apex": (
            "module app.core\n\n"
            "directive Core {}\n"
        ),
    }
    project = build_project(sources, entry="Main")
    graph = project.document_graph

    _require(
        graph.dependency_order
        == (
            "10-core.apex",
            "30-feature.apex",
            "20-util.apex",
            "40-main.apex",
        ),
        "accepted P11.3B dependency order changed",
    )

    _require(
        affected_project_sources(
            graph,
            ("10-core.apex",),
        )
        == graph.dependency_order,
        "core change did not invalidate all transitive importers",
    )
    _require(
        affected_project_sources(
            graph,
            ("30-feature.apex",),
        )
        == ("30-feature.apex", "40-main.apex"),
        "feature change invalidation closure changed",
    )
    _require(
        affected_project_sources(
            graph,
            ("20-util.apex",),
        )
        == ("20-util.apex", "40-main.apex"),
        "util change invalidation closure changed",
    )
    _require(
        affected_project_sources(
            graph,
            ("40-main.apex",),
        )
        == ("40-main.apex",),
        "root-only change invalidated dependencies",
    )
    _require(
        affected_project_sources(
            graph,
            ("30-feature.apex", "20-util.apex"),
        )
        == (
            "30-feature.apex",
            "20-util.apex",
            "40-main.apex",
        ),
        "multi-source affected closure/order changed",
    )
    _require_raises(
        ValueError,
        lambda: affected_project_sources(
            graph,
            ("unknown.apex",),
        ),
        "unknown changed source was silently ignored",
    )


def _assert_no_persistence_builder_tap_or_runtime_integration() -> None:
    source = (
        _root() / "apexforge" / "incremental_cache" / "operational.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

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

    for module_name in (
        "pickle",
        "shelve",
        "sqlite3",
        "tempfile",
        "tap_check",
        "runtime",
        "workflow",
        "tooling",
    ):
        _require(
            module_name not in imported_roots,
            "operational cache imported forbidden subsystem: " + module_name,
        )

    for symbol in (
        "ProjectBuilder",
        "build_project",
        "RuntimeEngine",
        "run_air_program",
        "TapCheckLedgerEntry",
        "audit_trace_map",
        "open",
        "write_text",
        "write_bytes",
    ):
        _require(
            symbol not in names and symbol not in calls,
            "operational cache acquired forbidden behavior: " + symbol,
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
    _require(diff.returncode == 0, "P11.12F mutated semantic owners")


def main() -> None:
    _assert_predecessor()
    _assert_surface_and_immutability()
    _assert_collection_store_lookup_invalidation()
    _assert_constructor_invariants()
    _assert_project_source_invalidation_closure()
    _assert_no_persistence_builder_tap_or_runtime_integration()
    _assert_owner_immutability()

    print("P11_12E_FREEZE_ANCESTRY=PASS")
    print("P11_12B_TOP_LEVEL_CACHE_SURFACE=UNCHANGED")
    print("OPERATIONAL_CACHE_PUBLIC_SYMBOL_COUNT=4")
    print("CACHE_COLLECTION_MODEL=FROZEN_FUNCTIONAL")
    print("CACHE_COLLECTION_ORDER=DEPENDENCY_FIRST_INSERTION_ORDER")
    print("CACHE_COLLECTION_KEY_UNIQUENESS=PASS")
    print("CACHE_LOGICAL_SLOT_UNIQUENESS=PASS")
    print("CACHE_STORE_DEPENDENCY_PRESENCE=ENFORCED")
    print("CACHE_STORE_DEPENDENCY_FINGERPRINT=ENFORCED")
    print("CACHE_LOOKUP_HIT=PASS")
    print("CACHE_LOOKUP_MISS=PASS")
    print("CACHE_LOOKUP_STALE=PASS")
    print("CACHE_STALE_ENTRY_REUSE=NONE")
    print("CONTENT_ADDRESSED_CORRECTNESS=PRIMARY")
    print("CACHE_INVALIDATION_TRANSITIVE_DEPENDENTS=PASS")
    print("CACHE_INVALIDATION_ORDER=DETERMINISTIC_COLLECTION_ORDER")
    print("CACHE_INVALIDATION_NOOP=PASS")
    print("CACHE_SUBJECT_KEY_PROJECTION=PASS")
    print("PROJECT_SOURCE_AFFECTED_CLOSURE=PASS")
    print("PROJECT_SOURCE_AFFECTED_ORDER=DEPENDENCY_FIRST")
    print("CACHE_OBSERVATION_MODEL=FROZEN")
    print("CACHE_OBSERVATION_OPERATIONS=store,lookup,invalidate")
    print("CACHE_OBSERVATION_OUTCOMES=stored,existing,hit,miss,stale,invalidated,noop")
    print("TAP_OPTIMIZATION_ADAPTER=DEFERRED")
    print("PERSISTENCE=NONE")
    print("GLOBAL_MUTABLE_SINGLETON=NONE")
    print("PROJECT_BUILDER_INTEGRATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("SEMANTIC_OWNER_MUTATION=NONE")
    print("P11_12F_DEPENDENCY_AWARE_OPERATIONAL_CACHE=PASS")


if __name__ == "__main__":
    main()