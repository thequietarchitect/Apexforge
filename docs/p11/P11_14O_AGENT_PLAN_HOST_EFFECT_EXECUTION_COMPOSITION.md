# P11.14O â€” Agent Plan Host-Effect Execution Composition

## Status

RED contract following frozen P11.14N.

Frozen predecessor:

- P11.14N commit: `f9471def8fa9b3f6cbbc39bb9b4743838d624e46`
- annotated tag: `afp-p11-14n-freeze`

This RED contract creates no production `agents.execution` module.

## Exact production owner

P11.14O production owner:

- `agents.execution`

The package-level `agents.__all__` remains the exact empty tuple.

## Exact production surface

P11.14O introduces exactly one function:

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

No class is introduced.

## Mandatory frozen composition

The function must compose the already-frozen boundaries:

```text
AgentPlan
  -> project_agent_plan_effect_intents(plan)      [P11.14J]
  -> ordered exact EffectIntent tuple
  -> execute_host_effect(intent, handler)         [P11.14M]
  -> ordered HostEffectExecutionRecord tuple
```

P11.14O must not directly access `plan.effect_intents` as a substitute for the
frozen J projection.

## Input and projection contract

1. the function accepts one `AgentPlan`;
2. exact AgentPlan validation is inherited from frozen J;
3. AgentPlan subclasses are rejected by J;
4. `project_agent_plan_effect_intents(plan)` is called exactly once;
5. the exact projected tuple is iterated in its existing order;
6. the adapter does not copy, sort, deduplicate, or transform intents before
   host execution.

## Handler contract

1. the caller supplies one handler object;
2. `handler` must be callable;
3. callable validation occurs before any host execution;
4. callable validation occurs even for an empty plan;
5. the same handler object is supplied to every M invocation;
6. no handler registry or effect-type dispatch is introduced.

## Execution contract

For each projected intent, in exact order:

```python
execute_host_effect(effect_intent, handler)
```

is called exactly once.

Execution is sequential.

There is no:

- concurrency;
- async execution;
- retry;
- batch host primitive.

## Return contract

Successful execution returns:

```python
Tuple[HostEffectExecutionRecord, ...]
```

The tuple contains exactly one M record per successful projected intent in the
same order.

Each record preserves the exact identity of its corresponding EffectIntent.

There is no:

- AgentExecutionResult;
- AgentExecutionRecord;
- wrapper status;
- payload;
- diagnostic envelope;
- receipt beyond M's frozen record.

## Empty plan

For a valid empty AgentPlan and callable handler:

```python
execute_agent_plan(plan, handler) == ()
```

The handler is invoked zero times.

The returned object is the canonical empty tuple.

## Failure contract

If the handler raises for one intent:

1. M propagates the same exception object unchanged;
2. O does not catch or translate it;
3. the failing intent is attempted once;
4. there is no retry;
5. later intents are not attempted;
6. earlier successfully completed host effects remain completed;
7. no rollback occurs;
8. no transactional or atomic execution guarantee is claimed;
9. no partial-result wrapper is returned.

## Authorization boundary

Authorization remains external and pre-execution.

P11.14O imports or accepts no:

- AIRPrincipal;
- Principal;
- AuthorityCheck;
- AuthorityGrant;
- capability;
- resource;
- authority registry;
- role registry.

No AgentIdentity-to-principal bridge is introduced.

## Runtime and workflow boundary

P11.14O does not modify or integrate with:

- `runtime.engine`;
- `runtime.state`;
- `workflow.air_runner`;
- `workflow.directive_engine`.

The AIR runtime remains forbidden from automatically executing host effects.

`StateDelta` remains runtime-owned.

## Deferred

Still deferred:

- AgentExecutor;
- AgentExecutionAdapter class;
- AgentExecutionResult;
- AgentRuntime;
- AgentSession;
- AgentAction;
- effect-type registry;
- handler registry;
- host batch API;
- dry-run / preview;
- retries;
- rollback;
- transaction manager;
- concurrency;
- async execution;
- tools/providers;
- concrete host implementations.

## Candidate GREEN implementation

The future GREEN production file is exactly:

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

The RED phase does not create this file.

## RED expectation

Before GREEN, importing:

```python
agents.execution
```

must fail specifically with:

```text
ModuleNotFoundError: No module named 'agents.execution'
```

A different failure is not the intended RED state.

## GREEN acceptance

After production implementation, the same smoke test must prove:

1. exact export `execute_agent_plan`;
2. exact parameters `plan`, `handler`;
3. exact AgentPlan/subclass rejection via J;
4. J projection invoked exactly once;
5. handler validation before host execution;
6. handler validation for empty plan;
7. same handler identity passed to every M call;
8. M invoked once per projected intent;
9. authored/projected order preserved;
10. record tuple order preserved;
11. exact intent identities preserved in records;
12. empty plan returns exact empty tuple;
13. empty plan invokes handler zero times;
14. handler exception identity propagates unchanged;
15. failing handler invoked once;
16. later intents not attempted after failure;
17. prior completed effects not rolled back;
18. no result wrapper;
19. no AgentExecutor/AgentAction;
20. no effect-type registry/dispatch;
21. no batch host API;
22. no authorization/runtime/workflow/StateDelta integration;
23. no filesystem/subprocess/network/tool/provider dependency;
24. `agents.__all__` remains empty.