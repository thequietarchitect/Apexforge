# P11.11E â€” Deterministic Whole-Ledger Aggregation and Category Coverage

## Purpose

P11.11E introduces pure TAP-owned aggregation over already-produced
`TapCheckAuditLedger` values and a deterministic category-coverage census.

E does not produce evidence.

It composes evidence that C, D, or another explicitly authorized TAP producer
has already placed into immutable ledgers.

## Predecessor

P11.11E begins from:

`afp-p11-11d-freeze`
â†’ `f8a3b6ddc2115ffa8f02033c4a45cf5b722bcc44`

The B model, C `TraceMap` projection, and D owner-evidence adapters remain
frozen.

D's exact nine-symbol public-surface assertion becomes a historical
stage-boundary proof when E adds two public aggregation APIs. D's durable
adapter implementation remains protected by frozen file hashes.

## Owner

The aggregation owner is:

`tap_check.aggregation`

It owns no source discovery, project discovery, compilation, execution,
semantic evaluation, or evidence production.

## Ledger composition API

E adds:

`compose_tap_check_ledgers(ledgers: Tuple[TapCheckAuditLedger, ...]) -> TapCheckAuditLedger`

The input must be an exact tuple.

Every element must be an exact `TapCheckAuditLedger`.

Composition is a direct concatenation of ledger blocks:

1. preserve caller-supplied ledger-block order;
2. preserve entry order inside each ledger;
3. preserve exact `TapCheckLedgerEntry` object references.

E performs no sorting.

E performs no deduplication.

E performs no entry rewriting.

Equal or duplicate entries remain present if the caller supplied them.

An empty input tuple produces an empty ledger.

An empty ledger block is legal and contributes no entries.

## Category coverage API

E adds:

`tap_check_category_coverage(ledger: TapCheckAuditLedger) -> Tuple[Tuple[str, int], ...]`

The input must be an exact `TapCheckAuditLedger`.

The result always contains exactly ten rows, one for each
`TAP_CHECK_CATEGORY_IDS` value, in canonical roadmap order.

Each row is:

`(category_id, observed_entry_count)`

The count is the number of entries currently present in the supplied ledger
whose `category_id` equals that category.

The result is an exact tuple of exact two-item tuples.

## Zero-count semantics

A zero count means only:

`no observed TAP ledger entry is present for this category`

It does not mean:

- the underlying event did not occur;
- the directive was inactive;
- no semantic change happened;
- no optimization happened;
- no continuity effect happened;
- no runtime behavior occurred.

This preserves the P11.11A rule that missing evidence is not a negative
semantic result.

## Partial category coverage

Partial coverage is valid.

For example, the current C/D evidence surfaces can populate several roadmap
categories while `semantic-changes`, `optimization-decisions`, or
`continuity-effects` may still have zero observed entries.

E does not fabricate entries to make coverage complete.

## Evidence-production boundary

Aggregation must not call:

- `audit_trace_map`;
- `adapt_runtime_result`;
- `adapt_convergence_ruling`;
- `adapt_narrative_state_change`;
- `adapt_air_lowering`;
- `adapt_active_directive`.

The caller explicitly supplies already-produced ledgers.

This keeps production ownership visible and prevents aggregation from silently
executing or reconstructing evidence.

## Semantic and execution boundary

E owns no:

- parsing;
- compilation;
- TAM production;
- TraceMap composition;
- authority evaluation;
- semantic inference;
- convergence resolution;
- Paradox Elevation;
- generic lowering;
- directive execution;
- runtime execution;
- narrative-state mutation;
- project I/O.

It imports only the TAP model contract necessary to compose and count entries.

## Public surface

After E, the TAP public surface is:

- `TAP_CHECK_CATEGORY_IDS`;
- `TapCheckLedgerEntry`;
- `TapCheckAuditLedger`;
- `audit_trace_map`;
- `adapt_runtime_result`;
- `adapt_convergence_ruling`;
- `adapt_narrative_state_change`;
- `adapt_air_lowering`;
- `adapt_active_directive`;
- `compose_tap_check_ledgers`;
- `tap_check_category_coverage`.

## Deferred project orchestration

E does not discover source files or owner artifacts and does not create a
project-level TAP workflow.

Project/source discovery and the user-facing `apexforge tap-check .` route
remain deferred to later CLI integration.

That future integration must explicitly decide which already-produced evidence
sources are available and must preserve the pure aggregation contract.

## Completion condition

P11.11E is complete when:

- P11.11D freeze ancestry is exact;
- B model, C projection, and D adapters remain frozen;
- composition requires an exact tuple of exact ledgers;
- caller ledger-block order and ledger entry order are preserved;
- exact entry object references are preserved;
- duplicate entries are preserved;
- empty composition produces an empty ledger;
- category coverage always emits ten rows in canonical category order;
- coverage values count observed entries only;
- zero counts remain absence-of-observation rather than semantic negatives;
- aggregation invokes no evidence producer;
- aggregation performs no semantic inference, runtime execution, or project I/O;
- existing evidence owners remain unchanged.