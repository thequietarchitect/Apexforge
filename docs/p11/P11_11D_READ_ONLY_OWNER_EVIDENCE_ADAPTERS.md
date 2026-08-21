# P11.11D â€” Read-Only Owner-Evidence Adapters

## Purpose

P11.11D adds narrow read-only adapters for already-produced evidence that does
not have to be reconstructed from TAM.

The adapters convert existing immutable owner results into
`TapCheckLedgerEntry` values.

They do not execute the owner subsystem.

## Predecessor

P11.11D begins from:

`afp-p11-11c-freeze`
â†’ `80a690c04f2fd6dcc6cd30f69373040ee8973bb2`

P11.11C's `tap_check.projection` and P11.11B's `tap_check.model` remain frozen.

C's exact public-surface assertion is a historical stage-boundary proof after
D extends the package with adapter APIs. C remains protected by freeze
ancestry and frozen hashes, while D directly reruns the durable
`audit_trace_map` behavior.

## Architecture result

The owner census found immutable already-produced evidence in several existing
subsystems:

- `runtime.engine.ExecutionResult`;
- `runtime.narrative_execution.NarrativeExecutionResult`;
- `semantic_decision.resolution.SemanticConvergenceResolution`;
- `type_system.lowering.GenericLoweringResult`;
- `workflow.directive_engine.DirectiveExecutionResult`.

These are results/evidence objects. Their producer functions and engines remain
outside TAP.

D therefore uses narrow type-specific adapters rather than a generic object
dispatcher.

## Public adapters

D adds:

`adapt_runtime_result(result: ExecutionResult) -> TapCheckLedgerEntry`

`adapt_convergence_ruling(resolution: SemanticConvergenceResolution) -> TapCheckLedgerEntry`

`adapt_narrative_state_change(result: NarrativeExecutionResult) -> TapCheckLedgerEntry`

`adapt_air_lowering(result: GenericLoweringResult) -> TapCheckLedgerEntry`

`adapt_active_directive(result: DirectiveExecutionResult) -> TapCheckLedgerEntry`

Each adapter requires the exact owner type.

## Runtime result

`ExecutionResult` is an immutable runtime result carrying:

- a `StateDelta`;
- a runtime trace;
- diagnostics;
- final state.

The adapter reports `runtime-results`.

It copies only passive stable counts available from the result:

- assignment count;
- event count;
- effect count;
- diagnostic count;
- final-state cell count.

It does not invoke `RuntimeEngine`.

## Convergence ruling

`SemanticConvergenceResolution` is the already-produced convergence result.

The adapter reports `convergence-rulings`.

The subject is the existing convergence policy identity.

Evidence contains only:

- outcome kind id;
- ranking count;
- candidate count;
- member count;
- provenance count.

The adapter does not call `apply_semantic_convergence_policy`, validation,
Paradox Elevation, or any other semantic-decision operation.

## Narrative state change observation

`NarrativeExecutionResult` contains both initial and final immutable narrative
execution states.

The adapter reports `narrative-state-changes`.

The subject is the final state's existing story identity rendered from its
canonical narrative `kind` and ordered `path`.

Evidence records:

- initial scene;
- final scene;
- structural `state_changed` equality result;
- initial/final fact counts;
- final progression count;
- final choice-history count;
- trace count;
- diagnostic count;
- choice-evidence count.

An execution result whose initial and final states are equal is still explicit
evidence. In that case the adapter records `state_changed=false`.

That is an explicit negative observation from supplied owner evidence, not an
inference from missing evidence.

The adapter does not execute a narrative step or mutate a session.

## AIR lowering evidence

`GenericLoweringResult` is already-produced type-system lowering evidence over
the executable AIR program.

The adapter reports `air-lowering`.

Evidence records only:

- binding count;
- rewritten-function count;
- specialized-function count;
- function count.

It does not invoke `lower_linked_generics` or any lowerer.

This mapping is deliberately scoped to the existing generic lowering result.
It does not claim that every AIR-lowering path is represented by this one
object.

## Active directive evidence

`DirectiveExecutionResult` is explicit existing execution evidence containing
the root directive and ordered results.

The adapter reports `active-directives`.

This satisfies the P11.11A rule that TAP must not infer activation from a
declaration alone: D consumes an already-produced directive execution result.

The subject is the existing `root` value.

Evidence records the owner and the result count.

The adapter does not invoke `DirectiveExecutionEngine`, activate a directive,
or perform authority checks.

## TAM trace linkage

None of these five owner result objects was shown by the architecture audit to
carry an exact canonical TAM `TraceIdentity`.

Their D entries therefore use:

`trace_ids=()`

This is intentional.

D does not fabricate a trace identity merely to connect external evidence to
TAM.

A later aggregator may preserve a supplied exact link if a future owner
contract exposes one, but missing linkage is not reconstructed.

## Deferred categories

Three roadmap categories still lack an unambiguous canonical owner event in
the D audit:

- `semantic-changes`;
- `optimization-decisions`;
- `continuity-effects`.

D does not force an existing object into these categories.

In particular:

- a convergence resolution is reported specifically as a convergence ruling,
  not duplicated as a generic semantic change;
- an AETHER-AIR transformation is not automatically called a semantic change;
- a narrative continuity declaration is not itself a continuity effect;
- no generic performance or optimization artifact is treated as an
  optimization decision.

These categories remain available in `TAP_CHECK_CATEGORY_IDS` and may be
populated when explicit evidence exists.

## Non-execution boundary

The adapter module may import owner result classes for exact type checks.

It must not call:

- runtime engines;
- directive execution engines;
- semantic convergence evaluation;
- semantic-decision validation;
- Paradox Elevation;
- generic lowering;
- AETHER-AIR transformation;
- narrative lowering;
- parsers;
- compilers.

The adapter module also must not create `TraceIdentity` values.

## Ordering and aggregation

Each D adapter returns exactly one `TapCheckLedgerEntry`.

D does not aggregate multiple evidence sources into a project ledger.

P11.11E owns deterministic project audit-ledger aggregation and coverage.

## Completion condition

P11.11D is complete when:

- P11.11C freeze ancestry is exact;
- B model and C projection files remain frozen;
- all five adapters accept only their exact owner result type;
- each adapter returns one immutable ledger entry;
- owner fields are copied only as passive deterministic text/count evidence;
- no missing TAM link is fabricated;
- runtime, directive, lowering, narrative, or semantic-decision behavior is not
  invoked;
- C's durable `audit_trace_map` capability still works;
- existing owner packages are not modified;
- the three ambiguous categories remain explicitly deferred.