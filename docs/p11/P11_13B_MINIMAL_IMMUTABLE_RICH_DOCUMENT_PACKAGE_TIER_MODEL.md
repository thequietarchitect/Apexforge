# P11.13B â€” Minimal Immutable Rich-Document + Package-Tier Model

## Purpose

P11.13B introduces the smallest production vocabulary required for later
`.apexdoc` and package-architecture work.

It defines immutable structure only.

B does not parse `.apexdoc`, compile executable blocks, mutate project
manifests, change CLI behavior, integrate cache/TAM, execute runtime behavior,
or implement a package manager.

## Predecessor

P11.13B begins from:

`afp-p11-13a-freeze`

at:

`01bfdc463b46b5032c6f541391be3aef1fd9ebe9`

The P11.13A audit remains the historical stage-boundary proof.

Because B intentionally introduces owners that A proved absent, later slices
must not treat the whole A absence test as a forward-compatible regression.
Use the A freeze tag, hashes, and durable decisions instead.

## Production package

B introduces:

`rich_documents`

The package-level public export tuple is intentionally empty.

The first production API is module-local:

`rich_documents.model`

This avoids prematurely expanding a wider public surface before parsing and
integration semantics are frozen.

## Schema

The model defines:

`RICH_DOCUMENT_SCHEMA_VERSION = 1`

This is the model contract version, not a `.apexdoc` file-format parser version.

## Document block kinds

`DocumentBlockKind` is a string enum with canonical ordered IDs:

1. `text`
2. `apex`
3. `semantic-table`
4. `diagram`
5. `world-bible`
6. `character-sheet`
7. `simulation-description`

These are classifications only in B.

In particular, an `apex` block is not compiled merely because its model kind is
`apex`.

## ApexDocumentBlock

`ApexDocumentBlock` is a frozen dataclass with fields:

- `block_id`
- `kind`
- `content`
- `span`
- `metadata`

`content` preserves the exact caller-provided string.

B performs no normalization, tokenization, parsing, extraction, or compilation.

`span` is either `None` or the existing canonical:

`language.source.SourceSpan`

B therefore reuses source-lineage ownership rather than creating another span
model.

## ApexDocument

`ApexDocument` is a frozen dataclass with fields:

- `document_id`
- `source_name`
- `blocks`
- `metadata`

`blocks` is an ordered tuple.

Caller order is preserved.

Duplicate `block_id` values inside one document are rejected because they would
make block identity ambiguous.

B does not require a document to contain any particular block kind.

## Metadata

Document and block metadata use immutable ordered tuples of:

`(str, str)`

pairs.

B deliberately restricts metadata values to string scalars so it does not
prematurely invent a rich metadata schema.

Order is preserved.

Duplicate keys within one metadata tuple are rejected.

No sorting or normalization occurs.

## PackageTier

`PackageTier` is a string enum with exactly four ordered values:

1. `core`
2. `standard`
3. `domain`
4. `experimental`

Tier classification remains metadata/visibility architecture.

It does not grant semantic or authority privileges.

## PackageDescriptor

`PackageDescriptor` is a frozen dataclass with fields:

- `package_id`
- `tier`
- `version`
- `documents`
- `metadata`

`documents` is an ordered tuple of document identifiers only.

B does not load, resolve, fetch, or validate referenced document files.

Duplicate document identifiers are rejected.

## Package version

`version` is an opaque deterministic non-empty string in B.

P11.13B intentionally does not impose semantic-version syntax or version
resolution policy.

Those decisions can be introduced only when later package integration requires
them.

## No package manager

B does not implement:

- a dependency solver;
- a remote package registry;
- remote package fetch;
- package restoration;
- signing;
- lockfiles.

Those remain P14 concerns.

## No `.apexdoc` parser

B has no `.apexdoc` parsing behavior.

It does not define document syntax, fences, headings, block markers, escaping,
or extraction rules.

That belongs to P11.13D.

## No executable-block compilation

B does not invoke the Apex compiler.

The future D parser/extractor must delegate executable Apex blocks to the
canonical compiler rather than adding alternate execution semantics.

## Narrative ownership

World-bible and character-sheet block kinds are classifications only.

B does not create a second narrative semantic model.

Existing owners such as `NarrativeCharacter`, `NarrativeScene`,
`NarrativeContinuity`, and `NarrativeStory` remain canonical.

The actual rich-document projections over those owners belong to P11.13E.

## Codex boundary

B has no Codex dependency.

P11.13-C remains reserved for the optional/advisory Experimental Codex Adapter.

Deterministic compilation must remain independent of that adapter.

## Project/CLI boundary

B does not modify:

- `ProjectManifest`;
- `LoadedProject`;
- project loading;
- `ProjectBuilder`;
- CLI commands.

Those integrations are deferred.

## Cache/TAM boundary

B does not cache rich-document products yet and emits no TAM records.

Once the parser and canonical rich-document products are frozen, later P11.13
slices may integrate with P11.12 Capture/Resonance and TAM.

## Runtime/TAP boundary

B performs no runtime execution and gives TAP no ownership.

## Constructor invariants

The model enforces only structural invariants needed for deterministic identity:

- required identifiers are non-empty strings;
- block kind must be exact `DocumentBlockKind`;
- package tier must be exact `PackageTier`;
- block/document/package collections are tuples;
- block IDs are unique within one document;
- package document IDs are unique within one package;
- metadata is an ordered tuple of exact `(str, str)` pairs;
- metadata keys are unique;
- source span is `None` or exact `SourceSpan`.

The constructors do not rewrite or normalize valid caller values.

## Public surface

`rich_documents.model.__all__` contains exactly eight symbols:

- `RICH_DOCUMENT_SCHEMA_VERSION`
- `DOCUMENT_BLOCK_KIND_IDS`
- `PACKAGE_TIER_IDS`
- `DocumentBlockKind`
- `ApexDocumentBlock`
- `ApexDocument`
- `PackageTier`
- `PackageDescriptor`

The package-level `rich_documents.__all__` remains empty in B.

## P11.13-C handoff

After B freezes, the roadmap-reserved next slice is:

`P11.13-C â€” Experimental Codex Adapter`

It should operate against these immutable rich-document/package classifications
only where useful, while remaining optional/advisory and never becoming a
deterministic-compilation prerequisite.

The `.apexdoc` parser itself remains P11.13D.