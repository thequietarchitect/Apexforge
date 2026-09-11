# P12.4D - COFF Reproducibility and Provenance Policy

## Identity rule

ApexForge distinguishes portable machine-code identity from build-container identity. For the selected Windows x64 MSVC COFF profile, executable code sections are portable identity evidence; the SHA-256 of an entire object file is recorded as build-instance evidence and is not required to remain identical across arbitrary build directories.

## Same-invocation requirement

When source, compiler, flags, environment, and output path are identical, `/Brepro` object output must remain byte-identical. P12.4C-R1 established this property.

## Cross-directory requirement

Across different output directories, executable `.text*` sections must remain byte-identical. The `.drectve` section is also required to remain stable. Variance in `.debug$S` and `.chks64` is permitted because P12.4D-R1 localized the observed container variance to those metadata sections while `.text$mn` remained identical. Any executable-section variance is a failure; any new non-allowlisted section variance requires review.

## Provenance

Native object provenance records the source hash, ABI-header hash, toolchain profile, compiler family and version, Windows SDK version, target, object format, machine, compiler flags, ordered executable-section hashes, and whole-object hash. Build-directory paths and debug metadata do not define ApexForge semantic identity.

## Scope

This policy does not link a native artifact, produce a DLL, implement the lifecycle exports, select a build system, or transfer semantic ownership away from canonical AIR.
