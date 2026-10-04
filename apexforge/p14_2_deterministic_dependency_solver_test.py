"""P14.2 exact closure, immutable graph integrity and deterministic failure gates."""
from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tooling.package_solver as solver
import tooling.package_manifest as pm
import p14_1_package_identity_manifest_contract_test as manifest_fixture


def coordinate(name, version="1.0.0", namespace="apexforge.example"):
    return manifest_fixture.coordinate(name, version, namespace)


def package(name, dependencies=(), version="1.0.0", **fields):
    dependencies = tuple(coordinate(x) if type(x) is str else x for x in dependencies)
    return pm.PackageManifest(coordinate(name, version), dependencies=dependencies, **fields)


def universe(*candidates):
    return solver.PackageUniverse(tuple(candidates))


def diamond():
    root = package("root", ("a", "b"))
    return root, (package("a", ("c",)), package("b", ("c",)), package("c"))


class DependencySolverTests(unittest.TestCase):
    def error(self, fn, *args, code=None, **kwargs):
        with self.assertRaises(solver.PackageSolverError) as caught:
            fn(*args, **kwargs)
        if code:
            self.assertEqual(caught.exception.code, code)
        self.assertIsInstance(caught.exception.diagnostic, solver.SolverDiagnostic)
        self.assertFalse(hasattr(caught.exception, "graph"))
        return caught.exception.diagnostic

    def test_root_only_graph_and_role(self):
        root = package("root")
        graph = solver.solve(root, universe())
        self.assertEqual(graph.root, root.coordinate)
        self.assertEqual(graph.root_content, root.content_identity())
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(graph.edges, ())
        self.assertEqual(graph.canonical_record()["nodes"][0]["role"], "root")

    def test_one_direct_dependency_preserves_both_identities(self):
        root, dependency = package("root", ("dep",)), package("dep")
        graph = solver.solve(root, universe(dependency))
        self.assertEqual({n.coordinate for n in graph.nodes}, {root.coordinate, dependency.coordinate})
        edge = graph.edges[0]
        self.assertEqual(edge.requiring, root.coordinate)
        self.assertEqual(edge.requiring_content, root.content_identity())
        self.assertEqual(edge.required, dependency.coordinate)
        self.assertEqual(edge.required_content, dependency.content_identity())

    def test_transitive_closure_retains_declaration_edges(self):
        a, b, c = package("a", ("b",)), package("b", ("c",)), package("c")
        graph = solver.solve(a, universe(c, b))
        self.assertEqual(tuple(n.coordinate.name for n in graph.nodes), ("a", "b", "c"))
        self.assertEqual(tuple((e.requiring.name, e.required.name) for e in graph.edges),
                         (("a", "b"), ("b", "c")))

    def test_diamond_node_deduplication_does_not_delete_edges(self):
        root, candidates = diamond()
        graph = solver.solve(root, universe(*candidates))
        self.assertEqual(len(graph.nodes), 4)
        self.assertEqual(len(graph.edges), 4)
        incoming = [e for e in graph.edges if e.required.name == "c"]
        self.assertEqual(tuple(e.requiring.name for e in incoming), ("a", "b"))
        self.assertEqual(len({e.required_content for e in incoming}), 1)
        self.assertNotEqual(incoming[0].declaration_fingerprint(), incoming[1].declaration_fingerprint())

    def test_missing_exact_candidate_records_original_requirement(self):
        root = package("root", (coordinate("dep", "2.0.0"),))
        diagnostic = self.error(solver.solve, root, universe(package("dep")), code="MISSING_DEPENDENCY")
        self.assertEqual(diagnostic.coordinates, (coordinate("dep", "2.0.0"),))
        self.assertEqual(diagnostic.requirements, ((root.coordinate, coordinate("dep", "2.0.0")),))

    def test_multiple_missing_requirements_have_canonical_first_diagnostic(self):
        root = package("root", ("z", "a"))
        diagnostic = self.error(solver.solve, root, universe(), code="MISSING_DEPENDENCY")
        self.assertEqual(diagnostic.coordinates, (coordinate("a"),))
        reversed_root = replace(root, dependencies=tuple(reversed(root.dependencies)))
        self.assertEqual(diagnostic, self.error(solver.solve, reversed_root, universe()))

    def test_self_dependency_is_separate_from_long_cycle(self):
        root = package("a", ("a",))
        diagnostic = self.error(solver.solve, root, universe(), code="SELF_DEPENDENCY")
        self.assertEqual(diagnostic.requirements, ((root.coordinate, root.coordinate),))
        self.assertEqual(diagnostic.cycle, ())

    def test_two_node_cycle_closes_actual_directed_path(self):
        a, b = package("a", ("b",)), package("b", ("a",))
        diagnostic = self.error(solver.solve, a, universe(b), code="DEPENDENCY_CYCLE")
        self.assertEqual(diagnostic.cycle, (a.coordinate, b.coordinate, a.coordinate))
        self.assertEqual(diagnostic.requirements, ((a.coordinate, b.coordinate), (b.coordinate, a.coordinate)))

    def test_multi_node_cycle_rotation_is_canonical_and_preserves_direction(self):
        z, b, a = package("z", ("b",)), package("b", ("a",)), package("a", ("z",))
        diagnostic = self.error(solver.solve, z, universe(b, a), code="DEPENDENCY_CYCLE")
        self.assertEqual(diagnostic.cycle, (a.coordinate, z.coordinate, b.coordinate, a.coordinate))

    def test_self_dependency_priority_independent_of_candidate_order(self):
        root = package("root", ("a", "z"))
        candidates = (package("a", ("b",)), package("b", ("a",)), package("z", ("z",)))
        records = {self.error(solver.solve, root, universe(*order)).canonical_json()
                   for order in permutations(candidates)}
        self.assertEqual(len(records), 1)
        # The declared diagnostic priority reports self-dependency before longer cycles.
        self.assertEqual(json.loads(records.pop())["code"], "SELF_DEPENDENCY")

    def test_long_cycle_diagnostic_independent_of_order_and_other_cycles(self):
        root = package("root", ("z", "a"))
        candidates = (package("a", ("b",)), package("b", ("a",)),
                      package("z", ("y",)), package("y", ("z",)))
        diagnostics = [self.error(solver.solve, root, universe(*order), code="DEPENDENCY_CYCLE")
                       for order in permutations(candidates)]
        self.assertEqual(len({d.canonical_json() for d in diagnostics}), 1)
        self.assertEqual(diagnostics[0].cycle, (coordinate("a"), coordinate("b"), coordinate("a")))

    def test_deep_transitive_graph_avoids_python_recursion_limit(self):
        candidates = tuple(package("p{:04d}".format(i),
            ("p{:04d}".format(i + 1),) if i < 1099 else ()) for i in range(1100))
        graph = solver.solve(candidates[0], universe(*reversed(candidates[1:])))
        self.assertEqual(len(graph.nodes), 1100)
        self.assertEqual(len(graph.edges), 1099)

    def test_deep_cycle_rejects_without_recursing(self):
        candidates = tuple(package("p{:04d}".format(i),
            ("p{:04d}".format(i + 1),) if i < 1099 else ("p0000",)) for i in range(1100))
        diagnostic = self.error(solver.solve, candidates[0], universe(*candidates[1:]), code="DEPENDENCY_CYCLE")
        self.assertEqual(len(diagnostic.cycle), 1101)
        self.assertEqual(diagnostic.cycle[0], diagnostic.cycle[-1])

    def test_candidate_and_dependency_order_do_not_choose_solution(self):
        root, candidates = diamond()
        records = {solver.solve(root, universe(*order)).canonical_json() for order in permutations(candidates)}
        self.assertEqual(len(records), 1)
        reversed_root = replace(root, dependencies=tuple(reversed(root.dependencies)))
        self.assertEqual(solver.solve(root, universe(*candidates)),
                         solver.solve(reversed_root, universe(*reversed(candidates))))

    def test_identical_candidates_deduplicate(self):
        dep = package("dep")
        candidates = universe(dep, dep, replace(dep))
        self.assertEqual(candidates.candidates, (dep,))
        graph = solver.solve(package("root", ("dep",)), candidates)
        self.assertEqual(len(graph.nodes), 2)

    def test_non_identity_metadata_never_becomes_duplicate_tie_breaker(self):
        a = package("dep", metadata=(("title", "First"),))
        b = replace(a, metadata=(("title", "Second"),))
        self.assertEqual(universe(a, b), universe(b, a))
        self.assertEqual(universe(a, b).candidates[0].metadata, ())
        root = package("root", ("dep",), metadata=(("authors", "display"),))
        graph = solver.solve(root, universe(a, b))
        self.assertEqual(graph, solver.solve(replace(root, metadata=()), universe(b)))
        self.assertEqual(a.metadata, (("title", "First"),))
        self.assertEqual(b.metadata, (("title", "Second"),))

    def test_same_coordinate_different_content_fails_without_selection(self):
        a = package("dep")
        b = replace(a, content=(manifest_fixture.member(),))
        records = []
        for order in ((a, b), (b, a)):
            diagnostic = self.error(universe, *order, code="PACKAGE_CONTENT_CONFLICT")
            self.assertEqual(diagnostic.coordinates, (a.coordinate,))
            self.assertEqual(set(diagnostic.content_identities), {a.content_identity(), b.content_identity()})
            records.append(diagnostic.canonical_json())
        self.assertEqual(records[0], records[1])

    def test_unrelated_content_conflict_invalidates_supplied_universe(self):
        a = package("unused")
        self.error(universe, a, replace(a, required_capabilities=("state.read",)),
                   code="PACKAGE_CONTENT_CONFLICT")

    def test_root_content_conflict_against_universe_rejects(self):
        root = package("root")
        self.error(solver.solve, root, universe(replace(root, dependencies=(coordinate("dep"),))),
                   code="PACKAGE_CONTENT_CONFLICT")

    def test_inconsistent_same_fingerprint_candidate_records_reject(self):
        a, b = package("dep"), package("dep", ("other",))
        with patch.object(pm.PackageManifest, "content_identity", return_value=pm.PackageContentIdentity("A" * 64)):
            self.error(universe, a, b, code="CANDIDATE_IDENTITY_INCONSISTENT")

    def test_exact_version_conflict_has_all_known_requiring_edges(self):
        root = package("root", ("a", "b"))
        a, b = package("a", (coordinate("c", "1.0.0"),)), package("b", (coordinate("c", "2.0.0"),))
        diagnostic = self.error(solver.solve, root, universe(a, b, package("c"), package("c", version="2.0.0")),
                                code="DEPENDENCY_VERSION_CONFLICT")
        self.assertEqual(diagnostic.coordinates, (coordinate("c"), coordinate("c", "2.0.0")))
        self.assertEqual(diagnostic.requirements, ((a.coordinate, coordinate("c")),
                                                 (b.coordinate, coordinate("c", "2.0.0"))))

    def test_conflict_diagnostics_independent_of_traversal_order(self):
        root = package("root", ("b", "a"))
        candidates = (package("a", (coordinate("c"),)), package("b", (coordinate("c", "2.0.0"),)),
                      package("c"), package("c", version="2.0.0"))
        records = {self.error(solver.solve, root, universe(*order)).canonical_json()
                   for order in permutations(candidates)}
        self.assertEqual(len(records), 1)

    def test_conflict_precedes_missing_and_root_version_is_also_required(self):
        root = package("root", (coordinate("root", "2.0.0"),))
        self.error(solver.solve, root, universe(), code="DEPENDENCY_VERSION_CONFLICT")

    def test_unrelated_versions_and_cycles_are_not_dependencies(self):
        root = package("root", (coordinate("dep", "2.0.0"),))
        graph = solver.solve(root, universe(package("dep", version="2.0.0"),
            package("dep", version="10.0.0"), package("unused", ("unused",))))
        self.assertEqual({n.coordinate for n in graph.nodes}, {root.coordinate, coordinate("dep", "2.0.0")})

    def test_root_supplied_separately_or_identically_in_universe(self):
        root, dep = package("root", ("dep",)), package("dep")
        self.assertEqual(solver.solve(root, universe(dep)), solver.solve(root, universe(dep, root)))
        self.error(solver.solve, root.coordinate, universe(dep), code="ROOT_PACKAGE_INVALID")

    def test_nodes_retain_canonical_manifest_capabilities_and_provenance(self):
        ref = pm.CanonicalReference("apexforge.trace-retention/v1", "provenance-scope", "A" * 64)
        dep = package("dep", required_capabilities=("unprovided.read",),
                      exported_capabilities=("state.read",), provenance=(ref,))
        root = package("root", ("dep",), required_capabilities=("state.read",))
        graph = solver.solve(root, universe(dep))
        node = next(n for n in graph.nodes if n.coordinate == dep.coordinate)
        self.assertEqual(node.manifest.provenance, (ref,))
        self.assertEqual(node.manifest.canonical_record(), dep.canonical_record())
        self.assertEqual(graph.required_capabilities, ("state.read", "unprovided.read"))
        self.assertEqual(graph.exported_capabilities, ("state.read",))
        self.assertEqual(graph.canonical_record()["capabilities"]["compatibility"], "not_evaluated")
        self.assertFalse(hasattr(graph, "authorize"))
        self.assertFalse(hasattr(graph, "verify_trust"))

    def test_edge_declaration_fingerprint_is_bound_to_source_manifest(self):
        root, dep = package("root", ("dep",)), package("dep")
        edge = solver.solve(root, universe(dep)).edges[0]
        declaration = {"requiring": root.coordinate.record(), "requiring_content": root.content_identity().record(),
                       "required": dep.coordinate.record()}
        encoded = json.dumps(declaration, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        expected = sha256((solver.DECLARATION_DOMAIN + "\0" + encoded).encode()).hexdigest().upper()
        self.assertEqual(edge.declaration_fingerprint(), expected)
        self.assertIn(edge.required, root.dependencies)

    def test_canonical_graph_order_is_identity_order_not_install_order(self):
        root = package("zroot", ("b", "a"))
        graph = solver.solve(root, universe(package("b", ("a",)), package("a")))
        self.assertEqual(tuple(n.coordinate.name for n in graph.nodes), ("a", "b", "zroot"))
        self.assertEqual(tuple((e.requiring.name, e.required.name) for e in graph.edges),
                         (("b", "a"), ("zroot", "a"), ("zroot", "b")))
        self.assertEqual(graph.canonical_record()["nodes"][-1]["role"], "root")

    def test_equivalent_independently_constructed_graph_fingerprint(self):
        root_a, candidates_a = diamond()
        root_b, candidates_b = diamond()
        first = solver.solve(root_a, universe(*candidates_a))
        second = solver.solve(root_b, universe(*reversed(candidates_b)))
        self.assertEqual(first, second)
        self.assertEqual(first.canonical_record(), second.canonical_record())
        self.assertEqual(first.canonical_json(), second.canonical_json())
        self.assertEqual(first.fingerprint(), second.fingerprint())
        encoded = (solver.FINGERPRINT_DOMAIN + "\0" + first.canonical_json()).encode("utf-8")
        self.assertEqual(first.fingerprint(), sha256(encoded).hexdigest().upper())
        self.assertNotEqual(first.fingerprint(), root_a.content_identity().fingerprint)

    def test_content_change_changes_resolution_not_coordinate(self):
        root, dep = package("root", ("dep",)), package("dep")
        changed = replace(dep, content=(manifest_fixture.member(),))
        a, b = solver.solve(root, universe(dep)), solver.solve(root, universe(changed))
        self.assertEqual(tuple(n.coordinate for n in a.nodes), tuple(n.coordinate for n in b.nodes))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_result_graph_rejects_wrong_root_missing_edges_and_disconnected_nodes(self):
        root, candidates = diamond()
        graph = solver.solve(root, universe(*candidates))
        self.error(replace, graph, root=coordinate("absent"), code="RESOLUTION_GRAPH_INVALID")
        self.error(replace, graph, root_content=pm.PackageContentIdentity("B" * 64), code="RESOLUTION_GRAPH_INVALID")
        self.error(replace, graph, edges=graph.edges[:-1], code="RESOLUTION_GRAPH_INVALID")
        self.error(replace, graph, nodes=graph.nodes + (solver.ResolvedPackage(package("extra")),),
                   code="RESOLUTION_GRAPH_INVALID")

    def test_result_graph_rejects_forged_edge_binding_and_duplicate_nodes(self):
        root, dep = package("root", ("dep",)), package("dep")
        graph = solver.solve(root, universe(dep))
        edge = replace(graph.edges[0], required_content=pm.PackageContentIdentity("B" * 64))
        self.error(replace, graph, edges=(edge,), code="RESOLUTION_GRAPH_INVALID")
        self.error(replace, graph, nodes=graph.nodes + (graph.nodes[0],), code="RESOLUTION_GRAPH_INVALID")
        self.error(replace, graph, edges=graph.edges + graph.edges, code="RESOLUTION_GRAPH_INVALID")

    def test_result_graph_cannot_be_constructed_as_cyclic_or_multi_version_solution(self):
        a, b = solver.ResolvedPackage(package("a", ("b",))), solver.ResolvedPackage(package("b", ("a",)))
        edges = (solver.ResolutionEdge(a.coordinate, a.content_identity, b.coordinate, b.content_identity),
                 solver.ResolutionEdge(b.coordinate, b.content_identity, a.coordinate, a.content_identity))
        self.error(solver.ResolutionGraph, a.coordinate, a.content_identity, (a, b), edges)
        other = solver.ResolvedPackage(package("a", version="2.0.0"))
        self.error(solver.ResolutionGraph, a.coordinate, a.content_identity, (a, other), ())

    def test_inputs_outputs_and_detached_records_are_immutable(self):
        root, candidates = diamond()
        supplied = universe(*candidates)
        before = tuple(m.to_json() for m in (root,) + candidates)
        graph = solver.solve(root, supplied)
        with self.assertRaises(FrozenInstanceError):
            supplied.candidates = ()
        with self.assertRaises(FrozenInstanceError):
            graph.root = candidates[0].coordinate
        with self.assertRaises(FrozenInstanceError):
            graph.nodes[0].manifest.dependencies = ()
        detached = graph.canonical_record(); detached["nodes"].clear()
        self.assertTrue(graph.canonical_record()["nodes"])
        self.assertEqual(before, tuple(m.to_json() for m in (root,) + candidates))

    def test_malformed_universe_and_raw_input_reject_without_parsing(self):
        root = package("root")
        for supplied in ([], (), {}, "registry", None):
            self.error(solver.solve, root, supplied, code="CANDIDATE_UNIVERSE_INVALID")
        for candidates in ([root], (root.to_mapping(),), ("module:untrusted",)):
            self.error(solver.PackageUniverse, candidates, code="CANDIDATE_UNIVERSE_INVALID")
        for raw in (root.to_mapping(), root.to_json(), None):
            self.error(solver.solve, raw, universe(), code="ROOT_PACKAGE_INVALID")

    def test_diagnostics_are_fixed_structured_and_do_not_echo_unknown_input(self):
        marker = "PRIVATE_SOLVER_SENTINEL_94"
        diagnostic = self.error(solver.solve, marker, universe(), code="ROOT_PACKAGE_INVALID")
        self.assertNotIn(marker, diagnostic.canonical_json())
        self.assertEqual(json.loads(diagnostic.canonical_json())["code"], "ROOT_PACKAGE_INVALID")
        with self.assertRaises(FrozenInstanceError):
            diagnostic.code = "other"

    def test_exact_only_no_latest_range_or_dependency_kinds(self):
        for text in ("latest", "^1.0.0", "~1.0.0", "*", ">=1.0.0"):
            with self.assertRaises(pm.PackageManifestError):
                pm.ExactVersion.parse(text)
        self.assertEqual(solver.CYCLE_POLICY, "REJECT")
        for name in ("resolve_latest", "resolve_range", "parse_manifest", "restore", "install", "lockfile",
                     "fetch", "publish", "sign", "execute", "grant_authority"):
            self.assertFalse(hasattr(solver, name))
        root, dep = package("root", ("dep",)), package("dep")
        edge = solver.solve(root, universe(dep)).edges[0]
        self.assertFalse(hasattr(edge, "optional"))
        self.assertFalse(hasattr(edge, "dependency_kind"))

    def test_security_static_and_dynamic_no_io_execution_or_authority(self):
        tree = ast.parse(Path(solver.__file__).read_text(encoding="utf-8"))
        imports = {x.module for x in ast.walk(tree) if isinstance(x, ast.ImportFrom)}
        imports.update(a.name for x in ast.walk(tree) if isinstance(x, ast.Import) for a in x.names)
        self.assertEqual(imports, {"__future__", "dataclasses", "hashlib", "heapq", "json",
                                  "tooling.package_manifest"})
        forbidden = {"open", "eval", "exec", "__import__", "run_air_program", "execute", "dispatch",
                     "AuthorityEngine", "RuntimeEngine", "Popen", "system", "import_module",
                     "parse_manifest", "from_mapping", "resolve", "glob", "walk"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                self.assertNotIn(name, forbidden)
        root, candidates = diamond()
        with patch("builtins.open", side_effect=AssertionError("filesystem forbidden")), \
             patch("subprocess.run", side_effect=AssertionError("process forbidden")), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch.object(pm, "parse_manifest", side_effect=AssertionError("parser forbidden")):
            graph = solver.solve(root, universe(*candidates))
            self.assertEqual(len(graph.nodes), 4)
            self.assertEqual(graph, solver.solve(root, universe(*reversed(candidates))))


if __name__ == "__main__":
    unittest.main()
