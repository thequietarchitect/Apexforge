# P11.8E - Canonical Projection Adapters and Optional Codex Advisory Adapter

## Status

Production adapter slice layered over the frozen P11.8D deterministic construction/indexing boundary.

## Purpose

P11.8E translates source-owned ApexForge semantic objects into ordinary P11.8 lattice subjects, relationships, evidence, and parameters without replacing source-domain identity ownership.

P11.8E also introduces the first narrow optional Codex advisory authoring surface. Codex-originated proposals are advisory inputs only. They must become ordinary canonical P11.8 objects and pass through the same P11.8D construction and structural validation path as every other authoring source.

## Canonical implementation

The implementation lives in:

- `apexforge/semantic_lattice/adapters.py`
- `apexforge/semantic_lattice/authoring.py`
- `apexforge/semantic_lattice/__init__.py`

The focused contract test is:

- `apexforge/p11_8e_canonical_projection_adapters_codex_advisory_smoke_test.py`

## Source-owned identity rule

P11.8E never fabricates a replacement identity merely to make an object fit the lattice.

Adapters preserve whichever identity surface the source domain actually owns.

### AIR

AIR objects with canonical `id` fields project those IDs.

AIR principal/role forms that own canonical `name` fields preserve those names rather than inventing IDs.

Projection does not change AIR verification, linking, resolution, or execution semantics.

### Authority

`Principal.id` and `AuthorityCheck.id` may project as canonical subject identities.

`AuthorityGrant` has no independent canonical ID. It therefore projects only as passive relationship/evidence metadata and is not assigned a fabricated lattice subject identity.

Projection does not grant, deny, resolve, or evaluate authority.

### Narrative

Narrative objects preserve canonical `NarrativeIdentity(kind, path)` identity exactly.

P11.8E does not replace narrative identity, reorder narrative content, or perform narrative validation.

### Quad-Vector

`QuadVectorInput.identity` may project as a canonical source-owned lattice subject identity.

`ResultantVector` has no identity field. Resultant coordinates, contributions, and provenance therefore project only as passive evidence/provenance and never as a fabricated subject identity.

P11.7 remains authoritative for executable Quad-Vector synchronization and resultant resolution.

### TAM

No canonical ApexForge TAM runtime/model type exists at this stage.

P11.8E may project TAM traceability only as passive `tam.traceability` metadata, evidence, or provenance.

P11.8E must not fabricate a `source_domain="tam"` subject identity or imply that a canonical TAM runtime object exists.

## Codex advisory authoring contract

Codex is integrated as an optional advisory authoring source, not as a privileged semantic domain or trusted runtime authority.

A Codex-originated proposal may supply ordinary P11.8 lattice parameters, subject references, relationships, and evidence through the neutral authoring surface.

Before acceptance, the proposal must be translated into ordinary canonical P11.8 objects and routed through the same P11.8D construction path used by all authoring sources.

Codex gains no direct mutation path to a canonical snapshot.

Codex gains no:

- parser ownership;
- AIR verification or linking authority;
- declaration resolver precedence;
- ambiguity-breaking privilege;
- semantic ranking or priority execution;
- authority grant/deny power;
- narrative validation authority;
- Quad-Vector execution, synchronization, or resultant-resolution bypass;
- runtime state mutation;
- CLI command authority;
- implementation-provider loading;
- dynamic import privilege;
- privileged insertion path.

Codex origin is provenance only. It does not change the semantic authority of the resulting canonical P11.8 objects.

## Authoring-source trust boundary

P11.8E follows the established ApexForge authoring distinction between human, tool, and advisory inputs.

Authoring provenance can be preserved, but source category does not change canonical validation rules and does not create semantic precedence.

An advisory proposal is not weaker or stronger in canonical meaning merely because its authoring source is advisory. It is accepted only after ordinary structural validation.

## P11.8D remains authoritative for construction

P11.8E adapters do not replace P11.8D.

All constructed lattice snapshots remain subject to the frozen P11.8D structural rules, including:

- exact immutable canonical object composition;
- deterministic encounter-order preservation;
- duplicate canonical subject collision rejection;
- relationship endpoint closure;
- passive deterministic indexing;
- no semantic ranking or execution behavior.

Adapter output that violates P11.8D structural invariants is rejected regardless of whether it originated from a human, tool, Codex, or another advisory source.

## Priority boundary

Priority remains passive lattice metadata.

P11.8E adapters and Codex proposals must not use priority metadata to select declarations, reorder narrative content, break ambiguity, grant authority, establish resolver precedence, or alter execution order.

## Convergence boundary

P11.7 remains authoritative for executable Quad-Vector synchronization and resultant resolution.

P11.8E may project already-created convergence/resultant metadata as passive evidence or provenance only.

P11.10 remains reserved for future advanced conditionals, convergence, and Paradox Elevation semantics.

## Immutability and passivity

Adapter results and authoring snapshots remain immutable canonical records.

P11.8E introduces no mutable semantic registry, executor, resolver, loader, runtime state manager, or privileged policy engine.

## Compatibility invariant

P11.8E layers over frozen P11.8D, P11.8C, P11.8B, P11.8A, and P11.7 without changing existing AIR, authority, narrative, runtime, tooling, Quad-Vector, or resolution behavior.

## Later Codex expansion

P11.8E establishes only the narrow canonical advisory interoperability surface.

A richer specialized Experimental Codex Adapter remains reserved for the later P11.13-C roadmap stage and must continue to respect canonical ApexForge validation and trust boundaries.
