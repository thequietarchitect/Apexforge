# P14.1 — Package Identity, Manifest and Canonical Package Contract

Status: **ready for owner review**. This report describes a bounded library contract, not package installation, registry operation, trust or execution. The owner retains final authority; no milestone release/freeze is declared.

## Frozen baseline and branch

The predecessor worktree was clean before branching, with no generated residue. The verified P13 annotated tag object is `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`; `afp-p13.12-freeze` peels to `860ba9287ee237ddca0691355607c896f3ea382f`. The new branch `p14-1-package-identity-manifest` was created directly from that tag and HEAD remains exactly that commit. The owner's active P14.1 assignment supersedes the stale P11.4A stage in AGENTS.md, while its stable authority/security policies remain binding.

The minimum candidate set is three new files:

1. `apexforge/tooling/package_manifest.py`
2. `apexforge/p14_1_package_identity_manifest_contract_test.py`
3. This evidence document.

No earlier file is modified. No schema/example file, package-manager CLI, project-loader integration, archive utility or new package-directory framework is needed. The external JSON example below is embedded here rather than adding another artifact.

## Repository census and continuity decision

Repository discovery covered package/manifest/version/namespace/dependency/export/capability/provenance/content-hash concepts, P11.13 evidence and tests, rich-document model/parser/project builds, project loaders, native receipts/mappings, CLI descriptors, and frozen IDE manifests. These concepts have different owners and must not be silently merged.

| Existing concept / owner | Classification | P14.1 decision |
| --- | --- | --- |
| `rich_documents.model.PackageTier` | REUSE | Reuse exact core/standard/domain/experimental enum as optional tier classification, with no authority implication |
| `rich_documents.model.PackageDescriptor`, ApexDocument and blocks | FROZEN_PREDECESSOR | Preserve opaque package_id/version, ordered documents, metadata and document semantics; not a distributable content identity |
| `tooling.project_manifest.ProjectManifest`, `apexforge.json` fixtures/examples | FROZEN_PREDECESSOR | Preserve schema 1, project name/source/entry/package fields and old normalizations; new package manifest coexists and is not accepted by the old loader |
| `tooling.project_loader.LoadedProject` and source snapshots | REFERENCE_ONLY | Existing project loading reads files; P14 declares paths/digests without loading them |
| P11.13F1 manifest, F2 rich-document build and F3 CLI routing | FROZEN_PREDECESSOR | Preserve explicit package-declared routing, source ordering, ordered package documents and existing build behavior |
| `language.identities.ProjectDeclaredIdentity` | ADAPT | Thin SymbolReference.from_declared preserves existing directive/function AIR IDs and module spelling; it does not resolve symbols |
| `language.modules` module/import graph and declared-name grammar | REFERENCE_ONLY | Reuse compatible ASCII identifier/dotted shape; package namespace is a lower-case subset, not a language module/import or dependency solver |
| `authority.model` principals/checks/grants | REFERENCE_ONLY | Existing authority remains owner; capabilities in a package are declarations, not checks or grants |
| `tooling.build_artifact`, passive interoperability integrity models | REFERENCE_ONLY | Reuse SHA-256, versioned schema and sorted JSON conventions; artifact hash and package identity remain separate |
| Native build receipts, source mappings and retained provenance scopes | REFERENCE_ONLY | Passive schema/kind/fingerprint references can carry supplied associations; no build, receipt issuance, dispatch or provenance inference |
| P12 metadata SourceIdentity and P13 evidence/debugger models | REFERENCE_ONLY | Test carries an actual existing source fingerprint without mutating the producer; production manifest does not import debugger or execution owners |
| VS Code package.json / tooling.vscode_package | NOT_A_PACKAGE_CONTRACT | Frozen editor extension distribution manifest/tooling, not ApexForge canonical package identity |
| Visual Studio VSIX PackageManifest | NOT_A_PACKAGE_CONTRACT | Frozen IDE deployment format, not ApexForge namespace/authority/content identity |
| Python packages/import layout, CLI project inventory and native binary/archive containers | NOT_A_PACKAGE_CONTRACT | Import organization, tooling presentation or artifacts; none establishes canonical package semantics |
| P11 incremental dependency-aware cache | NOT_A_PACKAGE_CONTRACT | Compilation/cache dependencies do not implement P14 package resolution |

P11.13 remains the rich-document semantic owner. The P14 manifest preserves its tier enum and document declaration order but requires explicit namespace/name/release/content declarations. There is no automatic conversion of a legacy opaque version such as `2026.1` or `v1`, nor inference of namespace from old package_id, directory, publisher, organization or Git owner. A caller must supply the new contract deliberately. The existing `.apexdoc` parser/compiler and document block identities are not duplicated.

## Identity model and namespaces

```text
PACKAGE = IDENTITY + MANIFEST + CONTENT BOUNDARY + CAPABILITY CONTRACT + PROVENANCE REFERENCES
PACKAGE_COORDINATE != PACKAGE_CONTENT_IDENTITY
SAME_COORDINATE + DIFFERENT_CANONICAL_CONTENT != SAME_PACKAGE_CONTENT
PACKAGE != ARCHIVE != FILESYSTEM_PATH
PACKAGE != ORGANIZATION
PACKAGE != EXECUTION
PACKAGE != AUTHORITY
PACKAGE_MANIFEST != SEMANTIC_AUTHORITY
```

`PackageCoordinate(namespace, name, ExactVersion, schema)` is immutable. Its record includes manifest generation, namespace, name and release string. It identifies a declaration coordinate, not unique contents. `PackageContentIdentity(fingerprint, domain)` is a separate immutable, domain-qualified address returned by a validated manifest. Different supplied content under one coordinate yields different addresses; registry conflict policy and resolved/installed instance identity are deferred.

Namespace grammar is `[a-z_][a-z0-9_]{0,63}(\.[a-z_][a-z0-9_]{0,63})*`, maximum 255 characters. It is an explicit lower-case ASCII subset of the established dotted module-name grammar. No trimming, case conversion, Unicode normalization or organization inference occurs.

Package name grammar is `[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*`, maximum 64 characters. Hyphen and underscore remain distinct; repeated/trailing separators, dots, paths, upper-case and non-ASCII names reject. A display title belongs in metadata and never replaces the coordinate.

Package strings do not establish principal, role, organization ownership or authorization. Content descriptors and source/artifact references remain different typed records, not packages themselves.

## Exact version and schema

P11 versions are opaque deterministic strings; IDE versions show numeric triples but do not establish universal package SemVer. `ExactVersion` therefore implements only numeric release triples: `major.minor.patch`, no leading zero except zero, each component an exact non-Boolean integer from 0 through 2147483647. External text is limited to 32 ASCII characters. Prerelease/build suffixes, ranges, tags and precedence algorithms are unsupported. This is the numeric release subset, not a full Semantic Versioning claim.

Manifest schema is `apexforge.package/v1`; fingerprint domain is `apexforge.package-manifest-identity/v1`. Schema generation and package release are separate. Only the current manifest schema is admitted; incompatible semantics require a new schema. Dependency coordinates default to this generation when omitted in raw dependency input and always serialize it explicitly.

## Immutable manifest fields and identity participation

| Field | Contract | Identity participation |
| --- | --- | --- |
| schema, namespace, name, version | Required raw identity fields; validated PackageCoordinate | IDENTITY_AFFECTING |
| content | Required raw explicit array, possibly empty; frozen ContentDescriptor tuple | IDENTITY_AFFECTING |
| tier | Optional existing PackageTier; absence means no supplied classification | IDENTITY_AFFECTING |
| documents | Ordered logical .apexdoc member paths, exactly matching document-kind content members | IDENTITY_AFFECTING; declaration order preserved |
| dependencies | Exact PackageCoordinate tuple, one declaration per namespace/name | IDENTITY_AFFECTING |
| exports | Existing directive/function SymbolReference tuple | IDENTITY_AFFECTING |
| entrypoints | Directive SymbolReference declarations only | IDENTITY_AFFECTING |
| capabilities.exports / requires | Separate exact qualified-name declaration tuples | IDENTITY_AFFECTING |
| provenance | Passive CanonicalReference tuple | IDENTITY_AFFECTING |
| metadata | Known string pairs: title, description, authors, license, homepage, documentation | NON_IDENTITY_METADATA |

All construction paths validate exact immutable value-object types and tuples. Canonical record/mapping methods return fresh detached JSON-compatible values; editing those returned records cannot mutate the validated manifest. Metadata permits bounded human text without control characters or lone surrogates. Authors/homepage/license are presentation text, not authenticated publisher or license/trust verification.

Changing metadata changes deterministic interchange JSON, but not canonical identity JSON or package content identity. There is no timestamp, PID, username, handle, mtime, temporary root or absolute-host-path identity field. Explicit logical names can be supplied by a caller, but the module never queries the host to populate them.

## Content boundary and portable path model

`ContentDescriptor(path: PackagePath, digest, kind, reference?)` separates the logical path, exact uppercase SHA-256 digest, content kind and optional producer reference. Supported member kinds are source, document, artifact and data; these describe members, not new package-tier semantics. Document members must use lowercase `.apexdoc` and must appear exactly once in the ordered document list.

Only explicitly declared member descriptors participate. The containing directory is never scanned or hashed. Unlisted build output/volatile files are outside the boundary; a build artifact enters only if deliberately declared as an artifact member. This slice validates digest syntax, not the truth of caller-supplied bytes/digests or producer associations. It does not create/read archives, sign, verify payload integrity, or establish the complete source -> package -> artifact -> registry chain.

PackagePath uses literal `/` separators, maximum 512 characters and 128 per segment. Segments match `[A-Za-z0-9_-][A-Za-z0-9_.-]*`, cannot end in a dot and cannot use Windows reserved device names. Absolute/UNC/drive-qualified paths, backslashes, traversal, dot segments, empty segments, colon/stream syntax, whitespace and Unicode alternatives reject rather than normalize. Case-colliding duplicate paths reject for portable uniqueness. A member also cannot be an ancestor directory of another member, including case variants. The model has no filesystem methods or implicit host-path conversion.

Content ordering is deterministic by case-folded logical member path, after rejecting collisions. Filesystem mtimes, archive compression and enumeration order do not participate. This is an explicit logical member boundary, not installation state.

## Dependencies, exports, entrypoints and capabilities

Dependencies are exact, unresolved coordinate declarations. Duplicate or conflicting versions for the same namespace/name reject. Canonical order is namespace/name; no version selection, transitive traversal, candidate comparison, backtracking, registry lookup or lock record exists. Absence of dependency evidence does not authorize inventing it. Dependency kind/range/optional-feature policies remain later work.

SymbolReference carries a supplied uppercase AIR/program fingerprint, existing kind (`directive` or `function`), exact `directive:<identifier>` / `function:<identifier>` identity and optional existing dotted module spelling. Its thin adapter consumes the frozen ProjectDeclaredIdentity carrier without changing IDs or interpreting display names as authority. It does not evaluate declarations, resolve imports or prove the reference exists in supplied content. Same module/kind/identity exported more than once rejects, including conflicting producer fingerprints. Exports and entrypoints are independently sorted nonsemantic declaration sets; an entrypoint is a directive declaration, not execution permission.

Capabilities are bounded exact ASCII dotted identifiers, sorted separately for exports and requirements. Duplicate/malformed names reject. Requiring and exporting the same capability is not inherently contradictory: neither grants authority. There are no principal bindings, authorization decisions, grants, wildcard authority, runtime checks or capability engine in this module.

```text
ENTRYPOINT_DECLARATION != EXECUTION_PERMISSION
DECLARED_CAPABILITY != GRANTED_AUTHORITY
REQUIRED_CAPABILITY != AUTHORIZATION
PARSED != VALIDATED
VALIDATED != AUTHORIZED
```

## Passive provenance references

CanonicalReference contains schema, kind and producer fingerprint. Schema syntax is `apexforge.<ASCII-domain>/v<positive-generation>`; admitted reference kinds are source, air, source-mapping, native-mapping, artifact, build-receipt, provenance-scope and result-association. Duplicate references reject; canonical ordering uses their deterministic JSON record. Unknown producer content is not loaded or evaluated.

The focused fixture builds an existing P12 SourceIdentity from supplied bytes and carries its actual schema/fingerprint alongside its separate raw source-content digest. The source identity remains unchanged. The reference shape does not claim existence, program/content binding, authenticity, signing, ownership or trust; those validations belong to the respective producer/integrity owners and later P14 contracts. No fabricated native execution receipt or human attribution reference is added.

`PROVENANCE_REFERENCE != TRUST_DECISION`. P14.6 owns signing/integrity/provenance/trust integration; the full source/package/artifact/registry chain is not operational here.

## Raw parsing, canonical records and fingerprints

`parse_manifest(text)` accepts supplied JSON text only. It does not accept file paths or discover/load a project. The parser bounds UTF-8 input to 1 MiB, rejects duplicate keys at every object depth and nonfinite constants, bounds numeric integer tokens to ten digits before conversion, and reports fixed parse errors for malformed JSON, invalid UTF-8 encodings/surrogates and excessive nesting. Numeric JSON fields are not package versions; exact version text has its own validator.

`PackageManifest.from_mapping` validates the exact dict/object/array shapes, required identity/content fields, nested known-field sets and typed values. Optional omissions become explicit canonical defaults. Parsing success alone is not validation or authorization.

`canonical_record()` includes all identity-affecting fields, with metadata omitted. `canonical_json()` uses sorted keys, compact separators, ASCII JSON escaping, finite values and no trailing newline. `to_mapping()` / `to_json()` additionally preserve sorted non-identity metadata. These are intentionally different contracts. Equivalent independently constructed manifests yield equal records, interchange, preimages and identities without dict insertion order, locale or Python repr dependence.

The uppercase SHA-256 identity is:

```text
SHA256(UTF8("apexforge.package-manifest-identity/v1" + NUL + canonical_json))
```

The NUL-delimited explicit domain is separate from raw source/artifact digest inputs. It is not a signature, authenticity proof or producer-content verification.

Minimal interchange example (explicitly empty logical content boundary):

```json
{"schema":"apexforge.package/v1","namespace":"apexforge.example","name":"sample","version":"1.2.3","content":[]}
```

## Fail-closed and forward compatibility contract

Missing fields, unknown schema, invalid namespace/name/version/tier, unsafe/conflicting/duplicate members, malformed hashes/references, duplicate/conflicting dependencies, duplicate exports/entrypoints, malformed capability names, mismatched document boundary and invalid metadata reject. No whitespace/case/separator repair or inferred metadata is applied.

Unknown fields reject at the root and every semantic record. Metadata has a fixed allowlist; there is no arbitrary extension field space in v1. This avoids dropping future semantics while retaining deterministic interpretation. Extending meaning requires an explicitly versioned future contract, not silently accepting a newer manifest. Unsupported package kinds, signing fields or timestamps are not ignored.

PackageManifestError exposes fixed codes rather than echoing arbitrary untrusted values; the sensitive diagnostic sentinel is absent from str/repr. No parser error becomes semantic execution failure or a trust decision.

## Security and static separation audit

Production imports are limited to dataclasses, hashlib, json, re, the passive language.identities carrier and rich_documents.model. AST checks reject direct AIR/RuntimeEngine/AuthorityEngine/native dispatch, eval/exec/dynamic payload imports, process launch and file access. Dynamic guards block file opening, subprocess and sockets while parsing, canonicalizing and independently constructing equivalent manifests.

No production code accesses registry/network, arbitrary host paths, executables, installation state or private host metadata. No existing authority/provenance engine is invoked. PACKAGE remains distinct from organization, principal, role, capability, authority, artifact, source member, coordinate and archive. JSON output is a declaration representation, not semantic or ownership authority.

## Focused validation and Patch Matrix ledger

Final owning suite:

```text
python -X utf8 -B apexforge/p14_1_package_identity_manifest_contract_test.py
36/36 PASS
```

Cases consolidate minimal/schema/namespace/name/version identity, same-coordinate content changes, all identity-affecting fields, metadata exclusion, safe paths/collisions/ancestor conflicts, ordered document boundaries, dependency/export/capability sorting and duplicate rejection, original symbol/source identity preservation, domain-separated fingerprints, malformed/missing/unknown fields, duplicate JSON keys, bounded parser errors, immutability/detached records, diagnostics, P11 coexistence and static/dynamic security separation.

| Failure / classification | Owner and narrow correction | Required regression |
| --- | --- | --- |
| First 34-case run: source-reference import failed | TEST_INVOCATION_DEFECT; new P14.1 test lacked established repo-root import setup; added it only to that test | Complete owning suite passed 34/34 |
| First run: detached-record inequality assertion failed | TEST_FIXTURE_DEFECT; fixture assigned the already-present document digest; changed the new test to a genuinely different digest | Same 34/34 rerun |
| Review probe accepted member `src` plus `src/main.apex` | PACKAGE_PATH_GAP; new P14 validator owns logical boundary ambiguity; reject member/ancestor conflicts using case-folded path prefixes | Final 36/36 owning suite and relevant predecessor groups |
| Review probe raised Python integer-conversion ValueError for 5000-digit token | MANIFEST_VALIDATION_GAP; new parser owns fixed bounded diagnostics; reject overlong numeric token before conversion without changing host security limits | Same final 36/36 and predecessor reruns |
| Discovery named nonexistent guessed module/artifact/CLI paths and used unsupported rg wildcard / Get-FileHash argument form | TEST_INVOCATION_DEFECT in inspection only; corrected discovery to actual rg inventory and named LiteralPath array; no source change | Actual owners inspected and final audit succeeded |

Two review probes initially produced one failure and one error before production correction. No old assertion was weakened, no frozen owner changed, and no host limit/security policy was bypassed.

Patch Matrix routing: observe -> classify -> owning P14.1 test or validator/parser -> preserve P10/P11/P12/P13 -> smallest two new-file patch surface -> path ambiguity/fixed diagnostic invariants -> final owning suite -> materially relevant predecessor groups -> preservation audit. Cross-client/P13 matrices are not affected because no debugger or shared contract changed. The P14 aggregate is currently this one 36-case suite; no unrelated closure stack is required. `PATCH_MATRIX=PASS` applies after the final audit.

## Final predecessor coexistence and regression selection

After the final P14 correction, unchanged P11.13B `_assert_public_surface`, `_assert_immutable_models`, `_assert_document_model`, `_assert_package_model` passed: `P11_13B_BEHAVIORAL_ASSERTIONS=4_GROUPS_PASS`.

Unchanged P11.4B `test_public_model_validation_order_queries_and_immutability` and `test_collection_determinism_families_and_project_compatibility` passed: `P11_4B_IDENTITY_ASSERTIONS=2_GROUPS_PASS`.

These groups were invoked by their existing functions using the established ApexForge import root. Full historical P11.13B/F1 harnesses contain stage-specific owner/artifact inventory requirements; they were inspected rather than incorrectly invoked as current-worktree acceptance. No historical test was edited or claimed to pass in full. The focused suite also checks original P11 project manifest JSON roundtrip, unchanged opaque version and preserved document ordering alongside P14.

P13 tests were not rerun because no P13/shared production module changed. P13 tag object, peeled target, immutable incoming P13 hashes and all tracked-file/index diffs were audited instead. No full P12/P11 closure stack was run.

Final production SHA-256: `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7`.
Final focused-test SHA-256: `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3`.

## Remaining gaps and explicit exclusions

| Gap | Classification / disposition |
| --- | --- |
| Dependency ranges, solving/transitive selection and resolved package instances | DEFER_TO_P14_2; no resolver introduced |
| Lockfile/reproducible restore | DEFER_TO_P14_3 |
| Payload verification, signature/trust/provenance-chain validation | DEFER_TO_P14_6; references are passive claims |
| Registry client/server, namespace ownership and coordinate conflict policy | DEFER_TO_P14_8; strings do not prove ownership |
| Publication/network exchange | DEFER_TO_P14_9 |
| Archive creation/installation/execution, package-manager CLI and full legacy project integration | Unimplemented; outside P14.1 |
| Arbitrary legacy versions, prerelease/build suffixes, optional/range dependency policies and broader exported symbol kinds | Explicitly unsupported in current bounded schema, not silently interpreted |
| P15/domain work or reopening frozen compiler/runtime/debugger/IDE owners | Excluded |

## Evidence-supported markers

```text
P14_BASELINE=P13_12_FREEZE
P14_BASELINE_COMMIT=860ba9287ee237ddca0691355607c896f3ea382f
P13_REOPENED=False
P14_PACKAGE_MODEL_IMMUTABLE=True
P14_PACKAGE_COORDINATE_DISTINCT_FROM_CONTENT_IDENTITY=True
P14_PACKAGE_PATH_DISTINCT_FROM_HOST_PATH=True
P14_MANIFEST_SCHEMA_VERSIONED=True
P14_MANIFEST_CANONICALIZATION=DETERMINISTIC
P14_PACKAGE_IS_ARCHIVE=False
P14_PACKAGE_IS_ORGANIZATION=False
P14_DECLARED_CAPABILITY_IS_AUTHORITY=False
P14_REQUIRED_CAPABILITY_IS_AUTHORIZATION=False
P14_MANIFEST_EXECUTES_AIR=False
P14_MANIFEST_EXECUTES_RUNTIME=False
P14_MANIFEST_DISPATCHES_NATIVE=False
P14_MANIFEST_GRANTS_AUTHORITY=False
P14_MANIFEST_NETWORK_ACCESS=False
P14_MANIFEST_HOST_COMMAND_EXECUTION=False
P14_DEPENDENCY_SOLVER_IMPLEMENTED=False
P14_LOCKFILE_IMPLEMENTED=False
P14_REGISTRY_CLIENT_IMPLEMENTED=False
P14_REGISTRY_SERVER_IMPLEMENTED=False
P14_PACKAGE_SIGNING_IMPLEMENTED=False
P14_PACKAGE_TRUST_ENGINE_IMPLEMENTED=False
P14_PROVENANCE_TRUST_VALIDATION=False
P14_PACKAGE_INSTALLER_IMPLEMENTED=False
P14_PACKAGE_EXECUTION_IMPLEMENTED=False
P14_PACKAGE_IDENTITY=PASS
P14_PACKAGE_NAMESPACE=PASS
P14_PACKAGE_VERSION=PASS
P14_MANIFEST_SCHEMA=PASS
P14_MANIFEST_VALIDATION=PASS
P14_MANIFEST_CANONICAL_SERIALIZATION=PASS
P14_PACKAGE_CONTENT_IDENTITY=PASS
P14_PACKAGE_PATH_MODEL=PASS
P14_DEPENDENCY_DECLARATION=PASS
P14_EXPORT_CONTRACT=PASS
P14_CAPABILITY_DECLARATION=PASS
P14_PROVENANCE_REFERENCE_MODEL=PASS
P14_PACKAGE_DETERMINISM=PASS
P14_PACKAGE_SECURITY_BOUNDARY=PASS
PATCH_MATRIX=PASS
P14_1_READY_FOR_REVIEW=True
```

The provenance model is implemented; PASS concerns structural references, not trust. All PASS values are limited to the demonstrated bounded schema and controlled fixtures.

## Exact Git status and preservation

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/tooling/package_manifest.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
```

Final P14 candidate count is three. Branch is `p14-1-package-identity-manifest`, with unchanged HEAD/base `860ba9287ee237ddca0691355607c896f3ea382f`. P13 annotated tag object and peeled target are unchanged. All 30 P13.12 incoming byte hashes are preserved; tracked/index diffs are empty, so P13/P12/P11/P10 frozen files are unchanged. No generated cache/binary residue or build output remains. Nothing staged; no commit/tag/push, P14.2, lockfile, resolver, registry/network, publication, signing/trust, installer, package execution or P15 work. Stop after P14.1 owner review readiness.
