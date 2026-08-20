# P11-TAM-J â€” Final Integration Architecture Audit

## Purpose

P11-TAM-J is an audit-only stage that closes the architecture question between
the ten dedicated TAM trace-production domains and the later TAP Check
consumer.

P11-TAM-J introduces no production behavior.

Its job is to freeze the exact whole-map composition contract that the next
implementation slice may add.

## Predecessor

P11-TAM-J begins from:

`afp-p11-tam-i-freeze`
â†’ `da05b68b7906a145e4edb7c1e8e0e9f019c23f9f`

The complete A-through-I freeze chain must remain an ancestor of J.

## Current canonical model

The frozen TAM model remains:

- `TraceDomain`;
- `TraceIdentity`;
- `TraceRecord`;
- `TraceMap`.

`TraceMap` is already the correct canonical whole-TAM artifact. It is an
immutable ordered collection of `TraceRecord` values and already owns:

- duplicate trace-identity rejection;
- exact ordered record storage;
- `find(trace_id)`;
- `for_domain(domain)`.

Therefore final integration does not require a second aggregate model.

## Domain-production closure

The ten canonical domains are:

1. `source`;
2. `token`;
3. `declaration`;
4. `reference`;
5. `scope`;
6. `type`;
7. `authority`;
8. `narrative`;
9. `ownership`;
10. `transformation`.

Their dedicated producer coverage is complete through P11-TAM-I.

Source and transformation are produced by the SourceMap projection.
Declaration and ownership are produced by declaration/identity projection.
Reference and scope are produced by resolution observation.
Type, authority, narrative, and token each have dedicated evidence-map
producers.

No eleventh domain is required.

## Confirmed integration gap

At the P11-TAM-I freeze there is no canonical public operation that composes
multiple already-produced `TraceMap` values into one `TraceMap`.

The frozen model does not own `merge` or `compose` methods.

The production module contains domain evidence producers, not whole-map
integration.

This gap is narrow and should remain narrow.

## Canonical integration owner

The next implementation stage should introduce:

`apexforge/tam/integration.py`

The canonical public operation should be:

`compose_trace_maps(trace_maps: Tuple[TraceMap, ...]) -> TraceMap`

This keeps integration separate from both:

- the frozen immutable model; and
- domain-specific evidence production.

## Composition semantics

Composition consumes already-produced `TraceMap` values only.

It preserves:

- caller-supplied map block order;
- record order within each input map;
- exact TraceRecord objects;
- existing TraceIdentity values;
- existing domain ownership;
- existing source spans;
- existing canonical identities;
- existing provenance;
- existing upstream/downstream references.

The function performs no sorting.

The function performs no deduplication.

The function performs no trace identity rewriting.

The function emits records by simple ordered concatenation of input map
records into the existing `TraceMap` constructor.

## Duplicate identity contract

`TraceMap` already rejects duplicate trace identities.

Final integration must preserve that invariant rather than weaken it.

If two input maps contain the same `TraceIdentity`, composition must fail via
the existing frozen `TraceMap` duplicate-identity rule.

The integration layer must not:

- silently drop one record;
- merge two records;
- choose one record;
- invent a segment namespace;
- rewrite either identity merely to force composition.

This makes collisions explicit evidence of incompatible or repeated inputs.

## Empty and partial maps

An empty input produces empty TraceMap.

A single-map input remains equal to that map's ordered record content.

Partial domain coverage is valid.

A real program or analysis is not required to emit evidence for all ten
domains. Absent evidence remains absent.

Ten-domain coverage is a capability proof, not an input requirement.

No synthetic empty-domain `TraceRecord` may be created merely to make a
coverage counter reach ten.

## Ten-domain integration proof

The implementation smoke test should construct real frozen predecessor
evidence for all producer families and compose their resulting maps.

The resulting integration fixture should demonstrate the union of:

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

The proof must use the existing domain producers rather than constructing fake
domain-placeholder records.

The test should establish:

- same ordered maps â†’ same `TraceMap`;
- every input record survives unchanged by identity and object reference;
- input map order determines block order;
- each input map's internal order remains unchanged;
- all ten domains can coexist;
- a partial map set remains legal;
- empty input remains empty;
- duplicate trace identities fail rather than being deduplicated or rewritten.

## Non-authoritative boundary

Whole-map composition is observational only.

It must not invoke or acquire ownership of:

- lexing;
- parsing;
- source reconstruction;
- compilation;
- lowering;
- name resolution;
- scope inference;
- type inference or coercion;
- authority checking;
- narrative graph construction;
- narrative validation;
- semantic-decision evaluation;
- convergence resolution;
- Paradox assessment;
- runtime execution;
- session mutation;
- presentation;
- editor classification;
- CLI or LSP behavior.

It must not infer new graph relationships between records merely because they
share a composed map.

Existing upstream/downstream trace IDs are preserved as recorded.

## Semantic lattice boundary

The existing `tam.traceability` semantic-lattice axis remains passive.

Final TAM integration does not automatically project the canonical TraceMap
into the semantic lattice and does not fabricate a semantic-lattice TAM
subject identity.

## TAP Check consumer boundary

P11.11 TAP Check consumes canonical TraceMap evidence.

TAP Check must not reconstruct source, token, declaration, resolution, type,
authority, narrative, ownership, or transformation evidence that TAM already
provides.

This architecture therefore gives TAP Check one stable observational
container without granting TAM or TAP semantic authority.

## Next stage

The next implementation slice may add only the thin `tam.integration`
composition primitive described here, expose it through `tam.__init__`, and
prove real ten-domain coexistence plus deterministic partial composition.

No new TAM model is authorized by this audit.