"""P14.12 compositional structural evidence, honest unavailable authentication."""
import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_supply_chain as chain
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_registry as registry
import tooling.package_publishing as publishing
import tooling.package_artifacts as artifacts
import tooling.package_trust as trust
import tooling.package_cache as cache
import tooling.package_compatibility as compat
import p14_2_deterministic_dependency_solver_test as packages
import p14_9_package_publishing_test as publication_fixture
import p14_11_managed_native_hybrid_package_artifacts_test as artifact_fixture
import p14_6_package_signing_integrity_provenance_trust_test as trust_fixture
from tooling.build_artifact import canonical_json_bytes
from hashlib import sha256


def basic():
    request=publication_fixture.material()
    return chain.SupplyChainEvidence(request.manifest,request.members,request.expected_content)


def full():
    q=publication_fixture.material();p=publication_fixture.policy(q)
    before=registry.RegistryCatalog(())
    result=publishing.publish(before,q,p)
    m,a,b,pa,pb,raw=artifact_fixture.material(q.manifest)
    bundle=artifacts.ArtifactBundle(m.content_identity(),(a,b),(pa,pb))
    builds=(chain.SuppliedBuild(a.path,pa.data,a.build.fingerprint),chain.SuppliedBuild(b.path,raw,b.build.fingerprint))
    graph=solver.solve(m,packages.universe())
    return chain.SupplyChainEvidence(m,q.members,m.content_identity(),graph,locks.PackageLock(graph),
        result.catalog.records[0],result.catalog,result.receipt,before,result.catalog,p,bundle,builds,(a.air,))


def codes(report):return {d['code'] for d in report.record()['diagnostics']}


class SupplyChainTests(unittest.TestCase):
    def test_schema_profile_immutable_and_unknown(self):
        profile=chain.ValidationProfile()
        self.assertEqual(chain.validate_supply_chain(basic()).record()['schema'],chain.SCHEMA)
        with self.assertRaises(FrozenInstanceError):profile.name='OTHER'
        with self.assertRaises(ValueError):chain.ValidationProfile('OTHER')

    def test_integrity_profile_and_optional_absence(self):
        report=chain.validate_supply_chain(basic())
        self.assertEqual(report.status,'VALID')
        self.assertIn('MISSING_OPTIONAL_EVIDENCE',codes(report))
        self.assertFalse(report.record()['grants_authority'])

    def test_member_missing_and_tamper_invalid(self):
        e=basic()
        for members in ((),(replace(e.members[0],data=b'changed'),),e.members+e.members):
            report=chain.validate_supply_chain(replace(e,members=members))
            self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_CONTENT_INTEGRITY_FAILED',codes(report))

    def test_missing_members_incomplete_not_invalid(self):
        report=chain.validate_supply_chain(replace(basic(),members=None))
        self.assertEqual(report.status,'INCOMPLETE')
        self.assertIn('SUPPLY_CHAIN_REQUIRED_EVIDENCE_MISSING',codes(report))

    def test_expected_package_identity_mismatch(self):
        report=chain.validate_supply_chain(replace(basic(),expected_content=pm.PackageContentIdentity('F'*64)))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_PACKAGE_IDENTITY_MISMATCH',codes(report))

    def test_lock_profile_exact_match(self):
        e=full();report=chain.validate_supply_chain(e,chain.ValidationProfile('LOCK_RESTORE_CHAIN'))
        self.assertEqual(report.status,'VALID')

    def test_lock_substitution_and_graph_mismatch(self):
        e=full();changed=replace(e.manifest,required_capabilities=('Read',))
        lock=locks.PackageLock(solver.solve(changed,packages.universe()))
        report=chain.validate_supply_chain(replace(e,lock=lock))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_LOCK_MISMATCH',codes(report))

    def test_registry_and_publication_profile(self):
        report=chain.validate_supply_chain(full(),chain.ValidationProfile('REGISTRY_PUBLICATION_CHAIN'))
        self.assertEqual(report.status,'VALID')
        self.assertEqual(report.record()['authentication']['publisher'],'EXTERNAL_PRECONDITION')
        self.assertEqual(report.record()['authentication']['final_trust'],'NOT_ESTABLISHED')

    def test_registry_coordinate_or_content_mismatch(self):
        e=full()
        for m in (packages.package('other'),replace(e.manifest,exported_capabilities=('Read',))):
            report=chain.validate_supply_chain(replace(e,registry_record=registry.RegistryRecord(m)))
            self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_REGISTRY_MISMATCH',codes(report))

    def test_registry_blob_missing_or_corrupt(self):
        e=full();r=e.registry
        report=chain.validate_supply_chain(replace(e,registry=registry.RegistryCatalog(r.records)))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_REGISTRY_MISMATCH',codes(report))

    def test_catalog_only_passive_signature_payload_association(self):
        e=basic();signature=replace(trust_fixture.envelope(e.manifest),payload_fingerprint='F'*64)
        record=registry.RegistryRecord(e.manifest,signature)
        blob=registry.RegistryBlob(e.manifest.content[0].digest,e.members[0].data)
        report=chain.validate_supply_chain(replace(e,registry=registry.RegistryCatalog((record,),(blob,))))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_SIGNATURE_MISMATCH',codes(report))

    def test_publication_package_policy_and_snapshot_tamper(self):
        e=full()
        for field,value in (('content_identity',pm.PackageContentIdentity('F'*64).record()),
            ('publisher','unauthorized'),('policy_fingerprint','F'*64),('previous_state','F'*64),
            ('resulting_state','F'*64),('runtime_authority_granted',True),('status','UNKNOWN')):
            r=e.publication.record();r[field]=value
            receipt=publishing.PublicationReceipt(json.dumps(r))
            report=chain.validate_supply_chain(replace(e,publication=receipt))
            self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_PUBLICATION_MISMATCH',codes(report))

    def test_publication_missing_required_incomplete(self):
        e=replace(full(),publication=None)
        self.assertEqual(chain.validate_supply_chain(e,chain.ValidationProfile('REGISTRY_PUBLICATION_CHAIN')).status,'INCOMPLETE')
        self.assertEqual(chain.validate_supply_chain(e).status,'VALID')

    def test_publication_duplicate_json_keys_invalid(self):
        e=full();receipt=publishing.PublicationReceipt('{"schema":"a","schema":"b"}')
        self.assertEqual(chain.validate_supply_chain(replace(e,publication=receipt)).status,'INVALID')

    def test_idempotent_retry_transition(self):
        e=full();q=publication_fixture.material()
        retry=publishing.publish(e.after,q,e.publication_policy)
        report=chain.validate_supply_chain(replace(e,before=e.after,publication=retry.receipt))
        self.assertEqual(report.status,'VALID')

    def test_artifact_profile_and_full_structural_profile(self):
        e=full()
        for name in ('PACKAGE_ARTIFACT_CHAIN','FULL_STRUCTURAL_SUPPLY_CHAIN'):
            report=chain.validate_supply_chain(e,chain.ValidationProfile(name))
            self.assertEqual(report.status,'VALID')
            self.assertEqual(report.record()['semantic_authority'],'CANONICAL_AIR')
            nodes={n['kind'] for n in report.record()['nodes']}
            self.assertTrue({'AIR_REFERENCE','GENERATED_SOURCE_REFERENCE','ARTIFACT_DESCRIPTOR'} <= nodes)

    def test_artifact_wrong_package(self):
        e=full();other=artifact_fixture.hybrid()
        report=chain.validate_supply_chain(replace(e,artifacts=other))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_ARTIFACT_PACKAGE_MISMATCH',codes(report))

    def test_corrupt_hybrid_payload_not_discarded(self):
        e=full();bundle=object.__new__(artifacts.ArtifactBundle)
        for field in ('package','descriptors'):object.__setattr__(bundle,field,getattr(e.artifacts,field))
        payload=object.__new__(artifacts.ArtifactPayload)
        object.__setattr__(payload,'digest',e.artifacts.payloads[0].digest);object.__setattr__(payload,'data',b'corrupt')
        object.__setattr__(bundle,'payloads',(payload,)+e.artifacts.payloads[1:])
        report=chain.validate_supply_chain(replace(e,artifacts=bundle))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_ARTIFACT_DIGEST_MISMATCH',codes(report))

    def test_missing_build_and_air_required_incomplete(self):
        e=full();profile=chain.ValidationProfile('PACKAGE_ARTIFACT_CHAIN')
        for changed in (replace(e,builds=()),replace(e,builds=e.builds[:1]),replace(e,air=())):
            self.assertEqual(chain.validate_supply_chain(changed,profile).status,'INCOMPLETE')

    def test_build_reference_and_air_contradictions(self):
        e=full();d=e.artifacts.descriptors[0]
        for field in ('build','air'):
            changed=replace(d,**{field:replace(getattr(d,field),fingerprint='F'*64)})
            bundle=artifacts.ArtifactBundle(e.artifacts.package,(changed,)+e.artifacts.descriptors[1:],e.artifacts.payloads)
            report=chain.validate_supply_chain(replace(e,artifacts=bundle))
            self.assertEqual(report.status,'INVALID')
            self.assertIn('SUPPLY_CHAIN_BUILD_BINDING_MISMATCH' if field=='build' else 'SUPPLY_CHAIN_AIR_BINDING_MISMATCH',codes(report))

    def test_supplied_air_exact_not_display_names(self):
        e=full();report=chain.validate_supply_chain(replace(e,air=(replace(e.air[0],fingerprint='F'*64),)))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_AIR_BINDING_MISMATCH',codes(report))

    def test_native_profile_widening_invalid(self):
        e=full();d=next(d for d in e.artifacts.descriptors if d.kind=='NATIVE')
        forged=object.__new__(artifacts.ArtifactDescriptor)
        from dataclasses import fields
        for f in fields(artifacts.ArtifactDescriptor):object.__setattr__(forged,f.name,getattr(d,f.name))
        object.__setattr__(forged,'profile','whole-language/v1')
        bundle=object.__new__(artifacts.ArtifactBundle)
        object.__setattr__(bundle,'package',e.artifacts.package);object.__setattr__(bundle,'payloads',e.artifacts.payloads)
        object.__setattr__(bundle,'descriptors',tuple(forged if x.kind=='NATIVE' else x for x in e.artifacts.descriptors))
        report=chain.validate_supply_chain(replace(e,artifacts=bundle))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_NATIVE_PROFILE_MISMATCH',codes(report))

    def test_provenance_reference_continuity(self):
        e=full();ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','E'*64)
        d=e.artifacts.descriptors[0];changed=replace(d,provenance=(ref,))
        bundle=artifacts.ArtifactBundle(e.artifacts.package,(changed,)+e.artifacts.descriptors[1:],e.artifacts.payloads)
        report=chain.validate_supply_chain(replace(e,artifacts=bundle))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_PROVENANCE_MISMATCH',codes(report))

    def test_managed_source_bytes_missing_matching_and_tampered(self):
        e=basic();raw=json.loads(artifact_fixture.managed_bytes())
        raw.pop('fingerprint');raw['project']['sources']=[{'path':e.members[0].path.value,
            'sha256':sha256(e.members[0].data).hexdigest()}];raw['project']['source_count']=1
        raw['fingerprint']={'algorithm':'sha256','value':sha256(canonical_json_bytes(raw)).hexdigest()}
        data=canonical_json_bytes(raw);path=pm.PackagePath('managed/build.json')
        d=artifacts.describe_managed(e.manifest,path,data)
        bundle=artifacts.ArtifactBundle(e.manifest.content_identity(),(d,),
                                      (artifacts.ArtifactPayload(artifact_fixture.digest(data),data),))
        e=replace(e,artifacts=bundle,builds=(chain.SuppliedBuild(path,data,d.build.fingerprint),),air=(d.air,))
        profile=chain.ValidationProfile('PACKAGE_ARTIFACT_CHAIN')
        self.assertEqual(chain.validate_supply_chain(e,profile).status,'INCOMPLETE')
        self.assertEqual(chain.validate_supply_chain(replace(e,sources=e.members),profile).status,'VALID')
        report=chain.validate_supply_chain(replace(e,sources=(replace(e.members[0],data=b'tampered'),)),profile)
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_PROVENANCE_MISMATCH',codes(report))

    def test_native_generated_source_bytes_do_not_become_authorship(self):
        e=full();native=next(b for b in e.builds if b.path.value.startswith('native/'))
        builds=tuple(replace(b,source_bytes=b'tampered') if b==native else b for b in e.builds)
        report=chain.validate_supply_chain(replace(e,builds=builds))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_PROVENANCE_MISMATCH',codes(report))

    def test_passive_signature_unverified_and_required_authentication(self):
        e=basic();e=replace(e,signature=trust_fixture.envelope(e.manifest))
        report=chain.validate_supply_chain(e)
        self.assertEqual(report.record()['structural_status'],'VALID')
        self.assertEqual(report.record()['authentication']['signature'],'UNVERIFIED')
        self.assertEqual(chain.validate_supply_chain(e,chain.ValidationProfile(require_authentication=True)).status,'UNVERIFIED')
        self.assertEqual(chain.validate_supply_chain(basic(),chain.ValidationProfile(require_authentication=True)).status,'INCOMPLETE')

    def test_signature_malformed_and_payload_mismatch(self):
        e=basic();s=trust_fixture.envelope(e.manifest)
        forged=object.__new__(trust.SignatureEnvelope)
        for field in ('signer_fingerprint','payload_fingerprint','signature','algorithm','schema'):
            object.__setattr__(forged,field,getattr(s,field))
        object.__setattr__(forged,'signature',b'short')
        for signature,code in ((forged,'SUPPLY_CHAIN_SIGNATURE_MALFORMED'),
            (replace(s,payload_fingerprint='F'*64),'SUPPLY_CHAIN_SIGNATURE_MISMATCH')):
            report=chain.validate_supply_chain(replace(e,signature=signature))
            self.assertEqual(report.status,'INVALID');self.assertIn(code,codes(report))

    def test_policy_approval_cannot_substitute_for_crypto(self):
        e=basic();e=replace(e,signature=trust_fixture.envelope(e.manifest),public_key=trust_fixture.KEY,
                           trust_policy=trust_fixture.policy(e.manifest))
        report=chain.validate_supply_chain(e,chain.ValidationProfile(require_authentication=True))
        self.assertEqual(report.status,'UNVERIFIED');self.assertEqual(report.record()['authentication']['final_trust'],'NOT_ESTABLISHED')
        self.assertIn('CRYPTO_PROVIDER_UNAVAILABLE',report.canonical_json)

    def test_cache_supplied_in_memory_reverified_without_io(self):
        e=basic();entry=cache.CacheEntry(e.manifest,e.members)
        self.assertEqual(chain.validate_supply_chain(replace(e,cache_entry=entry)).status,'VALID')
        wrong=cache.CacheEntry(packages.package('other'),())
        report=chain.validate_supply_chain(replace(e,cache_entry=wrong))
        self.assertEqual(report.status,'INVALID');self.assertIn('SUPPLY_CHAIN_CACHE_MISMATCH',codes(report))

    def test_compatibility_context_not_integrity_or_trust(self):
        e=basic();report=compat.compare_packages(e.manifest,replace(e.manifest,required_capabilities=('Read',)))
        result=chain.validate_supply_chain(replace(e,compatibility=report))
        self.assertEqual(result.status,'VALID')
        self.assertIn('NON_SUPPLY_CHAIN_METADATA',result.canonical_json)

    def test_determinism_permutation_and_independent_fixtures(self):
        e=full();other=replace(e,builds=tuple(reversed(e.builds)),air=tuple(reversed(e.air)))
        a=chain.validate_supply_chain(e);b=chain.validate_supply_chain(other)
        self.assertEqual(a.canonical_json,b.canonical_json);self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertEqual(a.fingerprint(),chain.validate_supply_chain(full()).fingerprint())
        self.assertNotEqual(a.fingerprint(),e.manifest.content_identity().fingerprint)

    def test_report_immutable_detached_and_no_attribution(self):
        report=chain.validate_supply_chain(full())
        with self.assertRaises(FrozenInstanceError):report.canonical_json='changed'
        record=report.record();record['nodes'].clear();self.assertTrue(report.record()['nodes'])
        self.assertFalse(report.record()['real_world_attribution']);self.assertNotIn(str(ROOT),report.canonical_json)

    def test_no_mutation_and_no_live_operations(self):
        from runtime.engine import RuntimeEngine
        from authority.engine import AuthorityEngine
        from native_backend import native_execution as native
        e=full();before=(e.lock.canonical_json(),e.registry.snapshot().canonical_json(),e.manifest.canonical_json())
        with (patch.object(solver,'solve',side_effect=AssertionError('solver')),
            patch.object(publishing,'publish',side_effect=AssertionError('publish')),
            patch.object(registry.RegistryCatalog,'query',side_effect=AssertionError('query')),
            patch.object(cache.PackageCache,'put',side_effect=AssertionError('cache')),
            patch.object(RuntimeEngine,'execute',side_effect=AssertionError('runtime')),
            patch.object(AuthorityEngine,'check',side_effect=AssertionError('authority')),
            patch.object(native,'build_native',side_effect=AssertionError('compile')),
            patch.object(native,'dispatch_native',side_effect=AssertionError('dispatch'))):
            self.assertEqual(chain.validate_supply_chain(e).status,'VALID')
        self.assertEqual(before,(e.lock.canonical_json(),e.registry.snapshot().canonical_json(),e.manifest.canonical_json()))

    def test_large_evidence_graph_iterative(self):
        e=basic();members=[e.manifest]
        for i in range(1000):members.append(packages.package('chain'+str(i),dependencies=(members[-1].coordinate,)))
        graph=solver.solve(members[-1],packages.universe(*members[:-1]))
        report=chain.validate_supply_chain(replace(e,graph=graph,lock=locks.PackageLock(graph)))
        self.assertEqual(report.status,'VALID')
        self.assertEqual(sum(n['kind']=='RESOLVED_PACKAGE' for n in report.record()['nodes']),1001)

    def test_security_static_audit(self):
        tree=ast.parse(Path(chain.__file__).read_text(encoding='utf-8'))
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports|={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertFalse(imports&{'os','pathlib','subprocess','socket','requests','authority.engine','runtime.engine'})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls&{'open','exec','eval','__import__','publish','solve','build_native','dispatch_native'})


if __name__=='__main__':unittest.main()
