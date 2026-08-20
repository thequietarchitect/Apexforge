# P11-TAM-A â€” Compiler Token Analysis Map Architecture and Traceability Ownership Audit

## Purpose

P11-TAM-A establishes the architecture and ownership boundaries for the
Compiler Token Analysis Map (TAM). This slice is audit-only. It introduces no
TAM runtime/model records, no compiler instrumentation, no new parsing or
semantic behavior, and no mutation of the frozen P11-SRC predecessor.

The audit establishes TAM as **observational, immutable, deterministic, and non-authoritative**.

## Predecessor

P11-TAM-A begins from the frozen P11-SRC-H checkpoint:

`afp-p11-src-h-freeze`
â†’ `a9e677353a7c01dd760bc0a670790efc16a1c7ef`

The Semantic Decision Source-Surface Bridge remains frozen.

## Existing traceability and provenance owners

The repository already contains multiple provenance-bearing subsystems. TAM
must reference these owners rather than replace or reinterpret them.

### Source locations

`language.source.SourceSpan` owns canonical source locations.

Lexers, parsers, narrative source records, semantic-decision source records,
diagnostics, and project metadata already carry or derive exact source spans
and source names.

### AIR source mapping

`language.compiler.SourceMapEntry` and `language.compiler.SourceMap` own the
existing AIR-ID-to-source-span mapping.

Compiler output already returns a `SourceMap`, and project compilation already
merges source maps. TAM must consume this map as evidence; it must not create a
competing source-map authority.

### Declaration ownership and identity

`language.declarations.ProjectDeclarationOwner` owns declaration ownership
metadata.

`language.identities.ProjectDeclaredIdentity` owns the current canonical
declared AIR identity, source name, declaration kind/name, and declaration
span relationships established by its frozen contract.

TAM may trace these identities and owners but must not manufacture replacement
canonical IDs.

### Resolution

The existing resolution-candidate and resolution-context layers own candidate
selection context and resolution evidence. TAM may record which canonical
resolution inputs or outputs participated in a transformation, but it does
not perform name resolution.

### Narrative

The narrative parser, lowering, analysis, graph, validation, execution, and
presentation tracks remain their own semantic owners. TAM may trace narrative
source-to-semantic transformations but must not reproduce narrative
interpretation or execution.

### Semantic Decision Source-Surface Bridge

P11-SRC owns semantic-decision source AST, parsing, lowering, validation,
analysis, project composition, CLI routing, and LSP diagnostic compatibility.

P11-SRC lowering already emits source provenance and reuses exact frozen
P11.10 semantic-decision objects. TAM may reference those spans, identities,
objects, and provenance records but must not reconstruct semantic-decision
semantics, convergence, or Paradox Elevation.

### AETHER-AIR

AETHER-AIR records, validation, transformation, projection, and reporting
already own their provenance tuples. TAM may preserve links to these existing
records but does not normalize them into a new semantic meaning.

### Semantic Lattice

The semantic lattice already contains the canonical `tam.traceability` axis.

`tam.traceability` remains a passive semantic-lattice axis. P11.8 established
that passive metadata, evidence, or provenance can be projected onto that axis
without fabricating a TAM subject model.

A future canonical TAM subsystem may become a producer of traceability values
that are projected through this frozen adapter contract. It does not alter
the meaning or ownership of the P11.8 axis.

## Canonical TAM trace domains

P11-TAM-A freezes the traceability domains, not the final Python class names.

The domains are:

1. `source`
2. `token`
3. `declaration`
4. `reference`
5. `scope`
6. `type`
7. `authority`
8. `narrative`
9. `ownership`
10. `transformation`

Later TAM slices may define immutable records for these domains after their
shared identity, provenance, producer, ownership, and relationship contracts
are established.

The earlier provisional names such as `TokenTrace`, `SourceTrace`,
`DeclarationTrace`, `ReferenceTrace`, `ScopeTrace`, `TypeTrace`,
`AuthorityTrace`, `NarrativeTrace`, `OwnershipTrace`, and
`TransformationTrace` remain design candidates rather than frozen class names
at TAM-A.

## Transformation seams identified by the audit

TAM can attach observational traceability around stable existing seams,
including:

- `parse_source_unit`
- `compile_source_with_map`
- `compile_source`
- narrative source analysis and lowering
- semantic-decision source analysis and lowering
- semantic-decision project analysis
- existing project/source-map composition

Instrumentation added in later TAM slices must preserve the input/output
semantics of those owners.

## Non-ownership boundary

TAM must not reconstruct compiler or semantic decisions.

Specifically, TAM does not own:

- lexical or parsing semantics;
- declaration or canonical identity generation;
- name/reference resolution;
- type semantics;
- authority decisions;
- narrative semantics;
- semantic-decision semantics;
- convergence policy execution;
- Paradox Elevation assessment or execution;
- runtime execution;
- AIR `SourceMap` meaning;
- AETHER-AIR provenance meaning;
- semantic-lattice provenance meaning;
- the P11.8 `tam.traceability` axis definition.

TAM records provenance relationships around those existing decisions.

## Minimum future TAM record contract

A later TAM model should prefer references and stable identifiers over copied
semantic payloads. At minimum, the architecture anticipates fields capable of
representing:

- stable trace identity;
- trace domain;
- canonical source span or source reference when available;
- producer;
- semantic owner;
- representation/stage;
- schema version;
- existing provenance references;
- upstream trace identities;
- downstream trace identities.

This is an architectural requirement, not a TAM-A implementation.

## TAP Check boundary

P11.11 TAP Check must consume canonical TAM evidence. It must not reconstruct
compiler or semantic decisions from source text, duplicated rules, or inferred
semantics.

TAM is therefore the traceability producer; TAP Check is a later read-only,
diagnostic, observational consumer.

## TAM-A completion condition

P11-TAM-A is complete when:

- the absence of a dedicated TAM implementation is recorded;
- existing provenance and semantic owners are mapped;
- stable compiler/source transformation seams are identified;
- the ten traceability domains are frozen;
- TAM's observational/non-authoritative boundary is frozen;
- `tam.traceability` remains passive and unchanged;
- frozen predecessor production files remain byte/content unchanged relative
  to the P11-SRC-H freeze;
- only the TAM-A audit smoke test and this audit document are introduced.

P11-TAM-B may then define the minimal immutable TAM model without changing the
ownership rules established here.