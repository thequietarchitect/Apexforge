"""P14.4 package addressing without changing or executing language identities."""
import ast
from dataclasses import FrozenInstanceError, replace
from itertools import permutations
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_namespace as ns
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import p14_2_deterministic_dependency_solver_test as fixture
from language.identities import ProjectDeclaredIdentity
from language.source import SourceSpan, SourcePosition


def symbol(name="Run", digest="A"*64, module="language.module"):
    return pm.SymbolReference(digest,"function","function:"+name,module)


def setup_pair():
    s=symbol(); provider=fixture.package("provider",exports=(s,))
    root=fixture.package("root",("provider",))
    graph=solver.solve(root,fixture.universe(provider))
    node=next(n for n in graph.nodes if n.coordinate==provider.coordinate)
    index=ns.PackageExportIndex(node,(s,symbol("Private")))
    return root,provider,s,graph,index


class NamespaceTests(unittest.TestCase):
    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(ns.PackageNamespaceError) as caught: fn(*args,**kwargs)
        if code: self.assertEqual(caught.exception.code,code)
        return caught.exception

    def test_minimal_and_canonical_identity(self):
        root,provider,s,g,i=setup_pair()
        binding=ns.PackageNamespace(g,(i,)).resolve(root.coordinate,ns.PackageSymbolReference(s.identity))
        self.assertIs(binding.symbol,s)
        self.assertEqual(binding.index.provider.content_identity,provider.content_identity())
        self.assertEqual(binding.consumer.coordinate,root.coordinate)
        self.assertEqual(binding.dependency,g.edges[0])

    def test_package_language_namespace_separation(self):
        root,provider,s,g,i=setup_pair()
        self.assertNotEqual(provider.coordinate.namespace,s.module)
        self.assertEqual(i.canonical_record()["exports"][0]["export_name"],"function:Run")
        self.assertEqual(i.canonical_record()["exports"][0]["symbol"],s.record())
        self.assertNotIn(provider.coordinate.namespace,s.identity)

    def test_from_actual_declared_identity(self):
        span=SourceSpan("decl.apex",SourcePosition(1,1,0),SourcePosition(1,4,3))
        declaration=ProjectDeclaredIdentity("function","Run","function:Run","decl.apex",
                                            "language.module","language.module.Run",span)
        s=pm.SymbolReference.from_declared(declaration,"A"*64)
        p=fixture.package("provider",exports=(s,))
        index=ns.PackageExportIndex(solver.ResolvedPackage(p),(s,))
        self.assertEqual(index.provider.manifest.exports[0].identity,declaration.current_air_id)

    def test_index_order_deterministic(self):
        a,b=symbol("A"),symbol("B")
        p=fixture.package("provider",exports=(b,a))
        expected=None
        for order in permutations((a,b,symbol("Private"))):
            index=ns.PackageExportIndex(solver.ResolvedPackage(p),order)
            if expected is None: expected=index
            self.assertEqual(index,expected)
            self.assertEqual(index.fingerprint(),expected.fingerprint())
        self.assertEqual([e["export_name"] for e in expected.canonical_record()["exports"]],[a.identity,b.identity])

    def test_duplicate_export_and_evidence(self):
        s=symbol()
        with self.assertRaises(pm.PackageManifestError): fixture.package("provider",exports=(s,s))
        root,p,s,g,i=setup_pair()
        self.error(ns.PackageExportIndex,i.provider,(s,s),code="EXPORT_EVIDENCE_DUPLICATE")

    def test_missing_or_stale_evidence(self):
        root,p,s,g,i=setup_pair()
        for supplied in ((),(replace(s,air_fingerprint="B"*64),),(replace(s,module="other.module"),)):
            self.error(ns.PackageExportIndex,i.provider,supplied,code="EXPORT_DECLARATION_MISSING")

    def test_malformed_and_unsupported_export(self):
        for name in ("Run","../Run","function:Bad.Name","authority:Run",""):
            self.error(ns.PackageSymbolReference,name,code="EXPORT_NAME_INVALID")
        with self.assertRaises(pm.PackageManifestError): pm.SymbolReference("A"*64,"workflow","workflow:Run")
        self.error(ns.PackageExportIndex,solver.ResolvedPackage(fixture.package("p")),("raw",),code="EXPORT_EVIDENCE_INVALID")

    def test_private_not_visible_and_local_lookup_separate(self):
        root,p,s,g,i=setup_pair(); namespace=ns.PackageNamespace(g,(i,))
        self.error(namespace.resolve,root.coordinate,ns.PackageSymbolReference("function:Private"),code="EXPORT_NOT_FOUND")
        self.error(namespace.resolve,p.coordinate,ns.PackageSymbolReference(s.identity,p.coordinate),code="EXPORT_PROVIDER_NOT_VISIBLE")

    def test_transitive_and_unrelated_not_visible(self):
        s=symbol(); c=fixture.package("c",exports=(s,)); b=fixture.package("b",("c",))
        root=fixture.package("root",("b",)); extra=fixture.package("extra",exports=(symbol("Extra"),))
        g=solver.solve(root,fixture.universe(b,c,extra))
        node=next(n for n in g.nodes if n.coordinate==c.coordinate)
        namespace=ns.PackageNamespace(g,(ns.PackageExportIndex(node,(s,)),))
        self.error(namespace.resolve,root.coordinate,ns.PackageSymbolReference(s.identity,c.coordinate),code="EXPORT_PROVIDER_NOT_VISIBLE")
        self.error(namespace.resolve,root.coordinate,ns.PackageSymbolReference("function:Extra",extra.coordinate),code="EXPORT_PROVIDER_NOT_VISIBLE")
        self.assertEqual(namespace.resolve(b.coordinate,ns.PackageSymbolReference(s.identity)).symbol,s)

    def test_provider_substitution(self):
        root,p,s,g,i=setup_pair()
        altered=replace(p,required_capabilities=("Read",))
        bad=ns.PackageExportIndex(solver.ResolvedPackage(altered),(s,))
        self.error(ns.PackageNamespace,g,(bad,),code="EXPORT_PROVIDER_CONTENT_MISMATCH")

    def test_lock_binding_accept_and_reject(self):
        root,p,s,g,i=setup_pair(); lock=locks.PackageLock(g)
        binding=ns.PackageNamespace(g,(i,),lock).resolve(root.coordinate,ns.PackageSymbolReference(s.identity,p.coordinate))
        self.assertEqual(binding.lock.fingerprint(),lock.fingerprint())
        altered=solver.solve(replace(root,required_capabilities=("Read",)),fixture.universe(p))
        self.error(ns.PackageNamespace,g,(i,),locks.PackageLock(altered),code="EXPORT_LOCK_BINDING_MISMATCH")
        self.error(replace,binding,lock=locks.PackageLock(altered),code="EXPORT_LOCK_BINDING_MISMATCH")

    def test_ambiguity_candidates_order_and_qualification(self):
        a,b=symbol(digest="A"*64),symbol(digest="B"*64)
        pa,pb=fixture.package("a",exports=(a,)),fixture.package("b",exports=(b,))
        root=fixture.package("root",("a","b"));g=solver.solve(root,fixture.universe(pa,pb))
        indexes=tuple(ns.PackageExportIndex(n,n.manifest.exports) for n in g.nodes if n.manifest.exports)
        errors=[]
        for order in permutations(indexes):
            namespace=ns.PackageNamespace(g,order)
            errors.append(self.error(namespace.resolve,root.coordinate,ns.PackageSymbolReference(a.identity),code="EXPORT_AMBIGUOUS").candidates)
            self.assertEqual(namespace.resolve(root.coordinate,ns.PackageSymbolReference(a.identity,pb.coordinate)).symbol,b)
        self.assertEqual(errors[0],errors[1]);self.assertEqual(len(errors[0]),2)

    def test_same_name_different_modules_collision(self):
        a,b=symbol(),symbol(module="other.module",digest="B"*64)
        p=fixture.package("p",exports=(a,b))
        self.error(ns.PackageExportIndex,solver.ResolvedPackage(p),(a,b),code="EXPORT_NAME_COLLISION")

    def test_no_reexport_or_cross_owner_claim(self):
        s=symbol();a=fixture.package("a",exports=(s,));b=fixture.package("b",exports=(s,))
        root=fixture.package("root",("a","b"));g=solver.solve(root,fixture.universe(a,b))
        indexes=tuple(ns.PackageExportIndex(n,(s,)) for n in g.nodes if n.manifest.exports)
        self.error(ns.PackageNamespace,g,indexes,code="EXPORT_DECLARATION_OWNERSHIP_CONFLICT")
        self.assertEqual(root.exports,())

    def test_missing_duplicate_and_external_indexes(self):
        root,p,s,g,i=setup_pair()
        self.error(ns.PackageNamespace,g,(),code="EXPORT_INDEX_MISSING")
        self.error(ns.PackageNamespace,g,(i,i),code="EXPORT_INDEX_DUPLICATE")
        extra=fixture.package("extra",exports=(symbol("Extra"),))
        external=ns.PackageExportIndex(solver.ResolvedPackage(extra),extra.exports)
        self.error(ns.PackageNamespace,g,(i,external),code="EXPORT_PROVIDER_CONTENT_MISMATCH")

    def test_provenance_and_capabilities_passive(self):
        root,p,s,g,i=setup_pair()
        ref=pm.CanonicalReference("apexforge.provenance/v1","provenance-scope","F"*64)
        p=replace(p,provenance=(ref,),exported_capabilities=("Read",))
        g=solver.solve(root,fixture.universe(p));node=next(n for n in g.nodes if n.coordinate==p.coordinate)
        binding=ns.PackageNamespace(g,(ns.PackageExportIndex(node,(s,)),)).resolve(root.coordinate,ns.PackageSymbolReference(s.identity))
        self.assertEqual(binding.canonical_record()["provenance"],[ref.record()])
        self.assertFalse(hasattr(binding,"authority"));self.assertFalse(hasattr(binding,"publisher"))

    def test_immutability_and_producer_unchanged(self):
        root,p,s,g,i=setup_pair();lock=locks.PackageLock(g);before=lock.canonical_json()
        namespace=ns.PackageNamespace(g,(i,),lock);binding=namespace.resolve(root.coordinate,ns.PackageSymbolReference(s.identity))
        for obj,field in ((namespace,"indexes"),(i,"declarations"),(binding,"symbol")):
            with self.assertRaises(FrozenInstanceError): setattr(obj,field,None)
        self.assertEqual(before,lock.canonical_json());self.assertEqual(p.exports,(s,))

    def test_binding_integrity(self):
        root,p,s,g,i=setup_pair();binding=ns.PackageNamespace(g,(i,)).resolve(root.coordinate,ns.PackageSymbolReference(s.identity))
        self.error(replace,binding,symbol=symbol("Private"),code="EXPORT_BINDING_INVALID")
        self.error(replace,binding,consumer=i.provider,code="EXPORT_BINDING_INVALID")

    def test_deterministic_independent_binding(self):
        bindings=[]
        for _ in range(2):
            root,p,s,g,i=setup_pair()
            bindings.append(ns.PackageNamespace(g,(i,),locks.PackageLock(g)).resolve(root.coordinate,ns.PackageSymbolReference(s.identity)))
        self.assertEqual(bindings[0].canonical_json(),bindings[1].canonical_json())
        self.assertEqual(bindings[0].fingerprint(),bindings[1].fingerprint())

    def test_missing_export_consumer_and_error_no_echo(self):
        root,p,s,g,i=setup_pair();namespace=ns.PackageNamespace(g,(i,))
        self.error(namespace.resolve,fixture.coordinate("missing"),ns.PackageSymbolReference(s.identity),code="EXPORT_CONSUMER_UNKNOWN")
        self.error(namespace.resolve,root.coordinate,ns.PackageSymbolReference("function:Missing"),code="EXPORT_NOT_FOUND")
        err=self.error(ns.PackageSymbolReference,"SENSITIVE_HOST_COMMAND",code="EXPORT_NAME_INVALID")
        self.assertNotIn("SENSITIVE",str(err))

    def test_no_solving_or_lock_generation(self):
        root,p,s,g,i=setup_pair();namespace=ns.PackageNamespace(g,(i,))
        with patch.object(solver,"solve",side_effect=AssertionError("solver called")),patch.object(locks,"plan_restore",side_effect=AssertionError("restore called")):
            self.assertEqual(namespace.resolve(root.coordinate,ns.PackageSymbolReference(s.identity)).symbol,s)

    def test_large_graph_indexes(self):
        providers=tuple(fixture.package("p"+str(n),exports=(symbol("Run"+str(n),format(n,"064X")),)) for n in range(1100))
        root=fixture.package("root",tuple(p.coordinate for p in providers))
        g=solver.solve(root,fixture.universe(*reversed(providers)))
        indexes=tuple(ns.PackageExportIndex(n,n.manifest.exports) for n in g.nodes if n.manifest.exports)
        a,b=ns.PackageNamespace(g,indexes),ns.PackageNamespace(g,tuple(reversed(indexes)))
        self.assertEqual(a,b)
        for n in (0,550,1099):
            ref=ns.PackageSymbolReference("function:Run"+str(n))
            self.assertEqual(a.resolve(root.coordinate,ref).fingerprint(),b.resolve(root.coordinate,ref).fingerprint())

    def test_static_separation(self):
        tree=ast.parse((ROOT/"apexforge/tooling/package_namespace.py").read_text(encoding="utf-8"))
        forbidden={"subprocess","os","socket","requests","urllib","runtime","authority","native_execution","importlib"}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ""]
                self.assertFalse(any(any(p in forbidden for p in n.split(".")) for n in names))
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ""
                self.assertNotIn(name,{"solve","plan_restore","eval","exec","open","execute","run_air_program","Popen","system","install","parse_manifest"})


if __name__=="__main__": unittest.main()
