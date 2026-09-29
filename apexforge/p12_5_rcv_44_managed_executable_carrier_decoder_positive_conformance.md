# P12.5-RCV-44 Managed Executable Carrier Decoder Positive Conformance

A live `VerifiedAIRProgram` fixture is serialized through `build_verified_air_lowering_input`, then decoded by the managed production decoder in a focused .NET probe.

The fixture covers all authorized expression and function-statement shapes, canonical types, generic variables and constraints, null optionals, exact large integers, binary64 negative zero, Unicode strings, booleans, recursive statements, a non-empty workflow root, and two functions whose order must be preserved. A separate empty program proves the empty-list behavior.

The test-only probe embedding is not a production transport. No ingress or execution capability is added.

Next gate: `P12.5-RCV-45 MANAGED EXECUTABLE CARRIER DECODER NEGATIVE CONFORMANCE`.
