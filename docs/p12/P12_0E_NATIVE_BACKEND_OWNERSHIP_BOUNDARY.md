# P12.0E - Native Backend Ownership Boundary

## Identity

The ApexForge native backend is a first-class execution target and a sibling of the C#/.NET managed runtime. It is not a second definition of the ApexForge language.

## Planned package

```text
apexforge/native_backend/
```

## Canonical input

The backend consumes verified canonical ApexForge products. `air.model.VerifiedAIRProgram` remains an upstream canonical owner. The backend does not acquire source parsing, resolution, authority, identity, workflow, or AIR-semantic ownership.

## Backend ownership

The native backend owns target selection, native lowering, native layout and symbol mapping, object emission, link planning, native artifact construction, native diagnostics, provenance, and target metadata. ABI ownership becomes concrete only under a later explicit ABI contract.

## Sibling runtimes

The Python runtime remains the reference/conformance runtime. `ApexForge.Runtime` remains the C#/.NET managed execution target. Neither runtime owns the native backend and the native backend owns neither runtime.

## Toolchain neutrality

This boundary does not select LLVM, a compiler backend, object format, or linker. Those choices require later architecture and target evidence.

## Optimization boundary

The native backend does not acquire optimizer semantic ownership. Later optimized products may be consumed only under semantics-preserving contracts.

## Interoperability

Generic FFI is not introduced here. ABI and managed/native interoperability require concrete P12 contracts.

## Deferred scope

PolyPlane remains deferred. Visual Studio remains editor integration rather than backend ownership.

## Freeze rule

No native-backend production package should be created until this ownership boundary is frozen.
