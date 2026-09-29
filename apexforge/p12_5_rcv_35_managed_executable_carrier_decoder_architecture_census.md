# P12.5-RCV-35 Recovered Managed Executable Carrier Decoder Architecture Census

RCV-35 is audit-only.

RCV-34 authorized 18 closed-world structural mappings from canonical AIR transport into the managed executable carrier, but deliberately left decoder identity and JSON parsing policy unselected.

Historical evidence recovers only one managed JSON deserialization surface: `CanonicalExecutionEnvelope.FromJson`, implemented with `System.Text.Json.JsonSerializer.Deserialize`. That surface belongs to the canonical execution envelope and does not establish a decoder architecture for `ManagedExecutableCarrier`.

No historical managed-carrier decoder has been recovered.

## Candidate architectures inventoried

- `JsonDocument` / `JsonElement` with explicit closed-world dispatch.
- `Utf8JsonReader` with explicit closed-world dispatch.
- direct `JsonSerializer.Deserialize` with an explicitly governed polymorphic configuration.
- another explicit custom/generated decoder, if later evidence or governance selects one.

This census does not choose among them.

The gate also leaves unresolved JSON-number handling, integer parsing, binary64 parsing, special-float transport behavior, discriminator shape, unknown-property handling, and duplicate-property handling.

No runtime crossing, external serialization, cross-runtime transport, or execution dispatch is authorized.

Next gate: `P12.5-RCV-36 MANAGED EXECUTABLE CARRIER DECODER ARCHITECTURE DECISION`.
