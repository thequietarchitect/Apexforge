# P12.5-RCV-18 Recovered Projection Bridge Representation Decision

RCV-18 selects a recovery representation for the source-side projection bridge.

Recovered evidence does not establish a concrete historical projection object, serializer, or cross-runtime transport. Therefore this gate does **not** claim historical identity equivalence.

## Decision

The source-side bridge representation is an internal immutable Python value object:

`apexforge.native_backend.managed_handoff_projection.ManagedHandoffProjection`

Representation kind:

`FROZEN_DATACLASS_VALUE_OBJECT`

Fields:

- `schema: str` -> managed `Schema`
- `verified_air_fingerprint: str` -> managed `VerifiedAirFingerprint`
- `routing_fingerprint: str` -> managed `RoutingFingerprint`
- `entry_directive: str` -> managed `EntryDirective`
- `directive_owner_ids: tuple[str, ...]` -> managed `DirectiveOwnerIds`
- `product_fingerprint: str` -> managed `ProductFingerprint`

Construction will be a direct copy from `TargetNeutralLoweringProduct` and its existing derived views. `canonical_json` and the binding object do not enter the projection value object.

The projection object performs no independent semantic reinterpretation and gains no execution or transport authority. Managed handoff validation remains owned by `ApexForge.Runtime`.

External serialization, cross-runtime transport, file/stdin/CLI formats, executable carriers, and execution dispatch remain unselected or deferred.

Next gate: `P12.5-RCV-19 PROJECTION VALUE-OBJECT IMPLEMENTATION FOUNDATION`.
