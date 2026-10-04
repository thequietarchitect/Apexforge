"""P14.3 exact lock graph, hostile parser and execution-free restore gates."""
import ast
from dataclasses import FrozenInstanceError, replace
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tooling.package_lock as lockmod
import tooling.package_solver as solver
import tooling.package_manifest as pm
import p14_2_deterministic_dependency_solver_test as fixture


def locked(root=None, candidates=()):
    root = root or fixture.package("root")
    return lockmod.PackageLock(solver.solve(root, fixture.universe(*candidates)))


class LockTests(unittest.TestCase):
    def error(self, fn, *args, code=None):
        with self.assertRaises(lockmod.PackageLockError) as caught:
            fn(*args)
        if code:
            self.assertEqual(caught.exception.code, code)
        self.assertFalse(hasattr(caught.exception, "plan"))
        return str(caught.exception)

    def mutate(self, change, code=None):
        root, candidates = fixture.diamond()
        raw = locked(root, candidates).canonical_record()
        change(raw)
        return self.error(lockmod.PackageLock.from_mapping, raw, code=code)

    def test_root_only(self):
        l = locked()
        self.assertEqual(len(l.resolution.nodes), 1)
        self.assertEqual(l.resolution.edges, ())
        self.assertEqual(lockmod.parse_lock(l.canonical_json()), l)

    def test_direct_transitive_and_diamond_edges(self):
        for root, candidates, size in ((fixture.package("root", ("a",)), (fixture.package("a"),), 1),
                (fixture.package("root", ("a",)), (fixture.package("a", ("b",)), fixture.package("b")), 2),
                (*fixture.diamond(), 4)):
            l = locked(root, candidates)
            self.assertEqual(len(l.resolution.edges), size)
            self.assertEqual(lockmod.parse_lock(l.canonical_json()), l)

    def test_order_and_independent_equivalence(self):
        root, candidates = fixture.diamond()
        expected = locked(root, candidates)
        for order in permutations(candidates):
            actual = locked(replace(root, dependencies=tuple(reversed(root.dependencies))), order)
            self.assertEqual(actual.canonical_json(), expected.canonical_json())
            self.assertEqual(actual.fingerprint(), expected.fingerprint())
        raw = expected.canonical_record()
        raw["resolution"]["nodes"].reverse()
        raw["resolution"]["edges"].reverse()
        self.assertEqual(lockmod.PackageLock.from_mapping(raw), expected)

    def test_root_dependency_and_declaration_binding(self):
        root, candidates = fixture.diamond()
        l = locked(root, candidates)
        self.assertEqual(l.resolution.root, root.coordinate)
        self.assertEqual(l.resolution.root_content, root.content_identity())
        for node in l.resolution.nodes:
            self.assertEqual(node.content_identity, node.manifest.content_identity())
        for edge in l.resolution.edges:
            self.assertEqual(len(edge.declaration_fingerprint()), 64)

    def test_provenance_capabilities_passive(self):
        ref = pm.CanonicalReference("apexforge.provenance/v1", "provenance-scope", "A" * 64)
        root = fixture.package("root", provenance=(ref,), required_capabilities=("Read",))
        l = lockmod.parse_lock(locked(root).canonical_json())
        self.assertEqual(l.resolution.nodes[0].manifest.provenance, (ref,))
        self.assertEqual(l.resolution.required_capabilities, ("Read",))
        self.assertEqual(l.resolution.canonical_record()["capabilities"]["compatibility"], "not_evaluated")

    def test_metadata_excluded(self):
        root = fixture.package("root", metadata=(("title", "Presentation"),))
        self.assertEqual(locked(root), locked(replace(root, metadata=())))
        self.assertNotIn("Presentation", locked(root).canonical_json())

    def test_fingerprint_changes_for_root_dependency_edges_and_version(self):
        root, candidates = fixture.diamond()
        original = locked(root, candidates).fingerprint()
        changed = replace(root, required_capabilities=("Read",))
        self.assertNotEqual(locked(changed, candidates).fingerprint(), original)
        other = (replace(candidates[0], required_capabilities=("Read",)),) + candidates[1:]
        self.assertNotEqual(locked(root, other).fingerprint(), original)
        other = (replace(candidates[0], dependencies=()),) + candidates[1:]
        self.assertNotEqual(locked(root, other).fingerprint(), original)
        self.assertNotEqual(locked(fixture.package("root", version="2.0.0")).fingerprint(), locked().fingerprint())

    def test_schema_and_solver_contract(self):
        self.mutate(lambda r: r.update(schema="future"), "LOCK_SCHEMA_UNSUPPORTED")
        self.mutate(lambda r: r.update(solver_schema="future"), "LOCK_SOLVER_SCHEMA_UNSUPPORTED")
        self.mutate(lambda r: r["resolution"].update(schema="future"), "LOCK_SOLVER_SCHEMA_UNSUPPORTED")

    def test_unknown_fields_all_levels(self):
        self.mutate(lambda r: r.update(install_path="C:/secret"))
        self.mutate(lambda r: r["resolution"].update(timestamp=123))
        self.mutate(lambda r: r["resolution"]["nodes"][0].update(unknown=True))
        self.mutate(lambda r: r["resolution"]["edges"][0].update(unknown=True))

    def test_malformed_node_and_content(self):
        self.mutate(lambda r: r["resolution"]["nodes"][0]["coordinate"].update(name="../bad"),
                    "LOCK_PACKAGE_RECORD_INVALID")
        self.mutate(lambda r: r["resolution"]["nodes"][0]["content_identity"].update(fingerprint="bad"),
                    "LOCK_PACKAGE_RECORD_INVALID")
        self.mutate(lambda r: r["resolution"]["nodes"][0]["content_identity"].update(fingerprint="F"*64),
                    "LOCK_NODE_IDENTITY_MISMATCH")

    def test_duplicate_conflicting_nodes(self):
        self.mutate(lambda r: r["resolution"]["nodes"].append(r["resolution"]["nodes"][0]), "LOCK_GRAPH_INVALID")
        self.mutate(lambda r: r["resolution"]["nodes"][0]["manifest"].update(metadata={"title":"hidden"}),
                    "LOCK_MANIFEST_NONCANONICAL")

    def test_missing_root_and_dangling_edge(self):
        self.mutate(lambda r: r["resolution"].update(root=fixture.coordinate("absent").record()), "LOCK_RECORD_INVALID")
        self.mutate(lambda r: r["resolution"]["edges"].pop(), "LOCK_GRAPH_INVALID")
        self.mutate(lambda r: r["resolution"]["edges"][0].update(required=fixture.coordinate("absent").record()),
                    "LOCK_DECLARATION_MISMATCH")

    def test_declaration_and_fingerprint_tampering(self):
        self.mutate(lambda r: r["resolution"]["edges"][0].update(declaration_fingerprint="F"*64), "LOCK_DECLARATION_MISMATCH")
        self.mutate(lambda r: r.update(resolution_fingerprint="F"*64), "LOCK_RESOLUTION_FINGERPRINT_MISMATCH")

    def test_detached_and_cyclic_graph_rejected(self):
        a, b = fixture.package("a", ("b",)), fixture.package("b", ("a",))
        nodes = tuple(solver.ResolvedPackage(m) for m in (a,b))
        edges = tuple(solver.ResolutionEdge(n.coordinate,n.content_identity,m.coordinate,m.content_identity)
                      for n,m in ((nodes[0],nodes[1]),(nodes[1],nodes[0])))
        raw = locked().canonical_record()
        raw["resolution"].update(root=a.coordinate.record(),root_content=a.content_identity().record(),
            nodes=[{**n.record(),"role":"root" if n.coordinate==a.coordinate else "dependency"} for n in nodes],
            edges=[e.record() for e in edges])
        self.error(lockmod.PackageLock.from_mapping,raw,code="LOCK_GRAPH_INVALID")
        self.mutate(lambda r:r["resolution"]["nodes"].append({**solver.ResolvedPackage(fixture.package("extra")).record(),
                    "role":"dependency"}), "LOCK_GRAPH_INVALID")

    def test_duplicate_json_keys_and_invalid_json(self):
        self.error(lockmod.parse_lock,'{"schema":"a","schema":"b"}',code="LOCK_JSON_DUPLICATE_KEY")
        for text in ('{', 'NaN', '1' * 100, '[' * 1500):
            self.error(lockmod.parse_lock,text,code="LOCK_JSON_INVALID")

    def test_raw_not_validated_and_size_bound(self):
        for value in (None, {}, [], "raw"):
            self.error(lockmod.PackageLock,value,code="LOCK_SUCCESSFUL_RESOLUTION_REQUIRED")
        self.error(lockmod.parse_lock," "*(lockmod.MAX_JSON_BYTES+1),code="LOCK_JSON_TOO_LARGE")

    def test_exact_restore_and_order(self):
        root,candidates=fixture.diamond()
        l=locked(root,candidates)
        expected=lockmod.plan_restore(l,fixture.universe(root,*candidates))
        for order in permutations((root,*candidates)):
            self.assertEqual(lockmod.plan_restore(l,fixture.universe(*order)).canonical_json(),expected.canonical_json())
        self.assertFalse(expected.canonical_record()["installs_packages"])

    def test_missing_and_no_alternative_version(self):
        root=fixture.package("root",("dep",)); dep=fixture.package("dep")
        l=locked(root,(dep,))
        for supplied in ((root,), (root,fixture.package("dep",version="2.0.0"))):
            self.error(lockmod.plan_restore,l,fixture.universe(*supplied),code="RESTORE_CONTENT_MISSING")

    def test_substitution_rejected(self):
        root=fixture.package("root")
        self.error(lockmod.plan_restore,locked(root),fixture.universe(replace(root,required_capabilities=("Read",))),
                   code="RESTORE_CONTENT_SUBSTITUTED")

    def test_ambiguous_universe_rejected(self):
        root=fixture.package("root")
        with self.assertRaises(solver.PackageSolverError):
            fixture.universe(root,replace(root,required_capabilities=("Read",)))
        forged=object.__new__(solver.PackageUniverse)
        object.__setattr__(forged,"candidates",(root,replace(root,required_capabilities=("Read",))))
        self.error(lockmod.plan_restore,locked(root),forged,code="RESTORE_UNIVERSE_AMBIGUOUS")

    def test_extra_content_ignored(self):
        root=fixture.package("root")
        plan=lockmod.plan_restore(locked(root),fixture.universe(root,fixture.package("extra")))
        self.assertEqual(tuple(n.coordinate for n in plan.packages),(root.coordinate,))

    def test_root_drift_and_dependency_drift(self):
        root=fixture.package("root")
        l=locked(root)
        self.assertTrue(lockmod.validate_lock_against_root(root,l))
        self.error(lockmod.validate_lock_against_root,fixture.package("other"),l,code="LOCK_ROOT_COORDINATE_DRIFT")
        for other in (replace(root,dependencies=(fixture.coordinate("dep"),)),replace(root,required_capabilities=("Read",))):
            self.error(lockmod.validate_lock_against_root,other,l,code="LOCK_ROOT_CONTENT_DRIFT")

    def test_immutable_and_no_mutation(self):
        root,candidates=fixture.diamond(); l=locked(root,candidates)
        before=l.canonical_json(); u=fixture.universe(root,*candidates)
        plan=lockmod.plan_restore(l,u)
        with self.assertRaises(FrozenInstanceError): l.schema="bad"
        with self.assertRaises(FrozenInstanceError): plan.packages=()
        self.assertEqual(before,l.canonical_json())
        self.assertEqual(u,fixture.universe(root,*candidates))
        self.error(lockmod.RestorePlan,l,(),code="RESTORE_PLAN_INVALID")

    def test_restore_does_not_resolve(self):
        root=fixture.package("root"); l=locked(root)
        with patch.object(solver,"solve",side_effect=AssertionError("must not solve")):
            lockmod.plan_restore(l,fixture.universe(root))
            self.error(lockmod.plan_restore,l,fixture.universe(),code="RESTORE_CONTENT_MISSING")

    def test_large_chain_roundtrip_and_restore(self):
        manifests=tuple(fixture.package("n"+str(i), ("n"+str(i+1),) if i<1099 else ()) for i in range(1100))
        l=locked(manifests[0],manifests[1:])
        parsed=lockmod.parse_lock(l.canonical_json())
        self.assertEqual(parsed.fingerprint(),l.fingerprint())
        self.assertEqual(len(lockmod.plan_restore(parsed,fixture.universe(*manifests)).packages),1100)

    def test_large_cycle_validation_iterative(self):
        manifests=tuple(fixture.package("n"+str(i),("n"+str((i+1)%1100),)) for i in range(1100))
        nodes=tuple(solver.ResolvedPackage(m) for m in manifests)
        raw=locked().canonical_record(); g=raw["resolution"]
        g.update(root=nodes[0].coordinate.record(),root_content=nodes[0].content_identity.record(),
            nodes=[{**n.record(),"role":"root" if i==0 else "dependency"} for i,n in enumerate(nodes)],
            edges=[solver.ResolutionEdge(n.coordinate,n.content_identity,nodes[(i+1)%1100].coordinate,
                    nodes[(i+1)%1100].content_identity).record() for i,n in enumerate(nodes)])
        self.error(lockmod.PackageLock.from_mapping,raw,code="LOCK_GRAPH_INVALID")

    def test_diagnostics_deterministic_no_payload_echo(self):
        sentinel="SENSITIVE_INVALID_HOST_PATH"
        messages=[self.error(lockmod.PackageLock.from_mapping,{"secret":sentinel}) for _ in range(2)]
        self.assertEqual(messages[0],messages[1]); self.assertNotIn(sentinel,messages[0])

    def test_static_security_and_no_hidden_solver(self):
        tree=ast.parse((ROOT/"apexforge/tooling/package_lock.py").read_text(encoding="utf-8"))
        forbidden={"subprocess","socket","urllib","requests","os","importlib","runtime","authority","native_execution"}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ""]
                self.assertFalse(any(any(part in forbidden for part in n.split(".")) for n in names))
                self.assertNotIn("solve",[a.name for a in node.names])
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ""
                self.assertNotIn(name,{"solve","eval","exec","open","execute","run_air_program","Popen","system","install"})


if __name__=="__main__":
    unittest.main()
