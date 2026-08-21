# P11.11G â€” Final TAP Check Integration, Regression, and Freeze

## Purpose

P11.11G closes P11.11 TAP Check.

It adds no production behavior.

Its purpose is to prove the complete P11.11A-through-F implementation,
reconcile the final reporting taxonomy with the evidence paths that actually
exist, run the durable compatibility gates, and freeze the resulting TAP Check
contract.

## Predecessor

P11.11G begins from:

`afp-p11-11f-freeze`
â†’ `69ca0d2d5e48f232ebf08d7b03902de0ba1f609a`

The complete P11.11A-through-F freeze chain must remain exact and ancestral.

## Final public TAP model

The passive immutable result model remains:

- `TapCheckLedgerEntry`;
- `TapCheckAuditLedger`.

The roadmap reporting taxonomy remains the exact ten-category tuple:

1. `active-directives`;
2. `compiler-transformations`;
3. `semantic-changes`;
4. `authority-intervention`;
5. `optimization-decisions`;
6. `continuity-effects`;
7. `narrative-state-changes`;
8. `convergence-rulings`;
9. `air-lowering`;
10. `runtime-results`.

All ten categories are reportable.

A report category is not semantic authority.

## Final public operations

The final TAP package exposes eight operations:

- `audit_trace_map`;
- `adapt_runtime_result`;
- `adapt_convergence_ruling`;
- `adapt_narrative_state_change`;
- `adapt_air_lowering`;
- `adapt_active_directive`;
- `compose_tap_check_ledgers`;
- `tap_check_category_coverage`.

Together with the category tuple and two immutable model classes, the final
`tap_check.__all__` contains eleven symbols.

## Canonical trace spine

The canonical TAM evidence input remains `TraceMap`.

P11.11C maps only three proven direct record signatures into two report
categories:

- compiler `source-map-entry` evidence
  â†’ `compiler-transformations`;
- `authority-check`
  â†’ `authority-intervention`;
- `authority-grant`
  â†’ `authority-intervention`.

Unmapped TAM evidence remains omitted rather than reinterpreted.

Exact TAM `TraceIdentity` references are preserved.

## Read-only owner evidence

P11.11D freezes five narrow adapters over already-produced immutable owner
results:

- `DirectiveExecutionResult`
  â†’ `active-directives`;
- `NarrativeExecutionResult`
  â†’ `narrative-state-changes`;
- `SemanticConvergenceResolution`
  â†’ `convergence-rulings`;
- `GenericLoweringResult`
  â†’ `air-lowering`;
- `ExecutionResult`
  â†’ `runtime-results`.

The adapters do not execute their owner subsystem.

When the supplied owner evidence has no exact canonical TAM identity link, the
adapter preserves `trace_ids=()` rather than fabricating one.

## Final explicit observation capability

Seven roadmap categories have an explicit observational path at P11.11 close:

1. `active-directives`;
2. `compiler-transformations`;
3. `authority-intervention`;
4. `narrative-state-changes`;
5. `convergence-rulings`;
6. `air-lowering`;
7. `runtime-results`.

Three categories remain reportable but have no unambiguous canonical owner
event proven by the P11.11 architecture audit:

- `semantic-changes`;
- `optimization-decisions`;
- `continuity-effects`.

This is a deliberate completeness result.

P11.11 does not force unrelated evidence into those categories merely to make
all ten counts nonzero.

## Missing evidence semantics

Missing evidence is absence of observation.

It is never automatically a negative semantic conclusion.

Examples:

- no `active-directives` entry does not prove every directive is inactive;
- no `authority-intervention` entry does not prove no authority event occurred;
- no `runtime-results` entry does not prove the program never ran;
- zero `semantic-changes` does not prove semantics were unchanged.

This rule also governs the category coverage API.

## Whole-ledger aggregation

`compose_tap_check_ledgers` remains a pure operation over already-produced
ledgers.

It preserves:

- caller ledger-block order;
- entry order within each ledger;
- exact entry references;
- duplicates;
- empty ledger blocks.

It performs no sorting, deduplication, evidence production, or semantic
inference.

## Category coverage

`tap_check_category_coverage` always reports exactly ten rows in
`TAP_CHECK_CATEGORY_IDS` order.

Each value is the observed ledger-entry count for that category.

A zero is an observed-entry count of zero, not a semantic falsehood.

Partial coverage is valid.

## Final CLI

The user-facing command is:

`apexforge tap-check .`

It is user-controlled, observational, diagnostic-only, non-activating, and
read-only.

`tooling.cli` owns only command routing and text presentation.

`tooling.project_loader` owns project discovery and immutable source loading.

The CLI deliberately does not create prerequisite evidence in a fresh
process. It does not:

- invoke the project builder;
- compile source for TAP evidence;
- parse source for TAP evidence;
- invoke a TAM producer;
- call `audit_trace_map`;
- call a D owner adapter;
- activate directives;
- evaluate authority;
- resolve semantic convergence;
- run generic lowering;
- execute runtime behavior;
- mutate project files.

When no already-produced evidence is supplied, the command returns a valid
empty ledger, renders all ten coverage rows as zero, explains that zero means
unobserved rather than negative, and exits successfully.

## Real `.apex` acceptance

P11.11F freezes real-project acceptance against a tracked
repository-resident ApexForge project.

The accepted project selected in the final integration environment is:

`apexforge/fixtures/p11_1b/manifest_entry`

It contains a real manifest and real `.apex` source files.

Both in-process and PowerShell console-wrapper acceptance prove deterministic
output and no project-byte or repository-status mutation.

## TAM-L forward-compatibility note

The historical TAM-L final-freeze test intentionally guarded the entire
`apexforge/tooling` directory against any post-TAM-K change.

P11.11F legitimately extends `apexforge/tooling/cli.py`.

Therefore downstream P11.11 final verification does not rerun TAM-L's obsolete
whole-tooling absence assertion.

Instead it verifies TAM-L's durable properties directly:

- complete TAM freeze chain;
- frozen hashes;
- public TAM contract;
- TAM integration boundary.

It additionally proves that the sole path changed inside TAM-L's historical
guarded set is the authorized:

`apexforge/tooling/cli.py`

The frozen TAM implementation itself remains unchanged.

## Final ownership boundaries

TAP Check remains observational.

It owns no:

- language semantics;
- type semantics;
- authority decisions;
- directive activation;
- narrative execution;
- semantic-decision execution;
- convergence resolution;
- Paradox Elevation;
- optimization decision;
- runtime execution;
- project mutation.

Existing owners produce evidence.

TAP observes and reports that evidence.

## G mutation boundary

P11.11G adds no production code.

Its only new artifacts are:

- `apexforge/p11_11g_final_tap_check_integration_regression_freeze_smoke_test.py`;
- `docs/p11/P11_11G_FINAL_TAP_CHECK_INTEGRATION_REGRESSION_FREEZE.md`.

All production and owner paths remain byte-identical to the P11.11F freeze.

## Final closure

P11.11 TAP Check is closed when:

- the A-through-F freeze chain is exact;
- all frozen TAP hashes remain exact;
- the final eleven-symbol public package contract is intact;
- all eight public TAP operations retain their signatures;
- the ten roadmap categories remain reportable in canonical order;
- seven categories retain proven explicit observation paths;
- the three unambiguous-owner gaps remain explicit rather than fabricated;
- missing evidence remains observational absence, not semantic negation;
- whole-ledger composition and coverage remain deterministic;
- real `apexforge tap-check .` acceptance remains green;
- P10 CLI compatibility remains green;
- passive Concordat/governance behavior remains green;
- the durable TAM-L contract remains green;
- G introduces no production mutation.

The handoff to P11.12 is therefore a frozen, deterministic, passive TAP Check
audit ledger and CLI surface.