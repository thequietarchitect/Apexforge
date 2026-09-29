# P12.5-RCV-46 Canonical AIR Transport to Managed Carrier Derivation Bridge Acceptance

`ManagedExecutableCarrierDecoder.DecodeCanonicalAirTransport` is the construction bridge selected but not yet implemented at RCV-32. A second bridge component is unnecessary.

The logical source remains `VerifiedAIRProgram`; the concrete source container is `VerifiedAIRLoweringInput.transport_json`, produced through `air_to_dict`. Upstream lowering rejects a raw `AIRProgram`, preserving verification ownership.

The bridge projects structure only. It does not mutate the source, serialize the managed graph, create a competing fingerprint, select transport, execute, or couple the executable graph to the target-neutral handoff.

Next gate: `P12.5-RCV-47 MANAGED CARRIER DERIVATION DETERMINISM AND RECURSIVE GRAPH ACCEPTANCE`.
