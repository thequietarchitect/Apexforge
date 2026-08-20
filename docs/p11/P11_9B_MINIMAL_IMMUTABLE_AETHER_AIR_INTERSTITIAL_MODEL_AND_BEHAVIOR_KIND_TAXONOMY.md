# P11.9B - Minimal Immutable AETHER-AIR 2.0 Interstitial Model and Behavior-Kind Taxonomy

## Status

Production model slice layered over the frozen P11.9A architecture boundary.

## Purpose

P11.9B introduces the minimal immutable AETHER-AIR 2.0 interstitial representation without moving semantic ownership away from AIR, authority, narrative, Quad-Vector, Parametric Semantic Lattice, runtime, downstream lowering, or future P11.10 advanced semantics.

AETHER-AIR 2.0 represents behavioral intent as data. It does not execute the represented behavior.

## Core model

The canonical model is implemented in `apexforge/aether_air/model.py` and exported through `apexforge/aether_air/__init__.py`.

The core types are:

- `AetherBehaviorKind`
- `AetherIntentParameter`
- `AetherBehaviorIntent`
- `AetherAirRepresentation`
- `CORE_AETHER_BEHAVIOR_KINDS`

The canonical minimal behavior-kind taxonomy is:

1. `behavior.intent`
2. `transformation.intent`
3. `constraint.intent`
4. `projection.intent`

The taxonomy is extensible. Additional behavior kinds may be appended explicitly without changing the meaning or ownership of the canonical core kinds.

These kinds classify non-executing intent only. They do not authorize execution, conditional evaluation, convergence, resolver precedence, lowering, or backend generation.

## Minimal intent record

`AetherBehaviorIntent` contains only:

- `kind_id`
- `intent`
- `parameters`

`AetherIntentParameter` contains only:

- `key`
- `value`

`AetherAirRepresentation` contains only:

- `behaviors`

The B slice deliberately keeps the representation local and minimal. It does not yet attach canonical predecessor references, source identities, evidence, provenance, relationships, validation findings, lowering artifacts, or backend identities.

## Immutability boundary

Behavior kinds, parameters, behavior intents, and representation snapshots are frozen dataclasses. Canonical containers are exact tuples.

Parameter values accept immutable scalar values and recursively immutable tuples only. Mutable lists, mappings, sets, or other mutable containers are rejected at the model boundary.

Construction of a different representation creates a different immutable value. Existing representation snapshots are not mutated in place.

## Ordering contract

The model preserves supplied tuple encounter order for parameters and behaviors.

Encounter order is deterministic representation/inspection order only. It is not semantic priority, resolver precedence, execution order, authorization precedence, convergence ranking, or downstream lowering priority.

## Non-execution contract

P11.9B introduces data only.

The minimal model does not:

- execute or run represented behavior;
- evaluate a condition or predicate;
- branch or select;
- grant or deny authority;
- resolve ambiguity or precedence;
- synchronize or converge Quad-Vector lanes;
- mutate runtime state;
- generate effects;
- normalize or transform source semantics;
- project, lower, compile, emit, or generate backend code;
- discover implementations, load providers, or scan the repository.

The words `transformation` and `projection` in behavior-kind identifiers describe intent categories only. They do not perform transformation or projection.

## P11.9C boundary

P11.9B intentionally does not introduce canonical predecessor references, source-identity records, evidence records, provenance records, or relationship records.

Those remain reserved for P11.9C.

No `source`, `subject`, `identity`, `evidence`, `provenance`, or `relation` field is introduced into the P11.9B core model.

## P11.9D / P11.9E / P11.9G boundaries

P11.9B does not construct AETHER-AIR automatically from semantic-lattice or other predecessor objects. Deterministic construction from explicit validated predecessor inputs remains reserved for P11.9D.

P11.9B does not normalize or transform predecessor semantics. Non-executing transformation and normalization contracts remain reserved for P11.9E.

P11.9B does not project to Optimized AIR or a Native Backend. Explicit downstream projection remains reserved for P11.9G.

## P11.10 boundary

`constraint.intent` may classify preserved constraint intent, but P11.9B does not evaluate, resolve, rank, or invent advanced conditional semantics.

Advanced conditionals, convergence, and Paradox Elevation remain exclusively owned by P11.10.

## Ownership preservation

P11.9B gains no parser ownership, AIR legality/linking authority, authority-policy decision power, narrative validation/execution ownership, Quad-Vector execution/resultant ownership, semantic-lattice construction/validation/mutation ownership, runtime state mutation, serialization authority, CLI command authority, dynamic loader/import privilege, backend code-generation ownership, or Codex privilege.

## Compatibility invariant

P11.9B must layer over the frozen P11.9A and P11.8H contracts without changing existing AIR, authority, narrative, Quad-Vector, semantic-lattice, runtime, CLI, editor, tooling, packaging, serialization, or backend behavior.

## Next stage

P11.9C may introduce canonical predecessor references, identity preservation, evidence, and provenance while preserving this immutable minimal model and all existing ownership boundaries.
