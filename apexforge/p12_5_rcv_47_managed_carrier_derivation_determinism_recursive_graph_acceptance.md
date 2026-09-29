# P12.5-RCV-47 Managed Carrier Derivation Determinism and Recursive Graph Acceptance

Repeated construction of the same verified AIR fixture produces identical canonical transport bytes and the same existing transport fingerprint. Repeated managed decoding produces structurally identical recursive carrier graphs with every collection order preserved.

A test-only structural summary is hashed to make the managed comparison exact. It is not a production serializer or a new carrier fingerprint contract. `VerifiedAIRLoweringInput.transport_fingerprint` remains the canonical transport fingerprint owner.

Recursive, empty, and multiple-function graphs pass. Malformed graphs remain rejected by RCV-45.

Next gate: `P12.5-RCV-48 MANAGED CARRIER INTEGRATION SCOPE DECISION`.
