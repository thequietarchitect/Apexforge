"""P14.4 structural package export addressing; language identities remain unchanged."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re

from tooling.package_manifest import PackageCoordinate, SymbolReference
from tooling.package_solver import ResolvedPackage, ResolutionGraph, ResolutionEdge
from tooling.package_lock import PackageLock

SCHEMA = "apexforge.package-exports/v1"
TRANSITIVE_VISIBILITY = "DIRECT_ONLY"


class PackageNamespaceError(ValueError):
    def __init__(self, code, candidates=()):
        self.code = code
        self.candidates = tuple(sorted(candidates))
        super().__init__(code)


def _require(ok, code):
    if not ok:
        raise PackageNamespaceError(code)


def _json(record):
    return json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def _fingerprint(domain, record):
    return sha256((domain + "\0" + _json(record)).encode("utf-8")).hexdigest().upper()


def _name(value):
    _require(type(value) is str and len(value) <= 256 and
        re.fullmatch(r"(?:directive|function):[A-Za-z_][A-Za-z0-9_]*", value) is not None,
        "EXPORT_NAME_INVALID")


@dataclass(frozen=True)
class PackageExportIndex:
    """Caller supplies canonical references owned by this exact package, including private ones.

    This is evidence admission, not compilation or authentication of producer claims.
    Export keys retain the P14.1 current AIR ID spelling; no new alias syntax.
    """
    provider: ResolvedPackage
    declarations: tuple[SymbolReference, ...]

    def __post_init__(self):
        _require(type(self.provider) is ResolvedPackage, "EXPORT_PROVIDER_INVALID")
        _require(type(self.declarations) is tuple and all(type(x) is SymbolReference
                 for x in self.declarations), "EXPORT_EVIDENCE_INVALID")
        _require(len(set(self.declarations)) == len(self.declarations), "EXPORT_EVIDENCE_DUPLICATE")
        exports = self.provider.manifest.exports
        _require(all(x in self.declarations for x in exports), "EXPORT_DECLARATION_MISSING")
        _require(len({x.identity for x in exports}) == len(exports), "EXPORT_NAME_COLLISION")
        object.__setattr__(self, "declarations", tuple(sorted(self.declarations,
            key=lambda x: _json(x.record()))))

    def canonical_record(self):
        return {"schema": SCHEMA, "provider": self.provider.reference(),
            "exports": [{"export_name": x.identity, "symbol": x.record()}
                        for x in sorted(self.provider.manifest.exports, key=lambda x: x.identity)],
            "provenance": [p.record() for p in self.provider.manifest.provenance]}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _fingerprint("apexforge.package-export-index-fingerprint/v1", self.canonical_record())


@dataclass(frozen=True)
class PackageSymbolReference:
    export_name: str
    provider: PackageCoordinate | None = None

    def __post_init__(self):
        _name(self.export_name)
        _require(self.provider is None or type(self.provider) is PackageCoordinate,
                 "EXPORT_QUALIFIER_INVALID")


@dataclass(frozen=True)
class ResolvedExportBinding:
    consumer: ResolvedPackage
    index: PackageExportIndex
    symbol: SymbolReference
    dependency: ResolutionEdge
    lock: PackageLock | None = None

    def __post_init__(self):
        _require(type(self.consumer) is ResolvedPackage and type(self.index) is PackageExportIndex
            and type(self.symbol) is SymbolReference and type(self.dependency) is ResolutionEdge,
            "EXPORT_BINDING_INVALID")
        provider = self.index.provider
        _require(self.symbol in provider.manifest.exports and self.symbol in self.index.declarations
            and provider.coordinate in self.consumer.manifest.dependencies, "EXPORT_BINDING_INVALID")
        expected = ResolutionEdge(self.consumer.coordinate, self.consumer.content_identity,
                                  provider.coordinate, provider.content_identity)
        _require(self.dependency == expected, "EXPORT_BINDING_INVALID")
        if self.lock is not None:
            _require(type(self.lock) is PackageLock and self.consumer in self.lock.resolution.nodes
                and provider in self.lock.resolution.nodes and self.dependency in self.lock.resolution.edges,
                "EXPORT_LOCK_BINDING_MISMATCH")

    @property
    def export_name(self):
        return self.symbol.identity

    def canonical_record(self):
        return {"schema": "apexforge.package-symbol-binding/v1",
            "consumer": self.consumer.reference(), "provider": self.index.provider.reference(),
            "export_name": self.export_name, "symbol": self.symbol.record(),
            "dependency": self.dependency.record(), "export_index_fingerprint": self.index.fingerprint(),
            "lock_fingerprint": None if self.lock is None else self.lock.fingerprint(),
            "provenance": [p.record() for p in self.index.provider.manifest.provenance]}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _fingerprint("apexforge.package-symbol-binding-fingerprint/v1", self.canonical_record())


@dataclass(frozen=True)
class PackageNamespace:
    graph: ResolutionGraph
    indexes: tuple[PackageExportIndex, ...]
    lock: PackageLock | None = None

    def __post_init__(self):
        _require(type(self.graph) is ResolutionGraph, "EXPORT_GRAPH_INVALID")
        # The existing validator owns closure/edge/cycle semantics; no solving is performed.
        ResolutionGraph(self.graph.root, self.graph.root_content, self.graph.nodes,
                        self.graph.edges, self.graph.schema)
        _require(type(self.indexes) is tuple and all(type(x) is PackageExportIndex for x in self.indexes),
                 "EXPORT_INDEX_INVALID")
        _require(len({x.provider.coordinate for x in self.indexes}) == len(self.indexes),
                 "EXPORT_INDEX_DUPLICATE")
        nodes = {n.coordinate: n for n in self.graph.nodes}
        for index in self.indexes:
            _require(nodes.get(index.provider.coordinate) == index.provider, "EXPORT_PROVIDER_CONTENT_MISMATCH")
        _require(all(not n.manifest.exports or any(i.provider == n for i in self.indexes)
                     for n in self.graph.nodes), "EXPORT_INDEX_MISSING")
        # Supplied ownership evidence cannot assign the same exact AIR declaration to two packages.
        owners = {}
        for index in self.indexes:
            for symbol in index.declarations:
                _require(symbol not in owners, "EXPORT_DECLARATION_OWNERSHIP_CONFLICT")
                owners[symbol] = index.provider.coordinate
        if self.lock is not None:
            _require(type(self.lock) is PackageLock and self.lock.resolution == self.graph,
                     "EXPORT_LOCK_BINDING_MISMATCH")
        object.__setattr__(self, "indexes", tuple(sorted(self.indexes, key=lambda x: _json(x.provider.reference()))))

    def resolve(self, consumer, reference):
        _require(type(consumer) is PackageCoordinate and type(reference) is PackageSymbolReference,
                 "EXPORT_LOOKUP_INVALID")
        nodes = {n.coordinate: n for n in self.graph.nodes}
        _require(consumer in nodes, "EXPORT_CONSUMER_UNKNOWN")
        permitted = nodes[consumer].manifest.dependencies
        if reference.provider is not None:
            _require(reference.provider in permitted, "EXPORT_PROVIDER_NOT_VISIBLE")
        matches = []
        for index in self.indexes:
            if index.provider.coordinate not in permitted or (reference.provider is not None
                    and index.provider.coordinate != reference.provider):
                continue
            for symbol in index.provider.manifest.exports:
                if symbol.identity == reference.export_name:
                    matches.append((index, symbol))
        _require(bool(matches), "EXPORT_NOT_FOUND")
        if len(matches) > 1:
            raise PackageNamespaceError("EXPORT_AMBIGUOUS", tuple(_json(i.provider.reference()) for i, _ in matches))
        index, symbol = matches[0]
        dependency = next(e for e in self.graph.edges
                          if e.requiring == consumer and e.required == index.provider.coordinate)
        return ResolvedExportBinding(nodes[consumer], index, symbol, dependency, self.lock)
