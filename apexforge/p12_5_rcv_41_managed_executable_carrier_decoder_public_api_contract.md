# P12.5-RCV-41 Managed Executable Carrier Decoder Public API Contract

`ApexForge.Runtime.ManagedExecutableCarrierDecoder` is a stateless, closed-world structural decoder owned by the managed runtime library.

Its public method is:

`IReadOnlyList<ManagedExecutableFunction> DecodeCanonicalAirTransport(string canonicalAirTransportJson)`

The input is the complete internal canonical AIR transport JSON. Null input raises `ArgumentNullException`; malformed, unknown, ambiguous, duplicate, missing, or kind-invalid input raises `FormatException` with a deterministic path-qualified diagnostic.

The result preserves source function order and never executes or selects a function. This API does not authorize an external ingress or cross-runtime protocol.

Next gate: `P12.5-RCV-42 MANAGED EXECUTABLE CARRIER STRUCTURAL AMBIGUITY CENSUS`.
