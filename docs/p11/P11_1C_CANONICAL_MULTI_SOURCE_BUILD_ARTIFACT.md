# P11.1C Canonical Multi-Source Build Artifact

## Scope

P11.1C adds one public command that persists a canonical linked and validated
project build. It does not execute the project and does not change the grammar,
compiler, AIR model, runtime, or manifest schema.

## Command syntax and output-path policy

```text
apexforge build [PATH] --output FILE [--entry NAME]
```

`PATH` defaults to the current directory and retains the project directory,
declared source path, or `apexforge.json` discovery behavior of `load_project`.
`--output` is required. The command never selects a default output file or
creates a default distribution directory, and the manifest has no output field.

## Build pipeline

The command uses this existing deterministic pipeline:

```text
load_project -> build_project -> canonical linked and validated ProjectBuild
```

It then serializes `ProjectBuild.program` through `air_to_dict`, the existing
AIR serialization support. It does not call `ProjectBuild.execute` or
`RuntimeEngine`, and it constructs no `ExecutionContext` or `AuthorityGrant`.

## Entry metadata

Artifact entry metadata uses this precedence:

1. Explicit `--entry`.
2. Manifest `entry`.
3. The only linked directive when exactly one exists.
4. `null` when no entry was selected and the linked project is ambiguous.

Explicit and manifest entries are resolved while building. The one-directive
fallback is resolved through `ProjectBuild.resolve_entry`. An undefined
explicit or manifest entry remains a build/entry error. A multi-directive
project without a selected entry is valid as an artifact and records `null`.

## Artifact schema

The command writes exactly one JSON document with this structure:

```text
schema: string ("apexforge.build-artifact/v1")
project:
  name: string
  source_count: integer
  sources: array in canonical manifest order
    path: manifest-relative forward-slash path
    sha256: lowercase 64-character source-content digest
  entry: canonical directive identity or null
air:
  canonical linked AIR mapping from existing AIR serialization support
fingerprint:
  algorithm: string ("sha256")
  value: lowercase 64-character hexadecimal digest
```

Source SHA-256 values are computed from the exact source bytes captured by the
project loader, before source-text newline normalization or compilation.

## Fingerprint and canonical JSON

The fingerprint input is an in-memory mapping containing exactly `schema`,
`project`, and `air`. That mapping is serialized as canonical JSON: UTF-8
without a BOM, preserved Unicode, sorted object keys, two-space indentation,
LF line endings, and exactly one final newline. SHA-256 is computed over all of
those UTF-8 bytes, including the final LF. The `fingerprint` object is added
afterward, so its algorithm and value are excluded from the digest boundary.
The complete artifact is then serialized under the same canonical JSON rules.

Artifacts contain no timestamp, duration, performance result, username,
hostname, home directory, absolute source/repository/output path, credential,
token, unordered value, or machine-dependent metadata. Identical loaded source
bytes, manifest metadata, linked AIR, and selected entry therefore produce
identical artifact bytes and fingerprints.

## Atomic writing

Loading, compilation, linking, validation, entry resolution, AIR conversion,
canonical serialization, and fingerprinting finish in memory before any output
file is created or altered. On success, the complete bytes are written to a
temporary sibling file, flushed, and atomically replace the requested output.
The temporary sibling is removed after a pre-replacement write failure. An
existing output remains unchanged for every failure before the final atomic
replacement. Temporary filenames are never printed.

## Success output

Success writes nothing to stderr and writes exactly:

```text
ApexForge build succeeded: PROJECT_NAME
Schema: apexforge.build-artifact/v1
Entry: CANONICAL_ENTRY_OR_<none>
Sources: SOURCE_COUNT
Fingerprint: sha256:HEX_DIGEST
Artifact written.
```

No absolute output path, timing value, source text, AIR body, or temporary
filename is printed.

## Diagnostics and exit codes

- `0`: artifact constructed and atomically written.
- `2`: invalid CLI usage, including a missing `--output`.
- `10`: manifest discovery, manifest validation, or source loading failure.
- `20`: compilation, linking, validation, or entry-resolution failure.
- `30`: runtime diagnostics; preserved for `run` and unused by `build`.
- `40`: output-path or artifact-write failure.
- `70`: unexpected internal CLI failure, including an unexpected serialization
  defect.
- `130`: keyboard interruption.

Failures print no success output and render their deterministic diagnostic to
stderr. Output-path failures use `[APX-BUILD-040] Unable to write build
artifact.` without exposing the requested path or a temporary sibling name.

## Known limitations and deferred work

Artifact v1 is JSON AIR persistence only. It contains no source maps, compiler
Token Analysis Map data, cache data, bytecode, native code, timestamps, host
metadata, or performance data. P11.1C does not add artifact loading,
deserialization, validation as an input format, run-from-artifact behavior, or
artifact execution. Those concerns, including P11.1D integration/freeze work,
remain explicitly deferred to separately reviewed roadmap slices.
