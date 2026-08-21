# P11.13E â€” Rich-Document Semantic Projections

## Purpose

P11.13E adds deterministic, caller-controlled projections for the five
structured non-executable rich-document block kinds introduced in P11.13B:

- semantic tables;
- diagrams;
- world bibles;
- character sheets;
- simulation descriptions.

P11.13E does not create alternate narrative, semantic-lattice, simulation, or
runtime semantics.

## Predecessor

P11.13E begins from:

`afp-p11-13d-freeze`

at:

`878927709a6c2ec37bf47ce84aa467761de6600b`

P11.13D remains authoritative for `.apexdoc` container parsing, exact block
content, executable Apex extraction, and compiler source mapping.

## Production owner

The E production owner is:

`rich_documents.projections`

The package-level:

`rich_documents.__all__`

remains empty.

Every E entry point must therefore be imported explicitly from the projections
module.

## Caller-controlled projection

Projection is never automatic.

A caller must provide:

- an exact `ApexDocument`;
- an exact `ApexDocumentBlock` object owned by that document;
- the projection function matching the block's exact `DocumentBlockKind`.

An equal but separately reconstructed block is rejected.

This keeps projection decisions explicit and preserves unambiguous lineage.

## Projection lineage

Every projected product contains an exact frozen:

`RichDocumentProjectionLineage`

with:

- `document_id`;
- `block_id`;
- the original P11.13D block `SourceSpan`, when present.

Projection does not replace or rewrite the source span.

## Structured-line conventions

All five E grammars are line-oriented.

Common rules:

- blank or whitespace-only lines are ignored;
- no comment syntax exists in E;
- no escaping syntax exists in E;
- encounter order is preserved;
- unknown directives are deterministic projection errors;
- scalar values remain strings;
- no semantic coercion is performed.

Structured projection failures use canonical `BuildDiagnostic` values carried
by `DiagnosticError` with diagnostic stage `parse`.

## Semantic-table grammar

A semantic-table block contains one or more columns followed by zero or more
rows:

```text
column <id>
column <id>
row <cell>|<cell>|...
```

Column IDs are non-empty single tokens.

Duplicate column IDs are rejected.

All column declarations must precede the first row.

Every row must have exactly the declared number of cells.

Cells are preserved as exact strings after splitting on the unescaped `|`
delimiter.

P11.13E defines no cell escaping or type coercion.

The frozen projection is:

`SemanticTableProjection(lineage, columns, rows)`.

This is structured rich-document metadata. It does not mutate or automatically
construct the P11.8 semantic lattice.

## Diagram grammar

A diagram block contains nodes and edges:

```text
node <id>
node <id> <label>
edge <source> <relation> <target>
```

Node IDs and edge source/relation/target values are non-empty single tokens.

A node label, when supplied, is the exact non-empty remainder after the node ID.

Duplicate node IDs and exact duplicate edges are rejected.

Edge endpoints must name declared nodes.

Node and edge encounter order is preserved in separate immutable tuples.

The frozen records are:

- `DiagramNode`;
- `DiagramEdge`;
- `DiagramProjection`.

E performs no rendering.

## Narrative identity paths

World-bible and character-sheet paths use `/` only as an E container
serialization convention:

```text
Universe/Main
People/Ada
```

The serialized path is projected to the exact canonical:

`NarrativeIdentity(kind, tuple(path_segments))`.

Segment spelling, case, and order are preserved.

Empty or whitespace-padded path segments are rejected.

P11.13E does not change the canonical narrative identity model.

## World-bible grammar

A world-bible block contains exactly one story declaration and may contain
character and continuity declarations:

```text
story <path>
character <path>
continuity <path> <kind>:<path>[,<kind>:<path>...] = <assertion>
```

The continuity syntax is the only correction to the preliminary E audit
proposal. The canonical `NarrativeContinuityConstraint` requires a non-empty
tuple of `NarrativeIdentity` subjects plus an assertion, so E makes those
subjects explicit instead of inventing them implicitly.

Each subject is serialized as:

```text
<kind>:<path>
```

and is reconstructed as the exact canonical `NarrativeIdentity`.

The world-bible projection constructs existing canonical types:

- `NarrativeIdentity`;
- `NarrativeCharacter`;
- `NarrativeContinuityConstraint`;
- `NarrativeContinuity`;
- `NarrativeStory`.

The resulting `NarrativeStory` uses empty tuples for narrative record families
not represented by this minimal world-bible grammar.

It does not create replacement narrative types.

Duplicate character and continuity identities are rejected.

## Character-sheet grammar

A character sheet contains exactly one character identity followed by zero or
more descriptive fields:

```text
character <path>
field <key> = <value>
```

The character is projected to the exact canonical:

`NarrativeCharacter(NarrativeIdentity("character", path))`.

Fields remain ordered immutable string pairs.

Fields do not become new properties on `NarrativeCharacter`.

Duplicate field keys are rejected.

## Simulation-description grammar

A simulation-description block contains exactly one simulation ID and zero or
more descriptive parameters:

```text
simulation <id>
parameter <key> = <value>
```

The frozen projection is:

`SimulationDescriptionProjection(lineage, simulation_id, parameters)`.

Parameters remain ordered immutable string pairs.

P11.13E introduces no simulation engine, execution semantics, or ApexMotion
implementation.

The projection is an intentional future handoff point for P11.15.

## Semantic-lattice boundary

P11.13E imports no semantic-lattice production module.

Semantic tables and diagrams are document-owned structured metadata.

If a caller later wants to propose semantic-lattice information, P11.13-C
remains the explicit optional Codex advisory path.

There is no automatic Codex invocation.

## Runtime and project boundaries

P11.13E does not modify or integrate:

- `ProjectManifest`;
- project loading;
- `ProjectBuilder`;
- CLI;
- cache layers;
- TAM;
- TAP;
- runtime execution;
- package resolution;
- remote I/O.

## Public surface

`rich_documents.projections.__all__` contains exactly thirteen symbols:

- `RichDocumentProjectionLineage`
- `SemanticTableProjection`
- `DiagramNode`
- `DiagramEdge`
- `DiagramProjection`
- `WorldBibleProjection`
- `CharacterSheetProjection`
- `SimulationDescriptionProjection`
- `project_semantic_table`
- `project_diagram`
- `project_world_bible`
- `project_character_sheet`
- `project_simulation_description`

## P11.13F handoff

After E freezes, P11.13F may integrate rich documents and package-tier
classification with the project/build/artifact/CLI surfaces.

That integration must preserve E's caller-controlled projections and must not
turn the optional P11.13-C Codex adapter into a compilation requirement.