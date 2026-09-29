# P12.5-RCV-17 Recovered Projection Bridge Ownership Contract

RCV-17 locks ownership without introducing a bridge implementation or transport format.

## Ownership split

- `apexforge.native_backend` owns the canonical `TargetNeutralLoweringProduct` and any source-side projection of that product into the historical six-field managed handoff boundary.
- `ApexForge.Runtime` owns `TargetNeutralLoweringHandoff`, its validation rules, and managed admission.
- `ApexForge.Runtime.ManagedRuntimeHost` owns validate-and-return admission.
- `ApexForge.Runtime.Host` remains only the orchestration/lifecycle shell.
- Canonical AIR remains the language-semantic authority.

## Boundary rule

Only these six values may cross the projection boundary:

- `Schema`
- `VerifiedAirFingerprint`
- `RoutingFingerprint`
- `EntryDirective`
- `DirectiveOwnerIds`
- `ProductFingerprint`

The Python `canonical_json`, `RegistryExecutionPlanBinding`, `RegistryExecutionPlan`, and `VerifiedAIRProgram` objects do not cross as managed handoff fields.

The source-side projection may copy canonical values but may not execute, lower, reinterpret, choose transport, or acquire semantic authority. The managed side may validate and admit, but may not reconstruct Python semantic objects from the handoff.

Projection representation, bridge implementation, external serialization, cross-runtime transport, executable carriers, and execution dispatch remain deferred.

Next gate: `P12.5-RCV-18 PROJECTION BRIDGE REPRESENTATION DECISION`.
