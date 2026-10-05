# P15.2 Domain Interchange & Portable Contract Exchange

## Baseline and preservation

Branch: `p15-1-domain-platform-contract-sdk`.
HEAD / P14 freeze commit / peeled `afp-p14.13-freeze`: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
P14 annotated tag object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`.
Frozen P14 branch `p14-1-package-identity-manifest` remains at the same freeze commit.

Before implementation: exactly three incoming P15.1 candidates, empty tracked/staged diffs, no generated residue. Incoming SHA-256 values:

| Incoming candidate | SHA-256 |
|---|---|
| `apexforge/p15_1_domain_platform_contract_sdk_test.py` | `0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62` |
| `apexforge/tooling/domain_platform.py` | `3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3` |
| `docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md` | `F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A` |

All three incoming hashes preserved; no P15.1 owning defect or frozen P14 blocker. Only the new interchange module, focused test and this report are added, giving six candidates. No stage/commit/tag/push.

P14 package crypto remains CRYPTO_PROVIDER_UNAVAILABLE; no provider installed. P14 Git commit/tag remain UNSIGNED, a separate signing state.

## P15.1 dependency and field census

P15.1 remains the authoritative domain-contract model. P15.2 reconstructs its existing immutable constructors, not a second domain object hierarchy.

| P15.1 field group | Classification | Exchange treatment |
|---|---|---|
| Platform identity: schema, opaque ID, domain kind | INTERCHANGE_REQUIRED | Exact field set, existing identity/kind validation |
| Descriptor implementation coordinate/content, explicit contract version, operations | INTERCHANGE_REQUIRED | Both P14 identities retained; bounded version strings; declared operation membership |
| Descriptor capabilities/dependencies/provenance | INTERCHANGE_OPTIONAL; REFERENCE_ONLY for provenance | Optional semantic collections are always present as canonical arrays, empty when absent |
| Request descriptor and operation | INTERCHANGE_REQUIRED | Full exact descriptor, revision fingerprint in envelope, membership validation |
| Request semantic inputs, symbols, artifacts, capabilities, provenance | INTERCHANGE_OPTIONAL; REFERENCE_ONLY for evidence | Canonical arrays; existing typed identities reconstructed |
| Request correlation | INTERCHANGE_OPTIONAL | Required wire field with null when absent; caller-supplied value remains part of P15.1 request identity |
| Artifact producer, implementation, operation, digest, descriptor fingerprint, kind/schema | INTERCHANGE_REQUIRED | Exact identity/reference claims; bytes are not acquired |
| Artifact semantic inputs/symbols/provenance | INTERCHANGE_OPTIONAL; REFERENCE_ONLY | Existing P14 reference carriers, no semantic reinterpretation |
| Result request binding, platform/package/operation/input projections, status | INTERCHANGE_REQUIRED | Exact request support plus consistency checks on all projections |
| Result outputs/diagnostics/provenance | INTERCHANGE_OPTIONAL | Arrays; P15.1 incomplete/failed diagnostic and output rules apply |
| Canonical AIR authority and false authority/authentication boundary flags | INTERCHANGE_REQUIRED | Exact fixed values checked, not silently ignored |
| Host/transport/authentication metadata | NON_CANONICAL_METADATA | Not supported or inferred; no extension fields |

Every field in a P15.1 canonical record must appear in its wire record. Optional means optional semantic content, not silently omitted canonical fields. No presentation metadata extension mechanism was invented.

## Schema, envelope and supported kinds

Schema: `apexforge.domain-interchange/v1`, separate from domain SDK, package, AIR, artifact, registry, debugger and authority schemas.

Supported kinds: platform, request, result, artifact. Unknown envelope schemas/kinds fail closed before reconstruction. Embedded schemas are also checked by explicit P15.1/P14 constructors.

`DomainInterchangeEnvelope` is frozen and stores the reconstructed P15.1 document plus interchange schema. Its detached record contains exactly:

- schema;
- kind;
- payload (the complete P15.1 canonical record);
- payload_fingerprint (the original object's fingerprint);
- descriptor_fingerprint (the exact revision);
- support (the exact request record for results, null for other kinds).

Result support is necessary because P15.1 DomainResult owns a DomainRequest while its canonical result record carries only the request fingerprint and selected projections. Carrying the full request permits reconstruction without inventing or fetching evidence. Support participates in envelope identity; it must match the payload's request fingerprint. No extra request/platform model is introduced.

Public API: serialize_document(document) returns canonical bytes; parse_document(bytes) returns an immutable envelope whose document is the authoritative P15.1 object. Envelope canonical_bytes(), fingerprint() and record() provide bytes, separate envelope identity and detached data.

## Canonical JSON and strict parsing

Canonical bytes are UTF-8, sorted keys, compact separators, ASCII escapes, finite values and no newline/BOM. All supported declaration/reference arrays are semantically unordered and canonicalized through existing P15.1 ordering. Input whitespace/key order and unordered array permutation are accepted and normalize to identical bytes.

Parsing requires exact caller-supplied bytes, not text, paths, bytearray or arbitrary buffers. Strict UTF-8 decode rejects malformed bytes. JSON duplicate object members reject at every level, including duplicate keys expressed through Unicode escapes. Trailing documents, comments/permissive JSON, malformed escaping and BOM fail. Lone Unicode surrogates reject even in escaped keys or values. Canonical identifiers remain the frozen owners' bounded ASCII subsets; no Unicode normalization silently changes identity.

Every semantic object uses an exact field set: unknown and missing fields fail. No arbitrary extension/class/module names or ignored authority flags. Reconstruction uses explicit supported constructors and no eval/exec/pickle/dynamic import/input-supplied hooks. The internal duplicate-key JSON callback is fixed validation code, not an input-selected hook.

### Limits and numeric policy

| Limit | v1 value | Basis |
|---|---|---|
| Document bytes | 16 MiB | Existing bounded P14 registry/artifact document convention |
| JSON container depth | 64 | Above actual finite SDK nesting; lexical precheck before recursive JSON decode |
| Individual decoded string/key | 512 characters | Covers frozen package namespace (255), reference/schema limits (256), platform/operation (128), fingerprints (64) and version text (32) |
| Each array | 4,096 elements | Bounded exchange policy; demonstrated 1,000-record inputs |
| Total decoded nodes, including keys | 200,000 | Aggregate resource limit, iterative inspection |

No JSON numeric value is part of actual P15.1 canonical records: exact versions are strings and boundary flags are booleans. JSON integers/floats/exponents/NaN/Infinity reject deterministically at decoding, including excessively long numeric forms. Booleans do not substitute for integers or string versions; numeric zero cannot masquerade as false. Frozen ExactVersion parsing is reused, and maximum 2147483647.2147483647.2147483647 round-trips. No arbitrary integer cap was applied to legitimate version strings.

Limits are explicit interchange admission limits, not truncation or a change to P15.1 identity. Objects exceeding exchange limits fail serialization/admission rather than lose fields. Bounds are not hostile-process memory/durability or performance guarantees.

## Round trips and exact bindings

Platform: full identity/kind/schema, exact P14 coordinate/content, contract version, operations, typed capabilities, exact dependencies and provenance reconstruct. Recomputed descriptor fingerprint must equal the supplied envelope revision.

Request: full descriptor, operation, input/reference sets, capability membership, provenance/context and correlation reconstruct. Exact descriptor fingerprint remains distinct from request fingerprint. Undeclared operations fail through P15.1 before fingerprint acceptance; nothing executes.

Result: full support request reconstructs first. Payload request fingerprint must match. P15.1 validates output descriptor revision, exact platform/package/operation and input/symbol lineage. All redundant result projections and fixed boundary flags are checked against reconstructed result data. Same-coordinate alternate content or a different revision cannot substitute under unchanged bindings. COMPLETE remains caller-declared; declaration_only=true does not prove execution. INCOMPLETE and FAILED retain diagnostics and existing output restrictions.

Artifact: full producer, package binding, kind/schema, operation, digest, descriptor revision, input/symbol/provenance references reconstruct. Artifact fingerprint and raw content digest remain separate. A standalone artifact is a passive reference: absent descriptor evidence cannot establish declared operation membership, and absent bytes cannot establish digest integrity. P15.1 verify_bytes remains available for separately supplied bytes; exchange does not fetch them or invent descriptor evidence.

Every supported OBJECT -> canonical bytes -> parse -> OBJECT preserves equality, canonical record and original fingerprint. No P15.1 field needed for construction is discarded.

## Fingerprints and tamper boundary

Object identity remains P15.1-owned. Envelope fingerprint is SHA-256(interchange schema + NUL + canonical envelope bytes), uppercase hex. It is neither payload-object identity, descriptor identity, package content identity nor AIR fingerprint. There is no self-referential envelope hash field.

Parser checks supplied payload/descriptor fingerprints against reconstructed objects. Result support is checked against its request fingerprint, and all supplied projections must agree with that request. Canonical record comparison checks false/true boundary flags exactly and rejects semantic-authority replacement.

Tests reject tampering to schema/kind, malformed or changed platform/package identity, descriptor revision, operation membership, capability declarations, AIR/symbol reference data, artifact identity, provenance, result status/diagnostics and request support at the corresponding layer. Malformed reconstruction is rejected independently of fingerprints.

Fingerprints are integrity/continuity identifiers, not signatures. A coherently changed document with fully recomputed identities is new structurally valid passive evidence; this is explicitly tested. Authentication/expected identity must come from separate caller evidence, not parse success. Parsing never establishes trust or authorization.

## Capability, provenance and semantic boundaries

DomainCapability is reconstructed as the distinct P15.1 type; P14 package capability strings are not converted to domain privileges. Capability records and request/result/artifact boundary flags grant no authority. No AuthorityEngine invocation or runtime grant.

CanonicalReference/SymbolReference retain exact frozen schema/kind/fingerprint/module/current AIR ID. Domain artifacts remain distinct from package artifacts, source and AIR; invalid native/AIR/source masquerading fails the SDK owner. Canonical semantic authority remains CANONICAL_AIR. Exchange never expands, executes or changes semantic input.

Provenance references remain passive references. The result's authenticates_provenance=false flag is checked. No author, publisher, organization, ownership or external-provider semantic authority is inferred.

INTERCHANGE_DOCUMENT != DOMAIN_PLATFORM; INTERCHANGE_DOCUMENT != DOMAIN_REQUEST_AUTHORITY; INTERCHANGE_DOCUMENT != DOMAIN_RESULT_AUTHORITY; INTERCHANGE_DOCUMENT != PACKAGE; INTERCHANGE_DOCUMENT != CANONICAL_AIR; INTERCHANGE_SERIALIZATION != EXECUTION; INTERCHANGE_PARSE_SUCCESS != TRUST; INTERCHANGE_PARSE_SUCCESS != AUTHORIZATION; INTERCHANGE_PROVENANCE != REAL_WORLD_ATTRIBUTION; TRANSPORT != SEMANTIC_OWNER; EXTERNAL_FORMAT != CANONICAL_SEMANTIC_AUTHORITY; INTERCHANGE_FINGERPRINT != PAYLOAD_OBJECT_IDENTITY.

## Transport, filesystem and parser security

No HTTP/WebSocket/TCP/gRPC/message queue/cloud/file watcher/external API. Future adapters can carry these bytes without owning semantics. No filesystem reads/writes/discovery or environmental/host acquisition in production.

Production imports only dataclasses/hashlib/json/re and existing P15.1/P14 passive carriers. Static audit and dynamic traps verify no process/shell, network, file access, authority, registry query or solve. No AIR/RuntimeEngine/native execution, compilation, installation, domain dispatch, arbitrary class instantiation, pickle or module loading from input.

Package signing remains CRYPTO_PROVIDER_UNAVAILABLE. No crypto install/fake verification, trust grant, live network, domain-specific implementation, P15.3 or P15 freeze work.

## Diagnostics and Patch Matrix

DomainInterchangeError exposes a deterministic code with no supplied payload/exception prose. Interchange codes distinguish schema/kind, malformed/UTF-8, duplicate key, field set, fingerprint, request/descriptor/projection binding, string/number/limits and bytes-only input. Existing SDK diagnostic codes are preserved when its owner rejects kind/operation/capability/result identity; frozen package/reference failures translate to DOMAIN_INTERCHANGE_REFERENCE_OR_PACKAGE_INVALID.

Admission order is fixed by object field ownership. Unordered element reconstruction and iterative limit inspection use canonical order, so malformed set permutations cannot choose a different first error. Duplicate declarations reject; no override/deduplication to conceal invalid data.

Initial focused 39/39 PASS. Review exposed DOMAIN_INTERCHANGE_DETERMINISM_GAP: two differently malformed elements of an unordered reference array could choose first-error codes by input order. Classified before patch; owner P15.2; patch surface only new interchange module/test. Canonicalize admission order and add reversed-invalid-set diagnostic assertion. Focused 40/40 PASS, P15.1/P15/P14 regressions and native/authority checks PASS, preservation PASS. No frozen predecessor repair.

```text
DOMAIN_INTERCHANGE_DETERMINISM_GAP=CLOSED
PATCH_MATRIX=PASS
```

## Validation

| Command | Final result |
|---|---|
| python -X utf8 -B apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| python -X utf8 -B apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py | 70/70 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| python -X utf8 -B apexforge/authority_consolidation_smoke_test.py | PASS |

Final P15 aggregate observed 1.695s; P14 aggregate observed 26.945s. Engineering observations only, not benchmark certification/SLA. Authority smoke confirms wrong principal/capability/resource denial, authorized existing runtime fixture and transactional denied execution; SDK/interchange do not invoke runtime.

Scale fixture has 1,000 canonical references and 1,000 domain artifact references in a request. Forward/reversed construction yields identical canonical bytes and exact round trip. No recursion-dependent domain traversal or new benchmark milestone.

No assertion failed; the review correction did not weaken coverage. Fixture test module imported as a module alias, avoiding duplicate predecessor TestCase discovery.

## Final preservation and exact Git status

All three incoming P15.1 hashes preserved. Branch/HEAD/P14 branch/tag object/peeled target unchanged. Empty tracked/staged diffs across the whole repository demonstrate no frozen P14/P13/P12/P11/P10 edits. No tag movement/history rewrite, stage/commit/tag/push or generated residue. Exactly six intended candidates:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
```

## Required markers

```text
P15_BASELINE=P14_13_FREEZE
P15_2_INCOMING_CANDIDATES=3
P14_REOPENED=False
P15_DOMAIN_INTERCHANGE_UNKNOWN_SCHEMA_FAILS_CLOSED=True
P15_DOMAIN_INTERCHANGE_CANONICALIZATION=DETERMINISTIC
P15_DOMAIN_INTERCHANGE_ROUND_TRIP_IDENTITY=True
P15_INTERCHANGE_PRESERVES_EXACT_PACKAGE_BINDING=True
P15_INTERCHANGE_PRESERVES_DESCRIPTOR_REVISION=True
P15_INTERCHANGE_PRESERVES_CANONICAL_AIR_REFERENCE=True
P15_INTERCHANGE_REDEFINES_CORE_SEMANTICS=False
P15_INTERCHANGE_REQUEST_EXECUTES_OPERATION=False
P15_INTERCHANGE_RESULT_PROVES_EXECUTION=False
P15_INTERCHANGE_GRANTS_AUTHORITY=False
P15_INTERCHANGE_CAPABILITY_DECLARATION_IS_PERMISSION=False
P15_INTERCHANGE_REAL_WORLD_ATTRIBUTION=False
P15_INTERCHANGE_NETWORK_TRANSPORT_IMPLEMENTED=False
P15_INTERCHANGE_INPUT=CALLER_SUPPLIED_BYTES
P15_INTERCHANGE_FILESYSTEM_DISCOVERY=False
P15_INTERCHANGE_PARSED_MODELS_IMMUTABLE=True
P15_INTERCHANGE_EXECUTES_AIR=False
P15_INTERCHANGE_EXECUTES_RUNTIME=False
P15_INTERCHANGE_DISPATCHES_NATIVE=False
P15_INTERCHANGE_COMPILES=False
P15_INTERCHANGE_INSTALLS_PACKAGES=False
P15_INTERCHANGE_EXECUTES_DOMAIN_CODE=False
P15_INTERCHANGE_HOST_COMMAND_EXECUTION=False
P15_INTERCHANGE_PARSE_GRANTS_TRUST=False
CRYPTO_PROVIDER_UNAVAILABLE
EVIDENCE_BEFORE_ATTRIBUTION=True
P15_DOMAIN_INTERCHANGE_MODEL=PASS
P15_DOMAIN_INTERCHANGE_SCHEMA=PASS
P15_DOMAIN_INTERCHANGE_DESCRIPTOR_ROUNDTRIP=PASS
P15_DOMAIN_INTERCHANGE_REQUEST_ROUNDTRIP=PASS
P15_DOMAIN_INTERCHANGE_RESULT_ROUNDTRIP=PASS
P15_DOMAIN_INTERCHANGE_ARTIFACT_ROUNDTRIP=PASS
P15_DOMAIN_INTERCHANGE_PACKAGE_BINDING=PASS
P15_DOMAIN_INTERCHANGE_DESCRIPTOR_BINDING=PASS
P15_DOMAIN_INTERCHANGE_REFERENCE_PRESERVATION=PASS
P15_DOMAIN_INTERCHANGE_PROVENANCE=PASS
P15_DOMAIN_INTERCHANGE_DETERMINISM=PASS
P15_DOMAIN_INTERCHANGE_SECURITY_BOUNDARY=PASS
P15_1_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P15_AUTHORITY_COEXISTENCE=PASS
P14_FROZEN_PREDECESSOR_PRESERVED=True
P15_CANDIDATE_COUNT=6
P15_2_READY_FOR_REVIEW=True
```

Stop at P15.2 review readiness.
