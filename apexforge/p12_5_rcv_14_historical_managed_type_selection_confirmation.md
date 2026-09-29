# P12.5-RCV-14 Recovered Historical Managed Type Selection Confirmation

RCV-14 confirms the recovered historical managed type surface for `ApexForge.Runtime.TargetNeutralLoweringHandoff`.

Selected declaration:

`public sealed record TargetNeutralLoweringHandoff(...)`

Selected fields:

- `string Schema`
- `string VerifiedAirFingerprint`
- `string RoutingFingerprint`
- `string EntryDirective`
- `IReadOnlyList<string> DirectiveOwnerIds`
- `string ProductFingerprint`

The required schema remains `apexforge.target-neutral-lowering/v1`.

Validation remains historical: schema equality by ordinal comparison; 64-character hexadecimal fingerprints; uppercase required only for `ProductFingerprint`; non-empty entry directive; non-null owner list with non-empty owner IDs.

`ManagedRuntimeHost.AdmitTargetNeutralHandoff(...)` remains a validate-and-return boundary.

No implementation is created at RCV-14. External serialization, executable-carrier reconstruction, execution dispatch, and QSI coupling remain deferred.

Next gate: `P12.5-RCV-15 TARGET-NEUTRAL HANDOFF IMPLEMENTATION FOUNDATION`.
