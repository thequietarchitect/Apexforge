# P11.12F â€” Dependency-Aware Operational Cache and Reuse Observations

## Purpose

P11.12F turns the immutable P11.12Bâ€“E cache-entry contracts into the first
operational cache collection.

F remains deliberately functional and in-memory.

It does not integrate with `ProjectBuilder`, persist entries, own semantic
products, execute runtime behavior, or adapt cache observations into TAP.

## Predecessor

P11.12F begins from:

`afp-p11-12e-freeze`

at:

`a68888734c4e20ed8152f1d9c2e08cf76b27eba6`

The exact E artifacts and hashes remain frozen.

## Operational production module

F introduces:

`incremental_cache.operational`

The frozen top-level `incremental_cache.__all__` remains unchanged.

The operational module exports exactly:

- `CacheObservation`
- `CacheCollection`
- `cache_keys_for_subjects`
- `affected_project_sources`

## Functional collection

`CacheCollection` is a frozen dataclass containing an ordered tuple of exact
`CacheEntry` values.

No method mutates the collection.

`store(...)` and `invalidate(...)` return a new `CacheCollection` plus an
immutable `CacheObservation`.

Exact already-resident stores are idempotent and return the same collection.

## Dependency-first invariant

Every stored entry must appear after every dependency declared by its
`CacheIdentity.dependencies`.

For each dependency:

- the dependency key must already exist;
- the resident dependency's `artifact_fingerprint` must exactly equal the
  declared dependency fingerprint.

This gives the collection deterministic dependency-first order and makes later
transitive dependent invalidation straightforward.

## Key uniqueness

Every resident `CacheEntry.cache_key` is unique.

The key remains the P11.12B SHA-256 identity projection.

F does not replace, shorten, alias, or reinterpret that identity.

## Logical slot uniqueness

F defines one operational logical slot as:

- schema version;
- layer;
- artifact kind;
- owner;
- subject.

Only one content-addressed version of that slot may reside in a collection at
one time.

A changed input/configuration/dependency fingerprint therefore creates a new
cache key but cannot silently replace the old resident version.

The caller must explicitly invalidate the old slot before storing the
replacement.

This preserves the distinction between content-addressed correctness and
physical cleanup.

## Lookup

`CacheCollection.lookup(identity)` always computes the requested content key.

It returns:

- `hit` when the exact key is resident and all dependency metadata remains
  valid;
- `stale` when a different version of the same logical slot remains resident;
- `miss` when no resident entry corresponds to the exact key or logical slot.

A stale entry is never returned for reuse.

This is the operational expression of P11.12's core rule:

changed fingerprints make stale cache entries unreachable even before
physical eviction.

## Store

`CacheCollection.store(entry)` requires all declared dependencies to already be
resident and to carry the exact declared artifact fingerprints.

Missing dependencies and fingerprint mismatches are rejected.

An identical resident entry is idempotent.

A different resident version of the same logical slot must be invalidated
before replacement.

## Physical invalidation

`CacheCollection.invalidate(seed_cache_keys)` removes:

1. every resident seed key;
2. every entry that directly depends on an affected key;
3. every transitive dependent of those entries.

Removal order is the collection's existing deterministic dependency-first
order.

Unknown seed keys produce a deterministic no-op.

Physical invalidation is cleanup. It is not the correctness boundary; the
content-addressed identity remains primary.

## Cache observations

`CacheObservation` is a frozen cache-owned evidence record containing:

- operation;
- outcome;
- requested cache keys;
- affected cache keys.

Canonical operations are:

- `store`;
- `lookup`;
- `invalidate`.

Canonical outcomes are:

- `stored`;
- `existing`;
- `hit`;
- `miss`;
- `stale`;
- `invalidated`;
- `noop`.

Observations contain no timestamp, process ID, wall-clock value, random value,
semantic ruling, authority decision, or runtime result.

## TAP boundary

P11.11 already contains the `optimization-decisions` category, but no cache
adapter exists yet.

F intentionally does not modify `tap_check`.

The cache now owns explicit immutable evidence suitable for a later adapter,
but TAP remains purely observational and does not own cache behavior.

## Project-source affected closure

F reuses the canonical `ProjectDocumentGraph` instead of creating a second
dependency graph.

Each `ResolvedImportEdge` already identifies:

- `target_source_name`: imported dependency;
- `importer_source_name`: document that depends on it.

F therefore walks the reverse edge direction:

dependency target â†’ importer.

Given one or more changed physical sources,
`affected_project_sources(...)` returns the changed sources plus every direct
and transitive importer.

The final result is filtered through
`ProjectDocumentGraph.dependency_order`, preserving the accepted
dependency-first project order.

## Subject-to-key projection

`cache_keys_for_subjects(...)` returns resident cache keys whose exact
`CacheIdentity.subject` matches one of the requested subjects, in collection
order.

This is intentionally small.

It does not assume that every project-wide product uses a physical source as
its subject.

P11.12G can combine project change knowledge with explicit cache dependency
edges rather than guessing semantic ownership from names.

## No persistence

F introduces no:

- disk cache;
- cache directory;
- SQLite;
- pickle;
- shelve;
- TTL;
- mtime correctness;
- background warming;
- external process cache;
- global mutable singleton.

Persistence remains outside this slice.

## No ProjectBuilder integration

F does not modify `ProjectBuilder`.

G remains the build-path integration slice.

That separation lets F prove collection and invalidation correctness before
the compiler/build pipeline begins depending on it.

## No runtime execution

F imports no runtime/workflow subsystem and executes no AIR or narrative state.

## P11.12G handoff

G can now integrate the functional collection into project/tooling build paths.

The required correctness primitives already exist:

- exact content keys;
- ordered dependencies;
- Capture reuse;
- Resonance reuse;
- Stability reuse;
- hit/miss/stale lookup;
- dependency-validated store;
- transitive physical invalidation;
- project-source affected closure;
- immutable cache observations.

G must preserve cached-vs-uncached semantic equivalence and should expose cache
reuse without turning cache state into semantic authority.

## Closure condition

P11.12F is complete when:

- E freeze ancestry and hashes remain exact;
- the B top-level cache surface remains unchanged;
- the operational module has exactly four public symbols;
- collection/observation records are frozen;
- entries are dependency-first and key-unique;
- logical slots have only one resident version;
- store rejects missing/mismatched dependencies;
- lookup proves hit, miss, and stale behavior;
- stale entries are never reused;
- invalidation removes transitive dependents deterministically;
- project-source invalidation follows canonical reverse import edges;
- cache observations are immutable and deterministic;
- no TAP adapter is added;
- no persistence/global mutable cache exists;
- no ProjectBuilder integration occurs;
- no runtime execution occurs;
- predecessor semantic owners remain unchanged.