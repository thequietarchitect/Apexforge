# P12.4F-D - Controlled Lifecycle Behavior Execution

P12.4F-D executes the committed lifecycle export and lifecycle-core objects through a test-only AMD64 PE32+ executable.

The probe verifies null and unknown-resource rejection, wrong-kind rejection without consumption, buffer-length mismatch rejection without consumption, valid handle and buffer release, double-release rejection, exactly one disposer invocation per successful release, and released-slot reuse.

The executable is linked with NODEFAULTLIB and imports only the operating-system ExitProcess dependency needed to report the test result. It is temporary acceptance evidence and is not the production ApexForge native runtime host or apexforge_native DLL.

The frozen public ABI remains unchanged. Public creation exports are not introduced. The internal registration seams remain non-public implementation/test seams.

No allocator family is selected. Dynamic allocation remains absent. Thread safety remains deferred. Canonical language semantics remain owned by upstream AIR.
