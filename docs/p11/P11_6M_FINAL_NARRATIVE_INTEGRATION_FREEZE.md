# P11.6M - Final Narrative Integration and Track Freeze

## Track scope

P11.6M is the audit-only closure of the P11.6 narrative-execution track on
frozen P11.6L commit `42dd1fc421ad4fce6394548b6f892051031922c3`
and tag `afp-p11.6l-freeze`. It adds no production API or behavior.

- P11.6B owns immutable narrative execution state, result, choice evidence,
  termination, trace, and diagnostic record shapes.
- P11.6C binds exact descriptive condition and consequence identities to the
  minimal narrative predicate and fact-assignment vocabulary.
- P11.6D exclusively owns deterministic choice/path resolution, condition
  evaluation, consequence application, destination movement, progression, and
  choice history.
- P11.6E owns observable execution results, deterministic diagnostics and
  trace, the terminated-state guard, and explicit termination.
- P11.6F packages analyzed narrative semantics and executable bindings into a
  canonical build artifact without executing them.
- P11.6G exposes one explicit one-shot narrative request and delegates it to
  E/D.
- P11.6H owns immutable artifact-associated session creation, validation,
  loading, stepping, explicit termination, canonical serialization, and atomic
  persistence. It delegates transition meaning to G/E/D.
- P11.6I owns deterministic human input grammar and exact one-based menu alias
  mapping to zero-based H choice/path requests. It never chooses autonomously.
- P11.6J owns immutable structured presentation and stable LF text rendering.
- P11.6K carries optional exact authored scene title/body and dialogue text
  through source, semantic model, artifact, material, and presentation.
- P11.6L defines canonical dialogue presentation order as authored array/tuple
  order after exact current-scene filtering.
- P11.6M supplies one final cross-layer acceptance proof and this closure
  record; it owns no production code.

## Final architecture

The frozen end-to-end data and authority chain is:

```text
authored narrative source/content
  -> dedicated opt-in parse
  -> immutable canonical narrative model and passive validation
  -> exact P11.6C executable bindings
  -> canonical build artifact and fingerprint
  -> immutable artifact-associated material
  -> deterministic J/K/L presentation
  -> explicit human I selection/request
  -> H session lifecycle and persistence
  -> G request router
  -> E trace, diagnostics, and explicit termination
  -> D condition/consequence transition authority
  -> immutable new state
  -> deterministic presentation of that state
```

Authored content supplies identities, structure, prose, and order. The semantic
model preserves those values. Binding supplies only explicitly registered
condition/consequence meaning. Presentation observes canonical material and
state. Interaction maps an explicit human command. H validates association and
persists successful results. G/E/D remain the execution chain.

## Canonical schemas

### Narrative source and semantic model

The dedicated opt-in source has one `story` and immutable ordered families for
characters, scenes, dialogues, choices and paths, perspectives, timelines,
narrative states/facts, and continuity constraints. Scene `title` and `body`
and dialogue `text` are optional exact prose; `None` is canonical absence.
Choice paths retain exact label, destination, optional condition identity, and
optional consequence identity. Source strings support the already-frozen
quoted-string escapes; P11.6M adds no general scripting grammar.

Analysis is the fixed parse -> lower -> semantic-graph -> passive-validation
pipeline. `NarrativeStory` retains exact identities and declaration tuples.
P11.6C walks choice/path tuples and binds exact condition/consequence source
text; prose and dialogue position are not binding inputs.

### Narrative build artifact

The outer schema remains `apexforge.build-artifact/v1`. Opt-in narrative
material uses `apexforge.narrative-build-artifact/v2`. The narrative member
contains the source name, complete immutable story projection, and executable
binding paths. Each scene contains `identity`, `title`, and `body`; each
dialogue contains identity, scene, speaker, participants, and `text`. JSON
array position preserves authored declaration order. v2 canonical absence is
JSON `null`.

The existing canonical serializer owns sorted mapping keys, two-space JSON,
UTF-8 bytes, LF delimiters, and one final LF. The outer fingerprint is SHA-256
over the canonical payload without its fingerprint member. Prose and dialogue
array order are artifact content, so changing either changes bytes and the
fingerprint even though execution semantics remain unchanged.

### Session schema and material

`apexforge.narrative-session/v1` contains only its schema, the associated outer
artifact SHA-256, exact story identity, and complete immutable execution state.
The state contains story, current scene, canonical facts, progression, choice
history, and termination. It contains no prose, dialogue array, presentation
order, UI selection, path menu, timestamp, UUID, or source path.

`NarrativeSessionMaterial` is an in-memory immutable reconstruction from the
verified artifact. It contains the artifact fingerprint, story identity,
declared identity/scene inventories, executable bindings, scene records, and
dialogue records. Rendering and execution need not reopen narrative source.

H request/result schemas remain:

- `apexforge.narrative-session-create-request/v1`;
- `apexforge.narrative-session-step-request/v1`;
- `apexforge.narrative-session-terminate-request/v1`;
- `apexforge.narrative-session-step-result/v1`.

### Rendering and presentation

`NarrativeSessionPresentation` contains exact story and current-scene identity,
status/reason, transition count, optional current-scene title/body, current-
scene authored dialogues with text, canonical facts, and structurally available
choices. Its text order is header/state, optional title, optional body,
authored current-scene dialogue sequence, facts, then choices.

Dialogue is filtered by exact scene while preserving material tuple position.
Facts sort by subject kind/path, name, and value. Active choice paths retain the
P11.6I rule `(choice kind, choice path, path index)` and receive consecutive
one-based display numbers afterward. A menu number is only an alias for the
retained exact choice identity and zero-based path index.

## Public commands

The frozen CLI surface discovered in `tooling/cli.py` is:

```text
apexforge build [PATH] --output FILE [--entry NAME]
apexforge run [PATH] [--entry NAME] [--report]
apexforge narrative BUILD_ARTIFACT --request REQUEST_JSON
apexforge narrative-session create BUILD_ARTIFACT --request REQUEST_JSON --output SESSION
apexforge narrative-session step BUILD_ARTIFACT SESSION --request REQUEST_JSON --output SESSION
apexforge narrative-session terminate BUILD_ARTIFACT SESSION --request REQUEST_JSON --output SESSION
apexforge narrative-session interact BUILD_ARTIFACT SESSION
```

Generic `build` compiles the ordinary project and writes the existing outer
artifact; it does not infer, attach, or execute narrative content. Generic
`run` exists and executes one canonical AIR project entry directive. It is not
a narrative or narrative-session runner. One-shot narrative execution is
intentionally the separate `narrative` route. Persistent creation, step,
termination, and human interaction are intentionally under
`narrative-session`.

The P11Validation project succeeds through generic `build` and generic `run`.
The M smoke separately constructs an explicitly routed canonical narrative
artifact and exercises every narrative command above with temporary request,
artifact, and session outputs. The protected validation fixture is never
rewritten.

## Determinism guarantees

- Equivalent source, model, binding, and project input produces identical
  canonical JSON bytes and SHA-256.
- Execution accepts an exact choice identity and zero-based path index; D uses
  exact deterministic condition and consequence records.
- Success deterministically updates facts, destination, progression, and
  choice history; failure preserves state and emits fixed E diagnostics/trace.
- Exact authored prose, UTF-8 text, whitespace, and LF content survive the v2
  pipeline without interpolation or normalization.
- Authored dialogue array/tuple position survives current-scene filtering.
- Choice ordering remains independent of passive dialogue order and uses the
  frozen identity/path-index rule.
- Menu numbers are deterministic presentation aliases, never semantic IDs.
- Time, random values, filesystem enumeration, locale, environment noise,
  network services, and model providers do not participate.

## Authority boundaries

Prose is inert authored data. Text resembling `${fact}`, `if (...)`,
`invoke Main`, `terminate`, or a choice identity is rendered literally; it is
not evaluated, interpolated, compiled, or used for selection.

Rendering is presentation-only. It cannot execute, persist, terminate, select,
rank, score, or reopen source. Authored dialogue position is content order, not
priority. P11.6I consumes only explicit human input and maps a valid menu alias
to one exact H request; it never chooses a default or tries an alternative.
Quit and EOF close interaction without a step, write, termination, or hidden
outcome. H owns association/lifecycle/persistence but not transition meaning.
Transition authority remains the D/E/G chain.

## Compatibility

Historical prose-free source and material retain the exact P11.6J rendering:
no title, body, or dialogue heading is invented. Strict narrative artifact v1
loading remains accepted; omitted scene/dialogue prose becomes canonical
`None`, identities and dialogue array order remain valid, and execution stays
functional. v2 retains exact prose and authored dialogue array order.

The session schema remains v1. Sessions created before K/L do not need prose or
ordering state because associated material supplies presentation content.
P11.6H session association, state validation, canonical bytes, step results,
and explicit termination remain unchanged.

## Deferred work

P11.6 does not include general narrative scripting, loops, calls, embedded
variables, conditional prose, macros, runtime templates/interpolation, scene
scripts, timed actions, or a content-node interpreter. It also does not include
conditional dialogue beyond existing executable choice semantics, dynamic
dialogue, AI/autonomous narration, procedural content, recommendation or
semantic scoring, localization, rich content, audio/voice, character
simulation, or an editor GUI/visual narrative designer. Those concerns belong
to deliberately reviewed later roadmap work.

## Final freeze statement

P11.6 is feature-complete at M. The frozen invariant is authored narrative
source -> deterministic semantic model -> deterministic canonical artifact ->
immutable material/session -> deterministic human-facing presentation ->
explicit human selection -> deterministic lifecycle/execution -> deterministic
new state -> deterministic presentation, with no hidden semantic authority in
prose, rendering, ordering, or interaction.

Later functionality must not be backfilled into P11.6 without deliberately
reopening the track under repository-owner review.
