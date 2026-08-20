# P11.9D - Deterministic Interstitial Construction from Explicit Validated Predecessor Inputs

## Status

Production construction slice layered over the frozen P11.9C traceability records and P11.9B immutable AETHER-AIR model.

## Purpose

P11.9D composes one explicit canonical `AetherAirRepresentation` with an exact tuple of explicit `AetherIntentTrace` records into one immutable deterministic AETHER-AIR snapshot.

P11.9D is a construction/composition layer only. Inputs are supplied explicitly by callers and are assumed to have passed whatever validation their owning subsystem requires. P11.9D does not discover predecessors, scan the semantic lattice or repository, reinterpret source semantics, normalize or transform behavior, validate semantic truth, execute behavior, or perform downstream lowering.

## Canonical implementation

The implementation lives in `apexforge/aether_air/construction.py` and is exported through `apexforge/aether_air/__init__.py`.

The canonical construction surface contains:

- `AetherAirSnapshot`
- `construct_aether_air_snapshot`

## Snapshot contract

`AetherAirSnapshot` contains exactly:

- `representation`
- `traces`

`representation` is one exact `AetherAirRepresentation`.

`traces` is an exact tuple of `AetherIntentTrace` values.

Construction preserves the exact supplied representation, trace, predecessor, intent, and evidence object identities. It does not clone, replace, normalize, sort, rank, deduplicate, reinterpret, or execute canonical objects.

## Explicit-input boundary

P11.9D accepts only objects explicitly supplied to the constructor.

It does not:

- discover semantic-lattice subjects or relationships;
- scan repository files, modules, registries, plugins, or providers;
- dynamically import implementation providers;
- infer a predecessor from an intent;
- manufacture predecessor identities;
- automatically create `AetherBehaviorIntent`, `AetherPredecessorReference`, `AetherEvidence`, or `AetherIntentTrace` records;
- invoke adapters merely because a source object exists.

Later stages may introduce explicit adapters or other owned integration surfaces, but they must feed ordinary canonical P11.9 objects through the same construction boundary.

## Deterministic encounter order

The trace tuple preserves supplied encounter order exactly.

Construction does not sort by predecessor domain, predecessor kind, source identity, behavior kind, intent text, evidence, provenance, priority, or any other semantic value.

Encounter order is a deterministic inspection/serialization property only. It is not semantic priority, resolver precedence, execution order, authorization precedence, convergence ranking, or lowering priority.

## P11.9F validation/collision/closure boundary

P11.9D performs structural type enforcement at the immutable snapshot boundary, but it does not acquire P11.9F validation, collision, or closure ownership.

In particular, P11.9D does not:

- deduplicate traces;
- reject repeated predecessor references merely because they repeat;
- decide whether multiple traces collide semantically;
- require every trace intent to occur in `representation.behaviors`;
- validate evidence truth or provenance sufficiency;
- select a winner among competing intents.

Those validation, collision, closure, and extension contracts remain reserved for P11.9F.

This means construction preserves explicit caller-supplied canonical objects without silently repairing, removing, ranking, or resolving them.

## P11.9B and P11.9C preservation

P11.9D does not modify the frozen shapes of:

- `AetherBehaviorKind`
- `AetherIntentParameter`
- `AetherBehaviorIntent`
- `AetherAirRepresentation`
- `AetherPredecessorReference`
- `AetherEvidence`
- `AetherIntentTrace`

The snapshot composes those existing objects around their frozen contracts rather than inserting D-stage fields into B or C records.

## P11.9E boundary

P11.9D does not normalize or transform predecessor semantics, intent text, parameters, evidence, or provenance.

Non-executing transformation and normalization contracts remain reserved for P11.9E.

## P11.9G boundary

P11.9D does not project, lower, compile, emit, optimize, or generate Optimized AIR or Native Backend artifacts.

Explicit downstream projection remains reserved for P11.9G or later downstream owners.

## P11.10 boundary

P11.9D does not evaluate advanced conditionals, perform convergence selection or ranking, recompute Quad-Vector resultants, use priority metadata as operative precedence, or create Paradox Elevation semantics.

Those remain exclusively owned by P11.10.

## Immutability boundary

`AetherAirSnapshot` is a frozen dataclass.

The trace container is an exact tuple. Mutable trace containers are rejected.

P11.9D exposes no mutation API and does not mutate the representation or trace records in place.

## Non-operative boundary

P11.9D gains no parser ownership, AIR verification/linker authority, authority-policy decision power, narrative validation/execution ownership, Quad-Vector execution/resultant-resolution ownership, Parametric Semantic Lattice construction/mutation ownership, runtime state mutation, CLI command authority, implementation-provider loading, dynamic import privilege, serialization authority, backend code-generation authority, or Codex privilege.

## Compatibility invariant

P11.9D layers over the frozen P11.9C, P11.9B, P11.9A, and P11.8H contracts without changing predecessor behavior.

## Next stage

P11.9E may introduce explicit non-executing transformation and normalization contracts over canonical AETHER-AIR objects while preserving this deterministic explicit-input construction boundary.
