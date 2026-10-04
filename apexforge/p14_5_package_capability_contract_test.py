"""P14.5 contract compatibility without authority grants or trust."""
import ast
from dataclasses import FrozenInstanceError, replace
from itertools import permutations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_capabilities as caps
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_namespace as namespaces
import p14_2_deterministic_dependency_solver_test as fixture
from authority.engine import AuthorityEngine
from authority.model import Principal, AuthorityGrant


def pair():
    root=fixture.package("root",("provider",),required_capabilities=("Contract.Read",))
    provider=fixture.package("provider",exported_capabilities=("Contract.Read",))
    return root,provider,solver.solve(root,fixture.universe(provider))


class CapabilityTests(unittest.TestCase):
    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(caps.PackageCapabilityError) as caught: fn(*args,**kwargs)
        if code: self.assertEqual(caught.exception.code,code)
        return str(caught.exception)

    def test_no_requirements(self):
        g=solver.solve(fixture.package("root"),fixture.universe())
        r=caps.validate_capabilities(g)
        self.assertTrue(r.compatible);self.assertEqual(r.bindings,());self.assertEqual(r.diagnostics,())

    def test_exact_binding_all_identities_and_edge(self):
        root,p,g=pair();r=caps.validate_capabilities(g);b=r.bindings[0]
        self.assertTrue(r.compatible);self.assertEqual(b.capability,"Contract.Read")
        self.assertEqual(b.consumer.content_identity,root.content_identity())
        self.assertEqual(b.provider.content_identity,p.content_identity())
        self.assertEqual(b.dependency,g.edges[0])
        self.assertEqual(b.record()["provider_declaration"]["package"],b.provider.reference())

    def test_missing_and_exact_case_no_implication(self):
        root,p,g=pair()
        for names in ((),("contract.Read",),("Contract.Read.All",)):
            altered=replace(p,exported_capabilities=names)
            r=caps.validate_capabilities(solver.solve(root,fixture.universe(altered)))
            self.assertFalse(r.compatible);self.assertEqual(r.diagnostics[0].code,"MISSING_REQUIRED_CAPABILITY")

    def test_malformed_and_duplicate_manifest_declarations(self):
        for name in ("*","Contract.*","Contract.Read@1","../Read",""):
            with self.assertRaises(pm.PackageManifestError): fixture.package("root",required_capabilities=(name,))
        with self.assertRaises(pm.PackageManifestError): fixture.package("root",exported_capabilities=("Read","Read"))
        self.error(caps.CapabilityBinding,None,"*",None,None,code="CAPABILITY_REFERENCE_INVALID")

    def test_transitive_provider_not_visible(self):
        root,p,g=pair(); middle=fixture.package("middle",("provider",))
        root=replace(root,dependencies=(middle.coordinate,))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(middle,p)))
        self.assertFalse(r.compatible);self.assertEqual(r.diagnostics[0].code,"CAPABILITY_PROVIDER_NOT_VISIBLE")

    def test_unrelated_universe_does_not_provide(self):
        root=fixture.package("root",required_capabilities=("Read",))
        p=fixture.package("extra",exported_capabilities=("Read",))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertFalse(r.compatible);self.assertEqual(r.canonical_record()["providers"],[])

    def test_ambiguity_and_order_independence(self):
        root=fixture.package("root",("a","b"),required_capabilities=("Read",))
        providers=(fixture.package("a",exported_capabilities=("Read",)),fixture.package("b",exported_capabilities=("Read",)))
        results=[caps.validate_capabilities(solver.solve(root,fixture.universe(*order))) for order in permutations(providers)]
        self.assertEqual(results[0].canonical_json(),results[1].canonical_json())
        self.assertFalse(results[0].compatible)
        self.assertEqual(results[0].diagnostics[0].code,"AMBIGUOUS_CAPABILITY_PROVIDER")
        self.assertEqual(len(results[0].diagnostics[0].providers),2)

    def test_all_packages_requirements_not_root_only(self):
        root,p,g=pair();p=replace(p,required_capabilities=("Missing",))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertFalse(r.compatible);self.assertEqual(len(r.bindings),1)
        self.assertEqual(r.diagnostics[0].consumer.coordinate,p.coordinate)

    def test_self_export_not_satisfaction(self):
        root=fixture.package("root",required_capabilities=("Read",),exported_capabilities=("Read",))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe()))
        self.assertFalse(r.compatible);self.assertEqual(r.diagnostics[0].code,"CAPABILITY_SELF_PROVIDER_NOT_ALLOWED")

    def test_self_and_dependency_allows_dependency_only(self):
        root,p,g=pair();root=replace(root,exported_capabilities=("Contract.Read",))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertTrue(r.compatible);self.assertEqual(r.bindings[0].provider.coordinate,p.coordinate)

    def test_lock_content_binding(self):
        root,p,g=pair();lock=locks.PackageLock(g)
        r=caps.validate_capabilities(g,lock)
        self.assertTrue(r.compatible);self.assertEqual(r.canonical_record()["lock_fingerprint"],lock.fingerprint())
        altered=solver.solve(root,fixture.universe(replace(p,exported_capabilities=("Contract.Read","Write"))))
        self.error(caps.validate_capabilities,altered,lock,code="CAPABILITY_LOCK_BINDING_MISMATCH")
        self.error(replace,r,lock=locks.PackageLock(altered),code="CAPABILITY_LOCK_BINDING_MISMATCH")

    def test_wrong_binding_content_rejected(self):
        root,p,g=pair();b=caps.validate_capabilities(g).bindings[0]
        bad=solver.ResolvedPackage(replace(p,exported_capabilities=("Contract.Read","Other")))
        self.error(replace,b,provider=bad,code="CAPABILITY_BINDING_INVALID")

    def test_symbol_export_not_capability(self):
        root,p,g=pair();symbol=pm.SymbolReference("A"*64,"function","function:Read")
        p=replace(p,exported_capabilities=(),exports=(symbol,))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertFalse(r.compatible)
        self.assertEqual(pair()[1].exports,())

    def test_authority_principal_roles_grants_unchanged(self):
        root,p,g=pair()
        grant=AuthorityGrant("principal:Test","Contract.Read","resource")
        engine=AuthorityEngine((grant,));principal=Principal("principal:Test",roles=("Role",),authorities=(grant,))
        before=(principal,engine.grants)
        with patch.object(AuthorityEngine,"check",side_effect=AssertionError("authority called")),patch.object(AuthorityEngine,"allows",side_effect=AssertionError("authority called")):
            r=caps.validate_capabilities(g)
        self.assertEqual((principal,engine.grants),before)
        self.assertTrue(r.compatible)
        self.assertFalse(r.canonical_record()["grants_authority"])
        self.assertFalse(r.canonical_record()["validates_trust"])

    def test_provenance_passive(self):
        root,p,g=pair();ref=pm.CanonicalReference("apexforge.provenance/v1","provenance-scope","F"*64)
        root=replace(root,provenance=(ref,));p=replace(p,provenance=(ref,))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertEqual(r.bindings[0].record()["consumer_provenance"],[ref.record()])
        self.assertEqual(r.bindings[0].record()["provider_provenance"],[ref.record()])
        self.assertFalse(hasattr(r,"trusted"));self.assertFalse(hasattr(r,"publisher"))

    def test_package_version_not_capability_version(self):
        root,p,g=pair();p=replace(p,coordinate=fixture.coordinate("provider","2.0.0"))
        root=replace(root,dependencies=(p.coordinate,))
        r=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertEqual(r.bindings[0].capability,"Contract.Read")

    def test_deterministic_requirement_and_diagnostic_order(self):
        root=fixture.package("root",required_capabilities=("Z","A"))
        a=caps.validate_capabilities(solver.solve(root,fixture.universe()))
        b=caps.validate_capabilities(solver.solve(replace(root,required_capabilities=("A","Z")),fixture.universe()))
        self.assertEqual(a.canonical_json(),b.canonical_json())
        self.assertEqual([d.capability for d in a.diagnostics],["A","Z"])

    def test_independent_construction_and_content_fingerprint(self):
        a=caps.validate_capabilities(pair()[2]);b=caps.validate_capabilities(pair()[2])
        self.assertEqual(a.fingerprint(),b.fingerprint());self.assertEqual(a.canonical_json(),b.canonical_json())
        root,p,g=pair();p=replace(p,exported_capabilities=("Contract.Read","Other"))
        changed=caps.validate_capabilities(solver.solve(root,fixture.universe(p)))
        self.assertNotEqual(a.fingerprint(),changed.fingerprint())

    def test_immutable_and_source_objects_unchanged(self):
        root,p,g=pair();lock=locks.PackageLock(g);before=lock.canonical_json()
        index=namespaces.PackageExportIndex(next(n for n in g.nodes if n.coordinate==p.coordinate),())
        old=index.canonical_json();r=caps.validate_capabilities(g,lock)
        for obj,field in ((r,"bindings"),(r.bindings[0],"capability")):
            with self.assertRaises(FrozenInstanceError): setattr(obj,field,None)
        self.assertEqual(lock.canonical_json(),before);self.assertEqual(index.canonical_json(),old)
        self.assertEqual(root.required_capabilities,("Contract.Read",));self.assertEqual(p.exported_capabilities,("Contract.Read",))

    def test_no_solver_restore_or_authority_fallback(self):
        root,p,g=pair()
        with patch.object(solver,"solve",side_effect=AssertionError("solver")),patch.object(locks,"plan_restore",side_effect=AssertionError("restore")):
            self.assertTrue(caps.validate_capabilities(g).compatible)

    def test_forged_result_cannot_hide_missing(self):
        root=fixture.package("root",required_capabilities=("Missing",));g=solver.solve(root,fixture.universe())
        self.error(caps.CapabilityCompatibilityResult,g,(),(),code="CAPABILITY_RESULT_INVALID")
        self.error(caps.validate_capabilities,{},code="CAPABILITY_GRAPH_INVALID")

    def test_large_chain_deterministic(self):
        packages=tuple(fixture.package("n"+str(i),("n"+str(i+1),) if i<1099 else (),
            exported_capabilities=("Contract"+str(i),),required_capabilities=("Contract"+str(i+1),) if i<1099 else ()) for i in range(1100))
        g=solver.solve(packages[0],fixture.universe(*packages[1:]))
        h=solver.solve(packages[0],fixture.universe(*reversed(packages[1:])))
        a,b=caps.validate_capabilities(g),caps.validate_capabilities(h)
        self.assertTrue(a.compatible);self.assertEqual(len(a.bindings),1099)
        self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_static_security_separation(self):
        tree=ast.parse((ROOT/"apexforge/tooling/package_capabilities.py").read_text(encoding="utf-8"))
        forbidden={"subprocess","os","socket","requests","urllib","runtime","authority","native_execution","importlib"}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ""]
                self.assertFalse(any(any(p in forbidden for p in n.split(".")) for n in names))
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ""
                self.assertNotIn(name,{"solve","plan_restore","eval","exec","open","execute","run_air_program","Popen","system","install"})


if __name__=="__main__": unittest.main()
