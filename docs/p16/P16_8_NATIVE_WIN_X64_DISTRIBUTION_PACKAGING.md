# P16.8 Native win-x64 Release Packaging — Review Evidence

## Baseline and scope

P16.8 packages only the frozen executable profile
`apexforge.native.win-x64.i64-literal-state-set/v1`.
Canonical semantic authority remains CANONICAL_AIR. This is review evidence,
not a production release, installation, publication, freeze, or execution permit.

Branch: `p16-1-release-baseline`.
HEAD / P15 freeze: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Parent: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Tag: `afp-p15.14-freeze`.
Tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
Peeled target equals HEAD. Initial inventory: exactly 21 incoming untracked P16
paths, no tracked/staged diff, no ignored/generated residue. No frozen owner was
changed. P15_REOPENED=False.

Incoming SHA-256 census:
```text
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
F12B0E26ED0589CBD11DF8F6729A8D10801EF3900E438000B422BAE4012F7DDE  apexforge/p16_6_vscode_distribution_packaging_test.py
3D3CEA0DA2FD2F1E8F779EB40628B6E7E4DA0E3B6854057360B12B4AAC3DB616  apexforge/p16_7_visualstudio_distribution_packaging_test.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
D92139A8BD491347762A488AEFBDF3C50E945E8F4923A5A339C7D6084F4E474F  apexforge/tooling/visualstudio_distribution.py
60040C7E90D99BC14771D9CC93DA7F8D518BB25157A6E17F9AFB3ADDCBB6EBB8  apexforge/tooling/vscode_distribution.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
478EE3227FEA029B7C1F9193F66D83D7D93D1A68E214AC0B9B29C18299B22BF6  docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
0FB837164A660844374A7C8534FD4AC88C36DC79CCAC7988736351B56D064F4F  docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md
0F83C51FB2C9B8E93B4D39CBDA03ACC82DCF12B6CD08DF031960A7D324DD4E90  docs/p16/P16_7_VISUAL_STUDIO_DISTRIBUTION_PACKAGING.md
```

## Existing-owner census

| Evidence / concern | Classification | P16.8 use |
| --- | --- | --- |
| native_backend/native_execution_contract.py; P12.5 profile tests and RCV-53/54 reports | FROZEN_NATIVE_PROFILE_CONTRACT / REUSE | Exact admission; no new AIR forms |
| native_backend/native_execution.py | FROZEN_NATIVE_BUILD_OWNER / REUSE | Existing C emission, toolchain discovery, fixed compiler/linker recipe, byte-backed receipt |
| native_backend/lowering_input.py, execution_plan_binding.py | FROZEN_NATIVE_ARTIFACT_CONTRACT / REUSE | Exact canonical AIR transport and routing |
| native_backend/source_mapping.py; P12.6-4 report | FROZEN_NATIVE_ARTIFACT_CONTRACT / REUSE | Producer-owned generated-source correspondence, no inferred physical spans |
| native_backend/model.py and target_neutral_lowering.py | REFERENCE_ONLY | Sibling backend / AIR ownership; no parallel lowering |
| payload, value, envelope, result and native dispatch portions | REFERENCE_ONLY | Execution boundary; not invoked |
| P12.4B/D COFF and P12.4G production DLL contracts | REFERENCE_ONLY | Distinct historical object/library profiles, not this execution-profile artifact |
| tooling/package_artifacts.py; P14.11 tests | FROZEN_NATIVE_ARTIFACT_CONTRACT / REUSE | Strict supplied receipt parser/hash syntax; exact native-image/package boundaries |
| P16.1 release architecture | REUSE / NATIVE_RELEASE_EXTENSION_POINT | Exact release target and descriptor; classified EXE format correction below |
| P16.2 version policy | REFERENCE_ONLY | Packaging grants no compatibility |
| P16.3 release build | REUSE | Existing COPY_BYTES adaptation |
| P16.4 release manifest | REUSE | Existing checksum/provenance/scoped completeness |
| P16.5–P16.7 wrappers and evidence | REFERENCE_ONLY | Target packaging conventions and unchanged limitations |
| Local MSVC/SDK | ENVIRONMENT_DEPENDENCY | Available tools only, no acquisition |
| Installation, publication, signing | DEFER_TO_P16_9 / DEFER_TO_P16_10 / DEFER_TO_P16_11 | No implementation here |

P12.4G's lifecycle library is `apexforge_native.dll`, with profile
`apexforge.win-x64-production-native-library/v1`, /DLL /NOENTRY and two lifecycle
exports. It is not the exact P12.5 executable profile requested here. P16.8
neither substitutes this DLL nor expands support to it. The frozen P12.5 owner
produces `program.exe`, a PE32+ AMD64 console image with apexforge_entry.

## Distribution identity and exact source continuity

NativeDistributionIdentity is immutable, domain-separated, explicit-release
bound, exact-P15-baseline bound, and rejects profile aliases, other targets and
formats. Windows/x64/EXE is the only accepted combination. The profile is not a
promise of whole-language native support.

Caller supplies exactly five fixed frozen native-owner Git blobs. Exact names,
counts, duplicate rejection and SHA-256 equality are validated; input ordering
canonicalizes. Source ledger:
```text
native_execution_contract.py 5742C08FA80A14F889C914C41959E174B782CA45A040DDDEF3C63B002E621902
native_execution.py 0E112B5FAB1A2305813FB7F6DBE322A7B034248DC509CFF1B34985C0591C5876
lowering_input.py 701ACD1A837FCEB57D6E66080E035C53E3B2C521D734B2254C159422874521B6
execution_plan_binding.py 0752F0AFFC2E8EE104110915FC3D7CB2F383C974E2A68902A7567D614C3A04E4
source_mapping.py C65A0F820351C0EAD0D02EE74883BDE52445E6341265BC05F496EE99925B2374
```
Test-only fixed read-only Git projection obtains these exact baseline blobs.
Checkout CRLF hashes differ from Git blob hashes; no frozen file is normalized or
rewritten. Production accepts supplied bytes, invokes no Git and performs no
source traversal. The imported frozen owner remains unchanged; Python source
line-ending translation does not alter emitted C. This ledger identifies the
five inspected owners, not authenticated proof of every transitive dependency.

The review ReleaseIdentity uses explicit identifier native-review, declared
version declared-16, DEVELOPMENT channel. It is not a final release-version
selection. Descriptor: native-exe, NATIVE_COMPONENT, native-win-x64, exe,
program.exe, surface version profile-v1, SUPPORTED. Python/editor/package
versions remain separate. No P14 package coordinate/content pair is invented:
the scoped artifact has no supplied package association.

## Admission, AIR, source mapping and receipts

NativeReleaseEvidence reuses admit_native_profile and emit_native_source_mapping.
Unsupported AIR rejects before temporary roots/toolchain/build. Exact AIR,
routing, entry, states, generated C, frozen options, image digest and receipt
schema/canonical bytes must agree. Toolchain identities are bounded hash evidence.
Receipt parsing rejects duplicate JSON keys, unknown fields, malformed data and
noncanonical representation.

The immutable evidence snapshots admission, mapping fingerprint, canonical
receipt and binary metadata; caller plan containers do not remain canonical state.
Hand-authored verified AIR has UNMAPPED_SOURCE physical-source correspondence.
Generated-C regions come from the frozen emitter; P16.8 fabricates no source spans
or machine addresses. The supplied receipt is integrity/linkage evidence, not
backend ticket issuance, authentication, a bearer token or authority. The local
path demonstrates genuine output through the owner; supplied-evidence ingestion
does not authenticate a compiler invocation.

Measured chain:
P15 frozen owners -> canonical verified AIR -> exact profile admission/routing
-> emitted program.c and native mapping -> frozen MSVC build receipt -> EXE bytes
-> P16.8 evidence -> P16.3 artifact -> P16.4 checksum/provenance/scoped manifest.

AIR fingerprint:
`E2BF031B6C1D82AC1FD83DAA1989A6F127EA3B286016479178A2115B3E96D77C`.
Routing:
`BB33622DD20CBDD9F1988CAB43D41CD020FC209BD28D5A130D3CC886F5BB7D0C`.
Generated C:
`8761AEB871ADDCA2993E0E9658930A9F3D669E7BD30287663CAC022B09A006C9`.
Native mapping:
`14822C7A688E3F7FA61B310C15484C584AD67980F3A143AA9F54EC4C3B206D74`.

## Toolchain and actual builds

Actual owner-discovered local compiler:
`C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/HostX64/x64/cl.exe`.
Linker is in that HostX64/x64 directory. Operational MSVC version 14.51.36231,
Windows SDK 10.0.26100.0, target x64. Host paths are operational evidence,
not release identity.

The unchanged owner uses fixed vswhere and VsDevCmd discovery (a fixed internal
batch wrapper, no caller command text), removes ambient CL/_CL_/LINK/_LINK_
overrides, validates x64, then fixed compiler argv, captured diagnostics and
bounded timeout. P16.8 calls only build_native with timeout 120 under an empty
controlled TemporaryDirectory. No dispatch/execute API is called. The owner binds
compiler/linker/kernel32.lib and companion DLL hashes in its existing receipt.
The new layer neither downloads tools nor installs dependencies. Selected hashes:
```text
cl.exe E6D57100C82AE0310C18B16ABFE52BC0DF8FBB272CA6C5FB287D485807CFCE91
link.exe 3EF8FCF80D409FAB22DDD89EE19249F31A26AD9914D3E3E48573C30998FA24DE
kernel32.lib 341C7D56125A03B458E4D5093E4C79B33123CCFDFD610FE236937B8E6F3134BB
```

Frozen argv:
```text
/nologo /TC /W4 /WX /Od /GS- /Zl /Brepro program.c /Foprogram.obj /Feprogram.exe
/link /Brepro /INCREMENTAL:NO /MACHINE:X64 /SUBSYSTEM:CONSOLE
/ENTRY:apexforge_entry /NODEFAULTLIB kernel32.lib
```

Two independently constructed inputs/build roots produced BUILT/BUILT.
Both images: 2,560 bytes, SHA-256
`1B75E5B4B507D9C96E440903877036992D777F16870F73A4AF64CA6A06B35D0A`.
Receipt fingerprint:
`47278AFED865903EACA8CEA25CFDFBD66AA5C88A74445FA47B7151C709DCA1B9`.

Comparison: context_equal=True, raw_bytes_equal=True,
structural_metadata_equal=True, receipt_equal=True, authenticated=False.
A further independent genuine build produced the same digest and was adapted
into P16.3 exact-byte build evidence and a COMPLETE scoped P16.4 manifest; existing
verify_checksum returned the exact checksum-reference evidence. No package,
build or manifest owner was reimplemented.

The measured PASS is scoped to these frozen inputs and this installed toolchain.
It is not cross-toolchain/platform/version reproducibility, whole-language
coverage, compatibility or release approval.

## Binary inspection, debug policy and residue

PE inspection is data-only and bounded: 1 MiB bytes, at most 96 sections and 64
debug-directory entries. DOS/PE signatures, AMD64, PE32+ executable (not DLL),
console subsystem, bounded/aligned headers/sections/directories, nonoverlapping
raw/virtual section ranges and executable entry RVA are checked. Debug payload
offsets and lengths are bounded. No loader, disassembler, dynamic import,
ctypes/loadlibrary, extraction, or native execution is added.

Measured image: entry RVA 4272, headers 1024, image size 16384. Three sections:
.text (512 raw bytes), .rdata (512), .pdata (512).
Section digests:
```text
.text 35D33FC74B203054BA9A057C405F219AA0D943BB77C42EFC15F7081701545B05
.rdata 1C076059EC6D5A4B07E156AF9C03272DDBA28BB0F49F6CBAD91E4727DFFD2A97
.pdata 7540428B3FCE7ADBF6480F1FF41794725D1CBF050A3CB73A767B8B02A3611D29
```
PE timestamp field 3544370520 is identical in both builds. It is recorded as a
field, not interpreted as the current time: /Brepro metadata need not be a
wall-clock timestamp. Debug kinds 13 and 16 are identical; type-16 reproducibility
metadata is present. No RSDS record, .pdb marker or controlled temporary-root
marker was found in the measured bytes. This is a bounded observed check,
not a universal claim that every binary has no host information.

No separate native archive is required by the owners. Only exact program.exe
bytes enter release evidence. Generated .obj, discover.cmd, program.c and any
diagnostic files stay in task-controlled temporary roots and are removed through
normal context cleanup. PDB is not declared as a release artifact; no symbols are
silently packaged. No installed copy, PATH change, service, runtime or system
binary location is touched.

## Integration and security boundaries

P16.1 owns release identity/targets/descriptors; P16.2 owns compatibility/version
policy; P16.3 owns COPY_BYTES build identity; P16.4 owns checksum/provenance and
manifest completeness. P16.8 records references and exact bytes through those
owners. The native artifact is derived from canonical AIR; it cannot redefine
AIR, authority, package identity, language support or editor behavior.

No final release container policy, native runtime, installer, publication,
signing/verification integration or later-slice acceptance/freeze work is added.
Production imports no subprocess/network/credential/signing/library-loading API.
Its only process-capable delegation is the existing native owner's build_native.
The frozen owner also contains dispatch/loading functions; those are neither
called nor used to validate this slice. Fixed toolchain-discovery batch mechanics
are preserved rather than generalized into a command API.

NATIVE_RELEASE_PACKAGE != WHOLE_LANGUAGE_NATIVE_SUPPORT
NATIVE_ARTIFACT != CANONICAL_AIR
NATIVE_ARTIFACT != SOURCE_IDENTITY
NATIVE_BUILD_SUCCESS != SEMANTIC_EXPANSION
NATIVE_BUILD_SUCCESS != COMPATIBILITY_PROOF
NATIVE_ARTIFACT != EXECUTED_ARTIFACT
NATIVE_ARTIFACT_DIGEST != AUTHENTICATION
NATIVE_PACKAGE_VALID != TRUSTED_PACKAGE
NATIVE_PACKAGE_VALID != AUTHORITY
NATIVE_BINARY_SEMANTICS_DERIVED_FROM_CANONICAL_AIR=True
CRYPTO_PROVIDER_UNAVAILABLE

## Validation and Patch Matrix

Focused P16.8: 36/36 PASS. Synthetic PE and synthetic receipt fixtures exercise
parsing/model security and are explicitly distinguished from the genuine local
builds above. Focused tests cover release/profile/target/source exactness,
unsupported AIR before build, wrong descriptors before build, receipt
substitution, bounded PE/debug offsets, architecture, section overlap, duplicates,
independent evidence determinism, no dispatch, cleanup, existing-manifest
integration and static security audit. Scale: two independently constructed sets
of 1,000 small PE inspections; deterministic iterative processing, no benchmark.

Predecessor focused: P16.7 38, P16.6 33, P16.5 35, P16.4 41, P16.3 31,
P16.2 31, P16.1 25 — all PASS after the owning correction.
P16 aggregate: final 270/270 PASS, including maximum-profile receipt coverage and exact-type target validation.
P14 aggregate: 330/330 PASS.
Frozen native contract: 7/7 PASS.
Authority consolidation: canonical identities/exact grant/wrong
principal-capability-resource denial/authorized RuntimeEngine execution/
transactional denied execution PASS. Only that unchanged frozen smoke executes
RuntimeEngine; P16.8 neither executes native artifacts nor workloads.
P15 aggregate: 428/428 PASS.

Patch route:
FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

| Finding | Classification / owner | Correction and evidence |
| --- | --- | --- |
| Native descriptor permits DLL only although P12.5 emits EXE | NATIVE_ARTIFACT_MODEL_GAP; owning P16.1 release artifact format | Added exe alongside existing dll in one native SURFACES tuple; profile/target/roles unchanged. New P16.8 positive/negative coverage; owning P16.1 and all descendants rerun |
| P16.1 format test assumed exe always unsupported | Same owning format contract | Unsupported-format assertion now uses wasm; invalid format remains rejected. No assertion removed; EXE positive continuity explicitly tested in P16.8 |
| Initial test bootstrap failed importing apexforge.native_backend through source mapping | NATIVE_AIR_CONTINUITY_GAP; P16.8 test harness | Added repository root before source root to match frozen mapping import convention; no owner patch; focused suite PASS |
| Initial 64 KiB receipt bound would exclude maximum frozen Unicode state identities | NATIVE_ARTIFACT_MODEL_GAP; P16.8 ingestion bound | Bounded 1 MiB receipts retain all 256 long Unicode state IDs without expanding the profile; focused maximum-profile regression PASS |
| Target comparison needed exact string types before equality | NATIVE_TARGET_BINDING_GAP; P16.8 identity | Exact types reject caller objects before equality callbacks; hostile-target focused regression PASS |
| Host reproducibility limitations from other packaging slices | REFERENCE_ONLY / ENVIRONMENT_DEPENDENCY | Carried unchanged; not repaired here |

Exactly two incoming files changed for the classified P16.1 owning defect:
release_architecture.py original
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A ->
9662672BA7CFE5FDD0C1DDD71B02B6C8804D8C2EA58FE4DF8E6D2E3F0B7679AC.
p16_1_release_architecture_contract_test.py original
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8 ->
D8849A290CF65A0FAB56416CFE0D6DD4588CAD28425E2B218BB604F918EEF869.
All remaining 19 incoming hashes are preserved. Earlier evidence reports retain
their historical census and are not edited to hide the correction.

## Carry-forward limitations

P16.5 sdist content reproducibility PASS, raw archive timestamps differ;
wheel construction remains unavailable. P16.6 VSIX contract PASS with exact Git
blob projection, real offline VSCE unverified. P16.7 actual cache-only VSIX build,
assembly continuity and P16.3/P16.4 adaptation PASS; independent raw/member/
assembly reproducibility remains DEFERRED due to PE/debug/generated/archive
metadata differences. All P16.2–P16.7 files remain unchanged. No tools or
dependencies were installed to alter these facts.

## Preservation and exact state

Final audit: branch remains p16-1-release-baseline; HEAD remains
c9c5ca186c9d942ce336ac1ebfe1287b16953200. P15 branch remains at that freeze;
tag object remains d7761c04e4422bfb91d9582275a60912874678f4 and peels to the
same commit. Tracked and staged diffs are empty. Exactly 24 intended P16 paths
are untracked: the 21 incoming candidates plus native_distribution.py,
p16_8_native_distribution_packaging_test.py and this report. No ignored/generated
native/object/bin/obj/VSIX/test residue exists in the repository. Controlled
native build/census temporary roots cleaned normally. No frozen P15 or earlier
file changed. Of the 21 incoming hashes, 19 are unchanged and two have the exact
classified P16.1 corrections documented above. No stage, commit, tag, push,
installation, publication or P16.9 work occurred.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_8_INCOMING_CANDIDATES=21
P16_8_REDEFINES_CORE_SEMANTICS=False
P16_8_NATIVE_PROFILE_REDEFINED=False
P16_8_REDEFINES_NATIVE_EXECUTION_CONTRACT=False
P16_8_EXACT_NATIVE_PROFILE_BOUND=True
P16_8_UNSUPPORTED_AIR_FAILS_CLOSED=True
P16_8_WHOLE_LANGUAGE_NATIVE_CLAIM=False
P16_8_UNSUPPORTED_NATIVE_TARGETS_ADVERTISED=False
P16_8_DISTRIBUTION_EXACT_RELEASE_BOUND=True
P16_8_DUPLICATE_NATIVE_BACKEND_ADDED=False
P16_8_HOST_TOOLCHAIN_NOT_SEMANTIC_AUTHORITY=True
P16_8_ONLY_NATIVE_TOOLCHAIN=True
P16_8_ARBITRARY_COMMAND_EXECUTION=False
P16_8_NETWORK_DEPENDENCY_ACQUISITION=False
P16_8_NATIVE_ARTIFACT_BYTE_BACKED=True
P16_8_NATIVE_PROVENANCE_EXPLICIT=True
P16_8_CANONICAL_AIR_CONTINUITY=True
P16_8_SOURCE_MAPPING_FABRICATED=False
P16_8_NATIVE_FORMAT_REPOSITORY_DERIVED=True
P16_8_NATIVE_BINARY_EXECUTED=False
P16_8_MACHINE_ARCHITECTURE_VERIFIED=True
P16_8_BUILD_ARTIFACT_CONTINUITY=True
P16_8_NATIVE_CONTAINER_REPOSITORY_DERIVED=True
P16_8_GENERATED_RESIDUE_PACKAGED=False
P16_8_RAW_BYTE_REPRODUCIBILITY_CLAIM_EVIDENCE_BASED=True
P16_8_RELEASE_VALIDATION_EXECUTES_NATIVE_ARTIFACT=False
P16_8_NATIVE_PACKAGE_GRANTS_AUTHORITY=False
P16_8_BUILD_GRANTS_COMPATIBILITY=False
P16_8_VALID_NATIVE_ARTIFACT_GRANTS_TRUST=False
P16_8_ARTIFACT_SIGNING_IMPLEMENTED=False
P16_8_CRYPTO_TRUST_FABRICATED=False
P16_8_REDEFINES_RELEASE_ARCHITECTURE=False
P16_8_REDEFINES_VERSION_POLICY=False
P16_8_REDEFINES_GENERIC_BUILD=False
P16_8_REDEFINES_RELEASE_MANIFEST=False
P16_8_REDEFINES_PYTHON_DISTRIBUTION=False
P16_8_REDEFINES_VSCODE_DISTRIBUTION=False
P16_8_REDEFINES_VISUAL_STUDIO_DISTRIBUTION=False
P16_8_INSTALLATION_PERFORMED=False
P16_8_PUBLICATION_PERFORMED=False
P16_8_CREDENTIAL_ACQUISITION=False
P16_8_UNBOUNDED_FILESYSTEM_DISCOVERY=False
P16_8_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_8_PACKAGE_EVIDENCE_DETERMINISTIC=True
P16_8_STATIC_SECURITY_AUDIT=PASS
CRYPTO_PROVIDER_UNAVAILABLE
P16_5_WHEEL_LOCAL_BUILD_AVAILABLE=False
P16_5_SDIST_CONTENT_REPRODUCIBLE=True
P16_5_SDIST_RAW_BYTES_REPRODUCIBLE=False
P16_6_REAL_VSCE_BUILD_VERIFIED=False
P16_7_REAL_VISUAL_STUDIO_VSIX_BUILD=True
P16_7_BUILD_VSIX_ASSEMBLY_CONTINUITY=True
P16_7_RAW_BYTES_REPRODUCIBLE=False
P16_NATIVE_DISTRIBUTION_MODEL=PASS
P16_NATIVE_PROFILE_BINDING=PASS
P16_NATIVE_TARGET_BINDING=PASS
P16_NATIVE_SOURCE_CONTINUITY=PASS
P16_NATIVE_AIR_CONTINUITY=PASS
P16_NATIVE_ARTIFACT_MODEL=PASS
P16_NATIVE_ARTIFACT_CONTINUITY=PASS
P16_NATIVE_BINARY_FORMAT=PASS
P16_NATIVE_MACHINE_ARCHITECTURE=PASS
P16_NATIVE_BINARY_SECURITY=PASS
P16_NATIVE_RELEASE_REPRODUCIBILITY=PASS
P16_NATIVE_RELEASE_MANIFEST_INTEGRATION=PASS
P16_NATIVE_RELEASE_TRUST_BOUNDARY=PASS
P16_NATIVE_RELEASE_AUTHORITY_BOUNDARY=PASS
P16_7_REGRESSION=PASS
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
P16_8_READY_FOR_REVIEW=True
```
