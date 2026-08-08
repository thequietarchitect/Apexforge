# P11.6A — Narrative Execution Architecture Audit

Status: **candidate / audit-only**

Predecessor: `afp-p11.5-freeze`  
Predecessor commit: `42538fc2afe8dc2fca824249edf7b797740c11e7`  
Branch: `p11.6a-narrative-execution-architecture-audit`

## Purpose

P11.6 begins the transition from narrative understanding to narrative execution.

P11.5 remains observational. It can parse narrative source, lower that source into
immutable semantic records, build a semantic graph, perform passive validation,
compose an analysis result, and render a deterministic report. It does not choose
paths, mutate narrative state, advance scenes, execute dialogue, or enforce
continuity assertions.

P11.6A is Audit-only. It makes no production change. Its purpose is to define the
execution boundary before implementation begins.

## Frozen boundaries found by the audit

### P11.5 narrative semantics

The P11.5 semantic model already supplies the information an execution layer will consume:
scenes, structural dialogue, choices, path destinations, optional conditions and
consequences, timelines, narrative-state facts, perspectives, and continuity assertions.

These records are immutable semantic evidence.

The current condition and consequence values are optional strings. Narrative-state
fact values are strings. Continuity assertions are strings. Do not reinterpret P11.5 strings as executable code. A later executable binding layer must translate
or bind explicitly supported narrative expressions into executable forms while
preserving the original P11.5 semantic records.

### Existing AIR project/runtime

The existing `ProjectBuild` owns an `AIRProgram` and `VerifiedAIRProgram`.
`ProjectBuild.execute()` resolves a directive entry and invokes `RuntimeEngine`
with that verified AIR program.

The existing `RuntimeEngine` is explicitly the AIR runtime execution engine.
Its result contains an AIR `StateDelta`, trace, diagnostics, and final `StateSnapshot`.

**AIR runtime remains unchanged** during P11.6A.

Narrative execution must not be forced into `ProjectBuild`, `VerifiedAIRProgram`,
`RuntimeEngine`, `StateSnapshot`, or `StateDelta` merely to reuse an existing
public command.

### Existing project manifest

Manifest schema 1 accepts only `schema`, `name`, `sources`, and `entry`. Unknown
fields are rejected. `entry` currently belongs to the ordinary directive-entry
contract, and the default scaffold creates `directive Main`.

**Manifest schema 1 remains unchanged** in P11.6A.

Future narrative project recognition therefore requires an explicit compatibility
decision: a versioned manifest schema, a separate narrative project descriptor,
or a routing layer that identifies narrative input without changing schema 1.

### Existing build artifact

`apexforge.build-artifact/v1` serializes canonical AIR plus project metadata and a
SHA-256 fingerprint.

**Build artifact v1 remains unchanged**.

Narrative build output must use a distinct, versioned artifact contract rather
than placing narrative data into the existing `air` field or silently changing
the meaning of build-artifact v1.

## Required P11.6 execution architecture

### 1. Separate narrative execution state

P11.6 requires **Separate narrative execution state**.

The future state should represent at least the story identity, current scene,
current narrative facts, deterministic progression history, selected-choice
history, and termination status. API boundaries should remain immutable, with
transitions yielding a new snapshot or explicit delta.

### 2. Initial scene resolution

P11.5 does not define an executable entry scene. A future resolver must select one
through an explicit execution contract; it must not guess from declaration order
when multiple reasonable candidates exist.

### 3. Executable condition binding

`NarrativeChoicePath.condition` is descriptive text. P11.6 should introduce an
executable condition representation and deterministic binding/evaluation boundary.
A missing condition means no condition gate. Unknown or unbound text must not
silently evaluate truthy.

### 4. Executable consequence binding

`NarrativeChoicePath.consequence` is descriptive text. P11.6 should introduce an
explicit consequence representation that yields a deterministic narrative-state
transition without mutating the frozen semantic story.

### 5. Choice and scene transition semantics

Selecting a path should perform an ordered transition:

1. validate current-scene ownership;
2. validate path availability;
3. apply the bound consequence;
4. transition to the declared destination;
5. append deterministic trace evidence.

Unresolved destinations must fail with an execution diagnostic rather than create
undeclared runtime state.

### 6. Dialogue events

P11.5 dialogue records identify scene, speaker, and participants but do not contain
a dialogue body. Early narrative execution may therefore emit structural dialogue
events only; text-bearing dialogue syntax requires its own later language contract.

### 7. Continuity

P11.5 continuity assertions remain passive textual evidence. Future enforcement
requires an explicit predicate/binding model. Until then, continuity clusters must
not silently terminate execution.

### 8. Separate result and trace

P11.6 requires **Separate narrative execution result and trace**.

A future result should contain initial state, final state, ordered narrative trace,
diagnostics, termination reason, and choice evidence as applicable. It should not
reuse `runtime.engine.ExecutionResult` unless a later generalized abstraction is
deliberately introduced and proven compatible.

## Public command integration

The target user experience remains:

```text
apexforge build <narrative-project>
apexforge run <narrative-project>
```

Narrative `apexforge build` requires project recognition, the P11.5 analysis
pipeline, executable binding where promised, deterministic narrative artifact
serialization, a narrative-specific schema/fingerprint, and CLI routing that
leaves ordinary AIR builds unchanged.

Narrative `apexforge run` additionally requires initial-scene resolution,
execution-state construction, condition evaluation, choice selection, consequence
application, scene transition, event emission, deterministic trace, termination,
and routing that leaves ordinary AIR runs unchanged.

## Recommended P11.6 sequence

- **P11.6A** — narrative execution architecture audit.
- **P11.6B** — immutable narrative execution state and result contracts.
- **P11.6C** — executable condition/consequence binding model.
- **P11.6D** — deterministic scene/choice transition engine.
- **P11.6E** — execution trace, diagnostics, and termination.
- **P11.6F** — deterministic narrative build artifact.
- **P11.6G** — project recognition and `apexforge build` routing.
- **P11.6H** — `apexforge run` routing and user-facing execution.
- **P11.6I** — integration and freeze gate.

The dependency order is normative: state before mutation, binding before
evaluation, engine before CLI routing, and compatibility before publication.

## Non-goals for P11.6A

P11.6A adds no narrative runtime engine, mutable execution, choice selection,
scene advancement, condition evaluation, consequence application, executable
continuity, narrative artifact schema, manifest schema change, CLI narrative
routing, editor integration, or AIR lowering of narrative semantics.

## Acceptance rule

P11.6A passes only when it begins from the exact annotated P11.5 track freeze,
every audited production surface remains byte-identical to that freeze, existing
AIR runtime/manifest/scaffold/CLI/build-artifact contracts remain intact, P11.5
descriptive strings remain descriptive, no narrative execution implementation is
added, this document records the future seams, and the smoke test causes no
repository mutation.
