# P11.5C-A Narrative Semantic Graph Construction Architecture Audit

## Status

P11.2I is the controlling integration freeze for this successor branch.
P11.5B is the semantic predecessor and remains an ancestor of that integration
freeze.

The original P11.5C-A audit established the boundary before graph production
existed. The **Reviewed P11.5C-B successor** now implements that exact passive
construction boundary.

P11.5C-A owns exactly:

- `apexforge/p11_5c_narrative_semantic_graph_construction_architecture_audit_smoke_test.py`
- `docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_ARCHITECTURE_AUDIT.md`

P11.5C-B owns exactly:

- `apexforge/language/narrative_graph.py`
- `apexforge/p11_5c_narrative_semantic_graph_construction_smoke_test.py`
- `docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_CONTRACT.md`

The reviewed branch delta is the union of those five paths.

## Purpose

P11.5B supplies passive immutable narrative records. P11.5C-B projects one
`NarrativeStory` into passive immutable graph evidence without changing those
records.

The graph preserves evidence rather than deciding narrative truth.

## Required construction policy

The reviewed graph contract requires:

- declared occurrences retain duplicates;
- referenced-only identities are represented explicitly;
- a fixed relation-family order;
- source tuple order within each relation family;
- deterministic output for identical input;
- no dependence on set or dictionary iteration order.

## Required relation families

The minimum projection boundary remains:

- containment;
- dialogue participation;
- choice destination;
- perspective viewpoint;
- timeline membership;
- temporal precedence;
- narrative-state subject;
- continuity subject.

The implementation gives these relations precise API names without adding
validation or execution semantics.

## Identity and duplicate policy

Narrative identity remains the P11.5B `NarrativeIdentity` value.

Duplicate declared records remain observable. Duplicate participants, choice
paths, timeline entries, state facts, and continuity constraints also remain
observable.

A reference to an identity not declared in the same story is evidence, not an
immediate construction failure. Referenced-only identities are represented so
a later validator can classify them.

## Ordering policy

The implementation freezes:

1. story node placement;
2. declared record-family order;
3. source tuple order;
4. referenced-only node order;
5. edge relation-family order;
6. evidence-key ordering.

Hash-table iteration never determines graph output.

## Separation contracts

Narrative Semantic Graph != AIR

Narrative Semantic Graph != artifact v1

Narrative graph construction remains distinct from runtime state, execution,
rendered prose, scheduling, and project declaration resolution.

## Explicit non-goals

P11.5C-A and the reviewed P11.5C-B successor add:

- no parser integration;
- no compiler integration;
- no runtime integration;
- no diagnostics;
- no serialization;
- no source syntax;
- no project auto-discovery;
- no reachability analysis;
- no contradiction detection;
- no knowledge filtering;
- no continuity verdict;
- no graph traversal API;
- no CLI or editor behavior.

## Compatibility requirements

P11.5B `narrative_model.py` remains byte-for-byte unchanged.

The parser, compiler, project builder, AIR model, AIR serialization, runtime,
CLI, language server, VS Code, and Visual Studio remain unchanged.

The graph production API is constrained to
`apexforge/language/narrative_graph.py`.

## Acceptance boundary

The aligned audit passes when:

- both predecessor tags remain annotated and correctly related;
- the branch owns exactly the five reviewed P11.5C-A/P11.5C-B paths;
- every required policy and relation family remains documented;
- graph production declarations exist only in the one reviewed module;
- the graph module remains passive;
- P11.5B and operational files match the controlling freeze;
- running the audit does not mutate repository status.

## Proposed next stage

A later P11.5 stage may define passive graph validation and evidence
classification. It must not retroactively change P11.5B records or P11.5C-B
construction order.
