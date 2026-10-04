"""P14.7 test-owned local CAS roots; integrity, atomic publication and no trust inference."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_cache as cachemod
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_trust as trust
import tooling.package_capabilities as capabilities
import tooling.package_namespace as namespaces
import p14_2_deterministic_dependency_solver_test as fixture


def material(name='root',data=b'shared canonical bytes',**kwargs):
    member=trust.ContentMember(pm.PackagePath('src/main.apex'),data)
    descriptor=pm.ContentDescriptor(member.path,sha256(data).hexdigest().upper(),'source')
    return fixture.package(name,content=(descriptor,),**kwargs),(member,)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='p147-',dir=ROOT)
        self.root=Path(self.temp.name)
        self.cache=cachemod.PackageCache(self.root)
        self.addCleanup(self.temp.cleanup)

    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(cachemod.PackageCacheError) as caught: fn(*args,**kwargs)
        if code:self.assertEqual(caught.exception.code,code)
        return str(caught.exception)

    def recordpath(self,m):return self.root.joinpath(*self.cache.package_key(m.content_identity()))
    def blobpath(self,m):return self.root.joinpath(*self.cache.blob_key(m.content[0].digest))

    def test_explicit_root_and_invalid_roots(self):
        self.error(cachemod.PackageCache,'relative',code='CACHE_ROOT_INVALID')
        self.error(cachemod.PackageCache,self.root/'absent',code='CACHE_ROOT_MISSING')
        self.error(cachemod.PackageCache,self.root/'..',code='CACHE_ROOT_INVALID')

    def test_put_get_exact_content_and_immutable_entry(self):
        m,c=material();entry=self.cache.put(m,c)
        self.assertEqual(entry.identity,m.content_identity())
        self.assertEqual(entry.members,c)
        self.assertEqual(self.cache.get(entry.identity),entry)
        with self.assertRaises(FrozenInstanceError):entry.members=()

    def test_integrity_gate_no_record_on_failed_input(self):
        m,c=material()
        for supplied in ((),(replace(c[0],data=b'changed'),),c+(trust.ContentMember(pm.PackagePath('extra'),b'x'),)):
            self.error(self.cache.put,m,supplied,code='CACHE_INSERT_INTEGRITY_FAILED')
            self.assertFalse(self.recordpath(m).exists())
        self.assertEqual(list(self.root.iterdir()),[])

    def test_layout_only_digest_and_fixed_names(self):
        m,c=material();self.cache.put(m,c)
        self.assertTrue(self.recordpath(m).is_file());self.assertTrue(self.blobpath(m).is_file())
        self.assertNotIn('root',self.cache.package_key(m.content_identity()))
        self.assertFalse((self.root/'src').exists())
        self.assertEqual(self.blobpath(m).read_bytes(),c[0].data)

    def test_root_independent_canonical_record_metadata(self):
        m,c=material();a=self.cache.put(m,c)
        with tempfile.TemporaryDirectory(prefix='p147-other-',dir=ROOT) as other:
            b=cachemod.PackageCache(Path(other)).put(replace(m,metadata=(('title','not identity'),)),c)
            self.assertEqual(a.canonical_json(),b.canonical_json());self.assertEqual(a.fingerprint(),b.fingerprint())
            self.assertNotIn(str(other),b.canonical_json())
        self.assertNotIn(str(self.root),a.canonical_json())

    def test_idempotent_and_dedup_distinct_package_identity(self):
        a,c=material('a');b,_=material('b')
        first=self.cache.put(a,c);self.assertEqual(first,self.cache.put(a,c))
        second=self.cache.put(b,c)
        self.assertNotEqual(first.identity,second.identity)
        self.assertEqual(len(list((self.root/'blobs').rglob(a.content[0].digest))),1)
        self.assertEqual(len(list((self.root/'packages').rglob('record.json'))),2)

    def test_same_coordinate_different_content_coexists(self):
        a,c=material();b,d=material(data=b'different')
        x,y=self.cache.put(a,c),self.cache.put(b,d)
        self.assertEqual(a.coordinate,b.coordinate);self.assertNotEqual(x.identity,y.identity)
        self.assertEqual(self.cache.get(x.identity),x);self.assertEqual(self.cache.get(y.identity),y)
        with self.assertRaises(solver.PackageSolverError):fixture.universe(a,b)

    def test_existing_blob_mismatch_never_overwritten(self):
        m,c=material();self.cache.put(m,c);self.blobpath(m).write_bytes(b'corruption')
        self.error(self.cache.put,m,c,code='CACHE_BLOB_DIGEST_MISMATCH')
        self.assertEqual(self.blobpath(m).read_bytes(),b'corruption')
        self.error(self.cache.get,m.content_identity(),code='CACHE_BLOB_DIGEST_MISMATCH')

    def test_existing_record_mismatch_never_overwritten(self):
        m,c=material();self.cache.put(m,c);self.recordpath(m).write_bytes(b'corrupt')
        self.error(self.cache.put,m,c,code='CACHE_RECORD_EXISTING_MISMATCH')
        self.assertEqual(self.recordpath(m).read_bytes(),b'corrupt')

    def test_miss_missing_record_and_missing_blob(self):
        m,c=material();self.error(self.cache.get,m.content_identity(),code='CACHE_MISS')
        self.cache.put(m,c);self.recordpath(m).unlink()
        self.error(self.cache.get,m.content_identity(),code='CACHE_RECORD_MISSING')
        self.cache.put(m,c);self.blobpath(m).unlink()
        self.error(self.cache.get,m.content_identity(),code='CACHE_BLOB_MISSING')

    def test_invalid_record_duplicate_keys_unknown_schema(self):
        m,c=material();self.cache.put(m,c)
        for raw in (b'{',b'{"schema":"a","schema":"b"}',b'[]',b'{"schema":"future"}'):
            self.recordpath(m).write_bytes(raw)
            self.error(self.cache.get,m.content_identity(),code='CACHE_RECORD_INVALID')

    def test_record_identity_and_manifest_tampering(self):
        m,c=material();entry=self.cache.put(m,c)
        for mutate in (lambda r:r['content_identity'].update(fingerprint='F'*64),
                       lambda r:r['manifest'].update(name='changed')):
            raw=entry.canonical_record();mutate(raw)
            self.recordpath(m).write_text(json.dumps(raw),encoding='utf-8')
            self.error(self.cache.get,m.content_identity(),code='CACHE_PACKAGE_IDENTITY_MISMATCH')

    def test_noncanonical_record_rejected(self):
        m,c=material();entry=self.cache.put(m,c)
        self.recordpath(m).write_text(json.dumps(entry.canonical_record(),indent=2),encoding='utf-8')
        self.error(self.cache.get,m.content_identity(),code='CACHE_RECORD_INVALID')

    def test_untrusted_keys_not_paths(self):
        for value in ('../host','C:/host','A'*64):
            self.error(self.cache.get,value,code='CACHE_KEY_INVALID')
        for path in ('../host','C:/host','/host'):
            with self.assertRaises(pm.PackageManifestError):pm.PackagePath(path)

    def test_nonregular_object_rejected(self):
        m,c=material();self.cache.put(m,c);blob=self.blobpath(m)
        blob.unlink();blob.mkdir()
        self.error(self.cache.get,m.content_identity(),code='CACHE_PATH_NOT_REGULAR')

    def test_exact_lock_restore_view_no_solver_no_install(self):
        root,rc=material(dependencies=(fixture.coordinate('dep'),));dep,dc=material('dep')
        g=solver.solve(root,fixture.universe(dep));lock=locks.PackageLock(g);before=lock.canonical_json()
        self.cache.put(root,rc);self.cache.put(dep,dc)
        with patch.object(solver,'solve',side_effect=AssertionError('solver invoked')):
            view=self.cache.restore_view(lock)
        self.assertEqual(view.plan.lock,lock);self.assertEqual(view.plan.packages,g.nodes)
        self.assertFalse(view.plan.canonical_record()['installs_packages'])
        self.assertEqual(lock.canonical_json(),before)

    def test_lock_missing_content_does_not_substitute_coordinate(self):
        m,c=material();changed,d=material(data=b'alt');self.cache.put(changed,d)
        lock=locks.PackageLock(solver.solve(m,fixture.universe()))
        self.error(self.cache.restore_view,lock,code='CACHE_MISS')

    def test_failure_during_blob_publication_no_record_temp_cleanup(self):
        m,c=material()
        with patch.object(cachemod.os,'link',side_effect=OSError('injected')):
            self.error(self.cache.put,m,c,code='CACHE_IO_ERROR')
        self.assertFalse(self.recordpath(m).exists());self.assertEqual(list(self.root.rglob('*.tmp')),[])

    def test_failure_during_record_publication_no_valid_partial_entry(self):
        m,c=material();original=cachemod.os.link
        def fail_record(src,dst):
            if Path(dst).name=='record.json':raise OSError('injected')
            return original(src,dst)
        with patch.object(cachemod.os,'link',side_effect=fail_record):
            self.error(self.cache.put,m,c,code='CACHE_IO_ERROR')
        self.assertFalse(self.recordpath(m).exists());self.assertEqual(list(self.root.rglob('*.tmp')),[])
        self.error(self.cache.get,m.content_identity(),code='CACHE_RECORD_MISSING')
        self.assertEqual(self.cache.put(m,c).identity,m.content_identity())

    def test_duplicate_thread_insertion_idempotent(self):
        m,c=material()
        with ThreadPoolExecutor(max_workers=4) as executor:
            results=list(executor.map(lambda _:self.cache.put(m,c),range(8)))
        self.assertTrue(all(x==results[0] for x in results))
        self.assertEqual(list(self.root.rglob('*.tmp')),[])

    def test_crypto_unavailable_trust_not_inferred(self):
        m,c=material();e=self.cache.put(m,c)
        key=b'K'*32
        envelope=trust.SignatureEnvelope(trust.key_fingerprint(key),trust.payload_fingerprint(e.manifest),b'\0'*64)
        r=trust.verify_package(e.manifest,e.members,envelope,key).record()
        self.assertEqual(r['signature'],'CRYPTO_PROVIDER_UNAVAILABLE')
        self.assertIsNone(r['accepted']);self.assertFalse(r['grants_runtime_authority'])
        self.assertFalse(any(importlib.util.find_spec(n) for n in ('cryptography','nacl','sigstore')))

    def test_provenance_capability_and_export_identity_preserved(self):
        ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','A'*64)
        sym=pm.SymbolReference('B'*64,'function','function:Run','language.module')
        m,c=material(provenance=(ref,),exports=(sym,),required_capabilities=('Missing',))
        entry=self.cache.put(m,c);self.assertEqual(entry.manifest.provenance,(ref,));self.assertEqual(entry.manifest.exports,(sym,))
        index=namespaces.PackageExportIndex(solver.ResolvedPackage(entry.manifest),(sym,))
        self.assertEqual(index.provider.content_identity,m.content_identity())
        self.assertFalse(capabilities.validate_capabilities(solver.solve(entry.manifest,fixture.universe())).compatible)

    def test_large_member_and_package_sets(self):
        members=tuple(trust.ContentMember(pm.PackagePath('data/f'+str(i)),str(i).encode()) for i in range(300))
        descriptors=tuple(pm.ContentDescriptor(x.path,sha256(x.data).hexdigest().upper(),'data') for x in members)
        m=fixture.package('many',content=descriptors);self.cache.put(m,tuple(reversed(members)))
        self.assertEqual(len(self.cache.get(m.content_identity()).members),300)
        for i in range(100):
            package,contents=material('pkg'+str(i));self.cache.put(package,contents)
        self.assertEqual(len(list((self.root/'packages').rglob('record.json'))),101)

    def test_resource_lifetime_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='p147-lifetime-',dir=ROOT) as temporary:
            path=Path(temporary);other=cachemod.PackageCache(path);m,c=material();other.put(m,c)
            self.assertEqual(list(path.rglob('*.tmp')),[])
        self.assertFalse(path.exists())

    def test_diagnostics_root_independent_and_static_security(self):
        m,c=material();self.assertEqual(self.error(self.cache.get,m.content_identity()),'CACHE_MISS')
        tree=ast.parse((ROOT/'apexforge/tooling/package_cache.py').read_text(encoding='utf-8'))
        forbidden={'subprocess','socket','requests','urllib','runtime','authority','native_execution','importlib'}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                self.assertFalse(any(any(p in forbidden for p in n.split('.')) for n in names))
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                self.assertNotIn(name,{'solve','eval','exec','execute','run_air_program','Popen','system','install','private_bytes','glob','rglob'})


if __name__=='__main__':unittest.main()
