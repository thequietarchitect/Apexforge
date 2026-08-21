# P11.11C â€” TraceMap Observational Audit Projection

## Purpose

P11.11C introduces the first TAP Check behavior:

`audit_trace_map(trace_map: TraceMap) -> TapCheckAuditLedger`

The function consumes a frozen canonical TAM `TraceMap` and projects only
facts that map directly to a P11.11 reporting category without semantic
inference.

It remains observational, deterministic, non-activating, and read-only.

## Predecessor

P11.11C begins from:

`afp-p11-11b-freeze`
â†’ `295613496b2c5f8d9123fd90cd55f501c6ec76ec`

P11.11B's immutable ledger model remains the canonical TAP result model.

B's historical assertion that `audit_trace_map` was absent is not rerun after C
introduces that API. B remains protected by exact freeze ancestry and frozen
model/test/document hashes.

## Mapping-audit result

The frozen TAM production census proves several kinds of trace records, but a
TAP reporting category may be assigned only when the record's complete frozen
signature directly supports that meaning.

C therefore uses exact signature matching across:

- trace domain;
- producer;
- owner;
- representation.

A partial match is insufficient.

Unknown or future representations are omitted until a later architecture slice
explicitly maps them.

## Direct mapping table

P11.11C freezes exactly three direct mapping signatures:

| TAM domain | producer | owner | representation | TAP category |
| --- | --- | --- | --- | --- |
| `transformation` | `language.compiler` | `language.compiler` | `source-map-entry` | `compiler-transformations` |
| `authority` | `authority.model` | `authority.model` | `authority-check` | `authority-intervention` |
| `authority` | `authority.model` | `authority.model` | `authority-grant` | `authority-intervention` |

These three signatures cover two TAP report categories.

## Why `source-map-entry` maps only to compiler transformations

The frozen TAM record is explicitly:

- domain `transformation`;
- producer `language.compiler`;
- owner `language.compiler`;
- representation `source-map-entry`.

That is direct compiler-transformation evidence.

C does not additionally label the same record `air-lowering`.

Although a source-map entry may carry an AIR canonical identity, the
representation is not named as an explicit AIR-lowering event. Calling it an
AIR-lowering result would add interpretation beyond the frozen trace record.

`air-lowering` therefore remains deferred until an existing lowering owner
provides explicit evidence suitable for a later read-only TAP adapter.

## Authority mapping

`authority-check` and `authority-grant` are explicit authority evidence and map
to `authority-intervention`.

The `principal` representation does not map.

A principal is authority context/identity evidence, not itself proof that an
authority intervention occurred.

TAP does not execute the check, issue the grant, grant authority, revoke
authority, or reinterpret the underlying authority result.

## Narrative evidence

C does not map generic narrative-domain evidence to
`narrative-state-changes`.

A narrative trace can describe identities, graph evidence, validation
evidence, state facts, or other narrative semantics. Domain membership alone
does not establish that a state change occurred.

Until an exact existing representation or owner event proves a state change,
the category remains absent.

This is an omission, not a negative result.

## Resolution, type, token, declaration, ownership, and source evidence

These TAM records remain unmapped in C.

In particular:

- a resolution outcome is not automatically a `semantic-change`;
- type evidence is not automatically a `semantic-change`;
- declaration evidence is not proof of an `active-directive`;
- token evidence is not a roadmap audit event;
- source evidence is not a roadmap audit event;
- ownership evidence is not a roadmap audit event.

P11.11 does not force every TAM domain into a roadmap report category.

## One mapped record, one entry

Each mapped `TraceRecord` produces exactly one `TapCheckLedgerEntry`.

The relative order of mapped records is the same as their order in
`TraceMap.records`.

C performs no sorting or deduplication.

If mapped records occur between unmapped records, removing the unmapped
records does not reorder the mapped subset.

## Trace linkage

Every projected entry contains:

`trace_ids=(record.trace_id,)`

The exact existing `TraceIdentity` object is preserved.

C does not create a new trace identity and does not infer additional
upstream/downstream links.

## Subject rule

The passive subject is selected only from fields already present on the
`TraceRecord`:

1. use `record.canonical_identity` when present;
2. otherwise use `record.trace_id.value`.

No name lookup, source reconstruction, resolution, or owner-specific
interpretation occurs.

## Evidence rule

C serializes only explicit generic `TraceRecord` fields:

- domain;
- producer;
- owner;
- representation;
- schema version;
- canonical identity when present.

These strings are descriptive ledger evidence, not semantic truth generated by
TAP.

C does not serialize or reinterpret the source owner's private payload because
the canonical `TraceRecord` intentionally does not own that payload.

## Unmapped-record policy

The canonical policy is:

`UNMAPPED_RECORD_POLICY=OMIT`

An unmapped record is not forced into the nearest roadmap category.

An unknown future representation is also omitted until explicitly mapped.

This preserves the P11.11A rule that missing evidence is not a negative result.

An empty `TraceMap` therefore yields an empty `TapCheckAuditLedger`.

A `TraceMap` containing only unmapped records also yields an empty ledger.

## Non-authoritative boundary

`audit_trace_map` does not:

- call a TAM producer;
- compose a `TraceMap`;
- parse source;
- lower source;
- resolve names;
- infer types;
- evaluate authority;
- activate directives;
- run narrative validation;
- mutate narrative state;
- evaluate semantic decisions;
- resolve convergence;
- assess Paradox Elevation;
- choose an optimization;
- execute runtime behavior;
- write project files.

It only observes a supplied `TraceMap`.

## Public surface

After C, the TAP package public surface is:

- `TAP_CHECK_CATEGORY_IDS`;
- `TapCheckLedgerEntry`;
- `TapCheckAuditLedger`;
- `audit_trace_map`.

No project aggregator, owner-evidence adapter, renderer, or CLI is added in C.

## Deferred categories

The following roadmap categories are not directly proven by the three C
mapping signatures and remain for later read-only owner-evidence adapters:

- `active-directives`;
- `semantic-changes`;
- `optimization-decisions`;
- `continuity-effects`;
- `narrative-state-changes`;
- `convergence-rulings`;
- `air-lowering`;
- `runtime-results`.

Additional evidence may also enrich `authority-intervention` and
`compiler-transformations` later, but C's direct TAM projection remains valid.

## Completion condition

P11.11C is complete when:

- P11.11B freeze ancestry is exact;
- the B ledger model remains frozen;
- `audit_trace_map` requires an exact `TraceMap`;
- the three direct signatures map exactly as frozen;
- all other current TAM records are omitted;
- future unknown signatures are omitted;
- one mapped record produces one entry;
- mapped-record order is preserved;
- exact `TraceIdentity` references are preserved;
- subjects use only canonical identity or trace identity;
- evidence uses only generic explicit TraceRecord fields;
- empty and unmapped-only maps produce empty ledgers;
- missing evidence is not turned into a negative result;
- no TAM producer, composition, semantic inference, authority action, activation,
  or runtime execution occurs;
- predecessor owners remain unchanged;
- only TAP projection/public-surface changes, the C smoke test, and this
  document are introduced.