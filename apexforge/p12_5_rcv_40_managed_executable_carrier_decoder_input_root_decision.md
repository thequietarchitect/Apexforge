# P12.5-RCV-40 Managed Executable Carrier Decoder Input Root Decision

The decoder accepts the whole canonical AIR document carried by `VerifiedAIRLoweringInput.transport_json` and projects only `$.functions` into managed executable carrier objects.

This is the sole existing canonical seam. A functions-only array or individual-function object would create a new transport contract and is not authorized.

The decoder validates the exact root property set and root JSON kinds. The historical omission of empty `workflows` is accepted; when present, `workflows` must be an array. Unrelated metadata is not semantically decoded because canonical AIR remains authoritative.

An empty functions array yields an empty list. Multiple functions are all decoded in source order. The decoder performs no function selection, execution, or dispatch.

External transport, runtime crossing, target-neutral handoff coupling, and execution dispatch remain deferred.

Next gate: `P12.5-RCV-41 MANAGED EXECUTABLE CARRIER DECODER PUBLIC API CONTRACT`.
