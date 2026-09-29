# P12.5-RCV-32 Recovered Managed Executable Carrier Derivation Source Decision

RCV-32 selects the logical source representation for future managed executable-carrier derivation.

## Decision

`DERIVATION_SOURCE = CANONICAL_AIR_TRANSPORT`

The selected direction is:

`Canonical AIR transport -> ManagedExecutableCarrier`

The semantic authority remains `air.model.VerifiedAIRProgram`, with canonical serialization delegated to `air.serialization.air_to_dict`. The already-existing `VerifiedAIRLoweringInput.transport_json` is the current canonical transport container.

This decision does **not** authorize a Python-to-.NET runtime crossing, external serialization, a JSON decoder, or execution dispatch. Those remain separate gates.

## Why the other candidates are not selected

- The direct Python `VerifiedAIRProgram` object graph cannot be the cross-runtime source without selecting a Python/.NET object transport.
- `TargetNeutralLoweringProduct` embeds the canonical AIR transport, but adds routing/product metadata that is not the carrier's semantic source.
- `TargetNeutralLoweringHandoff` carries only schema/fingerprint/routing/entry-owner identity and does not contain the executable expression/function graph required to construct the carrier.

The historical P12.5E-E compatibility census established that the verified AIR transport remained deterministic and preserved through lowering, while P12.5E-E-Q recorded no existing derivation bridge. This is therefore a recovery governance decision, not a historical identity claim.

Implementation remains deferred.

Next gate: `P12.5-RCV-33 MANAGED EXECUTABLE CARRIER DERIVATION MAPPING CENSUS`.
