# P12.5-RCV-30 Recovered Managed Executable Carrier Implementation Foundation

RCV-30 implements the corrected 25-declaration carrier graph authorized by RCV-29.

Production file:

`runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs`

The implementation preserves the recovered expression, type, constraint, statement, and function data graph while correcting only the documented R1 transcription defects.

Acceptance verifies:

- exact `BigInteger` storage,
- IEEE-754 binary64 special-value preservation,
- .NET string storage,
- the generic/type/identity graph,
- the function graph.

The carrier remains a representation surface only. It does not serialize, admit target-neutral handoffs, call native ABI, execute, or dispatch. Canonical AIR remains the language-semantic authority.

This is a recovery-corrected implementation and does not claim byte or commit identity with the lost historical implementation.

Next gate: `P12.5-RCV-31 MANAGED EXECUTABLE CARRIER DERIVATION BOUNDARY CENSUS`.
