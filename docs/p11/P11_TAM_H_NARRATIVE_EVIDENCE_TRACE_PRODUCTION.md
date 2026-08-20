# P11-TAM-H â€” Narrative Evidence Trace Production

## Purpose

P11-TAM-H adds deterministic TAM projection for already-existing canonical
narrative semantic model, graph, and validation evidence.

The slice is observational. It does not parse narrative source, lower source
AST, build a narrative graph, validate a graph, analyze a source/project,
execute narrative transitions, mutate sessions, or render presentation.

## Predecessor

P11-TAM-H begins from:

`afp-p11-tam-g-freeze`
â†’ `c3043f8d7e1f37ed05f0a86a5b6b5613d7b1263b`

P11-TAM-B through P11-TAM-G remain predecessor capabilities.

## Canonical semantic evidence boundary

P11-TAM-H consumes passive records owned by:

- `language.narrative_model`;
- `language.narrative_graph`;
- `language.narrative_validation`.

The supported semantic-model surface is:

- `NarrativeIdentity`;
- `NarrativeCharacter`;
- `NarrativeScene`;
- `NarrativeDialogue`;
- `NarrativeChoicePath`;
- `NarrativeChoice`;
- `NarrativePerspective`;
- `NarrativeTimeline`;
- `NarrativeStateFact`;
- `NarrativeState`;
- `NarrativeContinuityConstraint`;
- `NarrativeContinuity`;
- `NarrativeStory`.

The supported graph/validation surface is:

- `NarrativeGraphNode`;
- `NarrativeGraphEdge`;
- `NarrativeSemanticGraph`;
- `NarrativeValidationFinding`;
- `NarrativeValidationReport`.

These objects must already exist before TAM observes them.

## Excluded source-analysis and runtime surfaces

Narrative source-AST values remain owned by `language.narrative_source`.
Parsing and lowering remain owned by their existing P11.5 modules.

`NarrativeSourceAnalysis` and `NarrativeProjectAnalysis` are analysis pipeline
aggregates. TAM-H observes their canonical component semantic story, graph,
and validation records directly rather than duplicating the aggregate pipeline
as a TAM subject.

Runtime execution, binding, transition, observability, session persistence,
interactive UX, and presentation/rendering remain P11.6 owners and are
excluded from TAM-H production.

## Production API

P11-TAM-H introduces:

- `trace_record_from_narrative_evidence(evidence, evidence_index=...)`;
- `trace_map_from_narrative_evidence(evidence)`.

The map producer requires an exact tuple and preserves input order.

## Narrative-domain mapping

Every record uses the existing canonical TAM `narrative` domain.

The producer/owner field remains the exact frozen module that owns the
observed semantic value.

## Identity preservation

`NarrativeIdentity` owns a canonical `kind` plus ordered `path` tuple.

The existing semantic-lattice boundary preserves the path tuple rather than
inventing an AIR-style string identity. TAM-H follows the same rule.

`TraceRecord.canonical_identity` therefore remains `None` for narrative
records. The existing kind/path structure is preserved in the deterministic
TAM-local `TraceIdentity`.

This is identity preservation without string-identity fabrication.

## Semantic-content preservation

TAM-local identity preserves the already-existing factual fields of the
observed narrative records, including where applicable:

- scene title/body prose;
- dialogue scene, speaker, participants, and text;
- choice labels, destinations, conditions, and consequences;
- perspective viewpoint;
- timeline scene order;
- narrative-state facts;
- continuity subjects/assertions;
- story aggregate ordering;
- graph declared/reference state;
- graph relations and passive edge evidence;
- validation classifications, identity evidence, node/edge indexes, and
  passive evidence.

TAM does not interpret or recompute those facts.

## Source-span and provenance boundary

Semantic narrative model, graph, and validation records do not themselves own
a canonical source span. TAM-H therefore uses `source_span=None`.

Graph-edge and validation evidence remain their owners' factual evidence.
They are not silently promoted into TAM provenance.

P11-TAM-H also infers no upstream/downstream TAM graph edges.

## Forbidden behavior

`tam.production` must not invoke:

- `build_narrative_semantic_graph`;
- `validate_narrative_semantic_graph`;
- `lower_narrative_source`;
- `parse_narrative_source`;
- source/project narrative analysis;
- narrative execution/binding/transition/observability;
- narrative session creation, stepping, termination, or persistence;
- interactive narrative behavior;
- narrative presentation/rendering.

Therefore:

- `NARRATIVE_GRAPH_CONSTRUCTION=NONE`;
- `NARRATIVE_VALIDATION_EXECUTION=NONE`;
- `NARRATIVE_LOWERING=NONE`;
- `NARRATIVE_PARSING=NONE`;
- `NARRATIVE_ANALYSIS_EXECUTION=NONE`;
- `NARRATIVE_RUNTIME_EXECUTION=NONE`;
- `SESSION_MUTATION=NONE`;
- `PRESENTATION_EXECUTION=NONE`.

## Fixture rule

The P11-TAM-H smoke test may call frozen P11.5 graph construction and
validation only to obtain real already-produced evidence for the test fixture.

That fixture execution does not occur in `tam.production` and grants TAM no
graph-construction or validation ownership.

## Completion condition

P11-TAM-H is complete when:

- TAM-G freeze ancestry is proven;
- canonical narrative model, graph, and validation evidence are projected;
- all records use the `narrative` domain;
- kind/path identity is preserved without fabricated string identity;
- prose, choice, state, continuity, graph, and validation facts are preserved;
- input order and repeated projection are deterministic;
- source AST ownership remains separate;
- no source span, provenance, or TAM graph link is fabricated;
- no parsing, lowering, graph building, validation, source/project analysis,
  runtime execution, session mutation, or presentation execution occurs in
  TAM production;
- frozen narrative, semantic-lattice, compiler/tooling, and prior TAM owners
  remain unchanged;
- durable P11.5 and TAM predecessor regressions remain green.