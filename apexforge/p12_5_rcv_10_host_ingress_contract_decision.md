# P12.5-RCV-10 Recovered Host Ingress Contract Decision

RCV-10 selects the first managed-host ingress family without introducing any external transport or execution behavior.

## Decision

The first host ingress family is:

`IN_PROCESS_API`

The dedicated host will eventually admit an already-constructed canonical managed handoff object through an in-process API owned by `ApexForge.Runtime.Host`.

The handoff subject remains:

`TARGET_NEUTRAL_LOWERING_PRODUCT`

The concrete managed handoff type is intentionally deferred to the next reconstruction gate.

## Why this boundary

This avoids prematurely choosing JSON, files, standard input, command-line payload transport, sockets, HTTP, named pipes, or another external serialization. It also prevents the host shell from becoming a new semantic owner.

Canonical AIR remains the language-semantic authority. The ingress layer may validate an admitted canonical handoff, but it may not execute, lower, reinterpret, resolve, authorize, or redefine it.

The P12.2 schema remains `apexforge.target-neutral-lowering/v1`.

## Deferred

Target-neutral handoff type reconstruction, ingress implementation, external serialization, command-line/stdin/file payload ingress, managed executable carriers, managed/native execution dispatch, and QSI coupling remain deferred.

## Next gate

`P12.5-RCV-11 TARGET-NEUTRAL MANAGED HANDOFF RECONSTRUCTION CONTRACT`
