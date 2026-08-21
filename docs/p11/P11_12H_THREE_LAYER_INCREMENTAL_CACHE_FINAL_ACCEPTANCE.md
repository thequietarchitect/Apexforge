# P11.12H â€” Three-Layer Incremental Cache Final Acceptance

## Purpose

P11.12H closes the P11.12 three-layer incremental-cache milestone only after the
integrated cache demonstrates both semantic correctness and measured build-time
benefit.

The first H read-only probe correctly rejected freeze because the fully warm
cache was slower than an uncached build on the fixed P11.1A
`representative-linked` corpus.

The follow-up profile showed that the cost was not compiler, linker, or
validator work. Those owners were already bypassed. The dominant overhead was
re-validating and structurally re-fingerprinting immutable cached products plus
linear collection lookup.

H therefore optimizes only cache-owned integration bookkeeping.

## Predecessor

P11.12H begins from:

`afp-p11-12g-freeze`

at:

`93b9457f6be864dbc8bb066a193f6fd9942a8c7a`

The G tag remains the historical pre-optimization integration checkpoint.

## Failed pre-optimization acceptance

The first representative-linked probe measured approximately:

- uncached median: 2.613 ms;
- warm median: 4.061 ms;
- warm slowdown: about 55%.

A 31-sample paired reproduction measured an even larger slowdown.

The scale sweep showed the problem worsened with source count, ruling out a
tiny-project crossover as the main explanation.

P11.12H therefore did not freeze at that point.

## Profile result

The warm-path profile identified the dominant costs as:

- `reuse_or_produce_resonance`;
- structural `resonance_input_fingerprint`;
- `CacheCollection.lookup`;
- `reuse_or_produce_stability`;
- `stability_fingerprint`;
- repeated compiler-configuration fingerprints.

The profile demonstrated that the generic integrity checks were recomputing
deep structural fingerprints of already trusted immutable products on every
warm build.

The F collection also intentionally favors simple immutable correctness over
indexed lookup, so repeated warm lookups recalculated cache keys and scanned the
collection.

Those choices are appropriate at the generic layer but unnecessarily expensive
inside one explicit build session that controls all of its own stores and
invalidations.

## H warm-path optimization

H keeps the frozen Bâ€“F model and operational APIs unchanged.

It changes only:

`incremental_cache.integration`

The session now maintains derived, instance-local indexes:

- cache key â†’ `CacheEntry`;
- logical cache slot â†’ cache key;
- entry object identity â†’ cache key.

These indexes are derived from the canonical immutable `CacheCollection`.

They are rebuilt after store or invalidation.

They are never persisted and never become semantic authority.

## Trusted immutable entry fast path

Entries produced by the session are trusted after their generic creation path
has already computed and stored the exact artifact fingerprint.

They therefore do not need their deep immutable owner product to be
re-fingerprinted on every subsequent warm hit.

Externally supplied collection entries are not trusted automatically.

An external `CompiledSource` or `VerifiedAIRProgram` is structurally verified
once before entering the trusted set.

Corrupt or wrong-type external entries are invalidated before reuse.

This preserves the integrity boundary while removing repeated work from normal
session-owned warm builds.

## Fast lookup

On a warm lookup the session first resolves the canonical logical slot.

If the resident identity exactly equals the requested identity, the already
known resident key is used directly and a canonical cache-hit observation is
recorded.

The expensive SHA-256 cache-key projection is therefore avoided on exact warm
hits.

A changed identity still computes its new key, records `stale`, and delegates
physical transitive invalidation to the canonical F `CacheCollection`.

Content-addressed correctness remains unchanged.

## Compiler configuration memoization

The compiler configuration fingerprint depends on:

- compiler contract;
- function-signature contract;
- `allow_headerless_multi_directive`.

Within one explicit build session, repeated equivalent compiler calls now reuse
that configuration fingerprint.

The source-input fingerprint is still recomputed from the exact compiler input
text on every build.

## Verified-AIR warm path

The linker candidate path now finds the resident verified-AIR logical slot
through the session index.

For a trusted exact dependency/configuration match, it reuses the cached
verified program object without structurally re-fingerprinting the
`VerifiedAIRProgram`.

The validator then records the exact Stability hit and returns that same
verified wrapper.

This preserves:

`ProjectBuild.verified.program is ProjectBuild.program`

while avoiding duplicate structural fingerprints.

## What H does not optimize

H does not:

- cache `ProjectBuild`;
- bypass ProjectBuilder module/document/declaration/resolution stages;
- add a standalone AIRProgram cache type;
- mutate semantic owners;
- introduce a global mutable cache;
- persist cache data;
- cache runtime execution;
- weaken dependency invalidation;
- weaken content-addressed identities;
- add a TAP adapter.

## Final performance acceptance

The committed H acceptance test uses the fixed P11.1A
`representative-linked` fixture.

It alternates 31 uncached and fully warm builds and compares medians using
`time.perf_counter_ns`.

The acceptance criterion is deliberately simple:

`warm median < uncached median`

There is no arbitrary percentage threshold.

Every timed warm build must also prove:

- exact ProjectBuild equality;
- zero compiler owner invocations;
- zero linker owner invocations;
- zero validator owner invocations.

This prevents a timing pass from masking semantic or reuse regression.

## One-source changed acceptance

H changes `src/20-adjust.apex` in the representative fixture and requires:

- exact canonical ProjectBuild equality;
- exactly one compiler owner invocation;
- exactly one linker owner invocation;
- exactly one validator owner invocation;
- explicit stale evidence;
- transitive invalidation evidence;
- store evidence;
- unchanged-source hit evidence.

The changed-build timing is reported but is not assigned an arbitrary threshold.

## Three-layer capability census

P11.12 closes with the following implemented families:

### Capture

- exact loaded document/source-byte identity;
- token reuse;
- immutable formatting reuse.

### Resonance

- AST;
- compiled source/source map;
- module/document graph;
- declaration ownership;
- identity index;
- resolution candidate index;
- TAM trace map;
- narrative semantic graph;
- Quad-Vector resultant;
- parametric semantic lattice;
- semantic lattice snapshot.

### Stability

- verified AIR;
- registry execution plan.

The roadmap's story-continuity-checkpoint and optimized-artifact names remain
deferred because no explicit canonical owner exists for either slot.

They are not fabricated in H.

## Operational and integration capability

The milestone also includes:

- structured content-addressed identity;
- dependency-first immutable collection;
- hit/miss/stale lookup;
- dependency-validated store;
- transitive physical invalidation;
- project-source affected closure;
- immutable cache observations;
- explicit instance-local ProjectBuilder integration;
- CLI build/check/run builder compatibility;
- cached-vs-uncached artifact equivalence.

## TAP boundary

Cache observations now provide real optimization evidence.

H still does not modify TAP.

A later roadmap slice may adapt cache-owned evidence into the existing
`optimization-decisions` TAP category while preserving TAP's diagnostic-only
ownership boundary.

## Persistence boundary

P11.12 remains in-memory only.

No correctness decision depends on timestamps, mtimes, process IDs, random
values, disk cache contents, or external state.

## Closure condition

P11.12H is complete only when:

- G freeze ancestry is exact;
- frozen non-integration G artifacts remain exact;
- B top-level cache surface remains unchanged;
- Capture/Resonance/Stability/Operational surfaces remain intact;
- fixed-corpus cold/warm semantic equivalence passes;
- warm compiler/linker/validator owner counts are all zero;
- verified/program identity remains exact;
- build-artifact bytes/fingerprint remain exact;
- the paired representative warm median is faster than uncached;
- no percentage threshold is invented;
- one-source change recompiles/relinks/revalidates exactly once;
- stale/invalidation/store/hit observations are present;
- no new tooling mutation is introduced;
- semantic owners remain unchanged;
- persistence, global mutable cache, ProjectBuild caching, runtime caching, and
  TAP adaptation remain absent.

The final freeze tag is:

`afp-p11-12h-freeze`