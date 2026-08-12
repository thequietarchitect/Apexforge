# P11.8D - Deterministic Lattice Construction and Indexing

## Status

Production construction/indexing slice layered over the frozen P11.8C record model and P11.8B immutable lattice model.

## Purpose

P11.8D composes canonical P11.8B lattice metadata with canonical P11.8C subject references, relationships, and evidence into one immutable deterministic snapshot.

P11.8D is a construction and indexing layer only. It does not create semantic precedence, execute ApexForge behavior, validate source-domain truth, grant authority, resolve ambiguity, or recompute Quad-Vector convergence.

## Canonical implementation

The implementation lives in `apexforge/semantic_lattice/construction.py` and is exported through `apexforge/semantic_lattice/__init__.py`.

The canonical construction surface contains:

- `SemanticLatticeSnapshot`
- `construct_semantic_lattice_snapshot`
- `subjects_for_domain`
- `subjects_for_kind`
- `subjects_for_identity`
- `relationships_for_relation`
- `relationships_from_subject`
- `relationships_to_subject`

## Snapshot contract

`SemanticLatticeSnapshot` contains exactly:

- one exact `ParametricSemanticLattice`;
- an exact tuple of `SemanticLatticeSubjectReference` values;
- an exact tuple of `SemanticLatticeRelationship` values.

Construction preserves the exact supplied P11.8B and P11.8C object identities. It does not clone, replace, normalize, rank, or reinterpret canonical objects.

## Deterministic encounter order

Subject and relationship tuples preserve supplied encounter order.

Index projections preserve the encounter order of the underlying snapshot. Indexing does not sort by priority, source domain, kind, identity, relation name, evidence, or any other semantic value.

Encounter order is a deterministic inspection/serialization property only. It is not semantic precedence.

## Subject collision rule

A snapshot rejects duplicate canonical `SemanticLatticeSubjectReference` values.

Duplicate rejection is a structural consistency rule. It does not choose one duplicate over another and creates no winner, ranking, precedence, or resolver policy.

## Relationship closure rule

Every relationship source and target must be present in the snapshot subject tuple.

A dangling relationship endpoint is rejected before a snapshot is accepted.

Endpoint closure validates lattice referential integrity only. It does not validate the semantic truth of the relationship, authority eligibility, narrative legality, source resolution, or runtime behavior.

## Subject indexing

P1.8D provides passive projections by:

- source domain;
- source kind;
- source identity.

These projections return existing canonical subject-reference objects from the snapshot. They do not create replacement identities.

## Relationship indexing

P11.8D provides passive projections by:

- relationship label;
- source subject;
- target subject.

These projections return existing canonical relationship objects from the snapshot and preserve their evidence and encounter order.

## Immutability boundary

Snapshots are frozen dataclasses and canonical containers are exact tuples.

P11.8D does not expose mutation methods and does not mutate P11.8B lattice metadata, P11.8C subject references, relationships, or evidence in place.

## Non-operative boundary

P11.8D gains no:

- parser or source-language ownership;
- AIR verification or linking authority;
- declaration resolution or ambiguity policy;
- semantic ranking or priority execution;
- authority-policy decision power;
- narrative validation authority;
- Quad-Vector execution, synchronization, or resultant resolution;
- runtime state mutation;
- CLI command authority;
- implementation-provider loading;
- dynamic import privilege;
- Codex privilege.

## Priority boundary

Priority remains passive lattice metadata.

Construction and indexes do not use priority metadata to sort, select, rank, break ties, resolve ambiguity, alter narrative order, grant authority, or change execution order.

## Convergence boundary

P11.7 remains authoritative for executable Quad-Vector synchronization and resultant resolution.

P11.8D may carry or index convergence-related lattice metadata previously created by canonical inputs, but it does not resolve lanes, generate resultants, or reinterpret resultant provenance.

P11.10 remains reserved for future advanced conditional, convergence, and Paradox Elevation semantics.

## Codex boundary

Codex is intentionally absent from the P11.8D core.

P11.8E may introduce an optional advisory/authoring adapter that accepts Codex-originated proposals alongside other authoring sources. Any such proposal must be translated into ordinary canonical P11.8 objects and enter the same validation/construction boundaries as all other inputs.

Codex must not gain direct snapshot mutation, authority decisions, resolver precedence, Quad-Vector bypass, runtime execution, loader/import privilege, or a privileged insertion path.

A richer specialized Experimental Codex Adapter remains reserved for the later P11.13-C roadmap stage.

## Compatibity invariant

P11.8D layers over the frozen P11.8C, P11.8B, P11.8A, and P11.7 contracts without changing existing AIR, authority, narrative, runtime, tooling, or Quad-Vector behavior.

## Next stage

P11.8E may introduce canonical adapters for AIR, narrative, authority, TAM, and Quad-Vector projections, including the first narrow optional Codex advisory interoperability surface.

Those adapters must feed ordinary P11.8 canonical records and construction paths rather than bypassing them.
