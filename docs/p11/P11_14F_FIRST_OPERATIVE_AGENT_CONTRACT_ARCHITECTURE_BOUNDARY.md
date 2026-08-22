# P11.14F â€” First Operative Agent Contract Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14E.

Frozen predecessor:

- P11.14E commit: `6b13a8cf34d8b6e88fb6e1d3aa77d911db5c9ad1`
- annotated tag: `afp-p11-14e-freeze`

P11.14F introduces no production agent type.

## Purpose

P11.14F establishes the ownership and dependency direction for the first
operative agent-domain contract without prematurely choosing a field shape.

The architecture audit considered:

- agent goal / objective;
- intent;
- plan;
- action;
- host-effect request;
- tool request;
- authorization;
- execution;
- runtime / session state.

## Decision 1 â€” goal and objective remain declarative

`AgentGoal` and `AgentObjective` namespaces are currently unused.

However, a desired state or objective is still declarative metadata. Merely
declaring a goal does not order work, request an effect, invoke a tool, mutate
runtime state, or execute anything.

P11.14F therefore does not treat goal/objective declaration as the first
operative agent contract.

A future goal model may be introduced when planning has a concrete need to
reference one.

## Decision 2 â€” do not claim generic `intent`

ApexForge already has substantial `intent` vocabulary, including:

- AETHER behavior intents;
- AETHER intent traces;
- `effects.model.EffectIntent`.

P11.14 must not introduce a generic `AgentIntent` merely because the namespace is
available. The word is already semantically loaded and would obscure the
distinction between an agent's desired work and an actual host-effect request.

## Decision 3 â€” planning is the first agent-owned operative boundary

The first genuinely operative agent-domain layer is planning: an ordered,
non-executing representation of intended work owned by an `AgentDefinition`.

This does not mean a production `AgentPlan` field shape is frozen in F.

A plan cannot be frozen safely until the relationship between plan entries and
passive action descriptions is explicit.

P11.14G therefore owns the field-shape audit for the smallest immutable
plan/action representation.

Candidate owner:

- `agents.planning`

The owner name is not production-frozen until the P11.14G audit confirms the
dependency shape.

## Decision 4 â€” agent actions are descriptions, never execution

An eventual agent action is a passive description of intended work.

It must not:

- mutate runtime state;
- execute AIR;
- invoke a provider;
- perform filesystem, subprocess, network, timer, or remote I/O;
- grant authority;
- bypass authorization;
- directly apply host effects.

Execution belongs to a later downstream owner.

## Decision 5 â€” host effects reuse `EffectIntent`

`effects.model.EffectIntent` already owns passive host-effect requests.

The AIR/runtime boundary explicitly permits returning or queuing an
`EffectIntent` while forbidding the runtime from executing host effects itself.

Therefore any future agent action that represents a host-side effect must
reference an existing exact `EffectIntent` rather than duplicate host-effect
fields or invent a second effect system.

P11.14G must decide whether:

- every minimal action carries an `EffectIntent`;
- only one specialized action kind carries an `EffectIntent`; or
- the first action model remains effect-neutral and effect-bearing specialization
  is deferred.

P11.14F intentionally does not prejudge that field-shape decision.

## Decision 6 â€” tool requests are downstream specialization

Tool/provider invocation does not enter the first plan/action production slice.

A future tool request should be an explicit specialized action/request contract,
not an implicit side effect of constructing a plan or action.

Constructing a tool request must not itself invoke a provider.

## Decision 7 â€” authorization remains external

Existing authority owners already define:

- `AuthorityCheck`;
- `AuthorityGrant`;
- capability resolution;
- capability authorization.

An agent plan or action never grants authority.

Before any downstream executor performs protected work, existing
authority/authorization owners remain responsible for deciding whether execution
is permitted.

The agent domain does not duplicate capability, role, principal, grant, or policy
semantics.

## Decision 8 â€” runtime/session state is downstream

Runtime state, session state, execution receipts/results, traces, and mutation
remain downstream of passive plan/action records.

The first production slice must contain immutable data only:

- no planner algorithm;
- no executor;
- no provider call;
- no effect application;
- no I/O;
- no runtime/session mutation.

## Decision 9 â€” `AgentDefinition` remains frozen

The first operative record references the frozen `AgentDefinition`.

P11.14 does not add goals, plans, actions, runtime state, tool state, or
authorization fields to `AgentDefinition`.

## Decision 10 â€” package boundary remains module-local

`agents.__init__.__all__` remains empty.

The first operative production module remains module-local until a later explicit
integration/publication boundary.

## P11.14G next slice

P11.14G begins with a read-only field-shape audit for the minimal immutable
planning/action model.

It must settle at least:

1. whether the first production surface is `AgentPlan` alone or an
   `AgentPlan` + `AgentAction` pair;
2. whether actions use canonical IDs, embedded action objects, or typed variants;
3. whether a minimal action is effect-neutral or references exact `EffectIntent`;
4. authored-order preservation;
5. duplicate-ID and empty-plan rules;
6. exact `AgentDefinition` object identity preservation;
7. module owner and `__all__`;
8. zero planner/executor/provider/runtime/authorization behavior.

No RED production contract should be written before that field-shape audit.

## Freeze contract

P11.14F freezes only these architectural facts:

1. goal/objective remains declarative, not yet operative;
2. generic `AgentIntent` is not introduced;
3. planning is the first agent-owned operative boundary;
4. agent actions are passive descriptions;
5. host-effect semantics remain owned by exact `EffectIntent`;
6. tool requests are downstream specialization;
7. authorization remains external;
8. runtime/session execution remains downstream;
9. `AgentDefinition` remains byte/API frozen;
10. P11.14G performs the minimal planning/action field-shape audit;
11. P11.14F changes no production files.