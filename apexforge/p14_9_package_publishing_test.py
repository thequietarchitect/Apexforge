"""P14.9 immutable publication and external authentication boundary."""
import ast
from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tooling.package_publishing as pub
import tooling.package_registry as registry
import tooling.package_trust as trust
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_cache as cache
import p14_8_registry_protocol_test as fixtures
import p14_6_package_signing_integrity_provenance_trust_test as trust_fixture

P = pub.PublisherPrincipal('publisher-a')


def material(**fields):
    r, b = fixtures.material(**fields)
    return pub.PublicationRequest(P, r.manifest, (trust.ContentMember(r.manifest.content[0].path, b.data),), r.identity)


def policy(request):
    return pub.PublicationPolicy((pub.PublicationGrant(P, request.manifest.coordinate.namespace),))


class PublicationTests(unittest.TestCase):
    def error(self, request, code, catalog=None, grants=None):
        catalog = registry.RegistryCatalog(()) if catalog is None else catalog
        before = pub.registry_state_fingerprint(catalog)
        with self.assertRaises(pub.PublicationError) as caught:
            pub.publish(catalog, request, policy(request) if grants is None else grants)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), code)
        self.assertEqual(pub.registry_state_fingerprint(catalog), before)

    def test_schema_and_malformed_inputs(self):
        q = material()
        for fields, code in (({'schema':'future'}, 'PUBLICATION_SCHEMA_UNSUPPORTED'),
            ({'publisher':'caller'}, 'PUBLICATION_PRINCIPAL_INVALID'),
            ({'members':list(q.members)}, 'PUBLICATION_REQUEST_INVALID'),
            ({'manifest':{}}, 'PUBLICATION_REQUEST_INVALID'), ({'signature':{}}, 'PUBLICATION_REQUEST_INVALID')):
            with self.assertRaises(pub.PublicationError) as caught: replace(q, **fields)
            self.assertEqual(caught.exception.code, code)

    def test_principal_is_opaque_separate_domain(self):
        for value in ('', 'User@host', '../user', 'Org.Name', 'PUBLISHER', 1):
            with self.assertRaises(pub.PublicationError): pub.PublisherPrincipal(value)
        self.assertNotEqual(P, P.identifier)
        self.assertNotEqual(P.identifier, material().manifest.coordinate.namespace)

    def test_policy_order_duplicate_and_invalid(self):
        a = pub.PublicationGrant(P, 'apexforge.example')
        b = pub.PublicationGrant(pub.PublisherPrincipal('other'), 'other.space')
        self.assertEqual(pub.PublicationPolicy((a,b,a)), pub.PublicationPolicy((b,a)))
        self.assertEqual(pub.PublicationPolicy((a,b)).fingerprint(), pub.PublicationPolicy((b,a)).fingerprint())
        for namespace in ('bad/path', '*', 'Bad'):
            with self.assertRaises(pub.PublicationError): pub.PublicationGrant(P, namespace)

    def test_exact_scope_no_parent_child_inheritance(self):
        q = material()
        for namespace in ('apexforge', 'apexforge.example.child', 'unrelated'):
            self.error(q, 'PUBLICATION_NAMESPACE_NOT_AUTHORIZED',
                       grants=pub.PublicationPolicy((pub.PublicationGrant(P, namespace),)))

    def test_wrong_publisher_and_unauthorized_retry(self):
        q = material(); old = pub.publish(registry.RegistryCatalog(()),q,policy(q)).catalog
        self.error(replace(q,publisher=pub.PublisherPrincipal('other')), 'PUBLICATION_NAMESPACE_NOT_AUTHORIZED',
                   catalog=old,grants=policy(q))

    def test_integrity_missing_modified_extra(self):
        q = material()
        for members in ((), q.members + q.members, (replace(q.members[0],data=b'tampered'),),
            q.members + (trust.ContentMember(pm.PackagePath('extra.dat'),b'extra'),)):
            self.error(replace(q,members=members), 'PUBLICATION_CONTENT_INTEGRITY_FAILED')

    def test_expected_content_binding(self):
        self.error(replace(material(),expected_content=pm.PackageContentIdentity('F'*64)),
                   'PUBLICATION_CONTENT_IDENTITY_MISMATCH')

    def test_new_publication_is_functional(self):
        q=material(); old=registry.RegistryCatalog(())
        result=pub.publish(old,q,policy(q))
        self.assertIsNot(old,result.catalog);self.assertEqual(old.records,())
        self.assertEqual(result.receipt.record()['status'],'PUBLISHED_NEW')
        self.assertEqual(result.catalog.records[0].identity,q.expected_content)

    def test_retry_idempotent_without_duplicate_blobs_or_records(self):
        q=material(); first=pub.publish(registry.RegistryCatalog(()),q,policy(q))
        retry=pub.publish(first.catalog,q,policy(q))
        self.assertIs(retry.catalog,first.catalog)
        self.assertEqual(retry.receipt.record()['status'],'ALREADY_PRESENT')
        self.assertEqual(len(retry.catalog.records),1);self.assertEqual(len(retry.catalog.blobs),1)

    def test_coordinate_conflict_and_new_version(self):
        q=material(); old=pub.publish(registry.RegistryCatalog(()),q,policy(q)).catalog
        self.error(material(data=b'changed'),'PUBLICATION_COORDINATE_CONTENT_CONFLICT',catalog=old)
        other=material(data=b'changed',version='2.0.0')
        self.assertEqual(len(pub.publish(old,other,policy(other)).catalog.records),2)

    def test_external_divergence_rejected_order_independent(self):
        a,ba=fixtures.material(); b,bb=fixtures.material(data=b'variant');q=material()
        for records in ((a,b),(b,a)):
            self.error(q,'PUBLICATION_COORDINATE_CONTENT_CONFLICT',registry.RegistryCatalog(records,(ba,bb)))

    def test_blob_dedup_distinct_packages(self):
        q=material();old=pub.publish(registry.RegistryCatalog(()),q,policy(q)).catalog
        other=material(name='other')
        result=pub.publish(old,other,policy(other))
        self.assertEqual(len(result.catalog.blobs),1);self.assertEqual(len(result.catalog.records),2)

    def test_corrupt_existing_blob_never_overwritten(self):
        q=material();r,b=fixtures.material()
        # Controlled corruption bypasses a frozen validated constructor only in this adversarial fixture.
        forged=object.__new__(registry.RegistryBlob)
        object.__setattr__(forged,'digest',b.digest);object.__setattr__(forged,'data',b'corrupt')
        self.error(q,'PUBLICATION_BLOB_CONFLICT',registry.RegistryCatalog((),(forged,)))

    def test_incomplete_existing_entry_not_repaired_by_retry(self):
        r,b=fixtures.material()
        self.error(material(),'PUBLICATION_BLOB_CONFLICT',registry.RegistryCatalog((r,)))

    def test_receipt_exact_evidence_and_no_attribution(self):
        q=material();old=registry.RegistryCatalog(());p=policy(q)
        result=pub.publish(old,q,p);record=result.receipt.record()
        self.assertEqual(record['content_identity'],q.expected_content.record())
        self.assertEqual(record['publisher'],P.identifier);self.assertEqual(record['policy_fingerprint'],p.fingerprint())
        self.assertEqual(record['previous_state'],pub.registry_state_fingerprint(old))
        self.assertEqual(record['resulting_state'],pub.registry_state_fingerprint(result.catalog))
        self.assertEqual(record['authentication'],'EXTERNAL_PRECONDITION')
        self.assertFalse(record['package_trust_granted']);self.assertFalse(record['runtime_authority_granted'])
        self.assertNotIn('author',record);self.assertNotIn('owner',record)

    def test_deterministic_request_transition_and_receipt(self):
        q=material();p=policy(q)
        a=pub.publish(registry.RegistryCatalog(()),q,p)
        b=pub.publish(registry.RegistryCatalog(()),material(),policy(material()))
        self.assertEqual(q.canonical_json(),material().canonical_json())
        self.assertEqual(a.receipt,b.receipt);self.assertEqual(a.receipt.fingerprint(),b.receipt.fingerprint())

    def test_provenance_preserved_not_origin_proof(self):
        ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','A'*64)
        q=material(provenance=(ref,));result=pub.publish(registry.RegistryCatalog(()),q,policy(q))
        self.assertEqual(result.catalog.records[0].manifest.provenance,(ref,))
        self.assertEqual(result.receipt.record()['provenance'],[ref.record()])

    def test_passive_signature_and_retry_preserve_unverified_evidence(self):
        q=material();q=replace(q,signature=trust_fixture.envelope(q.manifest))
        first=pub.publish(registry.RegistryCatalog(()),q,policy(q))
        retry=pub.publish(first.catalog,replace(q,signature=None),policy(q))
        self.assertEqual(first.catalog.records[0].signature,q.signature)
        self.assertEqual(retry.receipt.record()['signature_status'],'NOT_VERIFIED')
        evidence=trust.verify_package(q.manifest,q.members,q.signature,trust_fixture.KEY)
        self.assertIn('CRYPTO_PROVIDER_UNAVAILABLE',json.dumps(evidence.record()))

    def test_read_protocol_interoperability(self):
        q=material();catalog=pub.publish(registry.RegistryCatalog(()),q,policy(q)).catalog
        for op,selector in (('coordinate',q.manifest.coordinate.record()),('content',q.expected_content.record()),
            ('versions',{'namespace':q.manifest.coordinate.namespace,'name':q.manifest.coordinate.name}),
            ('blob',{'digest':q.manifest.content[0].digest})):
            response=catalog.query(fixtures.request(op,selector));self.assertEqual(response.code,'OK')
        self.assertEqual(catalog.snapshot().records[0].identity,q.expected_content)
        with self.assertRaises(registry.RegistryError): fixtures.request('publish',{})

    def test_no_solver_cache_or_authority_invocation(self):
        from authority.engine import AuthorityEngine
        q=material()
        with (patch.object(solver,'solve',side_effect=AssertionError('solver')),
             patch.object(cache.PackageCache,'put',side_effect=AssertionError('cache')),
             patch.object(AuthorityEngine,'check',side_effect=AssertionError('authority'))):
            pub.publish(registry.RegistryCatalog(()),q,policy(q))

    def test_immutable_models_and_detached_receipt_record(self):
        q=material();p=policy(q);result=pub.publish(registry.RegistryCatalog(()),q,p)
        for obj,field in ((P,'identifier'),(q,'schema'),(p,'grants'),(result,'catalog'),(result.receipt,'canonical_json')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,None)
        record=result.receipt.record();record['publisher']='changed'
        self.assertEqual(result.receipt.record()['publisher'],P.identifier)

    def test_metadata_unsigned_identity_retry(self):
        q=material();old=pub.publish(registry.RegistryCatalog(()),q,policy(q)).catalog
        changed=replace(q,manifest=replace(q.manifest,metadata=(('title','Presentation'),)))
        self.assertEqual(q.canonical_json(),changed.canonical_json())
        self.assertIs(pub.publish(old,changed,policy(changed)).catalog,old)

    def test_large_catalog_determinism(self):
        records=tuple(fixtures.material(name='pkg'+str(i))[0] for i in range(1000))
        q=material();_,blob=fixtures.material()
        a=pub.publish(registry.RegistryCatalog(records,(blob,)),q,policy(q))
        b=pub.publish(registry.RegistryCatalog(tuple(reversed(records)),(blob,)),q,policy(q))
        self.assertEqual(a.receipt,b.receipt);self.assertEqual(len(a.catalog.records),1001)

    def test_static_security_and_read_only_predecessor(self):
        source=Path(pub.__file__).read_text(encoding='utf-8');tree=ast.parse(source)
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports|={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertFalse(imports & {'subprocess','socket','requests','os','pathlib','authority.engine'})
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertFalse(calls & {'open','eval','exec','__import__','solve'})
        self.assertEqual(registry.OPERATIONS,frozenset(('coordinate','content','versions','blob','catalog')))


if __name__=='__main__':unittest.main()
