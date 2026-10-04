"""P14.3 immutable locks and exact supplied-content restore plans; no execution or IO."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from tooling.package_manifest import (PackageManifest, PackageCoordinate,
    PackageContentIdentity, PackageManifestError)
from tooling.package_solver import (ResolutionGraph, ResolvedPackage, ResolutionEdge,
    PackageUniverse, PackageSolverError, SCHEMA as SOLVER_SCHEMA)

SCHEMA = "apexforge.package-lock/v1"
FINGERPRINT_DOMAIN = "apexforge.package-lock-fingerprint/v1"
MAX_JSON_BYTES = 16 * 1024 * 1024


class PackageLockError(ValueError):
    """Fixed diagnostic code; never a usable partial plan or untrusted payload echo."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code="LOCK_RECORD_INVALID"):
    if not ok:
        raise PackageLockError(code)


def _object(value, keys):
    _require(type(value) is dict and set(value) == set(keys))
    return value


def _array(value):
    _require(type(value) is list)
    return value


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def _content(value):
    v = _object(value, ("domain", "fingerprint"))
    return PackageContentIdentity(v["fingerprint"], v["domain"])


def _graph(value):
    v = _object(value, ("schema", "root", "root_content", "nodes", "edges", "capabilities"))
    _require(v["schema"] == SOLVER_SCHEMA, "LOCK_SOLVER_SCHEMA_UNSUPPORTED")
    root = PackageCoordinate.from_mapping(v["root"])
    nodes = []
    for raw in _array(v["nodes"]):
        n = _object(raw, ("coordinate", "content_identity", "manifest", "role"))
        node = ResolvedPackage(PackageManifest.from_mapping(n["manifest"]))
        _require(n["manifest"] == node.manifest.canonical_record(), "LOCK_MANIFEST_NONCANONICAL")
        _require(PackageCoordinate.from_mapping(n["coordinate"]) == node.coordinate
            and _content(n["content_identity"]) == node.content_identity, "LOCK_NODE_IDENTITY_MISMATCH")
        _require(n["role"] == ("root" if node.coordinate == root else "dependency"))
        nodes.append(node)
    edges = []
    for raw in _array(v["edges"]):
        e = _object(raw, ("requiring", "requiring_content", "required", "required_content",
                          "declaration_fingerprint"))
        edge = ResolutionEdge(PackageCoordinate.from_mapping(e["requiring"]),
            _content(e["requiring_content"]), PackageCoordinate.from_mapping(e["required"]),
            _content(e["required_content"]))
        _require(e["declaration_fingerprint"] == edge.declaration_fingerprint(),
                 "LOCK_DECLARATION_MISMATCH")
        edges.append(edge)
    graph = ResolutionGraph(root, _content(v["root_content"]), tuple(nodes), tuple(edges))
    _require(v["capabilities"] == graph.canonical_record()["capabilities"])
    return graph


@dataclass(frozen=True)
class PackageLock:
    resolution: ResolutionGraph
    schema: str = SCHEMA

    def __post_init__(self):
        _require(type(self.schema) is str and self.schema == SCHEMA, "LOCK_SCHEMA_UNSUPPORTED")
        _require(type(self.resolution) is ResolutionGraph, "LOCK_SUCCESSFUL_RESOLUTION_REQUIRED")
        g = self.resolution
        try:
            # Validate supplied typed graphs too; do not trust a forged/deserialized instance.
            checked = ResolutionGraph(g.root, g.root_content, g.nodes, g.edges, g.schema)
        except PackageSolverError as exc:
            raise PackageLockError("LOCK_GRAPH_INVALID") from exc
        object.__setattr__(self, "resolution", checked)

    def canonical_record(self):
        return {"schema": self.schema, "solver_schema": SOLVER_SCHEMA,
            "resolution_fingerprint": self.resolution.fingerprint(),
            "resolution": self.resolution.canonical_record()}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return sha256((FINGERPRINT_DOMAIN + "\0" + self.canonical_json()).encode("utf-8")).hexdigest().upper()

    @classmethod
    def from_mapping(cls, value):
        try:
            v = _object(value, ("schema", "solver_schema", "resolution_fingerprint", "resolution"))
            _require(v["schema"] == SCHEMA, "LOCK_SCHEMA_UNSUPPORTED")
            _require(v["solver_schema"] == SOLVER_SCHEMA, "LOCK_SOLVER_SCHEMA_UNSUPPORTED")
            result = cls(_graph(v["resolution"]))
            _require(v["resolution_fingerprint"] == result.resolution.fingerprint(),
                     "LOCK_RESOLUTION_FINGERPRINT_MISMATCH")
            return result
        except PackageManifestError as exc:
            raise PackageLockError("LOCK_PACKAGE_RECORD_INVALID") from exc
        except PackageSolverError as exc:
            raise PackageLockError("LOCK_GRAPH_INVALID") from exc


def parse_lock(text):
    """Bounded supplied JSON, matching P14.1's duplicate/nonfinite/integer safeguards."""
    _require(type(text) is str, "LOCK_JSON_INVALID")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "LOCK_JSON_DUPLICATE_KEY")
            result[key] = value
        return result
    def reject(_):
        raise PackageLockError("LOCK_JSON_INVALID")
    def integer(raw):
        _require(len(raw.lstrip("-")) <= 10, "LOCK_JSON_INVALID")
        return int(raw)
    try:
        _require(len(text.encode("utf-8")) <= MAX_JSON_BYTES, "LOCK_JSON_TOO_LARGE")
        return PackageLock.from_mapping(json.loads(text, object_pairs_hook=pairs,
            parse_constant=reject, parse_int=integer))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise PackageLockError("LOCK_JSON_INVALID") from exc


def validate_lock_against_root(root, lock):
    _require(type(root) is PackageManifest and type(lock) is PackageLock, "LOCK_ROOT_BINDING_INVALID")
    _require(root.coordinate == lock.resolution.root, "LOCK_ROOT_COORDINATE_DRIFT")
    _require(root.content_identity() == lock.resolution.root_content, "LOCK_ROOT_CONTENT_DRIFT")
    # Content identity includes declarations; graph validation already binds every edge to them.
    return True


@dataclass(frozen=True)
class RestorePlan:
    lock: PackageLock
    packages: tuple[ResolvedPackage, ...]

    def __post_init__(self):
        _require(type(self.lock) is PackageLock and type(self.packages) is tuple
            and all(type(n) is ResolvedPackage for n in self.packages), "RESTORE_PLAN_INVALID")
        _require(self.packages == self.lock.resolution.nodes, "RESTORE_PLAN_INVALID")

    def canonical_record(self):
        return {"schema": "apexforge.package-restore-plan/v1", "lock_fingerprint": self.lock.fingerprint(),
            "root": self.lock.resolution.root.record(),
            "root_content": self.lock.resolution.root_content.record(),
            "packages": [n.reference() for n in self.packages],
            "verification": "exact_supplied_identity_match", "installs_packages": False}

    def canonical_json(self):
        return _json(self.canonical_record())


def plan_restore(lock, universe):
    _require(type(lock) is PackageLock and type(universe) is PackageUniverse, "RESTORE_INPUT_INVALID")
    # Revalidate explicit candidates, preserving the universe's global ambiguity rejection.
    try:
        checked = PackageUniverse(universe.candidates)
    except PackageSolverError as exc:
        raise PackageLockError("RESTORE_UNIVERSE_AMBIGUOUS") from exc
    supplied = {m.coordinate: ResolvedPackage(m) for m in checked.candidates}
    for locked in lock.resolution.nodes:
        candidate = supplied.get(locked.coordinate)
        _require(candidate is not None, "RESTORE_CONTENT_MISSING")
        _require(candidate == locked, "RESTORE_CONTENT_SUBSTITUTED")
    return RestorePlan(lock, lock.resolution.nodes)
