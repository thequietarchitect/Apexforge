# P16.11 Release Security, Signing & Verification Integration — Review Evidence

## Baseline and incoming inventory

Branch: p16-1-release-baseline.
HEAD / P15 freeze: c9c5ca186c9d942ce336ac1ebfe1287b16953200.
Tag: afp-p15.14-freeze.
Tag object: d7761c04e4422bfb91d9582275a60912874678f4.
Peeled target equals HEAD. Before editing: exactly 30 incoming untracked P16
candidates; tracked/staged diffs empty; no ignored/generated residue.

Incoming SHA-256 census:
```text
E145F5836FC652533050C501C289C740A3E62AFF2AD26E4AC0448E2A44B4E0E7  apexforge/p16_10_ci_release_pipeline_dry_run_test.py
D8849A290CF65A0FAB56416CFE0D6DD4588CAD28425E2B218BB604F918EEF869  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
F12B0E26ED0589CBD11DF8F6729A8D10801EF3900E438000B422BAE4012F7DDE  apexforge/p16_6_vscode_distribution_packaging_test.py
3D3CEA0DA2FD2F1E8F779EB40628B6E7E4DA0E3B6854057360B12B4AAC3DB616  apexforge/p16_7_visualstudio_distribution_packaging_test.py
01639541D42E0F9814897F73EEABE54C6E78F064F593613AFEAD000D238D1C5E  apexforge/p16_8_native_distribution_packaging_test.py
FB928F16E828F5013074EFB697262C54A76E7E6E88D9708E3CBA14CD99411E72  apexforge/p16_9_install_upgrade_rollback_test.py
F2070A9831DD461321342CBCC8AC79CDB41BE6F59E41375471FDBD4A3DE88D3B  apexforge/tooling/native_distribution.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
9662672BA7CFE5FDD0C1DDD71B02B6C8804D8C2EA58FE4DF8E6D2E3F0B7679AC  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
8024EBC81C3910B188D741BBE6EBBF23F423782628546EF2C700FF391FC19219  apexforge/tooling/release_installation.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
CCC0778130E5D08687DAE8A63803059B8CE4C6B0032A3427FF0595A00DEC8778  apexforge/tooling/release_pipeline.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
D92139A8BD491347762A488AEFBDF3C50E945E8F4923A5A339C7D6084F4E474F  apexforge/tooling/visualstudio_distribution.py
60040C7E90D99BC14771D9CC93DA7F8D518BB25157A6E17F9AFB3ADDCBB6EBB8  apexforge/tooling/vscode_distribution.py
068D6B31DAF200DB06054A269ABB10F260F686994B3C86F06B2AD4BE80116A72  docs/p16/P16_10_CI_RELEASE_PIPELINE_DRY_RUN.md
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
478EE3227FEA029B7C1F9193F66D83D7D93D1A68E214AC0B9B29C18299B22BF6  docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
0FB837164A660844374A7C8534FD4AC88C36DC79CCAC7988736351B56D064F4F  docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md
0F83C51FB2C9B8E93B4D39CBDA03ACC82DCF12B6CD08DF031960A7D324DD4E90  docs/p16/P16_7_VISUAL_STUDIO_DISTRIBUTION_PACKAGING.md
9187091909FF50B12D3A6F4321CBBC2E5A13D433D4CFC716AC2B609E16C282AF  docs/p16/P16_8_NATIVE_WIN_X64_DISTRIBUTION_PACKAGING.md
47D54B944421C67339DA74DACFC51EE451C84F858BDE6E35236EC0BE61835657  docs/p16/P16_9_INSTALL_UPGRADE_ROLLBACK.md
```

Only release_security.py, the focused test and this report are added. No P16.12
acceptance or P16.13 closure/freeze work is performed. The historical AGENTS.md
P11 program text does not supersede the explicit P16.11 assignment; its frozen,
engineering and safety rules remain observed.

## Frozen owner and crypto census

| Inspected owner / concept | Classification | Relationship |
| --- | --- | --- |
| tooling/package_trust.py; P14.6 tests/report | FROZEN_PACKAGE_TRUST_CONTRACT / REUSE | Explicit ed25519 identifier, fingerprint syntax and 64-byte envelope layout; no change to package signing payload or trust policy |
| P14.6 unavailable verifier | FROZEN_CRYPTO_PROVIDER_CONTRACT / PROVIDER_UNAVAILABLE | Structural payload/key checks never yield cryptographic VALID |
| P14.12 supply-chain validation | FROZEN_PACKAGE_TRUST_CONTRACT / REFERENCE_ONLY | Authentication evidence remains passive, final crypto trust not established |
| P14 trust anchors / namespace rules | REFERENCE_ONLY | Package-specific semantics are not reinterpreted as release trust |
| P16.4 canonical manifest/checksum/provenance | REUSE | Exact owner fingerprints, bytes and SHA-256 evidence |
| P16.5–P16.8 signature/trust boundaries and artifact evidence | REFERENCE_ONLY | No target signing wrapper, rebuild or environment repair |
| P16.10 signing gate / publication model | REUSE | Existing BLOCKED/FAIL evidence adapter; no earlier-slice patch |
| Public key/certificate fingerprints | RELEASE_SIGNING_EXTENSION_POINT | Symbolic references only, not acquired material or chain validation |
| Release trust-policy declaration | TRUST_POLICY_EXTENSION_POINT | Exact release/subjects/algorithms/signers/domain; no authentication |
| Authenticode, VSIX/wheel/Marketplace signatures | REFERENCE_ONLY / PROVIDER_UNAVAILABLE | No approved executable adapter in inspected contracts |
| Historical Git signatures | REFERENCE_ONLY | P15 commit signature status N; annotated tag has no signature block |
| Production release approval / freeze | DEFER_TO_P16_12 / DEFER_TO_P16_13 | No implementation |

pyproject.toml declares dependencies=[]; no cryptographic package is installed
or added. Review availability probe checked module discovery and executable lookup
only:
```text
cryptography=False
nacl=False
Crypto=False
signtool=False
openssl=False
gpg=False
```
No tool was executed to sign/verify; no private store, keyring, enrollment, KMS,
HSM, public certificate store or environment-secret lookup was performed.
The frozen owner exposes no approved production adapter. Merely discovering or
installing a library would not approve/activate one.

P16_11_PRODUCTION_CRYPTO_PROVIDER_AVAILABLE=False.
CRYPTO_PROVIDER_UNAVAILABLE is preserved. Git's historical unsigned state is
separate from package/release cryptographic trust. No history, signing
infrastructure, Git object or certificate state was changed.

## Structural signing subjects and exact context

SigningSubject is immutable and accepts only exact P16.4 ReleaseManifest or P16.3
ReleaseBuildArtifact owner models. Bare filename, digest, raw arbitrary-data string
or callback provider is not a signing subject. Exact P15 baseline is required.
Manifest subjects require owner COMPLETE status; artifact subjects recheck supplied
digest equality. This does not add package qualification or release approval.

Manifest data is the exact P16.4 canonical JSON encoded UTF-8. Any changed artifact,
checksum or provenance member changes the manifest bytes/fingerprint and subject.
Artifact data is exact owner bytes; identity binds the descriptor, recipe, artifact,
release, digest, length and owner checksum/provenance references. Same filename or
length cannot substitute different bytes.

Signable payload uses apexforge.release-signing-payload/v1 with the complete
canonical subject context: exact release/baseline, kind, subject fingerprint,
descriptor where applicable, SHA-256, byte length and lineage. Payload fingerprint
is domain-separated. A checksum alone is never promoted to a signature or detached
from its release/identity context. No in-place manifest signature mutation occurs.

The generic detached release context does not implement embedded Authenticode,
VSIX, wheel, Marketplace or Git signatures. Canonical AIR remains the semantic
authority; artifact and signature representations do not replace it.

## Algorithm, provider and signer reference

Only the repository-owned declared ed25519 algorithm is accepted. Unknown,
unspecified, case-aliased and substituted identifiers reject before verification.
The algorithm is explicitly serialized and part of identity; it is not inferred
from byte length. No second algorithm is added for coverage and no Ed25519/RSA/
ECDSA primitive is implemented.

SigningProviderCapability is an immutable descriptor with two bounded identities:
frozen-provider-unavailable and structural-fixture-only. Both record
production_available=False, can_sign=False, can_verify=False,
can_validate_chain=False. Neither dispatches code. Caller objects/callbacks and
unreviewed provider identities reject by exact type/identity checks.

SignerIdentity contains symbolic key ID, explicit provider, public-key fingerprint,
trust-domain reference, declared RELEASE_SIGNER role and optional certificate
fingerprint. No private bytes, passphrase, token, PIN, certificate-store handle or
organizational authority field exists. Fingerprints must be canonical uppercase
SHA-256 syntax; zero placeholders are rejected. A well-formed supplied fingerprint
is not proof of mathematical key validity, key ownership or authenticated issuer.

Certificate evidence is fingerprint-only. Certificate bytes/parsing, X.509 chain,
trust-anchor validation, signer authorization, revocation and trusted timestamping
are not implemented and remain NOT_EVALUATED. No certificate presence implies
trust. Trust-domain reference matching is a policy comparison, not certificate
chain evaluation; no claim of trust-anchor substitution validation is emitted.

## Signature envelope and unsigned state

ReleaseSignatureEnvelope binds exact subject/payload/release, explicit algorithm,
signer reference, known provider descriptor, supplied provider-result reference,
bounded signature bytes, schema and origin. It reuses P14's layout checks while
retaining a separate P16 schema and payload; it is not a P14 package signature.

The initial declared Ed25519 representation is exactly 64 signature bytes.
Empty, zero-placeholder, short, oversized or wrong-type values reject.
Unsigned is envelope=None, not an empty/dummy envelope. Supplied nonzero bytes
passing these structural checks are still unverified; no mathematical validity
is asserted. The provider-result reference is supplied lineage, not authenticated
provider issuance.

Origins are SUPPLIED_UNVERIFIED and TEST_FIXTURE. A structural-fixture-only provider
requires TEST_FIXTURE origin. Focused tests use explicitly labeled arbitrary
non-production byte fixtures and symbolic fingerprints, not generated keys,
known-answer crypto verification or valid production signatures.

SIGNING_CONTRACT_VALID != PRODUCTION_SIGNING_AVAILABLE.
A valid structural envelope cannot authenticate provenance or satisfy the
production pipeline signing gate.

## Trust policy, request and result

ReleaseTrustPolicy is immutable, deterministic and bounded. It binds exact release,
policy ID/revision, required subjects, allowed algorithm identifiers, allowed
signer references and required trust-domain reference. Required signatures and
verified trust cannot be disabled by a development/stable channel. Empty signer
allowlists fail policy eligibility; conflicting key references reject. The policy
does not authenticate a signer or grant runtime authority.

SignatureVerificationRequest binds the exact subject, envelope (or explicit
unsigned state), expected signer, algorithm, mode and policy fingerprint.
Only PRODUCTION_VERIFICATION and STRUCTURAL_INSPECTION modes exist. Subject/release/
algorithm substitution rejects structurally; signer/domain/allowlist mismatch
produces policy rejection. Policy revisions re-identify requests and results.

SignatureVerificationResult is derived from its immutable request; callers cannot
label the result VALID or production-authenticated:
- missing envelope: INVALID with UNSIGNED and RELEASE_SIGNATURE_MISSING;
- expected signer or policy mismatch: POLICY_REJECTED, NOT_VERIFIED;
- matching structure/policy: UNAVAILABLE, CRYPTO_PROVIDER_UNAVAILABLE;
- fixture/structural mode: additional explicit non-production/non-crypto diagnostic.

Cryptographic validity, signature presence, signer-reference match, trust and
authentication claim are separate fields. Trust/chain/revocation/timestamp remain
NOT_EVALUATED. Accepted/production_authenticated/provenance_authenticated,
authority/release approval/safety/compatibility claims are all False.
No cryptographic VALID result or trusted-publisher result is produced by this
slice. Malformed inputs fail with deterministic structured exceptions rather than
exception prose being canonical identity.

The production signing entry point returns SigningOperationEvidence with
UNAVAILABLE, CRYPTO_PROVIDER_UNAVAILABLE, signing_performed=False and envelope=None.
It never emits a fake signature, even for the fixture provider.

## Signature bundle and owner integrations

ReleaseSignatureBundle binds exact policy/release, required subjects and exact
verification results. It canonicalizes by subject fingerprint, allows one envelope
per required subject, rejects duplicate/conflicting subjects and cross-policy
evidence, and bounds counts. It does not implement a multisignature threshold
language. Missing results or unsigned required subjects produce INCOMPLETE;
policy rejection produces REJECTED; a complete structural set remains UNAVAILABLE.
production_signed/cryptographically_verified/trusted are False.

P16.4 remains manifest/checksum/provenance owner. Signatures and verification
results are separate evidence references, never mutations of the fingerprinted
manifest. No checksum is treated as authentication and structural provenance is
not retroactively authenticated.

signing_gate maps bundle evidence into the unchanged P16.10 GateEvidence model,
with exact bundle reference and BLOCKED (or FAIL for rejection). It requires no
P16.10 patch and does not fabricate signing PASS. The historical
P16_11_SIGNING_REQUIRED reason remains an operational prerequisite, not proof
that architecture failed or a provider exists.

Actual in-memory demonstration using explicitly labeled fixture bytes:
```text
production_provider_available=False
signing_status=UNAVAILABLE
signing_envelope=None
verification_status=UNAVAILABLE
cryptographic_validity=UNAVAILABLE
signature_state=SIGNED_STRUCTURE_ONLY
trust=NOT_EVALUATED
authentication_claim=NONE
production_authenticated=False
bundle_status=UNAVAILABLE
pipeline_signing_gate=BLOCKED
unrelated_pipeline_evidence_unchanged=True
python_publication=BLOCKED
vscode_publication=BLOCKED
visual_studio_publication=BLOCKED
native_publication=BLOCKED
release_ready=False
publication_performed=False
```

The demonstration reuses the declared install-review / 1.0.0 / DEVELOPMENT fixture
context; it does not select a production release or real key. The result explicitly
retains TEST_FIXTURE_NOT_PRODUCTION. No raw signature vector is presented as
cryptographic success. Signing-architecture PASS does not clear unrelated blockers.

## Carry-forward facts and prohibitions

P16.5 sdist local construction/content reproducibility PASS; raw timestamp variance,
wheel unavailable. P16.6 model/archive/source continuity PASS with exact frozen
Git projection; real offline VSCE unverified. P16.7 genuine cache-only VSIX,
assembly continuity and P16.3/P16.4 integration PASS; raw/member/assembly
reproducibility remains DEFERRED. P16.8 genuine EXE, AMD64, measured byte
reproducibility/continuity/integration PASS only for the exact frozen profile.
P16.9 isolated contract PASS with one host-limited symlink skip; no global
installation. P16.10 provider-neutral pipeline PASS, all publication targets
BLOCKED, release readiness false, no credentials/publication.

P16.11 acquires no production/public key or certificate, installs no crypto
dependency, does no signing operation or actual crypto verification, accesses no
credential/store/network, and performs no timestamp/revocation service query.
No actual signing, publication, installation, key enrollment, Git commit/tag
signing, history rewrite, release acceptance or freeze occurs.

CHECKSUM != SIGNATURE
SIGNATURE_VALID != TRUSTED_PUBLISHER
SIGNATURE_VALID != SEMANTIC_CORRECTNESS
SIGNATURE_VALID != ARTIFACT_SAFETY
SIGNED_ARTIFACT != COMPATIBLE_ARTIFACT
SIGNED_ARTIFACT != RELEASE_APPROVAL
SIGNED_ARTIFACT != INSTALLED_ARTIFACT
SIGNING_KEY != ORGANIZATION_IDENTITY
CERTIFICATE_PRESENT != TRUST
KEY_ID != AUTHORITY
KEY_REFERENCE != VERIFIED_OWNER
TRUST_POLICY != CANONICAL_AIR
VERIFICATION_SUCCESS != RUNTIME_AUTHORITY
CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE

## Bounds, determinism and static audit

Owner subject data: at most 8 MiB each, 16 MiB per policy, at most 64 required
subjects / allowed signers / verification results, 64-byte signatures, bounded
symbolic IDs and canonical fingerprint/reference syntax. Diagnostic lists are
bounded fixed code sets. No unbounded recursive chain or parser is added.

Equivalent independent/permuted subjects, policies, requests, results and bundles
produce identical fingerprints and diagnostics. Host names, process IDs, temp
paths, provider process identities, certificate-store paths and current time are
not consulted. Artifact bytes remain exact explicit inputs even where earlier
packagers carry measured path/timestamp reproducibility limitations.

Static AST audit: no crypto library import/primitive, HMAC, pow/curve arithmetic,
key literal, private-key loader, secret environment lookup, store/keyring, network,
subprocess/OpenSSL/GPG/signtool command, dynamic imports/eval/exec, provider callback,
installation/publication or RuntimeEngine invocation. SHA-256 is integrity/identity
hashing only. Evaluation with filesystem I/O trapped still succeeds in the
unavailable-provider mode.

## Validation and Patch Matrix

Focused P16.11: 35/35 PASS. This is signing/verification contract PASS, not actual
cryptographic signing/verification PASS.
Predecessor focused: P16.10 34 PASS; P16.9 39 PASS + one host-limited SKIP; P16.8
36, P16.7 38, P16.6 33, P16.5 35, P16.4 41, P16.3 31, P16.2 31, P16.1 25 PASS.
P16 aggregate: 379 discovered, 378 PASS + one unchanged SKIP, no failures.
P14: 330/330 PASS. Native profile: 7/7 PASS. Authority consolidation PASS,
including wrong principal/capability/resource denial, authorized RuntimeEngine
execution and transactional denied execution. Only that unchanged smoke exercises
RuntimeEngine.
P15: 428/428 PASS.

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES -> PATCH SURFACE
-> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

Provider absence is classified RELEASE_CRYPTO_PROVIDER_UNAVAILABLE /
FROZEN_CRYPTO_PROVIDER_CONTRACT, not a reason to install libraries, invent a
provider, generate a key or weaken trust. P16.11's exact-subject/signature/trust
extension is architecture-preserving and references frozen owners. No executed
test failure or earlier-slice owning defect required a patch. Malformed,
substituted, missing and untrusted-reference cases are expected negative tests.
The existing host-limited P16.9 skip is preserved and not counted as PASS.

## Preservation and exact Git state

Final audit: exactly 33 intended untracked P16 candidates; all 30 incoming
SHA-256 hashes match byte-for-byte. Branch remains p16-1-release-baseline;
HEAD and P15 branch remain c9c5ca186c9d942ce336ac1ebfe1287b16953200. P15 tag
object remains d7761c04e4422bfb91d9582275a60912874678f4 and peels to the same
freeze commit. Tracked/staged diffs are empty; no ignored/generated key,
certificate, signature, build, installation, cache or temporary repository residue
exists. No frozen or P16.1–P16.10 file changed. No credentials/store material
were accessed or acquired. No crypto package installation, key/certificate
generation/import/enrollment, signing, publication, staging, commit, tag, push,
history rewrite, or P16.12 work occurred.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_11_INCOMING_CANDIDATES=30
P16_11_REDEFINES_CORE_SEMANTICS=False
P16_11_REDEFINES_P14_PACKAGE_TRUST=False
P16_11_PRODUCTION_CRYPTO_PROVIDER_AVAILABLE=False
P16_11_PROVIDER_UNAVAILABLE_FAILS_OPEN=False
P16_11_PRIVATE_KEY_MATERIAL_STORED=False
P16_11_KEY_REFERENCE_AUTHENTICATES_OWNER=False
P16_11_CERTIFICATE_PARSE_GRANTS_TRUST=False
P16_11_VERIFICATION_RESULT_GRANTS_AUTHORITY=False
P16_11_CUSTOM_CRYPTO_IMPLEMENTED=False
P16_11_TEST_SIGNATURE_FIXTURE_COUNTS_AS_PRODUCTION=False
P16_11_ARBITRARY_CRYPTO_CALLBACKS_SUPPORTED=False
P16_11_UNAVAILABLE_PROVIDER_EMITS_SIGNATURE=False
P16_11_CREDENTIAL_ACQUISITION=False
P16_11_NETWORK_ACCESS=False
P16_11_PRIVATE_CERTIFICATE_STORE_ACCESS=False
P16_11_TRUSTED_TIMESTAMPING_IMPLEMENTED=False
P16_11_REVOCATION_STATUS_FABRICATED=False
P16_11_TRUST_POLICY_GRANTS_AUTHORITY=False
P16_11_RELEASE_CHANNEL_IMPLIES_TRUST=False
P16_11_REDEFINES_RELEASE_MANIFEST=False
P16_11_PUBLICATION_PERFORMED=False
P16_11_INSTALLATION_PERFORMED=False
P16_11_GIT_COMMIT_SIGNING_PERFORMED=False
P16_11_GIT_TAG_SIGNING_PERFORMED=False
P16_11_FROZEN_GIT_HISTORY_REWRITTEN=False
P16_11_TARGET_SPECIFIC_SIGNING_FABRICATED=False
P16_11_SIGNING_SUBJECT_EXACT_BYTES_BOUND=True
P16_11_MANIFEST_SIGNATURE_EXACT_MANIFEST_BOUND=True
P16_11_ARTIFACT_SIGNATURE_CONTENT_BOUND=True
P16_11_SIGNATURE_ALGORITHM_EXPLICIT=True
P16_11_ALGORITHM_NOT_INFERRED=True
P16_11_SIGNATURE_ENVELOPE_IMMUTABLE=True
P16_11_UNSIGNED_NOT_VALID_SIGNATURE=True
P16_11_VERIFICATION_EXACT_SUBJECT_BOUND=True
P16_11_SIGNATURE_VALIDITY_DISTINCT_FROM_TRUST=True
P16_11_TRUST_POLICY_DETERMINISTIC=True
P16_11_MISSING_REQUIRED_SIGNATURE_NOT_SIGNED=True
P16_11_SIGNATURE_NOT_BARE_FILENAME_OR_DIGEST=True
P16_11_SIGNATURE_PRESENCE_DOES_NOT_AUTHENTICATE_PROVENANCE=True
P16_11_PIPELINE_SIGNING_EVIDENCE_EXPLICIT=True
P16_11_SIGNING_PASS_DOES_NOT_CLEAR_UNRELATED_BLOCKERS=True
P16_11_MALFORMED_SIGNATURE_EVIDENCE_FAILS_CLOSED=True
P16_11_SUBJECT_SUBSTITUTION_FAILS_CLOSED=True
P16_11_RELEASE_SUBSTITUTION_FAILS_CLOSED=True
P16_11_SIGNER_SUBSTITUTION_FAILS_CLOSED=True
P16_11_ALGORITHM_SUBSTITUTION_FAILS_CLOSED=True
P16_11_SECURITY_EVIDENCE_DETERMINISTIC=True
P16_11_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_11_WALL_CLOCK_NOT_CANONICAL_IDENTITY=True
P16_11_SIGNATURE_SET_DETERMINISTIC=True
P16_11_CONFLICTING_SIGNATURE_DUPLICATE_FAILS_CLOSED=True
P16_11_STATIC_SECURITY_AUDIT=PASS
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_SECURITY_MODEL=PASS
P16_RELEASE_SIGNING_SUBJECT_MODEL=PASS
P16_RELEASE_SIGNATURE_ALGORITHM_MODEL=PASS
P16_RELEASE_SIGNER_IDENTITY_MODEL=PASS
P16_RELEASE_SIGNATURE_ENVELOPE_MODEL=PASS
P16_RELEASE_SIGNATURE_VERIFICATION_MODEL=PASS
P16_RELEASE_SIGNATURE_SUBSTITUTION_HANDLING=PASS
P16_RELEASE_TRUST_POLICY_MODEL=PASS
P16_RELEASE_SIGNATURE_BUNDLE_MODEL=PASS
P16_RELEASE_CRYPTO_PROVIDER_BOUNDARY=PASS
P16_RELEASE_CERTIFICATE_BOUNDARY=PASS
P16_RELEASE_REVOCATION_BOUNDARY=PASS
P16_RELEASE_TIMESTAMP_BOUNDARY=PASS
P16_RELEASE_SIGNING_PIPELINE_INTEGRATION=PASS
P16_RELEASE_SIGNING_MANIFEST_INTEGRATION=PASS
P16_RELEASE_SIGNING_TRUST_BOUNDARY=PASS
P16_RELEASE_SIGNING_AUTHORITY_BOUNDARY=PASS
P16_RELEASE_SIGNING_SECURITY_BOUNDARY=PASS
P16_10_REGRESSION=PASS
P16_9_REGRESSION=PASS_WITH_HOST_LIMITED_SKIP
P16_8_REGRESSION=PASS
P16_7_REGRESSION=PASS
P16_6_REGRESSION=PASS
P16_5_REGRESSION=PASS
P16_4_REGRESSION=PASS
P16_3_REGRESSION=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS_WITH_HOST_LIMITED_SKIP
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_11_READY_FOR_REVIEW=True
```

PASS means the structural model and fail-closed unavailable-provider behavior are
demonstrated. It does not mean a real signer, crypto verifier or trust chain exists.
