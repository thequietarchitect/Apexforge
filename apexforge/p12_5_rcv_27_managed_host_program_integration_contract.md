# P12.5-RCV-27 Recovered Managed Host Program Integration Contract

RCV-27 decides **not** to wire `RuntimeHostIngress` into the executable `Program.cs` yet.

The recovered line has an in-process ingress adapter, but no recovered external payload source, no selected handoff serialization, and no authorized Python-to-.NET runtime transport. Wiring the adapter into `Program.cs` at this point would create dead composition without a legitimate handoff source.

## Decision

`PROGRAM_INGRESS_WIRING = DEFERRED_NO_PAYLOAD_SOURCE`

Therefore:

- `Program.cs` continues to own only deterministic host lifecycle/orchestration.
- `RuntimeHostIngress` remains available as an in-process API surface.
- `Program.cs` does not construct `RuntimeHostIngress`.
- `Program.cs` does not construct or admit `TargetNeutralLoweringHandoff`.
- lifecycle-to-ingress coupling remains deferred.
- external serialization remains unselected.
- cross-runtime transport remains unauthorized.
- network ingress remains forbidden.
- execution dispatch remains deferred.

This is a governance decision, not a historical identity claim.

The recovery line now pivots to the historically observed later P12.5 managed executable-carrier surface.

Next gate: `P12.5-RCV-28 MANAGED EXECUTABLE CARRIER HISTORICAL CENSUS`.
