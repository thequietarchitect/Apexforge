# P12.3E - Native Export and Resource-Lifecycle Contract

## Scope

This contract defines the native-side meaning of the two release entrypoints already consumed by the P12.3D managed boundary. It does not compile or load a native library.

## Export identity

The logical library is `apexforge_native`. The exact export symbols are `apexforge_release_handle` and `apexforge_release_buffer`. Export identity is C-compatible and unmangled; C++ name mangling is forbidden.

## Handle lifecycle

A live opaque handle is native-owned and non-dereferenceable by managed code. A successful `apexforge_release_handle` consumes exactly one live native handle. After success that handle is invalid and must not be reused. Managed zero handles are invalid and are not passed to release by SafeHandle.

## Buffer lifecycle

A native-owned output buffer is released only through `apexforge_release_buffer(pointer, length)`. The length must correspond to the buffer metadata held by the managed wrapper. A successful release consumes the live buffer and invalidates it.

## Status and failure

Both release operations return the P12.3C I32 status code with zero meaning success. For a valid live native resource, release must succeed. Nonzero status is reserved for invalid arguments or contract violations. Exceptions and stack unwinding may not cross the ABI boundary.

## Ownership invariant

Cross-runtime free is forbidden. Managed allocators may not release native-owned resources. Native code may not retain caller-borrowed managed inputs beyond the call duration.

## Deferred surface

Creation exports, retain/clone operations, callbacks, reverse P/Invoke, native compiler selection, header generation, DLL construction, object emission, and linking remain deferred.
