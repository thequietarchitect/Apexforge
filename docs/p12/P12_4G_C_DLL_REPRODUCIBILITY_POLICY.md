# P12.4G-C - Production Native Library Reproducibility Policy

Profile: `apexforge.win-x64-production-native-library-reproducibility/v1`

This policy resolves the reproducibility deferral established by P12.4G-B for the Windows x64 production native library `apexforge_native.dll`.

The governed build requires `/Brepro` at both object compilation and DLL link time. The DLL link remains `/DLL /NOENTRY /NODEFAULTLIB /MACHINE:X64` and uses `runtimes/native/link/apexforge_native.def` as the authoritative two-symbol export list.

For an unchanged source set, module-definition file, governed flags, and toolchain identity, both repeated same-path builds and builds produced in different build directories must be byte-identical. The release artifact identity is the SHA-256 of the complete DLL.

No PE section is exempted from DLL identity. In particular, `.rdata` and the PE header timestamp are not ignored. The baseline non-`/Brepro` experiment showed variance in `.rdata` and the timestamp; the `/Brepro` characterization eliminated both while preserving the exact export and dependency surface.

P12.4G-C-R1 observed the same whole-DLL SHA-256 in all four builds: `ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8`, with zero same-path and zero cross-directory section variance. That hash is characterization evidence for the current inputs, not a permanent ABI constant.

A toolchain-profile change requires reproducibility recharacterization. A source or governed link-contract change is expected to produce a new artifact identity and is not itself a reproducibility failure.

Compiled DLLs remain generated release artifacts and are not committed to Git. Canonical language semantics remain upstream in AIR.
