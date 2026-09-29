# P12.5-RCV-48 Managed Carrier Integration Scope Decision

Historical and current architecture do not authorize a carrier consumer, external payload source, process bridge, or execution contract.

The decoder is therefore retained as an in-process structural construction API in `ApexForge.Runtime`. A separate `ManagedRuntimeHost` carrier-admission method would have no authorized downstream consumer and is deferred. Host ingress wiring, execution dispatch, target-neutral handoff coupling, and cross-runtime transport are likewise deferred.

No stdio, file, pipe, socket, HTTP, shared-memory, Python.NET, new native FFI, or arbitrary external JSON ingress is selected. Network ingress remains forbidden.

This gate makes no production change.

Next gate: `P12.5-RCV-49 MANAGED CARRIER REPRESENTATIONAL EQUIVALENCE ACCEPTANCE`.
