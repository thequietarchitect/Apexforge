"""P16.11 structural release signatures; no approved crypto adapter or key access."""
from dataclasses import dataclass, field
from hashlib import sha256
from tooling import package_trust as frozen, release_architecture as r, release_build as b, release_manifest as m
from tooling import release_pipeline as pipeline
from tooling.domain_platform import CanonicalModel, _json
from tooling.package_manifest import CanonicalReference

ALGORITHMS = (frozen.ALGORITHM,)
PROVIDERS = ('frozen-provider-unavailable', 'structural-fixture-only')
MAX_SUBJECT_BYTES, MAX_TOTAL_BYTES, MAX_SUBJECTS = 8 * 1024 * 1024, 16 * 1024 * 1024, 64
MODES = ('PRODUCTION_VERIFICATION', 'STRUCTURAL_INSPECTION')


class ReleaseSecurityError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def require(ok, code):
    if not ok:
        raise ReleaseSecurityError(code)


def hash_reference(value):
    try:
        frozen._hash(value)
    except ValueError as exc:
        raise ReleaseSecurityError('RELEASE_SIGNING_FINGERPRINT_INVALID') from exc
    require(value != '0' * 64, 'RELEASE_SIGNING_FINGERPRINT_INVALID')


def digest(data):
    require(type(data) is bytes and len(data) <= MAX_SUBJECT_BYTES, 'RELEASE_SIGNING_BYTES_INVALID')
    return sha256(data).hexdigest().upper()


def algorithm(value):
    require(type(value) is str and value in ALGORITHMS, 'RELEASE_SIGNATURE_ALGORITHM_UNSUPPORTED')


@dataclass(frozen=True)
class SigningProviderCapability(CanonicalModel):
    identifier: str = 'frozen-provider-unavailable'
    DOMAIN = 'apexforge.release-signing-provider/v1'

    def __post_init__(self):
        require(type(self.identifier) is str and self.identifier in PROVIDERS, 'RELEASE_CRYPTO_PROVIDER_UNSUPPORTED')

    def record(self):
        return {'id': self.identifier, 'algorithms': ALGORITHMS, 'production_available': False,
                'can_sign': False, 'can_verify': False, 'can_validate_chain': False,
                'state': 'CRYPTO_PROVIDER_UNAVAILABLE', 'fixture_only': self.identifier == 'structural-fixture-only'}


@dataclass(frozen=True)
class SigningSubject(CanonicalModel):
    owner: object = field(repr=False)
    DOMAIN = 'apexforge.release-signing-subject/v1'

    def __post_init__(self):
        require(type(self.owner) in (m.ReleaseManifest, b.ReleaseBuildArtifact), 'RELEASE_SIGNING_SUBJECT_INVALID')
        require(self.release.baseline == r.P15_BASELINE, 'RELEASE_SIGNING_BASELINE_MISMATCH')
        if type(self.owner) is m.ReleaseManifest:
            require(self.owner.status == 'COMPLETE', 'RELEASE_SIGNING_MANIFEST_INCOMPLETE')
        else:
            require(digest(self.owner.data) == self.owner.declared_digest, 'RELEASE_SIGNING_ARTIFACT_DIGEST_MISMATCH')
        digest(self.data)

    @property
    def release(self):
        return self.owner.architecture.release if type(self.owner) is m.ReleaseManifest else self.owner.recipe.release

    @property
    def kind(self):
        return 'RELEASE_MANIFEST' if type(self.owner) is m.ReleaseManifest else 'RELEASE_ARTIFACT'

    @property
    def data(self):
        return self.owner.canonical_json().encode('utf-8') if self.kind == 'RELEASE_MANIFEST' else self.owner.data

    def record(self):
        if self.kind == 'RELEASE_MANIFEST':
            lineage = (m.reference(self.owner.architecture), m.reference(self.owner.checksums), m.reference(self.owner.provenance))
            descriptor = None
        else:
            lineage = (m.reference(self.owner.recipe), m.reference(m.checksum_for(self.owner)))
            descriptor = m.reference(self.owner._slot.descriptor).record()
        return {'release': self.release.record(), 'kind': self.kind, 'subject': m.reference(self.owner).record(),
                'descriptor': descriptor, 'sha256': digest(self.data), 'length': len(self.data),
                'provenance': [x.record() for x in sorted(lineage, key=m.ref_key)],
                'semantic_authority': 'CANONICAL_AIR', 'authentication': 'NOT_ESTABLISHED'}

    def signing_bytes(self):
        # Signable context commits to release + identity + content, never a bare digest/filename.
        return _json({'schema': 'apexforge.release-signing-payload/v1', 'subject': self.record()}).encode('utf-8')

    def payload_fingerprint(self):
        return digest(b'apexforge.release-signing-payload-fingerprint/v1\0' + self.signing_bytes())


@dataclass(frozen=True)
class SignerIdentity(CanonicalModel):
    key_id: str
    public_key_fingerprint: str
    trust_domain: CanonicalReference
    provider: str = 'frozen-provider-unavailable'
    certificate_fingerprint: str | None = None
    role: str = 'RELEASE_SIGNER'
    DOMAIN = 'apexforge.release-signer-reference/v1'

    def __post_init__(self):
        r.text(self.key_id, 'RELEASE_SIGNER_KEY_ID_INVALID')
        hash_reference(self.public_key_fingerprint)
        require(type(self.trust_domain) is CanonicalReference and self.trust_domain.kind == 'provenance-scope', 'RELEASE_SIGNER_DOMAIN_INVALID')
        require(type(self.provider) is str and self.provider in PROVIDERS and type(self.role) is str and self.role == 'RELEASE_SIGNER',
                'RELEASE_SIGNER_REFERENCE_INVALID')
        if self.certificate_fingerprint is not None:
            hash_reference(self.certificate_fingerprint)

    def record(self):
        return {'key_id': self.key_id, 'public_key_fingerprint': self.public_key_fingerprint, 'provider': self.provider,
                'trust_domain': self.trust_domain.record(), 'certificate_fingerprint': self.certificate_fingerprint,
                'role': self.role, 'key_owner_authenticated': False, 'certificate_parse': 'NOT_EVALUATED',
                'certificate_chain': 'NOT_EVALUATED', 'signer_authorization': 'NOT_EVALUATED'}


@dataclass(frozen=True)
class ReleaseSignatureEnvelope(CanonicalModel):
    subject: SigningSubject
    signer: SignerIdentity
    signature: bytes = field(repr=False)
    provider_result: CanonicalReference
    algorithm: str = frozen.ALGORITHM
    provider: SigningProviderCapability = SigningProviderCapability()
    origin: str = 'SUPPLIED_UNVERIFIED'
    schema: str = 'apexforge.release-signature/v1'
    DOMAIN = 'apexforge.release-signature/v1'

    def __post_init__(self):
        require(type(self.subject) is SigningSubject and type(self.signer) is SignerIdentity and
                type(self.provider) is SigningProviderCapability and self.provider.identifier == self.signer.provider,
                'RELEASE_SIGNATURE_BINDING_INVALID')
        algorithm(self.algorithm)
        require(type(self.signature) is bytes and len(self.signature) == 64 and any(self.signature), 'RELEASE_SIGNATURE_MALFORMED')
        require(type(self.provider_result) is CanonicalReference, 'RELEASE_SIGNATURE_PROVIDER_REFERENCE_INVALID')
        require(type(self.schema) is str and self.schema == self.DOMAIN and type(self.origin) is str
                and self.origin in ('SUPPLIED_UNVERIFIED', 'TEST_FIXTURE'), 'RELEASE_SIGNATURE_SCHEMA_INVALID')
        require(not self.provider.record()['fixture_only'] or self.origin == 'TEST_FIXTURE', 'RELEASE_SIGNATURE_FIXTURE_LABEL_REQUIRED')
        # Reuse the frozen Ed25519 envelope encoding/length checks, not its package payload semantics.
        frozen.SignatureEnvelope(self.signer.public_key_fingerprint, self.subject.payload_fingerprint(), self.signature, self.algorithm)

    def record(self):
        return {'schema': self.schema, 'release': self.subject.release.fingerprint(), 'subject': self.subject.fingerprint(),
                'payload': self.subject.payload_fingerprint(), 'algorithm': self.algorithm, 'signer': self.signer.record(),
                'signature_hex': self.signature.hex(), 'provider': self.provider.record(),
                'provider_result': self.provider_result.record(), 'origin': self.origin,
                'cryptographically_verified': False, 'production_authenticated': False}


@dataclass(frozen=True)
class ReleaseTrustPolicy(CanonicalModel):
    identifier: str
    revision: str
    release: r.ReleaseIdentity
    trust_domain: CanonicalReference
    required_subjects: tuple
    allowed_signers: tuple = ()
    allowed_algorithms: tuple = ALGORITHMS
    DOMAIN = 'apexforge.release-trust-policy/v1'

    def __post_init__(self):
        r.text(self.identifier, 'RELEASE_TRUST_POLICY_INVALID'); r.text(self.revision, 'RELEASE_TRUST_POLICY_INVALID')
        require(type(self.release) is r.ReleaseIdentity and self.release.baseline == r.P15_BASELINE and
                type(self.trust_domain) is CanonicalReference and self.trust_domain.kind == 'provenance-scope', 'RELEASE_TRUST_POLICY_INVALID')
        require(type(self.allowed_algorithms) is tuple and bool(self.allowed_algorithms) and len(self.allowed_algorithms) <= len(ALGORITHMS),
                'RELEASE_TRUST_ALGORITHMS_INVALID')
        for value in self.allowed_algorithms:
            algorithm(value)
        require(len(set(self.allowed_algorithms)) == len(self.allowed_algorithms), 'RELEASE_TRUST_ALGORITHMS_INVALID')
        require(type(self.required_subjects) is tuple and 1 <= len(self.required_subjects) <= MAX_SUBJECTS and
                all(type(s) is SigningSubject and s.release == self.release for s in self.required_subjects), 'RELEASE_TRUST_SUBJECTS_INVALID')
        require(sum(len(s.data) for s in self.required_subjects) <= MAX_TOTAL_BYTES, 'RELEASE_TRUST_SIZE_LIMIT')
        require(len({s.fingerprint() for s in self.required_subjects}) == len(self.required_subjects), 'RELEASE_TRUST_SUBJECT_CONFLICT')
        require(type(self.allowed_signers) is tuple and len(self.allowed_signers) <= MAX_SUBJECTS and
                all(type(s) is SignerIdentity for s in self.allowed_signers), 'RELEASE_TRUST_SIGNERS_INVALID')
        require(len({(s.provider, s.key_id) for s in self.allowed_signers}) == len(self.allowed_signers), 'RELEASE_TRUST_SIGNER_CONFLICT')
        object.__setattr__(self, 'required_subjects', tuple(sorted(self.required_subjects, key=lambda s:s.fingerprint())))
        object.__setattr__(self, 'allowed_signers', tuple(sorted(self.allowed_signers, key=lambda s:s.fingerprint())))
        object.__setattr__(self, 'allowed_algorithms', tuple(sorted(self.allowed_algorithms)))

    def record(self):
        return {'id': self.identifier, 'revision': self.revision, 'release': self.release.fingerprint(),
                'trust_domain': self.trust_domain.record(), 'required_subjects': [s.fingerprint() for s in self.required_subjects],
                'allowed_signers': [s.fingerprint() for s in self.allowed_signers], 'algorithms': self.allowed_algorithms,
                'require_signature': True, 'require_verified_trust': True, 'channel_bypasses_policy': False,
                'authenticates_signer': False, 'grants_authority': False, 'trust_anchor_validation': 'NOT_IMPLEMENTED'}


@dataclass(frozen=True)
class SignatureVerificationRequest(CanonicalModel):
    subject: SigningSubject
    policy: ReleaseTrustPolicy
    expected_signer: SignerIdentity
    envelope: ReleaseSignatureEnvelope | None = None
    algorithm: str = frozen.ALGORITHM
    mode: str = 'PRODUCTION_VERIFICATION'
    DOMAIN = 'apexforge.release-signature-verification-request/v1'

    def __post_init__(self):
        require(type(self.subject) is SigningSubject and type(self.policy) is ReleaseTrustPolicy and
                type(self.expected_signer) is SignerIdentity, 'RELEASE_VERIFICATION_REQUEST_INVALID')
        algorithm(self.algorithm)
        require(type(self.mode) is str and self.mode in MODES, 'RELEASE_VERIFICATION_MODE_UNSUPPORTED')
        require(self.subject.release == self.policy.release, 'RELEASE_SIGNATURE_RELEASE_MISMATCH')
        require(self.subject in self.policy.required_subjects, 'RELEASE_SIGNATURE_SUBJECT_POLICY_MISMATCH')
        require(self.envelope is None or type(self.envelope) is ReleaseSignatureEnvelope, 'RELEASE_SIGNATURE_MALFORMED')
        if self.envelope is not None:
            require(self.envelope.subject.release == self.subject.release, 'RELEASE_SIGNATURE_RELEASE_MISMATCH')
            require(self.envelope.subject == self.subject, 'RELEASE_SIGNATURE_SUBJECT_MISMATCH')
            require(self.envelope.algorithm == self.algorithm, 'RELEASE_SIGNATURE_ALGORITHM_MISMATCH')

    def record(self):
        return {'subject': self.subject.fingerprint(), 'release': self.subject.release.fingerprint(), 'policy': self.policy.fingerprint(),
                'expected_signer': self.expected_signer.fingerprint(), 'algorithm': self.algorithm, 'mode': self.mode,
                'envelope': None if self.envelope is None else self.envelope.fingerprint()}


@dataclass(frozen=True)
class SignatureVerificationResult(CanonicalModel):
    request: SignatureVerificationRequest
    DOMAIN = 'apexforge.release-signature-verification-result/v1'

    def __post_init__(self):
        require(type(self.request) is SignatureVerificationRequest, 'RELEASE_VERIFICATION_RESULT_INVALID')

    def assessment(self):
        req = self.request
        if req.envelope is None:
            return 'INVALID', 'NOT_VERIFIED', 'UNSIGNED', ('RELEASE_SIGNATURE_MISSING',)
        if req.envelope.signer != req.expected_signer:
            return 'POLICY_REJECTED', 'NOT_VERIFIED', 'SIGNED_STRUCTURE_ONLY', ('RELEASE_SIGNER_MISMATCH',)
        if (req.algorithm not in req.policy.allowed_algorithms or req.expected_signer not in req.policy.allowed_signers or
                req.expected_signer.trust_domain != req.policy.trust_domain):
            return 'POLICY_REJECTED', 'NOT_VERIFIED', 'SIGNED_STRUCTURE_ONLY', ('RELEASE_TRUST_POLICY_REJECTED',)
        reasons = ['CRYPTO_PROVIDER_UNAVAILABLE']
        if req.envelope.origin == 'TEST_FIXTURE':
            reasons.append('TEST_FIXTURE_NOT_PRODUCTION')
        if req.mode == 'STRUCTURAL_INSPECTION':
            reasons.append('STRUCTURAL_INSPECTION_NOT_CRYPTO_VERIFICATION')
        return 'UNAVAILABLE', 'UNAVAILABLE', 'SIGNED_STRUCTURE_ONLY', tuple(sorted(reasons))

    @property
    def status(self):
        return self.assessment()[0]

    def record(self):
        status, crypto, signed, diagnostics = self.assessment()
        return {'request': self.request.fingerprint(), 'subject': self.request.subject.fingerprint(),
                'policy': self.request.policy.fingerprint(), 'status': status, 'cryptographic_validity': crypto,
                'signature_state': signed, 'signer_reference_match': self.request.envelope is not None and
                self.request.envelope.signer == self.request.expected_signer, 'trust': 'NOT_EVALUATED',
                'certificate_chain': 'NOT_EVALUATED', 'revocation': 'NOT_EVALUATED', 'trusted_timestamp': 'NOT_EVALUATED',
                'diagnostics': diagnostics, 'authentication_claim': 'NONE', 'production_authenticated': False,
                'accepted': False, 'grants_authority': False, 'grants_release_approval': False,
                'artifact_safety_proven': False, 'compatibility_proven': False, 'provenance_authenticated': False}


def verify(request):
    return SignatureVerificationResult(request)


@dataclass(frozen=True)
class SigningOperationEvidence(CanonicalModel):
    subject: SigningSubject
    signer: SignerIdentity
    provider: SigningProviderCapability = SigningProviderCapability()
    DOMAIN = 'apexforge.release-signing-operation/v1'

    def __post_init__(self):
        require(type(self.subject) is SigningSubject and type(self.signer) is SignerIdentity and
                type(self.provider) is SigningProviderCapability and self.signer.provider == self.provider.identifier,
                'RELEASE_SIGNING_OPERATION_INVALID')

    @property
    def envelope(self):
        return None

    def record(self):
        return {'subject': self.subject.fingerprint(), 'signer': self.signer.fingerprint(), 'provider': self.provider.fingerprint(),
                'status': 'UNAVAILABLE', 'diagnostics': ('CRYPTO_PROVIDER_UNAVAILABLE',), 'envelope': None,
                'signing_performed': False, 'production_authenticated': False}


def sign(subject, signer, provider=SigningProviderCapability()):
    return SigningOperationEvidence(subject, signer, provider)


@dataclass(frozen=True)
class ReleaseSignatureBundle(CanonicalModel):
    policy: ReleaseTrustPolicy
    results: tuple = ()
    DOMAIN = 'apexforge.release-signature-bundle/v1'

    def __post_init__(self):
        require(type(self.policy) is ReleaseTrustPolicy and type(self.results) is tuple and len(self.results) <= MAX_SUBJECTS and
                all(type(x) is SignatureVerificationResult and x.request.policy == self.policy for x in self.results),
                'RELEASE_SIGNATURE_BUNDLE_INVALID')
        require(len({x.request.subject.fingerprint() for x in self.results}) == len(self.results), 'RELEASE_SIGNATURE_BUNDLE_CONFLICT')
        object.__setattr__(self, 'results', tuple(sorted(self.results, key=lambda x:x.request.subject.fingerprint())))

    @property
    def status(self):
        if any(x.status == 'POLICY_REJECTED' for x in self.results):
            return 'REJECTED'
        if {x.request.subject.fingerprint() for x in self.results} != {s.fingerprint() for s in self.policy.required_subjects} or any(
                x.request.envelope is None for x in self.results):
            return 'INCOMPLETE'
        return 'UNAVAILABLE'

    def record(self):
        return {'release': self.policy.release.fingerprint(), 'policy': self.policy.fingerprint(), 'status': self.status,
                'subjects': [s.fingerprint() for s in self.policy.required_subjects], 'results': [x.fingerprint() for x in self.results],
                'production_signed': False, 'cryptographically_verified': False, 'trusted': False,
                'provenance_authenticated': False, 'grants_authority': False, 'grants_release_approval': False,
                'crypto': 'CRYPTO_PROVIDER_UNAVAILABLE'}


def signing_gate(bundle):
    require(type(bundle) is ReleaseSignatureBundle, 'RELEASE_SIGNING_PIPELINE_INPUT_INVALID')
    ref = CanonicalReference(bundle.DOMAIN, 'artifact', bundle.fingerprint())
    return pipeline.GateEvidence(bundle.policy.release, 'SIGNING', 'release', 'FAIL' if bundle.status == 'REJECTED' else 'BLOCKED',
                                 (ref,), ('CRYPTO_PROVIDER_UNAVAILABLE',))
