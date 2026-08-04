# P11.5B Minimal Narrative Semantic Model Contract

## Scope and frozen predecessor

P11.5B introduces the first passive production representation for the nine
narrative semantic areas audited by P11.5A. P11.5A remains the frozen
predecessor at commit `3349617a689eb0d9c9849dc604f749d7951d62a0`, under
annotated tag `afp-p11.5a-freeze` with tag object
`983be9ef48d9f09cecb125810ab420e7c388eada`.

P11.5B follows the architecture audit because implementation needs a minimal,
reviewable fact model before graph construction or analysis can be designed.
This stage freezes only immutable structural records. It does not determine
whether a collection of those records is narratively valid.

## Sole production module and exact public API

P11.5B has one production module:

```text
apexforge/language/narrative_model.py
```

It is not re-exported through `language.__init__`. Its exact public API is:

```python
__all__ = (
    "NarrativeIdentity",
    "NarrativeCharacter",
    "NarrativeScene",
    "NarrativeDialogue",
    "NarrativeChoicePath",
    "NarrativeChoice",
    "NarrativePerspective",
    "NarrativeTimeline",
    "NarrativeStateFact",
    "NarrativeState",
    "NarrativeContinuityConstraint",
    "NarrativeContinuity",
    "NarrativeStory",
)
```

There is no public function, builder, validator, resolver, serializer,
registry, cache, or global state.

## Passive immutable record architecture

All thirteen records are frozen dataclasses. Their equality and hashing are the
ordinary structural behavior supplied by the dataclass implementation. No
record defines custom equality, ordering, ranking, normalization, or generated
identity behavior.

Every nested record and tuple is preserved as supplied. Constructors validate
structure, but they do not sort, copy into another representation, coerce,
trim, canonicalize, deduplicate, resolve, or replace values. Canonical semantic
tuple order is caller supplied in P11.5B.

Exact-type validation is controlling:

- tuple fields require an exact tuple, not a list or tuple subclass;
- string fields require an exact string, not an integer, Boolean, object, or
  string subclass;
- record fields require the exact declared record type, not a subclass;
- malformed values raise ordinary `TypeError` or `ValueError`;
- constructors emit no ApexForge diagnostic.

## Narrative identity

`NarrativeIdentity` has exactly:

```text
kind
path
```

The supported kind vocabulary is exactly:

```text
story
character
scene
dialogue
choice
perspective
timeline
narrative_state
continuity
```

`kind` is an exact string. `path` is a nonempty exact tuple of exact, nonblank,
already-trimmed strings. Segment spelling, case, and order are preserved.
Identity is not inferred from display text, object position, state, or object
address, and no ID is generated.

## Character and scene

`NarrativeCharacter` has exactly:

```text
identity
```

Its identity must have kind `character`.

`NarrativeScene` also has exactly `identity`, whose kind must be `scene`.
These records carry semantic identity only. Character biography, personality,
knowledge analysis, scene rendering, scheduling, and execution are absent.

## Dialogue structural references

`NarrativeDialogue` has exactly:

```text
identity
scene
speaker
participants
```

The identity has kind `dialogue`; `scene` has kind `scene`; and `speaker` has
kind `character`. `participants` is a nonempty exact tuple of character
identities. Its order and duplicates are preserved.

The speaker is neither required nor forbidden in `participants`. The model
does not verify that the scene, speaker, or participants are declared in a
story. Dialogue text, audio, voice, conditions, consequences, prose generation,
and runtime delivery are not represented.

## Choice paths and choices

`NarrativeChoicePath` has exactly:

```text
label
destination
condition
consequence
```

`label` is an exact nonblank trimmed string. `destination` is an exact scene
identity. `condition` and `consequence` are each either `None` or an exact
nonblank trimmed string. These strings are passive semantic descriptions; they
are not parsed, evaluated, executed, ranked, or compared.

`NarrativeChoice` has exactly:

```text
identity
scene
paths
```

Its identity has kind `choice`, its scene is a scene identity, and `paths` is a
nonempty exact tuple of exact choice-path records. Path order and duplicates
are preserved. The model selects no path, performs no reachability analysis,
and verifies no destination.

## Perspective

`NarrativePerspective` has exactly:

```text
identity
viewpoint
```

Its identity has kind `perspective`. `viewpoint` is either `None` or an exact
character identity. `None` says only that no character viewpoint is
structurally attached; it does not mean compiler omniscience or global truth.
No knowledge filtering or perspective accessibility exists.

## Timeline

`NarrativeTimeline` has exactly:

```text
identity
scenes
```

Its identity has kind `timeline`. `scenes` is an exact tuple containing only
exact scene identities, and it may be empty. Caller order and duplicate scene
references are retained. The model does not sort scenes, infer chronology,
detect impossible timelines, or introduce clocks, calendars, durations,
timestamps, or runtime schedules.

## Narrative state

`NarrativeStateFact` has exactly:

```text
subject
name
value
```

`subject` is any exact supported narrative identity. `name` and `value` are
exact nonblank trimmed strings whose spelling and case are preserved. Values
are not interpreted or coerced into runtime values.

`NarrativeState` has exactly:

```text
identity
facts
```

Its identity has kind `narrative_state`. `facts` is an exact tuple of exact
state-fact records and may be empty. Order and duplicates are retained. Facts
are not merged, contradictory values are not resolved, and transitions are not
applied.

Narrative semantic state remains separate from ApexForge runtime execution
state. No runtime-state record or execution path consumes this model.

## Continuity

`NarrativeContinuityConstraint` has exactly:

```text
subjects
assertion
```

`subjects` is a nonempty exact tuple of exact narrative identities. Subject
order and duplicates are retained. `assertion` is an exact nonblank trimmed
string and remains passive content; it is not parsed or evaluated.

`NarrativeContinuity` has exactly:

```text
identity
constraints
```

Its identity has kind `continuity`. `constraints` is an exact tuple of exact
constraint records and may be empty. Order and duplicates are preserved. The
record performs no contradiction, reachability, knowledge, time, identity, or
continuity validation and emits no diagnostic.

## Story root

`NarrativeStory` has exactly:

```text
identity
characters
scenes
dialogues
choices
perspectives
timelines
states
continuities
```

Its identity has kind `story`. Every collection is an exact tuple whose items
must be the exact corresponding record type. Every collection may be empty.
All tuple order, duplicate records, and nested object references are preserved.

The story is a passive ownership root. It does not verify that references point
to contained records, require unique identities, reject contradictions, detect
missing dialogue participants, calculate choice reachability, validate
timelines, construct a graph, generate prose, or execute a story.

## Exact preservation semantics

The following are required structural outcomes:

```text
(character, character) remains two entries
(scene_a, scene_b) remains in that order
two equal choice paths remain two paths
two identical state facts remain two facts
two identical continuity constraints remain two constraints
```

No record converts these tuples into a set, dictionary, sorted tuple, or
canonicalized string. A later graph stage may define graph-level canonical
ordering, but it must not retroactively mutate these records.

## Structural-only validation boundary

P11.5B validates local record shape only. All of the following remain
constructible and preserved:

- dialogue referencing a scene absent from its story;
- dialogue referencing a character absent from its story;
- choice targeting an absent scene;
- timeline referencing an absent scene;
- duplicate identities and equal records;
- contradictory narrative-state facts;
- contradictory continuity assertions;
- unreachable choice destinations.

Constructibility is not semantic approval. These facts are retained for later
graph construction and analysis without claiming that they form a valid
narrative.

## No Narrative Semantic Graph

P11.5B creates no graph class, graph builder, graph node, graph edge, adjacency
map, relation enum, traversal, index, node ID, edge ID, or graph serialization.
The immutable records are inputs that a later reviewed stage may consume.

## No diagnostics, syntax, serialization, or integration

P11.5B introduces no storytelling lexer keyword, grammar production, parser
path, AST record, source span, source name, module ownership, declaration
candidate, contextual resolution hook, or source syntax.

It adds no narrative, story, or continuity diagnostic code and no narrative
exception hierarchy. It adds no serializer and changes neither AIR nor artifact
v1.

The records are not integrated into `ProjectBuild`, `ProjectBuilder`, compiler,
linker, validator, entry resolution, manifests, runtime state, runtime
execution, CLI, LSP, VS Code, Visual Studio, or the standard library.

## Ownership boundaries

P11.5A remains owned by exactly:

```text
apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py
docs/p11/P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md
```

P11.5B owns exactly:

```text
apexforge/language/narrative_model.py
apexforge/p11_5b_minimal_narrative_semantic_model_smoke_test.py
docs/p11/P11_5B_MINIMAL_NARRATIVE_SEMANTIC_MODEL_CONTRACT.md
```

The only historical alignment is the P11.5A smoke test's exact reviewed branch
set. The frozen P11.5A architecture document is byte-for-byte unchanged.

## Compatibility invariants

Project construction, contextual resolution, AIR, artifact bytes and
fingerprints, compiler behavior, linker behavior, validator behavior, entry
resolution, runtime behavior, CLI behavior, LSP, VS Code, Visual Studio, and
existing diagnostics remain unchanged. The P11.5B smoke test reuses the
accepted P11.5A and P11.4H compatibility path rather than copying its fixtures.

## Explicit non-goals

P11.5B does not provide:

- cross-record lookup or reference validation;
- identity uniqueness or collision handling;
- graph construction, ordering, traversal, or serialization;
- semantic reachability, knowledge, timeline, or continuity analysis;
- condition or consequence evaluation;
- choice selection or runtime branching;
- prose, dialogue, audio, voice, or AI generation;
- diagnostics, source mapping, or recovery;
- syntax, parser, compiler, project, AIR, artifact, runtime, CLI, or tooling
  integration.

## Acceptance evidence

The executable contract verifies the exact predecessor commit and tag object,
the exact thirteen-name API and field order, every strict constructor rule,
frozen equality and hashing, exact nested-reference preservation, caller tuple
order, duplicate retention, allowed unresolved and contradictory facts, the
one-file production boundary, unchanged P11.5A documentation, absence of graph
and diagnostic surfaces, and the accepted operational compatibility matrix.

## Proposed next stage

```text
P11.5C  Narrative Semantic Graph Construction Contract
```

P11.5C is proposed only and was not begun. P11.5B does not define its API,
files, node forms, edge forms, ordering algorithm, or implementation.
