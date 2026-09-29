# P12.5-RCV-13-R1 Historical Handoff Projection Correction

Recovered historical P12.5 evidence shows that the original managed `TargetNeutralLoweringHandoff` did **not** mirror the four Python dataclass fields directly.

The historical managed record shape was:

- `string Schema`
- `string VerifiedAirFingerprint`
- `string RoutingFingerprint`
- `string EntryDirective`
- `IReadOnlyList<string> DirectiveOwnerIds`
- `string ProductFingerprint`

The managed boundary therefore projects selected canonical source data plus derived views from `TargetNeutralLoweringProduct`. `canonical_json` remains part of the Python lowering product but was not a field of the historical managed handoff.

Historical validation required the exact target-neutral schema, 64-character hexadecimal fingerprints, uppercase product fingerprint, a non-empty entry directive, and a non-null owner list containing only non-empty owner IDs.

This correction supersedes the initial RCV-13 one-to-one dataclass mapping. It does not yet create `TargetNeutralLoweringHandoff.cs` or modify `ManagedRuntimeHost.cs`.

Canonical AIR remains the language-semantic authority. Execution dispatch and external serialization remain deferred.

Next gate: `P12.5-RCV-14 HISTORICAL MANAGED TYPE SELECTION CONFIRMATION`.
