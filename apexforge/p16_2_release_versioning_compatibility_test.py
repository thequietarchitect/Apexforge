"""P16.2 explicit policy evidence and passive upgrade boundaries."""
import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
from tooling import release_architecture as r
from tooling import release_versioning as v
from tooling import package_manifest as pm
from tooling import package_compatibility as pc

EVIDENCE=pm.CanonicalReference("apexforge.release-review/v1","provenance-scope","A"*64)


def fixture(statuses=None):
    source=r.ReleaseIdentity("source","2.0.0","STABLE",r.P15_BASELINE)
    target=r.ReleaseIdentity("target","2.1.0","STABLE",r.P15_BASELINE)
    surfaces=tuple(v.ReleaseVersionSurface(r.ReleaseTarget(t,r.PROFILE if t=="native-win-x64" else ""),
                   domain,"apexforge") for t,domain in v.PRIMARY)
    versions=("10.1.3","0.1.0","0.1.0",r.PROFILE)
    sources=tuple(v.ReleaseSurfaceVersion(source,s,version,(EVIDENCE,)) for s,version in zip(surfaces,versions))
    targets=tuple(replace(m,release=target) for m in sources)
    statuses=("COMPATIBLE",)*4 if statuses is None else statuses
    declarations=[]
    for a,b,status in zip(sources,targets,statuses):
        if status is not None:
            migration=v.ReleaseMigrationReference("manual-review",a,b,"P16.9",(EVIDENCE,)) if status=="MIGRATION_REQUIRED" else None
            declarations.append(v.ReleaseCompatibilityDeclaration(a,b,status,(EVIDENCE,),migration))
    return v.ReleaseCompatibilityPolicy("review","v1",source,target,surfaces,sources,targets,
                                       tuple(declarations),(EVIDENCE,))


def finding(policy,target="python"):
    return next(f for f in v.compatibility_matrix(policy) if f.surface.target.identifier==target)


class ContractTests(unittest.TestCase):
    def error(self,code,factory):
        with self.assertRaises(v.ReleaseVersioningError) as caught:
            factory()
        self.assertEqual(caught.exception.code,code)
        self.assertEqual(str(caught.exception),code)

    def test_release_version_explicit_and_opaque(self):
        p=fixture()
        self.assertEqual(p.source.version,"2.0.0")
        self.assertEqual(p.record()["version_ordering"],"NOT_DEFINED")
        other=replace(p.source,version="opaque-review")
        self.assertEqual(other.version,"opaque-review")

    def test_all_policy_mapping_decision_records_immutable(self):
        p=fixture(("MIGRATION_REQUIRED","COMPATIBLE","COMPATIBLE","COMPATIBLE"))
        d=next(d for d in p.declarations if d.status=="MIGRATION_REQUIRED")
        objects=(p,p.source,p.surfaces[0],p.source_versions[0],d,d.migration,finding(p),
                 v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p)))
        for obj in objects:
            field=next(iter(obj.__dataclass_fields__))
            with self.assertRaises(FrozenInstanceError):
                setattr(obj,field,None)

    def test_version_domains_distinct_not_forced_equal(self):
        p=fixture()
        self.assertEqual({m.version for m in p.source_versions},{"10.1.3","0.1.0",r.PROFILE})
        self.assertNotIn(p.source.version,{m.version for m in p.source_versions})
        python=next(s for s in p.surfaces if s.target.identifier=="python")
        self.error("RELEASE_VERSION_DOMAIN_INVALID",lambda:replace(python,domain="VSCODE_EXTENSION"))
        self.error("RELEASE_VERSION_DOMAIN_INVALID",lambda:replace(python,domain="UNKNOWN"))

    def test_mapping_exact_release_bound_and_no_compatibility(self):
        m=fixture().source_versions[0]
        self.assertFalse(m.record()["implies_compatibility"])
        self.assertNotEqual(m.fingerprint(),replace(m,release=replace(m.release,version="other")).fingerprint())

    def test_mapping_version_syntax_and_provenance_immutable(self):
        m=fixture().source_versions[0]
        for value in (None,"",123,"arbitrary expression()","../value"):
            self.error("RELEASE_SURFACE_VERSION_INVALID",lambda value=value:replace(m,version=value))
        self.error("RELEASE_PROVENANCE_INVALID",lambda:replace(m,provenance=list(m.provenance)))

    def test_no_semver_same_major_channel_or_identity_inference(self):
        p=fixture((None,)*4)
        self.assertEqual(p.source.channel,p.target.channel)
        self.assertEqual([f.status for f in v.compatibility_matrix(p)],["UNKNOWN"]*4)
        self.assertEqual(v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p)).status,"INCOMPLETE")

    def test_identical_surface_versions_still_need_policy(self):
        p=fixture((None,)*4)
        self.assertEqual({m.version for m in p.source_versions},{m.version for m in p.target_versions})
        self.assertEqual(finding(p).status,"UNKNOWN")

    def test_missing_mapping_distinguished_from_missing_declaration(self):
        p=fixture((None,)*4)
        f=finding(p)
        self.assertEqual(f.record()["reason"],"RELEASE_COMPATIBILITY_UNKNOWN")
        p=replace(p,source_versions=())
        f=finding(p)
        self.assertEqual(f.status,"UNKNOWN")
        self.assertEqual(f.record()["reason"],"RELEASE_VERSION_MAPPING_MISSING")
        self.assertIsNone(f.record()["source_version"])

    def test_explicit_statuses_remain_surface_specific(self):
        p=fixture(("COMPATIBLE","MIGRATION_REQUIRED","INCOMPATIBLE","UNKNOWN"))
        statuses={f.surface.target.identifier:f.status for f in v.compatibility_matrix(p)}
        self.assertEqual(statuses,{"python":"COMPATIBLE","vscode":"MIGRATION_REQUIRED",
                                  "visual-studio":"INCOMPATIBLE","native-win-x64":"UNKNOWN"})
        self.assertEqual({f.surface.target.identifier:f.record()["upgrade_status"] for f in v.compatibility_matrix(p)},
                         {"python":"DIRECT","vscode":"MIGRATION_REQUIRED","visual-studio":"UNSUPPORTED",
                          "native-win-x64":"INCOMPLETE"})
        self.assertEqual(v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p)).status,"UNSUPPORTED")

    def test_explicit_non_unknown_requires_evidence(self):
        d=fixture().declarations[0]
        for status in ("COMPATIBLE","INCOMPATIBLE"):
            self.error("RELEASE_COMPATIBILITY_EVIDENCE_MISSING",lambda status=status:replace(d,status=status,evidence=()))
        self.assertEqual(replace(d,status="UNKNOWN",evidence=()).status,"UNKNOWN")
        self.error("RELEASE_COMPATIBILITY_STATUS_INVALID",lambda:replace(d,status="SAFE"))

    def test_exact_source_target_and_surface_substitution_rejected(self):
        p=fixture()
        self.error("RELEASE_SOURCE_MISMATCH",lambda:replace(p,source=replace(p.source,version="changed")))
        self.error("RELEASE_TARGET_MISMATCH",lambda:replace(p,target=replace(p.target,channel="DEVELOPMENT")))
        d=p.declarations[0]
        different=next(m for m in p.target_versions if m.surface!=d.source.surface)
        self.error("RELEASE_COMPATIBILITY_BINDING_INVALID",lambda:replace(d,target=different))

    def test_mapping_substitution_rejected(self):
        p=fixture()
        a=p.source_versions[0]
        wrong=replace(a,version="changed")
        self.error("RELEASE_SOURCE_MISMATCH",lambda:replace(p,source_versions=(wrong,)+p.source_versions[1:]))
        a=p.target_versions[0]
        wrong=replace(a,provenance=())
        self.error("RELEASE_TARGET_MISMATCH",lambda:replace(p,target_versions=(wrong,)+p.target_versions[1:]))

    def test_policy_revision_changes_findings_and_replay_rejected(self):
        p=fixture()
        revised=replace(p,revision="v2")
        self.assertNotEqual(p.fingerprint(),revised.fingerprint())
        self.assertNotEqual(finding(p).fingerprint(),finding(revised).fingerprint())
        self.error("RELEASE_POLICY_MISMATCH",lambda:v.ReleaseUpgradeAssessment(revised,v.compatibility_matrix(p)))
        self.assertEqual(finding(p).record()["policy"],p.fingerprint())

    def test_conflicting_and_identical_duplicate_declarations_fail_closed(self):
        p=fixture()
        d=p.declarations[0]
        for extra in (d,replace(d,status="INCOMPATIBLE")):
            self.error("RELEASE_COMPATIBILITY_CONFLICT",lambda extra=extra:replace(p,declarations=p.declarations+(extra,)))

    def test_conflicting_version_mapping_fails_closed(self):
        p=fixture((None,)*4)
        m=p.source_versions[0]
        self.error("RELEASE_VERSION_MAPPING_CONFLICT",lambda:replace(p,source_versions=p.source_versions+(replace(m,version="other"),)))

    def test_direct_requires_explicit_complete_policy(self):
        p=fixture()
        a=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
        self.assertEqual(a.status,"DIRECT")
        self.assertEqual(a.record()["execution"],"NOT_PERFORMED")
        self.assertEqual(v.ReleaseUpgradeAssessment(p,()).status,"INCOMPLETE")
        self.assertEqual(v.ReleaseUpgradeAssessment(p,a.findings[:-1]).status,"INCOMPLETE")

    def test_newer_and_downgrade_not_automatically_allowed(self):
        p=fixture((None,)*4)
        old=replace(p.target,version="1.0.0")
        downgraded=replace(p,target=old,target_versions=tuple(replace(m,release=old) for m in p.target_versions))
        self.assertEqual(v.ReleaseUpgradeAssessment(downgraded,v.compatibility_matrix(downgraded)).status,"INCOMPLETE")
        explicit=fixture()
        old=replace(explicit.target,version="1.0.0")
        mappings=tuple(replace(m,release=old) for m in explicit.target_versions)
        by_surface={m.surface:m for m in mappings}
        declarations=tuple(replace(d,target=by_surface[d.target.surface]) for d in explicit.declarations)
        downgraded=replace(explicit,target=old,target_versions=mappings,declarations=declarations)
        self.assertEqual(v.ReleaseUpgradeAssessment(downgraded,v.compatibility_matrix(downgraded)).status,"DIRECT")
        self.assertEqual(v.ReleaseUpgradeAssessment(downgraded,v.compatibility_matrix(downgraded)).record()["rollback"],"NOT_PERFORMED")

    def test_migration_reference_exact_and_nonexecutable(self):
        p=fixture(("MIGRATION_REQUIRED","COMPATIBLE","COMPATIBLE","COMPATIBLE"))
        a=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
        self.assertEqual(a.status,"MIGRATION_REQUIRED")
        d=next(d for d in p.declarations if d.migration)
        self.assertFalse(d.migration.record()["executes_migration"])
        self.assertFalse(hasattr(d.migration,"script"))
        self.error("RELEASE_MIGRATION_REFERENCE_INVALID",lambda:replace(d,migration=None))
        other=replace(d.migration,target=replace(d.target,version="changed"))
        self.error("RELEASE_MIGRATION_REFERENCE_INVALID",lambda:replace(d,migration=other))

    def test_unknown_and_migration_mixture_stays_incomplete(self):
        p=fixture(("MIGRATION_REQUIRED","COMPATIBLE",None,"COMPATIBLE"))
        a=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
        self.assertEqual(a.status,"INCOMPLETE")
        self.assertTrue(any(f.status=="MIGRATION_REQUIRED" for f in a.findings))

    def test_schema_distance_does_not_infer_compatibility(self):
        p=fixture((None,)*4)
        surface=v.ReleaseVersionSurface(r.ReleaseTarget("python"),"SCHEMA_CONTRACT","apexforge.package")
        source=v.ReleaseSurfaceVersion(p.source,surface,"v1")
        target=v.ReleaseSurfaceVersion(p.target,surface,"v2")
        policy=replace(p,surfaces=(surface,),source_versions=(source,),target_versions=(target,))
        self.assertEqual(finding(policy).status,"UNKNOWN")

    def test_contract_and_language_domains_are_explicit_caller_evidence(self):
        p=fixture((None,)*4)
        for domain in ("PACKAGE_CONTRACT","LANGUAGE_SEMANTICS"):
            s=v.ReleaseVersionSurface(r.ReleaseTarget("python"),domain,"explicit-owner")
            a=v.ReleaseSurfaceVersion(p.source,s,"caller-declared")
            b=replace(a,release=p.target)
            policy=replace(p,surfaces=(s,),source_versions=(a,),target_versions=(b,))
            self.assertEqual(finding(policy).status,"UNKNOWN")

    def test_native_profile_unchanged_not_automatically_compatible(self):
        p=fixture((None,)*4)
        native=next(m for m in p.source_versions if m.surface.domain=="NATIVE_PROFILE")
        self.assertEqual(native.version,r.PROFILE)
        self.error("RELEASE_NATIVE_PROFILE_CHANGED",lambda:replace(native,version="other-profile"))
        with self.assertRaises(r.ReleaseArchitectureError):
            r.ReleaseTarget("native-arm64")
        self.assertEqual(finding(p,"native-win-x64").status,"UNKNOWN")

    def test_existing_python_and_editor_requirements_unchanged(self):
        root=Path(__file__).resolve().parent.parent
        self.assertIn('requires-python = ">=3.9"',(root/"pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn('"vscode": "^1.85.0"',(root/"editors/vscode-apexforge/package.json").read_text(encoding="utf-8"))
        manifest=(root/"editors/visualstudio-apexforge/src/ApexForge.VisualStudio/source.extension.vsixmanifest").read_text(encoding="utf-8")
        self.assertIn('Version="[17.0,)"',manifest)

    def test_release_compatible_does_not_override_package_compatibility(self):
        p=fixture()
        self.assertEqual(finding(p).status,"COMPATIBLE")
        old=pm.PackageManifest(pm.PackageCoordinate("fixture","part",pm.ExactVersion(1,0,0)))
        new=replace(old,required_capabilities=("Added.Requirement",))
        report=pc.compare_packages(old,new)
        self.assertEqual(report.classification,pc.BREAKING)
        self.assertFalse(report.structurally_compatible)
        self.assertFalse(p.record()["package_solver_override"])

    def test_policy_and_findings_grant_neither_authority_nor_trust(self):
        p=fixture()
        self.assertFalse(p.record()["grants_authority"])
        for f in v.compatibility_matrix(p):
            self.assertFalse(f.record()["grants_authority"])
            self.assertFalse(f.record()["grants_trust"])
            self.assertEqual(f.record()["authentication"],"CRYPTO_PROVIDER_UNAVAILABLE")
            self.assertEqual(f.record()["semantic_authority"],"CANONICAL_AIR")
        a=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
        self.assertFalse(a.record()["grants_authority"])

    def test_exact_p15_baseline_preserved_and_revisions_reidentify(self):
        p=fixture((None,)*4)
        self.assertEqual(p.source.baseline,r.P15_BASELINE)
        self.assertEqual(p.target.baseline,r.P15_BASELINE)
        changed=replace(p.source,baseline=replace(r.P15_BASELINE,commit="a"*40))
        mappings=tuple(replace(m,release=changed) for m in p.source_versions)
        other=replace(p,source=changed,source_versions=mappings)
        self.assertNotEqual(finding(p).fingerprint(),finding(other).fingerprint())

    def test_canonical_order_for_mappings_findings_and_evidence(self):
        p=fixture()
        reversed_policy=replace(p,surfaces=tuple(reversed(p.surfaces)),source_versions=tuple(reversed(p.source_versions)),
                                target_versions=tuple(reversed(p.target_versions)),declarations=tuple(reversed(p.declarations)))
        self.assertEqual(p.fingerprint(),reversed_policy.fingerprint())
        first=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
        second=v.ReleaseUpgradeAssessment(reversed_policy,tuple(reversed(v.compatibility_matrix(reversed_policy))))
        self.assertEqual(first.record(),second.record())
        self.assertEqual(first.fingerprint(),second.fingerprint())

    def test_bounded_explicit_inputs_no_callbacks_or_mutable_arrays(self):
        p=fixture()
        self.error("RELEASE_SURFACE_UNKNOWN",lambda:replace(p,surfaces=list(p.surfaces)))
        self.error("RELEASE_POLICY_INVALID",lambda:replace(p,declarations=(lambda:True,)))
        self.error("RELEASE_UPGRADE_FINDINGS_INVALID",lambda:v.ReleaseUpgradeAssessment(p,list(v.compatibility_matrix(p))))
        self.error("RELEASE_SURFACE_UNKNOWN",lambda:replace(p,surfaces=()))

    def test_no_host_or_execution_side_effects(self):
        with patch("subprocess.run",side_effect=AssertionError("process")), \
             patch("subprocess.Popen",side_effect=AssertionError("process")), \
             patch("socket.socket",side_effect=AssertionError("network")), \
             patch("os.getenv",side_effect=AssertionError("environment")), \
             patch("builtins.open",side_effect=AssertionError("filesystem")):
            p=fixture()
            a=v.ReleaseUpgradeAssessment(p,v.compatibility_matrix(p))
            record=a.record()
            for field in ("execution","installation","rollback","migration","publication"):
                self.assertEqual(record[field],"NOT_PERFORMED")

    def test_1000_deterministic_findings_and_assessments(self):
        p=fixture()
        surface=next(s for s in p.surfaces if s.target.identifier=="python")
        source=next(m for m in p.source_versions if m.surface==surface)
        target=next(m for m in p.target_versions if m.surface==surface)
        def build(i):
            status=v.STATUSES[i%4]
            migration=v.ReleaseMigrationReference("migration",source,target,"P16.9") if status=="MIGRATION_REQUIRED" else None
            declaration=v.ReleaseCompatibilityDeclaration(source,target,status,(EVIDENCE,),migration)
            policy=replace(p,identifier="case-"+str(i),surfaces=(surface,),source_versions=(source,),
                           target_versions=(target,),declarations=(declaration,))
            matrix=v.compatibility_matrix(policy)
            assessment=v.ReleaseUpgradeAssessment(policy,matrix)
            self.assertEqual(matrix[0].status,status)
            expected={"COMPATIBLE":"DIRECT","MIGRATION_REQUIRED":"MIGRATION_REQUIRED",
                      "INCOMPATIBLE":"UNSUPPORTED","UNKNOWN":"INCOMPLETE"}[status]
            self.assertEqual(assessment.status,expected)
            return (policy.identifier,matrix[0].fingerprint(),assessment.fingerprint())
        results=[build(i) for i in range(1000)]
        self.assertEqual(len(results),1000)
        independently_reconstructed=[build(i) for i in reversed(range(1000))]
        self.assertEqual(sorted(results),sorted(independently_reconstructed))
        first=replace(p,identifier="case-0",surfaces=(surface,),source_versions=(source,),target_versions=(target,),
                      declarations=(v.ReleaseCompatibilityDeclaration(source,target,"COMPATIBLE",(EVIDENCE,)),))
        self.assertEqual(results[0][2],v.ReleaseUpgradeAssessment(first,v.compatibility_matrix(first)).fingerprint())

    def test_static_security_and_owner_dependencies(self):
        tree=ast.parse(Path(v.__file__).read_text(encoding="utf-8"))
        imports=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                imports.update(alias.name for alias in node.names)
            if isinstance(node,ast.ImportFrom):
                imports.add(node.module)
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                self.assertNotIn(node.func.id,{"eval","exec","open","compile","__import__"})
        self.assertEqual(imports,{"dataclasses","re","tooling","tooling.domain_platform","tooling.package_manifest"})
        self.assertFalse(any(isinstance(node,(ast.AsyncFunctionDef,ast.Await)) for node in ast.walk(tree)))
        self.assertEqual({n.name for n in tree.body if isinstance(n,ast.ClassDef)},
            {"ReleaseVersioningError","ReleaseVersionSurface","ReleaseSurfaceVersion","ReleaseMigrationReference",
             "ReleaseCompatibilityDeclaration","ReleaseCompatibilityPolicy","ReleaseCompatibilityFinding","ReleaseUpgradeAssessment"})


if __name__=="__main__":
    unittest.main()
