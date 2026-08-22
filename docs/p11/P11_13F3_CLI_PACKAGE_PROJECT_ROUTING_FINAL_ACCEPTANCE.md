# P11.13F3 â€” CLI Package-Project Routing and Final F Acceptance

P11.13F3 is the final P11.13F integration slice.

## Frozen predecessor

The exact predecessor is the annotated P11.13F2 freeze:

```text
commit 3c2ccb0af494fff546d879ad1ce07af34c5455c0
tag    afp-p11-13f2-freeze
```

F1 manifest/package declaration integration and F2 native rich-document project
build/artifact semantics are frozen and are not reimplemented in F3.

## Production owner

F3 has one production mutation owner:

```text
tooling.cli
```

The CLI reuses:

```text
rich_documents.project_build.build_rich_document_project
tooling.build_artifact.construct_rich_document_build_artifact
tooling.build_artifact.BUILD_ARTIFACT_SCHEMA_V3
tooling.build_artifact.write_build_artifact_atomic
```

No new rich-document project kind is introduced.

## Routing discriminator

A loaded project with:

```text
loaded.manifest.package is not None
```

is routed as a native rich-document package project for `check` and `build`.

This explicit manifest declaration is the discriminator. File-extension guessing
does not select the route.

## `project`

`apexforge project` remains a manifest/source inventory operation.

Its existing presentation is unchanged. F3 does not add package lines or alter
the frozen project summary.

## `check`

For a package-declared project, `apexforge check` invokes the frozen F2 native
rich-document builder. It does not send `.apexdoc` through the ordinary
`ProjectBuilder`.

The existing success presentation remains:

```text
ApexForge check passed: <name> (<N> source(s)).
```

## `build`

For a package-declared project, `apexforge build`:

1. invokes `build_rich_document_project(loaded)`;
2. invokes `construct_rich_document_build_artifact(loaded, build)`;
3. writes through the existing atomic artifact writer;
4. reports schema `apexforge.build-artifact/v3`.

Existing success-line structure is preserved:

```text
ApexForge build succeeded: <name>
Schema: apexforge.build-artifact/v3
Entry: <none>
Sources: <N>
Fingerprint: sha256:<fingerprint>
Artifact written.
```

The v3 artifact remains the exact F2 shape:

```text
fingerprint
package
project
rich_documents
schema
```

No synthetic top-level AIR or narrative material is introduced.

Executable rich-document blocks retain the F2 canonical nested AIR and
source-map provenance.

## Preserved boundaries

F3 does not mutate:

- `ProjectManifest` schema or fields;
- `LoadedProject` fields;
- project-kind enumeration;
- `ProjectBuilder`;
- rich-document parser/compiler/project-build owners;
- canonical build-artifact dataclass fields;
- runtime execution;
- incremental cache;
- TAM/TAP;
- package registry, solver, lockfile, signing, or remote package behavior.

`run` is not a P11.13F3 package-project integration surface.

## Final F acceptance

P11.13F is complete only when package-declared `project`, `check`, and `build`
behavior passes together with frozen F1/F2 semantics and existing AIR,
narrative, semantic-decision, CLI, cache, and artifact regressions.