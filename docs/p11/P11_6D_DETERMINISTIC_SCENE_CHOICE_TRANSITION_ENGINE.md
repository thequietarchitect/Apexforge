# P11.6D — Deterministic Scene/Choice Transition Engine

## Status

P11.6D creates the deterministic runtime transition layer for narrative
execution. It consumes the immutable P11.6B execution-state contracts and the
immutable P11.6C executable bindings.

The controlling predecessor is the annotated P11.6C freeze:

- tag: `afp-p11.6c-freeze`
- commit: `b7a811f7e395e2a31bf1209f358138a95e3ee7ca`

P11.6B and P11.6C production files remain unchanged.

## Narrow transition API

The production module is `runtime/narrative_transition.py` and exposes:

```python
transition_narrative_choice(
    state: NarrativeExecutionState,
    bindings: NarrativeExecutableBindingSet,
    choice: NarrativeIdentity,
    path_index: int,
) -> NarrativeExecutionState
```

The API requires an explicit choice identity and path index supplied by the
caller. No automatic choice selection is performed, and there is no
initial-scene resolver. A successful execution returns only a new immutable
`NarrativeExecutionState`.

## Deterministic resolution

The transition first requires the binding set story identity to equal the state
story identity. It then resolves the exact choice identity and path index among
the P11.6C executable paths whose source scene is the current scene.

Structural failures raise `NarrativeTransitionError` with one deterministic
`failure_kind`: `story_mismatch`, `choice_not_found`,
`choice_not_current_scene`, `path_not_found`, `ambiguous_path`, or
`condition_unsatisfied`. The exception also carries the requested choice,
path index, and current scene. No P11.6E diagnostic policy is introduced.

## Condition evaluation

An ungated path has no predicate and is satisfied. A gated path evaluates its
`NarrativeFactPredicate` against the current state's exact subject/name fact
slot:

- `equals` succeeds when the existing slot value equals the expected value;
- `not_equals` succeeds when the existing slot value differs from the expected
  value;
- Missing fact slots satisfy neither operator.

Thus a gated path fails closed when its required fact is absent or its predicate
is false. The state is not changed when a condition fails.

## Consequence and state transition

After a predicate succeeds, each bound `NarrativeFactAssignment` creates a new
immutable `NarrativeStateFact` value for its slot. Existing facts remain, and
the resulting `NarrativeExecutionState` constructor provides its deterministic
fact ordering and duplicate-slot invariant.

The new state then:

1. sets `current_scene` to the path's declared destination;
2. appends that destination to `progression`;
3. appends `NarrativeChoiceEvidence` containing the selected choice, source
   scene, path index, label, and destination to `choice_history`;
4. preserves the prior termination container without interpreting it.

`NarrativeStory`, `NarrativeChoice`, `NarrativeChoicePath`, the input execution
state, and all P11.5/P11.6 frozen objects are never mutated.

## Explicit boundaries

No AIR runtime reuse.

No runtime diagnostics.

No termination algorithm.

No ProjectBuild integration.

P11.6D has no AIR lowering and no AIR runtime reuse. It does not reuse
`AIRExpression`, `StateAssignment`, `StateSnapshot`, `StateDelta`,
`ExecutionResult`, or `RuntimeEngine`.

It produces no runtime diagnostics or trace records, defines no trace-generation
policy, and defines no termination algorithm or reason vocabulary. P11.6E owns
those semantics.

It does not integrate `ProjectBuild`, manifests, build artifacts, CLI routing,
or editor tooling. Those concerns remain outside this stage.
