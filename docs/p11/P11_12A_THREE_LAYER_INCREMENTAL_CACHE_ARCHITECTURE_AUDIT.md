# P11.12A â€” Three-Layer Incremental Cache Architecture, Ownership, Keying, Invalidation, and Compatibility Audit

## Purpose

P11.12A establishes the ownership and correctness boundary for the P11.12
three-layer incremental cache before any cache production code exists.

P11.12A is audit-only.

It does not add a cache, alter the compiler, alter project semantics, change
runtime behavior, persist artifacts, or introduce cache-dependent build
results.

## Predecessor

P11.12A begins from the published P11.11 TAP Check close:

`afp-p11-11g-freeze`
â†’ `c05ef70aa9243dbeadee9a9542509348ccf12e39`

P11.11 remains frozen.

## Canonical roadmap contract

P11.12 is the **Three-layer incremental cache**.

The roadmap layers are:

### Capture

- documents;
- source hashes;
- tokens;
- formatting.

### Resonance

- AST;
- symbols;
- TAM;
- narrative graph;
- Quad Vectors;
- semantic lattice.

### Stability

- verified AIR;
- execution plans;
- story continuity checkpoints;
- optimized artifacts.

P11.12 is the roadmap point where major incremental build-time reductions
begin.

## Governing rule

The cache owns reuse metadata.

It does **not** acquire semantic ownership of the values it stores.

A cached `Token` remains lexer evidence.
A cached AST remains parser evidence.
A cached `TraceMap` remains TAM evidence.
A cached `NarrativeSemanticGraph` remains narrative-semantic evidence.
A cached `ResultantVector` remains Quad-Vector evidence.
A cached `SemanticLatticeSnapshot` remains semantic-lattice evidence.
A cached `VerifiedAIRProgram` remains AIR-verifier evidence.
A cached `RegistryExecutionPlan` remains workflow execution-planning evidence.

Cache hit or miss status may affect work performed, but it must never alter the
meaning, identity, order, diagnostics, or serialized build result.

## Existing cache implementation

No dedicated P11.12 incremental-cache production package or module exists at
the A boundary.

This is a stage-boundary fact.

Once P11.12B adds the first cache model, later stages protect A by freeze tag
and hashes rather than rerunning the A absence assertion unchanged.

## Capture-layer owners

### Document snapshot

`tooling.project_loader.LoadedProjectSource` is a frozen dataclass with:

- `name`;
- `path`;
- `source`;
- `source_bytes`.

`load_project` reads each source with `read_bytes()` and then decodes UTF-8.
The exact bytes are therefore already available as the canonical Capture
content boundary.

The filesystem modification time is not required for correctness.

### Source hash

`tooling.build_artifact.construct_build_artifact` already computes:

`sha256(source.source_bytes).hexdigest()`

This exact-byte SHA-256 contract is the canonical content fingerprint anchor
for source-document cache identity.

The existing whole build-artifact fingerprint is not itself an incremental
cache key. It fingerprints the complete canonical build output and is better
used as an equivalence oracle.

### Tokens

`language.lexer.Token` is frozen and contains:

- `kind`;
- `value`;
- `span`.

Tokens may therefore be reused as owner-produced immutable values.

Token cache identity must include the exact source-content fingerprint plus all
lexer configuration that can change token output.

### Formatting

`language_server.formatting.format_document` remains the formatting owner.

Formatting is a Capture-layer tooling product, not compiler semantic evidence.

Its cache key must include document content, formatter contract/version, URI or
other output-relevant subject identity, and formatting options.

The formatter currently returns a tuple containing mapping values; therefore
P11.12 must not assume that every nested object is safe for direct mutable
reference reuse. The cache layer must preserve immutable/canonical
representation at its own boundary without changing formatting ownership.

## Resonance-layer owners

### AST

Ordinary parser AST node dataclasses are frozen.

The canonical ordinary source-unit root is:

`language.parser.SourceUnitNode`

Narrative source parsing remains owned by:

`language.narrative_parser.parse_narrative_source`

Semantic-decision source parsing remains owned by:

`language.semantic_decision_parser.parse_semantic_decision_source`

P11.12 must distinguish source/parser kind in cache identity rather than
treating every source text as one parser mode.

### Module and document dependency graphs

`language.modules.ModuleGraph` is frozen.

`language.modules.ProjectDocumentGraph` is frozen and contains:

- `documents`;
- `resolved_import_edges`;
- `canonical_order`;
- `dependency_order`.

`resolved_import_edges` plus `dependency_order` form the existing canonical
dependency evidence for incremental invalidation.

P11.12 must reuse these facts rather than invent a second import graph.

### Compiler products

`language.compiler.CompiledSource` is frozen and retains:

- compiled AIR program;
- source map.

`language.compiler.SourceMap` is frozen.

These remain compiler-owned products.

### Symbols and project semantic indexes

There is no need for the cache to invent a new global "symbol table" merely
because the roadmap uses the word symbols.

The existing `ProjectBuild` already owns the relevant immutable project
semantic/index products:

- `declaration_ownership`;
- `identity_index`;
- `resolution_candidate_index`.

P11.12 caches those exact owner products or owner-defined successors.

It does not reinterpret them into a competing symbol model.

### TAM

`tam.TraceMap` remains the canonical Compiler TAM trace spine.

The cache may reuse an already-produced exact `TraceMap`.

It must not reconstruct TAM semantics from unrelated data solely to obtain a
cache value.

### Narrative graph

The canonical narrative graph owner is:

`language.narrative_graph.NarrativeSemanticGraph`

It is a frozen dataclass containing story identity, graph nodes, and graph
edges.

The earlier broad audit probe of `narrative.model` was not the canonical module;
the targeted audit resolves that ownership to `language.narrative_graph`.

### Quad Vector

The top-level `quad_vector` public package surface exposes the core public
result model including:

`ResultantVector`

`ResultantVector` is frozen and carries the resultant coordinates,
contributions, and provenance.

The package contains additional frozen internal/integration products, but
P11.12 does not automatically make every internal Quad-Vector object a
cache contract. Cacheable kinds are added only where an explicit owner output
is required by a P11.12 integration path.

### Semantic lattice

The canonical lattice model is:

`semantic_lattice.model.ParametricSemanticLattice`

The canonical constructed snapshot is:

`semantic_lattice.construction.SemanticLatticeSnapshot`

Both are frozen.

The targeted audit corrects the broad-probe assumption that
`SemanticLatticeSnapshot` lived in `semantic_lattice.model`.

## Stability-layer owners

### Verified AIR

`air.model.VerifiedAIRProgram` is frozen.

It is the existing verified-AIR Stability owner.

P11.12 may reuse it only when all source, semantic, configuration, and
dependency fingerprints that produced it still match.

### Execution plan

`workflow.air_runner.RegistryExecutionPlan` is frozen and contains:

- `program`;
- `entry_directive`;
- `directive_owners`.

It is the existing explicit execution-plan owner found by the audit.

Live runtime results and mutable session progression are not execution-plan
cache entries.

### Story continuity checkpoint gap

No canonical production object explicitly owning a **story continuity
checkpoint** was found at the P11.12A boundary.

`NarrativeExecutionState` is an immutable execution-state snapshot, but the
cache must not relabel arbitrary runtime/session state as the roadmap's story
continuity checkpoint.

The Stability kind remains deferred until an explicit semantic owner exists.

### Optimized artifact gap

No canonical production object explicitly owning an **optimized artifact** or
optimization decision was found at the P11.12A boundary.

A canonical build artifact is not automatically an optimized artifact.

P11.12 therefore must not fabricate an optimization product merely to populate
the roadmap slot.

This gap may be resolved by later optimization work or by an explicit owner
introduced under the correct roadmap stage.

## AETHER-AIR note

`aether_air.construction.AetherAirSnapshot` is already a frozen deterministic
owner product.

However, the P11.12 roadmap does not explicitly name AETHER-AIR as one of the
three layer slots.

P11.12A therefore records it as an available immutable downstream product but
does not silently redefine the Stability taxonomy to include it.

A later slice may cache it only through an explicit integration contract.

## Cache identity

A bare source hash is necessary but insufficient for the entire three-layer
cache.

The canonical P11.12 identity must be structured and content-addressed.

At minimum, cache identity must distinguish:

- cache schema/version;
- layer;
- artifact kind;
- semantic owner;
- canonical subject identity;
- exact input/content fingerprint;
- configuration/contract fingerprint;
- ordered dependency identities and fingerprints.

The precise immutable Python model is P11.12B work.

## Fingerprint rules

SHA-256 is the existing canonical hash family for exact source bytes and
build-artifact fingerprints.

P11.12 should reuse that family unless a later requirement proves a need for
another algorithm.

Correctness must not depend on:

- filesystem modification timestamps;
- wall-clock time;
- process ID;
- random values;
- Python memory address;
- object hash randomization;
- cache insertion time.

Those values may be useful for non-semantic housekeeping later, but they may
not decide whether a cached semantic product is valid.

## Configuration fingerprinting

Configuration that can change owner output belongs in the key.

Examples include:

- parser/source kind;
- lexer flags;
- formatting contract/version and options;
- compiler mode;
- project kind;
- entry selection where it affects a derived product;
- generic-lowering configuration;
- relevant semantic schema/version.

A configuration change must naturally produce a different cache identity.

## Dependency invalidation

Correctness should be content-addressed rather than deletion-dependent.

When an input or dependency changes, its fingerprint changes and the previous
derived key becomes unreachable for the new build.

For project dependencies, P11.12 reuses:

- `ProjectDocumentGraph.resolved_import_edges`;
- `ProjectDocumentGraph.dependency_order`.

A changed source invalidates:

1. its content-derived Capture entries;
2. derived Resonance entries for that source;
3. reverse-transitive dependents whose semantic product depends on it;
4. Stability entries whose dependency-key closure includes any changed
   Resonance or verified-AIR input.

Physical eviction of old unreachable entries is a storage-management concern,
not the semantic correctness mechanism.

## In-memory versus persistence

The first implementation should separate the pure immutable cache model and
reuse semantics from persistence.

P11.12B begins with deterministic immutable identity/entry structures.

Early cache operation may be in-memory.

Persistent cache storage is not permitted to become semantically authoritative.
If persistence is added, loading or omitting the persistent store must produce
the same canonical build output.

No timestamp-based TTL is required for semantic validity.

## Cache observations and TAP Check

The cache, not TAP Check, should own any future canonical hit/miss/reuse or
invalidation evidence.

If P11.12 introduces an immutable cache-decision/observation product, TAP may
later receive a read-only adapter for `optimization-decisions`.

That would legitimately fill one of the P11.11 deferred evidence categories
without making TAP own optimization or cache semantics.

P11.12A does not add that product yet.

## Equivalence oracle

`tooling.build_artifact.CanonicalBuildArtifact.fingerprint` is the strongest
existing whole-build byte/canonical equivalence oracle.

For identical project/configuration input:

- uncached build;
- cold-cache build;
- warm-cache build;
- partially invalidated incremental build

must produce semantically equivalent owner outputs and, where the build
artifact contract applies, the same canonical build-artifact fingerprint.

Diagnostics, source-map order, graph order, identity order, AIR order, and TAP
observations must remain deterministic.

## Performance measurement

`tooling.performance_baseline` already measures project load and validated
project build separately.

P11.12 performance acceptance should extend this measurement discipline rather
than invent a new incompatible timing vocabulary.

P11.12A does not freeze an arbitrary percentage target before the incremental
workload is implemented and measured.

The final performance slice must demonstrate a measurable warm/incremental
build reduction on a declared corpus while retaining cached-versus-uncached
semantic equivalence.

## CLI and tooling boundary

Build/check paths may eventually consume an explicitly supplied cache through a
normal build owner.

Diagnostic/read-only commands must not silently compile or execute merely to
populate cache entries.

In particular, `apexforge tap-check .` remains observational and must stay
cache-neutral with respect to prerequisite evidence creation.

## Provisional P11.12 engineering decomposition

The architecture audit supports this implementation decomposition:

- **P11.12A** â€” architecture, ownership, keying, invalidation, compatibility
  audit;
- **P11.12B** â€” minimal immutable cache identity, fingerprint, dependency,
  entry, and layer model;
- **P11.12C** â€” Capture layer: document/source hash, token, formatting reuse;
- **P11.12D** â€” Resonance layer: AST, graph/index, compiler sidecars, TAM,
  narrative, Quad-Vector, and semantic-lattice reuse;
- **P11.12E** â€” Stability layer for currently owned verified AIR and execution
  plans, with continuity-checkpoint and optimized-artifact gaps kept explicit;
- **P11.12F** â€” dependency-aware invalidation, deterministic reuse, and
  cache-owned observation evidence;
- **P11.12G** â€” project-builder/tooling integration and cached-versus-uncached
  semantic/build-artifact equivalence;
- **P11.12H** â€” incremental performance acceptance, final integration,
  regression, and freeze.

This subdivision is the implementation plan derived from the roadmap and audit;
the canonical roadmap requirement remains the three-layer P11.12 stage itself.

## P11.12B handoff

P11.12B should add only the minimal immutable cache model.

It should not yet:

- modify `ProjectBuilder`;
- cache lexer/parser/compiler results;
- write persistent cache files;
- change build output;
- add runtime behavior;
- reinterpret semantic owner products.

The B model should be strict enough to support deterministic keys and future
layer implementations without forcing cache semantics into existing owners.

## Closure condition

P11.12A is complete when:

- the P11.11G predecessor freeze is exact;
- the three roadmap layers are preserved;
- exact existing owner products are identified;
- exact source bytes and SHA-256 are confirmed as the Capture content anchor;
- project dependency evidence is identified;
- the verified-AIR and execution-plan owners are identified;
- the continuity-checkpoint and optimized-artifact gaps remain explicit;
- cache identity rules exclude timestamps and other nondeterministic inputs;
- cache ownership remains metadata/reuse-only;
- the implementation plan is recorded;
- no production code changes.