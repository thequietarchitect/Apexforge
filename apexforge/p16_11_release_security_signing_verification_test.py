"""P16.11 structural-only fixtures; no real signatures, keys or crypto operations."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from hashlib import sha256
import ast
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'apexforge'));sys.path.insert(0,str(ROOT))
from tooling import release_security as s, release_pipeline as p, release_manifest as m
from tooling.package_manifest import CanonicalReference
from p16_9_install_upgrade_rollback_test import manifest
from p16_10_ci_release_pipeline_dry_run_test import snapshot


DOMAIN=CanonicalReference('apexforge.release-trust-domain/v1','provenance-scope','A'*64)
FIXTURE_SOURCE=CanonicalReference('apexforge.release-signature-fixture/v1','source','B'*64)


def subjects():
    man=manifest()
    return s.SigningSubject(man),s.SigningSubject(man.artifacts.artifacts[0])


def signer(provider='frozen-provider-unavailable'):
    # Symbolic fingerprint declaration, not generated/acquired/validated key material.
    return s.SignerIdentity('explicit-fixture-reference','C'*64,DOMAIN,provider)


def policy(subjects_=None,signer_=None):
    values=subjects() if subjects_ is None else subjects_
    key=signer() if signer_ is None else signer_
    return s.ReleaseTrustPolicy('release-review','1',values[0].release,DOMAIN,values,(key,))


def envelope(subject,signer_=None,signature=b'x'*64,origin='TEST_FIXTURE'):
    key=signer() if signer_ is None else signer_
    return s.ReleaseSignatureEnvelope(subject,key,signature,FIXTURE_SOURCE,provider=s.SigningProviderCapability(key.provider),origin=origin)


def request(subject=None,policy_=None,signer_=None,envelope_=True):
    subject=subjects()[1] if subject is None else subject
    key=signer() if signer_ is None else signer_
    pol=policy((subject,),key) if policy_ is None else policy_
    env=envelope(subject,key) if envelope_ is True else envelope_
    return s.SignatureVerificationRequest(subject,pol,key,env)


class ContractTests(unittest.TestCase):
    def error(self,code,callback):
        with self.assertRaises(s.ReleaseSecurityError) as failure:callback()
        self.assertEqual(failure.exception.code,code)

    def test_subject_signer_policy_envelope_request_result_immutable(self):
        req=request();result=s.verify(req)
        for obj,field in ((req.subject,'owner'),(req.expected_signer,'key_id'),(req.policy,'revision'),
                          (req.envelope,'signature'),(req,'mode'),(result,'request')):
            with self.assertRaises(FrozenInstanceError):setattr(obj,field,'changed')

    def test_artifact_and_manifest_exact_bytes(self):
        man,artifact=subjects()
        self.assertEqual(man.record()['sha256'],sha256(man.owner.canonical_json().encode()).hexdigest().upper())
        self.assertEqual(artifact.record()['sha256'],artifact.owner.declared_digest)
        self.assertEqual(artifact.record()['length'],len(artifact.owner.data))
        self.assertEqual(man.record()['subject']['fingerprint'],man.owner.fingerprint())

    def test_payload_is_context_not_digest_or_filename(self):
        subject=subjects()[1];payload=subject.signing_bytes()
        self.assertIn(b'release',payload);self.assertIn(b'descriptor',payload);self.assertIn(b'length',payload)
        self.assertNotEqual(payload,subject.owner.declared_digest.encode())
        self.assertNotEqual(payload,subject.owner._slot.descriptor.filename.encode())
        self.error('RELEASE_SIGNING_SUBJECT_INVALID',lambda:s.SigningSubject('a.vsix'))
        self.error('RELEASE_SIGNING_SUBJECT_INVALID',lambda:s.SigningSubject(subject.owner.declared_digest))

    def test_changed_content_same_filename_reidentifies(self):
        a=subjects()[1];b=s.SigningSubject(manifest(files=(('a',b'changed'),)).artifacts.artifacts[0])
        self.assertEqual(a.owner._slot.descriptor.filename,b.owner._slot.descriptor.filename)
        self.assertNotEqual(a.fingerprint(),b.fingerprint());self.assertNotEqual(a.payload_fingerprint(),b.payload_fingerprint())

    def test_manifest_content_and_provenance_reidentify(self):
        a=subjects()[0];man=manifest(files=(('a',b'changed'),));b=s.SigningSubject(man)
        self.assertNotEqual(a.fingerprint(),b.fingerprint())
        record=man.provenance.records[0]
        changed=replace(man,provenance=replace(man.provenance,records=(replace(record,identifier='different-evidence'),)+man.provenance.records[1:]))
        self.assertEqual(changed.status,'COMPLETE')
        self.assertNotEqual(b.payload_fingerprint(),s.SigningSubject(changed).payload_fingerprint())

    def test_incomplete_manifest_rejected(self):
        self.error('RELEASE_SIGNING_MANIFEST_INCOMPLETE',lambda:s.SigningSubject(replace(manifest(),checksums=None)))

    def test_explicit_algorithm_no_length_inference(self):
        env=request().envelope
        self.assertEqual(env.record()['algorithm'],'ed25519')
        for value in ('rsa','ED25519','',None):
            self.error('RELEASE_SIGNATURE_ALGORITHM_UNSUPPORTED',lambda:replace(env,algorithm=value))
        self.error('RELEASE_SIGNATURE_ALGORITHM_UNSUPPORTED',lambda:replace(request(),algorithm='rsa'))

    def test_key_and_certificate_fingerprints_bounded(self):
        key=signer()
        for value in ('a'*64,'0'*64,'C'*63,'G'*64,b'C'*64,None):
            self.error('RELEASE_SIGNING_FINGERPRINT_INVALID',lambda:replace(key,public_key_fingerprint=value))
        self.error('RELEASE_SIGNING_FINGERPRINT_INVALID',lambda:replace(key,certificate_fingerprint='bad'))
        with self.assertRaises(TypeError):s.SignerIdentity(key.key_id,key.public_key_fingerprint,DOMAIN,private_key=b'not-allowed')

    def test_key_certificate_presence_do_not_authenticate(self):
        key=replace(signer(),certificate_fingerprint='D'*64)
        record=key.record()
        self.assertFalse(record['key_owner_authenticated'])
        self.assertEqual(record['certificate_parse'],'NOT_EVALUATED');self.assertEqual(record['certificate_chain'],'NOT_EVALUATED')
        self.assertFalse(s.verify(request(signer_=key)).record()['accepted'])

    def test_empty_zero_and_oversized_signature_rejected(self):
        env=request().envelope
        for data in (b'',b'\0'*64,b'x'*63,b'x'*65,b'x'*1024,'x'*64):
            self.error('RELEASE_SIGNATURE_MALFORMED',lambda:replace(env,signature=data))

    def test_unsigned_explicit_never_valid(self):
        result=s.verify(request(envelope_=None)).record()
        self.assertEqual(result['signature_state'],'UNSIGNED');self.assertEqual(result['status'],'INVALID')
        self.assertFalse(result['accepted'])

    def test_subject_substitution_rejected(self):
        old=subjects()[1];new=s.SigningSubject(manifest(files=(('a',b'new-data'),)).artifacts.artifacts[0])
        self.error('RELEASE_SIGNATURE_SUBJECT_MISMATCH',lambda:request(new,envelope_=envelope(old)))

    def test_release_substitution_rejected(self):
        old=subjects()[1];new=s.SigningSubject(manifest('2.0.0').artifacts.artifacts[0])
        self.error('RELEASE_SIGNATURE_RELEASE_MISMATCH',lambda:request(new,envelope_=envelope(old)))
        self.error('RELEASE_SIGNATURE_RELEASE_MISMATCH',lambda:request(new,policy_=policy((old,))))

    def test_signer_substitution_policy_rejected(self):
        req=request();changed=replace(req.envelope,signer=replace(req.expected_signer,key_id='different-key-reference'))
        result=s.verify(replace(req,envelope=changed))
        self.assertEqual(result.status,'POLICY_REJECTED')
        self.assertEqual(result.record()['cryptographic_validity'],'NOT_VERIFIED')

    def test_trust_domain_substitution_rejected_and_policy_reidentified(self):
        req=request();domain=replace(DOMAIN,fingerprint='E'*64);pol=replace(req.policy,trust_domain=domain)
        self.assertNotEqual(pol.fingerprint(),req.policy.fingerprint())
        self.assertEqual(s.verify(replace(req,policy=pol)).status,'POLICY_REJECTED')

    def test_policy_without_allowed_signer_fails_closed(self):
        req=request()
        self.assertEqual(s.verify(replace(req,policy=replace(req.policy,allowed_signers=()))).status,'POLICY_REJECTED')

    def test_valid_structure_is_not_crypto_valid_or_trusted(self):
        result=s.verify(request()).record()
        self.assertEqual(result['signature_state'],'SIGNED_STRUCTURE_ONLY')
        self.assertEqual(result['cryptographic_validity'],'UNAVAILABLE');self.assertEqual(result['trust'],'NOT_EVALUATED')
        self.assertEqual(result['authentication_claim'],'NONE')

    def test_no_authority_approval_safety_compatibility_provenance_escalation(self):
        record=s.verify(request()).record()
        for key in ('production_authenticated','accepted','grants_authority','grants_release_approval',
                    'artifact_safety_proven','compatibility_proven','provenance_authenticated'):
            self.assertFalse(record[key])

    def test_provider_unavailable_no_signature_emitted(self):
        req=request();attempt=s.sign(req.subject,req.expected_signer)
        self.assertIsNone(attempt.envelope);self.assertEqual(attempt.record()['status'],'UNAVAILABLE')
        self.assertFalse(attempt.record()['signing_performed'])
        self.assertFalse(s.SigningProviderCapability().record()['production_available'])

    def test_arbitrary_crypto_provider_objects_never_called(self):
        class Callback:
            def verify(self,*args):raise AssertionError('must never run')
            def sign(self,*args):raise AssertionError('must never run')
        req=request()
        self.error('RELEASE_SIGNING_OPERATION_INVALID',lambda:s.sign(req.subject,req.expected_signer,Callback()))
        self.error('RELEASE_SIGNATURE_BINDING_INVALID',lambda:replace(req.envelope,provider=Callback()))
        self.error('RELEASE_CRYPTO_PROVIDER_UNSUPPORTED',lambda:s.SigningProviderCapability('unreviewed-library'))

    def test_fixture_provider_cannot_count_as_production(self):
        key=signer('structural-fixture-only');req=request(signer_=key)
        record=s.verify(req).record()
        self.assertIn('TEST_FIXTURE_NOT_PRODUCTION',record['diagnostics'])
        self.assertFalse(record['production_authenticated'])
        self.error('RELEASE_SIGNATURE_FIXTURE_LABEL_REQUIRED',lambda:replace(req.envelope,origin='SUPPLIED_UNVERIFIED'))
        self.assertIsNone(s.sign(req.subject,key,s.SigningProviderCapability(key.provider)).envelope)

    def test_structural_mode_not_crypto_or_callbacks(self):
        req=replace(request(),mode='STRUCTURAL_INSPECTION')
        self.assertEqual(s.verify(req).status,'UNAVAILABLE')
        self.assertIn('STRUCTURAL_INSPECTION_NOT_CRYPTO_VERIFICATION',s.verify(req).record()['diagnostics'])
        self.error('RELEASE_VERIFICATION_MODE_UNSUPPORTED',lambda:replace(req,mode='execute-provider'))

    def test_no_timestamp_revocation_or_chain_fabrication(self):
        record=s.verify(request()).record()
        for key in ('certificate_chain','revocation','trusted_timestamp'):self.assertEqual(record[key],'NOT_EVALUATED')

    def test_policy_immutable_deterministic_and_bounded(self):
        values=subjects();keys=(signer(),replace(signer(),key_id='second-reference',public_key_fingerprint='E'*64))
        pol=replace(policy(values),allowed_signers=keys)
        swapped=replace(pol,required_subjects=tuple(reversed(values)),allowed_signers=tuple(reversed(keys)))
        self.assertEqual(pol.fingerprint(),swapped.fingerprint())
        self.error('RELEASE_TRUST_SUBJECTS_INVALID',lambda:replace(pol,required_subjects=values*(s.MAX_SUBJECTS+1)))
        self.error('RELEASE_TRUST_SIGNER_CONFLICT',lambda:replace(pol,allowed_signers=(keys[0],replace(keys[0],public_key_fingerprint='F'*64))))

    def test_channel_does_not_bypass_trust(self):
        man=manifest();release=replace(man.architecture.release,channel='STABLE')
        artifact=man.artifacts.artifacts[0];recipe=artifact.recipe
        descriptor=replace(artifact._slot.descriptor,release=release)
        inp=replace(recipe.inputs[0],release=release)
        changed=replace(artifact,recipe=replace(recipe,release=release,inputs=(inp,),outputs=(replace(recipe.outputs[0],descriptor=descriptor),)))
        result=s.verify(request(s.SigningSubject(changed)))
        self.assertEqual(result.status,'UNAVAILABLE');self.assertFalse(result.record()['accepted'])

    def test_bundle_missing_required_signature_incomplete(self):
        pol=policy()
        bundle=s.ReleaseSignatureBundle(pol)
        self.assertEqual(bundle.status,'INCOMPLETE');self.assertFalse(bundle.record()['production_signed'])
        result=s.verify(request(pol.required_subjects[0],pol))
        self.assertEqual(s.ReleaseSignatureBundle(pol,(result,)).status,'INCOMPLETE')

    def test_signature_bundle_independent_and_order_deterministic(self):
        pol=policy();results=tuple(s.verify(request(subject,pol)) for subject in pol.required_subjects)
        a=s.ReleaseSignatureBundle(pol,results);c=s.ReleaseSignatureBundle(policy(),tuple(reversed(results)))
        self.assertEqual(a.fingerprint(),c.fingerprint());self.assertEqual(a.status,'UNAVAILABLE')
        self.assertFalse(a.record()['cryptographically_verified'])
        with self.assertRaises(FrozenInstanceError):a.results=()

    def test_duplicate_or_cross_policy_bundle_rejected(self):
        pol=policy();result=s.verify(request(pol.required_subjects[0],pol))
        self.error('RELEASE_SIGNATURE_BUNDLE_CONFLICT',lambda:s.ReleaseSignatureBundle(pol,(result,result)))
        self.error('RELEASE_SIGNATURE_BUNDLE_INVALID',lambda:s.ReleaseSignatureBundle(replace(pol,revision='2'),(result,)))

    def test_unsigned_bundle_is_not_signed(self):
        pol=policy();results=tuple(s.verify(request(subject,pol,envelope_=None)) for subject in pol.required_subjects)
        bundle=s.ReleaseSignatureBundle(pol,results)
        self.assertEqual(bundle.status,'INCOMPLETE');self.assertFalse(bundle.record()['production_signed'])

    def test_policy_revision_binds_verification_result(self):
        req=request();revised=replace(req,policy=replace(req.policy,revision='2'))
        self.assertNotEqual(req.fingerprint(),revised.fingerprint())
        self.assertNotEqual(s.verify(req).fingerprint(),s.verify(revised).fingerprint())

    def test_pipeline_signing_gate_explicit_and_other_blockers_unchanged(self):
        source=snapshot();subject=s.SigningSubject(manifest().artifacts.artifacts[0]);pol=policy((subject,))
        bundle=s.ReleaseSignatureBundle(pol,(s.verify(request(subject,pol)),));gate=s.signing_gate(bundle)
        self.assertEqual(gate.status,'BLOCKED')
        before=tuple(e for e in source.evidence if e.kind!='SIGNING')
        result=replace(source,evidence=before+(gate,))
        self.assertEqual(before,tuple(e for e in result.evidence if e.kind!='SIGNING'))
        self.assertFalse(result.record()['release_ready'])
        self.assertTrue(all(d.record()['state']=='BLOCKED' for d in p.publication_dry_run(result)))

    def test_fixture_cannot_enable_pipeline_publication(self):
        subject=subjects()[1];key=signer('structural-fixture-only');pol=policy((subject,),key)
        gate=s.signing_gate(s.ReleaseSignatureBundle(pol,(s.verify(request(subject,pol,key)),)))
        self.assertNotEqual(gate.status,'PASS')

    def test_no_io_provider_dispatch_or_host_time_dependency(self):
        req=request()
        with patch('builtins.open',side_effect=AssertionError('no I/O')):
            result=s.verify(req);s.sign(req.subject,req.expected_signer);s.signing_gate(s.ReleaseSignatureBundle(req.policy,(result,)))
        self.assertNotIn(str(ROOT),req.canonical_json());self.assertNotIn('timestamp',req.subject.canonical_json())

    def test_independent_subject_envelope_request_result_deterministic(self):
        a,c=request(),request()
        self.assertIsNot(a,c)
        self.assertEqual(a.subject.fingerprint(),c.subject.fingerprint())
        self.assertEqual(a.envelope.fingerprint(),c.envelope.fingerprint())
        self.assertEqual(a.fingerprint(),c.fingerprint());self.assertEqual(s.verify(a).fingerprint(),s.verify(c).fingerprint())

    def test_static_security_audit(self):
        source=(ROOT/'apexforge/tooling/release_security.py').read_text();tree=ast.parse(source)
        imports={a.name for node in ast.walk(tree) if isinstance(node,ast.Import) for a in node.names}
        imports|={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)}
        self.assertFalse(imports & {'os','pathlib','subprocess','socket','requests','urllib','keyring','cryptography','nacl','Crypto','time','ctypes','pickle'})
        calls={node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,(ast.Attribute,ast.Name))}
        self.assertFalse(calls & {'open','read_bytes','getenv','run','Popen','generate_private_key','eval','exec','__import__','pow','execute_native','apply','upload'})
        self.assertNotIn('PRIVATE KEY',source);self.assertNotIn('hmac',source.lower())


if __name__=='__main__':unittest.main(verbosity=2)
