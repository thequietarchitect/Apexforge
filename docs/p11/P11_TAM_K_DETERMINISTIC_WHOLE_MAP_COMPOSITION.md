# P11-TAM-K â€” Deterministic Whole-Map Composition

## Purpose

P11-TAM-K implements the narrow whole-map composition seam frozen by
P11-TAM-J.

All ten canonical TAM domains already have dedicated production coverage.
K does not create another trace domain and does not add another semantic
model.

## Predecessor

P11-TAM-K begins from:

`afp-p11-tam-j-freeze`
â†’ `661926bd8d42e7e93f05f4d2178216ae8a91c5b6`

P11-TAM-J is an audit boundary. Its smoke test proves that whole-map
composition was absent at that stage, so that historical negative assertion
is not a forward-compatible K regression.

K instead preserves J through freeze ancestry, its frozen contract, and
direct positive verification of the composition behavior authorized by J.

## Canonical integration owner

P11-TAM-K introduces:

`apexforge/tam/integration.py`

and one public operation:

`compose_trace_maps(trace_maps: Tuple[TraceMap, ...]) -> TraceMap`

`TraceMap` remains the canonical aggregate model.

No replacement or extension of `TraceMap` is introduced.

## Composition contract

The input must be an exact tuple of exact `TraceMap` values.

Composition preserves:

- caller-supplied map block order;
- record order inside every input map;
- exact `TraceRecord` object references;
- exact `TraceIdentity` values;
- domains;
- source spans;
- canonical identities;
- provenance;
- upstream/downstream trace references.

The implementation performs ordered concatenation only and passes that
ordered record tuple to the frozen `TraceMap` constructor.

## No sorting or rewriting

Composition performs:

- no sorting;
- no ranking;
- no deduplication;
- no record rewriting;
- no trace-identity rewriting;
- no canonical-identity rewriting;
- no source-span reconstruction;
- no provenance synthesis;
- no graph-link inference.

Caller map order is therefore observable and authoritative for composition
order.

## Duplicate trace identities

The frozen `TraceMap` model already rejects duplicate trace identities.

K preserves that invariant.

When two input maps contain the same trace identity, composition fails through
the existing `TraceMap` validation rule.

K does not drop, merge, select, namespace, or rewrite either record merely to
force the composition to succeed.

## Empty, single, and partial composition

`compose_trace_maps(())` produces an empty `TraceMap`.

A one-map composition preserves the input map's records and exact record
references.

Partial domain coverage is valid. If only type and authority maps are
provided, no records for the other eight domains are fabricated.

Ten-domain coverage remains a capability property of the TAM subsystem, not a
per-program completeness requirement.

## Real ten-domain coexistence proof

The K smoke test uses all seven frozen map-producing families:

1. SourceMap projection;
2. declaration/identity projection;
3. resolution observation;
4. type evidence;
5. authority evidence;
6. narrative evidence;
7. token evidence.

Those real producers collectively provide:

- source;
- token;
- declaration;
- reference;
- scope;
- type;
- authority;
- narrative;
- ownership;
- transformation.

The K integration proof composes their resulting maps and verifies that all
ten domains coexist in one canonical `TraceMap`.

No placeholder `TraceRecord` values are constructed merely to satisfy the
ten-domain proof.

## Producer boundary

`tam.integration` does not import `tam.production` and does not invoke any
domain producer.

Domain evidence must already exist before it is passed to composition.

The smoke fixture may invoke frozen predecessor producers to obtain real
evidence for testing; the production integration function itself never does.

## Non-authoritative boundary

K performs no:

- lexing;
- tokenization;
- parsing;
- source reconstruction;
- compilation or lowering;
- name resolution;
- scope inference;
- type inference or coercion;
- authority evaluation;
- narrative graph construction;
- narrative validation;
- semantic-decision evaluation;
- convergence resolution;
- Paradox assessment;
- runtime execution;
- session mutation;
- presentation;
- editor classification;
- CLI/LSP execution.

## Semantic lattice boundary

The existing passive `tam.traceability` semantic-lattice axis remains
unchanged.

Whole-map composition does not automatically project records into the
semantic lattice.

## TAP Check boundary

The result of `compose_trace_maps` is canonical `TraceMap` evidence suitable
for later consumption by P11.11 TAP Check.

TAP Check remains a consumer of TAM evidence rather than an independent
reconstructor of the source, token, declaration, resolution, type, authority,
narrative, ownership, or transformation facts already observed by TAM.

## Completion condition

P11-TAM-K is complete when:

- J freeze ancestry is preserved;
- `tam.integration` owns one composition primitive;
- the public API exposes `compose_trace_maps`;
- all seven predecessor map-producing families are exercised;
- all ten trace domains coexist in one composed map;
- exact map-block order and record order are preserved;
- exact `TraceRecord` references survive composition;
- empty, single, and partial composition are valid;
- duplicate trace identities fail through the frozen `TraceMap` invariant;
- no sorting, deduplication, rewriting, evidence fabrication, graph inference,
  producer execution, or semantic execution enters integration;
- frozen model, production, and evidence-owner surfaces remain unchanged.