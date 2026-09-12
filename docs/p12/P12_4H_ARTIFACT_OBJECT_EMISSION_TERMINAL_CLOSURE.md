# P12.4 - Artifact + Object Emission Terminal Closure

Profile: `apexforge.p12.artifact-object-emission-terminal-closure/v1`

P12.4 has satisfied its terminal readiness criteria and is ready for a dedicated closure commit and freeze tag.

The stage established the Windows x64 native artifact path from toolchain selection through controlled AMD64 COFF object emission, object reproducibility policy, lifecycle export object surface, lifecycle ownership behavior, deterministic production DLL linking, and actual .NET `LibraryImport` execution against the production-shaped native DLL.

The production native library remains `apexforge_native.dll`, targeting AMD64 PE32+. Its public export surface is exactly `apexforge_release_handle` and `apexforge_release_buffer`, and the characterized release-only library has zero imported DLL dependencies. Under the governed MSVC recipe, `/Brepro` is required at object compilation and DLL link time. Whole-file SHA-256 is the release artifact identity for unchanged governed inputs and toolchain identity. The observed characterization hash `ED1708825B13B6C23D1017A933EAAB1B681BD5D6D686C28525B9EC403B9A42A8` is evidence for the current inputs and toolchain, not a permanent ABI constant.

The committed `net10.0` managed runtime has loaded and invoked the production-shaped DLL through its actual `LibraryImport("apexforge_native")` bindings. Null and unknown-resource rejection paths are proven across the real managed/native boundary. Successful release of a valid live native resource remains deferred because public creation exports remain deferred; this closure does not fabricate a test-only public creation API.

Canonical language semantics remain upstream in AIR. The native backend is not a semantic authority. Generic FFI, callbacks, reverse P/Invoke, runtime hosting, allocator-family selection, and thread-safety guarantees are outside this stage and remain deferred where previously declared.

Generated `.dll`, `.obj`, `.lib`, and `.exp` artifacts remain build/release outputs and are not source-controlled. Source control contains the contracts, source, policies, and acceptance evidence necessary to reproduce and validate the stage.

Terminal freeze recommendation: create the dedicated P12.4 closure commit, tag it `afp-p12.4-freeze`, verify the tag peels to that closure commit, and publish only after local freeze verification succeeds.

Next stage after freeze: **P12.5 Runtime Hosts**.
