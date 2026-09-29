# P12.5-RCV-22 Recovered Cross-Runtime Transport Contract Decision

RCV-22 deliberately does **not** invent a Python-to-.NET transport.

Recovered evidence shows that historical P12.5 left external serialization and concrete handoff serialization unselected. The current recovery line likewise has no transport implementation in `ManagedHandoffProjection`, `TargetNeutralLoweringHandoff`, or the dedicated managed host.

## Decision

`CROSS_RUNTIME_TRANSPORT = DEFERRED_NO_TRANSPORT_AUTHORIZED`

The current authorized flow remains split:

- source side: `TargetNeutralLoweringProduct -> ManagedHandoffProjection`
- managed side: `TargetNeutralLoweringHandoff -> ManagedRuntimeHost.AdmitTargetNeutralHandoff`
- host shell: lifecycle/orchestration only

There is not yet a runtime crossing connecting those two value-object surfaces.

Managed host ingress remains `IN_PROCESS_API`, consistent with RCV-10. This does not imply a Python/.NET embedding technology, serializer, child process, pipe, socket, file, or FFI bridge.

Network ingress remains forbidden on this recovery line. Execution dispatch remains deferred.

Next gate: `P12.5-RCV-23 MANAGED HOST INGRESS IMPLEMENTATION CENSUS`.
