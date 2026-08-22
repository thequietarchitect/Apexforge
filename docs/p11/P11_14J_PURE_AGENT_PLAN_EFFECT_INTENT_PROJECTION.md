# P11.14J â€” Pure Agent Plan Effect-Intent Projection

## Status

RED contract only. Production implementation is intentionally absent.

Frozen predecessor:

- P11.14I commit: `cac40ce8b6ad3a5ca603a078f3c14cadedeeee1d`
- annotated tag: `afp-p11-14i-freeze`

## Production owner

P11.14J introduces one production module only after RED:

- `agents.plan_projection`

The module exposes exactly one public function:

```python
def project_agent_plan_effect_intents(
    plan: AgentPlan,
) -> Tuple[EffectIntent, ...]:
    ...
```

## Contract

`project_agent_plan_effect_intents`:

1. requires `type(plan) is AgentPlan`;
2. raises `TypeError` for every non-exact `AgentPlan`;
3. returns `plan.effect_intents`;
4. preserves tuple object identity exactly;
5. therefore preserves every exact `EffectIntent` object identity;
6. therefore preserves authored effect order;
7. accepts a valid empty `AgentPlan`;
8. returns the exact empty tuple owned by that empty plan;
9. performs no independent EffectIntent validation or deduplication;
10. does not copy or rebuild the tuple.

## Package boundary

`agents.plan_projection.__all__` must be exactly:

```python
("project_agent_plan_effect_intents",)
```

`agents.__init__.__all__` remains empty.

The function is not re-exported from `agents`.

## Dependency boundary

`agents.plan_projection` may import only:

- `Tuple`;
- `EffectIntent`;
- `AgentPlan`.

It must not import:

- agent model/catalog/resolution/character binding directly;
- AIR;
- authority/authorization/roles/governance;
- runtime/workflow;
- tooling;
- cache;
- TAM/TAP;
- providers;
- sessions.

## Non-operative boundary

Calling the projection:

- does not execute host effects;
- does not authorize capabilities;
- does not create or modify `StateDelta`;
- does not execute AIR;
- does not invoke workflow engines;
- does not invoke tools/providers;
- does not mutate an `AgentPlan`;
- does not mutate an `EffectIntent`;
- performs no filesystem, subprocess, network, timer, or remote I/O.

## Deferred

P11.14J does not introduce:

- `AgentAction`;
- `AgentPlanExecutionRequest`;
- `AgentPlanConsumptionRequest`;
- `AgentPlanProjection` record;
- `AgentPlanHandoff` record;
- `AgentPlanResult`;
- `AgentPlanReceipt`;
- `AgentExecutionResult`;
- `AgentExecutionReceipt`;
- `AgentExecutor`;
- `agents.execution`;
- authorization integration;
- runtime integration;
- tool/provider integration.

## RED condition

Before production implementation, importing `agents.plan_projection` must fail
specifically because the module does not exist.

The RED gate must not stage, commit, tag, or create production code.