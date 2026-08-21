# P11.13D â€” `.apexdoc` Parser, Executable-Block Extraction, and Source Mapping

## Purpose

P11.13D introduces the first deterministic parser for the P11.13 rich-document
container and the first adapter that extracts executable Apex blocks.

The container parser does not parse Apex language syntax.

Executable blocks are delegated to the existing canonical:

`language.compiler.compile_source_with_map`

which returns the existing exact:

`language.compiler.CompiledSource`.

## Predecessor

P11.13D begins from:

`afp-p11-13c-freeze`

at:

`b91cc3ea0ab47d560dff715deaf8a5d47ecf3156`

P11.13-C remains optional/advisory and is not invoked automatically by D.

## Corrected compiler architecture

The architecture audit initially considered a `Compiler` object seam.

The supplemental audit proved that no such `language.compiler.Compiler` class
exists.

The canonical standalone compilation entry point is:

```text
compile_source_with_map(
    source,
    *,
    source_name="<memory>",
    function_signatures=None,
    allow_headerless_multi_directive=True,
) -> CompiledSource
```

P11.13D therefore delegates directly to that function.

`ProjectBuilder` is canonically owned by `language.project` and has its own
injected compiler seam. D does not need or mutate that project-level seam for
standalone document-block compilation.

## Minimal `.apexdoc` syntax

P11.13D deliberately freezes a narrow container grammar.

A document begins on the first line with:

```text
@apexdoc <document-id>
```

Blocks use:

```text
@block <kind> <block-id>
<exact block content>
@endblock
```

The block kinds are the exact P11.13B `DocumentBlockKind` values.

The syntax uses exact single-space separators in the header/open marker.

Document IDs and block IDs are single non-whitespace tokens in D.

## Blank lines

Blank or whitespace-only lines are allowed outside blocks after the document
header.

The document header itself must be the first line.

Non-blank content outside a block is a parse error.

P11.13D defines no comment syntax.

## Block content

Everything between the end of the block-opening line and the beginning of the
exact `@endblock` line is block content.

The parser preserves that string exactly.

It does not:

- trim it;
- normalize line endings;
- dedent it;
- tokenize it;
- parse it as Apex;
- interpret semantic-table/diagram/world-bible/etc. syntax.

The exact line:

`@endblock`

is reserved as the close marker.

A line such as:

`@endblock extra`

is ordinary block content.

There is no escaping syntax in D.

## Source spans

P11.13D reuses:

- `language.source.SourceText`;
- `language.source.SourceSpan`.

Every parsed block receives an end-exclusive `SourceSpan` covering exactly the
stored block-content substring.

Lines and columns therefore follow the canonical one-based convention and
offsets remain canonical zero-based Python-string character offsets.

Marker spans are used only for parser diagnostics and are not added to the
frozen P11.13B model.

## Parser diagnostics

Container failures reuse the existing `language.parser.ParseError` carrying a
canonical `language.diagnostics.BuildDiagnostic` with stage `parse`.

D defines deterministic codes:

- `APXDOC-PARSE-001` â€” missing/malformed document header;
- `APXDOC-PARSE-002` â€” unexpected close marker;
- `APXDOC-PARSE-003` â€” malformed block-opening marker;
- `APXDOC-PARSE-004` â€” unknown block kind;
- `APXDOC-PARSE-005` â€” nested block marker;
- `APXDOC-PARSE-006` â€” unclosed block;
- `APXDOC-PARSE-007` â€” duplicate block identity rejected by the B model;
- `APXDOC-PARSE-008` â€” non-blank content outside a block.

There is no recovery mode in D. The first structural error fails
deterministically.

## Parser public surface

`rich_documents.parser.__all__` contains exactly:

- `parse_apex_document`

The parser returns the existing exact P11.13B `ApexDocument`.

## Executable extraction

`rich_documents.compilation` defines the frozen:

`ApexExecutableBlockSource`

with fields:

- `document_id`;
- `block_id`;
- `source_name`;
- `text`;
- `span`.

Only blocks whose kind is exactly `DocumentBlockKind.APEX` are extracted.

Extraction preserves document encounter order and the exact block content.

## Virtual source identity

Each executable block receives a deterministic virtual compiler source name:

```text
<document-source>::apexdoc::<document-id>::<block-id>
```

This name is passed to the canonical compiler.

As a result, parser/compiler diagnostics and the canonical `SourceMap` identify
the executable block virtual source rather than pretending the block begins at
line 1 of the outer `.apexdoc` file.

## Two-layer source mapping

D preserves both coordinate systems without mutating either owner.

The extracted `ApexExecutableBlockSource.span` retains the original absolute
`.apexdoc` content span.

The canonical `CompiledSource.source_map` retains the compiler's block-local
source spans under the deterministic virtual source name.

D does not rewrite canonical `SourceMapEntry` spans into outer-document
coordinates.

Later tooling can correlate them through the immutable D wrapper.

## Compilation wrapper

`ApexExecutableBlockCompilation` is a frozen dataclass containing:

- `source: ApexExecutableBlockSource`;
- `compiled: CompiledSource`.

It verifies that every canonical source-map entry remains associated with the
extracted block's virtual source name.

## Canonical compilation

`compile_apex_document_blocks(document)` performs:

```text
extract Apex blocks
    ->
compile_source_with_map(block.text, source_name=block.source_name)
    ->
ApexExecutableBlockCompilation
```

There is no alternate Apex parser or compiler.

D performs no cross-block linking or project composition.

Those are later integration concerns.

## Compiler failures

D does not replace canonical compiler/parser failures.

Because the canonical compiler receives the deterministic virtual source name,
its structured diagnostics identify the failing document/block source.

The virtual name embeds outer document source, document ID, and block ID,
preserving lineage even when compilation fails before a D compilation wrapper
can be returned.

## Codex boundary

P11.13-C remains entirely optional.

D does not automatically call:

- `adapt_codex_document_block_advisory`;
- `validate_codex_document_block_advisory`.

Non-executable structured blocks remain opaque container content in D.

## Deferred integration

P11.13D does not modify or integrate:

- `ProjectManifest`;
- `LoadedProject`;
- project loading;
- `ProjectBuilder`;
- CLI commands;
- P11.12 cache layers;
- TAM;
- TAP;
- runtime execution;
- package resolution.

Those remain later P11.13 slices.

## No I/O ownership

The parser accepts an explicit source name and already-decoded string.

It opens no files, performs no network access, writes no files, and owns no
global mutable state.

## Public compilation surface

`rich_documents.compilation.__all__` contains exactly:

- `ApexExecutableBlockSource`
- `ApexExecutableBlockCompilation`
- `extract_apex_executable_blocks`
- `compile_apex_document_blocks`

The package-level `rich_documents.__all__` remains empty.

## P11.13E handoff

After D freezes, P11.13E may introduce typed projections for semantic tables,
diagrams, world bibles, character sheets, and simulation descriptions.

Those projections must consume the immutable block model/parser results without
replacing existing narrative or semantic-lattice ownership.