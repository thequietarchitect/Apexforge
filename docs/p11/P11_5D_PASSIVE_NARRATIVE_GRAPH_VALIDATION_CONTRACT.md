# P11.5D-B Passive Narrative Graph Validation Contract

## Status

P11.5D-B is based on the annotated P11.5C freeze
`afp-p11.5c-freeze`, resolving to
`d7d19bb84845400c4b004c52e011c89a4a9b1c0d`.

P11.5D-B owns exactly:

- `apexforge/language/narrative_validation.py`
- `apexforge/p11_5d_passive_narrative_graph_validation_smoke_test.py`
- `docs/p11/P11_5D_PASSIVE_NARRATIVE_GRAPH_VALIDATION_CONTRACT.md`

The aligned P11.5D-A architecture audit retains separate ownership of its two
audit files.

## Purpose

P11.5D-B consumes an immutable `NarrativeSemanticGraph` and produces immutable
ordered validation evidence.

It does not change the graph, choose a narrative branch, interpret free-form
continuity prose, emit source diagnostics, or execute narrative state.

Classification is not a diagnostic.

## Public API

The production module exports exactly:

```python
NarrativeValidationFinding
NarrativeValidationReport
validate_narrative_semantic_graph
```

No validator object, mutable context, registry, diagnostic emitter, or
serialization API is introduced.

## Finding model

`NarrativeValidationFinding` contains:

- `classification: str`
- `identities: tuple[NarrativeIdentity, ...]`
- `node_indexes: tuple[int, ...]`
- `edge_indexes: tuple[int, ...]`
- `evidence: tuple[tuple[str, str], ...]`

Indexes are strictly increasing and identify evidence in the frozen graph.
Evidence keys are unique and canonically ordered.

Every finding contains at least one node or edge index.

## Report model

`NarrativeValidationReport` contains:

- `story: NarrativeIdentity`
- `findings: tuple[NarrativeValidationFinding, ...]`

The report is immutable and equality-comparable.

## Classification vocabulary

P11.5D-B supports exactly:

- `duplicate_declaration`
- `referenced_only_identity`
- `conflicting_state_value`
- `temporal_cycle`
- `repeated_relation_evidence`
- `continuity_assertion_cluster`
- `perspective_cluster`

These names are passive classification values, not diagnostic codes.

## Deterministic family order

Findings are emitted in fixed family order:

1. duplicate declarations
2. referenced-only identities
3. conflicting state values
4. temporal cycles
5. repeated relation evidence
6. continuity assertion clusters
7. perspective clusters

Within a family, first graph evidence controls output order.

No public ordering depends on set or dictionary iteration.

## Duplicate declarations

A duplicate declaration finding groups all declared node occurrences with the
same exact `NarrativeIdentity`.

Referenced-only nodes do not participate in duplicate declaration findings.

## Referenced-only identities

Each graph node with `declared=False` produces one referenced-only finding in
graph node order.

This is graph-local evidence. It is not proof that the identity is globally
missing from every future linking context.

## Conflicting state values

`state_subject` edges are grouped by exact target identity and exact state-name
string.

A finding is produced only when more than one distinct passive value string is
present.

P11.5D-B does not interpret value types, branch scope, chronology, or truth.

## Temporal cycles

Cycles are detected only over directed `precedes` edges.

Each cyclic strongly connected component produces one finding. A one-identity
component is cyclic only when it contains a self-loop.

Cycle findings are ordered by their earliest involved edge.

A temporal cycle is not runtime deadlock or automatic proof that all narrative
readings are impossible.

## Repeated relation evidence

Repeated evidence is grouped by relation, source, target, and passive semantic
evidence.

Index-only evidence keys are ignored for this comparison:

- `index`
- `constraint_index`
- `subject_index`

Story `contains` edges are excluded because duplicate declarations already
classify repeated declaration containment.

This permits repeated participants and repeated timeline membership to remain
observable without assigning severity.

## Continuity assertion clusters

Two or more `continuity_subject` edges targeting the same identity produce a
cluster finding.

The assertion strings remain preserved on the graph edges. P11.5D-B does not
interpret those free-form strings and does not call the cluster contradictory.

## Perspective clusters

Two or more `viewpoint` edges targeting the same identity produce a perspective
cluster.

Multiple perspectives are not inherently conflicting.

## Compatibility boundary

P11.5D-B does not modify:

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

P11.5D-B adds:

- no diagnostic codes or severities;
- no diagnostic messages;
- no source spans;
- no parser or compiler integration;
- no runtime or CLI integration;
- no graph serialization;
- no natural-language contradiction inference;
- no branch reachability analysis;
- no knowledge or revelation analysis;
- no repair suggestions;
- no story generation;
- no editor squiggles, hover, outline, completion, or navigation.

## Acceptance contract

P11.5D-B passes when:

- the exact annotated P11.5C predecessor remains intact;
- the reviewed P11.5D candidate owns exactly five paths;
- findings and reports are immutable;
- the classification vocabulary is exact;
- identical graphs produce identical reports;
- the P11.5C-X experimental graph produces the expected nine findings;
- continuity and perspective findings remain non-contradiction clusters;
- no operational subsystem changes;
- running validation does not mutate repository state.

## Proposed next stage

A later P11.5 stage may define diagnostic projection from selected passive
findings after source syntax and source evidence exist.

Diagnostic projection must remain separate from this passive validator and must
not retroactively change P11.5C graph ordering or P11.5D-B finding ordering.
