# P14.4 — Package Namespaces, Exports & Cross-Package Symbol Resolution

Review evidence only. No freeze, publication or closure operation.

## Frozen baseline and incoming hashes

Branch `p14-1-package-identity-manifest`; HEAD and peeled `afp-p13.12-freeze` both `860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

All nine SHA-256 hashes captured before implementation and preserved after all regressions:

| Incoming file | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/p14_3_lockfile_reproducible_restore_test.py` | `F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `apexforge/tooling/package_solver.py` | `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1` |
| `apexforge/tooling/package_lock.py` | `D9AA13C73B92A1F5FA4A0DDEE365A8978484F694B0E5DD3A42AC0892FB726E94` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |
| `docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md` | `CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B` |
| `docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md` | `7490A98A1C14EB975FCB51A6FB612E3D50A080FFD7A77BEF86B2548DD48E4FDE` |

Tracked and cached diffs remain empty, so P10/P11/P12/P13 frozen files are unchanged.

## Repository identity census

| Existing concept | Classification | P14.4 treatment |
|---|---|---|
| `language/identities.py`: ProjectDeclaredIdentity / ProjectIdentityIndex | REUSE; FROZEN_LANGUAGE_CONTRACT | Current directive/function AIR ID preserved; tests use the existing supplied declaration conversion. Index queries may return multiple candidates; display names remain non-resolving. |
| `language/modules.py`, project declaration ownership and module visibility | FROZEN_LANGUAGE_CONTRACT; NOT_PACKAGE_NAMESPACE | Existing language module and direct-import behavior remain unchanged. No package syntax inserted into source parsing or linking. |
| `language/source.py` source positions/spans | REUSE; FROZEN_LANGUAGE_CONTRACT | Used for an actual declared identity fixture; no new source reader. |
| P11.4A identity/nesting audit and P11.4B metadata evidence | REFERENCE_ONLY | Current AIR IDs are kind-prefixed and module metadata does not replace them. Aliases, language namespace syntax and export/re-export syntax were absent in that audited contract. |
| P11.13A rich-document architecture, package tiers and .apexdoc links | REFERENCE_ONLY; FROZEN_LANGUAGE_CONTRACT | Package tiers/document organization do not establish a new language import engine. Ordered rich-document contents and reference relationships remain P14.1 data. |
| P14.1 SymbolReference and manifest exports | REUSE | Immutable directive/function references, exact AIR fingerprint and optional module; no rewritten manifest fields. |
| P14.2 resolved packages/graphs/edges | REUSE | Exact admitted package content, dependency visibility evidence and iterative graph validation. No solving. |
| P14.3 PackageLock | REUSE | Exact locked graph/content association. No restore, regeneration or lock editing. |

Package namespace strings are coordinate fields. Language module strings are symbol metadata. Package names do not become module names. Package namespace is never prefixed onto an AIR ID to mint a language identity.

## Export interpretation and admission boundary

P14.1 explicitly lists `SymbolReference` exports. Supported categories are existing `directive` and `function` identities. P14.4 retains each reference exactly, including AIR fingerprint, kind, ID and module.

The package-facing export key uses the existing kind-prefixed spelling, for example `function:Run`. EXPORT_NAME and CANONICAL_SYMBOL_IDENTITY remain separate record fields and domains even when their strings match. No arbitrary alias name or new manifest declaration is invented. Export-key validation uses that bounded exact grammar. Package qualification is separate from language module qualification.

`PackageExportIndex` is a frozen provider-bound view over an exact `ResolvedPackage` and a tuple of supplied canonical `SymbolReference` declaration evidence, including private declarations if supplied. Each exported reference must occur exactly in that evidence. Missing or stale AIR/module evidence rejects. Unsupported/raw evidence types reject; duplicate evidence rejects. Repeated export names across different modules/AIR references within one package reject rather than choosing a display candidate. P14.1 already rejects repeated identical manifest exports.

Evidence ownership is a caller-supplied contract, not a compiler, authentication or trust verdict. This module cannot prove that arbitrary producer claims are authentic. Within the supplied namespace it rejects the same exact canonical declaration assigned to two distinct package providers. It does not recompile source or infer ownership from files, names or package metadata. No re-export descriptor is admitted or followed.

Private declarations may support export validation but are absent from the index's canonical public export record and cannot resolve through the package interface. Visibility is explicit manifest membership, with no underscore/path naming heuristic.

## Namespace, reference and binding models

`PackageNamespace` accepts only a validated P14.2 graph and immutable export indexes for its exact admitted nodes, optionally the exact matching P14.3 lock. Every node with exports requires an index. Duplicate indexes, an external provider, same-coordinate changed provider content, or wrong locked graph reject.

`PackageSymbolReference` contains the export key and optional exact provider coordinate. A coordinate is addressing input, not sufficient final identity. `resolve` returns `ResolvedExportBinding` containing consumer/provider exact content identities, original symbol reference, dependency edge/declaration fingerprint, index fingerprint, optional lock and provider provenance references. Result constructor checks declaration/export membership, direct dependency and exact edge/content binding. When locked, consumer, provider and edge must belong to that lock.

No language symbol is copied into a new declaration or renamed. Package handles and binding fingerprints never masquerade as canonical AIR identity.

## Visibility, ambiguity, collisions and re-export

Policy: DIRECT_ONLY. Consumer A can look up B only through A's direct resolved dependency edge. A -> B -> C does not expose C to A; B can address C. A package merely supplied in the universe but absent from this graph is invisible. A cannot use this resolver for local declarations; existing local language lookup remains separate.

An unqualified key searches only explicit direct-dependency exports. Zero matches is `EXPORT_NOT_FOUND`. Multiple matches is `EXPORT_AMBIGUOUS` with canonical provider candidate records sorted deterministically, independent of supplied index order. An exact provider coordinate disambiguates only if directly visible. Nothing silently shadows or selects by shortest name, order or traversal.

Within-package export-key collisions reject. Across-package same key is permitted as distinct references, requiring qualification when ambiguous. Same exact symbol evidence claimed by different owners rejects. Aliases and re-exports are deferred: IMPORT != REEXPORT, and a consumer does not automatically export its dependency's symbols. There is no recursive namespace/re-export traversal.

## Lock, provenance, authority and capability boundaries

A namespace's optional lock must exactly equal its resolution graph, including root, nodes, edges and package contents. Same coordinate with substituted content fails before lookup. Successful binding retains exact provider content and optional lock fingerprint. No lock update/regeneration is invoked.

Provider provenance remains a passive canonical reference list in index/binding records. It is not publisher ownership, actor attribution or trust validation. Capability declarations remain in referenced canonical package manifests. There is no satisfaction evaluation, AuthorityEngine, authority grant or executable import. Package capability enforcement is deferred to P14.5.

## Canonical forms, determinism and immutability

Index JSON orders export keys, preserves original symbol records and provenance, and includes exact provider reference. Private declaration evidence is deliberately outside public index serialization. Evidence tuples themselves normalize by canonical symbol record. Namespace indexes normalize by canonical provider reference; no host or insertion ordering.

Bindings serialize schema, consumer/provider references, export key, original symbol, exact dependency edge, index fingerprint, optional lock fingerprint and provenance. JSON uses sorted keys, ASCII escaping, compact separators and finite values.

SHA-256 fingerprints are domain-separated with NUL before canonical UTF-8 JSON:
- `apexforge.package-export-index-fingerprint/v1`
- `apexforge.package-symbol-binding-fingerprint/v1`

Both differ from manifest, solution, lock and AIR identity domains. Equivalent independently constructed inputs and supplied order permutations yield equal models/forms/fingerprints. No timestamps, host paths, local handles or object repr participate.

Frozen dataclasses protect namespace/index/reference/binding; all nested producer objects are existing immutable carriers. Resolution does not change manifests, graph, lock or supplied identities.

## Large supplied indexes and security

The focused suite resolves across 1,100 direct provider packages/exports in normal and reversed index order. Lookup uses supplied arrays/maps with no recursive namespace search. Existing graph validation is iterative; no new recursive semantic traversal is introduced. This is a bounded correctness check, not a performance claim. Current lookup is linear over supplied indexes; admission's completeness check can be quadratic, which remains practical for the tested size.

AST/import audit rejects direct AIR/runtime/native/authority execution, process/shell calls, dynamic payload imports, network modules, file opening, source parsing, solving, restore or installation. Lookup still succeeds when the external solver and restore owner functions are patched to throw if called. No candidate discovery, registry, source/file reader, installer, authority bypass or producer mutation API.

## Validation and Patch Matrix

Final exact-file results, run in required sequence:

| Suite | Result |
|---|---|
| P14.4 package namespace/export resolution | 23/23 PASS |
| P14.3 lockfile/restore | 28/28 PASS |
| P14.2 solver | 38/38 PASS |
| P14.1 manifest | 36/36 PASS |
| `python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py` | 125/125 PASS |

Frozen coexistence used only `p11_4b_declared_identity_metadata_smoke_test` behavioral groups:
`test_public_model_validation_order_queries_and_immutability` and
`test_collection_determinism_families_and_project_compatibility`: 2 GROUPS PASS.
No historical inventory-sensitive full harness was run and no frozen file was changed.

Initial focused run: 23 tests, three errors.
FAILURE: helper did not forward replacement keyword arguments (two errors), and SourcePosition fixture supplied offset in the line slot (one error).
CLASSIFICATION: TEST_FIXTURE_DEFECT.
OWNING SECTION / PATCH SURFACE: new P14.4 test file only.
FROZEN DEPENDENCIES: language source/identity, P14.1 manifest, P14.2 graph, P14.3 lock unchanged.
LOCAL CONTRACT: actual SourcePosition(line,column,offset), and keyword-forwarding error assertion helper.
SECTION REGRESSION: corrected focused 23/23 PASS.
DEPENDENCY / CROSS-SECTION / AGGREGATE: all required P14 predecessors, aggregate and two frozen behavioral groups PASS.
PRESERVATION: nine hashes unchanged, empty tracked/index diffs, expected lineage and no residue.
PATCH_MATRIX=PASS.

A read-only literal wildcard `rg` search produced a Windows invocation error; classification TEST_INVOCATION_DEFECT. It was replaced by the discovered exact filename. No source patch or contract change was associated with that search.

## Preserved limitations and deferred work

Supplied canonical identity evidence must already be admitted by the caller; this layer does not authenticate build ownership. Only directive/function references are supported. Package aliases, re-exports, language syntax integration and automatic source discovery are unavailable. Package capability enforcement, signing/trust, cache, registry, publication, installation, execution and P15 remain deferred. No P14.5 work.

PACKAGE_NAMESPACE != LANGUAGE_NAMESPACE; PACKAGE_NAME != MODULE_NAME; PACKAGE_EXPORT != LANGUAGE_DECLARATION; EXPORT_REFERENCE != COPY_OF_DECLARATION; IMPORT_BINDING != EXECUTION; IMPORT_BINDING != AUTHORIZATION; EXPORTED_CAPABILITY != GRANTED_AUTHORITY; PACKAGE_VISIBILITY != AUTHORITY; PACKAGE_ALIAS != CANONICAL_IDENTITY; RESOLVED_SYMBOL_HANDLE != CANONICAL_SYMBOL_IDENTITY; LOCAL_LANGUAGE_LOOKUP != PACKAGE_EXPORT_LOOKUP; SYMBOL_VISIBLE != AUTHORIZED_TO_EXECUTE; EXPORT_PROVENANCE_REFERENCE != ATTRIBUTION.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P14_4_INCOMING_CANDIDATES=9
P13_REOPENED=False
P14_EXPORT_INDEX_INPUT=SUPPLIED_VALIDATED_IDENTITIES
P14_PACKAGE_NAMESPACE_DISTINCT_FROM_LANGUAGE_NAMESPACE=True
P14_EXPORT_NAME_DISTINCT_FROM_CANONICAL_SYMBOL_IDENTITY=True
P14_EXPORTED_SYMBOL_CANONICAL_IDENTITY_PRESERVED=True
P14_EXPORT_PROVIDER_CONTENT_IDENTITY_PRESERVED=True
P14_PRIVATE_DECLARATIONS_EXPORTED=False
P14_AMBIGUOUS_EXPORT_FAILS_CLOSED=True
P14_REEXPORT_IMPLEMENTED=False
P14_EXPORT_RESOLUTION_GRANTS_AUTHORITY=False
P14_EXPORT_CAPABILITY_ENFORCEMENT_IMPLEMENTED=False
P14_SYMBOL_LOOKUP_DISCOVERS_PACKAGES=False
P14_NAMESPACE_EXECUTES_AIR=False
P14_NAMESPACE_EXECUTES_RUNTIME=False
P14_NAMESPACE_DISPATCHES_NATIVE=False
P14_NAMESPACE_GRANTS_AUTHORITY=False
P14_NAMESPACE_NETWORK_ACCESS=False
P14_NAMESPACE_FILESYSTEM_DISCOVERY=False
P14_NAMESPACE_HOST_COMMAND_EXECUTION=False
P14_PACKAGE_NAMESPACE_MODEL=PASS
P14_EXPORT_INDEX=PASS
P14_EXPORT_IDENTITY_BINDING=PASS
P14_EXPORT_VISIBILITY=PASS
P14_EXPORT_AMBIGUITY_HANDLING=PASS
P14_EXPORT_COLLISION_HANDLING=PASS
P14_EXPORT_LOCK_BINDING=PASS
P14_EXPORT_PROVENANCE=PASS
P14_EXPORT_DETERMINISM=PASS
P14_NAMESPACE_SECURITY_BOUNDARY=PASS
P14_TRANSITIVE_EXPORT_VISIBILITY=DIRECT_ONLY
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
PATCH_MATRIX=PASS
P14_4_READY_FOR_REVIEW=True
```

## Exact Git status and preservation

Final `git status --short --untracked-files=all`:

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/p14_4_package_namespace_export_resolution_test.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_namespace.py
?? apexforge/tooling/package_solver.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
?? docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md
```

Exactly 12 candidates, three new P14.4 files. Branch, HEAD, annotated freeze object and peeled target unchanged. All nine incoming hashes unchanged. No tracked frozen changes; nothing staged; no generated Python caches/bytecode, executable/library/symbol/object or VSIX residue. No commit, tag or push. Stop at P14.4 review readiness.

