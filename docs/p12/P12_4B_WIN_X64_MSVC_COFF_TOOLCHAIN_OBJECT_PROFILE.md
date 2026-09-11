# P12.4B - Windows x64 MSVC COFF Toolchain and Object Profile

## Selection

P12.4B selects the first concrete ApexForge native artifact toolchain profile: Windows x64, MSVC `cl.exe`, x64 COFF `.obj` files, and the MSVC `link.exe` linker targeting PE32+ images.

## Evidence

The selection is based on an installed x64 MSVC toolset and Windows SDK discovered through supported installation metadata. Absolute installation paths are environment evidence and are not part of the portable profile identity.

## Semantic boundary

The selected toolchain is an implementation mechanism only. Canonical ApexForge language semantics remain owned by upstream canonical AIR. The native backend and managed runtime remain sibling execution targets.

## Still deferred

P12.4B does not emit an object, compile ApexForge native implementation code, link a DLL or executable, choose a build system, choose a generated source-language strategy, introduce LLVM, or define compiler-specific export decoration. Those operations require later P12.4 gates.
