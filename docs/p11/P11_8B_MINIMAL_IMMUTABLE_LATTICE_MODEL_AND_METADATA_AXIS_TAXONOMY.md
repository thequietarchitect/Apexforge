# P11.8B - Minimal Immutable Lattice Model and Metadata-Axis Taxonomy

## Status

Production model slice layered over the frozen P11.8A architecture boundary.

## Purpose

P11.8B introduces the minimal immutable Parametric Semantic Lattice model without moving semantic ownership away from AIR, authority, narrative, Quad-Vector, runtime, or future P11.10 convergence semantics.

## Core model

The canonical model is implemented in `apexforge/semantic_lattice/model.py` and exported through `apexforge/semantic_lattice/__init__.py`.

The core types are:

- `SemanticLatticeAxis`
- `SemanticLatticeParameter`
- `ParametricSemanticLattice`
- `CORE_SEMANTIC_LATTICE_AXES`

The canonical core axis taxonomy is:

1. `structural.declaration`
2. `narrative.identity_relation`
3. `authority.integrity`
4. `priority`
5. `continuity`
6. `convergence`
7. `causal.provenance`
8. `tam.traceability`

The taxonomy is extensible. Additional axes may be appended explicitly without modifying the meaning or ownership of the canonical core axes.

## Immutability boundary

Axis, parameter, and lattice snapshots are frozen dataclasses. Canonical containers are exact tuples. Parameter values accept immutable scalar values and recursively immutable tuples only.

Mutable lists, mappings, or other mutable containers are rejected at the model boundary.

Construction may create a new lattice snapshot. Existing snapshots are not mutated in place.

## Ordering contract

The model preserves supplied tuple encounter order. That order is deterministic snapshot/serialization/inspection order only.

Encounter order is not semantic priority, resolver precedence, narrative ordering authority, execution order, or authorization precedence.

## Priority metadata boundary

The `priority` axis is passive metadata only. P11.8B does not:

- select declarations;
- rank candidates;
- resolve ambiguity;
- reorder narrative content;
- override visibility;
- grant authority; or
- alter runtime execution order.

## Convergence metadata boundary

The `convergence` axis is passive metadata only. Frozen P11.7 remains the owner of Quad-Vector synchronization and `ResultantVector` resolution.

P11.8B does not resolve lanes, execute modules, generate a resultant, mutate resultant coordinates or provenance, or treat lattice metadata as an execution result.

P11.10 remains the roadmap owner for future advanced conditional, convergence, and Paradox Elevation semantics.

## P11.8C boundary

P11.8B intentionally does not introduce canonical lattice subject references, relationship records, or evidence records. Those remain reserved for P11.8C.

The P11.8B parameter model therefore contains only:

- `axis_id`
- `key`
- `value`

No subject, relation, or evidence field is introduced here.

## Ownership preservation

P11.8B is a metadata model. It gains no parser ownership, AIR legality or linking authority, authority-policy decision power, narrative validation authority, Quad-Vector execution/resolution behavior, runtime state mutation, CLI command authority, dynamic loader/import privilege, or Codex privilege.

## Compatibility invariant

P11.8B must layer over the frozen P11.8A and P11.7 contracts without changing existing AIR, authority, narrative, runtime, tooling, or Quad-Vector behavior.

## Next stage

P11.8C may introduce canonical subject references and relationship/evidence records while preserving this immutable model and all existing ownership boundaries.
