# P11.12G â€” ProjectBuilder and Tooling Cache Integration

## Purpose

P11.12G inserts the P11.12 cache primitives into the real validated project
build path without transferring semantic ownership away from
`language.project.ProjectBuilder`.

G uses the extension seams already present in `ProjectBuilder`:

- compiler injection through `ProjectBuilder._compile_unit -> self._compiler`;
- linker injection through `_linker.link`;
- validator injection through `_validator.validate`.

The private module/document/declaration/resolution pipeline remains canonical and
is recomputed normally.

## Predecessor

P11.12G begins from:

`afp-p11-12f-freeze`

at:

`955e5a39dfc718fca7d29839a81d76a602a5d8cb`

The exact F artifacts and hashes remain frozen.

## Integration owner

G introduces:

`incremental_cache.integration`

with one public symbol:

`IncrementalProjectBuildSession`

The session is explicit and instance-local.

There is no module-global cache and no persistence.

## Why linker alignment is required

`ProjectBuild` has a strict object-identity invariant:

`build.verified.program is build.program`

A warm Stability hit returns the exact previously validated
`VerifiedAIRProgram`, whose `.program` references the previously linked
`AIRProgram`.

If a warm build were to relink into a fresh-but-equal AIR object and then return
the cached verified wrapper, `ProjectBuild` would correctly reject the mismatch.

G therefore uses the existing `ProjectBuilder` linker injection seam to align
the warm linked AIR object with the already-valid Stability entry whenever the
exact current CompiledSource dependency vector matches a resident verified-AIR
entry.

This does not introduce an `AIRProgram` cache entry.

The linked program is reused only as the program already owned by an exact,
integrity-checked `VerifiedAIRProgram`.

On a changed dependency vector the canonical `AIRProgramLinker` runs again.

## Compiler integration

The session injects a compiler-compatible callable through the existing
`ProjectBuilder._compile_unit` seam.

Each `CompiledSource` cache identity includes:

- layer `resonance`;
- canonical compiler owner/type binding from P11.12D;
- source name as subject;
- exact UTF-8 compiler-input text fingerprint;
- compiler call configuration;
- compiler contract metadata.

The project builder may pass module-analysis `masked_source`; G hashes the exact
text actually supplied to the compiler, not the original unmasked source.

A cold or changed compile invokes `compile_source_with_map`.

An exact hit returns the cached `CompiledSource` without invoking the compiler.

## Validator integration

The session injects a `RuntimeValidator`-compatible validator.

Each `VerifiedAIRProgram` identity includes:

- exact linked AIR structural fingerprint;
- ordered CompiledSource cache dependencies;
- the RuntimeValidator contract;
- the current standard-library API/signature contract;
- the linker contract used by the session.

A cold or changed linked program invokes canonical
`RuntimeValidator.validate`.

An exact warm hit returns the cached `VerifiedAIRProgram` without invoking the
validator.

## Content change behavior

When lookup observes a different resident version of the same logical compiler
slot:

1. the stale lookup is recorded;
2. the stale compiled-source key is physically invalidated;
3. F removes every transitive cache dependent, including the old verified-AIR
   entry;
4. the changed source is compiled and stored;
5. the project is canonically relinked;
6. the linked AIR is canonically revalidated and stored.

Unchanged source entries remain reusable.

The focused acceptance case changes one of two sources and requires exactly one
compiler owner invocation.

## ProjectBuilder private pipeline

G does not copy or replace the private project pipeline.

The following continue to run through the canonical ProjectBuilder:

- source normalization;
- module analysis;
- project document graph construction;
- source-map merge;
- declaration metadata;
- module visibility;
- linking when cache alignment is unavailable;
- validation when the Stability entry is unavailable;
- resolution-candidate indexing;
- `ProjectBuild` construction.

This is intentionally narrower than a monolithic cached build.

## Cached-vs-uncached equivalence

G requires:

- exact `ProjectBuild` equality;
- `verified.program is program`;
- exact canonical build-artifact bytes;
- exact canonical build-artifact SHA-256 fingerprint.

The canonical artifact remains an equivalence oracle, not an optimized-artifact
cache slot.

## Tooling integration

The read-only G audit found that CLI `check` and `run` already use a selected /
injected builder, while CLI `build` directly called `_default_project_builder`.

G normalizes only that asymmetry.

`_run_build` now accepts the same optional builder injection and `main` passes
its existing `project_builder` argument into the build command.

Default command behavior remains unchanged when no builder is supplied.

The focused test invokes CLI `build` twice with one explicit
`IncrementalProjectBuildSession` and requires:

- cold artifact bytes equal the canonical uncached artifact;
- warm artifact bytes remain identical;
- the second build invokes no compiler, linker, or validator owner.

## Language server

The G audit found no direct `build_project(...)` or `ProjectBuilder(...)`
callsite inside `language_server`.

G makes no language-server change.

## TAP boundary

Integrated cache observations now exist on real project builds, including
hit/miss/stale/store/invalidate evidence.

G still does not modify `tap_check`.

A later slice may adapt this cache-owned evidence into the already-existing TAP
`optimization-decisions` category without allowing TAP to control cache
behavior.

## No persistence

G remains in-memory only.

There is no disk cache, SQLite store, pickle payload, TTL, mtime correctness,
background warming, or cross-process cache.

## No runtime-execution cache

G caches project compilation/link-alignment/validation only.

It does not cache or bypass `RuntimeEngine`, `ProjectBuild.execute`, narrative
execution, or runtime results.

## P11.12H handoff

H can now perform final incremental-performance acceptance over a fixed corpus.

The comparison can measure:

- uncached validated build;
- cold integrated-cache build;
- fully warm integrated-cache build;
- one-source changed incremental rebuild.

H must retain semantic/artifact equality and should report measured reductions
without inventing an arbitrary percentage threshold.

H is also the appropriate point to complete the P11.12 regression/capability
census and freeze the three-layer cache milestone.

## Closure condition

P11.12G is complete when:

- F freeze ancestry and hashes remain exact;
- the B top-level cache surface remains unchanged;
- the integration module exports exactly one public session type;
- ProjectBuilder semantic-owner files remain unchanged;
- cold integrated build equals uncached canonical output;
- warm build invokes no compiler/linker/validator owner;
- warm verified/program object identity remains valid;
- one-source change recompiles exactly one source;
- stale lookup and transitive invalidation are observed;
- changed build canonically relinks and revalidates once;
- the next unchanged build becomes fully warm;
- canonical artifact bytes/fingerprint remain exact;
- CLI check/run injection remains intact;
- CLI build uses the same optional builder seam;
- default CLI behavior remains regression-compatible;
- no language-server, TAP, persistence, or runtime-execution integration occurs.