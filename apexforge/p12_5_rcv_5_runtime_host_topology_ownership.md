# P12.5-RCV-5 Recovered Runtime Host Topology and Ownership Contract

This recovered governance artifact re-establishes the P12.5 managed runtime-host topology on the audited recovered lineage. It does not claim Git identity equivalence with the unavailable original P12.5 history.

## Existing Foundation

The existing `ApexForge.Runtime` project and `ApexForge.Runtime.ManagedRuntimeHost` type are preserved unchanged from the verified P12.4 base.

`ManagedRuntimeHost` remains the canonical contract admission and validation surface already established before P12.5. It does not define ApexForge language semantics.

## Dedicated P12.5 Host

P12.5 adds a distinct project at `runtimes/dotnet/ApexForge.Runtime.Host`.

The dedicated host is:

- Project: `ApexForge.Runtime.Host`
- Target framework: `net10.0`
- Output type: `Exe`
- Project reference: `../ApexForge.Runtime/ApexForge.Runtime.csproj`
- Role: orchestration and lifecycle shell
- Language semantic authority: none
- Native interop duplication: prohibited

The dedicated host is additive. It must not replace or repurpose the existing `ManagedRuntimeHost` library type.

## Authority

Canonical AIR remains the language-semantic authority.

`ApexForge.Runtime` owns the managed runtime library boundary. `ApexForge.Runtime.Host` owns only the executable host shell. Native ABI declarations remain owned by `ApexForge.Runtime.ManagedNativeAbi`.

## Deferred and Unselected Boundaries

At this gate:

- Target-neutral handoff reconstruction is not yet selected as complete.
- Managed executable carrier reconstruction is not yet selected as complete.
- Host ingress remains unselected.
- External serialization remains unselected.
- Native host remains deferred.
- Execution dispatch remains deferred.

The P12.2 transport must not be promoted into semantic authority, and executable semantics must not be inferred from fingerprints.

## Next Stage Gate

`P12.5-RCV-6 DEDICATED MANAGED HOST PROJECT SKELETON`
