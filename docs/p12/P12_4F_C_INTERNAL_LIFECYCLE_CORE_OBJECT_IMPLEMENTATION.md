# P12.4F-C - Internal Lifecycle Core Object Implementation

## Purpose

This slice implements the internal ownership/liveness registry beneath the P12.4E forwarding exports while preserving the frozen public ABI.

## Registry

The lifecycle core uses a fixed-capacity internal registry. No CRT, Windows heap, COM allocator, or other dynamic allocator family is selected. Caller-provided resource addresses are treated as opaque identities and are not dereferenced during validation.

## Validation

Release validates non-null identity, registry membership, liveness, resource kind, and registered buffer length before disposal. A failure leaves the registered live resource unconsumed.

## Successful consumption

After all validation succeeds, the registry slot is cleared and made reusable before its registered disposer callback is invoked. This prevents a reentrant second release from succeeding against the same live registration and avoids permanent exhaustion after 64 lifetime releases. The public success value remains zero; all private failures remain nonzero and opaque to public ABI v1.

## Allocator boundary

The registry stores an internal disposer callback supplied by the native producer/registration seam. This does not select an allocator family and does not expose callbacks through the public ABI.

## Scope

This slice compiles an AMD64 COFF object only. It does not link a native image, produce a DLL, add public creation exports, execute a runtime host, or transfer semantic authority away from canonical AIR.
