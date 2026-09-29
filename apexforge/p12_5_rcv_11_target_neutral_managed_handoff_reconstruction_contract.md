# P12.5-RCV-11 Recovered Target-Neutral Managed Handoff Reconstruction Contract

RCV-11 restores the governance boundary for the managed target-neutral handoff without yet restoring its concrete field representation.

## Reconstructed boundary

- Subject: `TARGET_NEUTRAL_LOWERING_PRODUCT`
- Managed type: `ApexForge.Runtime.TargetNeutralLoweringHandoff`
- Source schema: `apexforge.target-neutral-lowering/v1`
- Owner project: `ApexForge.Runtime`
- Admission surface: `ManagedRuntimeHost.AdmitTargetNeutralHandoff(...)`
- Admission behavior: `VALIDATE_AND_RETURN`

The handoff is a managed boundary object. It is not a new language-semantic authority, execution engine, lowering engine, serializer, or native ABI owner.

Canonical AIR remains the language-semantic authority. The P12.2 target-neutral lowering schema remains canonical for this boundary.

## Still unselected

The handoff's exact field mapping, external serialization, file format, stdin format, and command-line format remain unselected. Managed executable carrier behavior and managed/native execution dispatch remain deferred.

## Next gate

`P12.5-RCV-12 TARGET-NEUTRAL HANDOFF REPRESENTATION CENSUS`
