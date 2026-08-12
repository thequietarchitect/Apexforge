# P11.8C - Canonical Subject References, Relationships, and Evidence Model

## Status

Production model slice layered over the frozen P11.8B immutable lattice model.

## Purpose

P11.8C introduces passive immutable records for referencing source-owned semantic subjects, relating those subjects, and attaching deterministic evidence without creating replacement identities or moving semantic ownership into the lattice.

## Canonical records

The implementation lives in `apexforge/semantic_lattice/records.py` and is exported through `apexforge/semantic_lattice/__init__.py`.

The canonical record types are:

- `SemanticLatticeSubjectReference`
- `SemanticLatticeRelationship`
- `SemanticLatticeEvidence`

## Subject-reference contract

`SemanticLatticeSubjectReference` contains exactly:

- `source_domain`
- `source_kind`
- `source_identity`

The reference is an indexing projection only. `source_identity` preserves the identifying components supplied by the source domain as an exact immutable tuple.

The lattice does not manufacture a new AIR, narrative, authority, Quad-Vector, runtime, or other canonical identity.

Narrative identities may therefore preserve their canonical `kind` plus `path`. AIR declarations may preserve their canonical AIR IDs. Authority records may preserve their source-owned IDs. Quad-Vector inputs may preserve their canonical input identity.

## Resultant boundary

`ResultantVector` does not own a canonical identity field. P11.8C must not fabricate one.

A resultant may be represented only through passive evidence such as:

- resultant coordinates;
- contribution-derived facts;
- provenance.

P11.7 remains the owner of Quad-Vector synchronization and resultant resolution.

## Evidence contract

`SemanticLatticeEvidence` contains:

- `kind`
- `facts`
- `provenance`

Evidence is passive and immutable. Facts are exact key/value tuples. Values must be immutable scalars or recursively immutable tuples. Provenance is an exact tuple of non-empty strings.

P11.8C does not validate the semantic truth of evidence. It preserves evidence supplied by an owning subsystem for later lattice indexing, inspection, traceability, and validation by later owning stages.

## Relationship contract

`SemanticLatticeRelationship` contains:

- `source`
- `relation`
- `target`
- `evidence`

Both endpoints are exact `SemanticLatticeSubjectReference` values. Evidence is an exact tuple of `SemanticLatticeEvidence` values.

Relationship construction preserves the exact supplied subject and evidence object identities and encounter order.

Relationship names are passive typed labels. They do not grant authority, resolve ambiguity, rank candidates, reorder narrative content, execute modules, synchronize vectors, or mutate runtime state.

## Immutability and ordering

Subject references, evidence, and relationships are frozen dataclasses.

Canonical containers are exact tuples. Mutable source-identity containers, mutable evidence collections, and mutable evidence values are rejected.

Encounter order is preserved deterministically. Encounter order is an inspection and serialization property, not semantic precedence.

## Ownership preservation

P11.8C does not gain:

- parser or source-language ownership;
- AIR verification or linking authority;
- authority-policy decision power;
- narrative validation authority;
- Quad-Vector execution, synchronization, or resultant-resolution behavior;
- runtime state mutation;
- CLI command authority;
- implementation-provider loading or dynamic import privilege;
- Codex privilege or a privileged advisory insertion path.

Existing source domains remain authoritative for the semantics and identities they own.

## P11.8D boundary

P11.8C intentionally does not add subject, relationship, or evidence collections to `ParametricSemanticLattice`.

P11.8D remains responsible for deterministic lattice construction and indexing from explicit canonical inputs. P11.8D may compose the P11.8B lattice model with P11.8C records, but it must preserve the ownership, immutability, identity, evidence, and ordering contracts frozen here.

## Compatibity invariant

P11.8C layers over the frozen P11.8B and P11.7 contracts without changing existing AIR, authority, narrative, runtime, tooling, or Quad-Vector behavior.
