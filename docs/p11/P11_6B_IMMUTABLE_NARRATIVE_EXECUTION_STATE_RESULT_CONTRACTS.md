# P11.6B — Immutable Narrative Execution State and Result Contracts

## Status

P11.6B defines immutable containers and invariants only.

It is the first production stage of P11.6, following the frozen P11.6A
narrative execution architecture audit. It does not make narrative source
executable by itself.

## Baseline

The controlling predecessor is the annotated P11.6A freeze:

- tag: `afp-p11.6a-freeze`
- commit: `7438aec1f105e749287998aff6cc35d01d174425`

The P11.5 semantic model remains frozen. In particular,
`NarrativeChoicePath.condition`, `NarrativeChoicePath.consequence`,
`NarrativeStateFact.value`, and continuity assertion strings remain descriptive
semantic text. P11.6B does not reinterpret them as executable code.

## Architectural boundary

AIR runtime remains unchanged.

P11.6B does not modify or reuse the AIR-specific execution containers in
`runtime.state` or `runtime.engine`. Narrative execution receives a separate
contract module:

`runtime/narrative_execution.py`

P11.6E owns trace, diagnostic, and termination execution semantics. P11.6B only
defines the immutable record shapes that later stages may populate.

## Public contracts

### NarrativeChoiceEvidence

Records structural choice-path evidence only:

- `choice`
- `source_scene`
- `path_index`
- `path_label`
- `destination`

### NarrativeTermination

Carries immutable termination state:

- `status`: `active` or `terminated`
- optional `reason`

P11.6B defines no stopping algorithm or reason-code vocabulary.

### NarrativeExecutionTraceFact

Immutable string key/value trace evidence.

### NarrativeExecutionTraceEvent

Carries:

- `kind`
- `message`
- ordered trace facts

P11.6B emits no events.

### NarrativeExecutionDiagnostic

Carries:

- severity
- code
- message
- optional narrative identity subject

P11.6B defines no diagnostic code catalog and generates no diagnostics.

### NarrativeExecutionState

Carries one immutable narrative execution snapshot:

- story identity
- current scene
- current narrative facts
- progression history
- choice history
- termination status

Facts are normalized deterministically and duplicate current fact slots are
rejected. An omitted progression canonicalizes to the current scene. A supplied
progression must end at the current scene.

### NarrativeExecutionResult

Carries:

- initial state
- final state
- ordered narrative trace
- narrative diagnostics
- choice evidence

It projects termination from the final state and reports `ok` when no contained
narrative diagnostic is an error.

It does not reuse `runtime.engine.ExecutionResult`.

## P11.6B non-goals

No scene selection.

No condition evaluation.

No consequence application.

No scene transition.

No choice-selection algorithm.

No runtime event emission.

No trace-event production policy.

No diagnostic production.

No termination algorithm.

No executable continuity.

No AIR lowering.

No `ProjectBuild` integration.

No manifest schema change.

No build-artifact schema change.

No CLI routing.

No editor integration.

## Successor boundary

The normative sequence remains:

- P11.6B — immutable state/result contracts;
- P11.6C — executable condition/consequence binding model;
- P11.6D — deterministic scene/choice transition engine;
- P11.6E — trace, diagnostics, and termination execution semantics;
- P11.6F — deterministic narrative build artifact;
- P11.6G — project recognition and build routing;
- P11.6H — run routing and user-facing execution;
- P11.6I — integration and freeze gate.

State remains before mutation. Binding remains before evaluation. Engine remains
before CLI routing.
