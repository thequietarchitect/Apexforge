# P11.9C - Canonical Predecessor References, Identity Preservation, Evidence, and Provenance

## Status

Production record slice layered over the frozen P11.9B immutable AETHER-AIR interstitial model.

## Purpose

P11.9C introduces passive immutable records that trace AETHER-AIR behavioral intent to explicit canonical predecessor identities and evidence without manufacturing replacement identities, automatically constructing AETHER-AIR representations, or moving semantic ownership into AETHER-AIR.

P11.9C preserves source identity and provenance. It does not discover predecessors, reinterpret predecessor semantics, validate semantic truth, execute behavior, or perform downstream lowering.

## Canonical records

The implementation lives in `apexforge/aether_air/records.py` and is exported through `apexforge/aether_air/__init__.py`.

The canonical record types are:

- `AetherPredecessorReference`
- `AetherEvidence`
- `AetherIntentTrace`

## Predecessor-reference contract

`AetherPredecessorReference` contains exactly:

- `source_domain`
- `source_kind`
- `source_identity`

`source_identity` preserves the canonical identifying components supplied by the predecessor domain as an exact immutable tuple of non-empty strings.

The reference is trace metadata only. AETHER-AIR does not manufacture replacement AIR, authority, narrative, Quad-Vector, TAM, Parametric Semantic Lattice, runtime, backend, or other canonical identities.

A predecessor object that has no canonical identity field must not be assigned a fabricated identity merely to enter AETHER-AIR.

## Evidence and provenance contract

`AetherEvidence` contains exactly:

- `kind`
- `facts`
- `provenance`

Evidence is passive and immutable. Facts are exact key/value tuples. Values accept immutable scalar values and recursively immutable tuples only. Provenance is an exact tuple of non-empty strings.

P11.9C preserves evidence supplied by predecessor owners. It does not validate the semantic truth of that evidence and does not convert evidence into executable instructions, condition results, priority, resolver precedence, convergence selection, or backend behavior.

## Intent-trace contract

`AetherIntentTrace` contains exactly:

- `predecessor`
- `intent`
- `evidence`

`predecessor` is an exact `AetherPredecessorReference`.
`intent` is an exact P11.9B `AetherBehaviorIntent`.
`evidence` is an exact tuple of `AetherEvidence` values.

Trace construction preserves the exact supplied predecessor, intent, and evidence object identities and encounter order.

An intent trace means only that an AETHER-AIR intent is traceable to an explicit predecessor source. It does not mean that the predecessor caused execution, authorized execution, selected a branch, won precedence, converged, or was lowered.

## Relationship boundary

P11.9C does not introduce a general-purpose arbitrary AETHER-AIR relationship graph or a free-form `relation` field.

P11.8C required generic source-to-source relationships because the Parametric Semantic Lattice is itself a relationship/indexing structure. AETHER-AIR has a narrower role: preserving traceability from explicit predecessor identity to non-executing behavioral intent.

The P11.9B reservation of relationship records permits P11.9C to define the required trace topology; it does not require AETHER-AIR to duplicate the lattice relationship model.

If a later P11.9 slice requires additional typed relationships, that capability must be introduced explicitly without changing predecessor ownership or acquiring resolver semantics.

## Resultant and identity boundary

A predecessor output without a canonical identity field may be represented through evidence and provenance only.

In particular, P11.9C must not fabricate a canonical identity for a Quad-Vector `ResultantVector`. Resultant coordinates, contribution-derived facts, and provenance may be preserved as passive evidence while P11.7 remains the owner of Quad-Vector synchronization and resultant resolution.

## Immutability and ordering

Predecessor references, evidence records, and intent traces are frozen dataclasses.

Canonical containers are exact tuples. Mutable source-identity containers, mutable evidence collections, and mutable evidence values are rejected.

Encounter order is preserved deterministically for inspection and traceability. Encounter order is not semantic priority, resolver precedence, execution order, authorization precedence, convergence ranking, or lowering priority.

## P11.9B preservation

P11.9C does not modify the frozen P11.9B core record shapes:

- `AetherBehaviorKind`
- `AetherIntentParameter`
- `AetherBehaviorIntent`
- `AetherAirRepresentation`

In particular, `AetherAirRepresentation` remains a minimal local behavior container during P11.9C.

## P11.9D boundary

P11.9C intentionally does not add automatic construction, adapter discovery, semantic-lattice scanning, implicit source conversion, or trace collections to `AetherAirRepresentation`.

P11.9D remains responsible for deterministic interstitial construction from explicit validated predecessor inputs. P11.9D may compose the frozen P11.9B model with P11.9C trace records while preserving all identity, evidence, provenance, immutability, ordering, and ownership contracts frozen here.

## P11.9E / P11.9G / P11.10 boundaries

P11.9C does not normalize or transform predecessor semantics. That remains P11.9E.

P11.9C does not project, lower, compile, emit, or generate Optimized AIR or Native Backend artifacts. That remains P11.9G or later downstream owners.

P11.9C does not evaluate advanced conditionals, introduce convergence selection/ranking, recompute Quad-Vector resultants, or create Paradox Elevation semantics. Those remain P11.10.

## Ownership preservation

P11.9C gains no parser ownership, AIR verification/linker authority, authority-policy decision power, narrative validation/execution ownership, Quad-Vector execution/resultant-resolution ownership, Parametric Semantic Lattice construction/mutation ownership, runtime state mutation, CLI command authority, implementation-provider loading, dynamic import privilege, serialization authority, backend code-generation authority, or Codex privilege.

Existing predecessor domains remain authoritative for the identities, evidence, provenance, and semantics they own.

## Compatibility invariant

P11.9C layers over frozen P11.9B, P11.9A, and predecessor contracts without changing existing AIR, authority, narrative, Quad-Vector, semantic-lattice, runtime, CLI, editor, tooling, packaging, serialization, or backend behavior.

## Next stage

P11.9D may introduce deterministic AETHER-AIR construction from explicit validated predecessor inputs while preserving the frozen P11.9B model and P11.9C reference/evidence/provenance contracts.
