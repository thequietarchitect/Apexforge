# P11.12E â€” Stability-Layer Verified-AIR and Execution-Plan Reuse

## Purpose

P11.12E implements the existing Stability products that were confirmed by the
P11.12A and P11.12E audits:

- `air.model.VerifiedAIRProgram`;
- `workflow.air_runner.RegistryExecutionPlan`.

E does not fabricate roadmap slots for which ApexForge has no canonical owner.

In particular, E does not relabel:

- `NarrativeExecutionState` as a story continuity checkpoint;
- `CanonicalBuildArtifact` as an optimized artifact;
- `AetherAirSnapshot` as an implicit Stability-layer product.

## Predecessor

P11.12E begins from:

`afp-p11-12d-freeze`

at:

`d961e7b02f029c2df8fdba44d4db0387b567b9b5`

The exact D artifacts and hashes remain frozen.

## Corrected Stability audit

The final read-only audit established the canonical verified-AIR path:

`language.validation.runtime_validator.RuntimeValidator.validate`

returns:

`air.model.VerifiedAIRProgram`

`ProjectBuilder` owns a canonical `RuntimeValidator` instance by default and
builds its `verified` field through `_validator.validate(...)`.

The `runtime` package re-exports that same validator class; it is not a second
validator identity.

The adjacent `air.verify.AIRVerifier` is a separate verification surface used
by execution helpers such as `run_air_program`. It does not replace the
ProjectBuilder Stability owner boundary selected by E.

## Verified AIR

`VerifiedAIRProgram` is a frozen dataclass containing one field:

`program`

E binds it to:

- layer: `stability`;
- artifact kind: `verified-air`;
- owner: `air.model`.

The input identity is expected to fingerprint the exact linked AIR program.

The configuration identity is expected to fingerprint the validation
contract/configuration, including anything that can change validation output.

The cache does not claim verification authority.

On a miss, the caller supplies the canonical validator producer.

On an exact valid hit, that producer is not invoked.

## Execution plan

`RegistryExecutionPlan` is a frozen dataclass containing:

- `program`;
- `entry_directive`;
- `directive_owners`.

E binds it to:

- layer: `stability`;
- artifact kind: `execution-plan`;
- owner: `workflow.air_runner`.

The canonical owner producer is:

`workflow.air_runner.build_registry_execution_plan(registry, name)`

The final audit distinguished raw source text from executable behavior.

The function contains the text `RuntimeEngine` only in a comment describing
where an unresolved target may later become a runtime diagnostic.

Its executable body:

- resolves the selected root program;
- resolves reachable registry programs;
- indexes directive ownership;
- coalesces shared principals;
- links the selected programs;
- constructs `RegistryExecutionPlan`.

It does not construct `RuntimeEngine`, call runtime execution, or verify AIR.

Runtime verification/execution remains in the later `run_air_program` path.

## Structural fingerprint reuse

P11.12D already introduced deterministic structural fingerprinting for explicit
cache input evidence.

E reuses that exact cache-owned structural encoder rather than introducing a
second serialization scheme.

This is exposed through:

- `stability_input_fingerprint`;
- `stability_fingerprint`.

`stability_fingerprint` accepts only the two E Stability owner-product types.

## Dependency metadata

E reuses the B/D ordered dependency model through:

- `stability_dependency`;
- `stability_dependencies_fingerprint`.

A Stability identity may therefore carry exact lower-layer Capture or Resonance
entry keys and artifact fingerprints.

Dependency order remains significant.

No dependency graph store exists yet.

## Reuse operation

`reuse_or_produce_stability(...)` requires:

- exact allowed Stability type;
- canonical subject;
- exact input fingerprint;
- exact configuration fingerprint;
- exact ordered dependency tuple;
- owner producer callback;
- optional cached entry.

On an exact valid hit, the same `CacheEntry` is returned without invoking the
producer.

On a miss, mismatch, wrong value type, or corrupt artifact fingerprint, the
producer runs again and must return the exact expected Stability owner type.

## Stability taxonomy

E admits exactly two products:

1. `VerifiedAIRProgram`;
2. `RegistryExecutionPlan`.

It rejects direct Stability identities for:

- raw `AIRProgram`;
- mixed-layer `ProjectBuild`;
- `NarrativeExecutionState`;
- `CanonicalBuildArtifact`;
- `AetherAirSnapshot`.

This keeps the roadmap taxonomy evidence-driven.

## Story continuity checkpoint gap

The read-only owner audit found no production class that canonically owns a
story continuity checkpoint.

`NarrativeExecutionState` remains a runtime narrative-state snapshot.

E does not rename it.

The continuity-checkpoint Stability slot remains deferred until an explicit
semantic owner exists.

## Optimized artifact gap

The read-only owner audit found no production class canonically owning an
optimized artifact.

`CanonicalBuildArtifact` remains an equivalence/build-artifact product, not an
optimization product.

The optimized-artifact Stability slot remains deferred.

## No AETHER-AIR reclassification

`AetherAirSnapshot` is already immutable and deterministic, but the P11.12
three-layer roadmap did not designate it as one of the Stability slots.

E does not silently reclassify it.

## No general store

E adds no:

- project-wide cache dictionary;
- global singleton;
- LRU;
- disk cache;
- SQLite database;
- pickle persistence;
- timestamp/TTL correctness;
- cache eviction;
- background warmup.

The explicit optional candidate entry remains the reuse boundary.

## No ProjectBuilder integration

E does not modify `ProjectBuilder`.

It validates that the canonical ProjectBuilder output and the direct
`RuntimeValidator.validate(...)` output agree for the real project fixture, but
the cache is not inserted into the build path yet.

That integration belongs to later P11.12 work.

## No runtime execution

E never calls:

- `RuntimeEngine.execute`;
- `run_air_program`;
- `run_air_from_registry`.

The execution-plan acceptance test additionally prevents `RuntimeEngine`
construction while the canonical plan producer runs.

## P11.12F handoff

With Capture, Resonance, and the existing Stability products represented, F can
introduce the first operational cache collection and dependency-aware
invalidation/reuse policy.

F must preserve content-addressed correctness:

changed fingerprints make stale entries unreachable even before physical
eviction.

F is also the natural point to introduce cache-owned immutable reuse /
invalidation observation evidence for the later TAP
`optimization-decisions` category.

ProjectBuilder integration still remains G.

## Closure condition

P11.12E is complete when:

- D freeze ancestry and hashes remain exact;
- B top-level cache surface remains unchanged;
- exactly two Stability owner types are admitted;
- verified AIR is produced through the canonical RuntimeValidator path;
- verified AIR exact hits skip validation;
- execution plans are produced through `build_registry_execution_plan`;
- execution-plan exact hits skip plan construction;
- execution-plan production performs no runtime execution;
- corrupt entries are rejected from reuse;
- mixed-layer and surrogate products remain excluded;
- no new Stability semantic owner class is invented;
- no general store or persistence exists;
- no ProjectBuilder integration occurs;
- predecessor semantic owners remain unchanged.