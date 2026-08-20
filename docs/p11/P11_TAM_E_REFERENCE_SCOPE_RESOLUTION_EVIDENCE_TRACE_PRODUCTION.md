# P11-TAM-E â€” Reference, Scope, and Resolution-Evidence Trace Production

## Purpose

P11-TAM-E extends the deterministic Compiler Token Analysis Map producer layer
to already-existing project reference, scope, candidate, and resolution
outcome contracts.

TAM observes frozen resolution evidence. It does not resolve names.

## Predecessor

P11-TAM-E begins from:

`afp-p11-tam-d-freeze`
â†’ `8b97f4336d724155e423ec3cf6ef9fddd3c210da`

P11-TAM-B through P11-TAM-D remain predecessor capabilities.

## Frozen input contracts

P11-TAM-E consumes:

- `ProjectResolutionQuery`;
- `ProjectResolutionContext`;
- `ProjectResolutionCandidate`;
- `ProjectResolutionCandidateIndex`;
- `ProjectResolvedBinding`;
- `ProjectUnresolvedResolution`;
- `ProjectAmbiguousResolution`.

These types remain owned by their existing `language.resolution_*` modules.

## Production API

P11-TAM-E introduces:

- `trace_record_from_resolution_query(query)`;
- `trace_record_from_resolution_context(context)`;
- `trace_record_from_resolution_candidate(candidate, candidate_index=...)`;
- `trace_record_from_resolution_outcome(outcome)`;
- `trace_map_from_resolution_observation(index, query, context, outcome)`.

The aggregate consumes a canonical candidate index, already-formed query,
already-formed context, and already-produced outcome.

It does not call a resolver.

## Query traces

`ProjectResolutionQuery` becomes a `reference`-domain trace.

The query carries no source span and no canonical AIR identity, so TAM does not
invent either. Its TAM-local identity is derived from the exact frozen query
fields:

- declaration kind;
- declaration path;
- optional module segments.

## Scope traces

`ProjectResolutionContext` becomes a `scope`-domain trace.

The trace ID incorporates:

- physical source name;
- current module segments;
- imported module segments in their frozen tuple order.

A context does not contain a canonical declaration identity or declaration
source span, so those trace fields remain absent.

TAM does not infer scope. It records the supplied context.

## Candidate traces

Each `ProjectResolutionCandidate` becomes a `reference`-domain trace.

The candidate already binds together:

- `ProjectDeclaredIdentity`;
- `ProjectDeclarationOwner`;
- `ProjectQualification`.

The frozen candidate validator guarantees those values agree. TAM does not
repeat the resolution algorithm.

The trace:

- preserves the exact identity `SourceSpan`;
- references `identity.current_air_id`;
- records the candidate's canonical index position;
- derives its TAM-local ID from the candidate's existing identity, owner,
  qualification, source, module, span, and index data;
- adds no inferred provenance or graph edges.

The canonical `ProjectResolutionCandidateIndex.candidates` order is consumed as
provided after that owner has performed its own canonical sorting.

## Resolution outcomes

P11-TAM-E observes all three canonical outcomes.

### Resolved

`ProjectResolvedBinding` becomes a `reference` trace that preserves:

- the existing query;
- the selected candidate evidence already present in the outcome;
- the candidate's exact source span;
- the candidate's existing AIR ID as `canonical_identity`.

TAM does not select the candidate. It receives an outcome in which the
resolution subsystem has already done so.

### Unresolved

`ProjectUnresolvedResolution` becomes a `reference` trace.

No declaration was resolved, so:

- `canonical_identity=None`;
- `source_span=None`.

TAM does not invent a missing target.

### Ambiguous

`ProjectAmbiguousResolution` becomes a `reference` trace whose deterministic
identity incorporates the frozen ambiguous-candidate tuple.

Because multiple candidates remain possible:

- `canonical_identity=None`;
- `source_span=None`.

TAM does not collapse ambiguity into a fabricated winner.

## Aggregate observation

`trace_map_from_resolution_observation` emits records in this stable order:

1. query;
2. context;
3. all candidates in canonical `ProjectResolutionCandidateIndex.candidates`
   order;
4. supplied resolution outcome.

The aggregate requires `outcome.query` to equal the supplied observed query.

For factual coherence only, a resolved outcome's selected candidate must
already occur in the supplied canonical candidate index, and every candidate
in an ambiguous outcome must already occur in that index. This is membership
validation over already-produced evidence, not candidate lookup, visibility
filtering, ranking, or resolution.

The aggregate does not determine which candidates are visible or which
candidate should win.

## Visibility boundary

P11-TAM-E deliberately does not consume `ProjectVisibilityEvidence` or
`ProjectVisibilityDecision`.

Visibility is already a separate semantic subsystem. It must not be relabeled
as TAM `authority` evidence.

A later TAM slice may add passive visibility traces if architecture review
shows that they are required, but that work must retain the distinction
between visibility and authority.

## Resolution boundary

`tam.production` does not call:

- `resolve_project_query`;
- `resolve_project_contextual_query`;
- `collect_project_visibility_evidence`;
- `evaluate_project_visibility`;
- `filter_project_visible_candidates`;
- candidate-index lookup methods.

Therefore:

- `RESOLUTION_EXECUTION=NONE`;
- `VISIBILITY_EVALUATION=NONE`;
- `CANDIDATE_SELECTION=NONE`;
- `SCOPE_INFERENCE=NONE`.

## Graph boundary

P11-TAM-E does not create upstream or downstream trace links.

Although the frozen resolution objects contain relationships, this slice first
freezes their direct observational projection without inventing a TAM graph.
Graph composition can be introduced only by a later slice with explicit
edge-ownership rules.

## Frozen ownership boundary

P11-TAM-E does not modify:

- `tam.model`;
- compiler/source ownership;
- declaration or identity ownership;
- project construction;
- resolution candidate construction;
- resolution contexts;
- resolution queries;
- resolution outcomes;
- visibility filtering/evaluation;
- CLI/LSP behavior;
- narrative semantics;
- semantic-decision semantics;
- semantic lattice;
- runtime behavior.

## Completion condition

P11-TAM-E is complete when:

- TAM-D freeze ancestry is proven;
- query, context, candidate, resolved, unresolved, and ambiguous evidence are
  all projected;
- candidate AIR IDs remain references only;
- exact candidate source spans are preserved;
- unresolved and ambiguous outcomes fabricate no canonical target;
- canonical candidate-index ordering is preserved;
- resolved and ambiguous outcomes are factually coherent with the supplied candidate index;
- repeated observations produce identical trace IDs and maps;
- no graph links are inferred;
- no resolution, visibility, selection, or scope computation occurs;
- frozen semantic owners remain unchanged;
- TAM-D/C/B and durable SRC regression remain green.