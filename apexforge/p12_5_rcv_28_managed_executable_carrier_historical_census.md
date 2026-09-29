# P12.5-RCV-28 Recovered Managed Executable Carrier Historical Census

RCV-28 is audit-only.

Historical evidence confirms that a later P12.5 snapshot contained:

`runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs`

with a 25-declaration managed executable/type/function graph. The intended carrier covered integer, binary64 floating-point, string, boolean, identifier, unary/binary/call expressions, type identities, generic types, constraints, function parameters, local bindings, returns, conditional statements, and executable functions.

The preserved R1 materialization is **not itself suitable for direct restoration**. It contains transcription defects:

- `IjeadOnlyList<ManagedGenericTypeLike>` where the historical smoke expected `IReadOnlyList<ManagedGenericTypeLike>`.
- `IjeadOnlyList<ManagedConstraintReference>` where the historical smoke expected `IReadOnlyList<ManagedConstraintReference>`.
- the smoke probe used `ManagedUnharyExpression` although the recovered carrier declaration is `ManagedUnaryExpression`.

That R1 diagnostic failed its carrier smoke and caused the managed-runtime regression build to fail. The historical diagnostic explicitly left the candidate bytes unchanged and classified the gate as `REVIEW_REQUIRED`.

Therefore RCV-28 records the intended carrier shape separately from defective intermediate bytes. It does not create `ManagedExecutableCarrier.cs`.

The carrier remains a representation surface only: no JSON serialization, target-neutral handoff coupling, native ABI ownership, execution, or dispatch is authorized here.

Next gate: `P12.5-RCV-29 MANAGED EXECUTABLE CARRIER CORRECTED TYPE-SHAPE CONTRACT`.
