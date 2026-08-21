# P11.12D â€” Resonance-Layer Immutable Owner-Product Reuse

## Purpose

P11.12D introduces the Resonance-layer reuse boundary on top of the frozen
Capture layer.

The Resonance layer caches existing immutable owner products by reference while
preserving their original semantic ownership.

D does not integrate caching into `ProjectBuilder`, does not add a general
store, does not persist entries, does not execute runtime behavior, and does not
cache Stability-layer products.

## Predecessor

P11.12D begins from:

`afp-p11-12c-freeze`

at:

`1fdf4480cec39f128cbb5961e68025f5fabf2627`

The exact C artifacts and hashes remain frozen.

## Audit findings

The D read-only audit established that all targeted Resonance owner products
are immutable and deterministically repeatable.

The project build surface contains a mixture of layers. In particular,
`ProjectBuild` contains both Resonance products and the Stability-layer
`VerifiedAIRProgram`.

Therefore D does **not** cache the whole `ProjectBuild`.

Instead, it admits the exact individual immutable Resonance products.

## Allowed Resonance products

D accepts exactly thirteen owner-product types:

1. `language.parser.SourceUnitNode`
2. `language.modules.ModuleGraph`
3. `language.modules.ProjectDocumentGraph`
4. `language.compiler.CompiledSource`
5. `language.compiler.SourceMap`
6. `language.declarations.ProjectDeclarationOwnership`
7. `language.identities.ProjectIdentityIndex`
8. `language.resolution_candidates.ProjectResolutionCandidateIndex`
9. `tam.TraceMap`
10. `language.narrative_graph.NarrativeSemanticGraph`
11. `quad_vector.ResultantVector`
12. `semantic_lattice.model.ParametricSemanticLattice`
13. `semantic_lattice.construction.SemanticLatticeSnapshot`

`ProjectBuild`, `VerifiedAIRProgram`, and `RegistryExecutionPlan` are rejected by
the Resonance identity constructor.

The latter two remain Stability work.

## Public module

D is exposed through:

`incremental_cache.resonance`

The frozen top-level P11.12B `incremental_cache.__all__` remains unchanged.

The Resonance module exports:

- `resonance_input_fingerprint`
- `resonance_fingerprint`
- `resonance_dependency`
- `resonance_dependencies_fingerprint`
- `resonance_identity`
- `reuse_or_produce_resonance`

## Structural fingerprints

Most Resonance owners do not expose one shared canonical serialization API.

D therefore defines an observational structural fingerprint encoder for cache
integrity and explicit input identity.

The encoder preserves:

- fully-qualified dataclass type;
- dataclass field order;
- tuple order;
- list order when an explicit owner input contains a list;
- mapping contents in canonical key order;
- set/frozenset contents in canonical encoded order;
- enum type and value;
- exact bytes;
- finite floats;
- decimal values;
- type identity;
- explicit object attributes or slots when encountered.

Cyclic values and unsupported values are rejected.

This encoder does **not** become a semantic serialization format and is not an
artifact interchange contract.

It is cache-owned integrity metadata only.

## Owner type binding

Each allowed type has one canonical D cache owner and artifact kind.

Callers cannot relabel a `TraceMap` as a narrative graph or a `ResultantVector`
as a compiler product.

This prevents a generic cache helper from silently taking semantic ownership.

## Dependencies

`resonance_dependency(CacheEntry)` projects one Capture or Resonance entry into
the P11.12B `CacheDependency` pair:

- cache key;
- artifact fingerprint.

`resonance_dependencies_fingerprint(...)` fingerprints the exact ordered
dependency vector.

Dependency order is significant.

Duplicate dependency keys remain invalid through the P11.12B model.

## Reuse operation

`reuse_or_produce_resonance(...)` requires:

- an allowed exact expected type;
- canonical subject;
- exact input fingerprint;
- exact configuration fingerprint;
- exact ordered dependencies;
- owner producer callback;
- optional cached entry.

On an exact valid hit, the existing `CacheEntry` object is returned and the
producer is not invoked.

On a miss, mismatch, corrupt fingerprint, or wrong value type, the producer is
invoked and its exact result type is required.

The cache does not reinterpret the result.

## Capture â†’ Resonance relationship

The D acceptance test proves AST reuse from the P11.12C token entry.

This demonstrates the first direct three-layer-cache dependency edge:

normalized source text â†’ token Capture entry â†’ AST Resonance entry.

The D test also uses ordered Capture document/token dependencies for project
graph and compiler-sidecar identities.

## Project graph and index products

D individually covers:

- `ModuleGraph`;
- `ProjectDocumentGraph`;
- `SourceMap`;
- declaration ownership;
- identity index;
- resolution-candidate index.

The index products remain owned by their existing language modules.

D does not create a new generalized â€œsymbol table.â€

## Compiler sidecar

`CompiledSource` is admitted because it is the compiler-owned immutable pair of
unverified AIR program plus source map.

Its presence in Resonance does not admit `VerifiedAIRProgram`.

AIR verification remains Stability-layer work.

## TAM

D reuses canonical `TraceMap` values generated from exact existing owner
evidence.

The acceptance path uses `trace_map_from_source_map(...)`.

D does not infer or reconstruct missing TAM semantics.

## Narrative graph

D admits the immutable `NarrativeSemanticGraph`.

The acceptance test constructs it through the canonical
`build_narrative_semantic_graph(...)` producer from an explicit
`NarrativeStory`.

The cache does not own story semantics or narrative validation.

## Quad-Vector

D admits the public immutable `ResultantVector`.

The cache does not run synchronization, convergence, or Quad-Vector execution.

The resultant remains a Quad-Vector-owned product.

## Semantic lattice

D admits both:

- `ParametricSemanticLattice`;
- `SemanticLatticeSnapshot`.

The snapshot remains the canonical construction-owned combination of lattice,
subjects, and relationships.

The cache does not modify lattice relationships, parameters, priority,
validation, or convergence semantics.

## Mixed-layer exclusion

`ProjectBuild` is intentionally excluded even though it is frozen.

Its fields span both Resonance and Stability.

Caching it here would collapse the roadmap layer boundary and could accidentally
reuse verified AIR under a Resonance identity.

Later ProjectBuilder integration must cache/reuse individual layer products
rather than treating `ProjectBuild` as one monolithic cache entry.

## No general store

D still introduces no project-wide dictionary, global singleton, LRU, disk
cache, cache directory, SQLite database, pickle payload, TTL, timestamp
validity, or eviction policy.

The optional candidate entry remains the explicit reuse boundary.

## No ProjectBuilder integration

The audit established the existing ProjectBuilder pipeline:

normalize â†’ module analysis â†’ document graph â†’ per-source compilation â†’
source-map merge â†’ declaration/identity metadata â†’ visibility â†’ link â†’
verification â†’ resolution-candidate index â†’ `ProjectBuild`.

D does not modify that pipeline.

Dependency-aware store/invalidation and builder integration remain later P11.12
slices.

## P11.12E handoff

P11.12E may now implement the Stability layer for the existing canonical
products that actually exist:

- `VerifiedAIRProgram`;
- `RegistryExecutionPlan`.

The architecture audit found no canonical continuity-checkpoint or optimized
artifact owner yet.

E must not fabricate them.

## Closure condition

P11.12D is complete when:

- C freeze ancestry and hashes remain exact;
- B top-level cache surface remains unchanged;
- all thirteen Resonance owner products are accepted;
- mixed-layer `ProjectBuild` is rejected;
- verified AIR and execution plans are rejected from Resonance;
- structural fingerprints are deterministic;
- Capture dependencies feed Resonance identities;
- exact valid hits skip owner invocation;
- corrupt entries are rejected from reuse;
- TAM, narrative, Quad-Vector, and lattice ownership remains external;
- no general store or persistence exists;
- no ProjectBuilder integration occurs;
- no runtime execution occurs;
- predecessor semantic owners remain unchanged.