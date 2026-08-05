# P11.2I-A Runtime Result Reporting Architecture Audit

## Scope

P11.2I-A is audit-only. It adds one architecture document and one focused smoke
test. It adds no command flag, renderer, serializer, report file, schema,
runtime behavior, artifact field, editor feature, commit, or tag.

## Frozen baseline

```text
branch: p11.2c-heterogeneous-source-units
annotated tag: afp-p11.2h-freeze
commit: 28b61e7392d164cc91c3ecaf2bb8c24cba522153
```

## Existing execution pipeline

The public run path loads and builds a project, resolves one canonical entry,
constructs its execution context, calls `ProjectBuild.execute` once, receives an
`ExecutionResult`, renders runtime diagnostics on failure, and otherwise prints:

```text
ApexForge run succeeded: <project>
Entry: directive:<name>
Runtime diagnostics: 0
```

A future report must be strictly opt-in. Running without the option must retain
this output byte-for-byte and must not execute the project a second time.

## Runtime result inventory

`ExecutionResult` already contains the canonical observational source:

- `delta: StateDelta`;
- `trace: Trace`;
- `diagnostics: tuple[Diagnostic, ...]`;
- `final_state: StateSnapshot`.

`StateDelta` preserves ordered assignments, events, and effects. `Trace`
preserves ordered trace steps and facts. `StateSnapshot` preserves final state.

## Dormant legacy helper

`apexforge/tools/runtime_report.py` is unconnected legacy code. Its current API
requires one caller-supplied integer `state_key`, reads message facts, and lists
event identifiers. It omits the complete assignments, effects, trace,
diagnostics, and final-state projection. P11.2I-A preserves it unchanged and
does not adopt it as the public contract.

## Canonical report source

A canonical report must project the single `ExecutionResult` returned by the
existing `ProjectBuild.execute` call. Rendering must be observational and must
not mutate runtime state, execution context, AIR, project build, registries,
filesystem, environment, or working directory.

Deterministic order is inherited from the result: diagnostics in established
order, assignments in execution order, events in emission order, effects in
production order, trace steps in trace order, and final-state cells in snapshot
order. No timestamps, process IDs, random values, absolute temporary paths, or
object identities may enter the report.

## Build-artifact separation

Runtime reporting is a command observation surface. It must not change
`apexforge.build-artifact/v1`, canonical artifact JSON, artifact fingerprints,
AIR serialization, manifest schema, source hashes, or linked AIR order.

## Proposed P11.2I-B contract

```text
P11.2I-B — Opt-In Human-Readable Runtime Result Report
```

Proposed command:

```text
apexforge run <project> --report
```

The option should execute through the existing `ProjectBuild.execute` call
exactly once, preserve the established success preamble, and append one
deterministic report to the supplied `stdout`. Candidate fixed sections are:

```text
RESULT
DIAGNOSTICS
ASSIGNMENTS
EVENTS
EFFECTS
TRACE
FINAL STATE
```

Every empty section should use one fixed explicit marker. Exact value rendering
must be frozen by the implementation contract and smoke test.

The existing failed-run behavior sends runtime diagnostics to `stderr` and
returns the runtime exit code. P11.2I-B should not emit a success-style report
after failure unless a later separately reviewed contract authorizes it.

## Explicit non-goals

P11.2I-A and the proposed P11.2I-B do not add runtime re-execution, new runtime
fields, AIR instructions, artifact fields, schema v2, report files, JSON/YAML/
XML/CSV/binary reports, fingerprints, signing, timing, profiling, telemetry,
network transmission, persistent history, filters, verbosity levels,
interactive output, editor integration, narrative reporting, or P11.5 changes.

## Acceptance boundary

P11.2I-A is accepted when the focused smoke proves the exact P11.2H annotated
baseline and ancestry, exact two-file ownership, no tracked or staged changes,
ordinary run output preservation, absence of `--report`, the existing result
surfaces, one runtime delegation from `ProjectBuild.execute`, the dormant helper
remaining unconnected, artifact-v1 separation, and no network or bytecode
mutation.
