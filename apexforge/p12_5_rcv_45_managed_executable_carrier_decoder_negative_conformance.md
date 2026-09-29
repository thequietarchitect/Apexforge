# P12.5-RCV-45 Managed Executable Carrier Decoder Negative Conformance

The production decoder is exercised against malformed strict JSON, all three non-finite Python tokens, root violations, duplicate/unknown/missing/case-mismatched properties, null collections and items, unknown carrier shapes, invalid number grammars, and malformed generic and constraint graphs.

Every invalid document fails before a carrier list is returned. Null method input raises `ArgumentNullException`; all document-shape and token failures raise `FormatException`. Diagnostics are stable across repeated decoding and contain the structural path where the decoder can identify one.

No non-finite normalization was introduced. `NaN`, `Infinity`, and `-Infinity` remain fail-closed transport inputs.

## R1 fixture repair

The initial probe placed its helper record before C# top-level statements and failed compilation before reaching production. The helper declaration was moved after the top-level program.

The R1 probe then expected a generic-shape diagnostic for a forbidden string type alias. Production correctly rejects the value earlier at the required JSON-object kind boundary, so R2 aligns the expected diagnostic with that more precise failure point.

Both failures were `TEST_FIXTURE_DEFECT`; neither was a decoder or semantic failure.

Next gate: `P12.5-RCV-46 CANONICAL AIR TRANSPORT TO MANAGED CARRIER DERIVATION BRIDGE ACCEPTANCE`.
