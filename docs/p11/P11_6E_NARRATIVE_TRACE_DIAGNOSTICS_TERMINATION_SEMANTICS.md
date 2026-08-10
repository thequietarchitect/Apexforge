# P11.6E — Narrative Trace, Diagnostics, and Termination Semantics

## Status

P11.6E adds the narrow narrative execution boundary that makes the immutable
P11.6D state movement observable and explicitly terminal. It does not change
the P11.6B, P11.6C, or P11.6D production contracts.

The controlling predecessor is the frozen P11.6D checkpoint:

- tag: `afp-p11.6d-freeze`
- commit: `f32e296da893a1be5aa2cfb0f107c3e067b0bd64`

## Execution API

The P11.6E production module is
`runtime/narrative_observability.py` and exposes:

```python
execute_narrative_choice(
    state: NarrativeExecutionState,
    bindings: NarrativeExecutableBindingSet,
    choice: NarrativeIdentity,
    path_index: int,
) -> NarrativeExecutionResult
```

The caller supplies the exact choice identity and path index. The function
delegates the attempted transition to `transition_narrative_choice` from
P11.6D and packages its immutable next state, trace, diagnostics, and choice
evidence in the P11.6B `NarrativeExecutionResult` contract.

P11.6E does not select a choice, resolve an initial scene, evaluate a
predicate, apply a consequence, or construct a replacement transition
engine. The P11.6D engine remains the authority for all successful and failed
choice-path transition semantics.

## Trace semantics

Each attempted explicit choice produces one immutable, ordered
`NarrativeExecutionTraceEvent` with kind `narrative_transition`. The facts
are emitted in this fixed order:

1. `source_scene`;
2. `selected_choice`;
3. `selected_path_index`;
4. `destination_scene` on success, or `failure_kind` on failure;
5. `outcome`.

Identity values are rendered as their narrative kind followed by their
slash-separated identity path. A successful event therefore records the
source scene, selected choice, selected path index, destination scene, and
`success` outcome. A rejected attempt records the requested source/selection,
the deterministic failure kind, and `failure` outcome. Trace is evidence of
what the boundary attempted and observed; it never chooses behavior.

No timestamps, wall-clock values, random identifiers, UUIDs, global tracing
policy, or other nondeterministic metadata are emitted.

## Diagnostic semantics

P11.6D's six `NarrativeTransitionError.failure_kind` values are all mapped to
one deterministic error diagnostic. No failure kind is swallowed:

| P11.6D failure kind | P11.6E diagnostic code |
| --- | --- |
| `story_mismatch` | `NARRATIVE_TRANSITION_STORY_MISMATCH` |
| `choice_not_found` | `NARRATIVE_TRANSITION_CHOICE_NOT_FOUND` |
| `choice_not_current_scene` | `NARRATIVE_TRANSITION_CHOICE_NOT_CURRENT_SCENE` |
| `path_not_found` | `NARRATIVE_TRANSITION_PATH_NOT_FOUND` |
| `ambiguous_path` | `NARRATIVE_TRANSITION_AMBIGUOUS_PATH` |
| `condition_unsatisfied` | `NARRATIVE_TRANSITION_CONDITION_UNSATISFIED` |

Messages have the deterministic form
`narrative transition failed: <failure_kind>`. The diagnostic subject is the
explicitly requested narrative choice. Failure results retain the original
state as `final_state`, contain no choice evidence, and never mutate the
input state. A missing or unsatisfied bound fact therefore remains fail-closed
through P11.6D.

An attempted transition from an explicitly terminated state is rejected at
this execution boundary with `NARRATIVE_EXECUTION_TERMINATED`; it does not
re-enter the P11.6D engine. This is a terminal-state guard, not graph
analysis or recovery policy.

Diagnostics are narrative-specific. No AIR runtime reuse is permitted. This
module does not reuse AIR expression, AIR state, AIR execution-result, or AIR
tracing/diagnostic structures.

## Termination semantics

The existing immutable `NarrativeTermination` status vocabulary remains
`active` or `terminated`. P11.6E adds one explicit reason value:
`explicit_outcome`. The API is:

```python
terminate_narrative(
    state: NarrativeExecutionState,
    reason: Literal["explicit_outcome"] = "explicit_outcome",
) -> NarrativeExecutionState
```

The caller must invoke this operation; P11.6E never infers completion from a
scene's outgoing choices, graph shape, or current location. The operation
returns a new immutable execution state with the prior story, scene, facts,
progression, and choice history preserved, plus
`NarrativeTermination(status="terminated", reason="explicit_outcome")`.
The prior active state is unchanged. Re-terminating a terminal state is a
deterministic error.

No broader lifecycle, orchestration, completion heuristic, or automatic
termination policy is introduced.

## Compatibility boundaries

- P11.6B immutable state/result/trace/diagnostic/termination record shapes
  remain unchanged.
- P11.6C binding remains descriptive-to-executable binding only.
- P11.6D remains the canonical transition engine, including fail-closed
  condition evaluation and immutable consequence application.
- No AIR lowering or AIR runtime reuse.
- No ProjectBuild integration, manifest or artifact change, CLI routing, or
  editor integration.
- No automatic choice selection and no initial-scene resolver.
- No initial-scene resolver.
- No graph-shape termination.

P11.6F and later stages own broader artifact, routing, and integration work.
