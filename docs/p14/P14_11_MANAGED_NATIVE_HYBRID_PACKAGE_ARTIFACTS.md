# P14.11 Managed, Native & Hybrid Package Artifacts

## Frozen baseline and preservation

Branch: `p14-1-package-identity-manifest`.
HEAD and peeled `afp-p13.12-freeze`: `860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.
Before implementation exactly 30 incoming P14 candidates were enumerated and SHA-256 captured. Tracked and cached diffs were empty. Branch, HEAD and both tag identities matched. No bytecode, pytest caches, native binaries/build outputs or temporary P14 test-root residue was present.

All 30 incoming hashes remain unchanged. Only package_artifacts.py, its focused test and this report were added; final candidate count is 33. No frozen P10/P11/P12/P13 source was modified. No staging, commit, tag or push occurred.

### Incoming SHA-256 (30/30 preserved)

```text
apexforge/p14_10_package_compatibility_migration_test.py ED7E0AF9A43771FB23030B866F62897FD6098EE36D9B669F75277DD2235CD99E
apexforge/p14_1_package_identity_manifest_contract_test.py 3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3
apexforge/p14_2_deterministic_dependency_solver_test.py C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47
apexforge/p14_3_lockfile_reproducible_restore_test.py F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F
apexforge/p14_4_package_namespace_export_resolution_test.py BCE5A2A91310CED3FBDFC0A6B284CC2D5C017F63C662DF36E8C10502FBFC1C3F
apexforge/p14_5_package_capability_contract_test.py B496B2159CBFF1F799281FB4184443A44D59561DD43BAFD770C41A9CBB5E6808
apexforge/p14_6_package_signing_integrity_provenance_trust_test.py F209EEF357AF894881C399D9E857202AE1C6DC4706E2460E62657E9A6B0F2937
apexforge/p14_7_content_addressed_package_cache_test.py 0E795FF9B0D06EEB7AA3CF571F47C2A94D4AFBF185AA1395AD516D46C2503A4D
apexforge/p14_8_registry_protocol_test.py B2BE44C37B50BA3B4EE96A2F495357F671CEE4A86CD702D8C03138EB388C15C2
apexforge/p14_9_package_publishing_test.py 1B5E9B21086DB59D51D0043AAE1EAACD43CE252E30FE5AA4158C0F1D7EE4D903
apexforge/tooling/package_cache.py DAB89DE443965C1053FCA0189D697E9FD4861A088AC7FB053A3715F4194A025A
apexforge/tooling/package_capabilities.py F2B7A04640BB35362DACB18F600995EC225AE7B7FD423C9FFA18975A00CBFAF9
apexforge/tooling/package_compatibility.py 9BDA7C54B6603000706D6D569F65510346832C3DC15ADF603AC8E7C9F78B4F7B
apexforge/tooling/package_lock.py D9AA13C73B92A1F5FA4A0DDEE365A8978484F694B0E5DD3A42AC0892FB726E94
apexforge/tooling/package_manifest.py 5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7
apexforge/tooling/package_namespace.py 57B6D3C8BB005D50E640E170525ACEC14C82134E1662AD5932F9BA0B66E42C05
apexforge/tooling/package_publishing.py 145FEDDBAFCFDB87331D7B76BA68CE786FB4499BD894C67B031ABB85FA94FF98
apexforge/tooling/package_registry.py D731ABC9554B63BF7EB631F878EA4ECAD7B13CFB89047D002832E2C1DE461E41
apexforge/tooling/package_solver.py 7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1
apexforge/tooling/package_trust.py 34445F195299756173690246E581664B7DF1D02EA432975EC90D2E3E28884FF7
docs/p14/P14_10_PACKAGE_COMPATIBILITY_MIGRATION.md 812B18DA433CB6151FC094B8117B0C4F1E7E15DBFB29CFDCAC55D590AF9B0D42
docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D
docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B
docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md 7490A98A1C14EB975FCB51A6FB612E3D50A080FFD7A77BEF86B2548DD48E4FDE
docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md 9E5DF5321AF33ADD30DA28BE896C5F81DE1A431509042C6AF0F4E1BE8848C63B
docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md 6BCC55F9A1FDC09E7F7EFA96A1F7ADC78FBE785F9A8E554A0D315598FCB8043D
docs/p14/P14_6_PACKAGE_SIGNING_INTEGRITY_PROVENANCE_TRUST.md 3985CB4940AD7150005DA5F9EC4864ABE366BB07386176D9E6358A4F039594BF
docs/p14/P14_7_CONTENT_ADDRESSED_PACKAGE_CACHE.md 52477C3097AE023A3A59ABF2A76B1D793B3C9DAA8CBDFC78E168BE0FCE190898
docs/p14/P14_8_REGISTRY_PROTOCOL.md 6307E85C9CC99320F9844D484CFD58F886B57AA27EA982D609A27DB0DBD18BAC
docs/p14/P14_9_PACKAGE_PUBLISHING.md 0899DCA2DE464FC7401B08F43A8E11F5A4E896AC3F8C7BEA34FCFE276C2A3BCD
```

## Existing artifact census

| Existing concept | Classification | Application |
|---|---|---|
| tooling.build_artifact CanonicalBuildArtifact and v1 canonical AIR envelope | REUSE / FROZEN_BUILD_CONTRACT | Consume existing serialized bytes; retain producer fingerprint without reconstructing a build |
| P11.15B interchange inspector and P11.15D integrity verifier | REUSE | Verify frozen canonical build fingerprint in memory |
| build-artifact/v2 narrative and v3 rich-document forms | REFERENCE_ONLY | Their word “native” denotes domain-native document/narrative artifacts, not Windows machine code; not admitted as AIR-managed variants |
| P11.13 package/document architecture and CLI project routing | FROZEN_BUILD_CONTRACT | Separate predecessor declaration/build contracts; not replaced by P14 |
| native_backend.native_execution NativeArtifact/receipt | ADAPT / FROZEN_BUILD_CONTRACT | Caller supplies image and receipt bytes; no Path access or backend ticket reissuance |
| native_execution_contract PROFILE | REUSE / FROZEN_BUILD_CONTRACT | Exact frozen profile constant; no new admission or lowering implementation |
| lowering_input canonical AIR transport | REFERENCE_ONLY | Managed AIR fingerprint convention and focused coexistence comparison |
| generated-C source digest and receipt routing/toolchain/options/image | REFERENCE_ONLY | Preserve exact receipt reference and generated-source hash, not a compiler invocation |
| P12.6 metadata/source/native mapping identities | REFERENCE_ONLY | Optional exact passive mapping reference; no metadata semantics changes |
| P12.7 managed/native retained execution evidence | REFERENCE_ONLY | Bounds meaning of managed/native; no new retained execution or equivalence claims |
| P12.8 reproducibility/resource custody evidence | FROZEN_BUILD_CONTRACT | Existing bounded toolchain/environment claim remains unchanged |
| NativeArtifact.image host Path and temporary build directories | NOT_A_PACKAGE_ARTIFACT | Never enter descriptor identity or trigger a filesystem read |
| P14.1 package content/relative paths/provenance | REUSE | Exact binding and existing path validation |
| P14.3 lock, P14.7 cache, P14.8 registry, P14.9 publication | REFERENCE_ONLY | Preserve identities and side-effect boundaries |
| P14.10 structural compatibility | REFERENCE_ONLY | Package contract compatibility is independent of representation target availability |

Repository inspection covered build serialization, rich-document architecture, native admission/build/receipt fields, managed retained evidence, metadata, reproducibility and existing P14 contracts. No standalone CLR/.NET artifact or universal managed portability contract was found.

## Exact supported forms

Artifact descriptor schema and bundle-manifest schema: `apexforge.package-artifacts/v1`.
A descriptor kind is MANAGED or NATIVE. HYBRID is a derived bundle classification when both independent kinds are present, not a third descriptor, merged executable or semantic implementation.

Managed means exact serialized `apexforge.build-artifact/v1` AIR-oriented build-envelope bytes. Target `apexforge-managed` is a P14 addressing label for this existing representation, not an OS architecture or a new runtime backend. Profile is its existing build schema. There is no .NET binary generation, independent .NET semantics, universal host compatibility or execution promise.

Native means supplied image bytes accompanied by a structurally admitted P12 canonical receipt. Explicit target is `win-x64`; profile is exactly:
`apexforge.native.win-x64.i64-literal-state-set/v1`.
No Linux/macOS/ARM target, wider lowering, additional type, runtime feature or profile expansion exists.

The native adapter verifies the receipt/image/fingerprint associations described below. It does not authenticate the producer, validate a PE executable, replay semantic admission, recreate an issuance ticket or prove successful execution. Supplied receipt evidence is passive and is not equivalent to P12's live issued NativeArtifact. Persisted native dispatch/admission remains outside P14.11.

## Descriptor, identities and package binding

ArtifactDescriptor is frozen and contains exact package content identity, kind/schema, package-relative logical path, raw byte digest, explicit target/profile, build reference, canonical AIR reference, optional source reference, ordered provenance, optional directive entrypoint and optional debug mapping reference.

Every descriptor in a bundle must bind to that bundle's exact P14.1 PackageContentIdentity. The package identity remains unchanged when describing independent artifact variants. This caller-supplied association is structural evidence, not proof that a build was historically produced from the package's sources.

Raw digest is uppercase SHA-256 of exact supplied bytes. The build producer fingerprint is retained separately; richer descriptor fingerprint uses SHA-256(`apexforge.package-artifact-descriptor/v1` + NUL + canonical JSON UTF-8). Package content identity, raw artifact digest, build fingerprint, descriptor fingerprint and bundle fingerprint remain separate domains.

A logical artifact name is a validated P14.1 PackagePath, never a host path. Absolute/drive/traversal/backslash forms fail. Bundle paths are casefold-unique and cannot have file/child conflicts. Target is never inferred from extension: the native fixture deliberately uses opaque.bin.

## Build/AIR/source lineage

### Managed adapter

describe_managed consumes a validated package manifest and existing envelope bytes. It rejects unsupported v2/v3 representations rather than synthesizing AIR. Strict parsing precedes frozen interchange inspection and fingerprint verification. The declared P11 build fingerprint must equal its canonical payload fingerprint; exact envelope bytes receive a separate raw digest.

The AIR reference uses the existing compact sorted, ensure_ascii=False canonical AIR transport convention. The focused test compares it with frozen build_verified_air_lowering_input over a verified existing AIR fixture. This is identity correspondence, not re-execution or semantic equivalence.

An optional supplied entrypoint must have the same AIR fingerprint and exactly match the build record's entry. Original source evidence remains committed by the frozen build-envelope fingerprint; no new guessed source mapping is minted. Descriptor source is explicitly unavailable (None) in this initial managed adapter.

### Native adapter

describe_native requires explicit target/profile, exact image bytes, canonical receipt bytes and the caller's receipt fingerprint. It validates the exact P12 receipt field set, canonical serialization, SHA-256 of receipt bytes, profile, AIR==owner_air, AIR/routing/source/image digest syntax, image digest equality, field shapes and toolchain digest values. Optional entrypoint must exactly match receipt entry and AIR.

Build reference wraps the existing receipt hash under `apexforge.native-build-receipt/v1`; it does not change P12 receipt hashing. AIR reference preserves the receipt AIR hash. Source reference is the receipt's generated-C source digest under `apexforge.native-generated-source/v1`, not an authored-source identity. Original source -> AIR links are retained only through independently supplied build/provenance evidence where available; generated C is not misrepresented as original source.

The adapters never construct or write build outputs, invoke MSVC/toolchain discovery, compile generated C, call RuntimeEngine, dispatch native code or inspect the host.

## Bundle and hybrid model

ArtifactBundle holds exact package content identity, a nonempty tuple of descriptors and exact supplied ArtifactPayload objects keyed by raw digests. Multiple descriptors may reference one identical payload without collapsing their descriptor identities.

All referenced digest keys must exactly equal supplied payload keys. Missing, extra and duplicate payload keys fail. Payload constructors verify bytes; bundle admission rechecks digest equality even for controlled corruption fixtures. Duplicate/conflicting logical descriptors fail. No partial validated bundle is returned.

Bundle canonical_record retains schema, package identity, derived MANAGED/NATIVE/HYBRID kind, CANONICAL_AIR semantic authority and each ordered descriptor. bundle_record additionally transports digest-keyed hex payload bytes. This is a deterministic in-memory representation, not a ZIP archive, extraction format, installer or universal packaging container.

Hybrid keeps managed and native descriptors/bytes separate. It does not assert they are semantically equivalent, share all behavior or represent the whole language. Canonical AIR remains authority for every representation; artifact availability does not authenticate correctness.

## Explicit selection and unsupported targets

select(kind, target, profile) accepts caller requirements, not live-host detection. For MANAGED/NATIVE, target/profile must be explicitly supplied from supported pairs. It returns the exact immutable descriptor only when one matching variant exists.

ANY without qualifiers over a hybrid or multiple variants is AMBIGUOUS_VARIANT. ANY with exact target/profile may select one exact match. There is no implicit preference, OS/architecture fallback, native-to-managed fallback, compilation or synthesis. Unsupported target pairs fail UNSUPPORTED_TARGET; absent supported variants fail NO_SUPPORTED_VARIANT; multiple exact variants fail AMBIGUOUS_VARIANT.

Selection is a structural plan result, not host validation, compatibility proof or authorization to execute.

## Canonicalization, parser and fingerprint

Descriptor order is canonical JSON record order; payloads are ordered by digest. Provenance references are sorted and deduplicated. Canonical JSON uses sorted keys, compact separators, ASCII escaping, UTF-8 and no timestamps, local handles, username, absolute paths or locale ordering. Exact payload bytes are never normalized.

Bundle fingerprint domain is `apexforge.package-artifacts/v1`, distinct from descriptor, manifest, build and lock domains. It commits to ordered descriptor records and therefore exact byte-digest references, not a second package identity.

Artifact evidence parser rejects duplicate JSON keys, nonfinite numbers, invalid UTF-8, malformed/deep JSON and inputs over 16 MiB. Integers are bounded to 128 digits for passive managed AIR transport, permitting the frozen I64 extrema without weakening P14.8's separate ten-digit protocol rule. This bound is input validation, not a native scalar expansion or a new language rule. The parser interprets metadata only and does not reconstruct or execute AIR.

## Interactions and deferred integration

Lock validate_lock confirms the bundle's exact package content appears in a supplied P14.3 lock. Content identity already commits to coordinate. Lock contents are not changed, and the lock does not become an artifact-selection lock.

Current cache/registry/publication records operate on P14.1 package members, not external artifact variants. Bundle records provide neutral side-effect-free bytes/reference evidence, but no artifact-specific registry or cache extension was added. Artifact payloads could only enter current package-member storage if the caller explicitly included them under the existing P14.1 content boundary; doing so affects package identity according to existing rules. Transporting out-of-band variants through new registry/cache semantics remains deferred to an explicit future extension. No automatic query, insertion, publication or mutation occurs.

Package contract compatibility (P14.10) is not artifact target compatibility. Having a matching image does not prove API compatibility, and a structurally compatible package may have no requested variant.

CRYPTO_PROVIDER_UNAVAILABLE remains active. Artifact digests verify byte identities only: they do not establish signed/trusted content, actor authentication, namespace ownership or execution authority. No passive signature state is upgraded.

## Provenance, debug and reproducibility boundaries

Package provenance references are preserved and remain passive. Build receipt/fingerprint linkage does not infer an author, organization, publisher or machine owner. EVIDENCE_BEFORE_ATTRIBUTION=True.

Optional debug references preserve exact source/native-mapping producer fingerprints, separate from payload identity. P14.11 does not evaluate debug mapping association, create PDBs, machine addresses, instruction pointers or richer native stepping.

P12.8 reproducibility remains bounded to the tested MSVC environment/toolchain/options. Packaging does not prove cross-machine/toolchain binary equality. P12.7 equivalence remains bounded to the frozen common domain; whole-language managed/native equivalence and independent .NET execution remain unproven.

## Security and resource boundary

The production module performs no filesystem I/O, network, registry query, compiler call, subprocess/shell, dynamic payload import, authority grant, installation, execution or private-key persistence. Frozen passive build inspector/verifier imports are used only for in-memory integrity. Native PROFILE is imported from the existing admission contract without calling admission.

Tests failure-trap native build/dispatch, RuntimeEngine.execute, AuthorityEngine.check, RegistryCatalog.query, publish, PackageCache.put and solve. All traps remain unused during packaging/selection. AST assertions inspect prohibited direct imports/calls. No test-owned filesystem root, executable launch or cleanup procedure is needed for this slice.

## Patch Matrix and failure history

| Observation | Classification / owner | Narrow correction |
|---|---|---|
| Initial 27 errors: registry JSON parser rejected valid 19-digit frozen I64 literal | PACKAGE_ARTIFACT_MANAGED_MODEL_GAP / P14.11 adapter | Replace inappropriate parser reuse with bounded artifact JSON admission; preserve duplicates/size/malformed checks and all predecessor contracts |
| One remaining fixture error: VerificationResult passed to frozen lowering | TEST_FIXTURE_DEFECT / P14.11 focused test | Use existing require_verified() conversion |
| Review: optional entrypoint could differ from supplied build entry despite AIR match | PACKAGE_ARTIFACT_BUILD_BINDING_GAP / P14.11 adapters | Require exact managed/native build-entry equality and add negative assertions; validate native toolchain digest syntax |

Frozen dependencies: P11 build/interchange, P12 profile/receipt/lowering, P13 and all 30 incoming P14 candidates unchanged. Patch surface stayed inside the new production/test pair. Local contracts: admit valid frozen I64 evidence, retain frozen verified wrapper semantics, and prohibit false entrypoint/build associations. Owning focused tests passed after corrections, all requested predecessor regressions passed, narrow frozen-profile coexistence passed, aggregate passed and final preservation passed.

```text
PACKAGE_ARTIFACT_MANAGED_MODEL_GAP=CLOSED
TEST_FIXTURE_DEFECT=CLOSED
PACKAGE_ARTIFACT_BUILD_BINDING_GAP=CLOSED
PATCH_MATRIX=PASS
```

## Validation and frozen coexistence

| Suite | Result |
|---|---|
| P14.11 focused | 27/27 PASS |
| P14.10 | 30/30 PASS |
| P14.9 | 24/24 PASS |
| P14.8 | 22/22 PASS |
| P14.7 | 25/25 PASS |
| P14.6 | 19/19 PASS |
| P14.5 | 23/23 PASS |
| P14.4 | 23/23 PASS |
| P14.3 | 28/28 PASS |
| P14.2 | 38/38 PASS |
| P14.1 | 36/36 PASS |
| Frozen P12.5 native profile contract | 7/7 PASS |
| Aggregate P14 | 295/295 PASS |

Focused command: `python -X utf8 -B apexforge/p14_11_managed_native_hybrid_package_artifacts_test.py`.
Requested P14.10–P14.1 regressions ran in descending order, followed by the non-compiling frozen P12.5 contract suite. Aggregate: `python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py`.
Observed aggregate elapsed 23.981s is engineering evidence only, not a benchmark/SLA.

Focused fixtures use existing AIR serialization and frozen canonical build bytes/fingerprint conventions. Native receipt/image fixtures model transport associations and deliberately are not executable images or authenticated backend-issued builds. Their PASS proves adapter integrity/identity behavior, not actual MSVC build success. Frozen native admission tests establish unchanged exact profile bounds without compilation or dispatch.

The suite checks byte/build tampering, duplicate JSON keys, schema/profile rejection, exact package binding, AIR fingerprint correspondence, hybrid identities, ambiguity/no fallback, payload sets/corruption, path safety, provenance/debug references, immutable results, lock nonmutation and a 1,000-descriptor deterministic set. Import/call guards prove separation. No inventory-sensitive historical harness or full P12/P13 execution suite was run.

## Truth markers

```text
P14_BASELINE=P13_12_FREEZE
P14_11_INCOMING_CANDIDATES=30
P13_REOPENED=False
P14_PACKAGE_ARTIFACT_PACKAGE_CONTENT_BOUND=True
P14_ARTIFACT_SEMANTIC_AUTHORITY=CANONICAL_AIR
P14_11_NATIVE_PROFILE_EXPANDED=False
P14_NATIVE_TARGET_INFERRED_FROM_FILENAME=False
P14_ARTIFACT_PACKAGING_MUTATES_LOCKFILE=False
P14_ARTIFACT_PACKAGING_PUBLISHES=False
P14_ARTIFACT_PACKAGING_AUTOMATIC_CACHE_INSERT=False
P14_ARTIFACT_SELECTION_GRANTS_AUTHORITY=False
P14_ARTIFACT_PACKAGING_COMPILES=False
P14_ARTIFACT_PACKAGING_EXECUTES=False
P14_WHOLE_LANGUAGE_MANAGED_NATIVE_EQUIVALENCE=False
P14_ARTIFACT_EXECUTES_AIR=False
P14_ARTIFACT_EXECUTES_RUNTIME=False
P14_ARTIFACT_INVOKES_COMPILER=False
P14_ARTIFACT_DISPATCHES_NATIVE=False
P14_ARTIFACT_GRANTS_AUTHORITY=False
P14_ARTIFACT_NETWORK_ACCESS=False
P14_ARTIFACT_FILESYSTEM_DISCOVERY=False
P14_ARTIFACT_HOST_COMMAND_EXECUTION=False
P14_ARTIFACT_INSTALLS_PACKAGES=False
P14_HYBRID_PRESERVES_VARIANT_IDENTITIES=True
P14_UNSUPPORTED_ARTIFACT_TARGET_FAILS_CLOSED=True
P14_ARTIFACT_PAYLOAD_INTEGRITY_REQUIRED=True
P14_ARTIFACT_IDENTITY_IMMUTABLE=True
P14_ARTIFACT_MANIFEST_CANONICALIZATION=DETERMINISTIC
P14_ARTIFACT_SELECTION_INPUT=EXPLICIT_TARGET_REQUIREMENT
CRYPTO_PROVIDER_UNAVAILABLE
P14_MANAGED_ARTIFACT_MODEL=PASS
P14_NATIVE_ARTIFACT_MODEL=PASS
P14_HYBRID_ARTIFACT_MODEL=PASS
P14_ARTIFACT_IDENTITY=PASS
P14_ARTIFACT_BUILD_BINDING=PASS
P14_ARTIFACT_PAYLOAD_INTEGRITY=PASS
P14_ARTIFACT_TARGET_BINDING=PASS
P14_ARTIFACT_SELECTION=PASS
P14_ARTIFACT_MANIFEST=PASS
P14_ARTIFACT_DETERMINISM=PASS
P14_ARTIFACT_PROVENANCE=PASS
P14_ARTIFACT_SECURITY_BOUNDARY=PASS
P14_10_REGRESSION=PASS
P14_9_REGRESSION=PASS
P14_8_REGRESSION=PASS
P14_7_REGRESSION=PASS
P14_6_REGRESSION=PASS
P14_5_REGRESSION=PASS
P14_4_REGRESSION=PASS
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
EVIDENCE_BEFORE_ATTRIBUTION=True
P14_AGGREGATE=295/295_PASS
P14_INCOMING_HASH_PRESERVATION=30/30_PASS
P14_CANDIDATE_COUNT=33
PATCH_MATRIX=PASS
P14_11_READY_FOR_REVIEW=True
```

## Exact final Git status

Tracked and staged diffs empty; nothing staged. All 30 incoming hashes preserved; no frozen file modification, generated residue or unauthorized scope expansion. Only three new P14.11 candidates. No P14.12 supply-chain validation, P14.13 closure/freeze, installation, runtime package execution or P15 begun.

`git status --short --untracked-files=all`:

```text
?? apexforge/p14_10_package_compatibility_migration_test.py
?? apexforge/p14_11_managed_native_hybrid_package_artifacts_test.py
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/p14_4_package_namespace_export_resolution_test.py
?? apexforge/p14_5_package_capability_contract_test.py
?? apexforge/p14_6_package_signing_integrity_provenance_trust_test.py
?? apexforge/p14_7_content_addressed_package_cache_test.py
?? apexforge/p14_8_registry_protocol_test.py
?? apexforge/p14_9_package_publishing_test.py
?? apexforge/tooling/package_artifacts.py
?? apexforge/tooling/package_cache.py
?? apexforge/tooling/package_capabilities.py
?? apexforge/tooling/package_compatibility.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_namespace.py
?? apexforge/tooling/package_publishing.py
?? apexforge/tooling/package_registry.py
?? apexforge/tooling/package_solver.py
?? apexforge/tooling/package_trust.py
?? docs/p14/P14_10_PACKAGE_COMPATIBILITY_MIGRATION.md
?? docs/p14/P14_11_MANAGED_NATIVE_HYBRID_PACKAGE_ARTIFACTS.md
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
?? docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md
?? docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md
?? docs/p14/P14_6_PACKAGE_SIGNING_INTEGRITY_PROVENANCE_TRUST.md
?? docs/p14/P14_7_CONTENT_ADDRESSED_PACKAGE_CACHE.md
?? docs/p14/P14_8_REGISTRY_PROTOCOL.md
?? docs/p14/P14_9_PACKAGE_PUBLISHING.md
```

Stop after P14.11 ready for owner review.

