"""P14.10 structural compatibility, unknown evidence and non-executing migration."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tooling.package_compatibility as compat
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_namespace as ns
import tooling.package_registry as registry
import tooling.package_publishing as publishing
import tooling.package_cache as cache
import p14_2_deterministic_dependency_solver_test as fixture
import p14_4_package_namespace_export_resolution_test as symbols
from rich_documents.model import PackageTier


def package(version='1.0.0', **fields):
    return fixture.package('provider', version=version, **fields)


def compare(old, new):
    a = ns.PackageExportIndex(solver.ResolvedPackage(old), old.exports)
    b = ns.PackageExportIndex(solver.ResolvedPackage(new), new.exports)
    return compat.compare_packages(old, new, a, b)


def graph_fixture(old):
    direct = fixture.package('direct', dependencies=(old.coordinate,))
    other = fixture.package('unrelated')
    root = fixture.package('root', dependencies=(direct.coordinate, other.coordinate))
    graph = solver.solve(root, fixture.universe(old, direct, other))
    return graph, locks.PackageLock(graph)


class CompatibilityTests(unittest.TestCase):
    def test_identical_and_metadata_only(self):
        old=package(); new=replace(old,metadata=(('title','Display'),))
        report=compare(old,new)
        self.assertEqual(report.classification,compat.IDENTICAL)
        self.assertTrue(report.structurally_compatible)
        self.assertEqual(report.fingerprint(),compare(old,old).fingerprint())

    def test_version_is_not_compatibility_proof(self):
        old=package()
        for version in ('1.0.1','1.1.0','2.0.0','0.0.1'):
            new=package(version)
            self.assertEqual(compare(old,new).classification,compat.IDENTICAL)
            self.assertNotEqual(old.content_identity(),new.content_identity())
        self.assertEqual(compare(old,package('1.0.1',required_capabilities=('Read',))).classification,compat.BREAKING)

    def test_namespace_and_name_family_change(self):
        old=package()
        for c in (fixture.coordinate('other'),fixture.coordinate('provider',namespace='other.space')):
            report=compare(old,replace(old,coordinate=c))
            self.assertEqual(report.classification,compat.FAMILY_CHANGED)
            self.assertFalse(report.structurally_compatible)

    def test_added_export_additive(self):
        a=symbols.symbol('A');b=symbols.symbol('B')
        report=compare(package(exports=(a,)),package('2.0.0',exports=(a,b)))
        self.assertEqual(report.classification,compat.ADDITIVE)
        self.assertEqual(report.changes[0].reason,'DECLARATION_ADDED')

    def test_removed_export_breaking(self):
        a=symbols.symbol('A')
        self.assertEqual(compare(package(exports=(a,)),package('2.0.0')).classification,compat.BREAKING)

    def test_retargeted_export_exact_air_and_module(self):
        a=symbols.symbol('A')
        for b in (replace(a,air_fingerprint='B'*64),replace(a,module='other.module')):
            report=compare(package(exports=(a,)),package('2.0.0',exports=(b,)))
            self.assertEqual(report.classification,compat.BREAKING)
            self.assertEqual(report.changes[0].reason,'DECLARATION_RETARGETED')

    def test_export_order_and_unchanged_identity(self):
        a,b=symbols.symbol('A'),symbols.symbol('B')
        old=package(exports=(a,b));new=package('2.0.0',exports=(b,a))
        self.assertEqual(compare(old,new).classification,compat.IDENTICAL)
        self.assertEqual(compare(old,new).canonical_json(),compare(package(exports=(b,a)),new).canonical_json())

    def test_missing_export_evidence_unknown(self):
        old=package(exports=(symbols.symbol(),));new=replace(old,coordinate=fixture.coordinate('provider','2.0.0'))
        report=compat.compare_packages(old,new)
        self.assertEqual(report.classification,compat.UNKNOWN)
        self.assertFalse(report.structurally_compatible)
        self.assertEqual(report.changes[0].reason,'CANONICAL_EXPORT_EVIDENCE_MISSING')

    def test_export_evidence_exact_provider_binding(self):
        old=package(exports=(symbols.symbol(),));new=package('2.0.0',exports=old.exports)
        index=ns.PackageExportIndex(solver.ResolvedPackage(new),new.exports)
        with self.assertRaises(compat.CompatibilityError) as caught:compat.compare_packages(old,new,index,index)
        self.assertEqual(caught.exception.code,'EXPORT_EVIDENCE_CONTENT_MISMATCH')

    def test_required_capability_add_remove_replace(self):
        old=package(required_capabilities=('Read',))
        self.assertEqual(compare(old,package('2.0.0',required_capabilities=('Read','Write'))).classification,compat.BREAKING)
        self.assertEqual(compare(old,package('2.0.0')).classification,compat.ADDITIVE)
        report=compare(old,package('2.0.0',required_capabilities=('Write',)))
        self.assertEqual(report.classification,compat.BREAKING);self.assertEqual(len(report.changes),2)

    def test_provided_capability_add_remove_replace(self):
        old=package(exported_capabilities=('Read',))
        self.assertEqual(compare(old,package('2.0.0',exported_capabilities=('Read','Write'))).classification,compat.ADDITIVE)
        self.assertEqual(compare(old,package('2.0.0')).classification,compat.BREAKING)
        self.assertEqual(compare(old,package('2.0.0',exported_capabilities=('Write',))).classification,compat.BREAKING)

    def test_dependency_add_remove_exact_change(self):
        d=fixture.coordinate('dep');old=package(dependencies=(d,))
        self.assertEqual(compare(package(),old).classification,compat.BREAKING)
        self.assertEqual(compare(old,package('2.0.0')).classification,compat.ADDITIVE)
        report=compare(old,package('2.0.0',dependencies=(fixture.coordinate('dep','2.0.0'),)))
        self.assertEqual(report.classification,compat.UNKNOWN)
        self.assertEqual(report.changes[0].reason,'EXACT_DEPENDENCY_CHANGED')

    def test_actual_package_tier_change(self):
        tiers=list(PackageTier)
        self.assertEqual(compare(package(tier=tiers[0]),package('2.0.0',tier=tiers[1])).classification,compat.BREAKING)

    def test_entrypoint_add_remove_retarget(self):
        a=pm.SymbolReference('A'*64,'directive','directive:Run')
        b=replace(a,air_fingerprint='B'*64)
        self.assertEqual(compare(package(),package('2.0.0',entrypoints=(a,))).classification,compat.ADDITIVE)
        self.assertEqual(compare(package(entrypoints=(a,)),package()).classification,compat.BREAKING)
        self.assertEqual(compare(package(entrypoints=(a,)),package(entrypoints=(b,))).classification,compat.BREAKING)

    def test_unknown_schema_fail_closed(self):
        old=package();coordinate=object.__new__(pm.PackageCoordinate)
        for field in ('namespace','name','version'):object.__setattr__(coordinate,field,getattr(old.coordinate,field))
        object.__setattr__(coordinate,'schema','apexforge.package/future')
        # Adversarial fixture bypasses frozen schema admission; no new schema interpretation.
        report=compat.compare_packages(old,replace(old,coordinate=coordinate))
        self.assertEqual(report.classification,compat.INCOMPATIBLE)
        self.assertFalse(report.structurally_compatible)

    def test_content_change_unknown_not_automatically_breaking(self):
        a=pm.ContentDescriptor(pm.PackagePath('main.apex'),sha256(b'a').hexdigest().upper(),'source')
        b=replace(a,digest=sha256(b'b').hexdigest().upper())
        report=compare(package(content=(a,)),package('2.0.0',content=(b,)))
        self.assertEqual(report.classification,compat.UNKNOWN)
        self.assertEqual(report.canonical_record()['behavioral_equivalence'],'NOT_ESTABLISHED')

    def test_provenance_not_compatibility_or_trust(self):
        ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','A'*64)
        report=compare(package(),package('2.0.0',provenance=(ref,)))
        self.assertEqual(report.classification,compat.IDENTICAL)
        self.assertEqual(report.canonical_record()['provenance']['new'],[ref.record()])
        self.assertEqual(report.canonical_record()['trust'],'NOT_EVALUATED')

    def test_dimensions_fact_and_classification_preserved(self):
        report=compare(package(),package('2.0.0',required_capabilities=('Read',),exported_capabilities=('Write',)))
        dimensions={d['dimension']:d['classification'] for d in report.canonical_record()['dimensions']}
        self.assertEqual(dimensions['required_capabilities'],compat.BREAKING)
        self.assertEqual(dimensions['provided_capabilities'],compat.ADDITIVE)
        self.assertEqual(report.classification,compat.BREAKING)
        self.assertEqual(report.changes[0].record()['classification'],report.changes[0].classification)

    def test_unknown_not_promoted_by_additive_changes(self):
        d=fixture.coordinate('dep');old=package(dependencies=(d,))
        new=package('2.0.0',dependencies=(fixture.coordinate('dep','2.0.0'),),exported_capabilities=('Read',))
        self.assertEqual(compare(old,new).classification,compat.UNKNOWN)

    def test_canonical_order_and_report_fingerprint(self):
        a,b=symbols.symbol('A'),symbols.symbol('B')
        x=compare(package(exports=(a,b)),package('2.0.0',required_capabilities=('Write','Read')))
        y=compare(package(exports=(b,a)),package('2.0.0',required_capabilities=('Read','Write')))
        self.assertEqual(x.canonical_json(),y.canonical_json());self.assertEqual(x.fingerprint(),y.fingerprint())
        self.assertNotEqual(x.fingerprint(),compare(package(),package()).fingerprint())

    def test_direct_transitive_and_unrelated_impact(self):
        old=package();graph,lock=graph_fixture(old)
        plan=compat.plan_migration(old,package('2.0.0'),graph,lock)
        self.assertEqual([n.coordinate.name for n in plan.directly_affected],['direct'])
        self.assertEqual([n.coordinate.name for n in plan.transitively_exposed],['root'])
        self.assertTrue(plan.lock_refresh_required)
        obligations={s.obligation for s in plan.steps}
        self.assertTrue({'UPDATE_EXACT_DEPENDENCY','REFRESH_LOCK_EXTERNALLY','VERIFY_TARGET_TRUST_SEPARATELY'}<=obligations)

    def test_removed_export_and_requirement_migration_obligations(self):
        old=package(exports=(symbols.symbol(),));graph,lock=graph_fixture(old)
        new=package('2.0.0',required_capabilities=('Read',),dependencies=(fixture.coordinate('newdep'),))
        plan=compat.plan_migration(old,new,graph,lock,ns.PackageExportIndex(solver.ResolvedPackage(old),old.exports),
                                   ns.PackageExportIndex(solver.ResolvedPackage(new),new.exports))
        reasons={s.reason for s in plan.steps}
        self.assertTrue({'DECLARATION_REMOVED','CAPABILITY_ADDED','REQUIRED_DEPENDENCY_ADDED'}<=reasons)
        self.assertTrue(all(s.record()['automation']=='MANUAL_OR_EXTERNAL_ACTION_REQUIRED' for s in plan.steps))

    def test_same_coordinate_content_cannot_replace_publication(self):
        old=package();new=replace(old,exported_capabilities=('Read',))
        plan=compat.plan_migration(old,new)
        self.assertIn('REQUIRE_DISTINCT_PUBLICATION_COORDINATE',{s.obligation for s in plan.steps})

    def test_family_change_no_automatic_rename(self):
        plan=compat.plan_migration(package(),fixture.package('renamed'))
        self.assertIn('REVIEW_IDENTITY_FAMILY_CHANGE',{s.obligation for s in plan.steps})
        self.assertFalse(plan.canonical_record()['executes_migration'])

    def test_exact_graph_and_lock_binding_failures(self):
        old=package();graph,lock=graph_fixture(old)
        changed=replace(old,required_capabilities=('Read',))
        with self.assertRaises(compat.CompatibilityError) as caught:compat.plan_migration(changed,package('2.0.0'),graph)
        self.assertEqual(caught.exception.code,'MIGRATION_OLD_GRAPH_BINDING_MISMATCH')
        with self.assertRaises(compat.CompatibilityError) as caught:compat.plan_migration(changed,package('2.0.0'),lock=lock)
        self.assertEqual(caught.exception.code,'MIGRATION_OLD_LOCK_BINDING_MISMATCH')
        other=solver.solve(package(),fixture.universe())
        with self.assertRaises(compat.CompatibilityError):compat.plan_migration(old,package('2.0.0'),graph,locks.PackageLock(other))

    def test_lock_refresh_absent_identical_or_unrelated(self):
        old=package();graph,lock=graph_fixture(old)
        self.assertFalse(compat.plan_migration(old,old,graph,lock).lock_refresh_required)
        self.assertFalse(compat.plan_migration(old,package('2.0.0'),graph).lock_refresh_required)
        other=solver.solve(fixture.package('other'),fixture.universe())
        self.assertFalse(compat.plan_migration(old,package('2.0.0'),lock=locks.PackageLock(other)).lock_refresh_required)

    def test_no_mutation_and_immutable_results(self):
        old=package();new=package('2.0.0');graph,lock=graph_fixture(old)
        before=(old.canonical_json(),new.canonical_json(),graph.canonical_json(),lock.canonical_json())
        plan=compat.plan_migration(old,new,graph,lock)
        self.assertEqual(before,(old.canonical_json(),new.canonical_json(),graph.canonical_json(),lock.canonical_json()))
        for obj,field in ((plan,'steps'),(plan.report,'changes'),(plan.steps[0],'reason')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,None)
        record=plan.canonical_record();record['steps'].clear();self.assertTrue(plan.steps)

    def test_separation_no_live_calls(self):
        from authority.engine import AuthorityEngine
        old=package();graph,lock=graph_fixture(old)
        with (patch.object(solver,'solve',side_effect=AssertionError('solver')),
            patch.object(registry.RegistryCatalog,'query',side_effect=AssertionError('registry')),
            patch.object(publishing,'publish',side_effect=AssertionError('publish')),
            patch.object(cache.PackageCache,'put',side_effect=AssertionError('cache')),
            patch.object(AuthorityEngine,'check',side_effect=AssertionError('authority'))):
            compat.plan_migration(old,package('2.0.0'),graph,lock)

    def test_large_iterative_impact_and_plan_determinism(self):
        old=package();members=[old]
        for i in range(1100):members.append(fixture.package('chain'+str(i),dependencies=(members[-1].coordinate,)))
        graph=solver.solve(members[-1],fixture.universe(*reversed(members[:-1])))
        a=compat.plan_migration(old,package('2.0.0'),graph)
        b=compat.plan_migration(package(),package('2.0.0'),graph)
        self.assertEqual(len(a.directly_affected),1);self.assertEqual(len(a.transitively_exposed),1099)
        self.assertEqual(a.canonical_json(),b.canonical_json());self.assertEqual(a.fingerprint(),b.fingerprint())

    def test_static_security_and_fixed_diagnostics(self):
        tree=ast.parse(Path(compat.__file__).read_text(encoding='utf-8'))
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports|={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertFalse(imports&{'os','pathlib','subprocess','socket','requests','authority.engine','tooling.package_registry'})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls&{'open','eval','exec','__import__','solve','publish'})
        for args in ((None,package()),(package(),{})):
            with self.assertRaises(compat.CompatibilityError) as caught:compat.compare_packages(*args)
            self.assertEqual(str(caught.exception),'COMPATIBILITY_INPUT_INVALID')


if __name__=='__main__':unittest.main()
