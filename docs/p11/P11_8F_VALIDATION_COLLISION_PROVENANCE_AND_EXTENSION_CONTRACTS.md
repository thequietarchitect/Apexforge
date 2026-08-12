# P11.8F - Validation, Collision, Provenance, and Extension Contracts

## Status

Production validation hardening layered over the frozen P11.8E projection/advisory adapters and the frozen P11.8D deterministic construction boundary.

## Purpose

P11.8F validates an already-constructed semantic-lattice snapshot without replacing P11.8D structural ownership. P11.8D remains authoritative for exact snapshot types, duplicate exact subject references, relationship endpoint closure, immutable construction, and deterministic encounter order.

P11.8F adds passive validation for cross-record coordinate integrity, provenance integrity, extension-axis closure, and advisory-source validation receipts.

## Canonical validation surface

The implementation lives in `apexforge/semantic_lattice/validation.py` and exports:

- `SemanticLatticeValidationReceipt`
- `SemanticLatticeAuthoringValidationReceipt`
- `validate_semantic_lattice_snapshot`
- `validate_semantic_lattice_authoring_proposal`
- `validate_codex_semantic_lattice_proposal`

These symbols are re-exported through `apexforge/semantic_lattice/__init__.py`.

## Axis coordinate integrity

Every semantic lattice axis must have a unique canonical ID.

Every parameter axis ID must reference an axis declared by the snapshot lattice.

Every parameter coordinate `(axis_id, key)` must be unique within the snapshot.

The canonical eight core axes must remain present. Any additional axes are preserved as extension axes in encounter order. Validation does not rank, privilege, or interpret an extension axis merely because it exists.

## Source-owned identity collision contract

P11.8D already rejects duplicate exact `SemanticLatticeSubjectReference` values.

P11.8F additionally rejects a source-owned identity coordinate that appears under conflicting subject kinds. The coordinate is the pair of source domain and source identity. This prevents one source-owned identity from being reinterpreted as multiple kinds without inventing a replacement identity.

This is a collision-integrity rule only. It does not choose a winner, resolve ambiguity, establish precedence, or mutate subjects.

## Relationship coordinate integrity

P11.8F rejects duplicate relationship coordinates. A relationship coordinate is the exact source subject, relation label, and target subject.

Within one relationship, duplicate evidence coordinates are also rejected. Evidence coordinates preserve the exact evidence kind, immutable facts, and provenance tuple.

These checks prevent silent duplicate semantic coordinates while preserving exact canonical object identity and encounter order.

## Provenance integrity

Every evidence provenance tuple remains immutable and encounter ordered.

Duplicate provenance entries inside one evidence record are rejected.

A validation receipt aggregates provenance in encounter order without rewriting, sorting, ranking, deduplicating, or interpreting provenance.

Provenance is traceability metadata. It does not grant authority, establish truth, select declarations, or alter execution.

## Extension contract

P11.8F recognizes canonical core axes only by their frozen canonical IDs.

Axes outside the frozen core taxonomy remain extensions. Validation preserves their canonical IDs and reports them through the immutable receipt.

Extension presence does not imply executable semantics, parser ownership, loader privilege, authority-policy behavior, resolver precedence, narrative legality, or convergence behavior.

## Authoring validation

`validate_semantic_lattice_authoring_proposal` routes a neutral P11.8E authoring proposal through the ordinary frozen P11.8E adapter and P11.8D constructor before applying P11.8F validation.

There is no alternative construction path in P11.8F.

## Codex advisory validation

`validate_codex_semantic_lattice_proposal` accepts Codex only through the frozen P11.8E advisory contract:

- the authoring source must be `ADVISORY`;
- the provider identity must be `codex`;
- the proposal must pass the ordinary Codex adapter;
- the resulting snapshot must pass the same P11.8F snapshot validator as every other authoring source.

Codex gains no direct lattice mutation, authority decision, resolver precedence, Quad-Vector bypass, runtime execution, implementation loading, dynamic import, or privileged insertion path.

P11.13-C remains available for a richer optional Experimental Codex Adapter without weakening this P11.8 trust boundary.

## Immutable validation receipts

Validation returns frozen receipt objects.

A snapshot receipt preserves the exact validated snapshot and carries immutable tuples for extension-axis IDs, aggregated provenance, and completed check names.

An authoring validation receipt preserves the exact proposal and its snapshot receipt.

Receipts are passive observations. They do not execute, bind, resolve, select, rank, grant, deny, synchronize, load, import, mutate, or rewrite canonical objects.

## Compatibility boundary

P11.8F layers over P11.8E, P11.8D, P11.8C, P11.8B, P11.8A, and frozen P11.7 without changing their established owners.

P11.8D remains authoritative for structural construction checks.

P11.8E remains authoritative for source projection and the optional Codex advisory adaptation path.

P11.7 remains authoritative for executable Quad-Vector synchronization and resultant resolution.

Priority metadata remains passive, and advanced convergence or Paradox Elevation semantics remain reserved for P11.10.

## Next stage

P11.8G may add reporting/tooling projections and a compatibility audit over the validated lattice without making validation receipts executable or authoritative over their source domains.
