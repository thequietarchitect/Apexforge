# P11.14G â€” Minimal Immutable Agent Plan over Exact Effect Intents

## Status

RED contract only. Production implementation is intentionally absent.

Frozen predecessor:

- P11.14F commit: `6dfd6004869dfd8e23c3bc1647d78574e66889ab`
- annotated tag: `afp-p11-14f-freeze`

## Architecture decision

P11.14G introduces the first operative agent-domain production record as a
minimal immutable plan.

The exact production shape is:

```python
@dataclass(frozen=True)
class AgentPlan:
    definition: AgentDefinition
    effect_intents: Tuple[EffectIntent, ...] = ()
```

Primary production owner:

- `agents.planning`

## Why G does not introduce `AgentAction`

The field-shape audit found no existing `AgentAction` or specialized agent-action
surface.

`EffectIntent` already supplies:

- stable request identity through `EffectIntent.id`;
- an effect kind through `effect_type`;
- immutable effect facts;
- passive/non-executing semantics.

Wrapping each `EffectIntent` in an `AgentAction` with another canonical ID would
duplicate identity. An effect-neutral `AgentAction` would currently contain no
concrete work semantics. A generic payload or kind taxonomy would be speculative.

Therefore G introduces no `AgentAction`.

A later slice may introduce a distinct action type only when a second concrete
operation kind requires a common action abstraction.

## AgentPlan invariants

`AgentPlan`:

1. is a frozen dataclass;
2. has fields exactly `definition,effect_intents`;
3. preserves the exact supplied `AgentDefinition` object;
4. requires `effect_intents` to be an exact tuple;
5. requires every tuple item to be an exact `EffectIntent`;
6. preserves authored tuple order;
7. preserves exact `EffectIntent` object identities;
8. accepts the empty tuple as a valid immutable no-work plan;
9. rejects duplicate `EffectIntent.id` values within one plan;
10. allows distinct effect intents with different IDs even when their
    `effect_type` and facts are otherwise equal.

Duplicate rejection is identity consistency, not execution policy.

## Dependency boundary

`agents.planning` may import only:

- dataclass support;
- `Tuple`;
- `effects.model.EffectIntent`;
- `AgentDefinition` from `agents.model`.

It must not import:

- agent archetype catalog/resolution;
- character binding;
- AIR;
- causality;
- authority/authorization/roles/governance;
- runtime/workflow;
- tooling;
- cache;
- TAM/TAP;
- providers or adapters.

## Execution boundary

Constructing an `AgentPlan`:

- does not execute effects;
- does not run AIR;
- does not authorize capabilities;
- does not invoke tools/providers;
- does not mutate runtime/session state;
- performs no filesystem, subprocess, network, timer, or remote I/O.

`EffectIntent` remains owned by `effects.model`.

## Package boundary

`agents.planning.__all__ == ("AgentPlan",)`.

`agents.__init__.__all__` remains empty and `AgentPlan` is not re-exported from
the top-level package.

## Frozen predecessor boundary

P11.14B-F production and architecture owners remain byte/API unchanged.

## Deferred

P11.14G does not introduce:

- `AgentAction`;
- action kind taxonomy;
- action resolver/catalog;
- planner algorithm;
- plan builder;
- executor;
- tool request/provider invocation;
- authorization integration;
- runtime/session integration;
- result/receipt/trace model;
- grammar/compiler/project/tooling integration.