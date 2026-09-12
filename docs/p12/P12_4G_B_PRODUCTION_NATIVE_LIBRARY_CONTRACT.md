# P12.4G-B - Production Native Library Contract

Profile: `apexforge.win-x64-production-native-library/v1`

The production native library identity is `apexforge_native.dll` for Windows x64, PE32+, AMD64. The managed logical library identity remains `apexforge_native`.

The production link recipe uses MSVC LINK with `/DLL`, `/NOENTRY`, `/NODEFAULTLIB`, and `/MACHINE:X64`. The versioned module-definition file `runtimes/native/link/apexforge_native.def` is the authoritative production export list.

The public export surface contains exactly `apexforge_release_handle` and `apexforge_release_buffer`. Export ordinals are not part of the ABI contract. Internal lifecycle registration and implementation symbols must not be exported.

The v1 library has zero imported DLL dependencies and no CRT dependency. Public creation exports, callbacks, reverse P/Invoke, generic FFI, and allocator selection remain outside this gate.

`apexforge_native.dll`, its import library, `.exp`, object files, and other compiled binary products are generated artifacts and are not source-controlled. The build/release pipeline is responsible for producing release binaries from the versioned sources and link contract.

DLL-level reproducibility is not presumed by this contract. It is explicitly deferred to P12.4G-C. The existing P12.4D COFF object reproducibility policy remains intact.

Canonical language semantics remain upstream in AIR; the native library does not become a semantic authority.
