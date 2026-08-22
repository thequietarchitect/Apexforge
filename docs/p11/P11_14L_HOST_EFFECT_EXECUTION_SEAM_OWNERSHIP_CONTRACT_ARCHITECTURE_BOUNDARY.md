# P11.14L â€” Host-Effect Execution Seam Ownership / Contract Architecture Boundary

## Status

Architecture-only boundary following frozen P11.14K.

Frozen predecessor:

- P11.14K commit: `1de4ef6e763d016983969ec9160005d89b53b8d4`
- annotated tag: `afp-p11-14k-freeze`

P11.14L introduces no production type, function, module, registry, executor, or
host-effect implementation.

## Audit conclusion

The missing prerequisite identified by P11.14K is real: ApexForge has no
canonical reusable host-effect execution seam.

P11.14L selects the smallest truthful owner and contract for P11.14M without
introducing agent execution, AIR-runtime host execution, provider/tool coupling,
or an effect-type taxonomy.

## Decision 1 â€” owner: `effects.host_execution`

`EffectIntent` is already source-owned by `effects.model`.

The repository has real filesystem/process side effects in specialized tooling,
tools, serialization, and export surfaces, but none of those subsystems owns a
generic reusable host-effect abstraction.

P11.14L therefore selects:

- production module: `effects.host_execution`

This does not make `effects.model` operative.  The model module remains a
passive declaration owner.

The host-execution module is separate so that passive description and optional
host-side operation remain distinct surfaces inside the same canonical domain.

## Decision 2 â€” the seam is not agent-owned

The execution seam must be reusable by:

- agent-originated projected effects;
- runtime-originated effect tuples after they leave the AIR runtime;
- future governance/simulation/distribution layers;
- direct non-agent host callers.

Therefore P11.14M must not import `agents`.

No `AgentExecutor`, `AgentRuntime`, `AgentSession`, or AgentIdentity bridge is
introduced.

## Decision 3 â€” primitive granularity: one exact `EffectIntent`

P11.14M's primitive host-operation seam accepts one exact `EffectIntent`.

It does not accept an effect tuple.

Reasons:

1. one-intent execution isolates one host operation;
2. failure boundaries remain per intent;
3. exact intent object identity can be preserved directly;
4. ordered tuple execution can be composed later without forcing batch policy
   into the primitive seam.

Batch execution remains deferred.

## Decision 4 â€” caller-supplied handler, no registry

There are currently no concrete canonical `effect_type` values used for
production dispatch.  The repository does not compare `effect_type` against a
canonical taxonomy.

Therefore P11.14M must not introduce:

- `EffectHandlerRegistry`;
- effect-type registration;
- effect-type dispatch;
- unknown-effect policy;
- provider discovery/loading;
- tool routing.

Instead, the caller supplies the callable that performs one host-side effect.

The P11.14M function validates only that the handler is callable.  It does not
infer or resolve a handler from `intent.effect_type`.

## Decision 5 â€” exact M function

P11.14M owns exactly:

```python
def execute_host_effect(
    intent: EffectIntent,
    handler: Callable[[EffectIntent], None],
) -> HostEffectExecutionRecord:
    ...
```

Rules:

1. `type(intent) is EffectIntent` is required;
2. non-exact intent values raise `TypeError`;
3. `handler` must be callable;
4. the handler receives the exact same `EffectIntent` object by identity;
5. the function invokes the handler exactly once;
6. the function performs no independent `effect_type` dispatch;
7. the handler's return value is not part of the P11.14M semantic contract;
8. successful handler return produces one immutable execution record;
9. handler exceptions propagate unchanged;
10. the function does not retry.

The callable annotation expresses a side-effect handler contract. P11.14M does
not inspect or serialize a handler return payload.

## Decision 6 â€” immutable success record

P11.14M introduces exactly:

```python
@dataclass(frozen=True)
class HostEffectExecutionRecord:
    intent: EffectIntent
```

Rules:

1. `intent` must be an exact `EffectIntent`;
2. the record preserves the exact executed intent object by identity;
3. the record adds no duplicated `id`, `effect_type`, or `facts`;
4. existence of the record means the supplied handler returned normally;
5. no success boolean is required;
6. no result payload is introduced;
7. no receipt/result/diagnostic/error field is introduced.

This record is not an authorization proof and not a runtime result.

## Decision 7 â€” failures propagate

P11.14M does not invent a new failure taxonomy before concrete host-effect
implementations exist.

If the caller-supplied handler raises an exception:

- the exception propagates unchanged;
- no `HostEffectExecutionRecord` is produced;
- the seam does not convert the exception into diagnostics;
- the seam does not retry;
- the seam does not partially report success.

Handler-specific failure semantics remain owned by the handler until a shared
cross-handler failure contract is justified.

## Decision 8 â€” authorization remains external

Existing authority/authorization code owns principal and capability decisions
that must occur before protected execution.

P11.14M receives no:

- AIRPrincipal;
- Principal;
- AuthorityCheck;
- AuthorityGrant;
- capability;
- resource;
- role registry;
- authority registry;
- authorization result.

The caller is responsible for authorization before calling
`execute_host_effect`.

This prevents a generic host-effect seam from inventing an AgentIdentity to
AIRPrincipal mapping.

## Decision 9 â€” AIR runtime remains non-executing

The frozen invariant remains:

**The AIR runtime may return/queue `EffectIntent` values but must never execute
host effects.**

P11.14M must not modify or be imported by:

- `runtime.engine`;
- `runtime.state`;
- `workflow.air_runner`;
- `workflow.directive_engine`.

No runtime path automatically calls `execute_host_effect`.

Host execution occurs only when an external caller explicitly invokes the new
seam.

## Decision 10 â€” no StateDelta mutation

P11.14M does not:

- construct `StateDelta`;
- append effects to `StateDelta`;
- remove effects from `StateDelta`;
- apply state assignments;
- mutate RuntimeEngine state.

`StateDelta` remains runtime-owned.

## Decision 11 â€” no dry-run flag

No repository precedent requires a generic host-effect dry-run contract yet.

Non-execution remains explicit: callers simply do not call
`execute_host_effect`.

P11.14M introduces no:

- `dry_run`;
- preview flag;
- simulation mode;
- execute/preview union.

A future Simulation Plane may define hypothetical execution independently.

## Decision 12 â€” no batch layer in M

P11.14M does not introduce `execute_host_effects`.

Ordered tuple execution remains a later composition boundary.

When introduced, an empty exact tuple may naturally represent deterministic
no-work, but M does not own that batch rule yet.

## Decision 13 â€” no tools/providers in M

Existing tools/tooling perform concrete specialized host work, but they are not
the generic host-effect owner.

P11.14M therefore does not invoke:

- tools;
- CLI;
- subprocess;
- filesystem APIs;
- network APIs;
- Codex;
- providers;
- plugins.

Concrete handler implementations remain downstream.

## Decision 14 â€” package exports

P11.14M production module:

- `effects.host_execution`

Its `__all__` must be exactly:

```python
(
    "HostEffectExecutionRecord",
    "execute_host_effect",
)
```

`effects.__init__.__all__` remains frozen and continues to expose only
`EffectIntent`.

The new execution surface is therefore explicit rather than implicitly
re-exported.

## P11.14M exact production contract

P11.14M begins RED for one production file only:

- `apexforge/effects/host_execution.py`

Candidate implementation shape:

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

This candidate is not created by P11.14L.

## P11.14M RED requirements

The M RED gate must prove before implementation:

1. `effects.host_execution` does not yet exist;
2. import fails specifically because that module is absent;
3. K/L frozen hashes remain exact;
4. effects model/package exports remain frozen;
5. runtime non-execution invariant remains exact;
6. no agent/runtime/workflow/authority/tool/provider integration is introduced.

After implementation, GREEN must prove:

1. exact `EffectIntent` required;
2. callable handler required;
3. exact intent identity delivered to handler;
4. handler called exactly once;
5. exact intent identity preserved in the execution record;
6. frozen dataclass record;
7. handler exception identity propagates unchanged;
8. no retry after failure;
9. no batch API;
10. no registry/effect-type dispatch;
11. no StateDelta/runtime mutation;
12. no package-level re-export;
13. no agent/AIR/runtime/workflow/authority/tool/provider imports.

## Freeze contract

P11.14L freezes:

1. host execution is not agent-owned;
2. `effects.host_execution` is the selected owner;
3. `effects.model` remains passive;
4. primitive execution accepts one exact `EffectIntent`;
5. caller supplies the handler explicitly;
6. no handler registry/effect-type dispatch exists in M;
7. M introduces `HostEffectExecutionRecord(intent)`;
8. exact EffectIntent identity is preserved into handler and record;
9. handler exceptions propagate unchanged;
10. authorization remains external/pre-execution;
11. AIR runtime remains permanently non-executing with respect to host effects;
12. StateDelta remains runtime-owned;
13. dry-run is deferred;
14. batch execution is deferred;
15. tools/providers/concrete host implementations are deferred;
16. `effects.__init__` remains unchanged;
17. P11.14L changes no production files.