# P12.0D - C# / .NET Managed Runtime Ownership Boundary

## Identity

`ApexForge.Runtime` is a first-class C#/.NET execution target. It is not the Visual Studio extension and it is not a second definition of the ApexForge language.

## Planned project

```text
runtimes/dotnet/ApexForge.Runtime/
    ApexForge.Runtime.csproj
```

The Visual Studio project remains independently located at `editors/visualstudio-apexforge/src/ApexForge.VisualStudio/ApexForge.VisualStudio.csproj`.

## Canonical input boundary

The managed runtime consumes verified canonical execution products. The current ownership anchors are `air.model.VerifiedAIRProgram` and `workflow.air_runner.RegistryExecutionPlan`. Source parsing, resolution, identity, authority, and workflow meaning remain upstream canonical concerns.

## Managed-runtime ownership

The runtime owns managed hosting and lifecycle, managed value representation, execution dispatch, execution context and call-stack behavior, diagnostic translation, managed artifact loading, and runtime services needed to execute canonical ApexForge behavior.

## Explicit exclusions

The managed runtime does not own grammar, parsing, source resolution, authority semantics, identity semantics, canonical AIR semantics, Visual Studio editor behavior, native ABI, object emission, linking, or PolyPlane.

## Runtime relationships

The Python runtime remains the independent reference/conformance runtime and is not silently replaced. The native backend is a sibling target. The managed runtime must not depend on the Visual Studio extension. A future editor may call into managed runtime services, but editor code may not become runtime semantic ownership.

## Interoperability

Generic FFI is not introduced here. Managed/native bridging requires a later concrete P12 interoperability contract.

## Freeze rule

No `ApexForge.Runtime` production project should be created until this ownership boundary is frozen.
