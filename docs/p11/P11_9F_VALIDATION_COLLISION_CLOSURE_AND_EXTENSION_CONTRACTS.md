# P11.9F - Validation, Collision, Closure, and Extension Contracts

## Status

Production validation-hardening slice layered over the frozen P11.9E transformation boundary and frozen P11.9D deterministic construction boundary.

## Purpose

P11.9F validates already-constructed canonical AETHER-AIR snapshots and P11.9E transformation records without replacing B/C/D/E ownership.

P11.9F may reject structural inconsistency. It does not choose winners, resolve ambiguity, rank intents, execute behavior, infer missing semantics, normalize content, or perform downstream lowering.

## Canonical implementation

The implementation lives in `apexforge/aether_air/validation.py` and exports:

- `AetherAirValidationReceipt`
- `AetherAirTransformationValidationReceipt`
- `validate_aether_air_snapshot`
- `validate_aether_air_transformation`

These symbols are re-exported through `apexforge/aether_air/__init__.py`.

## Snapshot validation receipt

`AetherAirValidationReceipt` contains exactly:

- `snapshot`
- `extension_kind_ids`
- `provenance`
- `checks`

The receipt is frozen and preserves the exact validated `AetherAirSnapshot`.

`extension_kind_ids`, `provenance`, and `checks` are exact tuples. Receipt order is deterministic traceability data only and never semantic precedence.

## Behavior-intent collision integrity

A snapshot rejects duplicate exact `AetherBehaviorIntent` values in `representation.behaviors`.

Duplicate rejection is structural integrity only. P11.9F does not rank, merge, deduplicate, reinterpret, or select among distinct behavior intents.

## Extension-kind contract

The frozen core behavior-kind IDs remain those owned by P11.9B.

`validate_aether_air_snapshot` accepts an explicit exact tuple of `AetherBehaviorKind` extension declarations.

Extension declarations must have unique canonical IDs and must not collide with any frozen core kind ID.

Every behavior whose `kind_id` is outside the frozen core taxonomy must reference one of the explicitly supplied extension kind IDs.

The receipt preserves the supplied extension kind IDs in encounter order.

Extension declaration does not create parser ownership, execution semantics, resolver precedence, authority privilege, convergence semantics, or backend meaning.

## Intent-trace collision and closure

A snapshot rejects duplicate exact `AetherIntentTrace` values.

Every trace must point to the exact `AetherBehaviorIntent` object present in `snapshot.representation.behaviors`. Equality with a detached replacement object is insufficient for canonical trace closure.

Trace closure verifies canonical object association only. It does not determine whether the intent is semantically true, preferred, executable, authorized, convergent, or lowerable.

## Predecessor identity collision

A canonical predecessor coordinate is `(source_domain, source_identity)`.

If the same predecessor coordinate appears under conflicting `source_kind` values within one snapshot, validation rejects the snapshot.

Repeated use of the same exact predecessor reference is allowed when its source-kind ownership is consistent.

This collision rule does not choose a winning predecessor, fabricate identity, or reinterpret source-owned semantics.

## Evidence and provenance integrity

Within one intent trace, duplicate exact `AetherEvidence` values are rejected.

Within one evidence record, duplicate provenance entries are rejected.

A snapshot receipt aggregates evidence provenance in trace/evidence/entry encounter order without sorting, ranking, rewriting, or deduplicating canonical inputs.

Provenance remains passive traceability metadata.

## Transformation validation receipt

`AetherAirTransformationValidationReceipt` contains exactly:

- `transformation`
- `source_receipt`
- `result_receipt`
- `checks`

The receipt preserves the exact P11.9E transformation and the exact snapshot validation receipts produced for its source and result.

## Transformation validation

`validate_aether_air_transformation` validates both source and result snapshots through the ordinary P11.9F snapshot validator.

The same explicit extension-kind declarations are applied to both snapshots.

Duplicate entries in transformation-level provenance are rejected.

For the frozen P11.9E operation label `normalization`, source and result canonical payloads must agree exactly: their representations and trace tuples must compare equal. P11.9F does not infer, repair, or choose a normalized target.

Other open transformation labels may carry explicit caller-supplied source/result differences. P11.9F does not judge whether such a transformation is semantically preferable or convergent.

A future normalization rule that intentionally changes canonical content must be introduced explicitly in a later owned contract before F may accept that changed-content normalization form.

## No repair and no selection

Validation never mutates, repairs, removes, inserts, sorts, merges, deduplicates, rewrites, or replaces canonical B/C/D/E objects.

A failed validation raises `ValueError`.

A successful validation returns an immutable receipt over the exact supplied objects.

Collision rejection never becomes resolver precedence or winner selection.

## P11.9G boundary

P11.9F does not project, lower, compile, emit, optimize, serialize for backend execution, or generate Optimized AIR or Native Backend artifacts.

Explicit downstream projection remains reserved for P11.9G or later downstream owners.

## P11.10 boundary

P11.9F does not evaluate advanced conditionals, choose branches, perform convergence selection or ranking, recompute Quad-Vector resultants, use metadata as operative precedence, or create Paradox Elevation semantics.

Those remain exclusively owned by P11.10.

## Non-operative boundary

Validation receipts expose no execute, run, bind, resolve, select, rank, grant, deny, synchronize, normalize, transform, lower, compile, emit, load, import, mutate, or repair methods.

P11.9F gains no parser ownership, AIR verification/linker authority, authority-policy decision power, narrative execution ownership, Quad-Vector execution/resultant-resolution ownership, Parametric Semantic Lattice mutation ownership, runtime state mutation, CLI command authority, implementation-provider loading, dynamic import privilege, serialization authority, backend code-generation authority, or Codex privilege.

## Frozen predecessor preservation

P11.9F layers over the frozen P11.9B model, P11.9C records, P11.9D construction, and P11.9E transformation surfaces without changing their record shapes or construction behavior.

## Compatibility invariant

Existing AIR, authority, narrative, Quad-Vector, Parametric Semantic Lattice, runtime, tooling, and backend behavior remains unchanged.

## Next stage

P11.9G may introduce explicit downstream projection boundaries from validated AETHER-AIR state while preserving F validation receipts as passive structural evidence rather than executable or resolver authority.
