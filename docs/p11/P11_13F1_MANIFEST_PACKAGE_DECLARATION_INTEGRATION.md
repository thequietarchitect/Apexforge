# P11.13F1 â€” Manifest Package Declaration Integration

P11.13F is split internally into F1 manifest/package declaration integration,
F2 native rich-document project build plus canonical artifact, and F3 CLI
project/check/build routing plus final F acceptance.

F1 begins from `afp-p11-13e-freeze` at
`88757be22340e3870e0eda9df98c784caf1935e4`.

The canonical owner remains `tooling.project_manifest.ProjectManifest`.
`PROJECT_MANIFEST_SCHEMA` remains `1`.

F1 appends one optional field after the existing schema field:

`package: Optional[PackageDescriptor] = None`

Appending after `schema` preserves historical four-positional-argument
construction where the fourth argument is the schema.

The package object reuses the exact P11.13B
`rich_documents.model.PackageDescriptor` and `PackageTier` owners. Its JSON
keys are exactly `id`, `tier`, `version`, and `documents`; all four are
required when a package object is present. Unknown package keys are rejected.
A JSON null package is treated as absence and is omitted by canonical output.

Package tiers remain exactly `core`, `standard`, `domain`, and `experimental`.
Tier classification does not grant authority.

Package document identifiers are bound to project source paths in F1. Each is
normalized through the existing canonical source-path normalizer, must end in
lowercase `.apexdoc`, must occur in manifest `sources`, and must be unique.
Package document declaration order is preserved while the existing manifest
source sorting remains unchanged.

`PackageDescriptor.metadata` remains supported by the descriptor model, but F1
does not define a manifest JSON representation for it. Directly attached
manifest package descriptors must therefore have empty metadata to preserve a
lossless deterministic round trip.

Legacy manifests without a package preserve their existing mapping and
canonical JSON. The loader model and project-kind set are unchanged. F1 does
not modify `LoadedProject`, source I/O, exact `source_bytes`, universal-newline
text, project builds, artifacts, CLI, cache, TAM, TAP, runtime, registry,
solver, lockfile, signing, or remote fetch behavior.

Earlier frozen tests that assert the exact pre-P11.13 manifest field set are
stage-boundary proofs. They remain frozen and are not modified or treated as
forward-compatible regressions after F1 intentionally introduces `package`.