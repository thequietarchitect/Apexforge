# P12.4G-D - Managed-to-Production Native DLL Binding Execution

Profile: `apexforge.win-x64-managed-production-native-binding-execution/v1`

P12.4G-D-B executed the committed `net10.0` managed runtime against a production-shaped deterministic `apexforge_native.dll` through the runtime's actual `LibraryImport` declarations.

The managed binding remains `ApexForge.Runtime.ManagedNativeAbi`, an internal static partial class whose logical library name is `apexforge_native`. Its entry points remain exactly `apexforge_release_handle` and `apexforge_release_buffer`. The temporary external probe used reflection only to reach those internal generated stubs; reflection did not replace or emulate the native binding.

The invoked native DLL matched the governed whole-file SHA-256 `ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8`, exported exactly the two lifecycle release functions, and imported zero DLL dependencies.

Execution proved four rejection paths through the real managed/native boundary: null handle, null buffer, unknown handle, and unknown buffer. All returned nonzero failure. The observed private implementation values were 1 for null and 2 for unknown, but those numeric values are characterization evidence only and are not added to the public ABI contract. The public v1 contract remains zero for success and nonzero opaque failure.

A successful release of a valid live native resource is not claimed by this gate. Public creation exports remain deferred and allocator family remains `UNSELECTED`, so this stage does not fabricate a public test-only creation API.

No custom DLL resolver was required. The test placed `apexforge_native.dll` beside the temporary managed host output and allowed normal `LibraryImport` resolution. No production DLL, managed probe, runtime host, or execution artifact is committed to Git.

Canonical language semantics remain upstream in AIR; successful native loading does not make the native backend a semantic authority.
