# P12.5-RCV-25 Recovered Managed Host Ingress Implementation Foundation

RCV-25 implements the narrow in-process ingress adapter selected by RCV-24.

Added production type:

`ApexForge.Runtime.Host.RuntimeHostIngress`

The adapter:

- accepts an existing `ManagedRuntimeHost`,
- rejects a null runtime dependency,
- exposes `Admit(TargetNeutralLoweringHandoff handoff)`,
- delegates directly to `ManagedRuntimeHost.AdmitTargetNeutralHandoff(handoff)`,
- returns the delegate result unchanged.

It does not duplicate handoff validation and has no lifecycle coupling.

`Program.cs`, `RuntimeHostLifecycle.cs`, `ManagedRuntimeHost.cs`, and `TargetNeutralLoweringHandoff.cs` remain unchanged by this gate.

No external serialization, Python/.NET runtime transport, CLI/stdin/file payload ingress, pipe/socket/network ingress, executable carrier, or execution dispatch is introduced.

This is a recovery-selected implementation and does not claim identity with a lost historical implementation.

Next gate: `P12.5-RCV-26 MANAGED HOST INGRESS INTEGRATION CENSUS`.
