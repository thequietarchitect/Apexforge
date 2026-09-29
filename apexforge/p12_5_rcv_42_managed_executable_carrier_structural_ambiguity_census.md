# P12.5-RCV-42 Managed Executable Carrier Structural Ambiguity Census

All canonical carrier shapes are resolvable without heuristic guessing.

The only same-property literal collision is `{ "value": ... }`. JSON value kind selects string and boolean literals; numeric token grammar selects integer versus float. The raw number contains a decimal point or exponent only for the float branch.

Other apparent similarities are separated by the expected semantic context and exact property sets. Canonical AIR normalization means generic type and constraint aliases do not survive as loose string-wrapper objects.

There are zero unresolved collisions. Unknown, duplicate, extra, missing, null-invalid, and kind-invalid structures must fail closed.

Next gate: `P12.5-RCV-43 MANAGED EXECUTABLE CARRIER DECODER IMPLEMENTATION`.
