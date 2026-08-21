"""P11.12B minimal immutable incremental-cache model smoke test."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
import inspect
from pathlib import Path
import subprocess

import incremental_cache
from incremental_cache import (
    CACHE_FINGERPRINT_ALGORITHM,
    CACHE_LAYER_IDS,
    CACHE_SCHEMA_VERSION,
    CacheDependency,
    CacheEntry,
    CacheFingerprint,
    CacheIdentity,
    cache_fingerprint,
    cache_identity_key,
)


PREDECESSOR_TAG = "afp-p11-12a-freeze"
PREDECESSOR_COMMIT = "eec3da648f1de8e5bd38fed04141cdb985c0c172"

A_HASHES = {
    "apexforge/p11_12a_three_layer_incremental_cache_architecture_audit_smoke_test.py":
        "B4D5C73EA65B64DE6CD436F8DBF66F22BA8C47AB576B4690AAF6C0B701BCAD15",
    "docs/p11/P11_12A_THREE_LAYER_INCREMENTAL_CACHE_ARCHITECTURE_AUDIT.md":
        "464744B053CFF2B153226E6613431D60D3CF626983D8F455C249F2E76B6B897D",
}

EXPECTED_PUBLIC = (
    "CACHE_SCHEMA_VERSION",
    "CACHE_LAYER_IDS",
    "CACHE_FINGERPRINT_ALGORITHM",
    "CacheFingerprint",
    "CacheDependency",
    "CacheIdentity",
    "CacheEntry",
    "cache_fingerprint",
    "cache_identity_key",
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


def _expect(exception_type, callback) -> None:
    try:
        callback()
    except exception_type:
        return
    raise AssertionError(
        "expected {} was not raised".format(exception_type.__name__)
    )


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _assert_predecessor() -> None:
    resolved = _git("rev-parse", "{}^{{}}".format(PREDECESSOR_TAG))
    _require(resolved.returncode == 0, resolved.stderr.strip())
    _require(
        resolved.stdout.strip() == PREDECESSOR_COMMIT,
        "P11.12A freeze target changed",
    )
    _require(
        _git("merge-base", "--is-ancestor", PREDECESSOR_TAG, "HEAD").returncode == 0,
        "P11.12A freeze is not an ancestor of P11.12B",
    )
    for relative, expected in A_HASHES.items():
        _require(
            _sha256(_root() / relative) == expected,
            "{} P11.12A hash changed".format(relative),
        )


def _assert_public_model() -> None:
    _require(CACHE_SCHEMA_VERSION == 1, "cache schema version changed")
    _require(
        CACHE_LAYER_IDS == ("capture", "resonance", "stability"),
        "cache layer taxonomy changed",
    )
    _require(
        CACHE_FINGERPRINT_ALGORITHM == "sha256",
        "cache hash algorithm changed",
    )
    _require(incremental_cache.__all__ == EXPECTED_PUBLIC, "public surface changed")

    expected_fields = {
        CacheFingerprint: ("algorithm", "value"),
        CacheDependency: ("cache_key", "fingerprint"),
        CacheIdentity: (
            "schema_version",
            "layer_id",
            "artifact_kind",
            "owner",
            "subject",
            "input_fingerprint",
            "configuration_fingerprint",
            "dependencies",
        ),
        CacheEntry: ("identity", "artifact_fingerprint", "value"),
    }
    for value, expected in expected_fields.items():
        _require(is_dataclass(value), "{} is not dataclass".format(value.__name__))
        _require(
            value.__dataclass_params__.frozen,
            "{} is not frozen".format(value.__name__),
        )
        _require(
            tuple(field.name for field in fields(value)) == expected,
            "{} fields changed".format(value.__name__),
        )

    _require(
        str(inspect.signature(cache_fingerprint))
        == "(payload: 'bytes') -> 'CacheFingerprint'",
        "cache_fingerprint signature changed",
    )
    _require(
        str(inspect.signature(cache_identity_key))
        == "(identity: 'CacheIdentity') -> 'str'",
        "cache_identity_key signature changed",
    )


def _assert_fingerprints() -> None:
    empty = cache_fingerprint(b"")
    again = cache_fingerprint(b"")
    changed = cache_fingerprint(b"x")

    _require(empty is not again, "fingerprint factory reused object identity")
    _require(empty == again, "fingerprint factory is nondeterministic")
    _require(empty != changed, "fingerprint did not change with exact bytes")
    _require(len(empty.value) == 64, "fingerprint length changed")
    _require(empty.value == empty.value.lower(), "fingerprint is not lowercase")

    _expect(TypeError, lambda: cache_fingerprint("not-bytes"))
    _expect(
        ValueError,
        lambda: CacheFingerprint("sha256", "A" * 64),
    )
    _expect(
        ValueError,
        lambda: CacheFingerprint("sha1", "0" * 64),
    )


def _identity(
    *,
    layer_id: str = "capture",
    artifact_kind: str = "document",
    owner: str = "tooling.project_loader",
    subject: str = "src/main.apex",
    input_payload: bytes = b"source",
    configuration_payload: bytes = b"config",
    dependencies=(),
) -> CacheIdentity:
    return CacheIdentity(
        schema_version=CACHE_SCHEMA_VERSION,
        layer_id=layer_id,
        artifact_kind=artifact_kind,
        owner=owner,
        subject=subject,
        input_fingerprint=cache_fingerprint(input_payload),
        configuration_fingerprint=cache_fingerprint(configuration_payload),
        dependencies=dependencies,
    )


def _assert_identity_and_key() -> None:
    base = _identity()
    first = cache_identity_key(base)
    second = cache_identity_key(base)
    _require(first == second, "cache identity key is nondeterministic")
    _require(len(first) == 64 and first == first.lower(), "cache key shape changed")

    variants = (
        _identity(layer_id="resonance"),
        _identity(artifact_kind="tokens"),
        _identity(owner="language.lexer"),
        _identity(subject="src/other.apex"),
        _identity(input_payload=b"source-2"),
        _identity(configuration_payload=b"config-2"),
    )
    for variant in variants:
        _require(
            cache_identity_key(variant) != first,
            "structured identity field failed to affect cache key",
        )

    dep_a = CacheDependency(
        cache_key=first,
        fingerprint=cache_fingerprint(b"dep-a"),
    )
    dep_b_identity = _identity(subject="src/dep.apex")
    dep_b = CacheDependency(
        cache_key=cache_identity_key(dep_b_identity),
        fingerprint=cache_fingerprint(b"dep-b"),
    )

    ordered = _identity(
        layer_id="resonance",
        artifact_kind="ast",
        dependencies=(dep_a, dep_b),
    )
    reversed_dependencies = _identity(
        layer_id="resonance",
        artifact_kind="ast",
        dependencies=(dep_b, dep_a),
    )
    _require(
        cache_identity_key(ordered) != cache_identity_key(reversed_dependencies),
        "ordered dependencies stopped affecting identity",
    )
    _require(
        ordered.dependencies[0] is dep_a and ordered.dependencies[1] is dep_b,
        "dependency references/order were rewritten",
    )

    _expect(
        ValueError,
        lambda: _identity(dependencies=(dep_a, dep_a)),
    )
    _expect(
        TypeError,
        lambda: CacheIdentity(
            schema_version=True,
            layer_id="capture",
            artifact_kind="document",
            owner="owner",
            subject="subject",
            input_fingerprint=cache_fingerprint(b"a"),
            configuration_fingerprint=cache_fingerprint(b"b"),
        ),
    )
    _expect(ValueError, lambda: _identity(layer_id="unknown"))
    _expect(ValueError, lambda: _identity(subject=" subject"))
    _expect(TypeError, lambda: cache_identity_key(object()))


def _assert_entry_reference_preservation() -> None:
    identity = _identity()
    payload = ("owner-produced", object())
    fingerprint = cache_fingerprint(b"artifact")
    entry = CacheEntry(identity, fingerprint, payload)

    _require(entry.identity is identity, "entry identity reference was replaced")
    _require(
        entry.artifact_fingerprint is fingerprint,
        "entry artifact fingerprint reference was replaced",
    )
    _require(entry.value is payload, "owner payload reference was replaced")
    _require(entry.cache_key == cache_identity_key(identity), "entry key changed")

    _expect(
        FrozenInstanceError,
        lambda: setattr(entry, "value", None),
    )
    _expect(TypeError, lambda: CacheEntry(object(), fingerprint, payload))


def _assert_no_operational_or_semantic_ownership() -> None:
    model_path = _root() / "apexforge" / "incremental_cache" / "model.py"
    source = model_path.read_text(encoding="utf-8")

    forbidden = (
        "ProjectBuilder",
        "build_project",
        "RuntimeEngine",
        "load_project",
        "parse(",
        "lex(",
        "audit_trace_map",
        "tap_check",
        "sqlite",
        "pickle",
        "shelve",
        "time.",
        "datetime",
        "mtime",
        "random",
        "tempfile",
        "Path(",
        "open(",
    )
    for token in forbidden:
        _require(
            token not in source,
            "minimal cache model acquired forbidden behavior: " + token,
        )


def _assert_predecessor_owners_unchanged() -> None:
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
    _require(diff.returncode == 0, "P11.12B mutated predecessor semantic owners")


def main() -> None:
    _assert_predecessor()
    _assert_public_model()
    _assert_fingerprints()
    _assert_identity_and_key()
    _assert_entry_reference_preservation()
    _assert_no_operational_or_semantic_ownership()
    _assert_predecessor_owners_unchanged()

    print("P11_12A_FREEZE_ANCESTRY=PASS")
    print("CACHE_SCHEMA_VERSION=1")
    print("CACHE_LAYER_COUNT=3")
    print("CACHE_LAYER_IDS=capture,resonance,stability")
    print("CACHE_FINGERPRINT_ALGORITHM=sha256")
    print("CACHE_PUBLIC_SYMBOL_COUNT=9")
    print("CACHE_IMMUTABLE_MODEL_TYPES=4")
    print("CACHE_FINGERPRINT_EXACT_BYTES=PASS")
    print("CACHE_STRUCTURED_IDENTITY=PASS")
    print("CACHE_IDENTITY_KEY=DETERMINISTIC_SHA256")
    print("CACHE_DEPENDENCY_ORDER=PRESERVED")
    print("CACHE_DUPLICATE_DEPENDENCY_KEYS=REJECTED")
    print("CACHE_ENTRY_OWNER_VALUE_REFERENCE=PRESERVED")
    print("TIMESTAMP_CORRECTNESS=NONE")
    print("PERSISTENCE=NONE")
    print("LOOKUP_OR_STORE=NONE")
    print("PROJECT_BUILDING=NONE")
    print("SEMANTIC_EVALUATION=NONE")
    print("RUNTIME_EXECUTION=NONE")
    print("PREDECESSOR_OWNER_MUTATION=NONE")
    print("P11_12B_MINIMAL_IMMUTABLE_INCREMENTAL_CACHE_MODEL=PASS")


if __name__ == "__main__":
    main()