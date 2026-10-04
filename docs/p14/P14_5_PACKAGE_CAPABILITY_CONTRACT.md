# P14.5 — Package Capability Contracts & Compatibility Validation

Review evidence; no release, freeze or closure operation.

## Baseline and incoming hashes

Branch `p14-1-package-identity-manifest`; HEAD and peeled `afp-p13.12-freeze`:
`860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

Twelve SHA-256 hashes captured before implementation and confirmed unchanged after validation:

| Incoming candidate | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/p14_3_lockfile_reproducible_restore_test.py` | `F818CD49F5F7B11B510ADAF3B1CCC4C2E3D38790CA055483FF76C7D9EF70555F` |
| `apexforge/p14_4_package_namespace_export_resolution_test.py` | `BCE5A2A91310CED3FBDFC0A6B284CC2D5C017F63C662DF36E8C10502FBFC1C3F` |
| `apexforge/tooling/package_lock.py` | `D9AA13C73B92A1F5FA4A0DDEE365A8978484F694B0E5DD3A42AC0892FB726E94` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `apexforge/tooling/package_namespace.py` | `57B6D3C8BB005D50E640E170525ACEC14C82134E1662AD5932F9BA0B66E42C05` |
| `apexforge/tooling/package_solver.py` | `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |
| `docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md` | `CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B` |
| `docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md` | `7490A98A1C14EB975FCB51A6FB612E3D50A080FFD7A77BEF86B2548DD48E4FDE` |
| `docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md` | `9E5DF5321AF33ADD30DA28BE896C5F81DE1A431509042C6AF0F4E1BE8848C63B` |

## Existing capability and authority census

| Carrier | Classification | Treatment |
|---|---|---|
| authority/model.py Principal, AuthorityCheck, AuthorityGrant | FROZEN_AUTHORITY_CONTRACT | Principal, role strings, capability request and explicit resource-bound grant remain distinct; no modification. |
| authority/engine.py AuthorityEngine | FROZEN_AUTHORITY_CONTRACT | Runtime permission owner, deny-by-default and wildcard grant semantics. Not imported or invoked by package validation. |
| authority/compiler.py / domain declarations | REFERENCE_ONLY | Existing capability names do not create package permission semantics. |
| P13 authority inspection | REFERENCE_ONLY | Observed program authority remains separate from debugger control authorization. |
| P14.1 exported_capabilities / required_capabilities | REUSE; PACKAGE_COMPATIBILITY_ONLY | Immutable exact qualified ASCII identifiers, sorted unique, identity-affecting manifest fields. |
| P14.2 graph capability unions | REUSE; PACKAGE_COMPATIBILITY_ONLY | Existing propagation is declaration-only with compatibility not_evaluated. P14.5 creates a separate result rather than rewriting that historical graph record. |
| P14.3 lock | REUSE | Pins exact packages and graph; unchanged by validation. |
| P14.4 symbol export/index | REFERENCE_ONLY; PACKAGE_COMPATIBILITY_ONLY | Direct-only visibility precedent; symbols are not capability declarations. No export-index mutation or implicit symbol access. |

There is no separate versioned canonical capability object in these contracts. P14.5 uses the existing P14.1 string references unchanged. Their exact qualified identifier grammar is the admitted package-facing subset, not a new runtime grant identity system. Authority checks may use other runtime-specific strings and wildcard permissions; those permission semantics are not imported into package matching.

## Declaration meanings and exact matching

An exported capability is a structural provider declaration for a named contract. A required capability is a consumer's structural requirement for a direct dependency to declare that same contract. Neither grants authority or trust.

P14.5 matches exact case-sensitive strings only. No ranges, wildcard matching, inheritance, fuzzy names, implication, supersets, package-version-to-capability-version conversion or capability generation. Invalid names and duplicates are rejected by P14.1; direct binding/diagnostic construction checks the same bounded name grammar. Provider qualification, optional and deferred requirements are not represented by P14.1 and are not invented here.

## Provider/consumer and visibility binding

`validate_capabilities` consumes only a successful supplied `ResolutionGraph`, optionally the exact `PackageLock`. Existing graph validation is reused for content, declarations, closure and edge integrity; there is no solve, discovery, restore or lock regeneration.

Provider index entries are canonical graph nodes paired with exported names. Every `CapabilityBinding` retains the consumer exact coordinate/content identity, required name, provider exact coordinate/content identity and actual direct dependency edge with declaration fingerprint. Provider declaration evidence is recorded as its exact package reference and exported name, backed by its canonical manifest.

Visibility is DIRECT_ONLY, matching P14.4: A -> B -> C does not allow C to satisfy A's requirements. An unrelated universe candidate absent from the admitted closure never participates. A package's own exported name does not automatically satisfy its requirement. A direct dependency can satisfy it even if the consumer also exports that name.

Every required capability of every graph package is evaluated, not only the root. One visible exact provider creates a binding; no visible provider is incompatible. Multiple direct exact providers produce ambiguity, never a lexical/order/version choice.

## Diagnostics and fail-closed result

`CapabilityDiagnostic` retains exact consumer, capability and deterministically ordered provider references. Codes distinguish:
- MISSING_REQUIRED_CAPABILITY: no supplied graph provider.
- CAPABILITY_PROVIDER_NOT_VISIBLE: graph providers exist outside the direct dependency boundary.
- CAPABILITY_SELF_PROVIDER_NOT_ALLOWED: only the consumer itself declares the contract.
- AMBIGUOUS_CAPABILITY_PROVIDER: more than one direct provider.

If both invisible others and self evidence exist, the not-visible diagnostic takes precedence while all recorded candidates remain explicit. This is diagnostic classification, not permission inference.

Malformed input/reference/binding/result and lock association errors use fixed `PackageCapabilityError.code` values without raw payload echo or nondeterministic repr. Missing/ambiguous evidence is returned in an immutable matrix with compatible=False, not a success exception or usable permission grant.

`CapabilityCompatibilityResult` records all satisfied bindings and all unresolved diagnostics. Its constructor rechecks completeness against the supplied graph, so removing an unsatisfied requirement cannot forge compatible=True. Success requires zero unresolved requirements.

## Lock, symbol, authority, trust and provenance separation

When supplied, lock.resolution must equal the complete graph. A same-coordinate provider with changed content or a different root/edge graph rejects with CAPABILITY_LOCK_BINDING_MISMATCH. Result canonical form includes the lock fingerprint; bindings use exact locked node/edge identities. Lock content is never edited.

SYMBOL_EXPORT != CAPABILITY_EXPORT: a function export alone cannot satisfy a capability, and a capability export does not expose symbols. No P14.4 alias/index behavior is changed.

Validation never calls AuthorityEngine, creates AuthorityGrant, mutates principals/roles/grants, or treats visible names as execution permission. A test patches AuthorityEngine.check/allows to throw and verifies successful validation plus unchanged principal/grant objects. No runtime policy engine is implemented.

Consumer and provider provenance references are retained in binding records. They do not establish trust, publisher identity, attribution or permission. compatible=True is strictly structural; result records grants_authority=false and validates_trust=false.

## Canonical form and fingerprint

Schema/domain `apexforge.package-capability-compatibility/v1`.
Canonical record includes graph fingerprint, optional lock fingerprint, compatible flag, matching and visibility rules, ordered provider entries, binding relations and diagnostics.

Ordering follows canonical P14.2 nodes (namespace/name/numeric exact version/schema/content), then P14.1's sorted required/exported names. Provider candidate ordering uses the same coordinate/content key. Canonical JSON has sorted keys, ASCII escaping, compact separators and finite values. SHA-256 covers schema/domain, NUL, then canonical JSON UTF-8 bytes. This domain differs from manifest, solution, lock and symbol identities. Independently constructed equivalent graphs and input permutations yield equal forms/fingerprints. Content changes alter the result fingerprint.

No timestamp, host path, username, local handle or object repr participates. Package version remains distinct from capability identity.

## Immutability, large graph and security

Bindings, diagnostics and results are frozen and contain existing immutable graph/package/reference carriers. Validation does not change manifest, graph, lock, symbol index or authority state.

A 1,100-package chain with 1,099 required bindings passes independently in forward/reversed supplied order. Provider indexing and graph traversal are iterative; no recursive namespace/provider search. Input validation delegates graph integrity to the existing iterative owner. No performance expansion beyond this bounded correctness experiment.

AST/import inspection rejects authority/runtime/native execution dependencies, network modules, dynamic imports, subprocess/shell, file opening, solver, restore and installation calls. A patched solver/restore owner that throws remains uncalled. No registry, filesystem discovery, source parsing, installation, signing or trust is present.

## Validation

Final runs:

| Suite | Result |
|---|---|
| P14.5 focused capability contracts | 23/23 PASS |
| P14.4 namespace/export regression | 23/23 PASS |
| P14.3 lock/restore regression | 28/28 PASS |
| P14.2 solver regression | 38/38 PASS |
| P14.1 manifest regression | 36/36 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 148/148 PASS |

The focused suite covers all graph requirements, exact matching/content/edge binding, missing/invisible/self/ambiguous providers, duplicate/malformed input, lock substitution, symbol distinction, authority noninvocation/passivity, provenance, version separation, canonical diagnostics/results/fingerprints, producer immutability, forbidden solve/restore calls, forged success rejection, large chain and static separation.

Frozen coexistence: `authority_consolidation_smoke_test.main()` PASS (canonical owner re-exports, exact grants and principal/capability/resource denial, authorized existing RuntimeEngine execution, transactional denied execution). That frozen test executes its existing runtime fixture outside the P14.5 module; it does not imply package validation executes.

No focused or regression test failed; no Patch Matrix code repair was necessary.
A read-only documentation search used literal Windows wildcards and failed: TEST_INVOCATION_DEFECT. Source files and authority smoke behavior supplied the needed evidence; no frozen file was edited for that search.

## Deferrals and invariants

No capability versions, provider qualification, optional requirements, runtime permission enforcement, signing/integrity/trust, cache, registry, publishing, installation or package execution. No P14.6/P15 work.

DECLARED_CAPABILITY != AUTHORITY; REQUIRED_CAPABILITY != AUTHORIZATION; CAPABILITY_COMPATIBILITY != PERMISSION; PACKAGE_CAPABILITY != PRINCIPAL_CAPABILITY_GRANT; PACKAGE_CAPABILITY != ROLE; PACKAGE_CAPABILITY != AUTHORITY_DECISION; EXPORTING_CAPABILITY != AUTHORIZED_EXECUTION; REQUIRING_CAPABILITY != ENTITLEMENT; COMPATIBLE != TRUSTED; PACKAGE_CAPABILITY_REFERENCE != NEW_AUTHORITY_CAPABILITY; PACKAGE_VERSION != CAPABILITY_VERSION; CAPABILITY_VALIDATION != DEPENDENCY_SOLVING; CAPABILITY_PROVENANCE != AUTHORITY; CAPABILITY_PROVENANCE != TRUST.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P14_5_INCOMING_CANDIDATES=12
P13_REOPENED=False
P14_DECLARED_CAPABILITY_IS_AUTHORITY=False
P14_REQUIRED_CAPABILITY_IS_AUTHORIZATION=False
P14_CAPABILITY_PROVIDER_CONTENT_BOUND=True
P14_CAPABILITY_MATCHING=EXACT_IDENTITY
P14_MISSING_REQUIRED_CAPABILITY_FAILS_CLOSED=True
P14_CAPABILITY_VALIDATION_GRANTS_AUTHORITY=False
P14_CAPABILITY_VALIDATION_INVOKES_AUTHORITY_ENGINE=False
P14_CAPABILITY_TRUST_VALIDATION=False
P14_CAPABILITY_VALIDATOR_RESOLVES_PACKAGES=False
P14_PACKAGE_POLICY_ENGINE_IMPLEMENTED=False
P14_CAPABILITY_EXECUTES_AIR=False
P14_CAPABILITY_EXECUTES_RUNTIME=False
P14_CAPABILITY_DISPATCHES_NATIVE=False
P14_CAPABILITY_GRANTS_AUTHORITY=False
P14_CAPABILITY_NETWORK_ACCESS=False
P14_CAPABILITY_FILESYSTEM_DISCOVERY=False
P14_CAPABILITY_HOST_COMMAND_EXECUTION=False
P14_CAPABILITY_CONTRACT_MODEL=PASS
P14_CAPABILITY_REQUIREMENT_VALIDATION=PASS
P14_CAPABILITY_PROVIDER_BINDING=PASS
P14_CAPABILITY_VISIBILITY=PASS
P14_CAPABILITY_AMBIGUITY_HANDLING=PASS
P14_CAPABILITY_LOCK_BINDING=PASS
P14_CAPABILITY_AUTHORITY_BOUNDARY=PASS
P14_CAPABILITY_PROVENANCE=PASS
P14_CAPABILITY_DETERMINISM=PASS
P14_CAPABILITY_SECURITY_BOUNDARY=PASS
P14_CAPABILITY_PROVIDER_VISIBILITY=DIRECT_ONLY
P14_CAPABILITY_VERSIONING_IMPLEMENTED=False
P14_4_REGRESSION=PASS
P14_3_REGRESSION=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
P14_5_READY_FOR_REVIEW=True
```

## Exact Git status and preservation

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/p14_4_package_namespace_export_resolution_test.py
?? apexforge/p14_5_package_capability_contract_test.py
?? apexforge/tooling/package_capabilities.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_namespace.py
?? apexforge/tooling/package_solver.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
?? docs/p14/P14_4_PACKAGE_NAMESPACE_EXPORT_RESOLUTION.md
?? docs/p14/P14_5_PACKAGE_CAPABILITY_CONTRACT.md
```

Exactly fifteen candidates, three new P14.5 files. All twelve incoming hashes preserved. Branch, HEAD, tag object and peeled freeze target unchanged. Empty tracked/cached diff confirms frozen P10/P11/P12/P13 files unchanged. No Python caches/bytecode, executables, libraries, symbols, object files or VSIX generated residue. Nothing staged; no commit/tag/push. Stop at P14.5 review readiness.

