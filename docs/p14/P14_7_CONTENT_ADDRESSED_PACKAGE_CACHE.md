# P14.7 — Deterministic Content-Addressed Package Cache

Review evidence; no registry, installer or freeze operation.

## Baseline and incoming hashes

Branch `p14-1-package-identity-manifest`; HEAD and peeled `afp-p13.12-freeze`:
`860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

Eighteen incoming SHA-256 hashes captured before editing and compared unchanged after regressions:

| Incoming candidate | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/p14_3_lockfile_reproducible_restore_test.py` | `F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F` |
| `apexforge/p14_4_package_namespace_export_resolution_test.py` | `BCE5A2A91310CED3FBDFC0A6B284CC2D5C017F63C662DF36E8C10502FBFC1C3F` |
| `apexforge/p14_5_package_capability_contract_test.py` | `B496B2159CBFF1F799281FB4184443A44D59561DD43BAFD770C41A9CBB5E6808` |
| `apexforge/p14_6_package_signing_integrity_provenance_trust_test.py` | `F209EEF357AF894881C399D9E857202AE1C6DC4706E2460E62657E9A6B0F2937` |
| `apexforge/tooling/package_capabilities.py` | `F2B7A04640BB35362DACB18F600995EC225AE7B7FD423C9FFA18975A00CBFAF9` |
| `apexforge/tooling/package_lock.py` | `D9AA13C73B92A1F5FA4A0DDEE365A8978484F694B0E5DD3A42AC0892FB726E94` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `apexforge/tooling/package_namespace.py` | `57B6D3C8BB005D50E640E170525ACEC14C82134E1662AD5932F9BA0B66E42C05` |
| `apexforge/tooling/package_solver.py` | `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1` |
| `apexforge/tooling/package_trust.py` | `34445F195299756173690246E581664B7DF1D02EA432975EC90D2E3E28884FF7` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |
| `docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md` | `CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B` |
| `docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md` | `7490A98A1C14EB975FCB51A6FB612E3D50A080FFD7A77BEF86B2548DD48E4FDE` |
| `docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md` | `9E5DF5321AF33ADD30DA28BE896C5F81DE1A431509042C6AF0F4E1BE8848C63B` |
| `docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md` | `6BCC55F9A1FDC09E7F7EFA96A1F7ADC78FBE785F9A8E554A0D315598FCB8043D` |
| `docs/p14/P14_6_PACKAGE_SIGNING_INTEGRITY_PROVENANCE_TRUST.md` | `3985CB4940AD7150005DA5F9EC4864ABE366BB07386176D9E6358A4F039594BF` |

## Storage census and architecture

| Facility | Classification | Decision |
|---|---|---|
| tooling/build_artifact.py atomic temporary-sibling writer | ADAPT; FROZEN_PREDECESSOR | Reuse flush/close/fsync/temp cleanup pattern conceptually. Do not call its replacing artifact writer or change it. |
| tooling/narrative_session.py atomic session writer | REFERENCE_ONLY; FROZEN_PREDECESSOR | Same local temporary-publication convention. |
| tooling/resource_observability.py resource classifications and link/reparse checks | REFERENCE_ONLY; FROZEN_PREDECESSOR | Preserve caller ownership, bounded lifetime, trusted quiescent filesystem qualification. |
| tooling/trace_retention.py retained evidence identities | REFERENCE_ONLY | Retention and provenance do not make local storage semantic authority or trust. |
| P14.1 content identity, members, strict parsing | REUSE | Exact package key and canonical manifest schema; no new package identity. |
| P14.2 ResolvedPackage / PackageUniverse | REUSE | Canonical metadata stripping and explicit identity universe. |
| P14.3 plan_restore / lock | REUSE | Exact verified cache contents produce existing restore plan, no re-solving. |
| P14.6 supplied-byte integrity | REUSE | Insertion and returned entries require actual supplied-content verification. |

Two-layer local CAS: raw member blobs are keyed by SHA-256 bytes; canonical package records are keyed by exact P14.1 content identity. Logical package member paths are descriptor metadata and never joined as storage paths.

## Explicit root and deterministic layout

Caller supplies an existing absolute cache directory. Relative, missing or traversal-bearing roots reject. No environment/user-profile/CWD/registry inference or package search. P14.7 only creates internal directories under that root.

Relative paths:
- blobs/sha256/<first-two-hex>/<uppercase-member-digest>
- packages/<first-two-hex>/<uppercase-package-fingerprint>/record.json

Fixed names and revalidated uppercase digest keys define every authoritative object location. Namespace/name/version do not become filesystem identity. Keys are not untrusted manifest path strings. Internal directories and files are checked using lstat; non-directory ancestors, non-regular object files, links and Windows reparse attributes reject. The explicitly supplied root is also checked as a regular directory.

This is a trusted/quiescent-root contract, matching frozen resource tooling. Checks do not defend against hostile simultaneous ancestor/reparse swaps, externally inserted hard links or a hostile privileged writer. No general filesystem sandbox or OS locking claim.

## Cache record and root independence

Schema `apexforge.package-cache-record/v1`.
The record stores exact package content identity and canonical manifest. That canonical manifest already includes coordinate, ordered member paths/digests/kinds/references and provenance; no redundant invented manifest identity hash is added. Human metadata is removed via ResolvedPackage. No timestamp, username, hostname, absolute original/cache root or usage metadata enters canonical JSON.

CacheEntry is an immutable manifest plus verified tuple members, ordered by logical path. Canonical serialization uses ASCII escaping, sorted keys, compact separators and finite values. Record fingerprint hashes schema/domain, NUL and canonical UTF-8 JSON with SHA-256. CACHE_RECORD_FINGERPRINT != PACKAGE_CONTENT_IDENTITY; package authoritative key remains the existing P14.1 identity.

Two distinct temporary roots produce equal canonical record/fingerprint. Physical roots differ without changing package identity or provenance.

## Integrity-gated insertion and immutable entries

put(manifest,members) constructs a verified CacheEntry before filesystem mutation. Missing, extra and changed bytes reject under P14.6 exact supplied-content rules. Every member's SHA-256 must match its descriptor.

Missing blobs publish first. Existing blobs must be regular and byte-identical; mismatches are corruption, never overwrite. Package record publishes last. Existing package records must be byte-identical canonical records, not merely coordinate-compatible. Successful insertion calls get for full read re-verification before returning.

Idempotent duplicate inserts reuse immutable objects. Same coordinate with different package content safely occupies separate digest keys. The solver's universe content-conflict rule is unchanged. Two distinct package identities with identical member bytes share one raw blob; blob deduplication does not collapse package identity.

Coordinate-only lookup is deferred. No latest/lexical-first/ambiguous coordinate selection is implemented.

## Atomicity, concurrency and lifecycle

Publication writes a random temporary sibling entirely under the cache root, flushes and fsyncs its file, closes it, then os.link atomically creates the final name if absent. Hard-link publication intentionally avoids replacing an existing authoritative key. If another writer wins, existing exact bytes are checked. Temporary name is unlinked in finally.

Tested on the current Windows filesystem: eight identical inserts with four threads succeed idempotently, with no temporary residue. Injected blob-publication and record-publication failures leave no authoritative package record. Record failure may leave verified orphan blobs/directories; these are not valid package entries. A subsequent insertion can reuse them. No GC is implemented.

P14_CACHE_PARTIAL_ENTRY_VISIBLE=False means no progressively written final package record becomes a successful read. An incomplete package directory can yield CACHE_RECORD_MISSING; it is not hidden as a successful entry.

Bounded atomic-create-if-absent publication is demonstrated. No cross-process locks, whole-package multi-process transaction, hostile-writer race protection or power-loss/directory-fsync durability guarantee. Filesystems lacking hard-link publication fail with CACHE_IO_ERROR rather than unsafe overwrite fallback.

Opened streams close before publication; temporary files clean up on tested failure/success paths. Caller owns root and cache lifetime. Tests use repository-contained TemporaryDirectory roots and release them, including large member/package fixtures. No new resource manager, eviction, age policy, LRU, disk heuristics or deletion API.

## Authoritative reads and corruption diagnostics

get accepts an exact PackageContentIdentity, not a coordinate/path. It revalidates digest syntax/domain, derives exact paths, strictly parses cache schema and duplicate JSON keys, and validates the nested manifest through P14.1 parse_manifest. Unknown/malformed/noncanonical records fail. The stored/recomputed package identity must equal the requested key. The full serialized record must equal canonical bytes.

All referenced blobs must exist, be regular and recompute to the descriptor digest. Returned CacheEntry also runs P14.6 integrity validation. Filename alone is never evidence of valid bytes.

Diagnostics include:
- CACHE_MISS: no required package path.
- CACHE_RECORD_MISSING: package directory exists without its record.
- CACHE_RECORD_INVALID: malformed/unsupported/noncanonical record.
- CACHE_PACKAGE_IDENTITY_MISMATCH: record or canonical manifest differs from key.
- CACHE_BLOB_MISSING / CACHE_BLOB_DIGEST_MISMATCH.
- CACHE_RECORD_EXISTING_MISMATCH: attempted overwrite under an existing key.
- CACHE_COORDINATE_MISMATCH / CACHE_RESTORE_VIEW_INVALID for lock associations.
- CACHE_PATH_NOT_REGULAR, CACHE_IO_ERROR and input/root/key errors.

Diagnostics use fixed codes without absolute-path/object-repr identity. Absence and corruption stay distinct. Outer records are limited to 16 MiB after reading; nested manifest parsing retains P14.1's 1 MiB input limit. This slice is not an untrusted hostile-large-file resource-limiting framework.

## Exact lock lookup and restore view

restore_view reads every locked node by exact content identity, rechecks blobs/record, verifies coordinate and complete canonical ResolvedPackage equality, then passes only those supplied manifests to P14.3 plan_restore. No solve/version selection, registry or filesystem package discovery. A cached same-coordinate alternative cannot satisfy a missing exact locked key.

CachedRestoreView is immutable, holds lock, exact ordered entries and the existing RestorePlan. Its canonical form delegates to that plan and has installs_packages=false. Constructor checks exact lock node sequence. No project/runtime materialization. Cache root is absent from restore identity.

## Provenance, trust, capability and namespace boundaries

Provenance references survive canonical retrieval; no download URL, registry publisher or actor identity is added. Cache location/presence is not provenance proof.

P14.6 CRYPTO_PROVIDER_UNAVAILABLE remains unchanged: the focused test confirms cryptography/PyNaCl/Sigstore remain absent, and a cached envelope still returns unavailable, accepted=None without a policy, and grants_runtime_authority=false. No dependencies or key store changed. The cache record does not attach or upgrade verification evidence; it preserves canonical package inputs only.

Capability-required declarations remain intact and can still be incompatible after caching. Symbol references remain exact AIR/module identities and P14.4 provider content remains unchanged. No cache hit satisfies compatibility, authority or trust by itself.

CACHE_HIT != TRUST; CACHE_HIT != AUTHORIZATION; CACHE_HIT != INSTALLATION; CACHE_HIT != DEPENDENCY_RESOLUTION; CACHE_PATH != PACKAGE_IDENTITY; CACHE_LOCATION != PROVENANCE; CONTENT_PRESENT != CONTENT_TRUSTED; CONTENT_PRESENT != LOCK_MATCH; BLOB_DIGEST != PACKAGE_COORDINATE; LOCAL_CACHE != TRUST_ANCHOR; CACHE_RESTORE_VIEW != INSTALLATION.

## Security audit

Filesystem IO is the authorized P14.7 exception, restricted to supplied root and digest-derived internal paths. No arbitrary scanning, host source access, subprocess/shell, AIR/runtime/native execution, AuthorityEngine, dynamic cached payload import, network/registry, installation or private-key persistence. Static audit checks prohibited imports/calls; filesystem primitives are deliberately allowed.

## Validation

| Suite | Result |
|---|---|
| P14.7 cache focused | 25/25 PASS |
| P14.6 | 19/19 PASS |
| P14.5 | 23/23 PASS |
| P14.4 | 23/23 PASS |
| P14.3 | 28/28 PASS |
| P14.2 | 38/38 PASS |
| P14.1 | 36/36 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 192/192 PASS |

Focused tests cover explicit-root validation, exact put/get, pre-write integrity gate, digest layout, root-independent canonical state, idempotence/dedup, coordinate divergence, immutable-key mismatch, miss/missing/corrupt objects, strict JSON/canonical records, identity tampering, traversal/key rejection, non-regular objects, exact lock/no-solver restore, failure atomicity/cleanup, four-thread duplicate insertion, preserved crypto gap, provenance/capability/export identity, 300-member and 100-package sets, temporary-root cleanup and static security.

No test failure or Patch Matrix repair was needed. No frozen/shared module changed, so no broad frozen regression was run.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P14_7_INCOMING_CANDIDATES=18
P13_REOPENED=False
P14_CACHE_ROOT=EXPLICIT_CALLER_SUPPLIED_PATH
P14_CACHE_PACKAGE_KEY=P14_PACKAGE_CONTENT_IDENTITY
P14_CACHE_INSERT_REQUIRES_CONTENT_INTEGRITY=True
P14_CACHE_READ_REVERIFIES_CONTENT=True
P14_CACHE_ENTRY_IMMUTABLE=True
P14_CACHE_EXISTING_KEY_MISMATCH_FAILS_CLOSED=True
P14_CACHE_SUPPORTS_COORDINATE_CONTENT_DIVERGENCE=True
P14_CACHE_LOCK_LOOKUP_EXACT=True
P14_CACHE_LOCK_LOOKUP_RESOLVES_DEPENDENCIES=False
P14_CACHE_CANONICAL_STATE_ROOT_INDEPENDENT=True
P14_CACHE_INSTALLS_PACKAGES=False
P14_CACHE_EXECUTES_PACKAGE_CONTENT=False
P14_CACHE_EVICTION_IMPLEMENTED=False
P14_CACHE_GARBAGE_COLLECTION_IMPLEMENTED=False
P14_CACHE_USAGE_METADATA_IMPLEMENTED=False
P14_CACHE_ARBITRARY_FILESYSTEM_DISCOVERY=False
P14_CACHE_EXECUTES_AIR=False
P14_CACHE_EXECUTES_RUNTIME=False
P14_CACHE_DISPATCHES_NATIVE=False
P14_CACHE_GRANTS_AUTHORITY=False
P14_CACHE_NETWORK_ACCESS=False
P14_CACHE_REGISTRY_ACCESS=False
P14_CACHE_HOST_COMMAND_EXECUTION=False
P14_CACHE_PARTIAL_ENTRY_VISIBLE=False
P14_CACHE_CROSS_PROCESS_LOCKING_IMPLEMENTED=False
CACHE_PRESERVES_PROVENANCE_REFERENCE=True
CRYPTO_PROVIDER_UNAVAILABLE
P14_CACHE_MODEL=PASS
P14_CACHE_CONTENT_ADDRESSING=PASS
P14_CACHE_BLOB_INTEGRITY=PASS
P14_CACHE_PACKAGE_RECORD=PASS
P14_CACHE_INSERTION=PASS
P14_CACHE_ATOMICITY=BOUNDED_ATOMIC_CREATE_IF_ABSENT_PUBLICATION_PASS
P14_CACHE_CORRUPTION_DETECTION=PASS
P14_CACHE_DEDUPLICATION=PASS
P14_CACHE_COORDINATE_DIVERGENCE=PASS
P14_CACHE_LOCK_BINDING=PASS
P14_CACHE_RESTORE_VIEW=PASS
P14_CACHE_PATH_BOUNDARY=PASS
P14_CACHE_RESOURCE_LIFECYCLE=PASS
P14_CACHE_DETERMINISM=PASS
P14_CACHE_SECURITY_BOUNDARY=PASS
P14_6_REGRESSION=PASS
P14_5_REGRESSION=PASS
P14_4_REGRESSION=PASS
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
P14_7_READY_FOR_REVIEW=True
```

## Exact Git status and preservation

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/p14_4_package_namespace_export_resolution_test.py
?? apexforge/p14_5_package_capability_contract_test.py
?? apexforge/p14_6_package_signing_integrity_provenance_trust_test.py
?? apexforge/p14_7_content_addressed_package_cache_test.py
?? apexforge/tooling/package_cache.py
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
?? docs/p14/P14_7_CONTENT_ADDRESSED_PACKAGE_CACHE.md
```

Exactly twenty-one candidates, three new. All eighteen incoming hashes preserved. Branch/HEAD/freeze object/peeled target unchanged. Empty tracked/cached diffs confirm no frozen P10/P11/P12/P13 changes. No Python caches/bytecode, executable/library/symbol/object/VSIX artifacts or p147 temporary roots remain. Nothing staged; no commit/tag/push.

No P14.8 registry, P14.9 publishing, migration, installation, execution or P15. Stop at P14.7 review readiness.

