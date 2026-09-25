# P12.5-RCV-2 Recovered P12.5 Lineage Provenance

This artifact establishes an explicit recovered P12.5 lineage from the published P12.4 freeze.

## Recovery Base

- Branch: `p12-native-backend-recovered`
- Base commit: `13f7646f1052746f54f906076d66d29117ee2718`
- Base freeze tag: `afp-p12.4-freeze`
- Base freeze tag object: `7c475986ed3ed1d58cc30148603fbfe8b09529ee`
- Base state: P12.4 complete, frozen, and published.

## Unavailable Original Continuation

The previously committed P12.5 continuation is recorded as `b7d5b1c1355c648f52f7293b675a9862f5655a98` at stage `P12.5E-E-P`.

At recovery initiation, that commit was unavailable on the Dell and unavailable from the advertised GitHub history. The recovered lineage does not claim Git identity equivalence with that unavailable history.

## Recovery Policy

The recovered branch is a new audited lineage. It does not reconstruct original commit IDs, does not reuse the original branch name, and does not silently identify recovered commits as the unavailable originals.

Each recovered P12.5 stage must be rebuilt from the verified P12.4 freeze and revalidated on the current machine. Historical P12.5 evidence may guide reconstruction, but recovered commits remain new identities.

The original history remains historical evidence and may be reconciled later if its exact Git objects are recovered.

## Known Original P Artifact Identities

- Managed executable carrier SHA256: `93A12A19AD7AF2EE4A8165A13C0B72E5005E09EEA022F856EFB8B52ECBE97157`
- P carrier smoke SHA256: `09B4C737BD9C77AA335C06BA450285EF2A4304880997E38A98B7BB932A5026E5`

These hashes are evidence targets only. Matching file bytes does not recreate the unavailable Git commit identity.

## Recovery Environment

- Python: 3.9.13
- .NET SDK: 10.0.302
- Environment equivalence to the original P12.5 build is not assumed.

## Next Gate

`P12.5-RCV-3 RECOVERED P12.5 READINESS AND RECONSTRUCTION CENSUS`
