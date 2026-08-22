# P11.14N â€” Agent Plan Host-Effect Consumption Successor Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14M.

Frozen predecessor:

- P11.14M commit: `4421984a8f5c43654eab9374516742a5b7333365`
- annotated tag: `afp-p11-14m-freeze`

P11.14N introduces no production type, function, module, executor, adapter class,
runtime integration, authorization bridge, handler registry, batch host API, or
AgentAction.

## Audit conclusion

P11.14M satisfied the missing prerequisite identified by P11.14K: ApexForge now
has one explicit reusable host-effect execution primitive.

The first legitimate agent-owned operative consumer can therefore be introduced
without inventing host execution, effect-type dispatch, agent identity
authorization mapping, runtime ownership, or tool-provider semantics.

The smallest truthful successor is one explicit function in `agents.execution`.

## Decision 1 â€” owner: `agents.execution`

P11.14O production owner:

- `agents.execution`

This is the first agent-owned operative bridge.

It consumes the already-frozen agent plan boundary and composes already-frozen
J/M contracts. It does not own host-effect semantics themselves.

## Decision 2 â€” no AgentExecutor class

No evidence justifies an `AgentExecutor` object with lifecycle, state, session,
tool, provider, or policy ownership.

P11.14O therefore introduces no:

- `AgentExecutor`;
- `AgentExecutionAdapter`;
- `AgentRuntime`;
- `AgentSession`;
- `AgentExecutionResult`.

The operative surface is one function.

## Decision 3 â€” exact function

P11.14O owns exactly:

```python
def execute_agent_plan(
    plan: AgentPlan,
    handler: Callable[[EffectIntent], None],
) -> Tuple[HostEffectExecutionRecord, ...]:
    ...
```

Module export:

```python
__all__ = ("execute_agent_plan",)
```

`agents.__init__.__all__` remains the exact empty tuple.

## Decision 4 â€” direct AgentPlan input

The function accepts an `AgentPlan`, not an already-projected tuple.

Reasons:

1. the agent-owned boundary remains anchored to the canonical agent plan;
2. J remains the mandatory projection path;
3. callers do not bypass the frozen planâ†’effect projection contract;
4. exact plan validation remains inherited from J.

The function must call:

```python
project_agent_plan_effect_intents(plan)
```

and must consume the exact tuple returned by that frozen projection.

## Decision 5 â€” handler contract

The caller supplies one:

```python
Callable[[EffectIntent], None]
```

The same handler object is used for every projected intent.

P11.14O validates that `handler` is callable before any host effect is executed,
including for an empty plan.

This preserves a stable function precondition independent of plan cardinality.

No effect-type dispatch is introduced. A caller may implement its own dispatch
inside its supplied callable, but that policy remains outside ApexForge's
P11.14 agent contract.

## Decision 6 â€” sequential authored-order execution

Projected intents are consumed in their exact tuple order.

For each intent, P11.14O calls the frozen M primitive:

```python
execute_host_effect(intent, handler)
```

exactly once.

The next intent is not attempted until the prior call returns normally.

No concurrency or asynchronous execution is introduced.

## Decision 7 â€” direct tuple return

Successful plan execution returns:

```python
Tuple[HostEffectExecutionRecord, ...]
```

No agent-specific wrapper result is introduced.

The returned tuple has:

1. exactly one record per projected intent;
2. the same order as the projected intent tuple;
3. each record's `intent` preserving the exact corresponding EffectIntent
   object identity.

This reuses M's success record rather than duplicating execution evidence.

## Decision 8 â€” empty plan

An empty `AgentPlan.effect_intents` tuple is valid.

After plan projection and handler validation:

```python
execute_agent_plan(empty_plan, callable_handler) == ()
```

The handler is not invoked.

No no-work result wrapper is created.

## Decision 9 â€” failure behavior

If a handler raises while executing an intent:

1. the exception propagates unchanged through M and O;
2. the failing intent is attempted exactly once;
3. no retry occurs;
4. later intents are not attempted;
5. already-completed earlier host effects remain completed;
6. no rollback is attempted;
7. no transaction/atomicity claim is made;
8. no partial-success wrapper is returned.

This is sequential host operation, not transactional execution.

## Decision 10 â€” authorization remains external

Authorization remains entirely outside `agents.execution`.

P11.14O accepts/imports no:

- AIRPrincipal;
- Principal;
- AuthorityCheck;
- AuthorityGrant;
- capability;
- resource;
- authority registry;
- role registry.

A protected caller must authorize before invoking `execute_agent_plan`.

No AgentIdentityâ†’AIRPrincipal mapping is introduced.

## Decision 11 â€” no runtime/workflow integration

P11.14O must not modify or be automatically consumed by:

- `runtime.engine`;
- `runtime.state`;
- `workflow.air_runner`;
- `workflow.directive_engine`.

The AIR runtime remains forbidden from automatically executing host effects.

`StateDelta` remains runtime-owned.

The O function is called only explicitly by a caller.

## Decision 12 â€” AgentAction remains deferred

`AgentPlan` plus its ordered `EffectIntent` values remains the only concrete
agent operation representation justified by the repository.

No second agent operation kind has appeared.

Therefore `AgentAction` remains deferred.

## Decision 13 â€” other deferred surfaces

P11.14O introduces no:

- effect-type registry;
- handler registry;
- host batch API;
- dry-run/preview;
- retry policy;
- rollback;
- transaction manager;
- concurrency;
- async execution;
- tool/provider integration;
- filesystem/network/subprocess behavior;
- diagnostics/result payloads;
- agent execution lifecycle.

## Decision 14 â€” P11.14O exact candidate implementation

P11.14O begins RED for one production file:

- `apexforge/agents/execution.py`

Candidate implementation:

```python
"""Explicit AgentPlan host-effect execution composition for P11.14O."""

from __future__ import annotations

from typing import Callable, Tuple

from effects.host_execution import (
    HostEffectExecutionRecord,
    execute_host_effect,
)
from effects.model import EffectIntent

from .plan_projection import project_agent_plan_effect_intents
from .planning import AgentPlan


def execute_agent_plan(
    plan: AgentPlan,
    handler: Callable[[EffectIntent], None],
) -> Tuple[HostEffectExecutionRecord, ...]:
    """Execute one agent plan through the frozen projection and host seam."""

    effect_intents = project_agent_plan_effect_intents(plan)

    if not callable(handler):
        raise TypeError("execute_agent_plan handler must be callable")

    records = []
    for effect_intent in effect_intents:
        records.append(execute_host_effect(effect_intent, handler))

    return tuple(records)


__all__ = ("execute_agent_plan",)
```

This candidate is not created by P11.14N.

## P11.14O RED requirements

Before implementation, the O RED gate must prove:

1. `agents.execution` does not exist;
2. import fails specifically because that module is absent;
3. M/J/N frozen hashes remain exact;
4. `agents.__all__` remains empty;
5. no AgentExecutor/AgentAction/runtime integration exists.

## P11.14O GREEN requirements

After implementation, GREEN must prove:

1. exact module export: `execute_agent_plan`;
2. exact function parameters: `plan`, `handler`;
3. exact AgentPlan/subclass rejection through frozen J projection;
4. callable handler required even for empty plans;
5. J projection called exactly once per `execute_agent_plan` invocation;
6. exact projected tuple consumed without copy/reordering before iteration;
7. same caller-supplied handler identity supplied to every M call;
8. M called once per intent in exact authored order;
9. one exact `HostEffectExecutionRecord` per successful intent;
10. output tuple order matches projected intent order;
11. output record intent identities match projected intent identities;
12. empty plan returns exact empty tuple;
13. empty plan invokes handler zero times;
14. handler exception object propagates unchanged;
15. failing handler is not retried;
16. later intents are not attempted after failure;
17. prior successful effects are not rolled back;
18. no wrapper result;
19. no batch host API;
20. no effect-type dispatch/registry;
21. no authorization/runtime/workflow/StateDelta integration;
22. no AgentExecutor/AgentRuntime/AgentSession/AgentAction;
23. no tool/provider/filesystem/network/subprocess dependency;
24. `agents.__init__.__all__` remains empty.

## Freeze contract

P11.14N freezes:

1. first agent-owned operative consumer = `agents.execution`;
2. one function, not an executor class;
3. function = `execute_agent_plan`;
4. direct exact AgentPlan input;
5. frozen J projection is mandatory;
6. one caller-supplied handler;
7. handler callable validation occurs even for empty plans;
8. frozen M primitive executes each intent sequentially;
9. direct ordered tuple of M execution records is returned;
10. exact intent identity/order preserved;
11. empty plan returns `()`;
12. failure propagates immediately unchanged;
13. no retry;
14. later intents stop after failure;
15. prior completed host effects are not rolled back;
16. authorization remains external;
17. runtime/workflow remain non-integrated;
18. StateDelta remains runtime-owned;
19. AgentAction remains deferred;
20. registries, batch host execution, dry-run, retries, rollback, concurrency,
    async execution, tools/providers, and execution lifecycle remain deferred;
21. `agents.__all__` remains empty;
22. P11.14N changes no production files.