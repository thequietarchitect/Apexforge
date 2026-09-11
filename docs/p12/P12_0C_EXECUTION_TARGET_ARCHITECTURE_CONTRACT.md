# P12.0C - Execution Target Architecture Contract

## Canonical ownership

ApexForge has one canonical semantic model. Execution targets consume that model; they do not define competing language semantics.

## Execution architecture

```text
Canonical ApexForge Semantics / AIR
        |
        +-- Python Reference Runtime        [EXISTING]
        +-- C# / .NET Managed Runtime       [P12 PLANNED]
        +-- Native Backend                  [P12 ACTIVE DESIGN]
```

## Python reference runtime

The existing `apexforge/runtime` implementation remains the reference/conformance execution runtime. P12 does not replace it merely by introducing additional targets.

## C# / .NET managed runtime

The managed runtime is a first-class P12 execution target. It must be implemented separately from the Visual Studio extension. `editors/visualstudio-apexforge/src/ApexForge.VisualStudio` is IDE integration and is not the ApexForge managed runtime.

## Native backend

The native backend owns native lowering, ABI contracts, object emission, linking, and native executable/library production. It consumes canonical ApexForge semantics and may not redefine them.

## Target equivalence

Targets may differ in representation, runtime services, performance, deployment, and implementation strategy. They must not change identity, authority, resolution, workflow meaning, diagnostic contracts, or observable ApexForge language semantics.

## Deferred scope

PolyPlane remains deferred. Generic FFI is introduced only when a concrete P12 managed/native interoperability contract justifies it. Unified cross-target debugging remains P13 scope.
