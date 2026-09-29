# P12.5-RCV-7 Recovered Managed Host Lifecycle and Startup Contract

This slice defines lifecycle and startup ownership only. It does not add host ingress, external serialization, executable-carrier semantics, or execution dispatch.

## Startup

`ApexForge.Runtime.Host` remains an orchestration and lifecycle shell. Startup is deterministic and single-process: process start, host construction, runtime-library availability, then ready-or-fail. No network listener, daemon, background service, or execution dispatch is introduced here.

## Shutdown

Shutdown is explicit and bounded: stop request or process exit, host quiesce, resource release through existing owners, then process exit. Native resource ownership remains with the existing managed/native ABI boundary.

## Authority

Canonical AIR remains the language-semantic authority. `ApexForge.Runtime` remains the managed runtime library. `ApexForge.Runtime.Host` does not define language semantics and may not duplicate `ManagedNativeAbi`.

## Deferred

Host ingress, external serialization, managed execution dispatch, native execution dispatch, managed executable carrier reconstruction, and QSI coupling remain deferred.

## Next

`P12.5-RCV-8 HOST LIFECYCLE AND STARTUP IMPLEMENTATION FOUNDATION`
