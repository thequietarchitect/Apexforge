"""P14.6 real byte integrity; no fake signing when crypto provider is unavailable."""
import ast
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tooling.package_trust as trust
import tooling.package_manifest as pm
import tooling.package_solver as solver
import tooling.package_lock as locks
import tooling.package_capabilities as caps
import p14_2_deterministic_dependency_solver_test as fixture
from authority.engine import AuthorityEngine

KEY=b'K'*32


def material():
    data=b'canonical supplied content'
    descriptor=pm.ContentDescriptor(pm.PackagePath('src/main.apex'),sha256(data).hexdigest().upper(),'source')
    return fixture.package('root',content=(descriptor,)),(trust.ContentMember(descriptor.path,data),)


def envelope(m):
    # Structural placeholder only: never generated or treated as a cryptographic signature.
    return trust.SignatureEnvelope(trust.key_fingerprint(KEY),trust.payload_fingerprint(m),b'\0'*64)


def policy(m):
    return trust.TrustPolicy((trust.TrustAnchor(KEY),),(trust.NamespaceTrustRule(trust.key_fingerprint(KEY),m.coordinate.namespace),))


class PackageTrustTests(unittest.TestCase):
    def error(self,fn,*args,code=None,**kwargs):
        with self.assertRaises(trust.PackageTrustError) as caught: fn(*args,**kwargs)
        if code: self.assertEqual(caught.exception.code,code)

    def test_canonical_payload_identity_schema_and_metadata(self):
        m,contents=material();p=json.loads(trust.signing_payload(m))
        self.assertEqual(p['schema'],trust.PAYLOAD_SCHEMA)
        self.assertEqual(p['coordinate'],m.coordinate.record())
        self.assertEqual(p['content_identity'],m.content_identity().record())
        self.assertEqual(trust.signing_payload(m),trust.signing_payload(replace(m,metadata=(('title','Unsigned'),))))
        self.assertNotIn(b'Unsigned',trust.signing_payload(m))

    def test_identity_coordinate_content_provenance_tampering(self):
        m,c=material();ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','A'*64)
        changes=(replace(m,coordinate=fixture.coordinate('other')),replace(m,required_capabilities=('Read',)),
            replace(m,provenance=(ref,)),replace(m,content=(replace(m.content[0],digest='F'*64),)))
        for changed in changes:
            self.assertNotEqual(trust.payload_fingerprint(m),trust.payload_fingerprint(changed))
            r=trust.verify_package(changed,c,envelope(m),KEY).record()
            self.assertEqual(r['signing_payload'],'SIGNING_PAYLOAD_MISMATCH')
            self.assertEqual(r['signature'],'NOT_VERIFIED')

    def test_real_content_integrity(self):
        m,c=material();r=trust.verify_integrity(m,c)
        self.assertTrue(r.valid)
        self.assertEqual(r.content_fingerprint,m.content_identity().fingerprint)
        with self.assertRaises(FrozenInstanceError):r.diagnostics=()

    def test_missing_extra_modified_members_layers(self):
        m,c=material()
        for members,code in (((),'CONTENT_MISSING'),(c+(trust.ContentMember(pm.PackagePath('extra'),b'x'),),'CONTENT_UNEXPECTED'),
            ((replace(c[0],data=b'tampered'),),'CONTENT_DIGEST_MISMATCH')):
            r=trust.verify_package(m,members,envelope(m),KEY,policy(m)).record()
            self.assertEqual(r['integrity']['diagnostics'][0]['code'],code)
            self.assertFalse(r['accepted'])

    def test_duplicate_and_host_paths_fail_closed(self):
        m,c=material();self.error(trust.verify_integrity,m,c+c,code='CONTENT_MEMBER_DUPLICATE')
        for path in ('C:/secret','../secret','/secret','a\\b'):
            with self.assertRaises(pm.PackageManifestError): pm.PackagePath(path)
        self.error(trust.ContentMember,pm.PackagePath('x'),'not bytes',code='CONTENT_MEMBER_INVALID')

    def test_key_fingerprint_domain_and_malformed_keys(self):
        self.assertEqual(trust.key_fingerprint(KEY),trust.key_fingerprint(bytes(KEY)))
        self.assertNotEqual(trust.key_fingerprint(KEY),sha256(KEY).hexdigest().upper())
        for key in (b'',b'x'*31,'KEY',bytearray(KEY)):
            self.error(trust.key_fingerprint,key,code='PUBLIC_KEY_MALFORMED')

    def test_envelope_schema_algorithm_encoding_no_fallback(self):
        m,c=material();e=envelope(m)
        self.assertEqual(e.record()['signature_hex'],'00'*64)
        for algorithm in ('rsa','ED25519','none'):
            self.error(replace,e,algorithm=algorithm,code='SIGNATURE_ALGORITHM_UNSUPPORTED')
        self.error(replace,e,schema='future',code='SIGNATURE_SCHEMA_UNSUPPORTED')
        self.error(replace,e,signature=b'short',code='SIGNATURE_MALFORMED')
        self.error(replace,e,signer_fingerprint='bad',code='SIGNATURE_MALFORMED')

    def test_provider_unavailable_never_signature_valid(self):
        m,c=material();e=envelope(m)
        for signature in (b'\0'*64,b'x'*64):
            r=trust.verify_package(m,c,replace(e,signature=signature),KEY,policy(m)).record()
            self.assertEqual(r['signature'],'CRYPTO_PROVIDER_UNAVAILABLE');self.assertFalse(r['accepted'])

    def test_wrong_key_and_signer_fingerprint(self):
        m,c=material();e=envelope(m)
        for key,env in ((b'Z'*32,e),(KEY,replace(e,signer_fingerprint='F'*64)),(None,e)):
            r=trust.verify_package(m,c,env,key).record()
            self.assertEqual(r['signature'],'SIGNER_KEY_FINGERPRINT_MISMATCH')

    def test_unsigned_explicit_acceptance_policy(self):
        m,c=material()
        self.assertEqual(trust.verify_package(m,c).record()['signature'],'UNSIGNED')
        self.assertIsNone(trust.verify_package(m,c).record()['accepted'])
        self.assertFalse(trust.verify_package(m,c,policy=trust.TrustPolicy()).record()['accepted'])
        permissive=trust.TrustPolicy(require_signature=False,require_scope_trust=False)
        self.assertTrue(trust.verify_package(m,c,policy=permissive).record()['accepted'])
        self.assertFalse(trust.verify_package(m,(),policy=permissive).record()['accepted'])

    def test_anchor_removal_scope_separation_no_ownership(self):
        m,c=material();e=envelope(m)
        good=trust.verify_package(m,c,e,KEY,policy(m)).record()
        self.assertEqual(good['signer_trust'],'SIGNER_TRUSTED')
        self.assertEqual(good['scope_trust'],'TRUSTED_FOR_PACKAGE_SCOPE')
        noanchor=trust.verify_package(m,c,e,KEY,trust.TrustPolicy()).record()
        self.assertEqual(noanchor['signer_trust'],'SIGNER_UNTRUSTED')
        wrong=trust.TrustPolicy((trust.TrustAnchor(KEY),),(trust.NamespaceTrustRule(trust.key_fingerprint(KEY),'other.namespace'),))
        self.assertEqual(trust.verify_package(m,c,e,KEY,wrong).record()['scope_trust'],'TRUST_SCOPE_MISMATCH')
        self.assertNotIn('owner',good);self.assertNotIn('person',good)

    def test_policy_order_duplicates_fingerprint(self):
        anchors=(trust.TrustAnchor(KEY),trust.TrustAnchor(b'Z'*32))
        rules=tuple(trust.NamespaceTrustRule(a.fingerprint,'example.namespace') for a in anchors)
        expected=trust.TrustPolicy(anchors,rules)
        for a in permutations(anchors):
            for r in permutations(rules):
                self.assertEqual(trust.TrustPolicy(a,r).fingerprint(),expected.fingerprint())
        self.assertEqual(trust.TrustPolicy(anchors+anchors,rules+rules),expected)
        self.error(trust.TrustPolicy,require_signature=False,require_scope_trust=True,code='TRUST_POLICY_CONFLICT')
        self.error(trust.TrustPolicy,(),rules,code='TRUST_RULE_ANCHOR_MISSING')

    def test_lock_exact_match_and_changed_content(self):
        m,c=material();lock=locks.PackageLock(solver.solve(m,fixture.universe()));before=lock.canonical_json()
        r=trust.verify_package(m,c,lock=lock).record();self.assertEqual(r['lock'],'MATCH')
        changed=replace(m,required_capabilities=('Read',))
        r=trust.verify_package(changed,c,envelope(changed),KEY,policy(changed),lock).record()
        self.assertEqual(r['lock'],'LOCK_CONTENT_MISMATCH');self.assertFalse(r['accepted'])
        self.assertEqual(lock.canonical_json(),before)

    def test_signed_reference_not_provenance_truth(self):
        m,c=material();ref=pm.CanonicalReference('apexforge.provenance/v1','provenance-scope','F'*64)
        m=replace(m,provenance=(ref,));r=trust.verify_package(m,c,envelope(m),KEY).record()
        self.assertEqual(r['provenance'],[ref.record()])
        self.assertEqual(r['provenance_status'],'REFERENCE_COMMITTED_CLAIM_UNVERIFIED')
        self.assertNotIn('verified_claim',r)

    def test_authority_not_invoked(self):
        m,c=material()
        with patch.object(AuthorityEngine,'check',side_effect=AssertionError('authority')),patch.object(AuthorityEngine,'allows',side_effect=AssertionError('authority')):
            r=trust.verify_package(m,c,envelope(m),KEY,policy(m)).record()
        self.assertFalse(r['grants_runtime_authority'])

    def test_capability_independence(self):
        m,c=material();g=solver.solve(m,fixture.universe())
        self.assertTrue(caps.validate_capabilities(g).compatible)
        self.assertEqual(trust.verify_package(m,c,envelope(m),KEY,trust.TrustPolicy()).record()['signer_trust'],'SIGNER_UNTRUSTED')
        m=replace(m,required_capabilities=('Missing',));g=solver.solve(m,fixture.universe())
        self.assertFalse(caps.validate_capabilities(g).compatible)
        self.assertEqual(trust.verify_package(m,c,envelope(m),KEY,policy(m)).record()['scope_trust'],'TRUSTED_FOR_PACKAGE_SCOPE')

    def test_models_inputs_unchanged_diagnostics_deterministic(self):
        m,c=material();p=policy(m);e=envelope(m);before=m.canonical_json()
        a,b=trust.verify_package(m,c,e,KEY,p),trust.verify_package(m,c,e,KEY,p)
        self.assertEqual(a,b);self.assertEqual(m.canonical_json(),before)
        self.assertEqual(c[0].data,b'canonical supplied content')
        for obj,field in ((p,'rules'),(e,'signature'),(a,'canonical_json')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,None)
        detached=a.record();detached['accepted']=True;self.assertFalse(a.record()['accepted'])

    def test_large_content_set_order(self):
        members=tuple(trust.ContentMember(pm.PackagePath('data/f'+str(i)),str(i).encode()) for i in range(1100))
        descriptors=tuple(pm.ContentDescriptor(x.path,sha256(x.data).hexdigest().upper(),'data') for x in members)
        m=fixture.package('root',content=descriptors)
        self.assertTrue(trust.verify_integrity(m,members).valid)
        self.assertEqual(trust.verify_package(m,members),trust.verify_package(m,tuple(reversed(members))))
        self.assertEqual(trust.signing_payload(m),trust.signing_payload(replace(m,content=tuple(reversed(descriptors)))))

    def test_static_security_no_private_persistence_or_execution(self):
        tree=ast.parse((ROOT/'apexforge/tooling/package_trust.py').read_text(encoding='utf-8'))
        forbidden={'subprocess','socket','requests','urllib','os','runtime','authority','native_execution','importlib'}
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
                self.assertFalse(any(any(p in forbidden for p in n.split('.')) for n in names))
            if isinstance(node,ast.Call):
                name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else ''
                self.assertNotIn(name,{'solve','open','write','private_bytes','eval','exec','execute','Popen','system','install'})


if __name__=='__main__':unittest.main()
