# P11.11B â€” Minimal Immutable TAP Check Audit Ledger Model

## Purpose

P11.11B introduces the first dedicated TAP Check production package and the
minimal immutable data model frozen by P11.11A.

This slice defines passive audit-ledger records only.

It does not project a `TraceMap`, inspect a project, execute compiler behavior,
activate directives, evaluate authority, execute runtime behavior, or expose
the `apexforge tap-check .` CLI.

## Predecessor

P11.11B begins from:

`afp-p11-11a-freeze`
â†’ `e8d541a61cce3c27f3b1154b21e684453c5612ce`

P11.11A remains a historical architecture stage-boundary proof. Its
"no dedicated TAP implementation at entry" assertion is not a forward
regression after this slice introduces the dedicated package.

A is protected by exact freeze ancestry and frozen artifact hashes.

## Dedicated owner

The production owner is:

`apexforge/tap_check/`

P11.11B adds:

- `tap_check.model`;
- the package public surface in `tap_check.__init__`.

No predecessor owner moves into TAP.

## Canonical category taxonomy

`TAP_CHECK_CATEGORY_IDS` freezes the ten roadmap reporting categories in
roadmap order:

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

The taxonomy is reporting metadata. It does not give TAP authority to produce
the underlying semantic fact.

## `TapCheckLedgerEntry`

One immutable entry contains:

- `category_id: str`;
- `subject: str`;
- `evidence: Tuple[str, ...] = ()`;
- `trace_ids: Tuple[TraceIdentity, ...] = ()`.

`category_id` must be one of `TAP_CHECK_CATEGORY_IDS`.

`subject` is required passive identification text.

`evidence` is an exact tuple of non-empty strings. B does not interpret the
strings or assign semantic truth to them.

`trace_ids` is an exact tuple of existing canonical TAM `TraceIdentity`
objects.

B does not manufacture a trace identity.

Supplied evidence and trace-id order are preserved exactly. Duplicate values
are not silently removed or reordered.

## `TapCheckAuditLedger`

The minimal ledger contains:

`entries: Tuple[TapCheckLedgerEntry, ...] = ()`

The entries container must be an exact tuple of exact
`TapCheckLedgerEntry` instances.

Input order is preserved.

An empty ledger is valid.

Partial category coverage is valid.

No entry is synthesized merely because a roadmap category is absent.

Therefore, a missing category remains absent and is not a negative semantic
result.

## Immutability

Both model types are frozen dataclasses.

The model does not expose mutable list or dictionary containers.

P11.11B performs validation of its own representation contract only:

- canonical category id;
- non-empty passive text;
- exact tuple containers;
- exact `TraceIdentity` links;
- exact ledger-entry element type.

That validation is not compiler, semantic, authority, narrative, convergence,
or runtime validation.

## Non-authoritative boundary

The model owns no:

- parsing;
- name resolution;
- type inference;
- authority evaluation;
- semantic-decision evaluation;
- convergence resolution;
- Paradox Elevation assessment;
- directive activation;
- optimization choice;
- narrative-state mutation;
- AIR lowering;
- runtime execution.

It also owns no `TraceMap` projection in this slice.

## Missing evidence

P11.11A froze the distinction between absence of evidence and evidence of
absence.

P11.11B preserves that distinction structurally:

- an empty ledger is valid;
- partial category coverage is valid;
- absent categories remain absent;
- no negative entry is fabricated.

A later adapter may explicitly preserve evidence that an existing owner
produced a negative result. That is different from TAP inferring a negative
result from missing evidence.

## Public surface

The initial package surface is:

- `TAP_CHECK_CATEGORY_IDS`;
- `TapCheckLedgerEntry`;
- `TapCheckAuditLedger`.

No projection, aggregation, CLI, rendering, or execution API is public in B.

## Deferred to P11.11C

P11.11C introduces the first narrow consumer operation frozen by A:

`audit_trace_map(trace_map: TraceMap) -> TapCheckAuditLedger`

C must consume canonical TAM evidence observationally and must preserve B's
immutable model contract.

## Completion condition

P11.11B is complete when:

- P11.11A freeze ancestry and hashes remain exact;
- the ten category ids are present in roadmap order;
- both models are frozen dataclasses;
- exact tuple containers are enforced;
- supplied entry/evidence/trace-id order is preserved;
- exact existing `TraceIdentity` references are preserved;
- duplicates are not silently deduplicated;
- empty ledgers and partial category coverage remain valid;
- missing categories do not fabricate negative results;
- no `TraceMap` projection occurs;
- no semantic, authority, activation, or runtime behavior occurs;
- predecessor production owners remain unchanged;
- only the new TAP package, B smoke test, and B document are introduced.