# P11-TAM-B â€” Minimal Immutable Trace Model

## Purpose

P11-TAM-B introduces the first canonical production model for the Compiler
Token Analysis Map (TAM).

This slice defines immutable observational records only. It does **not**
instrument the compiler, parser, project builder, CLI, LSP, narrative system,
semantic-decision bridge, convergence machinery, Paradox Elevation, or
runtime.

The governing invariant remains:

> TAM records what existing stages produced and how artifacts relate. TAM does
> not decide what those artifacts mean.

## Predecessor

P11-TAM-B begins from:

`afp-p11-tam-a-freeze`
â†’ `d7967f0fd25d96c8bbd779627adff5aa37431b07`

P11-TAM-A's ownership audit remains authoritative for all TAM boundaries.

## Production package

P11-TAM-B introduces:

- `tam.TraceDomain`
- `tam.TraceIdentity`
- `tam.TraceRecord`
- `tam.TraceMap`

It also freezes:

- `TRACE_SCHEMA_VERSION = 1`
- the ten canonical trace-domain identifiers
- the canonical tuple of `TraceDomain` values

No specialized `TokenTrace`, `SourceTrace`, `DeclarationTrace`, or other
domain-specific class is introduced yet.

## Trace domains

The immutable domain taxonomy is:

1. `source`
2. `token`
3. `declaration`
4. `reference`
5. `scope`
6. `type`
7. `authority`
8. `narrative`
9. `ownership`
10. `transformation`

These are traceability domains, not new semantic authorities.

## TraceIdentity

`TraceIdentity` is a TAM-local stable identifier.

It identifies a trace record. It is not an AIR ID, declaration identity,
runtime identity, narrative identity, semantic-decision identity, or
semantic-lattice subject identity.

TAM therefore preserves canonical subsystem identities separately rather than
relabeling them as TAM identity.

## TraceRecord

`TraceRecord` is an immutable observational record containing:

- `trace_id`
- `domain`
- `producer`
- `owner`
- `representation`
- `schema_version`
- optional `source_span`
- optional `canonical_identity`
- `provenance`
- `upstream_trace_ids`
- `downstream_trace_ids`

### Source span

`source_span` references the existing `language.source.SourceSpan` type. TAM
does not define a replacement source-location model.

A trace may omit a source span when the observed artifact has no canonical
source location. TAM must not fabricate one.

### Canonical identity

`canonical_identity` is reference-only metadata. Its meaning remains owned by
the subsystem that produced it.

TAM does not generate a replacement AIR ID, declaration identity, narrative
identity, authority identity, or semantic-decision identity.

### Provenance

`provenance` preserves external/subsystem provenance references as immutable
strings. P11-TAM-B does not normalize those strings into a new semantic
meaning.

### Relationships

`upstream_trace_ids` and `downstream_trace_ids` are observational links between
TAM records.

P11-TAM-B does not infer missing relationships, compute transitive closure,
perform graph resolution, or require referenced records to be present in the
same `TraceMap`. This permits later stages and project-level composition to
link traces without changing the minimal model.

## TraceMap

`TraceMap` is an immutable ordered collection of `TraceRecord` values.

It:

- preserves supplied order;
- requires unique TAM trace identities;
- supports exact trace-ID lookup;
- supports domain selection;
- returns no fabricated records.

It does not perform semantic graph evaluation.

## Determinism

Construction from the same immutable inputs yields equal records and equal
maps. No timestamps, random values, environment-dependent values, memory
addresses, or implicit ordering are introduced by the model.

Later producer slices are responsible for defining deterministic trace-ID
generation from canonical compiler inputs.

## Non-ownership boundary

P11-TAM-B introduces no:

- lexer/parser instrumentation;
- compiler instrumentation;
- project-builder mutation;
- source-map mutation;
- name/reference resolution;
- type inference or type validation;
- authority decision;
- narrative interpretation;
- semantic-decision interpretation;
- convergence resolution;
- Paradox Elevation;
- semantic-lattice reinterpretation;
- CLI command;
- LSP behavior;
- runtime execution.

Existing source spans, SourceMap records, declaration identities, resolution
records, narrative semantics, semantic-decision semantics, AETHER-AIR
provenance, and semantic-lattice provenance remain owned by their frozen
subsystems.

## `tam.traceability`

The P11.8 `tam.traceability` semantic-lattice axis remains unchanged and
passive.

P11-TAM-B does not automatically project a `TraceRecord` or `TraceMap` into
the lattice. A later integration slice may use the already-frozen passive
adapter contract after producer semantics are established.

## Completion boundary

P11-TAM-B is complete when the minimal immutable data contract is frozen and
its determinism, immutability, validation, ownership boundaries, and
predecessor preservation are demonstrated.

The next TAM slice may define deterministic trace-production contracts around
existing compiler/source seams, but must consume this frozen model rather than
altering its semantic ownership rules.