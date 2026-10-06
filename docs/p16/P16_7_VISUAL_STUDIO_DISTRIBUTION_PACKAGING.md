# P16.7 — Visual Studio Extension Release Packaging

P16.7 adds exact frozen-source/release binding and bounded Visual Studio VSIX
evidence around the existing project and frozen T5 auditors. Real offline builds
succeeded. Reproducibility is **not** established: independent assemblies,
normalized payloads, and raw archives differ. This is contract/build evidence for
review, not installation, publication, trust, or release-candidate approval.

## Baseline and incoming census

Branch: `p16-1-release-baseline`.
HEAD, P15 branch, and P15 tag peel:
`c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Tag: `afp-p15.14-freeze`; annotated object:
`d7761c04e4422bfb91d9582275a60912874678f4`.
Parent: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Baseline tracked/staged diffs were empty, with eighteen intended untracked P16
paths and no ignored/generated residue. The active user assignment supersedes
AGENTS.md's historical P11 target; its engineering/preservation rules remain.

```text
P16_7_INCOMING_CANDIDATES=18
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
F12B0E26ED0589CBD11DF8F6729A8D10801EF3900E438000B422BAE4012F7DDE  apexforge/p16_6_vscode_distribution_packaging_test.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
60040C7E90D99BC14771D9CC93DA7F8D518BB25157A6E17F9AFB3ADDCBB6EBB8  apexforge/tooling/vscode_distribution.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
478EE3227FEA029B7C1F9193F66D83D7D93D1A68E214AC0B9B29C18299B22BF6  docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
0FB837164A660844374A7C8534FD4AC88C36DC79CCAC7988736351B56D064F4F  docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md
```

All eighteen hashes remain identical. No predecessor, project, source, version,
manifest, editor, compiler, or package-owner file was patched.

## Existing-owner census

| Evidence | Classification | Use |
| --- | --- | --- |
| tooling.visualstudio_packaging, T5.7 | REUSE; FROZEN_VISUAL_STUDIO_CONTRACT | Manifest identity/assets/prerequisites, archive hardening, assembly and VSIX hashes |
| tooling.visualstudio_integration, T5.8 | REUSE; FROZEN_VISUAL_STUDIO_CONTRACT | Composite source and VSIX audits, every predecessor receipt, normalized payload digest |
| T5.1 extension/foundation, T5.2 editor, T5.3 bridge, T5.4 diagnostics, T5.5 intelligence, T5.6 commands | REUSE through T5.8; FROZEN_LANGUAGE_SERVER_CONTRACT | Preserve existing source/editor contracts; never activate them |
| csproj, solution, source.extension.vsixmanifest, package registration | FROZEN_VISUAL_STUDIO_CONTRACT | The project remains the sole assembly/VSIX build definition |
| Installed-copy SHA-256/registration uniqueness owner | REFERENCE_ONLY; DEFER_TO_P16_9 | Never call installed-profile discovery from new production code |
| P10 packaging/integration smokes and P11 Visual Studio boundary references | REFERENCE_ONLY | Existing smoke/metadata/identity evidence; no new editor acceptance behavior |
| P16.1 | REUSE | ReleaseIdentity, exact P15 baseline, visual-studio target and descriptor |
| P16.2 | REFERENCE_ONLY | Distinct Visual Studio surface/version domain; no compatibility grant |
| P16.3 | REUSE | Exact supplied VSIX byte COPY_BYTES artifact and provenance reference |
| P16.4 | REUSE | Scoped release manifest, checksum and provenance ownership |
| P16.5/P16.6 | REFERENCE_ONLY | Carry unresolved Python/VSCE facts; no builders or repairs invoked |
| New immutable release/evidence wrapper and controlled build entry points | VISUAL_STUDIO_RELEASE_EXTENSION_POINT | Release binding, exact source ledger, assembly continuity, bounded byte inspection |
| Dotnet/full MSBuild/local NuGet cache | ENVIRONMENT_DEPENDENCY | Operational facts only, never release identity |
| Installation / Marketplace / signing | DEFER_TO_P16_9; DEFER_TO_P16_10; DEFER_TO_P16_11 | No implementation or credential acquisition |

There is no second VSIX packager. Both entry points invoke only the frozen
Visual Studio project. The existing composite auditor still owns manifest,
editor, bridge, packaging, and payload semantics. The release layer supplements
exact source metadata/asset resolution and bounded parsing; it does not replace
the owning interpretation.

## Exact project and extension metadata

The frozen source declares:

| Field | Value |
| --- | --- |
| Extension ID | GravitasStudios.ApexForge.VisualStudio |
| Extension version | 0.1.0 |
| Publisher metadata | Gravitas Studios |
| Display name | ApexForge Language Tools |
| Description | Visual Studio editor foundation for ApexForge .apex source files. |
| Language | en-US |
| MoreInfo | https://github.com/Gravitas-Studios/ApexForge |
| Tags | ApexForge, language, editor, VSIX |
| Installation targets | Microsoft.VisualStudio.Community [17.0,), amd64 and arm64, in declared order |
| Prerequisite | Microsoft.VisualStudio.Component.CoreEditor [17.0,) |
| Source assets | Microsoft.VisualStudio.VsPackage / PkgdefProjectOutputGroup; Microsoft.VisualStudio.MefComponent / BuiltProjectOutputGroup |
| Packaged assets | ApexForge.VisualStudio.pkgdef and ApexForge.VisualStudio.dll |
| Project SDK/framework | Microsoft.NET.Sdk / net472 |
| Assembly / namespace | ApexForge.VisualStudio / GravitasStudios.ApexForge.VisualStudio |
| Platform / deterministic | AnyCPU / true |
| Deployment | DeployExtension=false; VsixDeployOnDebug=true is retained in source, no debug/IDE launch |
| Package registration | AsyncPackage; managed resources; background loading declaration |
| Package GUID | DF54A578-54A2-52F4-8643-4A85DDDFB2F2 |
| InstalledProductRegistration version | 0.1.0 |
| SDK reference | Microsoft.VisualStudio.SDK 17.14.40265, runtime assets excluded |
| Language client reference | Microsoft.VisualStudio.LanguageServer.Client 17.14.60, runtime assets excluded |
| Build tools reference | Microsoft.VSSDK.BuildTools 18.5.40034, private assets all |

The complete source manifest and project XML are retained as deterministic
projections, including references and all declared metadata. The project does
not declare an independent assembly version; none is invented or equated to the
VSIX version. Extension, release, Python, VS Code, package, and language/schema
version domains remain distinct even when numeric strings coincide. Publisher,
author, GUID and product metadata are not authenticated organizational identity.

## Distribution identity and frozen source continuity

`VisualStudioDistributionIdentity` is immutable and requires the exact P15
baseline plus exactly twenty-two caller-supplied frozen Git blob files. Their
canonical path/SHA-256 ledger is pinned to:

`9EDF0D0A9E950BDEA07113338E547345AD57CB0EFA7BF5B7BC2DC26C854D5F6F`.

The full ledger appears in the identity record. It includes .gitignore, solution,
README, three Visual Studio evidence guides, csproj, source manifest, package,
five classification files, three command files, content-type declaration, three
language-server files, and VSCT resources. Exact paths are enumerated in the
module; there is no recursive source discovery. Permutations canonicalize;
changed bytes, missing/extra/duplicate files, or CRLF rewriting fail closed.

Source bytes are obtained in acceptance through fixed read-only Git commands
against the named P15 commit. Production consumes supplied bytes and never
invokes Git or normalizes line endings. Temporary projection bytes are preserved
exactly. T5.8's composite source auditor validates the projection before building.

T5.7 fingerprint:
`44825d6431ffbce78bfc2f3c099bee34608518cb177b8196fd66c12df4bf0019`.
T5.8 fingerprint:
`bdb42496823c8e9fa10e196b1cc624817f48df02bcfa3ec7dab006cf7c6be026`.

The supplementary unchanged T5.8 smoke against this CRLF checkout failed on raw
classification-file hashes. The full same auditor passes against frozen Git
bytes. This checkout failure is documented, not hidden or fixed by editing the
frozen owner. The unchanged T5.7 packaging smoke passed, including its isolated
synthetic installed-copy equality checks; it did not install into Visual Studio.

## Local environment and controlled build paths

Operational inspection found:
- dotnet SDK 10.0.400; its MSBuild version 18.9.6.38015;
- MSBuild was absent on PATH;
- the installed Visual Studio tool locator found full Community MSBuild at
  `C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/MSBuild.exe`;
- full MSBuild version: 18.9.1.35102;
- all three directly declared package/version directories already existed in the
  local NuGet package cache.

The first disposable dotnet Release probe used `--no-restore`, warnings as
errors, explicit output, no deployment, fixed argv, no shell, 120-second timeout,
captured diagnostics, and an isolated environment. It reported NETSDK1004 because
the clean source projection had no restored assets. No bytes were fabricated.

The cache-only full MSBuild path then succeeded. It uses fixed supported installed
Community tool locations, an explicit frozen project, and:
1. Restore with an explicit temporary NuGet.Config, packageSources cleared, one
   empty local feed, existing global package cache, and NuGetAudit=false to prevent
   public audit-feed acquisition.
2. Release Rebuild with warnings as errors, DeployExtension=false, explicit
   disposable output, no shared compiler, and nodeReuse:false.

Each invocation has shell=False, captured output, and a 120-second timeout.
Source, obj/bin, output, configuration, home, appdata and temporary directories
are disposable. Selected non-secret system/tool-location values are operational;
inherited credentials and publisher tokens are not forwarded. The empty local
feed cannot download missing packages. Missing-cache/tool/framework codes yield
an explicit environment limitation; arbitrary compilation errors are rejected,
not relabeled as environmental success. No dependency/tool installation or
public-network restore occurred. Package-cache availability is not package trust.

The initial cached attempt left a shared compiler holding analyzer DLLs, causing
TemporaryDirectory cleanup to fail. The build result from that failed attempt
was not used as acceptance evidence. The correction disables shared compilation
and node reuse without editing the frozen project. The exact task-owned compiler
was identified by modules inside the controlled scratch root, stopped, and the
verified scratch directory removed. Subsequent successful builds cleaned normally.

## VSIX evidence, archive safety and assembly continuity

`VisualStudioVSIXEvidence` binds exact distribution identity, descriptor, release,
frozen source ledger, VSIX bytes, byte length/SHA-256, source/packaged manifest
metadata, archive members, explicit build-output assembly bytes and declared
digest, both owner fingerprints, and normalized owner payload.

Every construction invokes the existing full composite VSIX audit and hardened
packaging audit. The package manifest must retain source Metadata, Installation,
Dependencies and Prerequisites. Assets remain validated by the existing owner
and must resolve to the reported payload. The contained assembly must equal the
supplied build-output bytes, with matching SHA-256. Wrong digest, substituted
assembly, unresolved asset, changed target/display metadata, or cross-release
descriptor reuse fails closed. Existing installed-copy discovery is never called.

The wrapper performs bounded raw ZIP checks before legacy auditors: malformed
archives, absolute/drive/backslash/traversal/control-character names, Windows
case aliases, conflicting duplicates, file/directory conflicts, encryption,
links/special files, expanded size/count limits, and CRC-valid reads. XML must be
bounded UTF-8; DTD/entities, NUL/UTF-16 entity bypass, malformed text and excessive
depth/count are rejected. No archive extraction or assembly loading occurs.

Bounds: 1 MiB compressed archive/assembly/member (P16.3's existing byte profile),
4 MiB total expanded payload, 1,024 members, 128 KiB XML, depth 16/count 4,096.
One thousand small resources demonstrate deterministic inventory. The frozen
owner supplies its existing compression-ratio and forbidden payload policy.
Development bin/obj, source/project/debug payloads, caches, IDE state, credentials,
test/temp scratch and stale VSIX are rejected. VS-hosted language-server assemblies
are excluded by the frozen bridge owner. The server remains the frozen workspace
bridge; no Python server or editor session is launched.

## Genuine independent build evidence

Two independent cache-only full MSBuild builds from equivalent frozen source and
release records produced genuine owner-audited outputs:

| Evidence | Build A | Build B |
| --- | --- | --- |
| Status | BUILT | BUILT |
| VSIX length | 21,722 | 21,719 |
| VSIX SHA-256 | 39069669B89C1C8CF582F891E353F6F10893331F7809C0CE079A52BB5AF0995B | B05FFCD5CDEAB7E108F6F13E0E87399432626CD2ABEACFEAFD9368619F65E7FE |
| Assembly length | 46,080 | 46,080 |
| Assembly SHA-256 | F83B38FE8A5AA0E5D3F90735E75027E321B9D83051C8677C3511C7FA8E184E00 | E0014666C2F552BAE778C4DCDDB2F43C155D5E31AC157776A243462493120F80 |
| Manifest SHA-256 | 9A53D28C5966C5FEE02BDC9530D48AAA6D4CA9C9F1CC89D1E391B4A496AFA8F0 | same |
| Normalized owner payload SHA-256 | AF6C0975E9075B38482473F62BC18879CCF588BDB4DC3DDDC991C49D15ECE3C3 | 960AF6AB0CED077541DABC98155EFBB85DB8A53DA1C04C540C44ED391D75BEB8 |
| Build-to-VSIX assembly equality | PASS | PASS |

The genuine inventory is:
`extension.vsixmanifest`, `ApexForge.VisualStudio.dll`,
`ApexForge.VisualStudio.pkgdef`, `[Content_Types].xml`, `manifest.json`,
`catalog.json`, in that archive order. The last two are SDK-generated VSIX
metadata, not a competing P16 release manifest. Primary assembly, SDK JSON and
ZIP timestamps differ. Pkgdef/content-types/VSIX XML match. All member bytes and
observed timestamps/digests are retained in inspection evidence, not normalized
away. Artifacts were inspected in memory and disposable outputs cleaned; no
release binaries are left in the repository.

Comparison:
```text
context_equal=True
member_content_equal=False
assembly_equal=False
raw_bytes_equal=False
authenticated=False
```

A second independent diagnostic pair was inspected strictly as PE bytes:
CodeView records exist and differ; embedded PDB paths differ and both reference
the controlled temporary projection. PDB basename remains ApexForge.VisualStudio.pdb.
Both DLLs are 46,080 bytes, with 80 differing byte positions and different PE
timestamp fields. No DLL was loaded or extension activated. These observations
show path/debug/build metadata variation; the PE field difference is not assumed
to be a wall-clock timestamp. Deterministic=true alone does not remove path input
from compiler identity. SDK JSON digests and normalized payload also change.

Retained classifications:
`VISUAL_STUDIO_VSIX_REPRODUCIBILITY_GAP` and
`VISUAL_STUDIO_VSIX_BYTE_REPRODUCIBILITY_GAP`.
No PathMap, timestamp rewriting, metadata stripping, fixed GUID, or frozen build
semantic change is applied. Assembly continuity PASS concerns each individual
build/package pair; it does not claim equality across builds. Reproducibility
qualification remains DEFERRED. Release/source identities exclude host paths;
actual generated bytes are content-bound and honestly preserve observed debug
path variation. Real build success is not release approval.

## P16.1–P16.6 integration and security boundaries

P16.1 owns exact target/role/descriptor and frozen baseline. P16.2 owns version and
compatibility; a constructed VSIX grants neither. P16.3 adapts inspected existing
VSIX bytes into its unchanged COPY_BYTES input/recipe/artifact contract, carrying
the P16.7 evidence fingerprint as source/provenance. P16.4 owns the checksum,
scoped architecture, explicit required provenance chain and completeness.
Focused fixtures prove complete scoped inclusion. Genuine-output adaptation:
An additional genuine cache-only VSIX build was adapted through P16.3 and P16.4: actual VSIX build BUILT; generic build artifact BUILT; scoped release manifest COMPLETE; exact source evidence and SHA-256 verification True; VSIX length 21,725 bytes. This demonstrates integration with the existing owners, not release approval or reproducibility.
No competing build/manifest/version format is added.

P16.5/P16.6 remain byte-for-byte unchanged. Carry-forward facts:
```text
P16_5_WHEEL_LOCAL_BUILD_AVAILABLE=False
P16_5_SDIST_CONTENT_REPRODUCIBLE=True
P16_5_SDIST_RAW_BYTES_REPRODUCIBLE=False
P16_6_REAL_VSCE_BUILD_VERIFIED=False
```
Their gaps were neither repaired nor relabeled. No Python distribution builder or
VSCE/npm acquisition was invoked in P16.7.

CANONICAL_AIR remains semantic authority. The VSIX is not compiler core, a language
server, installed extension, Marketplace listing, organization identity, signature,
runtime authority or trust. New code does not activate Visual Studio, extension,
debugger or RuntimeEngine; invoke VSIXInstaller; publish; look up credentials or
keys; sign; load assemblies; use dynamic imports/eval/exec; or perform unsafe
extraction. Existing SDK build tasks operate only as the authorized frozen build
owner, not a runtime extension session. Publisher/GUID/product metadata, package
cache, checksums and provenance do not authenticate anything.

Static AST checks enforce no network/dynamic-loading/assembly-loading APIs,
shell=False and bounded timeout on the two narrow process call sites, no public
arbitrary-argv/callback API, no installed-copy scan or extraction, and fixed
project/output/configuration paths. Caller records and bytes are exact-type and
bounded. Structured reason codes are canonical; operational diagnostics are
separate and never fingerprinted. Cryptographic status stays
`CRYPTO_PROVIDER_UNAVAILABLE`. No signing infrastructure is created.

## Patch Matrix and retained findings

| Finding | Classification | Owner / patch surface / disposition |
| --- | --- | --- |
| Clean dotnet projection lacks restored assets (NETSDK1004) | VISUAL_STUDIO_PACKAGE_ENVIRONMENT_DEPENDENCY | P16.7 probe reports unavailable without fabricating bytes |
| Existing direct packages/full MSBuild found | ENVIRONMENT_DEPENDENCY | P16.7 controlled empty-feed cache-only path; real build succeeds |
| Shared compiler held analyzer/temp DLL | VISUAL_STUDIO_VSIX_SECURITY_GAP | P16.7 invocation only: shared compilation/node reuse disabled; exact owned helper/scratch cleaned |
| UTF-16 entity-guard bypass found in static review | VISUAL_STUDIO_VSIX_SECURITY_GAP | P16.7 bounded UTF-8/NUL/XML guards and focused test |
| Checkout T5.8 raw classification hashes fail | VISUAL_STUDIO_SOURCE_CONTINUITY_GAP | Exact Git projection passes unchanged owner; no frozen patch |
| Assemblies / normalized payload / ZIP bytes differ | VISUAL_STUDIO_VSIX_REPRODUCIBILITY_GAP; VISUAL_STUDIO_VSIX_BYTE_REPRODUCIBILITY_GAP | Retain measured debug-path/metadata/timestamp evidence; no reproducibility PASS or semantic rewrite |

Route: FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.
All corrections are limited to P16.7. PATCH_MATRIX=PASS means no hidden contract
failure or boundary weakening; it does not erase retained release-hardening gaps
or approve a release. Human review retains final authority.

## Validation

All required Python commands use `python -X utf8 -B`.

| Check | Result |
| --- | --- |
| P16.7 focused | 38/38 PASS |
| P16.6 focused | 33/33 PASS |
| P16.5 focused | 35/35 PASS |
| P16.4 focused | 41/41 PASS |
| P16.3 focused | 31/31 PASS |
| P16.2 focused | 31/31 PASS |
| P16.1 focused | 25/25 PASS |
| Final P16 aggregate | 234/234 PASS |
| Frozen P15 aggregate | 428/428 PASS |
| Frozen P14 aggregate | 330/330 PASS |
| Native profile | 7/7 PASS |
| Authority coexistence | PASS |
| T5.7 unchanged packaging smoke | PASS; temporary synthetic installed-copy check only |
| T5.8 unchanged smoke against checkout | FAIL: CRLF raw source hashes, documented above |
| Same T5.8 source/VSIX composite auditor against frozen projection/output | PASS |
| Actual full MSBuild cached builds and individual assembly continuity | PASS |
| Actual cross-build assembly/content/raw reproducibility | DEFERRED; measured mismatches retained |

Authority smoke preserves wrong principal/capability/resource denial, authorized
RuntimeEngine execution and transactional denial. That existing predecessor test
is the sole runtime execution exercised; P16.7 production code triggers none.
Independent fixtures also test raw timestamp/order mismatch reporting and
canonical source/inventory ordering; fixtures are not real build claims.

## Preservation and exact Git state

Only new paths:
- `apexforge/tooling/visualstudio_distribution.py`
- `apexforge/p16_7_visualstudio_distribution_packaging_test.py`
- `docs/p16/P16_7_VISUAL_STUDIO_DISTRIBUTION_PACKAGING.md`

All eighteen incoming hashes match. Branch, HEAD, P15 branch and tag object/peel
remain unchanged. No P15 or earlier path, authority owner, editor owner, Python/VS
Code contract or metadata changed. Tracked and staged diffs are empty. Exactly
twenty-one intended P16 candidates remain untracked; no ignored/generated
bin/obj/VSIX/cache/test residue. Temporary builds clean normally after the
server-reuse fix, and the initial task-owned leftover was explicitly removed.

Exact final status:
Branch: p16-1-release-baseline. HEAD and P15 branch: c9c5ca186c9d942ce336ac1ebfe1287b16953200. P15 annotated tag object: d7761c04e4422bfb91d9582275a60912874678f4; peeled target equals HEAD. Exactly 21 intended untracked P16 candidates exist: 18 preserved incoming paths plus the three P16.7 paths. Tracked and staged diffs are empty; ignored/generated residue is absent. No staging, commit, tag, push, installation, publication, or P16.8 work occurred.

P16_7_INCOMING_HASHES_PRESERVED=True
P16_7_CANDIDATES=21

No stage, commit, tag, push, global installation, Marketplace activity, signing,
P16.8 work, release-candidate acceptance, or closure/freeze occurred.

## Required markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_7_INCOMING_CANDIDATES=18
P16_7_REDEFINES_CORE_SEMANTICS=False
P16_7_REDEFINES_EXISTING_VISUAL_STUDIO_PACKAGING=False
P16_7_METADATA_REPOSITORY_DERIVED=True
P16_7_VISUAL_STUDIO_VERSION_DOMAIN_DISTINCT=True
P16_7_DISTRIBUTION_EXACT_RELEASE_BOUND=True
P16_7_PUBLISHER_METADATA_AUTHENTICATES=False
P16_7_DUPLICATE_VISUAL_STUDIO_PACKAGER_ADDED=False
P16_7_ONLY_VISUAL_STUDIO_PACKAGING_TOOLCHAIN=True
P16_7_ARBITRARY_COMMAND_EXECUTION=False
P16_7_AUTOMATIC_NETWORK_DEPENDENCY_ACQUISITION=False
P16_7_EXACT_FROZEN_SOURCE_CONTINUITY=True
P16_7_VSIX_EVIDENCE_BYTE_BACKED=True
P16_7_VSIX_ARCHIVE_PATHS_SAFE=True
P16_7_REDEFINES_VSIX_MANIFEST_SEMANTICS=False
P16_7_BUILD_VSIX_ASSEMBLY_CONTINUITY=True
P16_7_EXTENSION_ASSEMBLY_EXECUTED=False
P16_7_EXTENSION_EXECUTED=False
P16_7_LANGUAGE_SERVER_EXECUTED=False
P16_7_REDEFINES_EDITOR_SEMANTICS=False
P16_7_GENERATED_RESIDUE_PACKAGED=False
P16_7_RAW_BYTE_REPRODUCIBILITY_CLAIM_EVIDENCE_BASED=True
P16_7_REDEFINES_RELEASE_ARCHITECTURE=False
P16_7_BUILD_GRANTS_COMPATIBILITY=False
P16_7_REDEFINES_VERSION_POLICY=False
P16_7_REDEFINES_GENERIC_BUILD=False
P16_7_REDEFINES_RELEASE_MANIFEST=False
P16_7_REDEFINES_PYTHON_DISTRIBUTION=False
P16_7_REDEFINES_VSCODE_DISTRIBUTION=False
P16_7_GLOBAL_EXTENSION_INSTALLATION_PERFORMED=False
P16_7_MARKETPLACE_PUBLICATION_PERFORMED=False
P16_7_CREDENTIAL_ACQUISITION=False
P16_7_ARTIFACT_SIGNING_IMPLEMENTED=False
P16_7_CRYPTO_TRUST_FABRICATED=False
P16_7_VALID_VSIX_GRANTS_TRUST=False
P16_7_VSIX_GRANTS_AUTHORITY=False
P16_7_PACKAGE_EVIDENCE_DETERMINISTIC=True
P16_7_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_7_STATIC_SECURITY_AUDIT=PASS
CRYPTO_PROVIDER_UNAVAILABLE
P16_5_WHEEL_LOCAL_BUILD_AVAILABLE=False
P16_5_SDIST_CONTENT_REPRODUCIBLE=True
P16_5_SDIST_RAW_BYTES_REPRODUCIBLE=False
P16_6_REAL_VSCE_BUILD_VERIFIED=False
P16_VISUAL_STUDIO_DISTRIBUTION_MODEL=PASS
P16_VISUAL_STUDIO_EXTENSION_METADATA=PASS
P16_VISUAL_STUDIO_VERSION_BINDING=PASS
P16_VISUAL_STUDIO_VSIX_MODEL=PASS
P16_VISUAL_STUDIO_VSIX_ARCHIVE=PASS
P16_VISUAL_STUDIO_VSIX_CONTENT=PASS
P16_VISUAL_STUDIO_SOURCE_CONTINUITY=PASS
P16_VISUAL_STUDIO_ASSEMBLY_CONTINUITY=PASS
P16_VISUAL_STUDIO_VSIX_REPRODUCIBILITY=DEFERRED
P16_VISUAL_STUDIO_VSIX_SECURITY=PASS
P16_VISUAL_STUDIO_PACKAGE_RELEASE_BINDING=PASS
P16_VISUAL_STUDIO_PACKAGE_MANIFEST_INTEGRATION=PASS
P16_VISUAL_STUDIO_PACKAGE_TRUST_BOUNDARY=PASS
P16_VISUAL_STUDIO_PACKAGE_AUTHORITY_BOUNDARY=PASS
P16_6_REGRESSION=PASS
P16_5_REGRESSION=PASS
P16_4_REGRESSION=PASS
P16_3_REGRESSION=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_7_READY_FOR_REVIEW=True
```

Readiness concerns this bounded packaging contract and honest evidence report.
It does not assert reproducibility qualification, compatibility, trust, signature,
installation safety, release approval or completion of a later milestone.
