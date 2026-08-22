# P11.14M â€” Explicit Reusable Host-Effect Execution Seam

## Status

RED contract following frozen P11.14L.

Frozen predecessor:

- P11.14L commit: `26bbd97cf749ca84abca722eb7e3119bcecb3458`
- annotated tag: `afp-p11-14l-freeze`

This RED contract creates no production host-execution module.

## Production owner

P11.14M production owner:

- `effects.host_execution`

The passive `EffectIntent` declaration remains owned by `effects.model`.

`effects.__init__` remains unchanged and continues to export only
`EffectIntent`.

## Exact production surface

P11.14M introduces exactly:

```python
@dataclass(frozen=True)
class HostEffectExecutionRecord:
    intent: EffectIntent
```

and:

```python
def execute_host_effect(
    intent: EffectIntent,
    handler: Callable[[EffectIntent], None],
) -> HostEffectExecutionRecord:
    ...
```

Module exports:

```python
__all__ = (
    "HostEffectExecutionRecord",
    "execute_host_effect",
)
```

## HostEffectExecutionRecord contract

1. immutable frozen dataclass;
2. one field only: `intent`;
3. `type(intent) is EffectIntent` required;
4. stores the exact `EffectIntent` object by identity;
5. does not copy `id`, `effect_type`, or `facts`;
6. is evidence only that the supplied handler returned normally;
7. is not an authorization proof;
8. is not a runtime result;
9. contains no payload/result/diagnostic/error/status/success field.

## execute_host_effect contract

1. `type(intent) is EffectIntent` required;
2. non-exact intent values raise `TypeError`;
3. `handler` must be callable;
4. non-callable handlers raise `TypeError`;
5. handler receives the exact `EffectIntent` object;
6. handler is invoked exactly once;
7. handler return value is ignored;
8. successful handler return creates one
   `HostEffectExecutionRecord(intent=intent)`;
9. returned record preserves exact intent object identity;
10. handler exceptions propagate unchanged;
11. handler exceptions do not produce a record;
12. no retry occurs after handler failure.

## No effect-type dispatch

P11.14M does not inspect `intent.effect_type` to select an implementation.

There is no:

- handler registry;
- provider registry;
- effect-type registry;
- dispatch table;
- unknown-effect policy;
- dynamic import/discovery.

The handler is explicit and caller-supplied.

## No batch execution

P11.14M introduces no:

- `execute_host_effects`;
- batch request;
- batch result;
- effect tuple executor.

The primitive seam executes one exact intent.

## Authorization boundary

Authorization remains external and must occur before a protected caller invokes
the host seam.

P11.14M does not import or accept:

- AIRPrincipal;
- Principal;
- AuthorityCheck;
- AuthorityGrant;
- role registry;
- authority registry;
- capability;
- resource.

It does not map AgentIdentity to AIRPrincipal.

## AIR runtime boundary

The AIR runtime remains permanently non-executing with respect to host effects.

P11.14M does not modify or integrate with:

- `runtime.engine`;
- `runtime.state`;
- `workflow.air_runner`;
- `workflow.directive_engine`.

No runtime path automatically invokes `execute_host_effect`.

## State boundary

P11.14M does not construct, modify, or consume StateDelta.

It does not mutate runtime state.

## No host implementation in M

The seam itself performs no filesystem, subprocess, network, plugin, provider,
tool, or CLI operation.

Only the caller-supplied handler may perform a concrete host operation.

P11.14M imports no:

- agents;
- air;
- authority;
- authorization;
- runtime;
- workflow;
- tooling;
- tools;
- providers;
- subprocess;
- pathlib;
- os;
- socket;
- requests.

## Deferred

The following remain deferred:

- EffectHandlerRegistry;
- effect-type dispatch;
- unknown-effect handling policy;
- batch execution;
- dry-run / preview;
- simulation;
- execution diagnostics;
- execution receipts beyond the minimal success record;
- result payloads;
- retries;
- tools/providers;
- AgentExecutor;
- AgentRuntime;
- AgentSession;
- AgentAction;
- agent authorization bridge.

## Candidate implementation

The future GREEN implementation is intentionally minimal:

```python
"""Explicit reusable host-effect execution seam for P11.14M."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from effects.model import EffectIntent


@dataclass(frozen=True)
class HostEffectExecutionRecord:
    """Immutable evidence that one supplied host-effect handler returned."""

    intent: EffectIntent

    def __post_init__(self) -> None:
        if type(self.intent) is not EffectIntent:
            raise TypeError(
                "HostEffectExecutionRecord.intent must be an exact EffectIntent"
            )


def execute_host_effect(
    intent: EffectIntent,
    handler: Callable[[EffectIntent], None],
) -> HostEffectExecutionRecord:
    """Invoke one explicit caller-supplied host-effect handler exactly once."""

    if type(intent) is not EffectIntent:
        raise TypeError("execute_host_effect requires an exact EffectIntent")
    if not callable(handler):
        raise TypeError("execute_host_effect handler must be callable")

    handler(intent)

    return HostEffectExecutionRecord(intent=intent)


__all__ = (
    "HostEffectExecutionRecord",
    "execute_host_effect",
)
```

The RED phase does not create that file.

## RED expectation

The P11.14M smoke test imports:

```python
effects.host_execution
```

Before GREEN, the import must fail specifically with:

```text
ModuleNotFoundError: No module named 'effects.host_execution'
```

A different failure is not accepted as the intended RED state.

## Future GREEN acceptance

After the one production module exists, the same smoke test must prove:

1. exact module exports;
2. exact function signature parameters `intent`, `handler`;
3. frozen dataclass record;
4. one record field only: `intent`;
5. exact `EffectIntent` input requirement;
6. exact record intent requirement;
7. callable handler requirement;
8. same intent object reaches handler;
9. handler called exactly once;
10. handler return payload ignored;
11. record preserves exact intent identity;
12. handler exception object propagates unchanged;
13. no retry after failure;
14. `effects.__all__` remains `("EffectIntent",)`;
15. host execution is not package-level re-exported;
16. no `execute_host_effects`;
17. no registry/dispatch surface;
18. no dry-run/preview;
19. no authorization/runtime/workflow/agent/tool/provider dependency;
20. no filesystem/subprocess/network behavior in the production seam.