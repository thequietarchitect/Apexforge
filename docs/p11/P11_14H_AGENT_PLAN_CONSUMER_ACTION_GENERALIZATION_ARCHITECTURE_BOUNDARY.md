# P11.14H â€” Agent Plan Consumer / Action Generalization Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14G.

Frozen predecessor:

- P11.14G commit: `5bb5dad8886c0896a06332d2055f2bb58309e31d`
- annotated tag: `afp-p11-14g-freeze`

P11.14H introduces no production agent type or function.

## Purpose

P11.14H determines whether the first frozen `AgentPlan` creates enough concrete
consumer pressure to justify:

- a common `AgentAction` abstraction;
- a tool-request abstraction;
- a plan-consumption request;
- an execution adapter;
- execution results/receipts/traces.

The audit found that it does not yet justify any production addition.

## Decision 1 â€” no current production AgentPlan consumer

Repository references to `AgentPlan`, `agents.planning`, and `effect_intents` are
confined to the frozen P11.14G production model, its regression contract, and
architecture documentation.

There is no current production consumer that:

- accepts an `AgentPlan`;
- executes an `AgentPlan`;
- authorizes an `AgentPlan`;
- adapts an `AgentPlan` into runtime input;
- emits a plan result/receipt/trace;
- transforms a plan into AIR.

Therefore P11.14H does not invent a consumer implementation.

## Decision 2 â€” `AgentAction` remains deferred

The audit found no second concrete agent operation kind.

No production surface currently defines:

- `AgentAction`;
- `AgentToolRequest`;
- `AgentToolCall`;
- `AgentToolInvocation`;
- `AgentDirectiveRequest`;
- `AgentMessage`;
- `AgentObservation`;
- `AgentDecision`;
- `AgentStateChange`;
- `AgentEvent`;
- `AgentInvocation`;
- `AgentOperation`;
- `AgentWorkItem`.

`EffectIntent` remains the only concrete passive operation-description contract
needed by the frozen agent plan.

A common `AgentAction` abstraction is therefore still unjustified.

P11.14H must not wrap `EffectIntent` merely to create an action hierarchy.

## Decision 3 â€” frozen AgentPlan is not generalized or mutated

`agents.planning.AgentPlan` remains exactly:

```python
@dataclass(frozen=True)
class AgentPlan:
    definition: AgentDefinition
    effect_intents: Tuple[EffectIntent, ...] = ()
```

P11.14H adds no fields, variants, methods, helpers, base classes, protocols, or
execution semantics to that model.

A future consumer must accept the exact frozen `AgentPlan` object rather than
copying its `definition` and `effect_intents` into a replacement planning model.

## Decision 4 â€” exact AgentPlan identity is the preferred handoff boundary

If a later plan-consumption request or adapter is introduced, it should preserve
the exact `AgentPlan` object identity.

This keeps:

- `AgentDefinition` identity;
- `EffectIntent` identities;
- authored effect ordering;
- duplicate-effect-ID invariants;

owned by the already-frozen plan instead of revalidating or reconstructing those
fields downstream.

P11.14H does not yet freeze the shape or name of such a request.

## Decision 5 â€” authorization remains a downstream pre-execution gate

Existing authority owners already define:

- principals;
- `AuthorityCheck`;
- `AuthorityGrant`;
- capability resolution;
- capability authorization.

An `AgentPlan` is not authority.

P11.14H adds no:

- principal field to `AgentPlan`;
- capability field to `AgentPlan`;
- authority grant/check field to `AgentPlan`;
- authorization result to `AgentPlan`.

Any future execution path must use existing authority/authorization owners before
performing protected work.

## Decision 6 â€” effect execution remains outside agents

`effects.model.EffectIntent` remains a declarative host-effect request.

Existing runtime state can carry effect intents, while runtime execution remains
owned by runtime/workflow machinery.

The agents domain therefore does not become the owner of host-effect execution.

A future agent execution adapter may hand the plan's exact effect intents toward
existing effect/runtime mechanisms, but constructing or consuming a plan must not
itself execute host effects.

## Decision 7 â€” tool requests remain deferred

The audit found no canonical `ToolRequest`, `ToolCall`, or `ToolInvocation`
contract.

Provider vocabulary exists in unrelated subsystems, but there is no
provider-independent passive agent tool request that P11.14H can safely reuse.

Therefore H does not introduce a tool-request model.

A future tool request should be introduced only when there is a concrete
provider-independent contract. It should remain a sibling specialized operation
unless its semantics are genuinely those of a host-side `EffectIntent`.

## Decision 8 â€” result / receipt / trace semantics remain deferred

No production plan consumer exists yet.

Therefore P11.14H does not introduce:

- `AgentPlanResult`;
- `AgentPlanReceipt`;
- `AgentExecutionResult`;
- `AgentExecutionReceipt`;
- plan execution records;
- plan execution traces.

Those concepts require a concrete consumer/execution boundary first.

## Decision 9 â€” package and dependency boundaries stay frozen

`agents.__init__.__all__` remains empty.

`agents.planning.__all__` remains exactly `("AgentPlan",)`.

P11.14H changes no production agent module.

## P11.14I next slice

P11.14I begins with a read-only architecture audit for the first
plan-consumption / execution-adapter contract.

That audit must decide:

1. whether the first consumer is a passive request wrapper, a pure adapter, or
   another explicitly named boundary;
2. whether it should reference exact `AgentPlan` only or also require an external
   principal/authority context;
3. where authorization is checked relative to plan consumption;
4. whether plan effects are merely projected/handed off or actually executed;
5. whether an empty plan is consumable;
6. what result is possible without inventing runtime/session ownership;
7. whether the first consumer remains pure/non-executing;
8. whether execution should be deferred to a later slice.

P11.14I must not begin with `AgentAction`.

## Freeze contract

P11.14H freezes these architectural facts:

1. no production `AgentPlan` consumer currently exists;
2. no second concrete agent operation kind currently exists;
3. `AgentAction` remains deferred;
4. frozen `AgentPlan` is not generalized or mutated;
5. a future consumer should preserve exact `AgentPlan` identity;
6. authorization remains external and pre-execution;
7. effect execution remains outside the agents domain;
8. tool requests remain deferred;
9. result/receipt/trace semantics remain deferred;
10. P11.14I audits the first plan-consumption/execution-adapter contract;
11. P11.14H changes no production files.