# P16.4 — Release Manifest, Checksums & Provenance Bundle

## Scope and frozen baseline

P16.4 adds release-level evidence over reviewed P16.1–P16.3 owners. It consumes
explicit immutable records and supplied bytes. It does not assemble artifacts,
package any target, sign, publish, install, authorize, or approve a release.

Branch: `p16-1-release-baseline`.
HEAD and frozen P15 commit: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
P15 tag: `afp-p15.14-freeze`.
Annotated tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
P15 parent: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
The incoming branch, HEAD, tag object, peeled target and P15 branch were checked.
Tracked and staged diffs were empty. There were exactly nine untracked P16 paths
and no additional ignored/generated residue.

## Incoming SHA-256 census

All nine incoming paths are preserved byte-for-byte. SHA-256 uses uppercase
hexadecimal, matching the existing contract convention.

```text
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
```

## Ownership census

| Existing owner/evidence | Classification | P16.4 relationship |
| --- | --- | --- |
| P16.1 release identity, frozen baseline, target, descriptor and matrix | REUSE | Exact objects and domain-separated references; no parallel architecture |
| P16.2 surface-version mappings | REUSE | Optional exact mappings; release, surface and primary descriptor versions must agree |
| P16.2 compatibility policy and upgrade assessment | REFERENCE_ONLY | Completeness never establishes compatibility or upgrade eligibility |
| P16.3 artifact set, recipe, artifact and digest utility | REUSE | Supplied exact build evidence; no assembler invocation |
| P15.1 CanonicalModel/canonical JSON | REUSE | Existing deterministic JSON and fingerprint conventions only |
| P14 package_manifest PackageCoordinate, PackageContentIdentity, CanonicalReference | REUSE / FROZEN_PACKAGE_MANIFEST_CONTRACT | Preserve paired package identity/content in the descriptor; never replace a package manifest |
| P14.11 package_artifacts artifact manifest/build receipt | REFERENCE_ONLY / FROZEN_PACKAGE_MANIFEST_CONTRACT | Package/native artifact ownership stays frozen; release inventory has a separate scope |
| P14 package_trust integrity/signature models | FROZEN_TRUST_CONTRACT | SHA-256 equality remains integrity-only; unavailable crypto is not bypassed |
| P14 package_supply_chain evidence/provenance | FROZEN_PROVENANCE_CONTRACT | Package validation and provenance semantics remain owner-defined |
| P14 package_publishing records | REFERENCE_ONLY | Publication is not performed or inferred |
| P15 closure evidence and P16 predecessor reports | REFERENCE_ONLY | Frozen baseline and existing slice boundaries |
| Release-level checksum scope, provenance owner links and completeness | RELEASE_EVIDENCE_EXTENSION_POINT | Sole new production contract of this slice |
| Python/final target artifacts | DEFER_TO_P16_5 | Current generic bytes are not certified production packages |
| Signing/authentication | DEFER_TO_P16_11 | CRYPTO_PROVIDER_UNAVAILABLE |
| Release-candidate acceptance/approval | DEFER_TO_P16_12 | A complete scoped manifest is not release readiness |
| SPDX/SBOM | REFERENCE_ONLY | Repository search identified no reusable SPDX/SBOM owner; none introduced |

## Manifest and artifact inventory

`ReleaseManifest` is frozen and uses schema/domain
`apexforge.release-manifest/v1`. It binds the exact P16.1 matrix fingerprint,
full release identity and baseline, descriptor records, supplied P16.3 artifact
set (including recipes), checksum set, provenance bundle and optional P16.2
surface mappings. Unsupported manifest schemas are rejected, not silently read
as v1. No serialized-input parser is introduced.

The initial manifest validation profile accepts the exact P15 baseline from
P16.1. Another frozen baseline produces a distinct fingerprint and an INVALID
manifest with RELEASE_MANIFEST_BASELINE_MISMATCH. The current tag, tag object,
commit and parent are retained together, without deriving identity from Git or
the host. Provenance/checksum containers retain their supplied release baseline;
manifest validation is the profile gate.

Inventory rows include artifact identity, exact descriptor/recipe/artifact
references, role, target, format, byte length, digest and evidence state.
Missing artifact length/digest/reference is null, never an invented empty file.
Filename alone does not establish identity. Same filename with another identity
is rejected at exact inventory binding. The full descriptor retains optional
P14 package coordinate and content identity as an exact pair. A changed package
content identity changes dependent evidence identity.

Descriptors describe expectations; build artifacts describe actual supplied
bytes; manifests associate their evidence. A generic COPY_BYTES artifact is not
claimed to be a final wheel, sdist, VSIX, DLL or other qualified target package.
The `target_packaging` field remains NOT_ESTABLISHED.

## Checksums and caller-supplied verification

`ReleaseChecksumRecord` requires exact release/artifact identity, descriptor,
recipe and build-artifact references, explicit algorithm SHA256, uppercase
64-character hexadecimal digest and integer byte length. Boolean/floating
lengths, negative/oversized lengths, malformed digests, omitted algorithms and
unsupported algorithms fail with structured codes. Digests are never repaired
or replaced.

`checksum_for` projects already-supplied P16.3 artifact evidence. It does not
build anything. `verify_checksum` requires the exact projected record and exact
build artifact before checking bounded caller-supplied bytes for both length and
SHA-256 equality. Byte or binding mismatches raise deterministic structured
errors. Its returned canonical reference is integrity evidence only.

`ReleaseChecksumSet` binds exact release and exact architecture matrix scope.
Records sort by logical artifact identity; identical or conflicting duplicate
identities are rejected. No circular dependency on a future manifest fingerprint
exists. Later target-packaging owners can supply new exact artifact evidence and
new scope; P16.4 does not fabricate those artifacts in advance.

Checksum match is not a signature, authentication, publisher verification,
package trust or release approval. Checksum records explicitly report
authenticated=False and trusted=False.

## Provenance model and explicit chain

`ReleaseProvenanceRecord` contains a bounded identity, exact release, bounded kind,
exact canonical subject and exact predecessor references. Kinds are:
FROZEN_SOURCE_BASELINE, RELEASE_IDENTITY, RELEASE_ARCHITECTURE, VERSION_MAPPING,
ARTIFACT_DESCRIPTOR, BUILD_RECIPE, BUILD_ARTIFACT and ARTIFACT_CHECKSUM.

`ReleaseProvenanceBundle` binds the release and its exact baseline; canonicalizes
records by identifier; rejects duplicate identifiers and duplicate kind/subject
claims, including conflicting contents. Predecessor references are sorted and
duplicates rejected. Authentication and authorship remain NOT_ESTABLISHED.

Required structural links are:

1. Frozen P15 baseline -> release identity.
2. Release identity -> exact architecture matrix and optional surface mappings.
3. Architecture matrix -> each exact artifact descriptor.
4. Release and exact output descriptors -> build recipe.
5. Recipe and exact descriptor -> built artifact.
6. Build artifact, descriptor and recipe -> checksum record.
7. Manifest -> the exact scoped checksum/provenance bundles and all owner evidence.

`required_lineage` only describes required owner references. It creates no
provenance record and establishes no authorship. Callers must supply each record.
Manifest evaluation compares exact subjects and predecessor sets. A record with
the expected subject and contradictory links is INVALID; a missing record is
INCOMPLETE. Unexpected provenance is INVALID when its owner evidence is supplied.
If an entire owner evidence class is missing, its related supplied provenance
cannot make that evidence exist: the manifest remains INCOMPLETE. No provenance
bundle refers to its containing manifest fingerprint, avoiding a self-referential
seal. The manifest fingerprint binds the bundle instead.

P14 package lineage is preserved in the exact descriptor record and therefore in
descriptor, recipe, build artifact and manifest identities. Release provenance
does not reinterpret P14 package trust or claim verified authorship.

## Completeness and diagnostics

COMPLETE requires every descriptor in the explicit architecture scope to have
exact supplied artifact, checksum and all required provenance owner links.
Optional supplied version mappings must bind the release and surface exactly;
primary target-version mappings must match descriptor versions and carry their
own required provenance.

Missing build artifact, checksum or required provenance is INCOMPLETE.
Contradictory release, baseline, architecture, descriptor, checksum, version,
provenance or unexpected artifact evidence is INVALID. Contradictions take
precedence over missing evidence. Malformed constructors and duplicates fail
closed with structured reason codes. Diagnostics are sorted code/subject tuples;
exception prose is never used as identity.

A complete manifest grants no compatibility, trust, authentication, authority or
release approval. Published/installed remain false. No status means a runtime,
workflow, packaging, publication or installation ran.

## Serialization, determinism and bounds

All canonical serialization reuses CanonicalModel: sorted-key compact JSON,
UTF-8 fingerprint encoding, deterministic collection ordering, no nonfinite
floating values and domain-separated uppercase SHA-256 fingerprints. No parser,
new top-level wire owner, timestamp, random identity or host discovery is added.
Host paths cannot be injected by this module; artifact payload bytes are omitted
from manifest serialization and represented by exact length/digest evidence.
Caller-supplied opaque bytes are never interpreted, imported or executed.

Checksum/provenance collections are bounded at 8,192 records; provenance
predecessor references are bounded in total at 32,768. Existing P16.1/P16.3 bounds
remain in force (1,024 artifact/input slots, 1 MiB per byte payload and 8 MiB
aggregate input/output budgets). Algorithms iterate over bounded collections.
Independent construction of 1,000 artifacts produces 1,000 checksum records and
3,004 provenance records; exact complete manifests have equal fingerprints.
Permutation tests separately prove canonical checksum/provenance ordering.

## Boundaries and static security audit

Production imports are restricted to dataclasses, re and inspected frozen
in-process owner modules. AST audit rejects execution/acquisition calls including
eval, exec, open, compile, dynamic import, assemble, getenv, system and popen.
A dynamic trap on the P16.3 assembler proves manifest evaluation, fingerprinting
and checksum verification do not invoke it. Script-like supplied bytes remain data.

No filesystem discovery, network, credentials, subprocess/shell/toolchain, Git,
target packaging, build execution, publication, installation, signing, rollback,
CI automation or model dispatch is introduced. No trust keys/certificates are
acquired and no signature validation success is claimed. Crypto remains
CRYPTO_PROVIDER_UNAVAILABLE.

P16.1 remains architecture owner, P16.2 version/compatibility owner, P16.3
build/reproducibility owner, P14 package manifest/trust owners remain frozen,
and CANONICAL_AIR remains semantic authority.

## Patch Matrix

Local review findings were classified as RELEASE_COMPLETENESS_GAP (retained
provenance with omitted owner evidence), RELEASE_MANIFEST_BINDING_GAP
(primary version/baseline continuity) and RELEASE_ARTIFACT_INVENTORY_GAP
(explicit inventory references). Owning section: P16.4 only. Patch surface:
the new module and focused tests. Frozen dependencies: P16.1–P16.3 and P15/P14
unchanged. Corrections preserve exact owner bindings and fail-closed behavior.

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

No predecessor patch or weakened assertion was required. Final validation and
preservation evidence are recorded below after completion.

## Validation and preservation

| Command / contract | Demonstrated result |
| --- | --- |
| python -X utf8 -B apexforge/p16_4_release_manifest_provenance_test.py | 41/41 PASS |
| python -X utf8 -B apexforge/p16_3_reproducible_release_build_test.py | 31/31 PASS |
| python -X utf8 -B apexforge/p16_2_release_versioning_compatibility_test.py | 31/31 PASS |
| python -X utf8 -B apexforge/p16_1_release_architecture_contract_test.py | 25/25 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p16_*_test.py | 128/128 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py | 428/428 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| python -X utf8 -B apexforge/authority_consolidation_smoke_test.py | PASS |

Authority evidence: canonical identities PASS; exact grant PASS;
wrong principal/capability/resource denial PASS; authorized RuntimeEngine execution
PASS; denied execution transactional PASS. Runtime execution occurs only in that
unchanged frozen smoke test, never in P16.4 production or focused tests.

Final local audits also classified RELEASE_EVIDENCE_SECURITY_BOUNDARY_GAP:
schema type is checked before equality, and the reference helper accepts exact
inspected owner types rather than duck-typed caller methods. Hostile caller-object
tests pass. The final focused and aggregate P16 runs include both corrections.

The nine incoming hashes were recomputed and matched. Branch, HEAD, P15 branch,
tag object and peeled target remain unchanged. No tracked P15/P14/earlier path
changed. Tracked and staged diffs are empty. No ignored/generated residue exists.
No P16.5 work, stage, commit, tag or push was performed. The sole patch surface is
the three new P16.4 files. No unresolved finding remains; PATCH_MATRIX=PASS.

Exact Git status (twelve intended untracked candidates):

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/p16_2_release_versioning_compatibility_test.py
?? apexforge/p16_3_reproducible_release_build_test.py
?? apexforge/p16_4_release_manifest_provenance_test.py
?? apexforge/tooling/release_architecture.py
?? apexforge/tooling/release_build.py
?? apexforge/tooling/release_manifest.py
?? apexforge/tooling/release_versioning.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
?? docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
?? docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
?? docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
```

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_4_INCOMING_CANDIDATES=9
P16_4_ALL_INCOMING_HASHES_PRESERVED=True
P16_4_REDEFINES_CORE_SEMANTICS=False
P16_4_REDEFINES_P14_PACKAGE_MANIFEST=False
P16_4_REDEFINES_P14_PACKAGE_TRUST=False
P16_4_RELEASE_MANIFEST_EXACT_RELEASE_BOUND=True
P16_4_RELEASE_MANIFEST_DETERMINISTIC=True
P16_4_ARTIFACT_INVENTORY_CONTENT_BOUND=True
P16_4_DESCRIPTOR_AND_ARTIFACT_DISTINCT=True
P16_4_CHECKSUM_ALGORITHM_EXPLICIT=True
P16_4_CHECKSUM_MISMATCH_FAILS_CLOSED=True
P16_4_CHECKSUM_MATCH_GRANTS_TRUST=False
P16_4_CHECKSUM_MATCH_AUTHENTICATES=False
P16_4_CHECKSUM_SET_DETERMINISTIC=True
P16_4_CONFLICTING_CHECKSUM_DUPLICATE_FAILS_CLOSED=True
P16_4_PROVENANCE_BUNDLE_DETERMINISTIC=True
P16_4_CONFLICTING_PROVENANCE_DUPLICATE_FAILS_CLOSED=True
P16_4_PROVENANCE_CHAIN_EXPLICIT=True
P16_4_PROVENANCE_AUTHENTICATION_IMPLEMENTED=False
P16_4_SIGNING_IMPLEMENTED=False
P16_4_CRYPTO_TRUST_FABRICATED=False
P16_4_MISSING_EVIDENCE_NOT_COMPLETE=True
P16_4_COMPLETE_MANIFEST_GRANTS_RELEASE_APPROVAL=False
P16_4_EXACT_P15_FREEZE_BOUND=True
P16_4_REDEFINES_RELEASE_ARCHITECTURE=False
P16_4_MANIFEST_COMPLETENESS_GRANTS_COMPATIBILITY=False
P16_4_REDEFINES_VERSION_POLICY=False
P16_4_REDEFINES_RELEASE_BUILD=False
P16_4_BUILD_EXECUTION_IMPLEMENTED=False
P16_4_TARGET_PACKAGING_IMPLEMENTED=False
P16_4_CANONICAL_SERIALIZATION_DETERMINISTIC=True
P16_4_WALL_CLOCK_CANONICAL=False
P16_4_HOST_STATE_CANONICAL=False
P16_4_FILESYSTEM_DISCOVERY=False
P16_4_NETWORK_ACCESS=False
P16_4_CREDENTIAL_ACQUISITION=False
P16_4_HOST_COMMAND_EXECUTION=False
P16_4_PUBLICATION_PERFORMED=False
P16_4_INSTALLATION_PERFORMED=False
P16_4_RELEASE_EVIDENCE_GRANTS_AUTHORITY=False
P16_4_VALID_BUNDLE_GRANTS_TRUST=False
P16_4_ARTIFACT_BYTES_EXECUTED=False
P16_4_RELEASE_EVIDENCE_DETERMINISTIC=True
P16_4_DETERMINISM_USES_INDEPENDENT_CONSTRUCTION=True
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_MANIFEST_MODEL=PASS
P16_RELEASE_MANIFEST_BINDING=PASS
P16_RELEASE_ARTIFACT_INVENTORY=PASS
P16_RELEASE_CHECKSUM_MODEL=PASS
P16_RELEASE_CHECKSUM_VERIFICATION=PASS
P16_RELEASE_CHECKSUM_CONFLICT_HANDLING=PASS
P16_RELEASE_PROVENANCE_MODEL=PASS
P16_RELEASE_PROVENANCE_BUNDLE=PASS
P16_RELEASE_PROVENANCE_CONFLICT_HANDLING=PASS
P16_RELEASE_COMPLETENESS_MODEL=PASS
P16_RELEASE_EVIDENCE_DETERMINISM=PASS
P16_RELEASE_EVIDENCE_TRUST_BOUNDARY=PASS
P16_RELEASE_EVIDENCE_AUTHORITY_BOUNDARY=PASS
P16_RELEASE_EVIDENCE_SECURITY_BOUNDARY=PASS
P16_3_REGRESSION=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_4_READY_FOR_REVIEW=True
```


