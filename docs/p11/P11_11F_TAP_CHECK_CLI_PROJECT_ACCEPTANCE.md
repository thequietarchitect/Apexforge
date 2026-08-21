# P11.11F â€” TAP Check CLI and Real `.apex` Project Acceptance

## Purpose

P11.11F exposes the user-controlled command `apexforge tap-check .` through
the existing `tooling.cli:main` console-entry architecture.

The command targets a real repository-resident ApexForge project and reports
the current TAP Check ledger coverage without creating prerequisite evidence.

## Predecessor

P11.11F begins from `afp-p11-11e-freeze` at
`1e75e0b228836a2e045829512f745d2c4b40e2d8`.

The B immutable model, C `TraceMap` projection, D read-only owner-evidence
adapters, and E aggregation/coverage implementation remain frozen.

## CLI ownership

`tooling.cli` remains a thin host adapter. It owns command parsing,
project-path routing, deterministic text presentation, and stable exit-code
routing. It does not own TAP semantics.

Project discovery and source loading remain owned by
`tooling.project_loader`. TAP ledger composition and category coverage remain
owned by `tap_check.aggregation`.

## Command

The new parser route is `apexforge tap-check [PATH]`, with `PATH` defaulting
to `.`.

It accepts the same project directory, declared source path, or
`apexforge.json` discovery contract already owned by `load_project`.

## Read-only project targeting

The command calls `load_project(Path(path))` only to identify and snapshot the
requested project. This reads the manifest and declared source files in their
existing canonical order.

TAP Check does not reinterpret those source files as audit evidence.

## No prerequisite creation

P11.11A froze the rule that TAP Check must not silently compile, execute,
authorize, activate, optimize, mutate narrative state, resolve convergence, or
create prerequisite artifacts merely to make the ledger more complete.

P11.11F therefore does not call the canonical project builder, a compiler or
parser for TAP evidence, a TAM producer, `audit_trace_map`, a P11.11D owner
adapter, an authority engine, semantic-convergence evaluation, or a runtime
engine.

In a fresh CLI process no prerequisite TAP ledger has been supplied. The F CLI
therefore composes the exact empty ledger with
`compose_tap_check_ledgers(())` and reports its canonical coverage.

This is deliberate rather than a failure. Future explicit workflows may make
already-produced evidence available to TAP, but F does not manufacture it from
project source.

## Report format

A successful report has the deterministic shape:

```text
TAP CHECK
Project: <manifest project name>
Root: <canonical project root>
Mode: observational
Sources: <declared source count>
Entries: <observed TAP entry count>
Coverage:
  active-directives: <count>
  compiler-transformations: <count>
  semantic-changes: <count>
  authority-intervention: <count>
  optimization-decisions: <count>
  continuity-effects: <count>
  narrative-state-changes: <count>
  convergence-rulings: <count>
  air-lowering: <count>
  runtime-results: <count>
Zero counts mean no observed TAP evidence, not a negative semantic result.
```

The coverage order is exactly `TAP_CHECK_CATEGORY_IDS`.

## Zero-count meaning

A zero is an observed-entry count. It does not mean that the corresponding
semantic event did not occur.

`active-directives: 0` does not prove every directive is inactive.
`authority-intervention: 0` does not prove no authority event occurred.
`runtime-results: 0` does not prove the project has never executed.

It means only that the current CLI invocation received no already-produced TAP
evidence for that category.

## Exit behavior

A valid project audit exits `0` even when the ledger is empty or partial.
Existing CLI/project errors retain their existing exit-code ownership. Missing
evidence alone does not create an error exit.

## Repository-resident real `.apex` acceptance

The acceptance gate selects the first available tracked repository-resident
project from this deterministic candidate order:

1. `apexforge/fixtures/p11_1b/manifest_entry`
2. `examples/T1Demo`
3. `examples/P11Validation`

A candidate is eligible only when it is a directory containing
`apexforge.json`, at least one `.apex` file, and tracked project content.

This makes the acceptance proof independent of optional or previously
untracked example directories while still exercising a real on-disk ApexForge
project.

The focused Python test verifies parser routing, real project loading,
deterministic report output, all ten coverage rows, exact zero-count semantics,
no project-builder invocation, and no project-file mutation.

The dedicated PowerShell acceptance invokes the actual source-tree console
wrapper twice from the selected project's directory using
`apexforge_cli.py tap-check .`. It verifies exit `0` twice, deterministic
output, canonical category order, no project byte changes, and no repository
status changes.

## Public-surface boundary

F adds no new public Python symbol to `tooling.cli`; `main` remains the public
CLI entrypoint. F also does not modify the public TAP package surface.

The user-facing command is a CLI route, not a new semantic API.

## Completion condition

P11.11F is complete when P11.11E ancestry is exact, frozen B-E files remain
unchanged, project discovery stays with `tooling.project_loader`, TAP creates
no prerequisite semantic evidence, valid empty or partial audits exit `0`, all
ten coverage rows appear in roadmap order, zero counts remain observational
absence rather than semantic negatives, repeated real-project output is
deterministic, and project/repository state remains unchanged.