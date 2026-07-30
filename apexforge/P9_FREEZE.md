AFP-P9 — Generics Freeze Candidate

Status: FREEZE CANDIDATECompletion gate: p9_final_integration_smoke_test.py plus the complete P7–P9 regression suite.

Frozen slices

P9.1 Generic Declarations

P9.2 Call-Site Inference and Substitution

P9.3 Explicit Type Arguments

P9.4 Generic Constraints

P9.5 Specialization Records

P9.6 Linked Specialization Closure

P9.7 Deterministic Generic Lowering

P9.8 Final Integration and Freeze

Frozen semantic guarantees

Function-scoped generic type identities

Inferred and explicit type arguments

Exact repeated-variable unification

No implicit numeric conversion

Enforceable numeric constraints

Canonical specialization records

Deterministic linked specialization closure

Stable concrete specialization identities

Runtime-erased generic execution

Preservation of source generic declarations

Closed executable AIR after lowering

Input-order-independent specialization output

Change control after freeze

After the P9.8 completion smoke and full regression suite pass, P9 changes are limited to confirmed defect repairs, regression-preserving refactors, later-phase integration work, or explicitly versioned language changes.