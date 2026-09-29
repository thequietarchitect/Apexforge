# P12.5-RCV-15 Recovered Target-Neutral Handoff Implementation Foundation

RCV-15 restores the historical managed handoff implementation boundary.

It adds `ApexForge.Runtime.TargetNeutralLoweringHandoff` as a public sealed record with the recovered six-field surface:

- `string Schema`
- `string VerifiedAirFingerprint`
- `string RoutingFingerprint`
- `string EntryDirective`
- `IReadOnlyList<string> DirectiveOwnerIds`
- `string ProductFingerprint`

Validation reproduces the recovered historical rules. `ManagedRuntimeHost.AdmitTargetNeutralHandoff(...)` performs null rejection, calls `Validate()`, and returns the same admitted handoff.

This gate does not add external serialization, file/stdin/CLI payload ingress, managed executable carriers, native calls, or execution dispatch.

Canonical AIR remains the language-semantic authority.

Next gate: `P12.5-RCV-16 TARGET-NEUTRAL HANDOFF PROJECTION BRIDGE CENSUS`.
