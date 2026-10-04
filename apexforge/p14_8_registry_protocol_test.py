"""P14.8 read-only deterministic discovery; no solving, cache mutation or trust."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from itertools import permutations
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_registry as registry
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_cache as cachemod
import tooling.package_trust as trust
import p14_2_deterministic_dependency_solver_test as fixture


def request(op,selector):return registry.RegistryRequest(op,json.dumps(selector))
def content(record):return request('content',record.identity.record())


def material(name='root',version='1.0.0',data=b'registry member',**fields):
    digest=sha256(data).hexdigest().upper()
    descriptor=pm.ContentDescriptor(pm.PackagePath('src/main.apex'),digest,'source')
    manifest=fixture.package(name,version=version,content=(descriptor,),**fields)
    return registry.RegistryRecord(manifest),registry.RegistryBlob(digest,data)


class RegistryTests(unittest.TestCase):
    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(registry.RegistryError) as caught:fn(*args,**kwargs)
        if code:self.assertEqual(caught.exception.code,code)
        return str(caught.exception)

    def test_protocol_request_roundtrip_schema_and_selectors(self):
        r,b=material()
        for op,selector in (('coordinate',r.manifest.coordinate.record()),('content',r.identity.record()),
            ('versions',{'namespace':r.manifest.coordinate.namespace,'name':'root'}),('blob',{'digest':b.digest}),('catalog',{})):
            q=request(op,selector)
            self.assertEqual(registry.RegistryRequest.parse(q.canonical_json()),q)
            self.assertEqual(q.record()['schema'],registry.SCHEMA)
            self.assertNotEqual(q.record()['schema'],r.manifest.coordinate.schema)

    def test_schema_unknown_operation_and_read_only(self):
        self.error(registry.RegistryRequest,'catalog','{}','future',code='UNSUPPORTED_PROTOCOL_VERSION')
        for op in ('latest','publish','delete','put_package','transfer_namespace','yank','install'):
            self.error(request,op,{},code='UNKNOWN_OPERATION')

    def test_strict_request_json_duplicate_and_unknown_fields(self):
        for text in ('{','{"schema":"a","schema":"b"}','NaN','['*1500):
            self.error(registry.RegistryRequest.parse,text,code='INVALID_REQUEST')
        self.error(request,'catalog',{'path':'C:/host'},code='INVALID_REQUEST')
        self.error(request,'versions',{'namespace':'bad/namespace','name':'root'},code='INVALID_REQUEST')
        self.error(request,'blob',{'digest':'../host'},code='INVALID_REQUEST')
        r,b=material();self.error(request,'coordinate',{**r.manifest.coordinate.record(),'latest':True},code='INVALID_REQUEST')

    def test_coordinate_content_hits_and_misses(self):
        r,b=material();catalog=registry.RegistryCatalog((r,),(b,))
        hit=catalog.query(request('coordinate',r.manifest.coordinate.record()))
        self.assertEqual(hit.code,'OK');self.assertEqual(hit.records,(r,))
        self.assertEqual(catalog.query(content(r)).records,(r,))
        self.assertEqual(catalog.query(request('coordinate',fixture.coordinate('missing').record())).code,'PACKAGE_NOT_FOUND')
        self.assertEqual(catalog.query(request('content',pm.PackageContentIdentity('F'*64).record())).code,'CONTENT_NOT_FOUND')

    def test_ambiguity_retains_content_variants_order_independent(self):
        a,ba=material();b,bb=material(data=b'variant')
        self.assertEqual(a.manifest.coordinate,b.manifest.coordinate);self.assertNotEqual(a.identity,b.identity)
        outputs=[]
        for order in permutations((a,b)):
            c=registry.RegistryCatalog(order,(ba,bb));r=c.query(request('coordinate',a.manifest.coordinate.record()))
            self.assertEqual(r.code,'AMBIGUOUS_COORDINATE');self.assertEqual(len(r.records),2)
            outputs.append(r.canonical_json())
            self.assertEqual(c.query(content(a)).records,(a,));self.assertEqual(c.query(content(b)).records,(b,))
        self.assertEqual(outputs[0],outputs[1])

    def test_versions_numeric_informational_no_selection(self):
        records=tuple(material(version=v)[0] for v in ('10.0.0','2.0.0','1.0.0'))
        c=registry.RegistryCatalog(records)
        r=c.query(request('versions',{'namespace':records[0].manifest.coordinate.namespace,'name':'root'}))
        self.assertEqual([v.text() for v in r.versions],['1.0.0','2.0.0','10.0.0'])
        self.assertNotIn('selected',r.record());self.assertNotIn('latest',r.record())

    def test_manifest_descriptors_exports_capabilities_provenance_preserved(self):
        ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','F'*64)
        sym=pm.SymbolReference('B'*64,'function','function:Run','language.module')
        r,b=material(exports=(sym,),provenance=(ref,),required_capabilities=('Read',))
        response=registry.RegistryCatalog((r,)).query(content(r))
        parsed=registry.RegistryResponse.parse(response.canonical_json()).records[0]
        self.assertEqual(parsed.manifest.canonical_json(),r.manifest.canonical_json())
        self.assertEqual(parsed.identity,r.identity);self.assertEqual(parsed.manifest.content,r.manifest.content)
        self.assertEqual(parsed.manifest.exports,(sym,));self.assertEqual(parsed.manifest.provenance,(ref,))
        self.assertEqual(parsed.manifest.required_capabilities,('Read',))

    def test_record_identity_tampering_rejected(self):
        r,b=material()
        for mutate in (lambda v:v['content_identity'].update(fingerprint='F'*64),lambda v:v['coordinate'].update(name='other')):
            v=r.record();mutate(v)
            self.error(registry.RegistryRecord.from_mapping,v,code='CONTENT_IDENTITY_MISMATCH')
        v=r.record();v['trusted']=True
        self.error(registry.RegistryRecord.from_mapping,v,code='REGISTRY_RECORD_INVALID')

    def test_passive_signature_no_crypto_verdict(self):
        r,b=material();key=b'K'*32
        envelope=trust.SignatureEnvelope(trust.key_fingerprint(key),trust.payload_fingerprint(r.manifest),b'\0'*64)
        r=replace(r,signature=envelope)
        response=registry.RegistryCatalog((r,)).query(content(r))
        parsed=registry.RegistryResponse.parse(response.canonical_json()).records[0]
        self.assertEqual(parsed.signature,envelope);self.assertEqual(parsed.record()['signature_status'],'NOT_VERIFIED')
        members=(trust.ContentMember(r.manifest.content[0].path,b.data),)
        self.assertEqual(trust.verify_package(r.manifest,members,envelope,key).record()['signature'],'CRYPTO_PROVIDER_UNAVAILABLE')
        self.assertFalse(any(importlib.util.find_spec(n) for n in ('cryptography','nacl','sigstore')))

    def test_catalog_duplicate_and_conflicting_passive_record(self):
        r,b=material();c=registry.RegistryCatalog((r,r),(b,b))
        self.assertEqual(c.records,(r,));self.assertEqual(c.blobs,(b,))
        e=trust.SignatureEnvelope('A'*64,trust.payload_fingerprint(r.manifest),b'\0'*64)
        self.error(registry.RegistryCatalog,(r,replace(r,signature=e)),code='REGISTRY_RECORD_INVALID')

    def test_blob_retrieval_roundtrip_and_corruption(self):
        r,b=material();c=registry.RegistryCatalog((r,),(b,))
        response=c.query(request('blob',{'digest':b.digest}))
        self.assertEqual(registry.RegistryResponse.parse(response.canonical_json()).blob,b)
        self.assertEqual(c.query(request('blob',{'digest':'F'*64})).code,'BLOB_NOT_FOUND')
        self.error(registry.RegistryBlob,b.digest,b'tamper',code='BLOB_DIGEST_MISMATCH')
        v=response.record();v['blob']['data_hex']=b'changed'.hex()
        self.error(registry.RegistryResponse.parse,json.dumps(v),code='BLOB_DIGEST_MISMATCH')

    def test_response_validation_schema_payload_and_duplicate_keys(self):
        r,b=material();response=registry.RegistryCatalog((r,)).query(content(r));v=response.record()
        v['schema']='future';self.error(registry.RegistryResponse.parse,json.dumps(v),code='RESPONSE_SCHEMA_INVALID')
        self.error(registry.RegistryResponse,'content',code='RESPONSE_SCHEMA_INVALID')
        self.error(registry.RegistryResponse,'content','CONTENT_NOT_FOUND',(r,),code='RESPONSE_SCHEMA_INVALID')
        self.error(registry.RegistryResponse.parse,'{"schema":"a","schema":"b"}',code='RESPONSE_SCHEMA_INVALID')
        v=response.record();v['status']='ERROR'
        self.error(registry.RegistryResponse.parse,json.dumps(v),code='RESPONSE_SCHEMA_INVALID')

    def test_response_bound_to_exact_request_selector(self):
        a,ba=material('a');b,bb=material('b',data=b'other')
        c=registry.RegistryCatalog((a,b),(ba,bb));q=content(a)
        self.assertEqual(registry.validate_response(q,c.query(q)),c.query(q))
        self.error(registry.validate_response,q,c.query(content(b)),code='CONTENT_IDENTITY_MISMATCH')
        self.error(registry.validate_response,request('coordinate',a.manifest.coordinate.record()),
            c.query(request('coordinate',b.manifest.coordinate.record())),code='CONTENT_IDENTITY_MISMATCH')
        self.error(registry.validate_response,request('blob',{'digest':ba.digest}),
            c.query(request('blob',{'digest':bb.digest})),code='BLOB_DIGEST_MISMATCH')
        self.error(registry.validate_response,q,c.query(request('catalog',{})),code='RESPONSE_SCHEMA_INVALID')

    def test_snapshot_determinism_independent_construction(self):
        records=(material('a')[0],material('b')[0])
        a=registry.RegistryCatalog(records).snapshot();b=registry.RegistryCatalog(tuple(reversed(records))).snapshot()
        self.assertEqual(a,b);self.assertEqual(a.canonical_json(),b.canonical_json());self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertEqual(tuple(m.content_identity() for m in a.to_universe().candidates),tuple(r.identity for r in a.records))

    def test_snapshot_conflict_not_solver_selection(self):
        a,_=material();b,_=material(data=b'different')
        snapshot=registry.RegistryCatalog((a,b)).snapshot()
        self.assertEqual(len(snapshot.records),2)
        with self.assertRaises(solver.PackageSolverError):snapshot.to_universe()
        with patch.object(solver,'solve',side_effect=AssertionError('solver called')):
            self.assertEqual(registry.RegistryCatalog((a,)).snapshot().to_universe().candidates,(a.manifest,))

    def test_lock_exact_binding_missing_no_substitution(self):
        r,b=material();alt,_=material(data=b'other')
        g=solver.solve(r.manifest,fixture.universe());lock=locks.PackageLock(g);before=lock.canonical_json()
        self.assertEqual(registry.RegistryCatalog((r,alt)).locked_records(lock).records,(r,))
        self.error(registry.RegistryCatalog((alt,)).locked_records,lock,code='CONTENT_NOT_FOUND')
        self.assertEqual(lock.canonical_json(),before);self.assertEqual(g,lock.resolution)

    def test_cache_not_mutated_by_fetch_caller_insertion_explicit(self):
        r,b=material();c=registry.RegistryCatalog((r,),(b,))
        with tempfile.TemporaryDirectory(prefix='p148-',dir=ROOT) as temporary:
            root=Path(temporary);cache=cachemod.PackageCache(root)
            with patch.object(cachemod.PackageCache,'put',side_effect=AssertionError('automatic insertion')):
                record=c.query(content(r)).records[0];blob=c.query(request('blob',{'digest':b.digest})).blob
                self.assertEqual(list(root.iterdir()),[])
            supplied=(trust.ContentMember(record.manifest.content[0].path,blob.data),)
            self.assertTrue(trust.verify_integrity(record.manifest,supplied).valid)
            self.assertEqual(cache.put(record.manifest,supplied).identity,r.identity)
        self.assertFalse(root.exists())

    def test_metadata_nonidentity_and_no_trust_owner_attribution(self):
        r,b=material();other=registry.RegistryRecord(replace(r.manifest,metadata=(('title','unsigned'),)))
        self.assertEqual(other,r)
        text=registry.RegistryCatalog((r,)).query(content(r)).canonical_json()
        for key in ('trusted','verified_owner','official','organization','publisher'):
            self.assertNotIn('"'+key+'"',text)

    def test_immutable_catalog_snapshot_response_and_manifests(self):
        r,b=material();c=registry.RegistryCatalog((r,),(b,));before=c.snapshot().canonical_json()
        response=c.query(content(r));snapshot=c.snapshot()
        for obj,field in ((c,'records'),(snapshot,'records'),(response,'records'),(r,'manifest')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,())
        with self.assertRaises(TypeError):c._content[r.identity]=r
        self.assertEqual(before,c.snapshot().canonical_json())

    def test_diagnostics_deterministic_without_payload_echo(self):
        messages=[self.error(request,'catalog',{'secret':'HOST_SECRET'}) for _ in range(2)]
        self.assertEqual(messages[0],messages[1]);self.assertNotIn('HOST_SECRET',messages[0])

    def test_thousand_catalog_exact_lookup_and_order(self):
        records=tuple(material('pkg'+str(i))[0] for i in range(1000))
        a,b=registry.RegistryCatalog(records),registry.RegistryCatalog(tuple(reversed(records)))
        self.assertEqual(a.snapshot().fingerprint(),b.snapshot().fingerprint())
        for i in (0,500,999):self.assertEqual(a.query(content(records[i])),b.query(content(records[i])))
        response=a.query(request('catalog',{}));self.assertEqual(len(response.records),1000)
        self.assertEqual(registry.RegistryResponse.parse(response.canonical_json()),response)

    def test_static_security_no_network_execution_publication(self):
        tree=ast.parse((ROOT/'apexforge/tooling/package_registry.py').read_text(encoding='utf-8'))
        forbidden={'subprocess','socket','requests','urllib','os','runtime','authority','native_execution','importlib'}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                self.assertFalse(any(any(p in forbidden for p in n.split('.')) for n in names))
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                self.assertNotIn(name,{'solve','put','open','write','eval','exec','execute','run_air_program','Popen','system','install','private_bytes','publish','delete'})


if __name__=='__main__':unittest.main()
