# ApexForge P11.1 Integration and Freeze Gate

## Status and scope

P11.1D is the integration, verification, documentation, and human
freeze-preparation slice for P11.1. It adds no production feature and does not
declare P11.1 complete or frozen. Repository ownership, review, and freeze
authority remain human responsibilities.

P11.1 consists of these accepted or candidate slices:

| Slice | Scope | Accepted commit |
| --- | --- | --- |
| P11.1A | Internal observational performance-baseline harness | `bba89ab` |
| P11.1B | Canonical public source-project `run` command | `214b899` |
| P11.1C | Canonical deterministic multi-source `build` artifact | `01f51f4` |
| P11.1D | Integrated smoke coverage, contract audit, documentation, and human freeze gate | Freeze candidate only |

The accepted commits above must be reachable from any reviewed P11.1 freeze
candidate. P11.2 multi-declaration work has not begun in this slice.

## Public CLI command matrix

| Command | Input and selection | Builds and validates | Executes | Writes an artifact |
| --- | --- | ---: | ---: | ---: |
| `apexforge project [PATH]` | Project directory, declared source, or `apexforge.json`; current directory by default | No | No | No |
| `apexforge check [PATH]` | Same project discovery; manifest entry is forwarded to the project builder | Yes | No | No |
| `apexforge run [PATH] [--entry NAME]` | Same project discovery; explicit entry overrides the manifest | Yes | Yes, through `ProjectBuild.execute` | No |
| `apexforge build [PATH] --output FILE [--entry NAME]` | Same project discovery; explicit output is required and explicit entry overrides the manifest | Yes | No | Yes |
| `apexforge new <NAME> [DIRECTORY]` | Creates the accepted deterministic project scaffold | No | No | No build artifact |
| `apexforge --version` | No project input | No | No | No |

The direct repository wrapper is `apexforge/apexforge_cli.py`. The packaged
console entry remains `tooling.cli:main` as declared in `pyproject.toml`. Both
surfaces expose the same command set, and both `run` and `build` retain their
accepted behavior.

## Execution and non-execution boundaries

The public run pipeline is exactly:

```text
load_project -> build_project -> ProjectBuild.execute
```

The CLI resolves one entry and supplies that entry to `ProjectBuild.execute`.
It never exposes `RuntimeEngine.execute(entry_directives=None)`.

The public build pipeline is exactly:

```text
load_project -> build_project -> construct_build_artifact
             -> write_build_artifact_atomic
```

`build` does not call `ProjectBuild.execute`, construct a runtime engine, or
construct execution authority. `check` builds and validates but likewise does
not execute, construct a runtime engine, construct execution authority, or
write an artifact. `project` only reports the loaded project inventory.

## Entry-selection matrix

| Project entry condition | `run` | `build` |
| --- | --- | --- |
| Explicit `--entry NAME` | Overrides the manifest and executes the resolved canonical directive | Overrides the manifest and records the resolved canonical directive |
| No override; manifest `entry` exists | Executes the resolved manifest entry | Records the resolved manifest entry |
| No override or manifest entry; exactly one linked directive | Executes the canonical one-directive fallback | Records the canonical one-directive fallback |
| No override or manifest entry; multiple linked directives | Fails with the accepted entry diagnostic and exit `20` | Succeeds and records `project.entry` as `null` |
| Explicit or manifest entry is undefined | Fails with no success output and exit `20` | Fails with no success output and exit `20`; any existing output is preserved |

Plain names and canonical `directive:NAME` identities share
`ProjectBuild.resolve_entry`; the CLI does not implement a second resolver.

## Authority boundary

Only public `run` constructs execution authority. After resolving the selected
entry directive, it constructs exactly one grant:

```text
principal:  resolved directive principal
capability: directive.invoke:<resolved directive name>
resource:   resolved canonical directive ID
```

The authority engine remains deny-by-default. No root, wildcard, universal,
cross-directive, standard-library, host-effect, or internal capability is
added. A downstream directive invocation performs its normal independent
authority check and, without its own grant, fails with `RUN001`; public `run`
returns exit `30` and no success output. `build` and `check` construct no
execution authority.

## Artifact and fingerprint boundary

The persisted schema remains `apexforge.build-artifact/v1`. Its top-level JSON
object contains exactly `schema`, `project`, `air`, and `fingerprint`.

Each source record contains its manifest-relative forward-slash path and a
lowercase SHA-256 digest over the exact source bytes captured by
`load_project`, before source-text newline normalization. The AIR member is
the existing canonical linked AIR mapping produced by `air_to_dict`; P11.1
does not change the AIR model or serialization schema.

The fingerprint input contains exactly:

```text
schema
project
air
```

That mapping is serialized as canonical JSON using preserved Unicode, sorted
keys, two-space indentation, UTF-8 without a BOM, LF-only line endings, and
exactly one final newline. SHA-256 covers all those bytes, including the final
LF. The `fingerprint` object is added only after hashing and is therefore not
part of its own digest.

The complete artifact uses the same canonical JSON rules. Repeated builds from
identical loaded source bytes, manifest metadata, linked AIR, and selected
entry produce identical artifact bytes. The artifact contains no timestamp,
duration, performance result, username, hostname, home or repository path,
absolute source or output path, credential, token, or other host metadata.

Construction finishes in memory before output mutation. The writer uses a
temporary sibling and atomic replacement. A failed build preserves an existing
output and leaves no temporary sibling residue.

## Exit-code matrix

| Exit | Meaning |
| ---: | --- |
| `0` | Success |
| `2` | Invalid command-line usage |
| `10` | Project discovery, manifest validation, or source loading failure |
| `20` | Compilation, linking, validation, or entry-resolution failure |
| `30` | One or more runtime diagnostics |
| `40` | Artifact output-path or write failure |
| `70` | Unexpected internal CLI failure |
| `130` | Keyboard interruption |

Failures print no success output. Existing command-specific deterministic
diagnostic rendering remains unchanged.

## Performance-baseline isolation

P11.1A remains an internal observational harness. It measures project loading,
validated project construction, internal `ProjectBuild.execute`, and total
elapsed time with `time.perf_counter_ns`. Timing results are advisory and no
absolute performance threshold or pass/fail speed assertion exists.

Running the baseline does not modify project sources or create a project build
artifact. Its optional JSON report remains
`apexforge.performance-baseline/v1`, with exactly the accepted top-level fields
`schema`, `clock`, `duration_unit`, `configuration`, `environment`, and
`benchmarks`.

## Determinism guarantees

- Project discovery, manifest validation, source snapshot order, compilation,
  linking, validation, and entry resolution retain their existing deterministic
  boundaries.
- Public success output excludes timing values, runtime traces, final-state
  serialization, artifact bodies, and temporary filenames.
- Runtime diagnostics retain their deterministic ordering.
- Source hashes cover the exact loaded bytes.
- Fingerprints cover only canonical `schema`, `project`, and `air` JSON bytes.
- Identical builds produce byte-identical artifacts.
- Artifact writes are atomic and failure-preserving.
- The compiler and runtime remain usable without an AI service.

## Accepted limitations

- Public `run` has no JSON, trace, debugger, final-state dump, authority-policy
  configuration, or output-file mode.
- Public `run` grants only selected-entry invocation, so projects needing
  downstream authority can fail with `RUN001`.
- Artifact v1 contains no source maps, compiler Token Analysis Map data, cache
  data, bytecode, native code, timestamps, host metadata, or performance data.
- P11.1 adds no artifact deserialization, validation as an input format,
  artifact loading, run-from-artifact behavior, or artifact execution.
- Passing an artifact where a source project or manifest is expected is
  rejected through the existing deterministic loading or manifest boundary;
  P11.1 does not canonize a more specific rejection diagnostic.
- No grammar, compiler, AIR, runtime, authority, or manifest-schema expansion is
  part of P11.1D.
- P11.2 and all later roadmap work have not begun.

## Human freeze checklist

- [ ] The working tree is clean after all reviewed P11.1D changes are included.
- [ ] The focused P11.1A, P11.1B, P11.1C, and P11.1D smoke tests pass.
- [ ] Directly affected CLI, packaging, project-builder, linker, validator,
      authority, runtime, and AIR serialization tests pass.
- [ ] The full regression harness passes with `PYTHONUTF8=1`.
- [ ] Direct repository-wrapper checks pass for the complete public command
      surface.
- [ ] Packaged `tooling.cli:main` console-entry checks pass.
- [ ] Repeated identical builds produce byte-identical artifacts and matching
      fingerprints.
- [ ] Artifact inspection finds no forbidden absolute path or host metadata.
- [ ] Accepted commits `bba89ab`, `214b899`, and `01f51f4` are reachable from
      the reviewed freeze candidate.
- [ ] Review confirms no P11.2 files or behavior and no later-roadmap work are
      present.
- [ ] The repository owner completes human review and explicitly authorizes any
      freeze action.
- [ ] Tag creation remains a human action after review; automation or an agent
      has not created it.

Following the repository's lowercase `afp-<phase>-freeze` convention, the
proposed P11.1 freeze tag is `afp-p11.1-freeze`. This document proposes the
name only; it does not create, require, or declare that tag.
