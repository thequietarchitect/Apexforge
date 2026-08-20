# P11-TAM-C â€” Deterministic Trace Production Foundation

## Purpose

P11-TAM-C introduces the first canonical producer of Compiler Token Analysis
Map records.

The slice is intentionally a **pure adapter**. It consumes existing canonical
`SourceSpan`, `SourceMapEntry`, and `SourceMap` evidence and returns the frozen
P11-TAM-B `TraceIdentity`, `TraceRecord`, and `TraceMap` values.

It does not instrument the compiler or alter any producing subsystem.

## Predecessor

P11-TAM-C begins from:

`afp-p11-tam-b-freeze`
â†’ `1cac37a13af6ab229401277848a1a1c6bfef3c4b`

`tam.model` remains frozen from P11-TAM-B.

## Production API

P11-TAM-C introduces `tam.production` with three pure functions:

- `trace_identity_for_source_span(span)`
- `trace_identity_for_source_map_entry(entry, entry_index=...)`
- `trace_map_from_source_map(source_map)`

The functions are exported from `tam.__init__`.

## Deterministic identities

TAM-local trace IDs are derived only from canonical input evidence.

Source-span trace identity incorporates the canonical source name and exact
start/end source coordinates.

Source-map-entry trace identity incorporates:

- the entry's deterministic position in the frozen `SourceMap` order;
- the existing AIR ID;
- the exact source-span coordinates.

The identity digest uses SHA-256 and contains no timestamp, randomness,
process ID, Python memory address, filesystem timestamp, or mutable global
counter.

Therefore the same canonical input yields the same TAM identity.

The source-map entry index is part of the observed canonical ordered evidence.
It prevents separate entries with otherwise identical visible location and AIR
identity from collapsing into one TAM record.

## Source records

Each distinct observed `SourceSpan` produces one `source`-domain `TraceRecord`.

The record:

- keeps the exact existing `SourceSpan` object;
- uses `language.source` as producer and owner;
- uses `source-span` as representation;
- does not fabricate a canonical semantic identity;
- does not fabricate provenance;
- records only the TAM IDs of source-map observations downstream from it.

When multiple `SourceMapEntry` values use the same source span, the source
record is emitted once and references each corresponding downstream mapping.

## Source-map records

Every existing `SourceMapEntry` produces one `transformation`-domain
`TraceRecord`.

The record:

- keeps the exact existing `SourceSpan`;
- references `SourceMapEntry.air_id` as `canonical_identity`;
- uses `language.compiler` as producer and owner;
- uses `source-map-entry` as representation;
- links upstream to the corresponding source trace;
- adds no inferred provenance or semantic payload.

Calling the TAM record a `transformation` observation does not transfer
compiler semantic ownership to TAM. The existing compiler remains the owner.

## Ordering

`trace_map_from_source_map` iterates the existing `SourceMap.entries` tuple
without re-sorting it.

Transformation records therefore preserve source-map entry order. A source
record is inserted immediately before the first transformation record that
observes its span.

No semantic reordering is performed.

## Empty and missing evidence

An empty `SourceMap` produces an empty `TraceMap`.

TAM does not synthesize source locations, AIR IDs, provenance, declarations,
references, semantic objects, or graph nodes when the producing subsystem did
not provide them.

This establishes:

`MISSING_EVIDENCE=NO_FABRICATION`

## Frozen ownership boundary

P11-TAM-C does not modify:

- `language.source`;
- `language.compiler`;
- `language.project`;
- `ProjectBuilder`;
- project loading or CLI routing;
- LSP diagnostics;
- narrative analysis;
- semantic-decision analysis/project composition;
- semantic-lattice adapters;
- runtime execution.

No compiler function calls TAM automatically in this slice.

The smoke test may invoke the frozen compiler to obtain real canonical
`SourceMap` evidence for acceptance testing. That is test consumption, not
production instrumentation.

## Semantic boundary

P11-TAM-C performs no:

- parsing;
- compilation;
- declaration resolution;
- reference resolution;
- type analysis;
- authority decision;
- narrative interpretation;
- convergence;
- Paradox Elevation;
- runtime execution.

It converts already-produced evidence into observational TAM records.

## Completion condition

P11-TAM-C is complete when:

- frozen TAM-B model reuse is proven;
- real `SourceMap` evidence is accepted;
- repeated input yields equal trace IDs and maps;
- source-map entry order is preserved;
- exact `SourceSpan` references are preserved;
- AIR IDs remain references only;
- no missing evidence is fabricated;
- the compiler and other frozen owners remain unchanged;
- no CLI/LSP or runtime integration is introduced.

Later TAM slices may add producers for additional frozen evidence domains and,
only after those producer contracts are stable, controlled instrumentation.