# P12.3C - Windows x64 Managed/Native ABI and Memory-Ownership Contract

## Profile

`apexforge.win-x64-managed-native-abi/v1` is the first concrete ApexForge managed/native ABI profile. It is scoped to Windows x64 and is not a universal ABI.

## Architecture boundary

Canonical ApexForge language semantics remain upstream. The native backend owns this native ABI profile; the C#/.NET runtime remains a sibling execution target. Neither Visual Studio nor the native backend becomes a language-semantic owner.

## Calling convention

The profile uses the Windows x64 platform ABI through a C-compatible flat boundary. C++ name mangling, C++ object types, exceptions, and cross-boundary stack unwinding are forbidden.

## Value boundary

The v1 boundary permits fixed-width I32, I64, U32, U64, and U8 scalars. Boolean values cross as U8 values 0 or 1. Text crosses as UTF-8 bytes with an explicit U64 length; NUL termination is not required. By-value structs are forbidden in v1. Native handles are opaque pointer-sized values and may not be dereferenced by managed code.

## Memory ownership

Input buffers are caller-owned and borrowed only for the duration of a call; native code may not retain them. Output buffers are native-owned until explicitly released through a matching native release operation. Cross-runtime free is forbidden. Managed GC pointers may not be retained by native code. Opaque handles must be released through the runtime that created them. SafeHandle integration is deferred to P12.3D.

## Error boundary

ABI operations report I32 status codes with zero representing success. Exceptions may not cross the boundary. Diagnostics use UTF-8 pointer-plus-length data whose ownership follows the native-release rule.

## Deferred concerns

The exact .NET binding/loading mechanism, callbacks, reverse P/Invoke, compiler selection, object format, linker, machine-code emission, generic FFI, and PolyPlane remain deferred. P12.3D may implement the managed binding only after this contract is committed.
