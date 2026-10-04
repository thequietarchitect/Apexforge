"""P14.5 exact structural capability compatibility, never runtime permission."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling.package_solver import ResolvedPackage, ResolutionGraph, ResolutionEdge
from tooling.package_lock import PackageLock

SCHEMA = "apexforge.package-capability-compatibility/v1"
PROVIDER_VISIBILITY = "DIRECT_ONLY"
MATCHING = "EXACT_IDENTITY"


class PackageCapabilityError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageCapabilityError(code)


def _capability(value):
    # Same exact ASCII qualified identifier admitted by P14.1; no new permission identity.
    _require(type(value) is str and len(value) <= 256 and re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*", value) is not None,
        "CAPABILITY_REFERENCE_INVALID")


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _key(package):
    c = package.coordinate
    return (c.namespace, c.name, c.version.major, c.version.minor, c.version.patch,
            c.schema, package.content_identity.fingerprint)


@dataclass(frozen=True)
class CapabilityBinding:
    consumer: ResolvedPackage
    capability: str
    provider: ResolvedPackage
    dependency: ResolutionEdge

    def __post_init__(self):
        _capability(self.capability)
        _require(type(self.consumer) is ResolvedPackage and type(self.provider) is ResolvedPackage
            and type(self.dependency) is ResolutionEdge, "CAPABILITY_BINDING_INVALID")
        _require(self.capability in self.consumer.manifest.required_capabilities
            and self.capability in self.provider.manifest.exported_capabilities
            and self.provider.coordinate in self.consumer.manifest.dependencies,
            "CAPABILITY_BINDING_INVALID")
        _require(self.dependency == ResolutionEdge(self.consumer.coordinate, self.consumer.content_identity,
            self.provider.coordinate, self.provider.content_identity), "CAPABILITY_BINDING_INVALID")

    def record(self):
        return {"consumer": self.consumer.reference(), "capability": self.capability,
            "provider": self.provider.reference(), "dependency": self.dependency.record(),
            "consumer_provenance": [r.record() for r in self.consumer.manifest.provenance],
            "provider_provenance": [r.record() for r in self.provider.manifest.provenance],
            "provider_declaration": {"package": self.provider.reference(), "exports": self.capability}}


@dataclass(frozen=True)
class CapabilityDiagnostic:
    code: str
    consumer: ResolvedPackage
    capability: str
    providers: tuple[ResolvedPackage, ...] = ()

    def __post_init__(self):
        _capability(self.capability)
        _require(self.code in ("MISSING_REQUIRED_CAPABILITY", "AMBIGUOUS_CAPABILITY_PROVIDER",
            "CAPABILITY_PROVIDER_NOT_VISIBLE", "CAPABILITY_SELF_PROVIDER_NOT_ALLOWED")
            and type(self.consumer) is ResolvedPackage and type(self.providers) is tuple
            and all(type(p) is ResolvedPackage for p in self.providers), "CAPABILITY_DIAGNOSTIC_INVALID")
        _require(self.capability in self.consumer.manifest.required_capabilities
            and all(self.capability in p.manifest.exported_capabilities for p in self.providers)
            and len(set(self.providers)) == len(self.providers), "CAPABILITY_DIAGNOSTIC_INVALID")
        object.__setattr__(self, "providers", tuple(sorted(self.providers, key=_key)))

    def record(self):
        return {"code": self.code, "consumer": self.consumer.reference(), "capability": self.capability,
                "providers": [p.reference() for p in self.providers]}


def _matrix(graph):
    nodes = {n.coordinate: n for n in graph.nodes}
    edges = {(e.requiring, e.required): e for e in graph.edges}
    provider_index = {}
    for node in graph.nodes:
        for capability in node.manifest.exported_capabilities:
            provider_index.setdefault(capability, []).append(node)
    bindings, diagnostics = [], []
    for consumer in graph.nodes:
        for capability in consumer.manifest.required_capabilities:
            _capability(capability)
            providers = tuple(provider_index.get(capability, ()))
            visible = tuple(p for p in providers if p.coordinate in consumer.manifest.dependencies)
            if len(visible) == 1:
                provider = visible[0]
                bindings.append(CapabilityBinding(consumer, capability, provider,
                    edges[(consumer.coordinate, provider.coordinate)]))
            elif len(visible) > 1:
                diagnostics.append(CapabilityDiagnostic("AMBIGUOUS_CAPABILITY_PROVIDER", consumer,
                                                        capability, visible))
            else:
                others = tuple(p for p in providers if p != consumer)
                code = ("CAPABILITY_PROVIDER_NOT_VISIBLE" if others else
                    "CAPABILITY_SELF_PROVIDER_NOT_ALLOWED" if consumer in providers else
                    "MISSING_REQUIRED_CAPABILITY")
                diagnostics.append(CapabilityDiagnostic(code, consumer, capability, providers))
    return tuple(bindings), tuple(diagnostics)


@dataclass(frozen=True)
class CapabilityCompatibilityResult:
    graph: ResolutionGraph
    bindings: tuple[CapabilityBinding, ...]
    diagnostics: tuple[CapabilityDiagnostic, ...]
    lock: PackageLock | None = None

    def __post_init__(self):
        _require(type(self.graph) is ResolutionGraph, "CAPABILITY_GRAPH_INVALID")
        ResolutionGraph(self.graph.root, self.graph.root_content, self.graph.nodes,
                        self.graph.edges, self.graph.schema)
        _require(type(self.bindings) is tuple and all(type(b) is CapabilityBinding for b in self.bindings)
            and type(self.diagnostics) is tuple and all(type(d) is CapabilityDiagnostic for d in self.diagnostics),
            "CAPABILITY_RESULT_INVALID")
        _require((self.bindings, self.diagnostics) == _matrix(self.graph), "CAPABILITY_RESULT_INVALID")
        if self.lock is not None:
            _require(type(self.lock) is PackageLock and self.lock.resolution == self.graph,
                     "CAPABILITY_LOCK_BINDING_MISMATCH")

    @property
    def compatible(self):
        return not self.diagnostics

    def canonical_record(self):
        return {"schema": SCHEMA, "graph_fingerprint": self.graph.fingerprint(),
            "lock_fingerprint": None if self.lock is None else self.lock.fingerprint(),
            "compatible": self.compatible, "matching": MATCHING, "provider_visibility": PROVIDER_VISIBILITY,
            "providers": [{"package": n.reference(), "capabilities": list(n.manifest.exported_capabilities)}
                          for n in self.graph.nodes if n.manifest.exported_capabilities],
            "bindings": [b.record() for b in self.bindings],
            "diagnostics": [d.record() for d in self.diagnostics],
            "grants_authority": False, "validates_trust": False}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return sha256((SCHEMA + "\0" + self.canonical_json()).encode("utf-8")).hexdigest().upper()


def validate_capabilities(graph, lock=None):
    """All graph requirements, including dependency packages; unresolved means incompatible."""
    _require(type(graph) is ResolutionGraph, "CAPABILITY_GRAPH_INVALID")
    checked = ResolutionGraph(graph.root, graph.root_content, graph.nodes, graph.edges, graph.schema)
    if lock is not None:
        _require(type(lock) is PackageLock and lock.resolution == checked, "CAPABILITY_LOCK_BINDING_MISMATCH")
    bindings, diagnostics = _matrix(checked)
    return CapabilityCompatibilityResult(checked, bindings, diagnostics, lock)
