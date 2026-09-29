# P12.5-RCV-21 Recovered Cross-Runtime Transport Architecture Census

RCV-21 is audit-only.

It inventories current transport signals around the recovered Python projection, managed runtime, and dedicated managed host without selecting a cross-runtime transport.

Historical evidence remains explicit:

- P12.5 external serialization was unselected.
- The target-neutral managed handoff had no selected concrete serialization.
- P12.2 already has a canonical AIR transport representation delegated through `air.serialization.air_to_dict`; that upstream representation must not be mistaken for a newly selected P12.5 cross-runtime transport.
- Existing managed JSON support elsewhere in `ApexForge.Runtime` likewise does not by itself select a transport for `TargetNeutralLoweringHandoff`.

The census considers in-process embedding/binding, child-process stdio, files, named pipes, local sockets, network/HTTP, shared memory, and native FFI/embedded-runtime families.

No family is selected at this gate. Network ingress remains forbidden on this recovery line, and the prior host-ingress decision remains `IN_PROCESS_API`.

Next gate: `P12.5-RCV-22 CROSS-RUNTIME TRANSPORT CONTRACT DECISION`.
