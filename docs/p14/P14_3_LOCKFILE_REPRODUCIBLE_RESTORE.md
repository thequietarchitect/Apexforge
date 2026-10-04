# P14.3 — Deterministic Lockfile & Reproducible Restore Contract

Review evidence; no closure, release, or freeze operation is performed.

## Baseline and preservation

Branch: `p14-1-package-identity-manifest`.
HEAD and peeled `afp-p13.12-freeze`: `860ba9287ee237ddca0691355607c896f3ea382f`.
Annotated predecessor tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

All six incoming SHA-256 file hashes were captured before editing and confirmed unchanged after testing:

| Incoming candidate | SHA-256 |
|---|---|
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/p14_2_deterministic_dependency_solver_test.py` | `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `apexforge/tooling/package_solver.py` | `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |
| `docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md` | `CAA63ECDB5645110AFBC958EA39DFC5F28157F225728BE1BBC4FC9364682384B` |

Tracked and cached diffs are empty. This verifies no P10/P11/P12/P13 tracked frozen file was changed. No predecessor correction was necessary.

## Lock contract and reused carriers

`PackageLock` is a distinct frozen dataclass containing a validated successful P14.2 `ResolutionGraph`. It is neither a manifest nor installed state. Failed, partial, raw, or wrong-type resolution inputs do not construct it. Construction revalidates the supplied graph rather than trusting its label.

Schema: `apexforge.package-lock/v1`. Solver interpretation is pinned to `apexforge.package-resolution/v1`. Both the solver schema and resolution fingerprint are recorded. Unknown lock or solver schemas reject.

The embedded canonical graph pins root coordinate and root content identity, all resolved node coordinates/content identities, canonical manifests, root/dependency roles, provenance references, declared capabilities, and every dependency edge including its declaration fingerprint. P14.1 content identity is the canonical manifest identity; there is no separate invented manifest hash. Human presentation metadata is stripped by P14.2 and absent from the lock. Package versions remain exact; schema versions are separate.

Nodes and edges inherit P14.2 deterministic coordinate ordering (namespace, name, numeric version components, schema, then content fingerprint); edges order by requiring and required coordinates and content identities. This is ordering, not version selection.

## Canonical serialization and fingerprint

Canonical JSON uses ASCII escaping, sorted keys, compact separators and finite values. Node/edge input permutations normalize through the graph validator. SHA-256 hashes UTF-8 bytes of `apexforge.package-lock-fingerprint/v1`, NUL, then canonical lock JSON. The lock domain is separate from manifest and resolution domains. Root content, dependency content, edge structure and coordinate/version changes alter the fingerprint; equivalent orders do not.

There are no host paths, usernames, timestamps, transport handles or producer object representations. Lock identities do not specify installation paths. A lock fingerprint can be retained externally; this schema does not store a recursively self-hashed fingerprint. The recorded resolution fingerprint is checked on loading.

## Raw parsing and integrity

`parse_lock` accepts supplied JSON text only, bounded to 16 MiB to accommodate substantial flat graphs. It rejects duplicate keys at every depth, nonfinite constants, oversized integer tokens, malformed JSON, invalid Unicode and excessive JSON nesting. It matches P14.1's hardened parsing pattern; the predecessor parser returns a manifest rather than a generic JSON record, so it cannot directly parse lock envelopes. No predecessor refactor was made.

`PackageLock.from_mapping` strictly checks envelope, graph, node and edge keys. Nested package validation delegates to P14.1, including relative content paths, hash/domain and reference validation. Stored manifests must equal their canonical form; metadata or noncanonical nested records are rejected. Node coordinate/content pins, roles, edge declaration hashes, solver capabilities and resolution fingerprint are checked.

P14.2's iterative graph validator verifies unique nodes and edges, root existence/binding, one version per package family, all required targets, exact declaration-derived edge set, acyclicity and complete root reachability. Duplicate/conflicting nodes, detached nodes, missing edges, dangling endpoints, cycles and stale associations fail closed. No usable partial lock or restore plan is returned.

Diagnostics are fixed structured error codes exposed through `PackageLockError.code`, without raw input, object repr or host details. Representative codes distinguish unsupported schema, node/declaration/fingerprint mismatch, graph invalidity, root drift, missing content, substitution and supplied ambiguity. Equivalent invalid inputs yield equal messages.

## Drift and regeneration

`validate_lock_against_root` checks current root coordinate and canonical content identity. Identity includes dependency declarations, so declaration drift is content drift; graph validation independently binds those declarations to locked edges. Presentation-only metadata does not drift. No automatic lock update occurs. A changed successful resolution can create a new immutable lock with a new fingerprint.

## Restore verification and planning

`plan_restore` consumes a validated lock and explicitly supplied P14.2 `PackageUniverse`. The root must be supplied along with dependencies. It revalidates the supplied universe's ambiguity boundary and performs exact locked-coordinate and canonical-content comparisons in lock order. It never calls or imports `solve`, selects alternative versions, discovers files, or fetches content.

Missing exact coordinates produce `RESTORE_CONTENT_MISSING`; same-coordinate changed content produces `RESTORE_CONTENT_SUBSTITUTED`. Candidate content conflicts are rejected by `PackageUniverse` before planning; a forged typed universe is also rechecked and produces `RESTORE_UNIVERSE_AMBIGUOUS`. Global universe ambiguity rejection matches P14.2, including conflicts outside the locked closure. Valid unrelated extra candidates are ignored and cannot enter the plan.

`RestorePlan` is immutable, binds the lock fingerprint/root identity and canonical ordered package references, and records `verification=exact_supplied_identity_match` and `installs_packages=false`. Construction requires exactly the validated locked node sequence. It references immutable canonical records without copying files or changing producers.

Success proves a supplied validated manifest universe matches locked canonical identities. It does not verify physical payload bytes, signatures, ownership, publishers, trust or installation. Those are separate future contracts. Content match is not signature validation; locked declarations are not authority grants. Provenance references remain passive and capabilities retain `compatibility=not_evaluated`.

## Large graphs and security

A 1,100-node chain generates, serializes, parses and verifies a restore plan without recursive graph traversal. A 1,100-node raw cyclic graph rejects without recursion failure. JSON nesting is bounded separately from graph depth; serialized graphs are flat arrays.

The AST audit rejects direct semantic/runtime/native execution, AuthorityEngine, process/shell calls, dynamic payload imports, network modules, file opening, installation and solver calls. A patched execution-owner `solve` that throws remains uncalled during successful and missing-content restore tests. No IO, registry, trust, authorization or producer mutation is implemented by this module.

## Validation

Final exact-file runs:

| Suite | Result |
|---|---|
| `python -X utf8 -B apexforge/p14_3_lockfile_reproducible_restore_test.py` | 28/28 PASS |
| `python -X utf8 -B apexforge/p14_2_deterministic_dependency_solver_test.py` | 38/38 PASS |
| `python -X utf8 -B apexforge/p14_1_package_identity_manifest_contract_test.py` | 36/36 PASS |
| `python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py` | 102/102 PASS |

The 28 focused cases use subtests/loops for root/direct/transitive/diamond graphs, canonical permutations, exact bindings, provenance/capability passivity, metadata exclusion, identity-sensitive hashing, hostile schemas/fields/nodes/edges/JSON, cycle/detached rejection, restore success/missing/substitution/ambiguity/extras, root/declaration drift, immutability, no re-solving, large graphs, deterministic diagnostics and static separation.

No test failure occurred and no Patch Matrix repair was needed. Older frozen suites were not rerun because no shared/frozen module changed.

## Deferred capabilities and explicit boundaries

`MANIFEST != LOCKFILE`; `RESOLUTION_GRAPH != LOCKFILE`; `LOCKFILE != INSTALLED_STATE`; `LOCKFILE != TRUST_DECISION`; `LOCKFILE != AUTHORIZATION`; `RESTORE_PLAN != RESTORE_EXECUTION`; `LOCKED_COORDINATE != TRUSTED_CONTENT`; `CONTENT_MATCH != SIGNATURE_VALIDATION`; `PARSED != VALIDATED`; `STALE_LOCK != UPDATED_LOCK`.

No P14.4 namespaces/exports work, new capability compatibility, signing/trust, cache, registry, publishing, installation, package execution or P15 work. No lockfile filesystem writer, restore materialization or automatic regeneration. Fixed diagnostics intentionally do not echo untrusted payloads.

## Markers

```text
P14_BASELINE=P13_12_FREEZE
P13_REOPENED=False
P14_3_INCOMING_CANDIDATES=6
P14_LOCKFILE_SCHEMA_VERSIONED=True
P14_LOCKFILE_CANONICALIZATION=DETERMINISTIC
P14_LOCKFILE_IMMUTABLE=True
P14_LOCK_ROOT_CONTENT_BOUND=True
P14_LOCK_EXACT_CONTENT_IDENTITIES=True
P14_LOCKED_CONTENT_SUBSTITUTION_FAILS_CLOSED=True
P14_RESTORE_INPUT=EXPLICIT_SUPPLIED_UNIVERSE
P14_RESTORE_RESOLVES_DEPENDENCIES=False
P14_RESTORE_RE_SOLVES=False
P14_RESTORE_INSTALLS_PACKAGES=False
P14_LOCK_PROVENANCE_TRUST_VALIDATION=False
P14_LOCK_EXECUTES_AIR=False
P14_LOCK_EXECUTES_RUNTIME=False
P14_LOCK_DISPATCHES_NATIVE=False
P14_LOCK_GRANTS_AUTHORITY=False
P14_LOCK_NETWORK_ACCESS=False
P14_LOCK_HOST_COMMAND_EXECUTION=False
P14_REGISTRY_CLIENT_IMPLEMENTED=False
P14_REGISTRY_SERVER_IMPLEMENTED=False
P14_PACKAGE_INSTALLER_IMPLEMENTED=False
P14_PACKAGE_EXECUTION_IMPLEMENTED=False
P14_LOCKFILE_MODEL=PASS
P14_LOCKFILE_GRAPH_INTEGRITY=PASS
P14_LOCKFILE_CANONICAL_SERIALIZATION=PASS
P14_LOCKFILE_FINGERPRINT=PASS
P14_LOCKFILE_DRIFT_DETECTION=PASS
P14_RESTORE_PLAN=PASS
P14_RESTORE_MISSING_CONTENT=PASS
P14_RESTORE_SUBSTITUTION_PROTECTION=PASS
P14_RESTORE_AMBIGUITY_PROTECTION=PASS
P14_RESTORE_DETERMINISM=PASS
P14_LOCKFILE_SECURITY_BOUNDARY=PASS
P14_2_REGRESSION=PASS
P14_1_REGRESSION=PASS
P14_3_READY_FOR_REVIEW=True
```

## Exact repository inventory

Final `git status --short --untracked-files=all`:

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/p14_3_lockfile_reproducible_restore_test.py
?? apexforge/tooling/package_lock.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_solver.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
?? docs/p14/P14_3_LOCKFILE_REPRODUCIBLE_RESTORE.md
```

Exactly nine candidate files, three new in this slice. Nothing staged; no commit, tag or push. Generated-residue scan found no Python caches/bytecode, executables, libraries, symbols, object files or VSIX outputs. Stop at P14.3 review readiness.

