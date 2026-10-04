"""P14.10 structural observations and declarative migration; no solving or execution."""
from dataclasses import dataclass
from hashlib import sha256
import json

from tooling.package_manifest import PackageManifest, SCHEMA as MANIFEST_SCHEMA
from tooling.package_solver import ResolutionGraph, ResolvedPackage
from tooling.package_lock import PackageLock
from tooling.package_namespace import PackageExportIndex

SCHEMA = "apexforge.package-compatibility/v1"
IDENTICAL = "IDENTICAL_CONTRACT"
ADDITIVE = "COMPATIBLE_ADDITIVE"
BREAKING = "BREAKING_STRUCTURAL_CHANGE"
UNKNOWN = "COMPATIBILITY_UNKNOWN"
INCOMPATIBLE = "INCOMPATIBLE_SCHEMA"
FAMILY_CHANGED = "PACKAGE_IDENTITY_FAMILY_CHANGED"


class CompatibilityError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(value, code):
    if not value:
        raise CompatibilityError(code)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _fingerprint(domain, record):
    return sha256((domain + "\0" + _json(record)).encode("utf-8")).hexdigest().upper()


def _reference(manifest):
    return {"coordinate": manifest.coordinate.record(), "content_identity": manifest.content_identity().record()}


def _classification(changes):
    for status in (FAMILY_CHANGED, INCOMPATIBLE, BREAKING, UNKNOWN, ADDITIVE):
        if any(c.classification == status for c in changes):
            return status
    return IDENTICAL


@dataclass(frozen=True)
class PackageChange:
    dimension: str
    reason: str
    classification: str
    old_json: str
    new_json: str

    def record(self):
        return {"dimension": self.dimension, "reason": self.reason, "classification": self.classification,
                "old": json.loads(self.old_json), "new": json.loads(self.new_json)}


@dataclass(frozen=True)
class CompatibilityReport:
    old: PackageManifest
    new: PackageManifest
    changes: tuple[PackageChange, ...]

    @property
    def classification(self):
        return _classification(self.changes)

    @property
    def structurally_compatible(self):
        return self.classification in (IDENTICAL, ADDITIVE)

    def canonical_record(self):
        dimensions = ("family", "schema", "exports", "dependencies", "required_capabilities",
                      "provided_capabilities", "tier", "entrypoints", "content", "documents")
        return {"schema": SCHEMA, "old": _reference(self.old), "new": _reference(self.new),
            "classification": self.classification, "structurally_compatible": self.structurally_compatible,
            "behavioral_equivalence": "NOT_ESTABLISHED", "trust": "NOT_EVALUATED",
            "provenance": {"old": [p.record() for p in self.old.provenance],
                           "new": [p.record() for p in self.new.provenance]},
            "dimensions": [{"dimension": d, "classification": _classification(tuple(
                c for c in self.changes if c.dimension == d))} for d in dimensions],
            "changes": [c.record() for c in self.changes]}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _fingerprint(SCHEMA, self.canonical_record())


def compare_packages(old, new, old_exports=None, new_exports=None):
    """Compare declared structure; supplied P14.4 indexes admit canonical export evidence."""
    _require(type(old) is PackageManifest and type(new) is PackageManifest, "COMPATIBILITY_INPUT_INVALID")
    changes = []
    def change(dimension, reason, status, before, after):
        changes.append(PackageChange(dimension, reason, status, _json(before), _json(after)))
    if (old.coordinate.namespace, old.coordinate.name) != (new.coordinate.namespace, new.coordinate.name):
        change("family", "IDENTITY_FAMILY_CHANGED", FAMILY_CHANGED,
               [old.coordinate.namespace, old.coordinate.name], [new.coordinate.namespace, new.coordinate.name])
    if old.coordinate.schema != MANIFEST_SCHEMA or new.coordinate.schema != MANIFEST_SCHEMA:
        change("schema", "MANIFEST_SCHEMA_UNSUPPORTED", INCOMPATIBLE, old.coordinate.schema, new.coordinate.schema)
        return CompatibilityReport(old, new, tuple(sorted(changes, key=lambda c: _json(c.record()))))
    for manifest, index in ((old, old_exports), (new, new_exports)):
        if index is not None:
            _require(type(index) is PackageExportIndex and index.provider == ResolvedPackage(manifest),
                     "EXPORT_EVIDENCE_CONTENT_MISMATCH")
    if (old.exports and old_exports is None) or (new.exports and new_exports is None):
        change("exports", "CANONICAL_EXPORT_EVIDENCE_MISSING", UNKNOWN,
               [s.record() for s in old.exports], [s.record() for s in new.exports])
    def symbols(field):
        before, after = getattr(old, field), getattr(new, field)
        _require(len({s.identity for s in before}) == len(before) and len({s.identity for s in after}) == len(after),
                 "SYMBOL_EXPORT_NAME_COLLISION")
        a, b = {s.identity: s for s in before}, {s.identity: s for s in after}
        for key in sorted(a.keys() | b.keys()):
            if key not in a:
                change(field, "DECLARATION_ADDED", ADDITIVE, None, b[key].record())
            elif key not in b:
                change(field, "DECLARATION_REMOVED", BREAKING, a[key].record(), None)
            elif a[key] != b[key]:
                change(field, "DECLARATION_RETARGETED", BREAKING, a[key].record(), b[key].record())
    symbols("exports")
    symbols("entrypoints")
    for field, dimension, add_status, remove_status in (
        ("required_capabilities", "required_capabilities", BREAKING, ADDITIVE),
        ("exported_capabilities", "provided_capabilities", ADDITIVE, BREAKING)):
        a, b = set(getattr(old, field)), set(getattr(new, field))
        for capability in sorted(b-a):
            change(dimension, "CAPABILITY_ADDED", add_status, None, capability)
        for capability in sorted(a-b):
            change(dimension, "CAPABILITY_REMOVED", remove_status, capability, None)
    a = {(c.namespace, c.name): c for c in old.dependencies}
    b = {(c.namespace, c.name): c for c in new.dependencies}
    for key in sorted(a.keys() | b.keys()):
        if key not in a:
            change("dependencies", "REQUIRED_DEPENDENCY_ADDED", BREAKING, None, b[key].record())
        elif key not in b:
            change("dependencies", "REQUIRED_DEPENDENCY_REMOVED", ADDITIVE, a[key].record(), None)
        elif a[key] != b[key]:
            change("dependencies", "EXACT_DEPENDENCY_CHANGED", UNKNOWN, a[key].record(), b[key].record())
    if old.tier != new.tier:
        change("tier", "PACKAGE_TIER_CHANGED", BREAKING,
               None if old.tier is None else old.tier.value, None if new.tier is None else new.tier.value)
    if old.content != new.content:
        change("content", "CONTENT_BEHAVIOR_NOT_ESTABLISHED", UNKNOWN,
               [c.record() for c in old.content], [c.record() for c in new.content])
    if old.documents != new.documents:
        change("documents", "DOCUMENT_ORDER_CONTRACT_CHANGED", UNKNOWN,
               [p.value for p in old.documents], [p.value for p in new.documents])
    return CompatibilityReport(old, new, tuple(sorted(changes, key=lambda c: _json(c.record()))))


@dataclass(frozen=True)
class MigrationStep:
    consumer_json: str
    obligation: str
    reason: str
    subject_json: str

    def record(self):
        return {"consumer": json.loads(self.consumer_json), "obligation": self.obligation,
            "reason": self.reason, "subject": json.loads(self.subject_json),
            "automation": "MANUAL_OR_EXTERNAL_ACTION_REQUIRED"}


@dataclass(frozen=True)
class MigrationPlan:
    report: CompatibilityReport
    directly_affected: tuple[ResolvedPackage, ...]
    transitively_exposed: tuple[ResolvedPackage, ...]
    steps: tuple[MigrationStep, ...]
    lock_refresh_required: bool
    graph_fingerprint: str | None
    lock_fingerprint: str | None

    def canonical_record(self):
        return {"schema": "apexforge.package-migration/v1", "compatibility": self.report.canonical_record(),
            "directly_affected": [n.reference() for n in self.directly_affected],
            "transitively_exposed": [n.reference() for n in self.transitively_exposed],
            "steps": [s.record() for s in self.steps], "lock_refresh_required": self.lock_refresh_required,
            "graph_fingerprint": self.graph_fingerprint, "lock_fingerprint": self.lock_fingerprint,
            "executes_migration": False}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _fingerprint("apexforge.package-migration/v1", self.canonical_record())


def plan_migration(old, new, graph=None, lock=None, old_exports=None, new_exports=None):
    report = compare_packages(old, new, old_exports, new_exports)
    _require(graph is None or type(graph) is ResolutionGraph, "MIGRATION_GRAPH_INVALID")
    _require(lock is None or type(lock) is PackageLock, "MIGRATION_LOCK_INVALID")
    old_identity = old.content_identity()
    direct, transitive = (), ()
    if graph is not None:
        nodes = {n.coordinate: n for n in graph.nodes}
        _require(old.coordinate in nodes and nodes[old.coordinate].content_identity == old_identity,
                 "MIGRATION_OLD_GRAPH_BINDING_MISMATCH")
        reverse = {c: set() for c in nodes}
        for edge in graph.edges:
            reverse[edge.required].add(edge.requiring)
        direct_keys = reverse[old.coordinate]
        reached, pending = set(direct_keys), list(direct_keys)
        while pending:
            for parent in reverse[pending.pop()]:
                if parent not in reached:
                    reached.add(parent)
                    pending.append(parent)
        key = lambda c: _json(nodes[c].reference())
        direct = tuple(nodes[c] for c in sorted(direct_keys, key=key))
        transitive = tuple(nodes[c] for c in sorted(reached-direct_keys, key=key))
    locked = False
    if lock is not None:
        if graph is not None:
            _require(lock.resolution == graph, "MIGRATION_LOCK_GRAPH_MISMATCH")
        for node in lock.resolution.nodes:
            if node.coordinate == old.coordinate:
                _require(node.content_identity == old_identity, "MIGRATION_OLD_LOCK_BINDING_MISMATCH")
                locked = True
    refresh = locked and old_identity != new.content_identity()
    steps = []
    def step(consumer, obligation, reason, subject):
        steps.append(MigrationStep(_json(consumer), obligation, reason, _json(subject)))
    changed = old_identity != new.content_identity()
    if changed:
        step(None, "VERIFY_TARGET_TRUST_SEPARATELY", "TRUST_NOT_COMPATIBILITY", _reference(new))
    if changed and old.coordinate == new.coordinate:
        step(None, "REQUIRE_DISTINCT_PUBLICATION_COORDINATE", "IMMUTABLE_PUBLISHED_COORDINATE", _reference(new))
    if report.classification == FAMILY_CHANGED:
        step(None, "REVIEW_IDENTITY_FAMILY_CHANGE", "RENAME_NOT_IMPLEMENTED", _reference(new))
    for consumer in direct:
        if old.coordinate != new.coordinate:
            step(consumer.reference(), "UPDATE_EXACT_DEPENDENCY", "CALLER_SUPPLIED_TARGET", new.coordinate.record())
        if changed:
            step(consumer.reference(), "SOLVE_AND_VALIDATE_EXTERNALLY", "NEW_GRAPH_NOT_COMPUTED", _reference(new))
        for change in report.changes:
            step(consumer.reference(), "REVIEW_" + change.dimension.upper(), change.reason, change.record())
    if refresh:
        step(None, "REFRESH_LOCK_EXTERNALLY", "LOCKED_CONTENT_CHANGED", _reference(new))
    return MigrationPlan(report, direct, transitive, tuple(sorted(steps, key=lambda s: _json(s.record()))),
                         refresh, None if graph is None else graph.fingerprint(),
                         None if lock is None else lock.fingerprint())
