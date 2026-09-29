# P12.5-RCV-36 Recovered Managed Executable Carrier Decoder Architecture Decision

RCV-36 selects the managed decoder architecture while leaving parsing policy and implementation deferred.

## Selected architecture

`SYSTEM_TEXT_JSON_DOM`

Future decoder type:

`ApexForge.Runtime.ManagedExecutableCarrierDecoder`

The selected mechanism is manual closed-world traversal using `System.Text.Json.JsonDocument` / `JsonElement`.

This architecture is selected because it:

- keeps dispatch explicit and closed-world,
- supports exact access to raw numeric token text before numeric conversion,
- supports recursive construction of the authorized 18 carrier mappings,
- rejects unknown node kinds explicitly,
- avoids implicit polymorphic `JsonSerializer` binding,
- adds no external JSON dependency.

The decision does **not** authorize a decoder implementation yet.

Before implementation, the recovery line must census the exact canonical AIR JSON emitted by `air.serialization.air_to_dict`, including node discriminator keys, field names, null/optional representation, collection shape, numeric tokens, and any special-float behavior.

Runtime crossing, external serialization, target-neutral handoff coupling, and execution dispatch remain deferred.

Next gate: `P12.5-RCV-37 CANONICAL AIR TRANSPORT JSON SHAPE CENSUS`.
