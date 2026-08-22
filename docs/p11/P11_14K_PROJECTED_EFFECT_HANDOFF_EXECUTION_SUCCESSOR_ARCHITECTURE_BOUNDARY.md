# P11.14K â€” Projected Effect Handoff / Execution Successor Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14J.

Frozen predecessor:

- P11.14J commit: `2865a29835da0cc19e0524c866172eef991ed6d5`
- annotated tag: `afp-p11-14j-freeze`

P11.14K introduces no production type, function, module, executor, or bridge.

## Purpose

P11.14K determines whether the first frozen agent-side plan projection creates
enough concrete downstream pressure to justify:

- an effect-handoff record;
- an agent execution adapter;
- an agent executor/runtime/session;
- an agent authorization request;
- an AgentIdentity-to-principal bridge;
- an execution result/receipt;
- `AgentAction`.

The audit found that it does not.

## Decision 1 â€” the J projection remains terminal and unconsumed

Repository references to `project_agent_plan_effect_intents` are confined to:

- `agents.plan_projection`;
- its architecture/contract documentation;
- its regression contract.

No production consumer accepts or calls the projection.

Therefore P11.14K does not invent a consumer merely to extend the chain.

## Decision 2 â€” no canonical host-effect executor or dispatcher exists

The repository contains no canonical:

- `execute_effect`;
- `execute_effects`;
- `apply_effect`;
- `apply_effects`;
- `dispatch_effect`;
- `dispatch_effects`;
- `handle_effect`;
- `handle_effects`;
- effect executor;
- effect dispatcher.

`effects.model.EffectIntent` remains a declarative host-effect request.

The AIR runtime may collect and return effect intents, but it explicitly must not
execute host effects.

The runtime also records that host effect intents are queued without executing
them.

Therefore there is no legitimate downstream execution target for an
agent execution adapter.

## Decision 3 â€” no redundant handoff record

The frozen J function already returns the exact `plan.effect_intents` tuple by
object identity.

A new `AgentEffectHandoff`, `AgentPlanHandoff`, or similar record would add no
concrete semantic field currently required by a downstream consumer.

P11.14K therefore does not wrap:

- the exact AgentPlan;
- the exact effect-intent tuple;
- the AgentDefinition;
- effect identities;

inside a second passive envelope.

If a future downstream consumer requires provenance beyond the effect tuple, a
new record may be justified then. Such a record should reference the exact
`AgentPlan` rather than reconstruct it.

## Decision 4 â€” AgentExecutionAdapter remains deferred

An execution adapter requires a real execution target.

Because no host-effect executor/dispatcher currently exists, an
`AgentExecutionAdapter` would either:

1. execute effects itself, violating the agents/effects ownership boundary; or
2. return the same tuple already returned by J, duplicating the projection.

Both are rejected.

## Decision 5 â€” AgentIdentity is not an AIRPrincipal

The audit found no existing relationship that maps:

- `AgentIdentity`;
- `AgentDefinition`;
- an agent canonical ID;

to an `AIRPrincipal`.

There is no agent `principal_id`, `principal_name`, or `agent_id` association.

Existing capability authorization is owned by authority/authorization layers and
accepts AIR principals plus existing registry/program context.

P11.14K therefore does not infer identity equivalence from equal text IDs.

## Decision 6 â€” no AgentAuthorizationRequest or authority bridge

An `AgentAuthorizationRequest` would duplicate existing authority/authorization
owners without a canonical agent-to-principal association.

P11.14K introduces no:

- principal field on AgentDefinition or AgentPlan;
- authority/capability field on AgentPlan;
- agent authorization request;
- authorized-agent-plan record;
- authorized-effect record;
- implicit AIRPrincipal creation.

If an agent-to-principal association becomes necessary, it must be designed as
an explicit future bridge with its own architecture audit.

## Decision 7 â€” StateDelta remains runtime-owned

`runtime.state.StateDelta` is an output/state-transition representation owned by
the runtime.

It may contain `EffectIntent` values produced while verified AIR is evaluated,
but it is not a generic agent effect-dispatch envelope.

P11.14K therefore does not:

- construct StateDelta from an AgentPlan;
- inject projected effects into StateDelta;
- use StateDelta as an agent handoff;
- mutate runtime state.

## Decision 8 â€” empty projected effects remain a no-work boundary

The runtime already uses empty effect tuples as a valid representation.

A valid empty AgentPlan therefore continues to project to its exact empty tuple.

P11.14K does not manufacture an execution result, receipt, trace, or no-op
execution record for an empty projection.

## Decision 9 â€” AgentAction remains deferred

No second concrete agent operation kind emerged.

`EffectIntent` remains the only concrete passive operation description in the
frozen AgentPlan.

P11.14K therefore does not introduce:

- `AgentAction`;
- action kinds;
- action union/protocol/base class;
- action resolver/catalog.

## Decision 10 â€” execution/runtime/session/tool surfaces remain deferred

P11.14K does not introduce:

- `AgentExecutor`;
- `AgentRuntime`;
- `AgentSession`;
- `AgentExecutionRequest`;
- `AgentExecutionResult`;
- `AgentPlanExecutionRequest`;
- `AgentPlanExecutionResult`;
- tool/provider requests or invocations;
- runtime/workflow integration.

These require a concrete downstream execution owner first.

## Missing prerequisite

The next prerequisite is not another agent wrapper.

The missing architectural seam is a canonical host-effect execution boundary
outside the agents domain: an owner and contract that can consume validated
`EffectIntent` values without violating the rule that the AIR runtime itself
does not execute host effects.

P11.14K does not choose that owner.

## P11.14L next slice

P11.14L begins with a read-only architecture audit for:

**host-effect execution seam ownership and contract**

The L audit must determine:

1. which domain should own optional host-effect execution;
2. whether that owner belongs in `effects`, a host/integration layer, or another
   existing subsystem;
3. whether the seam consumes one exact `EffectIntent` or an exact ordered tuple;
4. what authorization context, if any, is required before host execution;
5. whether execution results/receipts are required;
6. how failures are represented;
7. how dry-run/non-executing behavior is separated from real host execution;
8. how the seam preserves `EffectIntent` identity/provenance;
9. whether the seam is reusable by non-agent callers;
10. how the AIR-runtime non-execution invariant remains frozen.

P11.14L must begin read-only and must not create an agent executor.

## Freeze contract

P11.14K freezes these architectural facts:

1. J projection remains terminal/unconsumed by production;
2. no canonical host-effect executor/dispatcher currently exists;
3. no redundant effect-handoff record is introduced;
4. AgentExecutionAdapter remains deferred;
5. AgentIdentity is not implicitly AIRPrincipal;
6. agent-to-principal association remains deferred;
7. AgentAuthorizationRequest remains deferred;
8. StateDelta remains runtime-owned and is not an agent dispatch envelope;
9. empty projected effects remain a deterministic no-work boundary;
10. AgentAction remains deferred;
11. AgentExecutor/AgentRuntime/AgentSession remain deferred;
12. tool/provider integration remains deferred;
13. the missing prerequisite is an external host-effect execution seam;
14. P11.14L audits ownership/contract for that seam;
15. P11.14K changes no production files.