# P14.6 — Package Signing, Integrity, Provenance & Trust

Provider-unavailable foundation ready for review. Actual asymmetric signing/verification remains unavailable; no cryptographic PASS is claimed.

## Baseline and hashes

Branch `p14-1-package-identity-manifest`; HEAD and peeled `afp-p13.12-freeze`:
`860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

All fifteen incoming SHA-256 hashes captured before editing and confirmed unchanged after all tests:

| Incoming file | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/p14_3_lockfile_reproducible_restore_test.py` | `F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F` |
| `apexforge/p14_4_package_namespace_export_resolution_test.py` | `BCE5A2A91310CED3FBDFC0A6B284CC2D5C017F63C662DF36E8C10502FBFC1C3F` |
| `apexforge/p14_5_package_capability_contract_test.py` | `B496B2159CBFF1F799281FB4184443A44D59561DD43BAFD770C41A9CBB5E6808` |
| `apexforge/tooling/package_capabilities.py` | `F2B7A04640BB35362DACB18F600995EC225AE7B7FD423C9FFA18975A00CBFAF9` |
| `apexforge/tooling/package_lock.py` | `D9AA13C73B92A1F5FA4A0DDEE365A8978484F694B0E5DD3A42AC0892FB726E94` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `apexforge/tooling/package_namespace.py` | `57B6D3C8BB005D50E640E170525ACEC14C82134E1662AD5932F9BA0B66E42C05` |
| `apexforge/tooling/package_solver.py` | `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |
| `docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md` | `CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B` |
| `docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md` | `7490A98A1C14EB975FCB51A6FB612E3D50A080FFD7A77BEF86B2548DD48E4FDE` |
| `docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md` | `9E5DF5321AF33ADD30DA28BE896C5F81DE1A431509042C6AF0F4E1BE8848C63B` |
| `docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md` | `6BCC55F9A1FDC09E7F7EFA96A1F7ADC78FBE785F9A8E554A0D315598FCB8043D` |

## Crypto and predecessor census

Repository searches for Ed25519, cryptography, PyNaCl, Sigstore, GPG, signatures and public-key conventions found no reusable signing provider/model in the searched Python/dependency surfaces. pyproject.toml declares dependencies=[].

The installed Python probe reported cryptography=False, nacl=False, sigstore=False; importing cryptography raised ModuleNotFoundError. Classification: CRYPTO_PROVIDER_UNAVAILABLE (environmental capability gap). No package/dependency installation or manual cryptography was attempted.

| Facility | Classification | Decision |
|---|---|---|
| Existing SHA-256/domain-separated P14 identity hashes | REUSE | Manifest, resolution and lock conventions retained. |
| P14.1 canonical manifests/content descriptors/provenance | REUSE | Signing-material commitment and actual supplied-byte integrity. |
| P14.3 lock identity | REUSE | Exact coordinate/content match; no editing. |
| P14.5 compatibility | REFERENCE_ONLY | Independent structural dimension; no trust inference. |
| P12/P13 provenance evidence | REFERENCE_ONLY | Evidence reference is not content/proof; provenance is not actor attribution. |
| Existing authority model/engine | REFERENCE_ONLY | Frozen authority owner; no invocation from this module. |
| cryptography/PyNaCl/Sigstore asymmetric provider | UNAVAILABLE | Crypto execution deferred; no SUPPORTED_LIBRARY classification justified. |

The envelope anticipates Ed25519 raw public bytes/signature sizes only. No Ed25519 implementation, successful signing, actual signature validation, mathematical key validity or crypto-tamper rejection is claimed. This implementation always returns CRYPTO_PROVIDER_UNAVAILABLE after successful structural payload/key checks. A future vetted-provider integration is required; merely installing a provider would not automatically activate this module.

## Signing payload and coverage

Signing material is compact sorted ASCII-safe JSON encoded UTF-8 with schema `apexforge.package-signature-payload/v1`, exact coordinate and canonical P14.1 content identity. The content identity already commits to schema, coordinate, logical member descriptors/digests, ordered document contract, exports/dependencies/capability declarations and provenance references. No duplicate invented manifest hash.

Payload fingerprint: SHA-256 of `apexforge.package-signing-payload-fingerprint/v1`, NUL, payload bytes. The payload schema provides signing-domain separation independently of this digest. Existing content and lock fingerprints retain their own domains.

Identity signatures would cover canonical identity, not non-identity metadata. Presentation title/description/etc. remain NON_IDENTITY_METADATA_UNSIGNED. Changing metadata leaves signing material unchanged; coordinate, identity fields, content descriptor digest or provenance-reference changes alter it.

Actual signatures are not produced. The provenance-signing PASS marker below means deterministic payload commitment has been demonstrated, not that a signature has cryptographically authenticated provenance.

## Actual content integrity

`ContentMember` holds a validated package-relative PackagePath and immutable supplied bytes. `verify_integrity` accepts only caller-supplied tuple members and a validated manifest. No host paths, filesystem reads, extraction or discovery.

Exact member set is required: missing, unexpected and SHA-256 digest mismatch are separate deterministic diagnostics. Duplicate/case-colliding supplied paths reject before verification. Matching is exact logical path spelling; P14.1 owns path/hash validation. No filesystem metadata is hashed.

`IntegrityResult` is immutable and records canonical content fingerprint, VALID/INVALID and ordered path/code diagnostics. Content failure prevents explicit acceptance regardless of envelope/policy. A 1,100-member fixture demonstrates order-independent integrity and signing material without recursive traversal.

## Signer identity and envelope

Raw 32-byte Ed25519-shaped public input yields a domain-separated SHA-256 key fingerprint using `apexforge.package-signing-key/v1`. This is a structural representation boundary, not mathematical public-key validation; key identity is unrelated to filenames, namespaces, people or organizations.

`SignatureEnvelope` is immutable: schema `apexforge.package-signature/v1`, algorithm exactly ed25519, signer/payload uppercase fingerprints, 64-byte signature encoded lowercase hex in records. Unknown schema/algorithm, malformed hashes, wrong types/lengths reject. No fallback. Placeholder test bytes are explicitly unverified fixtures, not signatures.

Verification reconstructs payload, compares payload fingerprint and recomputes signer fingerprint from supplied public bytes. Wrong payload yields SIGNING_PAYLOAD_MISMATCH/NOT_VERIFIED; wrong or absent matching public key yields SIGNER_KEY_FINGERPRINT_MISMATCH; matching shape and bindings yield CRYPTO_PROVIDER_UNAVAILABLE, never VALID.

UNSIGNED is distinct from malformed or unavailable signature verification. Changed signature bytes remain unavailable, not incorrectly classified as cryptographically valid/invalid. That portion of the tamper matrix is deferred.

## Explicit trust policy

`TrustAnchor` contains public bytes, with key fingerprint identity. `NamespaceTrustRule` accepts an exact fingerprint and validated exact package namespace. `TrustPolicy` is immutable with explicitly supplied anchors/rules and explicit require_signature/require_scope_trust booleans. No default anchors or TOFU.

Anchor/rule sets sort/deduplicate deterministically. Dangling rules reject. Contradictory require_scope_trust=True with require_signature=False rejects. Distinct keys may intentionally be accepted for a namespace; this is not a conflict or exclusive ownership record. No wildcard scopes, deny rule precedence, network revocation or registry ownership.

Policy fingerprint domain `apexforge.package-trust-policy-fingerprint/v1` commits to canonical key IDs, exact scope rules and acceptance flags. Labels/display names are not key identity.

SIGNER_TRUSTED means the supplied key matches a local anchor. TRUSTED_FOR_PACKAGE_SCOPE means that key has an exact namespace rule. These are **policy eligibility states**, not proof that a package signature authenticated the key. They remain separate from signature status; signed acceptance cannot succeed without cryptographic VALID. Removing anchors produces untrusted status; changing scope produces mismatch. Namespace policy is not organization ownership or human attribution.

## Verification versus acceptance and lock matching

`VerificationEvidence` is immutable canonical serialized evidence; record() returns a detached presentation copy. It records exact package identity, actual integrity, structural payload status, signature status/envelope, key ID, signer/scope policy eligibility, lock match/fingerprint, policy fingerprint, provenance and unsigned-metadata status. It is diagnostic output, not an authority token or persisted evidence parser.

No policy means accepted=None. An explicitly supplied policy may accept unsigned exact-integrity material only when both signature and scope requirements are disabled. Policy requiring signatures rejects unsigned material. Every signed envelope currently rejects acceptance because crypto is unavailable. Integrity invalidity and lock mismatch always reject.

Optional lock matching requires an exact admitted coordinate AND canonical content identity, for root or dependency nodes. Same-coordinate changed content yields LOCK_CONTENT_MISMATCH, independently of signature shape/payload. No solving, fallback selection, restore, lock regeneration or mutation. Lock-binding PASS is exact content association testing, not a valid-signature-with-lock experiment.

## Capability, authority and provenance boundaries

Capability compatibility and trust eligibility remain independent. Tests demonstrate compatible/untrusted and incompatible/anchor-scope-eligible combinations. The latter is not claimed cryptographically trusted while crypto is unavailable.

AuthorityEngine.check/allows patched to throw remain uncalled. No grants, runtime permissions or principal/role mutations. Provenance references are committed by canonical content and retained in evidence, but status is REFERENCE_COMMITTED_CLAIM_UNVERIFIED. Referenced historical content is neither loaded nor verified. No external actor attribution.

CONTENT_INTEGRITY != SIGNATURE_VALIDITY; SIGNATURE_VALIDITY != SIGNER_TRUST; SIGNER_TRUST != PACKAGE_SCOPE_TRUST; PACKAGE_SCOPE_TRUST != ORGANIZATION_OWNERSHIP; PACKAGE_TRUST != RUNTIME_AUTHORITY; PROVENANCE_REFERENCE != PROVENANCE_PROOF; SIGNED_PROVENANCE_REFERENCE != VERIFIED_PROVENANCE_CLAIM; VALID_SIGNATURE != AUTHORIZED_EXECUTION; TRUSTED_PACKAGE != EXECUTION_PERMISSION; CRYPTOGRAPHIC_IDENTITY != HUMAN_IDENTITY; VALID_SIGNATURE != LOCK_MATCH.

## Secret-key and security audit

No private-key object accepted, stored, logged, serialized or persisted in this provider-unavailable slice. No key store, key upload, signing primitive, insecure fallback or fabricated crypto.

AST/import audit excludes AIR/runtime/native execution, AuthorityEngine, subprocess/shell, network/socket/registry, arbitrary files, package discovery, dynamic payload imports, installation and private-key persistence. Package contents remain bytes only. Current trust set controls local eligibility; no network revocation.

## Validation

| Suite | Result |
|---|---|
| P14.6 supplied-byte integrity/signing/trust boundary | 19/19 PASS |
| P14.5 | 23/23 PASS |
| P14.4 | 23/23 PASS |
| P14.3 | 28/28 PASS |
| P14.2 | 38/38 PASS |
| P14.1 | 36/36 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 167/167 PASS |

Focused cases include canonical payload/metadata, identity/provenance tampering, real integrity, missing/extra/changed/duplicate members, path security, key fingerprint/shape, envelope rejection, honest provider-unavailable signature states, wrong key/ID, unsigned policy, anchor/scope changes, policy ordering/conflicts, exact lock matching, provenance truth boundary, authority noninvocation, capability separation, immutability, deterministic diagnostics, 1,100 members and static security.

Frozen authority consolidation smoke PASS: canonical identities, exact grant, wrong principal/capability/resource denial, authorized existing runtime fixture and transactional denied execution. This test's runtime execution is outside the package-trust module. Frozen P13 evidence/reference/attribution contracts were inspected; no additional native provenance execution was needed because no retention/provenance owner changed.

No focused/regression failures. Patch Matrix capability-gap routing:
FAILURE: vetted crypto imports unavailable.
CLASSIFICATION: CRYPTO_PROVIDER_UNAVAILABLE.
OWNER: P14.6 environment/provider seam.
FROZEN DEPENDENCIES: all prior stages read-only.
PATCH SURFACE: three new P14.6 files only.
LOCAL CONTRACT: unavailable crypto never reports VALID or signed acceptance; actual byte integrity implemented.
REGRESSIONS: focused/predecessors/aggregate PASS.
PRESERVATION: all fifteen incoming hashes and frozen files unchanged.
No cryptographic implementation repair, dependency installation or provider substitution performed.

## Remaining gaps

Actual signing and verification, wrong-key cryptographic verification, altered-signature rejection, mathematical public-key checks and authenticated provenance signatures remain CRYPTO_PROVIDER_UNAVAILABLE. No full signed-package acceptance demonstrated. Tests do not substitute fake crypto. Review readiness is for this explicitly allowed provider-unavailable architecture, not operational package signing.

No P14.7 cache, registry, publisher infrastructure, migration, installation, execution or P15. No signature file parser, key manager, network revocation, publisher ownership or runtime authority.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P14_6_INCOMING_CANDIDATES=15
P13_REOPENED=False
P14_SIGNING_PAYLOAD_DETERMINISTIC=True
P14_INTEGRITY_INPUT=EXPLICIT_SUPPLIED_CONTENT
P14_TRUST_ANCHORS_EXPLICITLY_SUPPLIED=True
P14_PRIVATE_KEY_STORAGE_IMPLEMENTED=False
P14_TRUST_ON_FIRST_USE_IMPLEMENTED=False
P14_SIGNATURE_ALGORITHM_FALLBACK=False
P14_TRUST_GRANTS_RUNTIME_AUTHORITY=False
P14_TRUST_INVOKES_AUTHORITY_ENGINE=False
P14_NETWORK_REVOCATION_IMPLEMENTED=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P14_TRUST_EXECUTES_AIR=False
P14_TRUST_EXECUTES_RUNTIME=False
P14_TRUST_DISPATCHES_NATIVE=False
P14_TRUST_GRANTS_AUTHORITY=False
P14_TRUST_NETWORK_ACCESS=False
P14_TRUST_FILESYSTEM_DISCOVERY=False
P14_TRUST_HOST_COMMAND_EXECUTION=False
P14_SIGNATURE_ALGORITHM=ED25519_ENVELOPE_ONLY_CRYPTO_PROVIDER_UNAVAILABLE
P14_SIGNER_IDENTITY=PUBLIC_KEY_FINGERPRINT
P14_SIGNATURE_COVERS_NON_IDENTITY_METADATA=False
P14_PACKAGE_INTEGRITY=PASS
P14_SIGNING_PAYLOAD=PASS
P14_SIGNATURE_ENVELOPE=PASS
P14_SIGNATURE_VERIFICATION=CRYPTO_PROVIDER_UNAVAILABLE
P14_SIGNER_TRUST=PASS
P14_PACKAGE_SCOPE_TRUST=PASS
P14_TRUST_POLICY_DETERMINISM=PASS
P14_SIGNATURE_LOCK_BINDING=PASS
P14_PROVENANCE_REFERENCE_SIGNING=PASS
P14_PROVENANCE_TRUTH_VALIDATION=False
P14_PACKAGE_TRUST_AUTHORITY_BOUNDARY=PASS
P14_PACKAGE_TRUST_SECURITY_BOUNDARY=PASS
P14_5_REGRESSION=PASS
P14_4_REGRESSION=PASS
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
P14_6_READY_FOR_REVIEW=True
```

## Exact Git status

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/p14_4_package_namespace_export_resolution_test.py
?? apexforge/p14_5_package_capability_contract_test.py
?? apexforge/p14_6_package_signing_integrity_provenance_trust_test.py
?? apexforge/tooling/package_capabilities.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_namespace.py
?? apexforge/tooling/package_solver.py
?? apexforge/tooling/package_trust.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
?? docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md
?? docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md
?? docs/p14/P14_6_PACKAGE_SIGNING_INTEGRITY_PROVENANCE_TRUST.md
```

Exactly eighteen candidates, three new. Branch/HEAD/tag object/peeled target unchanged. All fifteen hashes preserved; empty tracked/cached diffs confirm no frozen-file modification. No Python caches/bytecode, executable/library/symbol/object or VSIX residue. Nothing staged; no commit/tag/push. Stop at P14.6 review readiness.

