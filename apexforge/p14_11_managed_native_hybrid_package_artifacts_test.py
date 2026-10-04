"""P14.11 supplied artifact identity/integrity; no backend build or dispatch."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_artifacts as artifacts
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_cache as cache
import tooling.package_registry as registry
import tooling.package_publishing as publishing
import tooling.build_artifact as build
import p14_2_deterministic_dependency_solver_test as fixture
import p12_5_native_profile_contract_test as native_fixture
from air.serialization import air_to_dict
from native_backend import native_execution as native
from native_backend.lowering_input import build_verified_air_lowering_input
from air.verify import AIRVerifier
from runtime.engine import RuntimeEngine


def digest(data):return sha256(data).hexdigest().upper()


def managed_bytes():
    # Existing canonical AIR transport and P11 build-envelope serialization; no source compilation.
    payload={'schema':build.BUILD_ARTIFACT_SCHEMA,'air':air_to_dict(native_fixture.fixture()),
             'project':{'entry':'directive:main','name':'fixture','source_count':0,'sources':[]}}
    fp=sha256(build.canonical_json_bytes(payload)).hexdigest()
    return build.canonical_json_bytes({**payload,'fingerprint':{'algorithm':'sha256','value':fp}})


def material(manifest=None):
    m=fixture.package('root') if manifest is None else manifest
    data=managed_bytes()
    managed=artifacts.describe_managed(m,pm.PackagePath('managed/build.json'),data)
    image=b'supplied native image fixture; never executed'
    receipt={'profile':artifacts.PROFILE,'air':managed.air.fingerprint,'owner_air':managed.air.fingerprint,
        'routing':'B'*64,'entry':'directive:main','states':['state:value','state:unchanged'],
        'source':'C'*64,'toolchain':{'cl.exe':'D'*64},'options':list(native.OPTIONS),'image':digest(image)}
    raw=native.canonical(receipt).encode('utf-8')
    descriptor=artifacts.describe_native(m,pm.PackagePath('native/opaque.bin'),image,raw,digest(raw),
                                        target=artifacts.NATIVE_TARGET,profile=artifacts.PROFILE)
    return m,managed,descriptor,artifacts.ArtifactPayload(digest(data),data),artifacts.ArtifactPayload(digest(image),image),raw


def hybrid():
    m,a,b,pa,pb,_=material()
    return artifacts.ArtifactBundle(m.content_identity(),(a,b),(pa,pb))


class PackageArtifactTests(unittest.TestCase):
    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(artifacts.PackageArtifactError) as caught:fn(*args,**kwargs)
        if code:self.assertEqual(caught.exception.code,code)

    def test_schema_kind_and_package_identity(self):
        m,a,b,pa,pb,_=material()
        self.assertEqual(a.schema,artifacts.SCHEMA);self.assertEqual(a.package,m.content_identity())
        self.assertEqual(a.kind,'MANAGED');self.assertEqual(b.kind,'NATIVE')
        self.assertNotEqual(a.digest,a.package.fingerprint);self.assertNotEqual(a.digest,b.digest)
        self.error(replace,a,schema='future',code='ARTIFACT_SCHEMA_UNSUPPORTED')

    def test_managed_actual_build_fingerprint(self):
        _,a,_,pa,_,_=material();record=json.loads(pa.data)
        self.assertEqual(a.build.fingerprint,record['fingerprint']['value'].upper())
        self.assertEqual(a.digest,digest(pa.data));self.assertNotEqual(a.build.fingerprint,a.digest)
        self.assertEqual(a.profile,build.BUILD_ARTIFACT_SCHEMA)

    def test_managed_air_matches_frozen_lowering(self):
        _,a,_,_,_,_=material();program=native_fixture.fixture()
        verified=AIRVerifier().verify(program).require_verified()
        lowering=build_verified_air_lowering_input(verified)
        self.assertEqual(a.air.fingerprint,lowering.transport_fingerprint)

    def test_managed_not_narrative_or_rich_document_native_label(self):
        m,*_=material()
        for schema in (build.BUILD_ARTIFACT_SCHEMA_V2,build.BUILD_ARTIFACT_SCHEMA_V3):
            raw=json.dumps({'schema':schema,'air':{}}).encode()
            self.error(artifacts.describe_managed,m,pm.PackagePath('build.json'),raw,
                       code='MANAGED_REPRESENTATION_UNSUPPORTED')

    def test_build_fingerprint_tampering_and_duplicate_keys(self):
        m,a,b,pa,pb,_=material();record=json.loads(pa.data);record['project']['name']='changed'
        self.error(artifacts.describe_managed,m,a.path,json.dumps(record).encode(),code='BUILD_FINGERPRINT_MISMATCH')
        self.error(artifacts.describe_managed,m,a.path,b'{"schema":"a","schema":"b"}',code='BUILD_EVIDENCE_INVALID')

    def test_native_frozen_profile_and_receipt_binding(self):
        _,a,b,pa,pb,raw=material();receipt=json.loads(raw)
        self.assertEqual(b.profile,'apexforge.native.win-x64.i64-literal-state-set/v1')
        self.assertEqual(b.build.fingerprint,digest(raw));self.assertEqual(b.air.fingerprint,receipt['air'])
        self.assertEqual(b.source.fingerprint,receipt['source']);self.assertEqual(b.digest,receipt['image'])
        self.assertEqual(b.target,'win-x64');self.assertEqual(b.path.value,'native/opaque.bin')

    def test_unsupported_native_targets_and_profiles(self):
        m,a,b,pa,pb,raw=material()
        for target,profile in (('linux-x64',artifacts.PROFILE),('win-arm64',artifacts.PROFILE),
            ('win-x64','whole-language/v1'),('mac-x64',artifacts.PROFILE)):
            self.error(artifacts.describe_native,m,b.path,pb.data,raw,digest(raw),target=target,profile=profile,
                       code='UNSUPPORTED_TARGET')

    def test_native_receipt_image_air_and_digest_mismatch(self):
        m,a,b,pa,pb,raw=material()
        self.error(artifacts.describe_native,m,b.path,b'changed',raw,digest(raw),target=b.target,profile=b.profile,
                   code='ARTIFACT_PAYLOAD_DIGEST_MISMATCH')
        self.error(artifacts.describe_native,m,b.path,pb.data,raw,'F'*64,target=b.target,profile=b.profile,
                   code='BUILD_FINGERPRINT_MISMATCH')
        record=json.loads(raw);record['owner_air']='F'*64;changed=native.canonical(record).encode()
        self.error(artifacts.describe_native,m,b.path,pb.data,changed,digest(changed),target=b.target,profile=b.profile,
                   code='ARTIFACT_BUILD_BINDING_INVALID')

    def test_hybrid_variant_identity_and_authority(self):
        bundle=hybrid();self.assertEqual(bundle.kind,'HYBRID')
        self.assertEqual({d.kind for d in bundle.descriptors},{'MANAGED','NATIVE'})
        self.assertEqual(len(bundle.payloads),2)
        self.assertEqual(bundle.canonical_record()['semantic_authority'],'CANONICAL_AIR')
        self.assertEqual(len({d.fingerprint() for d in bundle.descriptors}),2)

    def test_single_kind_bundle_forms(self):
        m,a,b,pa,pb,_=material()
        for d,p in ((a,pa),(b,pb)):
            self.assertEqual(artifacts.ArtifactBundle(m.content_identity(),(d,),(p,)).kind,d.kind)

    def test_exact_explicit_managed_native_selection(self):
        bundle=hybrid()
        for d in bundle.descriptors:self.assertEqual(bundle.select(d.kind,d.target,d.profile),d)

    def test_any_ambiguity_no_priority(self):
        self.error(hybrid().select,'ANY',code='AMBIGUOUS_VARIANT')

    def test_missing_variant_no_fallback_or_host_detection(self):
        m,a,b,pa,pb,_=material();bundle=artifacts.ArtifactBundle(m.content_identity(),(a,),(pa,))
        self.error(bundle.select,'NATIVE',b.target,b.profile,code='NO_SUPPORTED_VARIANT')
        self.error(bundle.select,'MANAGED',code='UNSUPPORTED_TARGET')
        self.error(bundle.select,'NATIVE','linux-x64',b.profile,code='UNSUPPORTED_TARGET')

    def test_multiple_same_target_variants_ambiguous(self):
        m,a,b,pa,pb,_=material();other=replace(a,path=pm.PackagePath('managed/other.json'))
        bundle=artifacts.ArtifactBundle(m.content_identity(),(a,other),(pa,))
        self.error(bundle.select,'MANAGED',a.target,a.profile,code='AMBIGUOUS_VARIANT')

    def test_canonical_order_independent_serialization_and_fingerprint(self):
        m,a,b,pa,pb,_=material()
        x=artifacts.ArtifactBundle(m.content_identity(),(a,b),(pa,pb))
        y=artifacts.ArtifactBundle(m.content_identity(),(b,a),(pb,pa))
        self.assertEqual(x.canonical_json(),y.canonical_json());self.assertEqual(x.fingerprint(),y.fingerprint())
        self.assertEqual(x.bundle_record(),y.bundle_record());self.assertEqual(x.fingerprint(),hybrid().fingerprint())
        self.assertNotEqual(x.fingerprint(),a.fingerprint());self.assertNotEqual(x.fingerprint(),m.content_identity().fingerprint)

    def test_missing_extra_duplicate_payload(self):
        m,a,b,pa,pb,_=material()
        for payloads,code in (((pa,),'ARTIFACT_PAYLOAD_SET_MISMATCH'),
            ((pa,pb,artifacts.ArtifactPayload(digest(b'extra'),b'extra')),'ARTIFACT_PAYLOAD_SET_MISMATCH'),
            ((pa,pb,pa),'ARTIFACT_PAYLOAD_DUPLICATE')):
            self.error(artifacts.ArtifactBundle,m.content_identity(),(a,b),payloads,code=code)

    def test_payload_corruption_rejected_at_admission(self):
        m,a,b,pa,pb,_=material()
        self.error(artifacts.ArtifactPayload,pa.digest,b'changed',code='ARTIFACT_PAYLOAD_DIGEST_MISMATCH')
        forged=object.__new__(artifacts.ArtifactPayload)
        object.__setattr__(forged,'digest',pa.digest);object.__setattr__(forged,'data',b'corrupt')
        self.error(artifacts.ArtifactBundle,m.content_identity(),(a,),(forged,),code='ARTIFACT_PAYLOAD_DIGEST_MISMATCH')

    def test_duplicate_descriptor_and_ancestor_path(self):
        m,a,b,pa,pb,_=material()
        self.error(artifacts.ArtifactBundle,m.content_identity(),(a,a),(pa,),code='ARTIFACT_PATH_DUPLICATE')
        other=replace(a,path=pm.PackagePath('managed'))
        self.error(artifacts.ArtifactBundle,m.content_identity(),(a,other),(pa,),code='ARTIFACT_PATH_CONFLICT')

    def test_package_content_substitution_rejected(self):
        m,a,b,pa,pb,_=material();changed=replace(m,required_capabilities=('Read',))
        self.error(artifacts.ArtifactBundle,changed.content_identity(),(a,b),(pa,pb),code='ARTIFACT_PACKAGE_BINDING_INVALID')

    def test_logical_path_host_boundary(self):
        for path in ('../payload','/payload','C:/payload','dir\\payload'):
            with self.assertRaises(pm.PackageManifestError):pm.PackagePath(path)
        canonical=hybrid().canonical_json();self.assertNotIn(str(ROOT),canonical)
        self.assertNotIn('timestamp',canonical);self.assertNotIn('hostname',canonical)

    def test_provenance_and_debug_reference_preserved(self):
        ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','E'*64)
        m,a,b,pa,pb,raw=material(fixture.package('root',provenance=(ref,)))
        debug=pm.CanonicalReference('apexforge.metadata-identity/v1','native-mapping','F'*64)
        b=replace(b,debug_metadata=debug)
        self.assertEqual(b.provenance,(ref,));self.assertEqual(b.record()['debug_metadata'],debug.record())
        self.assertNotIn('author',b.record());self.assertNotIn('machine_address',b.record())

    def test_entrypoint_exact_air_binding(self):
        m,a,b,pa,pb,raw=material();entry=pm.SymbolReference(a.air.fingerprint,'directive','directive:main')
        self.assertEqual(replace(a,entrypoint=entry).entrypoint,entry)
        self.error(replace,a,entrypoint=replace(entry,air_fingerprint='F'*64),code='ARTIFACT_ENTRYPOINT_INVALID')
        other=replace(entry,identity='directive:other')
        self.error(artifacts.describe_managed,m,a.path,pa.data,entrypoint=other,code='ARTIFACT_ENTRYPOINT_INVALID')
        self.error(artifacts.describe_native,m,b.path,pb.data,raw,digest(raw),target=b.target,profile=b.profile,
                   entrypoint=other,code='ARTIFACT_ENTRYPOINT_INVALID')

    def test_lock_exact_package_independent_of_variant(self):
        m,a,b,pa,pb,_=material();lock=locks.PackageLock(solver.solve(m,fixture.universe()))
        before=lock.canonical_json();bundle=hybrid()
        self.assertIs(bundle.validate_lock(lock),bundle);self.assertEqual(before,lock.canonical_json())
        wrong=locks.PackageLock(solver.solve(fixture.package('other'),fixture.universe()))
        self.error(bundle.validate_lock,wrong,code='ARTIFACT_LOCK_CONTENT_MISMATCH')

    def test_no_compilation_execution_authority_or_other_layer_mutation(self):
        from authority.engine import AuthorityEngine
        with (patch.object(native,'build_native',side_effect=AssertionError('build')),
            patch.object(native,'dispatch_native',side_effect=AssertionError('dispatch')),
            patch.object(RuntimeEngine,'execute',side_effect=AssertionError('runtime')),
            patch.object(AuthorityEngine,'check',side_effect=AssertionError('authority')),
            patch.object(registry.RegistryCatalog,'query',side_effect=AssertionError('query')),
            patch.object(publishing,'publish',side_effect=AssertionError('publish')),
            patch.object(cache.PackageCache,'put',side_effect=AssertionError('cache')),
            patch.object(solver,'solve',side_effect=AssertionError('solve'))):
            bundle=hybrid();bundle.select('NATIVE',artifacts.NATIVE_TARGET,artifacts.PROFILE)

    def test_immutable_models_and_detached_record(self):
        bundle=hybrid()
        for obj,field in ((bundle,'descriptors'),(bundle.descriptors[0],'digest'),(bundle.payloads[0],'data')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,None)
        record=bundle.canonical_record();record['artifacts'].clear();self.assertEqual(len(bundle.descriptors),2)

    def test_large_set_deterministic(self):
        m,a,b,pa,pb,_=material()
        descriptors=tuple(replace(a,path=pm.PackagePath('managed/build'+str(i)+'.json')) for i in range(1000))
        x=artifacts.ArtifactBundle(m.content_identity(),descriptors,(pa,))
        y=artifacts.ArtifactBundle(m.content_identity(),tuple(reversed(descriptors)),(pa,))
        self.assertEqual(x.fingerprint(),y.fingerprint());self.assertEqual(len(x.descriptors),1000)

    def test_static_security_and_crypto_not_claimed(self):
        source=Path(artifacts.__file__).read_text(encoding='utf-8');tree=ast.parse(source)
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports|={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertFalse(imports&{'subprocess','os','socket','requests','pathlib','authority.engine','runtime.engine'})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls&{'open','exec','eval','__import__','build_native','dispatch_native','solve'})
        self.assertNotIn('signature_valid',hybrid().canonical_json())


if __name__=='__main__':unittest.main()
