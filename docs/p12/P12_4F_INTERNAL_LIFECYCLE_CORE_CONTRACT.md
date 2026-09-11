# P12.4F - Internal Lifecycle Core Contract

## Purpose

P12.4F defines the internal ownership state machine required beneath the two public release entrypoints without changing the frozen public ABI.

## Public status compatibility

The public ABI remains I32 with zero representing success. P12.4F does not add public numeric error constants. Any nonzero result remains an opaque failure to public ABI v1.

## Lifecycle rules

A successful handle release consumes exactly one live native-owned handle. A successful buffer release consumes exactly one live native-owned buffer. Null, unknown, already-released, wrong-kind, or buffer-length-mismatched resources must fail without consuming another resource. Exactly one successful release is permitted for each live resource.

## Validation and safety

The implementation must validate native ownership and resource kind before disposal. Arbitrary caller pointers may not be dereferenced before ownership validation. Buffer length is part of the registered buffer identity. Cross-runtime free remains forbidden.

## Internal-only surface

The existing public functions continue forwarding to apexforge_internal_release_handle and apexforge_internal_release_buffer. An internal registration/disposer seam may be used to establish and consume live-resource state, but these helpers are not public ABI. Internal failure-code values remain private implementation details.

## Allocator boundary

No allocator family is selected by this contract. No public creation export is introduced. Allocator binding remains deferred so P12.4F does not silently choose CRT, process-heap, COM, or another allocation family.

## Scope

P12.4F-B does not link a DLL, execute a runtime host, add generic FFI, or transfer semantic authority away from canonical AIR.
