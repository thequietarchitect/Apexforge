# P12.5-RCV-31 Recovered Managed Executable Carrier Derivation Boundary Census

RCV-31 is audit-only.

The historical P12.5E-E-Q census passed and recorded:

- 139 canonical derivation-source references,
- 26 managed-runtime references,
- 0 production-Python references to the managed carrier,
- 0 existing derivation-bridge references,
- 22 references to the already-existing target-neutral handoff boundary,
- full predecessor regression-stack PASS,
- repository unchanged.

That evidence establishes a crucial separation: canonical AIR and the target-neutral handoff existed, and the managed carrier existed, but there was no recovered production bridge deriving one into the other at that point.

RCV-31 therefore verifies the current recovery tree preserves the same boundary:

- `ManagedExecutableCarrier.cs` exists and builds through RCV-30.
- canonical AIR expression/function surfaces remain present.
- production Python does not refer to managed carrier types.
- managed runtime/host files outside `ManagedExecutableCarrier.cs` do not derive or construct carrier nodes.
- `TargetNeutralLoweringHandoff` remains separate from the carrier.
- no derivation source, owner, direction, transport, serialization, or execution dispatch is selected.

Candidate derivation sources are inventoried but not chosen:

1. verified AIR object graph,
2. canonical AIR transport,
3. target-neutral lowering product,
4. target-neutral managed handoff.

Structural similarity is not sufficient to select one.

Next gate: `P12.5-RCV-32 MANAGED EXECUTABLE CARRIER DERIVATION SOURCE DECISION`.
