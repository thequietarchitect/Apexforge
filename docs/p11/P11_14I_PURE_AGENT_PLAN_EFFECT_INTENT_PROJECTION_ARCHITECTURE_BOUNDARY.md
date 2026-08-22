# P11.14I â€” Pure Agent Plan Effect-Intent Projection Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14H.

Frozen predecessor:

- P11.14H commit: `f7faccd051e0101e43cecf564aeefcc5e45ffa6d`
- annotated tag: `afp-p11-14h-freeze`

P11.14I introduces no production type or function.

## Purpose

P11.14I settles the smallest legitimate first consumer of the frozen
`agents.planning.AgentPlan`.

The read-only audit considered:

- `AgentPlanExecutionRequest`;
- `AgentPlanConsumptionRequest`;
- a pure adapter/projection;
- principal/authorization context;
- host-effect handoff;
- empty-plan behavior;
- result/receipt/trace records.

## Decision 1 â€” the first consumer is a pure projection, not an execution request

`AgentPlanExecutionRequest` is rejected for the first consumer boundary because
the name would imply execution behavior that does not exist.

`AgentPlanConsumptionRequest` is also unnecessary at this stage. A one-field
wrapper containing only an exact `AgentPlan` adds no semantic information and no
validation not already owned by `AgentPlan`.

The smallest truthful consumer is therefore a pure projection function.

Candidate production owner for P11.14J:

- `agents.plan_projection`

Candidate function:

```python
def project_agent_plan_effect_intents(
    plan: AgentPlan,
) -> Tuple[EffectIntent, ...]:
    ...
```

The function name and module owner are architecture-frozen by I for the J RED
contract.

## Decision 2 â€” exact AgentPlan is the only input

The projection accepts one exact `AgentPlan`.

It must not accept:

- `AgentDefinition`;
- `AgentIdentity`;
- an agent canonical-ID string;
- an `EffectIntent` tuple directly;
- a mapping or generic object;
- a request wrapper.

The projection must not reconstruct a plan.

## Decision 3 â€” projection returns the exact frozen effect-intent tuple

The projection output is the exact `plan.effect_intents` tuple.

The output must satisfy identity, not merely equality:

```python
projected is plan.effect_intents
```

Therefore it automatically preserves:

- authored tuple order;
- exact `EffectIntent` object identities;
- the already-frozen duplicate-ID invariant;
- the already-frozen empty-plan contract.

The projection performs no independent effect validation or deduplication.

## Decision 4 â€” empty plans project deterministically

A valid empty `AgentPlan` projects successfully to its exact empty
`effect_intents` tuple.

Empty-plan projection is a no-work handoff, not an error and not an execution
result.

## Decision 5 â€” no request, result, receipt, response, or trace record

Because the first consumer only exposes an already-frozen tuple and performs no
execution, P11.14I does not justify:

- `AgentPlanExecutionRequest`;
- `AgentPlanConsumptionRequest`;
- `AgentPlanProjection` record;
- `AgentPlanHandoff` record;
- `AgentPlanResult`;
- `AgentPlanReceipt`;
- `AgentExecutionResult`;
- `AgentExecutionReceipt`;
- projection trace/provenance records.

Those would add structure without new semantics.

## Decision 6 â€” authorization remains outside projection

Existing capability authorization requires an AIR principal together with
existing role/authority registries and program context.

`AgentDefinition` is not an AIR authority principal.

Therefore the pure plan projection accepts no:

- principal;
- capability;
- authority check;
- authority grant;
- role registry;
- authority registry;
- program;
- authorization result.

Authorization remains a downstream pre-execution concern.

## Decision 7 â€” projection does not execute host effects

`EffectIntent` remains owned by `effects.model` as a declarative host-effect
request.

The projection only returns the exact tuple already carried by the plan.

It must not:

- execute or apply an `EffectIntent`;
- enqueue an effect into runtime state;
- create a `StateDelta`;
- call `RuntimeEngine`;
- run AIR;
- invoke workflow execution;
- perform provider/tool calls;
- mutate runtime/session state.

## Decision 8 â€” runtime StateDelta remains untouched

Plan projection is not runtime execution.

P11.14I therefore does not project into, construct, or modify `StateDelta`.

Any future execution adapter that consumes projected effects remains downstream
of this pure boundary.

## Decision 9 â€” no `agents.execution` module yet

Actual execution behavior does not exist in the agent domain.

Therefore `agents.execution` remains deferred.

The first production owner is the neutral, non-operative
`agents.plan_projection`.

## Decision 10 â€” AgentAction remains deferred

No second concrete operation kind emerged in the I audit.

P11.14I does not introduce `AgentAction`, action kinds, or an action hierarchy.

## P11.14J next slice

P11.14J owns the RED/production contract for exactly:

```python
def project_agent_plan_effect_intents(
    plan: AgentPlan,
) -> Tuple[EffectIntent, ...]:
    return plan.effect_intents
```

with strict exact-type validation before returning the tuple.

P11.14J must prove:

1. exact `AgentPlan` input type;
2. output object identity with `plan.effect_intents`;
3. exact `EffectIntent` object identity preservation;
4. authored order preservation;
5. deterministic empty-plan projection;
6. no request/result/receipt/action/execution model;
7. no authorization/runtime/workflow/tool/provider behavior;
8. `agents.__init__.__all__` remains empty;
9. `agents.plan_projection.__all__` exposes only
   `project_agent_plan_effect_intents`.

## Freeze contract

P11.14I freezes these architectural facts:

1. the first `AgentPlan` consumer is a pure projection;
2. no request wrapper is introduced;
3. the projection takes exact `AgentPlan` only;
4. the projection returns exact `plan.effect_intents` by object identity;
5. empty plans project successfully;
6. no result/receipt/response/trace record is introduced;
7. authorization remains external and downstream;
8. effect execution remains outside the agents domain;
9. `StateDelta` remains untouched;
10. `agents.execution` remains deferred;
11. `AgentAction` remains deferred;
12. P11.14J owns the minimal production projection contract;
13. P11.14I changes no production files.