# P11.11A â€” TAP Check Architecture and Ownership Audit

## Purpose

P11.11A freezes the ownership and semantic boundaries for the P11.11 TAP Check
Audit Ledger before any TAP-specific production implementation is introduced.

P11.11 remains a user-controlled, diagnostic-only, non-activating, read-only
inspection surface.

The eventual user-facing command remains:

`apexforge tap-check .`

P11.11A is audit-only.

## Predecessor

P11.11A begins from the final P11-TAM freeze:

`afp-p11-tam-l-freeze`
â†’ `28022e59728f28bfbf60fbc1d811e39b4b672acd`

P11-TAM is closed before TAP Check begins.

## Existing TAP precedent

No dedicated TAP Check implementation exists at the P11.11A entry boundary.

The existing governance subsystem already owns the constant:

`TAP_CHECK_MODE = "observational"`

and `ConflictReferral` preserves that mode while keeping
`activates_directives=False`.

This governance contract is a predecessor precedent, not the implementation
owner for the P11.11 audit ledger.

Governance continues to own conflict evidence, conflict referral, Concordat
Court destination metadata, and its WCCD / Gravitas Mode referral methods.

P11.11 does not move, replace, or reinterpret those contracts.

## Canonical P11.11 owner

The dedicated P11.11 implementation owner is frozen as:

`apexforge/tap_check/`

TAP Check must not be implemented inside:

- `governance`;
- `tam`;
- `semantic_lattice`;
- `semantic_decision`;
- `authority`;
- `runtime`;
- `tooling`.

Those subsystems remain evidence or behavior owners.

`tooling` may later expose the CLI command, but it does not own TAP semantics.

## Canonical trace spine

The canonical trace input to TAP Check is the frozen TAM:

`TraceMap`

TAP must consume the supplied `TraceMap`.

It must not reconstruct source, token, declaration, reference, scope, type,
authority, narrative, ownership, or transformation facts already represented
by TAM.

For TAM-backed observations, exact `TraceIdentity` references must be retained.

The frozen TAM ordering contract remains observable:

- caller map-block order;
- record order inside each map;
- exact record identity;
- exact trace identity;
- no sorting;
- no deduplication;
- no evidence fabrication.

TAP may filter or index evidence for reporting, but it must not mutate the
source `TraceMap` or redefine TAM identity.

## Dedicated passive result model

P11.11 requires its own passive audit-ledger model rather than reusing
semantic-lattice, semantic-decision, authority, runtime, or governance result
types.

The minimal model owner for P11.11B is frozen as `apexforge.tap_check`.

The initial public model names are frozen as:

- `TapCheckLedgerEntry`;
- `TapCheckAuditLedger`.

The ledger is diagnostic evidence, not a semantic decision receipt and not an
authority receipt.

P11.11B will define the exact immutable fields and invariants.

The model must use frozen dataclasses and exact tuple containers.

The ledger must preserve supplied evidence order unless a later slice
explicitly freezes a category-specific canonical ordering rule.

## Core TraceMap audit API

The first narrow trace-consumer API is frozen for P11.11C as:

`audit_trace_map(trace_map: TraceMap) -> TapCheckAuditLedger`

This API is observational only.

It may summarize facts explicitly present in the supplied `TraceMap`, but it
must not:

- run a TAM producer;
- compose a replacement TraceMap;
- parse source;
- resolve names;
- infer types;
- evaluate authority;
- construct narrative semantics;
- execute semantic decisions;
- resolve convergence;
- assess Paradox Elevation;
- execute runtime behavior;
- activate directives;
- change compiler output.

P11.11B defines the model. P11.11C defines the first deterministic TraceMap
projection into that model.

## Canonical report-category coverage

The P11.11 roadmap requires TAP Check to report these ten categories in this
order:

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

This is the reporting taxonomy, not a new semantic authority taxonomy.

A category name does not authorize TAP to calculate the fact represented by
that category.

## Evidence-owner rule

TAP Check reports evidence that existing owners have already produced.

It does not become the owner of the underlying decision merely because that
decision appears in the audit ledger.

### `active-directives`

"Active" must not be inferred merely from a declaration trace.

A later adapter must consume explicit existing activation/session/runtime
evidence.

TAP never activates a directive.

### `compiler-transformations`

TAP may report already-recorded compiler or TAM transformation evidence.

It does not perform the transformation.

### `semantic-changes`

TAP may report already-produced semantic evidence or differences.

It does not run semantic evaluation merely to create a ledger item.

### `authority-intervention`

Authority remains owned by the authority subsystem.

TAP may report an already-produced authority event, check, grant, denial, or
related trace evidence.

It cannot grant, revoke, override, or reinterpret authority.

### `optimization-decisions`

Optimization remains owned by the optimization/compiler subsystem.

TAP may report an already-produced optimization decision or artifact.

It does not choose an optimization.

### `continuity-effects`

Continuity meaning remains owned by the narrative / continuity subsystem.

TAP may report already-produced continuity evidence.

### `narrative-state-changes`

Narrative state mutation remains owned by narrative/runtime owners.

TAP may report an already-produced state change.

It does not mutate narrative state.

### `convergence-rulings`

Convergence and Paradox semantics remain owned by `semantic_decision`.

TAP may report an existing ruling or validation result.

It does not rank candidates, resolve convergence, or elevate a paradox.

### `air-lowering`

AIR lowering remains owned by the compiler/lowering path.

TAP may report an existing lowering or transformation record.

It does not lower AIR.

### `runtime-results`

Runtime execution remains owned by runtime.

TAP may report an already-produced runtime result.

It does not execute the program merely to manufacture an audit entry.

## Missing-evidence semantics

The absence of evidence is not itself evidence that an event did not occur.

For every TAP report category, evidence absence must not be interpreted as a
negative result.

Examples:

- no activation evidence does not mean a directive was inactive;
- no authority-intervention evidence does not mean no authority event occurred;
- no runtime-result evidence does not mean the program did not run.

A later ledger model may represent unavailable or unobserved evidence
explicitly, but it must not fabricate a negative semantic conclusion.

## Governance non-override boundary

The predecessor governance contract establishes that structural errors and
authorization denials are non-overridable.

TAP Check does not weaken this rule.

TAP cannot use diagnostic evidence to:

- override a structural error;
- override an authorization denial;
- select a conflict winner;
- activate a directive;
- execute Concordat Court methods.

The existing `TAP_CHECK_MODE` remains observational.

## Semantic-lattice boundary

The canonical `tam.traceability` axis remains owned by the semantic lattice
and remains passive.

TAP Check does not redefine that axis and does not automatically project its
ledger into the lattice.

If a later integration explicitly projects TAP diagnostics into an existing
passive metadata surface, that projection must preserve the existing owner and
must not create semantic authority.

## External evidence beyond TAM

`TraceMap` is the canonical trace spine, but several roadmap report categories
require facts whose canonical owners are outside the frozen TAM producer set.

Later P11.11 slices may therefore introduce read-only adapters over existing
owner evidence for runtime, optimization, semantic-decision, narrative
continuity, or other already-produced facts.

Those adapters must:

- preserve the existing owner's evidence rather than recompute it;
- link back to exact TAM `TraceIdentity` values when such links already exist;
- never fabricate a TAM trace identity merely to obtain a link;
- never treat missing trace linkage as permission to infer semantics;
- never mutate the source owner or the supplied `TraceMap`.

External evidence supplements the canonical trace spine. It does not replace
it.

## CLI boundary

The later CLI command is:

`apexforge tap-check .`

The CLI remains:

- user-controlled;
- diagnostic-only;
- non-activating;
- read-only.

Running TAP Check must not silently compile, execute, authorize, activate,
optimize, mutate narrative state, resolve convergence, or change project
files merely to make the ledger more complete.

Any prerequisite artifact creation must remain owned by its normal explicit
command or workflow.

## P11.11 decomposition frozen by A

P11.11 proceeds through these architectural slices:

- **P11.11A** â€” architecture and ownership audit;
- **P11.11B** â€” minimal immutable TAP audit-ledger model;
- **P11.11C** â€” deterministic `TraceMap` observational audit projection;
- **P11.11D** â€” read-only owner-evidence adapters for the roadmap reporting
  categories that are not fully represented by TAM alone;
- **P11.11E** â€” deterministic project audit-ledger aggregation and coverage;
- **P11.11F** â€” `apexforge tap-check .` CLI integration and real `.apex`
  acceptance;
- **P11.11G** â€” final TAP Check integration, completeness census, regression,
  and freeze.

This decomposition may be extended only when an implementation audit
demonstrates a concrete missing boundary; later slices must not collapse
existing subsystem ownership into TAP.

## P11.11A completion condition

P11.11A is complete when:

- the TAM-L freeze is the exact predecessor;
- no dedicated TAP implementation existed at the entry boundary;
- governance `TAP_CHECK_MODE` remains exactly `observational`;
- passive governance referral remains non-activating;
- structural errors remain non-overridable;
- authorization denials remain non-overridable;
- `TraceMap` is frozen as the canonical TAP trace input;
- `apexforge/tap_check/` is frozen as the dedicated future owner;
- dedicated passive ledger model ownership is frozen;
- the ten roadmap report categories are frozen in roadmap order;
- missing evidence is distinguished from a negative result;
- authority, semantic-decision, semantic-lattice, compiler, optimization,
  narrative, runtime, and governance ownership remain external;
- P11.11A adds only its smoke test and this document;
- no predecessor production file is modified.

P11.11B may then introduce the minimal immutable TAP Check Audit Ledger model.