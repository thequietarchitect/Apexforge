# P12.5-RCV-34 Recovered Managed Executable Carrier Derivation Mapping Contract

RCV-34 authorizes the 18 structural mappings identified by RCV-33.

The contract remains strictly structural. Canonical AIR remains the semantic authority.

Authorized coverage:

- 8 executable-expression mappings,
- 5 function/control-flow mappings,
- 3 type mappings,
- 2 constraint mappings.

Seven managed declarations remain topology-only base/interface surfaces and are not independently decoded source nodes.

## Normalization rules

- snake_case canonical fields may map to structurally corresponding PascalCase managed properties,
- Python tuples may become `IReadOnlyList<T>` while preserving order,
- optional source values may become nullable managed reference/interface values,
- Python integers map exactly to `System.Numerics.BigInteger`,
- AIR floating-point values map to managed `double` / binary64,
- string content and boolean values are preserved.

## Closed-world rule

Unknown expression, statement, generic-type, or constraint variants must be rejected. Silent defaults, semantic coercion, and reinterpretation are forbidden.

RCV-34 does not select a decoder implementation, JSON number policy, special-float transport policy, runtime crossing, handoff coupling, or execution dispatch.

Next gate: `P12.5-RCV-35 MANAGED EXECUTABLE CARRIER DECODER ARCHITECTURE CENSUS`.
