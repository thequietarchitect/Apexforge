# P12.5-RCV-43 Managed Executable Carrier Decoder Implementation

The managed runtime now contains `ManagedExecutableCarrierDecoder.cs`.

The decoder consumes a whole canonical AIR transport document through `JsonDocument`/`JsonElement`, validates the exact root and carrier-node structures, and constructs only the managed carrier nodes authorized by RCV-34.

Integer tokens are parsed directly into `BigInteger`. Float tokens are parsed invariantly into finite binary64 values, including negative zero. Non-finite Python transport tokens remain invalid strict JSON and fail closed.

No existing carrier semantics or project configuration changed. No host wiring, execution dispatch, target-neutral coupling, file/stdio/network protocol, or direct polymorphic serializer was added.

Next gate: `P12.5-RCV-44 MANAGED EXECUTABLE CARRIER DECODER POSITIVE CONFORMANCE`.
