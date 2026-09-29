# P12.5-RCV-49 Managed Carrier Representational Equivalence Acceptance

The managed projection preserves every carrier-relevant canonical representation: arbitrary-precision integers, finite binary64 values and negative zero, Unicode strings, booleans, functions, recursive control-flow shape, generic types and constraints, null optionals, collection order, and deterministic construction.

Malformed and non-finite transport inputs fail closed.

P12.5 does not contain an authorized carrier executor. This gate therefore does not manufacture a managed/native execution-equivalence claim. The frozen cross-target canonical execution-result contract remains covered by its existing P12.1 regression; the new decoder neither replaces nor widens it.

Canonical AIR remains the sole language semantic authority.

Next gate: `P12.5-RCV-50 P12.5 RECOVERY CLOSURE AUDIT`.
