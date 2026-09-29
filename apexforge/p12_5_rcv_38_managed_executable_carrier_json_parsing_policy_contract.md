# P12.5-RCV-38 Recovered Managed Executable Carrier JSON Parsing Policy Contract

RCV-38 freezes the parsing rules required by the RCV-36 DOM decoder architecture and the live RCV-37 transport findings.

## Structural dispatch

Canonical AIR transport does not carry class/type discriminators. The decoder therefore uses a closed-world rule:

`exact property set + JSON value kind`

Unknown properties, missing required properties, duplicate properties, unknown shapes, and silent default injection are rejected.

Property names are matched exactly as canonical snake_case. Collection ordering is preserved.

## Numeric policy

Objects with the exact shape `{"value": ...}` are disambiguated by JSON value kind and number grammar:

- string -> `AIRStringLiteral`
- boolean -> `AIRBooleanLiteral`
- number without `.` / `e` / `E` -> `AIRIntegerLiteral`
- number with `.` / `e` / `E` -> `AIRFloatLiteral`

Integer raw text is parsed exactly into `System.Numerics.BigInteger`.

Finite floating-point raw text is parsed invariantly into `System.Double` / binary64. `-0.0` must preserve its sign bit.

## Non-finite floats

RCV-37 proved the Python transport encoder can emit bare `NaN`, `Infinity`, and `-Infinity`. Those are not strict JSON accepted by the selected `JsonDocument` input.

RCV-38 therefore fails closed on those transport forms. This does **not** remove non-finite values from the managed carrier model; it records a transport incompatibility that requires a separate normalization decision before such values can cross this JSON boundary.

## Canonical type normalization

Canonical AIR normalizes string type/constraint spellings before serialization. The initial decoder therefore treats `ApexType` and `ApexTypeConstraint` object shapes as the primary transported forms; the managed named type/constraint variants are not constructed from this canonical transport path.

Decoder method shape, root extraction, implementation, runtime crossing, and execution dispatch remain deferred.

Next gate: `P12.5-RCV-39 MANAGED EXECUTABLE CARRIER DECODER INPUT ROOT CENSUS`.
