# P11.5C-B Narrative Semantic Graph Construction Contract

## Status

P11.2I is the controlling integration freeze for this successor branch.
P11.5B is the semantic predecessor and remains an ancestor of that integration
freeze.

P11.5C-B owns exactly:

- `apexforge/language/narrative_graph.py`
- `apexforge/p11_5c_narrative_semantic_graph_construction_smoke_test.py`
- `docs/p11/P11_5C_NARRATIVE_SEMANTIC_GRAPH_CONSTRUCTION_CONTRACT.md`

The inherited P11.5C-A audit owns its separate two-file architecture evidence.

## Purpose

P11.5B introduced passive immutable narrative records. P11.5C-B projects one
exact `NarrativeStory` into passive immutable graph evidence.

The graph preserves semantic evidence. It does not decide narrative truth.

Narrative Semantic Graph != AIR

Narrative Semantic Graph != artifact v1

## Public API

The module exports exactly:

```python
NarrativeGraphNode
NarrativeGraphEdge
NarrativeSemanticGraph
build_narrative_semantic_graph
```

No other public operation is introduced.

## Node model

`NarrativeGraphNode` contains:

- `identity: NarrativeIdentity`
- `declared: bool`

The graph begins with its declared story node.

Declared record occurrences retain collection order and duplicates.
Referenced-only identities are appended once in first-encounter order with
`declared=False`.

P11.5C-B deliberately preserves duplicate declaration evidence. Duplicate
identity validation remains deferred.

## Edge model

`NarrativeGraphEdge` contains:

- `relation: str`
- `source: NarrativeIdentity`
- `target: NarrativeIdentity`
- `evidence: tuple[tuple[str, str], ...]`

Evidence keys are unique and canonically ordered by key. Evidence remains
passive string data. Constructors emit no ApexForge diagnostic.

The fixed P11.5C-B relation vocabulary is:

- `contains`
- `occurs_in`
- `spoken_by`
- `participant`
- `leads_to`
- `viewpoint`
- `timeline_scene`
- `precedes`
- `state_subject`
- `continuity_subject`

## Graph model

`NarrativeSemanticGraph` contains:

- `story: NarrativeIdentity`
- `nodes: tuple[NarrativeGraphNode, ...]`
- `edges: tuple[NarrativeGraphEdge, ...]`

The graph is frozen and equality-comparable. Every edge endpoint must occur in
the graph node tuple.

P11.5C-B defines no node ID or edge ID separate from narrative identities and
tuple order.

## Deterministic construction order

Identical `NarrativeStory` input produces identical graph output.

Declared nodes use this fixed family order:

1. story
2. characters
3. scenes
4. dialogues
5. choices
6. perspectives
7. timelines
8. narrative states
9. continuities

Collection order and duplicate occurrences are retained within each family.

Referenced-only nodes follow declared nodes in first-encounter order.

Edges are emitted in this fixed relation-family traversal:

1. story containment for every declared record occurrence
2. dialogue scene, speaker, and participant relations
3. choice scene and ordered path destinations
4. perspective viewpoint relations
5. timeline membership and adjacent-scene temporal precedence
6. narrative-state subject facts
7. continuity subjects

Graph ordering never depends on set or dictionary iteration.

## Evidence projection

Choice-destination edges preserve:

- path index
- label
- optional condition
- optional consequence

Dialogue-participation and timeline-membership edges preserve tuple index.

Temporal-precedence edges preserve adjacency index and timeline identity.

Narrative-state subject edges preserve:

- fact index
- fact name
- fact value

Continuity-subject edges preserve:

- constraint index
- subject index
- assertion

## Duplicate and unresolved evidence

P11.5C-B does not reject:

- duplicate declared narrative identities
- duplicate participants
- duplicate choice paths
- repeated timeline scenes
- contradictory state facts
- contradictory continuity assertions
- references to identities not declared in the same story

Instead, construction preserves available evidence. Referenced-only identities
become graph nodes with `declared=False`.

Validation, contradiction classification, reachability, and diagnostics remain
deferred.

## Compatibility boundary

P11.5C-B does not modify:

- `language/narrative_model.py`
- lexer, grammar, parser, or compiler
- project construction or declaration resolution
- AIR models, verification, or serialization
- runtime state, execution, traces, or reports
- CLI behavior
- build artifact v1
- language-server behavior
- VS Code or Visual Studio integration

## Explicit non-goals

P11.5C-B adds:

- no narrative source syntax
- no automatic project integration
- no graph traversal or query APIs
- no reachability analysis
- no contradiction detection
- no knowledge or revelation analysis
- no perspective accessibility rules
- no timeline validation
- no continuity validation
- no narrative diagnostic codes or messages
- no source spans or recovery
- no graph serialization
- no graph rendering
- no story generation
- no runtime scheduling or execution
- no editor integration

## Acceptance contract

P11.5C-B passes when:

- both predecessor tags remain annotated and correctly related;
- the reviewed branch owns exactly the two P11.5C-A files and three P11.5C-B
  files;
- the public API is exact and immutable;
- identical input produces identical graph output;
- fixed family and source ordering is preserved;
- duplicate evidence remains observable;
- referenced-only identities are projected deterministically;
- choice, timeline, state, and continuity evidence is retained;
- no operational subsystem changes;
- running both smoke tests does not mutate repository state.

## Proposed next stage

A later P11.5 stage may define semantic graph validation and passive evidence
classification. That stage must consume this graph without mutating P11.5B
records or retroactively changing P11.5C-B construction order.
