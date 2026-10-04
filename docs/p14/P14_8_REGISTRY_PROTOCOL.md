# P14.8 — Registry Protocol & Immutable Package Discovery

Review evidence for a transport-independent protocol foundation. No publication or freeze operation.

## Baseline and incoming hashes

Branch `p14-1-package-identity-manifest`; HEAD and peeled `afp-p13.12-freeze`:
`860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

Exactly twenty-one incoming candidates, hashed before editing and confirmed unchanged after validation:

| Incoming file | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/p14_3_lockfile_reproducible_restore_test.py` | `F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F` |
| `apexforge/p14_4_package_namespace_export_resolution_test.py` | `BCE5A2A91310CED3FBDFC0A6B284CC2D5C017F63C662DF36E8C10502FBFC1C3F` |
| `apexforge/p14_5_package_capability_contract_test.py` | `B496B2159CBFF1F799281FB4184443A44D59561DD43BAFD770C41A9CBB5E6808` |
| `apexforge/p14_6_package_signing_integrity_provenance_trust_test.py` | `F209EEF357AF894881C399D9E857202AE1C6DC4706E2460E62657E9A6B0F2937` |
| `apexforge/p14_7_content_addressed_package_cache_test.py` | `0E795FF9B0D06EEB7AA3CF571F47C2A94D4AFBF185AA1395AD516D46C2503A4D` |
| `apexforge/tooling/package_cache.py` | `DAB89DE443965C1053FCA0189D697E9FD4861A088AC7FB053A3715F4194A025A` |
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
| `docs/p14/P14_7_CONTENT_ADDRESSED_PACKAGE_CACHE.md` | `52477C3097AE023A3A59ABF2A76B1D793B3C9DAA8CBDFC78E168BE0FCE190898` |

## Protocol census

| Existing facility | Classification | Treatment |
|---|---|---|
| P13 debug_dap.py request/errors/strict duplicate-key JSON/canonical encoding | REFERENCE_ONLY; FROZEN_PROTOCOL_CONTRACT | Inspect conventions; do not import, alter or overload DAP. |
| P14.1 manifest parsing and canonical identity | REUSE | Existing schema, field validation and content commitments unchanged. |
| P14.2 ResolvedPackage/PackageUniverse | REUSE | Canonical record and explicit candidate admission, never solve(). |
| P14.3 lock | REUSE | Exact admitted identities, immutable association. |
| P14.6 envelope and supplied integrity | REUSE | Passive signature shape and explicit byte verification boundary. |
| P14.7 cache | REFERENCE_ONLY | Tests prove explicit caller-controlled insertion; registry does not import cache. |
| Strict bounded parsing and canonical JSON pattern | ADAPT | New registry-envelope owner, no frozen helper refactor. |

No suitable package-network transport was established by this census. The reference service is in-memory and read-only. No HTTP/socket/daemon, registry persistence or fake network support.

## Schema, transport and request contract

Protocol schema `apexforge.registry/v1`, separate from manifest/package versions, lock/cache/signature schemas.

Flow: RegistryRequest -> supplied immutable RegistryCatalog.query -> RegistryResponse. Five operations:
- coordinate: exact PackageCoordinate selector.
- content: exact PackageContentIdentity selector.
- versions: validated exact namespace/name selector.
- blob: exact uppercase SHA-256 digest selector.
- catalog: empty selector, full supplied catalog.

All models are frozen. Unknown schema/operation, extra semantic fields, contradictory selectors, malformed coordinates/keys and duplicate JSON keys reject. No latest/preferred/range semantics. There is no correlation token, random ID or registry URL/organization identity; none is needed for this in-process seam.

Raw envelope JSON is bounded to 16 MiB, duplicate/nonfinite/oversized-integer/invalid-Unicode/deep-JSON safeguards follow prior conventions. Nested canonical manifests use P14.1's own 1 MiB parser bound. Parsed input is validated before becoming a request/model. Unknown semantic fields are not discarded.

## Catalog and package records

RegistryRecord holds canonical metadata-stripped PackageManifest and optional passive SignatureEnvelope. It serializes exact coordinate, exact content identity, original canonical manifest, optional envelope, and NOT_VERIFIED or UNSIGNED status. Manifest fingerprint is the existing P14.1 content identity; no second package identity is minted.

Parsing validates manifest schema/fields, recomputes content identity, checks coordinate/content associations and canonical record equality. Registry cannot rewrite capabilities, exports, content descriptors or provenance unnoticed. Non-identity presentation metadata is excluded from this canonical discovery protocol.

RegistryCatalog takes only explicitly supplied record/blob tuples. Identical duplicates deduplicate; conflicting passive records under the same content identity fail closed rather than selecting an envelope by order. Same coordinate with different content identities remains allowed and distinct. Indexes are immutable MappingProxyType maps with tuple values for exact content, coordinate, version family and blob lookup.

Registry ID/URL is not represented; if later supplied it must remain operational, not a trust anchor or namespace/organization identity.

## Coordinate/content lookup and version discovery

Coordinate query returns PACKAGE_NOT_FOUND, one OK exact record, or AMBIGUOUS_COORDINATE plus all distinct supported records in deterministic order. Ambiguity remains an error, not a selected package. Input permutation cannot change candidates or code.

Content query is keyed by the exact existing PackageContentIdentity and returns one exact record or CONTENT_NOT_FOUND. No coordinate substitution.

Versions query returns informational exact versions sorted by numeric components, not precedence selection, latest, recommended or preferred. Versions are deduplicated even when multiple contents share a coordinate/version.

## Responses and client association

RegistryResponse contains operation, deterministic code/status, immutable records, versions and optional blob. Constructor validates payload shape: exact lookup success requires one record; ambiguity requires multiple records at one coordinate; versions/catalog/blob have distinct payload shapes; ordinary errors contain no success payload. Schema/status, duplicate identities, nested record/signature/blob fields and canonical encodings are validated on parse.

validate_response(request,response) separately checks operation association and exact coordinate/content/blob selector binding. A valid record for another query cannot be admitted as the requested content merely because it is internally consistent. Version responses are informational under the paired request; no package is selected.

Malformed request/response errors use fixed RegistryError.code, without arbitrary exception text or input echo. Codes include INVALID_REQUEST, UNSUPPORTED_PROTOCOL_VERSION, UNKNOWN_OPERATION, PACKAGE_NOT_FOUND, CONTENT_NOT_FOUND, BLOB_NOT_FOUND, AMBIGUOUS_COORDINATE, REGISTRY_RECORD_INVALID, CONTENT_IDENTITY_MISMATCH, BLOB_DIGEST_MISMATCH and RESPONSE_SCHEMA_INVALID. Invalid envelopes reject before service querying; adapters may later map these codes into a transport error envelope without changing their identity.

## Candidate snapshots and solver separation

RegistryCandidateSnapshot is an immutable canonical ordered record set with protocol/schema association. Canonical JSON retains exact coordinate/content/provenance/passive envelopes. Fingerprint domain `apexforge.registry-snapshot/v1` hashes domain, NUL and JSON UTF-8; it is observed candidate evidence, not registry trust/live identity.

snapshot() returns supplied catalog candidates. Caller explicitly invokes to_universe() to construct P14.2's validated PackageUniverse. This is not solve(). Divergent content at one coordinate remains representable in the snapshot and still fails P14.2's content-conflict gate on universe conversion. No preferred candidate or hidden dependency closure.

Exact lookup indexes avoid repeated full-catalog scans. Catalog construction sorts/indexes once; query dictionary lookups are bounded by result size. Full snapshot/version/catalog serialization still scales with represented records.

## Blob retrieval and integrity boundary

RegistryBlob stores caller-supplied digest and immutable bytes; constructor and response parsing recompute SHA-256, rejecting mismatched bytes. Blobs serialize canonical lowercase hex with uppercase raw-byte digest. Different digest meaning is preserved from package content/lock/payload/key domains.

Reference-service returned blobs have been checked as raw blobs; that is not package acceptance or trust. The caller must still check exact package member set/descriptors with P14.6 supplied-content integrity before use/cache insertion. No arbitrary path selector, filesystem discovery or source read.

## Cache and lock boundaries

Registry module has no cache dependency or automatic put. A test queries record/blob while PackageCache.put is patched to throw; the cache root stays empty. Caller then independently constructs ContentMember, verifies integrity and explicitly calls cache.put. Registry fetch != cache insertion.

locked_records(lock) resolves each exact locked content identity from this catalog and confirms full canonical ResolvedPackage equality. Absent exact content returns CONTENT_NOT_FOUND, including when same-coordinate alternatives exist. No lock mutation, solver, version selection, restore execution or installation.

## Trust, signature, provenance and namespace separation

Optional envelopes are passive records only. Parsing preserves P14.6 schema/algorithm/hex shape; no signing/verification occurs. NOT_VERIFIED is never rewritten to cryptographic VALID. The focused suite confirms installed cryptography/PyNaCl/Sigstore remain absent and supplied registry envelopes still return CRYPTO_PROVIDER_UNAVAILABLE through P14.6.

No trusted, official, verified_owner or ownership fields exist. No trust anchor, publisher authentication, namespace ownership or runtime authority is inferred from catalog membership, serving host, package namespace or registry location.

Provenance remains canonical package references; serving a package does not establish its origin, author or historical truth. EVIDENCE_BEFORE_ATTRIBUTION=True. Package namespaces remain coordinate strings distinct from organization identity.

REGISTRY != TRUST_AUTHORITY; REGISTRY != PACKAGE_AUTHORITY; REGISTRY != ORGANIZATION; REGISTRY != NAMESPACE_OWNER; REGISTRY_RECORD != PACKAGE_IDENTITY; REGISTRY_COORDINATE != CONTENT_IDENTITY; REGISTRY_DISCOVERY != DEPENDENCY_RESOLUTION; REGISTRY_QUERY != SOLVER_SELECTION; REGISTRY_FETCH != INSTALLATION; REGISTRY_FETCH != CACHE_INSERTION; REGISTRY_AVAILABILITY != TRUST; REGISTRY_AVAILABILITY != AUTHORIZATION; REGISTRY_METADATA != PROVENANCE_PROOF; REGISTRY_RESPONSE != SIGNATURE_VERIFICATION; DOWNLOAD_SOURCE != PACKAGE_ORIGIN.

## Determinism, scale and security

Requests normalize selectors to canonical records. Responses sort unordered records by namespace/name/numeric version/schema/content fingerprint; versions sort numerically. Compact sorted-key ASCII-safe UTF-8 JSON has no line endings, timestamps, machine data, host paths or object repr. Equivalent independent catalogs and permutations produce equal responses/snapshots/fingerprints.

A 1,000-record catalog demonstrates independent forward/reversed construction, exact lookup, full catalog response and validated serialization roundtrip. Pagination is deferred; the current bounded model does not promise arbitrary catalog-size transport. No registry mutable state or publication APIs.

AST/import audit excludes subprocess/shell, network/socket/HTTP, host filesystem, dynamic payload import, AIR/runtime/native execution, AuthorityEngine, cache put, signing-key persistence, install, publish and delete calls. Queries preserve manifests, catalog/maps, graph, lock, and cache.

## Validation and Patch Matrix

| Suite | Final result |
|---|---|
| P14.8 protocol | 22/22 PASS |
| P14.7 cache | 25/25 PASS |
| P14.6 integrity/trust boundary | 19/19 PASS |
| P14.5 capability | 23/23 PASS |
| P14.4 namespace/export | 23/23 PASS |
| P14.3 lock/restore | 28/28 PASS |
| P14.2 solver | 38/38 PASS |
| P14.1 manifest | 36/36 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 214/214 PASS |

Initial focused suite passed 21/21. Subsequent contract review identified missing client-side exact request/response association.
CLASSIFICATION: REGISTRY_RESPONSE_VALIDATION_GAP.
OWNER: P14.8 protocol.
PATCH SURFACE: new package_registry.py and its new test only.
FROZEN DEPENDENCIES: P14.1–P14.7 and P10–P13 unchanged.
LOCAL CONTRACT: valid foreign response cannot satisfy exact coordinate/content/blob selector.
SECTION REGRESSION: 22/22 PASS after added validator/test.
DEPENDENCY/CROSS-SECTION/AGGREGATE: all required predecessors and 214/214 aggregate PASS, including cache and lock integration.
PRESERVATION: all twenty-one hashes unchanged; expected lineage; no residue.
PATCH_MATRIX=PASS. No test failures occurred.

No older frozen protocol suites were rerun because frozen/shared modules were untouched.

## Deferrals and limitations

No live transport, pagination, publication, deletion, yanking, unlisting, authenticated publisher, namespace transfer/ownership, migration, managed/native packaging, supply-chain closure, installation or execution. No P14.9/P15 work.

Asymmetric verification remains unavailable. Snapshot is candidate evidence, not selected solution or universal integrity/trust proof. Blobs/catalog are trusted fixture inputs validated structurally/integrity-wise; no remote authentication/authorization seam is established here.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P14_8_INCOMING_CANDIDATES=21
P13_REOPENED=False
P14_REGISTRY_PROTOCOL_VERSIONED=True
P14_REGISTRY_PROTOCOL_CANONICALIZATION=DETERMINISTIC
P14_REGISTRY_REFERENCE_SERVICE=READ_ONLY
P14_REGISTRY_COORDINATE_AMBIGUITY_FAILS_CLOSED=True
P14_REGISTRY_VERSION_SELECTION_IMPLEMENTED=False
P14_REGISTRY_INVOKES_DEPENDENCY_SOLVER=False
P14_REGISTRY_AUTOMATIC_CACHE_INSERT=False
P14_REGISTRY_LOCK_SUBSTITUTION=False
P14_REGISTRY_PUBLICATION_IMPLEMENTED=False
P14_REGISTRY_DELETE_IMPLEMENTED=False
P14_REGISTRY_NAMESPACE_OWNERSHIP_IMPLEMENTED=False
P14_REGISTRY_EXECUTES_AIR=False
P14_REGISTRY_EXECUTES_RUNTIME=False
P14_REGISTRY_DISPATCHES_NATIVE=False
P14_REGISTRY_GRANTS_AUTHORITY=False
P14_REGISTRY_HOST_COMMAND_EXECUTION=False
P14_REGISTRY_INSTALLS_PACKAGES=False
P14_REGISTRY_EXECUTES_PACKAGE_CONTENT=False
CRYPTO_PROVIDER_UNAVAILABLE
P14_REGISTRY_NETWORK_TRANSPORT_IMPLEMENTED=False
P14_REGISTRY_PAGINATION_IMPLEMENTED=False
P14_REGISTRY_PROTOCOL_MODEL=PASS
P14_REGISTRY_REQUEST_VALIDATION=PASS
P14_REGISTRY_RESPONSE_MODEL=PASS
P14_REGISTRY_COORDINATE_LOOKUP=PASS
P14_REGISTRY_CONTENT_LOOKUP=PASS
P14_REGISTRY_COORDINATE_AMBIGUITY=PASS
P14_REGISTRY_VERSION_LISTING=PASS
P14_REGISTRY_BLOB_RETRIEVAL=PASS
P14_REGISTRY_CANDIDATE_SNAPSHOT=PASS
P14_REGISTRY_LOCK_BINDING=PASS
P14_REGISTRY_CACHE_BOUNDARY=PASS
P14_REGISTRY_TRUST_BOUNDARY=PASS
P14_REGISTRY_PROVENANCE_BOUNDARY=PASS
P14_REGISTRY_NAMESPACE_BOUNDARY=PASS
P14_REGISTRY_DETERMINISM=PASS
P14_REGISTRY_SECURITY_BOUNDARY=PASS
P14_7_REGRESSION=PASS
P14_6_REGRESSION=PASS
P14_5_REGRESSION=PASS
P14_4_REGRESSION=PASS
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
PATCH_MATRIX=PASS
P14_8_READY_FOR_REVIEW=True
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
?? apexforge/p14_8_registry_protocol_test.py
?? apexforge/tooling/package_cache.py
?? apexforge/tooling/package_capabilities.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_namespace.py
?? apexforge/tooling/package_registry.py
?? apexforge/tooling/package_solver.py
?? apexforge/tooling/package_trust.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
?? docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md
?? docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md
?? docs/p14/P14_6_PACKAGE_SIGNING_INTEGRITY_PROVENANCE_TRUST.md
?? docs/p14/P14_7_CONTENT_ADDRESSED_PACKAGE_CACHE.md
?? docs/p14/P14_8_REGISTRY_PROTOCOL.md
```

Exactly twenty-four candidates, three new. Expected branch, HEAD, tag object and peeled target unchanged. All twenty-one incoming hashes preserved. Tracked/cached diffs empty, confirming no frozen P10/P11/P12/P13 changes. No Python caches/bytecode, executable/library/symbol/object/VSIX artifacts or p147/p148 temporary roots remain. Nothing staged; no commit/tag/push. Stop at P14.8 review readiness.

