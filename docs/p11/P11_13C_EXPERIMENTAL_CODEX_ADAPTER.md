# P11.13-C â€” Experimental Codex Adapter

## Purpose

P11.13-C implements the roadmap-reserved Experimental Codex Adapter as an
optional, caller-controlled bridge between the frozen P11.13B rich-document
model and the already-frozen P11.8 Codex semantic-lattice advisory path.

It does not introduce a second Codex semantics implementation.

It does not become necessary for deterministic compilation.

## Predecessor

P11.13-C begins from:

`afp-p11-13b-freeze`

at:

`a59e86e3acb22ca963eb4cdc18bdd42562afdd38`

P11.13B remains authoritative for the immutable rich-document/package-tier
model.

## Existing Codex owners

P11.8 already owns the Codex advisory path.

Canonical adaptation is:

`semantic_lattice.authoring.adapt_codex_semantic_lattice_proposal`

Canonical validation is:

`semantic_lattice.validation.validate_codex_semantic_lattice_proposal`

The frozen P11.8 contract requires Codex proposals to:

- use `SemanticLatticeAuthoringSource.ADVISORY`;
- use provider identity `codex`;
- pass through ordinary semantic-lattice construction;
- pass through the same semantic-lattice validation path as other authoring
  sources.

P11.13-C delegates these policies rather than reimplementing them.

## Production owner

The C production owner is:

`rich_documents.codex_adapter`

The package-level `rich_documents.__all__` remains empty.

C therefore adds no package-level export.

## Eligible block kinds

The adapter accepts only these P11.13B block classifications:

1. `semantic-table`
2. `diagram`
3. `world-bible`
4. `character-sheet`
5. `simulation-description`

The adapter does not inspect or parse block content.

`text` blocks are not interpreted by C.

`apex` executable blocks are not interpreted by C.

Executable Apex semantics remain outside the Codex adapter and will later pass
through the canonical Apex compiler.

## CodexDocumentBlockAdvisory

`CodexDocumentBlockAdvisory` is a frozen dataclass containing:

- the exact `ApexDocument`;
- the exact document-owned `ApexDocumentBlock`;
- an existing `SemanticLatticeAuthoringProposal`.

The block must be the exact object stored by the document.

This preserves unambiguous document/block lineage and prevents an equal but
separately constructed block from silently being treated as document-owned.

C does not inspect the proposal's authoring-source/provider policy in this
wrapper.

Those rules remain owned by the existing semantic-lattice Codex adapter.

## Adaptation

`adapt_codex_document_block_advisory` accepts an exact
`CodexDocumentBlockAdvisory` and delegates directly to:

`adapt_codex_semantic_lattice_proposal`

Its result is the existing exact:

`SemanticLatticeSnapshot`

C does not introduce a replacement lattice snapshot.

## Validation

`validate_codex_document_block_advisory` delegates directly to:

`validate_codex_semantic_lattice_proposal`

and receives the existing:

`SemanticLatticeAuthoringValidationReceipt`

C wraps that receipt only to retain exact rich-document lineage.

## CodexDocumentBlockValidationReceipt

The C receipt is a frozen dataclass containing:

- the exact `CodexDocumentBlockAdvisory`;
- the exact existing semantic-lattice authoring validation receipt.

The validation receipt's proposal must be the same object as the advisory's
proposal.

The wrapper does not reinterpret validation results.

## Determinism

Repeated adaptation of the same advisory yields equal canonical semantic-lattice
snapshots.

Repeated validation yields equal immutable wrapper receipts.

The adapter preserves the proposal's lattice, subject tuple, and relationship
tuple identities through the existing P11.8 path.

## Source lineage

C preserves lineage by holding exact immutable document and block objects.

The block therefore retains its existing:

- `block_id`;
- `kind`;
- `content`;
- `SourceSpan`, when present;
- metadata.

C does not create another source-span model.

## No content interpretation

P11.13-C does not interpret:

- semantic-table syntax;
- diagram syntax;
- world-bible syntax;
- character-sheet syntax;
- simulation-description syntax.

The caller supplies an already-constructed P11.8
`SemanticLatticeAuthoringProposal`.

Actual `.apexdoc` parsing and block extraction remain P11.13D.

## Optional/advisory boundary

Using this adapter is caller-controlled.

The absence of Codex adaptation must not make ordinary deterministic
compilation fail.

Codex remains an advisory provider, not a compiler, resolver, validator owner,
authority engine, or runtime.

## No privileged path

C does not modify:

- `semantic_lattice.authoring`;
- `semantic_lattice.validation`;
- semantic-lattice construction;
- rich-document model semantics.

A non-advisory source or non-`codex` provider is rejected by the existing P11.8
Codex functions.

This proves that P11.13-C gains no privileged bypass.

## No parser dependency

C does not depend on a `.apexdoc` parser.

It operates over already-created P11.13B immutable objects.

This allows the specialized optional adapter to remain roadmap-reserved before
P11.13D without forcing parser work into C.

## No integration side effects

P11.13-C does not add:

- ProjectManifest integration;
- project-loader integration;
- CLI integration;
- cache integration;
- TAM integration;
- TAP ownership;
- runtime execution;
- global mutable state;
- network access;
- remote package fetch;
- package-tier authority escalation.

## Public surface

`rich_documents.codex_adapter.__all__` contains exactly five symbols:

- `CODEX_ADVISORY_BLOCK_KINDS`
- `CodexDocumentBlockAdvisory`
- `CodexDocumentBlockValidationReceipt`
- `adapt_codex_document_block_advisory`
- `validate_codex_document_block_advisory`

## P11.13D handoff

After C freezes, P11.13D may introduce the `.apexdoc` parser, executable-block
extraction, and source mapping.

D must not make this optional Codex adapter a required parser or compilation
dependency.