# P11.5D-A Narrative Graph Validation Architecture Audit

## Status

P11.5C is the frozen construction predecessor. Its annotated freeze tag is
`afp-p11.5c-freeze`, resolving to
`d7d19bb84845400c4b004c52e011c89a4a9b1c0d`.

The original P11.5D-A audit established the boundary before production
validation existed. The **reviewed P11.5D-B successor** now implements that
boundary through one passive production module.

P11.5D-A owns exactly:

- `apexforge/p11_5d_narrative_graph_validation_architecture_audit_smoke_test.py`
- `docs/p11/P11_5D_NARRATIVE_GRAPH_VALIDATION_ARCHITECTURE_AUDIT.md`

P11.5D-B owns exactly:

- `apexforge/language/narrative_validation.py`
- `apexforge/p11_5d_passive_narrative_graph_validation_smoke_test.py`
- `docs/p11/P11_5D_PASSIVE_NARRATIVE_GRAPH_VALIDATION_CONTRACT.md`

## Purpose

P11.5C preserves ordered graph evidence without judging it. P11.5D-B consumes
that graph and produces immutable passive classifications.

Validation consumes the graph without mutating it.

Classification is not a diagnostic. It supplies no source span, severity,
compiler failure, runtime failure, or editor presentation.

## Validation boundary

The reviewed validator may inspect only:

- story identity;
- ordered graph nodes;
- declared and referenced-only status;
- ordered graph edges;
- relations;
- endpoint identities;
- passive edge evidence.

It must not rewrite narrative records, graph records, source text, AIR,
artifacts, runtime state, or editor state.

## Deterministic evidence classes

The reviewed production contract classifies:

- duplicate declaration;
- referenced-only identity;
- conflicting state value;
- temporal cycle;
- repeated relation evidence;
- continuity assertion cluster;
- perspective cluster.

These are structural evidence classifications, not diagnostic codes.

## Non-contradiction boundaries

Free-form continuity text is not semantically interpreted.

A continuity assertion cluster is not automatically a contradiction.

Multiple perspectives are not inherently contradictory.

Repeated participants, scenes, paths, or relations are observable but do not
automatically receive error meaning.

A referenced-only identity is graph-local unresolved evidence, not proof of
global absence.

## Ordering and identity policy

The validator uses a fixed classification-family order and deterministic
first-evidence order within each family.

Exact `NarrativeIdentity`, relation, and passive evidence equality govern
grouping.

Temporal-cycle findings are anchored to their earliest involved edge.

No public result order depends on set or dictionary iteration.

## Production boundary

P11.5D-B introduces one passive production module:

`apexforge/language/narrative_validation.py`

That module contains exactly the reviewed finding, report, and validation
function surface.

It emits no source diagnostic and performs no integration.

## Compatibility boundary

P11.5D changes none of the following:

- P11.5B narrative records;
- P11.5C graph records, relations, builder, or ordering;
- lexer or grammar;
- parser;
- compiler;
- project construction;
- AIR;
- artifact v1;
- runtime;
- CLI;
- language server;
- VS Code;
- Visual Studio;
- existing diagnostics.

## Explicit non-goals

P11.5D adds:

- no diagnostic codes;
- no diagnostic messages;
- no severity;
- no source spans;
- no parser integration;
- no compiler integration;
- no runtime integration;
- no CLI integration;
- no graph serialization;
- no branch reachability analysis;
- no natural-language contradiction inference;
- no repair;
- no story generation;
- no editor integration.

## Acceptance contract

The aligned audit passes when:

- the exact annotated P11.5C freeze remains intact;
- the reviewed branch owns exactly five P11.5D paths;
- the passive production API remains in one file;
- all seven evidence classifications remain explicit;
- continuity and perspective remain non-contradiction clusters;
- deterministic first-evidence order remains explicit;
- no operational subsystem changes;
- running the audit does not mutate repository status.

## Proposed next stage

A later P11.5 stage may project selected passive findings into source
diagnostics only after narrative source syntax and source evidence exist.

That later projection must not change P11.5C graph ordering or P11.5D-B
classification ordering.
