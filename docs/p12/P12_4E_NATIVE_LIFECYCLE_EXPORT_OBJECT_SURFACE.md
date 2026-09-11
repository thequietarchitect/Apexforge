# P12.4E - Native Lifecycle Export Object Surface

## Purpose

P12.4E moves the two P12.3 lifecycle entrypoints from declaration-only ABI surface into real AMD64 COFF object symbols without yet linking a DLL or implementing allocator ownership behavior.

## Public object surface

The object defines `apexforge_release_handle` and `apexforge_release_buffer`. Each public entrypoint is a forwarding boundary only.

## Deferred lifecycle core

The public functions forward to unresolved internal dependencies `apexforge_internal_release_handle` and `apexforge_internal_release_buffer`. P12.4E deliberately does not invent allocation, deallocation, handle validation, resource registries, or successful-release behavior. The lifecycle core remains deferred to P12.4F.

## Reproducibility

The object must be byte-identical for an identical same-path `/Brepro` invocation. Across build directories, executable section identity must remain stable under the P12.4D provenance policy. Whole-object cross-directory identity is not required.

## Scope

No native link, DLL production, creation exports, callbacks, reverse P/Invoke, generic FFI, build-system selection, or semantic ownership is introduced.
