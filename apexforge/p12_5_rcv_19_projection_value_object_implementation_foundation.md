# P12.5-RCV-19 Recovered Projection Value-Object Implementation Foundation

RCV-19 implements the recovery-selected source-side projection representation authorized by RCV-18.

The implementation adds:

`apexforge.native_backend.managed_handoff_projection.ManagedHandoffProjection`

as a frozen Python dataclass, plus:

`project_managed_handoff(product)`

which accepts only `TargetNeutralLoweringProduct` and directly copies the six values required by the recovered managed handoff boundary.

No semantic interpretation is performed. `canonical_json`, the binding object, the execution-plan object, and the verified-AIR object are not projected into the value object.

This is a recovery-selected implementation and does not claim identity with a lost historical bridge implementation.

External serialization, cross-runtime transport, file/stdin/CLI formats, executable carriers, and execution dispatch remain unselected or deferred.

Next gate: `P12.5-RCV-20 PROJECTION VALUE-OBJECT COMPATIBILITY CENSUS`.
