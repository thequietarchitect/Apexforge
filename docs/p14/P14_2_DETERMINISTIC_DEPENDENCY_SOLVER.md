# P14.2 — Deterministic Dependency Solver

Status: **ready for owner review**. This slice implements exact structural package resolution only. No installation, lockfile, trust, registry or package execution is claimed.

## Frozen baseline and incoming custody

Branch: `p14-1-package-identity-manifest`.
HEAD/base and peeled `afp-p13.12-freeze`: `860ba9287ee237ddca0691355607c896f3ea382f`.
P13 annotated tag object: `06484cafbf15c9fe08ccc1c5a45217ad442f16a7`.

Before implementation, exactly three P14.1 candidates were present, tracked/index diffs were empty and no generated residue was found. All incoming hashes were captured:

| Incoming candidate | SHA-256 |
| --- | --- |
| `apexforge/p14_1_package_identity_manifest_contract_test.py` | `3E991E69CF0D3A3C1BE39996B4E1CF3D4F09EBBE134680540980CB74F75791B3` |
| `apexforge/tooling/package_manifest.py` | `5BB81E4F428678BC0099771DB1A43D13428D629C919E238B74E48A642EE04CC7` |
| `docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md` | `B17914226429C79B79A6014C59734701C3DF8DFB243EBEB49B211343E9AEF58D` |

All three hashes remain preserved. P14.1 was not corrected or expanded. The owner's active assignment and current roadmap supersede the stale AGENTS.md stage; its stable safety, frozen-lineage and reviewer-authority rules remain binding.

Three new files comprise this slice:

- `apexforge/tooling/package_solver.py`
- `apexforge/p14_2_deterministic_dependency_solver_test.py`
- this evidence report.

Final total P14 candidate count: **six**.

## Inspected contracts and scope

P14.1 provides immutable PackageManifest, PackageCoordinate, ExactVersion, PackageContentIdentity, content boundaries, exact dependency coordinates, separate declared exported/required capabilities and passive provenance references. It has no dependency kinds, optionality, version ranges, registry ownership, multi-version coexistence or capability-provider binding semantics. Its manifest identity excludes presentation metadata.

Existing frozen `language.modules` provides deterministic module graph/cycle/ordering conventions, but its compiler/import graph is not reused as a package resolver or changed. P14.2 follows the established frozen dataclass, sorted canonical JSON, fixed diagnostic and uppercase/domain-separated SHA-256 conventions. It imports only the P14.1 value-model types, not parsing, project loading, module resolution, runtime or authority owners.

```text
DEPENDENCY_DECLARATION != RESOLUTION
RESOLUTION != INSTALLATION
RESOLUTION != AUTHORIZATION
CANDIDATE_AVAILABILITY != TRUST
SOLVER_SELECTION != AUTHORITY_GRANT
PACKAGE_COORDINATE != PACKAGE_CONTENT_IDENTITY
```

## Explicit candidate universe and duplicate policy

`PackageUniverse(candidates: tuple[PackageManifest, ...])` accepts exact validated P14.1 manifest objects only. Lists, JSON strings/dicts, paths, external providers and other types reject with CANDIDATE_UNIVERSE_INVALID. There is no discovery, environment search path, Git lookup or registry client.

The constructor groups every supplied candidate by its complete coordinate, ordered by namespace/name/numeric release triple/schema. It rejects different content identities at any identical coordinate with PACKAGE_CONTENT_CONFLICT, including conflicts in candidates not reachable from the root. It never uses input order to resolve ambiguity. Different versions may be available in the universe; availability alone does not select them.

Identical canonical records deduplicate. Differing non-identity metadata does not become a tie-breaker: each candidate is represented by an immutable copy with metadata removed, leaving its P14.1 canonical record/content identity unchanged. Original caller manifests and their metadata remain untouched. If canonical records differ despite an equal computed identity, CANDIDATE_IDENTITY_INCONSISTENT rejects; a controlled fingerprint-collision fixture validates that guard.

The universe is caller-supplied evidence of availability, not proof of payload integrity, publisher ownership, authenticity or trust.

## Root and resolved node identity

`solve(root: PackageManifest, universe: PackageUniverse)` accepts a validated root manifest. The root need not already be in the universe: it is explicitly added to the candidate set, with identical root candidates deduplicated and conflicting root contents rejected. A bare coordinate/raw root description is unsupported and rejects ROOT_PACKAGE_INVALID rather than invoking a loader.

`ResolvedPackage` retains the canonical immutable manifest and computes its PackageContentIdentity through the existing P14.1 owner. The coordinate and content address remain separate. A graph binds both the root coordinate and root content identity to an actual node; output records label that node root and all other nodes dependency. These roles are graph classifications, not privileges or installation state.

No UI/process/filesystem handle participates. Canonical metadata stripping applies to the supplied root as well as dependencies; presentation metadata is not lost from or rewritten in the producer object.

## Exact-version and coexistence policy

P14.1's bounded numeric `major.minor.patch` grammar is preserved. Dependencies select that exact coordinate only. There is no range, latest, wildcard, precedence selection, registry preference or alias rewriting.

P14.1 establishes no side-by-side coexistence rule. The narrow fail-closed P14.2 policy therefore admits **one exact version per namespace/name within a solution**, including the root. If reachable declarations require two versions, DEPENDENCY_VERSION_CONFLICT contains their sorted coordinates and all known declaration relationships requiring those coordinates. This remains distinct from same-coordinate/different-content PACKAGE_CONTENT_CONFLICT.

Unrelated available versions do not conflict with a solution. The exact-version test selects 2.0.0 when explicitly required even if 10.0.0 is available. Numeric release order is a canonical ordering key, not a selection/precedence algorithm. Version-range solving is unimplemented.

## Transitive closure and algorithm

The solver builds an ephemeral coordinate index from the supplied canonical universe plus root. A deterministic heap frontier expands each reachable available coordinate once, recording each original requiring -> required declaration. Missing coordinates are recorded but not expanded; no absent manifest's dependencies are guessed. Scheduling membership prevents infinite traversal through cycles.

For `A -> B -> C`, all three nodes and both edges remain. For a diamond `root -> A,B; A -> C; B -> C`, C is resolved once and both incoming relationships are retained:

```text
GRAPH_NODE_DEDUPLICATION != EDGE_DELETION
```

After total known expansion, the solver checks conflicts, missing candidates, self-dependencies and cycles in the fixed priority below. No SAT, backtracking, candidate ranking or version-range infrastructure is needed: exact requirements admit a unique closure or a conflict.

Cycle checking uses iterative DFS with sorted starting coordinates and sorted adjacency. A reported directed cycle is rotated to its least coordinate key and includes the repeated closing endpoint. Direction is preserved; a reverse path is not invented. When multiple cycles exist, the first witness under deterministic DFS is reported, not an assertion that it is the only cycle or a globally enumerated minimal cycle.

The 1,100-node chain/cycle fixtures demonstrate operation beyond Python's ordinary recursion depth without altering recursion/security limits.

Ignoring canonical serialization/hash byte cost, processing uses approximately O(U log U + V log V + E log E) time, with adjacency sorting bounded by O(E log V), and O(U + V + E) structural space, where U is supplied candidates, V reachable required coordinates and E known declaration edges. Canonical manifest copies reuse immutable member/reference values; no payload files are copied or materialized. Universe revalidation and graph integrity validation add constant-pass work over those same structures.

## Missing candidates, self-dependencies and failure priority

Missing exact candidates fail closed with MISSING_DEPENDENCY, the first missing coordinate under the canonical key and all known requiring declarations for it. A similarly named package or another version is never substituted. One missing requirement makes the whole solve invalid.

`A -> A` is SELF_DEPENDENCY, separate from a longer DEPENDENCY_CYCLE. No established package lazy-cycle/runtime semantics exist, so the policy is REJECT.

Deterministic priority is:

1. malformed root/universe;
2. global supplied candidate content conflict/inconsistent identity, including root binding;
3. reachable exact-version conflict (first namespace/name family);
4. missing dependency (first canonical coordinate);
5. direct self-dependency (first canonical coordinate);
6. longer directed cycle (deterministic DFS witness).

The universe constructor may reject before solve is entered. Input order does not change those priorities or the selected witness. Missing dependencies can conceal unknown further conflicts; the diagnostic describes only supplied/known requirements.

A failed solve raises PackageSolverError carrying an immutable SolverDiagnostic. It returns no ResolutionGraph and exposes no valid partial solution or partial lock. Diagnostics are evidence of rejection, not usable install/lock state.

## Resolution graph and edge declaration binding

`ResolutionGraph` contains the root coordinate/content address, immutable node/edge tuples and `apexforge.package-resolution/v1` schema.

`ResolutionEdge` binds:

- requiring PackageCoordinate;
- requiring PackageContentIdentity;
- required PackageCoordinate;
- selected required PackageContentIdentity.

Its declaration fingerprint is derived from the requiring coordinate/content address and the original required coordinate under `apexforge.package-dependency-declaration/v1`. This identifies a declaration in its source manifest; required content selection remains a separate edge field. The source content fingerprint changes if any identity-affecting declaring manifest field changes.

No dependency kind or optionality field is invented. All P14.1 dependency declarations are required and exact.

Graph construction rechecks that the root binding matches a node, node coordinates are unique, one version exists per family, every manifest dependency has its correct edge and endpoint/content identities, no extra/duplicate/forged edge exists, all nodes are reachable from the root, and the graph is acyclic/non-self-dependent. Wrong root identities, disconnected nodes, incomplete edges, mismatched content binding, duplicate nodes/edges, cyclic or multi-version handcrafted graphs reject RESOLUTION_GRAPH_INVALID. A successful result is not merely a loosely assembled node list.

## Canonical ordering and resolution fingerprint

Node order is namespace, name, numeric major/minor/patch, manifest schema, then content fingerprint. Edge order is requiring coordinate key, required coordinate key, then requiring/required content fingerprints. This is deterministic identity order, **not dependency build/install execution order**. The root need not appear first in the node array.

`canonical_record()` preserves all node references/canonical manifests, root/dependency labels, declaration-bound edges and declaration-only capability summary. `canonical_json()` uses sorted keys, ASCII escaping, compact separators, finite values and no repr/timestamps. Returned records are detached and cannot mutate a graph.

The uppercase SHA-256 resolution fingerprint is:

```text
SHA256(UTF8("apexforge.package-resolution-fingerprint/v1" + NUL + canonical_json))
```

It is domain-separated from the P14.1 manifest/content fingerprint and edge-declaration fingerprint. Equivalent independently constructed universes, dependency permutations and metadata-only differences yield identical canonical graphs/fingerprints. Changing resolved content changes the graph identity without changing its coordinate. No host directory, timestamp, local handle, input insertion order or stack trace participates.

This is an in-memory result identity. No lockfile parser/writer, restore contract, frozen-lock mode or persistence format is implemented.

## Capability and provenance propagation

Each node retains its manifest's exported/required capabilities and passive provenance references. Graph summaries provide sorted unions of declared capability names while node records retain package-specific associations.

P14.1 has no required-capability provider binding or satisfaction semantics. Accordingly the result explicitly reports capability compatibility `not_evaluated`; an unprovided declared capability does not trigger an invented rejection or authority grant. CAPABILITY_PROPAGATION=PASS means faithful declaration carriage, not compatibility or authorization success.

```text
CAPABILITY_COMPATIBILITY != AUTHORIZATION
RESOLUTION_PROVENANCE != TRUST_VALIDATION
```

No AuthorityEngine invocation, principal inference, grant, revocation, signature check or provenance rewrite occurs. Node identities refer to already validated manifest declarations, not proof that supplied content digests are authentic or package payloads have been independently verified.

## Diagnostics and immutability

SolverDiagnostic contains fixed code, sorted/deduplicated typed coordinates, sorted content addresses, sorted requiring/required pairs and an ordered cycle path where applicable. Its JSON schema is the versioned resolution schema. Unknown root/universe input text is not echoed; a distinctive sentinel validates the fixed diagnostic boundary.

Validated universe/node/edge/graph/diagnostic records are frozen dataclasses with immutable nested P14.1 objects and tuples. The solver's dictionaries, sets, heap and DFS stack are local implementation state only. All producer manifests, dependencies and provenance remain unchanged after solving.

Diagnostic codes implemented:

```text
CANDIDATE_UNIVERSE_INVALID
ROOT_PACKAGE_INVALID
PACKAGE_CONTENT_CONFLICT
CANDIDATE_IDENTITY_INCONSISTENT
MISSING_DEPENDENCY
DEPENDENCY_VERSION_CONFLICT
SELF_DEPENDENCY
DEPENDENCY_CYCLE
RESOLUTION_GRAPH_INVALID
```

Neither an error record nor a successful graph grants authority or creates installable/trusted package state.

## Security/separation audit

Production imports are only dataclasses, hashlib, heapq, json and the P14.1 manifest value types. The AST audit rejects AIR execution, RuntimeEngine/AuthorityEngine use, native dispatch, host process/shell execution, eval/exec/dynamic import, filesystem glob/walk, package parsing and loader calls.

Under dynamic guards blocking file open, process launch, sockets and parse_manifest, universe construction and solving still succeed and return deterministic equivalent graphs. No paths from dependency names are opened; no installation state, registry/cache, network metadata or executable is accessed. Static and dynamic tests establish that all capability/provenance operations are structural.

## Focused validation and regressions

Final commands/results:

```text
python -X utf8 -B apexforge/p14_2_deterministic_dependency_solver_test.py
38/38 PASS

python -X utf8 -B apexforge/p14_1_package_identity_manifest_contract_test.py
36/36 PASS

python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py
74/74 PASS
```

The final aggregate contains exactly the unchanged 36 P14.1 cases and all 38 solver cases. It ran after the strengthened cycle test; production code was unchanged between the direct P14.1 rerun and final aggregate.

Focused coverage includes root/direct/transitive/diamond closure, node dedup with preserved edges, missing exact coordinates, self/two-node/multi-node/deep cycles, competing-cycle/permutation diagnostics, identical/metadata-only candidates, same-coordinate content conflict including unrelated candidates/root binding, simulated inconsistent equal fingerprints, version conflict/priority/traversal independence, exact selection among available versions, immutable manifest/provenance/capability carriage, declaration binding, canonical ordering/identity/fingerprints, malformed graph integrity, no partial result, no unsupported solving/IO/authority/execution and immutable inputs/results.

Final production SHA-256: `7DC98954A69733853401AC7056F9D5BFE4BE4F0AFA4B5853EFD94122A1D26EA1`.
Final focused-test SHA-256: `C2ED507445BCFD9F8A809338C0B5EB866EBCEE36D9D930E652F4121F91056A47`.

No P14.1 or frozen shared identity assumptions were changed. Its own regression still exercises the original project/document coexistence and source/declared-identity adapters. No full P13/P12 stack or historical P11 stage-specific inventory/freeze harness was rerun. P11 assertion groups used in P14.1 remain historical coexistence evidence, not newly claimed passes here.

## Patch Matrix and review ledger

The initial solver focused run passed 37/37 with no implementation failure; P14.1 passed 36/36 and the initial aggregate passed 73/73.

Coverage review found that a candidate-order test named for cycle diagnostics exercised self-dependency priority only. Classification: **TEST_FIXTURE_DEFECT (coverage gap)**, owning the new P14.2 test. The original assertion was retained under an accurate name and a separate competing-long-cycle permutation gate was added. No production patch or weaker assertion was used. Final focused/aggregate reruns passed 38/38 and 74/74.

Routing: observed coverage gap -> classified owning current test -> preserve P14.1/P13 and older frozen owners -> patch only the new test -> satisfy actual longer-cycle order-independent diagnostic gate -> focused P14.2 -> P14 aggregate including P14.1 -> preservation audit. No current implementation defect, P14.1 contract defect, environmental test failure or unresolved regression remains.

The fail-closed one-version/cycle policies and unevaluated capability compatibility are explicit current contracts, not defects attributed to frozen predecessors. `PATCH_MATRIX=PASS` is limited to the completed current validation/preservation cells.

## Deferred capabilities

| Gap | Disposition |
| --- | --- |
| Lockfile/restore serialization and frozen-lock behavior | DEFER_TO_P14_3 |
| Materialization, cache or installation | Outside this slice; no directories/state written |
| Capability provider/satisfaction rules | DEPENDENCY_CAPABILITY_COMPATIBILITY_GAP; declarations carried, compatibility not evaluated |
| Signing, integrity and provenance trust | DEFER_TO_P14_6 |
| Registry client/server, fetching and remote candidate discovery | DEFER_TO_P14_8 |
| Version ranges, aliases, side-by-side versions, optional/dev/peer/build dependencies | Unsupported by the P14.1 contract; no silent inference |
| Package publication/execution/native package dispatch/P15 | Excluded |

## Evidence-supported markers

```text
P14_BASELINE=P13_12_FREEZE
P14_1_INCOMING_CANDIDATES=3
P13_REOPENED=False
P14_SOLVER_INPUT=EXPLICIT_CANDIDATE_UNIVERSE
P14_SOLVER_DETERMINISTIC=True
P14_SOLVER_EXACT_VERSION_ONLY=True
P14_VERSION_RANGE_SOLVING_IMPLEMENTED=False
P14_DEPENDENCY_CYCLE_POLICY=REJECT
P14_MISSING_DEPENDENCY_FAILS_CLOSED=True
P14_PACKAGE_CONTENT_CONFLICT_FAILS_CLOSED=True
P14_SOLVER_TRUST_VALIDATION=False
P14_SOLVER_EXECUTES_AIR=False
P14_SOLVER_EXECUTES_RUNTIME=False
P14_SOLVER_DISPATCHES_NATIVE=False
P14_SOLVER_HOST_COMMAND_EXECUTION=False
P14_SOLVER_NETWORK_ACCESS=False
P14_SOLVER_FILESYSTEM_DISCOVERY=False
P14_SOLVER_GRANTS_AUTHORITY=False
P14_LOCKFILE_IMPLEMENTED=False
P14_REGISTRY_CLIENT_IMPLEMENTED=False
P14_REGISTRY_SERVER_IMPLEMENTED=False
P14_PACKAGE_INSTALLER_IMPLEMENTED=False
P14_PACKAGE_EXECUTION_IMPLEMENTED=False
P14_DEPENDENCY_GRAPH=PASS
P14_TRANSITIVE_RESOLUTION=PASS
P14_DUPLICATE_REQUIREMENT_HANDLING=PASS
P14_MISSING_DEPENDENCY_HANDLING=PASS
P14_DEPENDENCY_CYCLE_HANDLING=PASS
P14_VERSION_CONFLICT_HANDLING=PASS
P14_CONTENT_CONFLICT_HANDLING=PASS
P14_RESOLUTION_IDENTITY=PASS
P14_RESOLUTION_ORDERING=PASS
P14_RESOLUTION_FINGERPRINT=PASS
P14_RESOLUTION_DIAGNOSTICS=PASS
P14_CAPABILITY_PROPAGATION=PASS
P14_CAPABILITY_COMPATIBILITY_EVALUATED=False
P14_PROVENANCE_PROPAGATION=PASS
P14_SOLVER_SECURITY_BOUNDARY=PASS
P14_1_REGRESSION=PASS
PATCH_MATRIX=PASS
P14_2_READY_FOR_REVIEW=True
```

## Exact final Git status and preservation

```text
?? apexforge/p14_1_package_identity_manifest_contract_test.py
?? apexforge/p14_2_deterministic_dependency_solver_test.py
?? apexforge/tooling/package_manifest.py
?? apexforge/tooling/package_solver.py
?? docs/p14/P14_1_PACKAGE_IDENTITY_MANIFEST_CANONICAL_CONTRACT.md
?? docs/p14/P14_2_DETERMINISTIC_DEPENDENCY_SOLVER.md
```

Six untracked P14 candidates; all three incoming P14.1 hashes preserved. HEAD/base, branch, P13 tag object and peeled target remain unchanged. All 30 P13.12 incoming file-byte hashes are preserved and all tracked/index diffs are empty, preserving P13/P12/P11/P10 including frozen IDE files. No generated residue or build output remains. Nothing staged; no commit, tag, push, P14.3, lockfile, registry access, signing/trust, installation, package execution or P15. Stop after P14.2 review readiness.

