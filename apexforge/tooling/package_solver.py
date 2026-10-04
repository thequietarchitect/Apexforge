"""P14.2 exact dependency closure over supplied immutable package declarations.

No discovery, parsing, version precedence, trust, materialization or execution.
All failures raise a structured diagnostic, never a usable partial graph.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import heapq
import json

from tooling.package_manifest import PackageManifest, PackageCoordinate, PackageContentIdentity

SCHEMA = "apexforge.package-resolution/v1"
FINGERPRINT_DOMAIN = "apexforge.package-resolution-fingerprint/v1"
DECLARATION_DOMAIN = "apexforge.package-dependency-declaration/v1"
CYCLE_POLICY = "REJECT"
_CODES = frozenset(("CANDIDATE_UNIVERSE_INVALID", "ROOT_PACKAGE_INVALID",
    "PACKAGE_CONTENT_CONFLICT", "CANDIDATE_IDENTITY_INCONSISTENT", "MISSING_DEPENDENCY",
    "DEPENDENCY_VERSION_CONFLICT", "SELF_DEPENDENCY", "DEPENDENCY_CYCLE",
    "RESOLUTION_GRAPH_INVALID"))


def _json(record):
    return json.dumps(record, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _digest(domain, record):
    return sha256((domain + "\0" + _json(record)).encode("utf-8")).hexdigest().upper()


def _key(coordinate):
    v = coordinate.version
    return (coordinate.namespace, coordinate.name, v.major, v.minor, v.patch, coordinate.schema)


@dataclass(frozen=True)
class SolverDiagnostic:
    code: str
    coordinates: tuple[PackageCoordinate, ...] = ()
    content_identities: tuple[PackageContentIdentity, ...] = ()
    requirements: tuple[tuple[PackageCoordinate, PackageCoordinate], ...] = ()
    cycle: tuple[PackageCoordinate, ...] = ()

    def __post_init__(self):
        if type(self.code) is not str or self.code not in _CODES:
            raise ValueError("SOLVER_DIAGNOSTIC_INVALID")
        for values, item_type in ((self.coordinates, PackageCoordinate),
                (self.content_identities, PackageContentIdentity), (self.cycle, PackageCoordinate)):
            if type(values) is not tuple or any(type(x) is not item_type for x in values):
                raise ValueError("SOLVER_DIAGNOSTIC_INVALID")
        if type(self.requirements) is not tuple or any(type(x) is not tuple or len(x) != 2
                or any(type(c) is not PackageCoordinate for c in x) for x in self.requirements):
            raise ValueError("SOLVER_DIAGNOSTIC_INVALID")
        object.__setattr__(self, "coordinates", tuple(sorted(set(self.coordinates), key=_key)))
        object.__setattr__(self, "content_identities", tuple(sorted(set(self.content_identities),
                           key=lambda x: (x.domain, x.fingerprint))))
        object.__setattr__(self, "requirements", tuple(sorted(set(self.requirements),
                           key=lambda x: (_key(x[0]), _key(x[1])))))
        # A cycle is an ordered path, including its repeated closing endpoint.

    def record(self):
        return {"schema": SCHEMA, "code": self.code,
            "coordinates": [x.record() for x in self.coordinates],
            "content_identities": [x.record() for x in self.content_identities],
            "requirements": [{"requiring": a.record(), "required": b.record()}
                             for a, b in self.requirements],
            "cycle": [x.record() for x in self.cycle]}

    def canonical_json(self):
        return _json(self.record())


class PackageSolverError(ValueError):
    def __init__(self, diagnostic):
        if type(diagnostic) is not SolverDiagnostic:
            raise TypeError("SOLVER_DIAGNOSTIC_REQUIRED")
        self.diagnostic = diagnostic
        self.code = diagnostic.code
        super().__init__(diagnostic.canonical_json())


def _fail(code, **details):
    raise PackageSolverError(SolverDiagnostic(code, **details))


def _require(ok, code="RESOLUTION_GRAPH_INVALID"):
    if not ok:
        _fail(code)


@dataclass(frozen=True)
class ResolvedPackage:
    """Identity-bound canonical manifest; no author/display metadata tie-breaker."""
    manifest: PackageManifest
    content_identity: PackageContentIdentity = field(init=False)

    def __post_init__(self):
        _require(type(self.manifest) is PackageManifest, "CANDIDATE_UNIVERSE_INVALID")
        canonical = replace(self.manifest, metadata=())
        object.__setattr__(self, "manifest", canonical)
        object.__setattr__(self, "content_identity", canonical.content_identity())

    @property
    def coordinate(self):
        return self.manifest.coordinate

    def reference(self):
        return {"coordinate": self.coordinate.record(), "content_identity": self.content_identity.record()}

    def record(self):
        return {**self.reference(), "manifest": self.manifest.canonical_record()}


@dataclass(frozen=True)
class PackageUniverse:
    """Canonical, deduplicated candidates; multiple available versions are inert."""
    candidates: tuple[PackageManifest, ...]

    def __post_init__(self):
        _require(type(self.candidates) is tuple and all(type(x) is PackageManifest
                 for x in self.candidates), "CANDIDATE_UNIVERSE_INVALID")
        groups = {}
        for manifest in self.candidates:
            node = ResolvedPackage(manifest)
            groups.setdefault(node.coordinate, []).append(node)
        canonical = []
        for coordinate in sorted(groups, key=_key):
            nodes = groups[coordinate]
            identities = tuple(set(x.content_identity for x in nodes))
            if len(identities) != 1:
                _fail("PACKAGE_CONTENT_CONFLICT", coordinates=(coordinate,), content_identities=identities)
            if len({x.manifest.canonical_json() for x in nodes}) != 1:
                _fail("CANDIDATE_IDENTITY_INCONSISTENT", coordinates=(coordinate,),
                      content_identities=identities)
            # Identical canonical records, even with different display metadata, are one candidate.
            canonical.append(nodes[0].manifest)
        object.__setattr__(self, "candidates", tuple(canonical))


@dataclass(frozen=True)
class ResolutionEdge:
    requiring: PackageCoordinate
    requiring_content: PackageContentIdentity
    required: PackageCoordinate
    required_content: PackageContentIdentity

    def __post_init__(self):
        _require(type(self.requiring) is PackageCoordinate and type(self.required) is PackageCoordinate
            and type(self.requiring_content) is PackageContentIdentity
            and type(self.required_content) is PackageContentIdentity)

    def declaration_fingerprint(self):
        return _digest(DECLARATION_DOMAIN, {"requiring": self.requiring.record(),
            "requiring_content": self.requiring_content.record(), "required": self.required.record()})

    def record(self):
        return {"requiring": self.requiring.record(), "requiring_content": self.requiring_content.record(),
            "required": self.required.record(), "required_content": self.required_content.record(),
            "declaration_fingerprint": self.declaration_fingerprint()}


def _edge_key(edge):
    return (_key(edge.requiring), _key(edge.required),
            edge.requiring_content.fingerprint, edge.required_content.fingerprint)


def _cycle(adjacency):
    """Iterative deterministic DFS; rotate a recorded directed cycle to its least key."""
    done = set()
    for start in sorted(adjacency, key=_key):
        if start in done:
            continue
        path, positions = [start], {start: 0}
        stack = [(start, iter(sorted(adjacency[start], key=_key)))]
        while stack:
            current, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                done.add(current)
                positions.pop(current)
                path.pop()
            elif child in positions:
                ring = path[positions[child]:]
                i = min(range(len(ring)), key=lambda n: _key(ring[n]))
                ring = ring[i:] + ring[:i]
                return tuple(ring + [ring[0]])
            elif child not in done:
                positions[child] = len(path)
                path.append(child)
                stack.append((child, iter(sorted(adjacency[child], key=_key))))
    return ()


@dataclass(frozen=True)
class ResolutionGraph:
    root: PackageCoordinate
    root_content: PackageContentIdentity
    nodes: tuple[ResolvedPackage, ...]
    edges: tuple[ResolutionEdge, ...]
    schema: str = SCHEMA

    def __post_init__(self):
        _require(type(self.schema) is str and self.schema == SCHEMA
            and type(self.root) is PackageCoordinate and type(self.root_content) is PackageContentIdentity)
        _require(type(self.nodes) is tuple and all(type(x) is ResolvedPackage for x in self.nodes)
            and type(self.edges) is tuple and all(type(x) is ResolutionEdge for x in self.edges))
        index = {x.coordinate: x for x in self.nodes}
        _require(len(index) == len(self.nodes) and self.root in index)
        _require(index[self.root].content_identity == self.root_content)
        _require(len({(c.namespace, c.name) for c in index}) == len(index))
        _require(len(set(self.edges)) == len(self.edges))
        expected = set()
        adjacency = {}
        for coordinate, node in index.items():
            dependencies = node.manifest.dependencies
            _require(all(c in index and c != coordinate for c in dependencies))
            adjacency[coordinate] = dependencies
            for required in dependencies:
                expected.add(ResolutionEdge(coordinate, node.content_identity, required,
                                            index[required].content_identity))
        _require(set(self.edges) == expected and not _cycle(adjacency))
        reached, pending = {self.root}, [self.root]
        while pending:
            for child in adjacency[pending.pop()]:
                if child not in reached:
                    reached.add(child)
                    pending.append(child)
        _require(reached == set(index))
        object.__setattr__(self, "nodes", tuple(sorted(self.nodes,
            key=lambda n: (_key(n.coordinate), n.content_identity.fingerprint))))
        object.__setattr__(self, "edges", tuple(sorted(self.edges, key=_edge_key)))

    @property
    def required_capabilities(self):
        return tuple(sorted({c for n in self.nodes for c in n.manifest.required_capabilities}))

    @property
    def exported_capabilities(self):
        return tuple(sorted({c for n in self.nodes for c in n.manifest.exported_capabilities}))

    def canonical_record(self):
        return {"schema": self.schema, "root": self.root.record(),
            "root_content": self.root_content.record(),
            "nodes": [{**n.record(), "role": "root" if n.coordinate == self.root else "dependency"}
                      for n in self.nodes], "edges": [e.record() for e in self.edges],
            "capabilities": {"requires": list(self.required_capabilities),
                "exports": list(self.exported_capabilities), "compatibility": "not_evaluated"}}

    def canonical_json(self):
        return _json(self.canonical_record())

    def fingerprint(self):
        return _digest(FINGERPRINT_DOMAIN, self.canonical_record())


def solve(root, universe):
    """Unique exact closure or structured failure. Root need not be in the universe."""
    _require(type(root) is PackageManifest, "ROOT_PACKAGE_INVALID")
    _require(type(universe) is PackageUniverse, "CANDIDATE_UNIVERSE_INVALID")
    combined = PackageUniverse(universe.candidates + (root,))
    available = {m.coordinate: m for m in combined.candidates}
    scheduled = {root.coordinate}
    pending = [(_key(root.coordinate), root.coordinate)]
    requirements = set()
    while pending:
        _, current = heapq.heappop(pending)
        manifest = available.get(current)
        if manifest is None:
            continue
        for required in manifest.dependencies:
            requirements.add((current, required))
            if required not in scheduled:
                scheduled.add(required)
                heapq.heappush(pending, (_key(required), required))

    families = {}
    for coordinate in scheduled:
        families.setdefault((coordinate.namespace, coordinate.name), []).append(coordinate)
    for family in sorted(families):
        coordinates = tuple(families[family])
        if len(coordinates) > 1:
            _fail("DEPENDENCY_VERSION_CONFLICT", coordinates=coordinates,
                  requirements=tuple(r for r in requirements if r[1] in coordinates))
    missing = tuple(sorted(scheduled - set(available), key=_key))
    if missing:
        target = missing[0]
        _fail("MISSING_DEPENDENCY", coordinates=(target,),
              requirements=tuple(r for r in requirements if r[1] == target))
    self_dependencies = tuple(sorted((a for a, b in requirements if a == b), key=_key))
    if self_dependencies:
        target = self_dependencies[0]
        _fail("SELF_DEPENDENCY", coordinates=(target,), requirements=((target, target),))
    adjacency = {c: available[c].dependencies for c in scheduled}
    cycle = _cycle(adjacency)
    if cycle:
        _fail("DEPENDENCY_CYCLE", cycle=cycle, requirements=tuple(zip(cycle, cycle[1:])))
    nodes = {c: ResolvedPackage(available[c]) for c in scheduled}
    edges = tuple(ResolutionEdge(a, nodes[a].content_identity, b, nodes[b].content_identity)
                  for a, b in requirements)
    return ResolutionGraph(root.coordinate, nodes[root.coordinate].content_identity,
                           tuple(nodes.values()), edges)
