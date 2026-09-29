# P12.5-RCV-37 Recovered Canonical AIR Transport JSON Shape Census — R1

RCV-37 R1 repairs the failed census fixture. The original failure was not a semantic regression: the fixture created a non-canonical constraint named `Numeric`, while ApexForge's canonical constraint is the exported `NUMERIC` object with source name `numeric`.

R1 also replaces the invented `Number` type fixture with canonical `INT`.

## Normalization finding

RCV-34 authorized 18 source-to-carrier structural mappings from the broader Python union topology. The live canonical AIR objects normalize two of those source forms before transport serialization:

- a `GenericTypeLike` string such as `"int"` normalizes to canonical `ApexType`,
- a `ConstraintLike` string such as `"numeric"` normalizes to canonical `ApexTypeConstraint`.

Therefore the canonical AIR transport exposes 16 concrete object shapes, while 2 union input forms are normalization aliases rather than independent transported node shapes.

## Serializer shape

`air.serialization.air_to_dict` remains dataclass-structural:

- no explicit node discriminator,
- Python class identity erased,
- snake_case field names,
- tuples/lists become JSON arrays,
- `None` becomes JSON null.

The live probe also checks exact arbitrary-precision integer token emission, negative zero, and Python JSON's non-finite float tokens (`NaN`, `Infinity`, `-Infinity`).

No decoder implementation, runtime crossing, transport selection, or execution dispatch is authorized.

Next gate: `P12.5-RCV-38 MANAGED EXECUTABLE CARRIER JSON PARSING POLICY CONTRACT`.
