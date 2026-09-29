# P12.5-RCV-16 Recovered Target-Neutral Handoff Projection Bridge Census

RCV-16 is audit-only.

It verifies that the recovered six-field managed `TargetNeutralLoweringHandoff` can be deterministically projected from the canonical P12.2 `TargetNeutralLoweringProduct` without transferring semantic authority.

Historical projection:

- `Schema` <- `product.schema`
- `VerifiedAirFingerprint` <- `product.verified_air_fingerprint`
- `RoutingFingerprint` <- `product.routing_fingerprint`
- `EntryDirective` <- `product.entry_directive`
- `DirectiveOwnerIds` <- `product.directive_owner_ids`
- `ProductFingerprint` <- `product.product_fingerprint`

`canonical_json`, the Python `binding` object, the execution-plan object, and the verified-AIR object are not projected as managed handoff fields.

No bridge implementation or bridge owner is selected at this gate.

Canonical AIR remains the language-semantic authority, and execution dispatch remains deferred.

Next gate: `P12.5-RCV-17 PROJECTION BRIDGE OWNERSHIP CONTRACT`.
