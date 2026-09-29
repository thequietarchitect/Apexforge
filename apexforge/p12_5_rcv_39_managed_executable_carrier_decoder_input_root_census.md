# P12.5-RCV-39 Recovered Managed Executable Carrier Decoder Input Root Census

RCV-39 is audit-only.

The canonical P12 lowering seam serializes:

`air_to_dict(verified.program)`

into:

`VerifiedAIRLoweringInput.transport_json`

Therefore the existing canonical JSON root is the whole `AIRProgram` object, not a functions-only payload.

The live census verifies three distinct root topologies:

1. `AIRProgram` has 12 dataclass fields, ending in `functions` and `workflows`.
2. `air_to_dict(AIRProgram)` intentionally omits `workflows` when it is empty, preserving the historical 11-key document shape. A non-empty workflow is serialized as the twelfth field.
3. `VerifiedAIRLoweringInput.transport_json` uses `sort_keys=True`, so its JSON object keys are alphabetically ordered. The empty transport has 11 keys; the non-empty-workflow transport has 12.

The managed-carrier-relevant subtree is:

`$.functions`

Each item in that array is an `AIRFunction` structural object corresponding to `ManagedExecutableFunction`.

RCV-39 inventories three candidate decoder roots:

1. the whole canonical AIR document,
2. the `functions` array subtree,
3. an individual function object.

Only the first already has an existing canonical transport seam. The latter two would require new extraction/subtree contracts.

No root is selected here. Decoder method shape, metadata validation scope, empty/multiple function handling, implementation, runtime crossing, and execution dispatch remain deferred.

Next gate: `P12.5-RCV-40 MANAGED EXECUTABLE CARRIER DECODER INPUT ROOT DECISION`.

## R2 repair

The R1 fixture equated dataclass topology with canonical serialized transport topology. It therefore expected an empty transport to contain all 12 dataclass fields in declaration order.

Production evidence establishes intentional compatibility behavior: empty workflows are omitted so historical AIR documents retain their pre-workflow shape, while non-empty workflows are serialized. The lowering seam independently canonicalizes JSON key order.

The failure is `TEST_FIXTURE_DEFECT`, not fixture drift or a semantic regression. The carrier-relevant subtree remains `$.functions`, and no decoder input root is selected by this census.
