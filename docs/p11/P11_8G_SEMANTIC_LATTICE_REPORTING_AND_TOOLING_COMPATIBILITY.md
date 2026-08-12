# P11.8G - Semantic Lattice Reporting and Tooling Compatibility

## Status

Production reporting projection and compatibility boundary layered over the frozen P11.8F validation contract.

## Purpose

P11.8G adds a deterministic, human-readable, read-only reporting surface for validated semantic-lattice products. Reporting consumes already-produced P11.8F validation receipts and exposes their canonical content without revalidation, reconstruction, adaptation, execution, ranking, authority decisions, mutation, loading, importing, or semantic reinterpretation.

P11.8G does not change existing runtime, narrative, CLI, language-server, Visual Studio, VS Code, build-artifact, project-loader, compiler, AIR, authority, Quad-Vector, or execution behavior.

## Production surface

The implementation lives in `apexforge/semantic_lattice/reporting.py`.

The semantic-lattice package re-exports only:

- `render_semantic_lattice_validation_report`
- `render_semantic_lattice_authoring_validation_report`

Report headings and end markers remain owned by the reporting module and are not elevated into the package-level public surface.

## Validated lattice report

`render_semantic_lattice_validation_report` accepts an exact `SemanticLatticeValidationReceipt`.

The renderer projects, in preserved encounter order:

- lattice axes;
- lattice parameters;
- subject references;
- relationships;
- relationship evidence;
- extension-axis IDs;
- provenance entries;
- completed validation checks.

The report does not call a validation function and does not construct a new semantic-lattice snapshot. The receipt supplied by P11.8F remains authoritative for the fact that the snapshot has already passed P11.8 validation.

## Authoring report

`render_semantic_lattice_authoring_validation_report` accepts an exact `SemanticLatticeAuthoringValidationReceipt`.

The authoring report displays:

- authoring source;
- author identity;
- provider identity;
- the deterministic validated-lattice report represented by the receipt's snapshot receipt.

This makes authoring provenance visible without granting the author or provider any semantic privilege.

## Codex advisory visibility

A validated Codex proposal remains an ordinary P11.8E/P11.8F advisory authoring product.

When its authoring validation receipt is rendered, the report may display:

- `source=advisory`;
- the proposal's author identity;
- `provider_identity=codex`.

Visibility is not authority. Reporting does not give Codex:

- direct lattice mutation;
- admission bypass;
- authority decisions;
- resolver precedence;
- declaration selection;
- Quad-Vector bypass;
- runtime execution;
- implementation loading;
- dynamic import;
- privileged insertion;
- semantic ranking.

The existing P11.8E Codex adapter and P11.8F validator remain the only applicable admission and validation path.

## Determinism and encounter order

The reporter preserves the encounter order already held by the immutable lattice and receipt objects.

It does not sort axes, parameters, subjects, relationships, evidence, provenance, extension axes, or validation checks.

Repeated rendering of the same receipt must produce the same exact string.

The report contains no trailing newline and introduces no repository changes.

## Reporting is not serialization

P11.8G follows the established ApexForge reporting boundary:

- reporting is a human-readable projection;
- reporting is not a persistent wire format;
- reporting is not canonical storage;
- reporting is not an import format;
- reporting is not execution;
- reporting is not validation;
- reporting is not diagnostic conversion.

Any later machine-readable semantic-lattice serialization must be introduced under an explicit contract rather than inferred from this report text.

## Type boundary

Both public renderers require exact P11.8F receipt types.

A validated-lattice report rejects values that are not an exact `SemanticLatticeValidationReceipt`.

An authoring report rejects values that are not an exact `SemanticLatticeAuthoringValidationReceipt`.

The reporting layer therefore observes the frozen validation boundary rather than accepting arbitrary duck-typed or partially constructed objects.

## Existing reporting surfaces

P11.8G does not modify or automatically integrate with:

- `tools/runtime_report.py`;
- `tools/narrative_report.py`;
- the ApexForge CLI;
- runtime diagnostics;
- narrative diagnostics;
- build artifacts;
- project loading;
- Visual Studio tooling;
- VS Code tooling;
- language-server reporting or diagnostics.

Those surfaces remain frozen under their existing contracts.

A later stage may deliberately expose semantic-lattice reporting through tooling, but such integration must remain opt-in and must not create execution or authority semantics.

## Compatibility audit

The P11.8G smoke contract verifies:

1. exact deterministic validated-lattice rendering and empty markers;
2. ordered axes, parameters, subjects, relationships, evidence, and provenance projection;
3. exact receipt type boundaries;
4. Codex advisory author/provider provenance visibility without privilege;
5. no revalidation, reconstruction, adaptation, mutation, execution, or authority behavior;
6. frozen CLI, runtime, tooling, editor, and existing reporter surfaces remain untouched;
7. package-level export containment;
8. repository no-op reporting behavior.

## Ownership boundary

P11.8D remains authoritative for deterministic snapshot construction and structural closure.

P11.8E remains authoritative for source projections and ordinary/advisory authoring adaptation.

P11.8F remains authoritative for semantic-lattice validation receipts, collision checks, provenance integrity, and extension-axis validation.

P11.8G owns only deterministic human-readable projection of those already-produced receipts and its compatibility audit.

P11.7 remains authoritative for executable Quad-Vector synchronization and resultant resolution.

P11.10 remains reserved for advanced convergence and Paradox Elevation semantics.

## Next stage

P11.8H may perform the final P11.8 integration regression and freeze over the complete P11.8A-G semantic-lattice stack without expanding P11.8G reporting into an executable or authoritative subsystem.
