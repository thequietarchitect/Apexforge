# P11.13F2 â€” Native Rich-Document Project Build and Canonical Artifact

## Status

RED contract prepared against the frozen P11.13F1 predecessor.

F1 freeze:

`b79ab744677cf888031ebeab24833210ceac0676`

Tag:

`afp-p11-13f1-freeze`

## Purpose

P11.13F2 integrates the already-frozen rich-document model, parser, executable-block
compilation path, and F1 package declaration into one native project-level build
material and one canonical serialized build artifact.

F2 does not manufacture an empty `ProjectBuild` and does not synthesize aggregate
AIR merely to pass through the pre-existing AIR build path.

## Canonical owners

- Package declaration: `tooling.project_manifest` â€” frozen by F1.
- Project loading and exact bytes: `tooling.project_loader` â€” unchanged.
- Rich-document model: `rich_documents.model` â€” reused.
- Rich-document parsing: `rich_documents.parser.parse_apex_document` â€” reused.
- Executable-block compilation: `rich_documents.compilation.compile_apex_document_blocks` â€” reused.
- New native project build material: `rich_documents.project_build`.
- Canonical serialized envelope: `tooling.build_artifact`.

## Native project-build contract

`RichDocumentProjectBuild` is a frozen dataclass with exactly:

1. `package`
2. `documents`
3. `compilations`

`build_rich_document_project(loaded)`:

- requires an exact `LoadedProject`;
- requires `loaded.manifest.package`;
- resolves only package-declared `.apexdoc` documents;
- follows `PackageDescriptor.documents` declaration order;
- locates each document in the already-loaded source snapshot;
- decodes the corresponding exact `source_bytes` as UTF-8;
- passes that exact decoded text to `parse_apex_document`;
- delegates every parsed document to `compile_apex_document_blocks`;
- preserves document/block lineage;
- returns no synthetic aggregate AIR;
- performs no runtime execution.

The distinction between canonical manifest source sorting and package document
declaration order is deliberate. Project source fingerprints retain manifest order;
native rich-document build semantics retain package document order.

## Nested payload contract

Schema:

`apexforge.rich-document-project-build/v1`

Shape:

```text
schema
package
  id
  tier
  version
documents[]
  id
  path
  blocks[]
    id
    kind
    content
executable_blocks[]
  document_id
  block_id
  source_name
  text
  air
  source_map[]
    air_id
    kind
    reference
    span
      source_name
      start
        line
        column
        offset
      end
        line
        column
        offset
```

Block content is serialized exactly as held by the frozen rich-document parser,
including original line endings.

Each executable block additionally carries the exact canonical semantic result
already produced by `compile_apex_document_blocks`:

- `air` is `air_to_dict(compilation.compiled.program)`;
- `source_map` projects the frozen compiler `SourceMap.entries` in canonical
  order, including exact AIR identity, kind, reference, source name, and
  start/end line, column, and offset provenance.

This is nested executable-block semantic material. It is not a synthesized
project-wide AIR program and does not add a top-level `air` field to the
native rich-document artifact.

## Canonical artifact contract

F2 introduces:

`apexforge.build-artifact/v3`

Top-level shape:

```text
fingerprint
package
project
rich_documents
schema
```

There is no top-level `air` member and no `narrative` member for a native
rich-document artifact.

`CanonicalBuildArtifact` remains unchanged with exactly:

```text
content
entry
fingerprint
source_count
narrative_artifact
```

The existing `narrative_artifact` field remains `None` for native rich-document
artifacts. No new dataclass field is introduced.

Project source fingerprints continue to hash exact `LoadedProjectSource.source_bytes`.

## Explicit exclusions

F2 does not change:

- `LoadedProject`;
- `LoadedProjectSource`;
- project-kind classification;
- `ProjectBuilder`;
- project loader I/O;
- CLI `project`, `check`, or `build` routing;
- runtime execution;
- incremental cache integration;
- Compiler TAM;
- TAP Check;
- remote registry behavior;
- dependency solving;
- lockfiles;
- signing.

CLI routing and end-to-end user-facing project/check/build behavior remain P11.13F3.