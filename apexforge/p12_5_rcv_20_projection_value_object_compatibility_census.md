# P12.5-RCV-20 Recovered Projection Value-Object Compatibility Census

RCV-20 is audit-only. It verifies structural compatibility between the recovery-selected Python `ManagedHandoffProjection` and the recovered C# `TargetNeutralLoweringHandoff`.

Compatibility is limited to:

- identical six-field boundary ordering,
- deterministic Python-to-managed field correspondence,
- compatible scalar/list representations,
- exact target-neutral schema continuity,
- Python projection immutability,
- managed record immutability,
- managed validate-and-return admission,
- absence of `canonical_json` and binding objects from the boundary.

This census does not select or implement serialization, IPC, hosting, embedding, file/stdin/CLI transport, executable carriers, or execution dispatch.

It also records whether `ManagedHandoffProjection` is currently exported from `apexforge.native_backend.__init__`, but RCV-20 is not authorized to change that package surface.

Next gate: `P12.5-RCV-21 CROSS-RUNTIME TRANSPORT ARCHITECTURE CENSUS`.
