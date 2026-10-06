# P16.6 — VS Code Extension Release Packaging

P16.6 adds release identity and bounded VSIX inspection evidence around the frozen
editor packaging owners. It adds no packager, editor behavior, activation,
publication, installation, signing, or later-slice implementation.

## Frozen baseline and incoming census

Branch: `p16-1-release-baseline`. HEAD and P15 branch:
`c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Predecessor: `afp-p15.14-freeze`; annotated object
`d7761c04e4422bfb91d9582275a60912874678f4`; peeled target equals HEAD.
The baseline tracked/staged diffs were empty. Exactly fifteen untracked P16
candidates existed; no ignored/generated residue was reported.

```text
P16_6_INCOMING_CANDIDATES=15
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
478EE3227FEA029B7C1F9193F66D83D7D93D1A68E214AC0B9B29C18299B22BF6  docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
```

These hashes are preserved. No earlier P16, P15, editor, metadata, or frozen file
was patched. The user-directed current slice supersedes AGENTS.md's historical
P11 target; its engineering, determinism and preservation requirements remain.

## Ownership census

| Evidence | Classification | Relationship |
| --- | --- | --- |
| tooling.vscode_package, P10-T3 source/VSIX audits | REUSE; FROZEN_VSCODE_CONTRACT | Source file selection, syntax manifest projection, VSIX XML/embedded manifest semantics; never replace its packager |
| tooling.vscode_lsp_activation, P10-T4 activation/VSIX audit | REUSE; FROZEN_LANGUAGE_SERVER_CONTRACT | Entry/client/guide byte equality, activation declarations, restart/settings records |
| extension.js and runtime/lsp-client.js | REFERENCE_ONLY; FROZEN_LANGUAGE_SERVER_CONTRACT | Package opaque exact bytes; never require/activate/run them |
| package.json, grammar, language configuration, .vscodeignore | FROZEN_VSCODE_CONTRACT | Preserve all declarations; exclusions remain owner-controlled |
| P10-T3 packaging smoke / P10-T4 activation lifecycle tests | REFERENCE_ONLY | Existing mock packaging/install and client lifecycle evidence; no new live install/session |
| P16.1 release_architecture | REUSE | Exact ReleaseIdentity, P15 baseline, vscode target/descriptor |
| P16.2 release_versioning | REFERENCE_ONLY | Distinct VSCODE_EXTENSION mapping; packaging grants no compatibility |
| P16.3 release_build | REUSE | Supplied-existing-artifact COPY_BYTES recipe and exact byte-backed artifact |
| P16.4 release_manifest | REUSE | Scoped architecture/checksum/provenance completeness via its unchanged owners |
| P16.5 python_distribution | REFERENCE_ONLY | Carry forward environment limitations; never call its builders |
| New release identity/evidence wrapper | VSCODE_RELEASE_EXTENSION_POINT | Exact frozen editor/source and release bindings, bounded hostile-archive checks |
| Node/npx and absence of standalone vsce on PATH | ENVIRONMENT_DEPENDENCY | Node v24.19.0 found; offline pinned VSCE not established |
| Installation / Marketplace / signing | DEFER_TO_P16_9; DEFER_TO_P16_10; DEFER_TO_P16_11 | No corresponding behavior added |

The extension has no checked-in package-lock or npm dependency declarations.
The existing owner selects pinned VSCE 3.9.1 with Node >=20 and fixed package
arguments. Its default `npx --yes @vscode/vsce@3.9.1` can acquire packages.
That path was deliberately not invoked: no offline availability was established,
and this task prohibits acquisition. There is no new duplicate VSIX packager.

## Exact metadata and identities

The repository declares:
- name: `apexforge-language`; displayName: `ApexForge Language`;
- extension ID: `gravitas-studios.apexforge-language`;
- publisher metadata: `gravitas-studios`; no authentication assertion;
- extension version: `0.1.0`; VS Code engine: `^1.85.0`;
- main: `./extension.js`; extensionKind: `workspace`;
- activation: `onLanguage:apexforge` and
  `workspaceContains:apexforge/apexforge_lsp.py`;
- language: `apexforge`, aliases ApexForge/apexforge, extension `.apex`,
  `./language-configuration.json`;
- grammar: `source.apexforge`, `./syntaxes/apexforge.tmLanguage.json`;
- commands: showLanguageServerOutput and restartLanguageServer;
- configuration: pythonCommand, serverPath, trace; default serverPath
  `apexforge/apexforge_lsp.py`, empty Python command, trace false.

The immutable identity retains the complete package.json projection and its exact
byte digest, so contributions, settings, activation events, descriptions, and
engine declarations are retained without mutable nested dictionaries. Records
return new projections. Publisher metadata is never Marketplace ownership or
organization identity. Extension version is independent of Python 10.1.3 and the
explicit caller-declared P16 release version. No predecessor metadata is edited.

Every identity requires the exact P15 baseline. Every VSIX evidence record requires
the exact vscode descriptor, version, filename, release, and eight frozen source
digests. Changed release identity re-identifies evidence; source substitution is
rejected even if a substituted archive matches the substituted source bytes.

## Exact frozen source projection and host line endings

The worktree uses `core.autocrlf=true`. The unchanged T3 packaging smoke run
against this checkout failed: expected projected fingerprint
`75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c`,
observed `0bfc8f7f50fc661405a7c262ef5949f89a310ecf5d8a4f1865616905c79e1983`.
This failure is recorded, not hidden or repaired by changing the frozen owner.

A temporary LF diagnostic matched the frozen fingerprint. Acceptance fixtures
therefore obtain the exact source bytes from the named P15 Git blobs through
fixed, read-only test commands. Production does not invoke Git or normalize
bytes. Callers supply the exact frozen source projection; the default checkout
path fails closed when its byte representation differs. A temporary projection
preserves supplied bytes and lets both unchanged owner auditors run.

T3 owner fingerprint: `75a39c44354d4f647ab46cb6aba42adf00f5396c7563b1433ff2d93d66e9498c`.
T4 owner fingerprint: `b74759e09a2de60a9ca78d6baa36d0d608b650858b6220f3ab4b3f2916a940d6`.

The frozen Git byte ledger is enforced in the model:

| Source | SHA-256 |
| --- | --- |
| package.json | 393404F48C57C1D4887B27F6F6A796E606E40486365D8FD140337A97EF60CB80 |
| language-configuration.json | 583DF5B35CA06C090A2AF590A08C47C1B822905B3B6430F267DE45A8CB7EBBF1 |
| syntaxes/apexforge.tmLanguage.json | 80EC2C528EE37EC4C67DB6EBD40D2E8BBF8C48A872DA3CEDCAC3F90125A0808F |
| README.md | 990040AE71C7A4CB2AEEF40387D6D90587E42E3BA7F80F15C04A3C490E9861F1 |
| CHANGELOG.md | 3791A395C77B073A4A01E101B6205BC052D19217609DFA024529106C5A516B29 |
| extension.js | 45E4B9D96A579A558055D24FDE05AE9806DAB1A70C0D2F3C42AD502CB5F98B3E |
| runtime/lsp-client.js | 853B5C026E65B9DB895C82AB322FCF267B41B57E87F2D819C1E1336C64D80145 |
| LANGUAGE_SERVER.md | 98FD6E92D7EA765FDC3CD280BEEB836C773E6453E70CA097BCD6CC6D75ED0F91 |

The five T3 payload files and three T4 runtime/guide files must match byte-for-byte.
The Python language server remains the declared workspace reference, not an
invented packaged server. No extension or server execution occurred.

## Archive/evidence contract and security

The constructor validates bytes, exact immutable source ledger, XML structure
through the existing owner validators, and source/member equality. The inspection
factory additionally invokes both full frozen owner audits. Direct construction
cannot bypass the XML manifest owner. Descriptor/evidence identities bind supplied
archive bytes and length. The P16.3 adapter carries the P16.6 evidence fingerprint
in its explicit source and provenance references; it copies inspected bytes
without redefining generic build identity. P16.4 alone evaluates scoped manifest
completeness. A complete test manifest is not release approval.

ZIP checks are performed before legacy auditors read hostile bytes: safe raw
relative names, no traversal/backslashes/drives/control characters, case-folded
duplicates, file/directory collisions, special files/symlinks, encryption, residue,
size/count limits, and CRC-valid reads. The model rejects .git, .vscode, caches,
node_modules, build/dist, pyc, nested VSIX, and .pypirc. No extraction is performed.
Metadata JSON rejects duplicate keys, malformed UTF-8, floats/nonfinite values,
overlarge data, excessive depth/count. XML is bounded and rejects DTD/entities.
Bounds: 1 MiB archive (P16.3 owner bound), 512 KiB member, 4 MiB expanded total,
1,024 entries, 128 KiB metadata, depth 16/count 4,096. This is a bounded profile,
not a claim that all future extensions fit; a larger artifact requires a classified
owner decision. One thousand small resources demonstrate deterministic inventory.

Static AST tests prohibit process/network/credential/dynamic-loading APIs, arbitrary
commands, discovery, package/install APIs and activation calls. Explicit source
reads use fixed repository paths; temporary writes are controlled and cleaned.
No secret/credential lookup, network, external toolchain, npm install/update, VSCE
install, global extension install, Marketplace operation, or signing exists in
this production module. Frozen JS is never imported/executed. Frozen auditors
read their existing explicit spec/conformance references, not source discovery.

## Reproducibility and local-build availability

Two independent data fixtures pass both frozen owner auditors. Their inventories,
member bytes, metadata and exact release evidence agree. Identical explicitly
fixed timestamp/order fixtures match raw bytes. Altered timestamps or reversed
member order preserve content equality but change raw archive bytes and evidence
fingerprints. Observed timestamps and order remain explicit data; there is no
clock/path/hostname-derived identity.

These are inspection fixtures, not locally constructed VSCE release packages.
A fixture is 17,518 bytes; its SHA-256 is
`10F6EFCFC0DC884125C1401BB6C4123C9BD01E75271543EBF68D55704FD59BF5`.
No actual VSCE artifact was built or retained. Therefore actual-toolchain raw-byte
and member-content reproducibility are NOT_EVALUATED. The model supports byte-backed
evidence, but the actual-local-build marker is False. No fabricated local build
PASS, signed/trusted status, or authenticated publisher is emitted.

## Patch Matrix

| Failure/evidence | Classification | Owner / patch surface / disposition |
| --- | --- | --- |
| Wrong filename constant in initial wrapper | VSCODE_DISTRIBUTION_MODEL_GAP | P16.6 only; use frozen CANONICAL_VSIX_FILENAME |
| Windows ZipInfo normalized hostile fixture path | VSCODE_VSIX_SECURITY_GAP | P16.6 tests preserve raw hostile names; reader validates original names |
| Direct construction could bypass XML owner check | VSCODE_VSIX_SECURITY_GAP | P16.6 constructor reuses existing owner validators; focused bypass test |
| Host CRLF packaging fingerprint differs | VSCODE_VSIX_SOURCE_CONTINUITY_GAP | Exact frozen Git projection supplied; no normalization or frozen patch |
| Offline pinned VSCE not established | VSCODE_PACKAGE_ENVIRONMENT_DEPENDENCY | Retained explicit operational limitation; never invoke acquisition path |

Route: FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.
All code corrections remain within P16.6. Operational limitations remain visible;
PASS for the contract matrix does not mean a local VSCE build succeeded.

## Validation

| Check | Result |
| --- | --- |
| P16.6 focused | 33/33 PASS |
| P16.5 | 35/35 PASS |
| P16.4 | 41/41 PASS |
| P16.3 | 31/31 PASS |
| P16.2 | 31/31 PASS |
| P16.1 | 25/25 PASS |
| Final P16 aggregate | 196/196 PASS |
| Frozen P15 aggregate | 428/428 PASS |
| Frozen P14 aggregate | 330/330 PASS |
| Native profile | 7/7 PASS |
| Authority coexistence | PASS: exact identities/grant; wrong principal/capability/resource denial; authorized RuntimeEngine execution; transactional denial |

All required commands use `python -X utf8 -B`. The authorized RuntimeEngine run
is confined to the unchanged frozen authority smoke; P16.6 triggers none.
The unchanged checkout T3 smoke failure above remains separately documented.

## Preservation and exact Git state

Only these three paths are added:
`apexforge/tooling/vscode_distribution.py`,
`apexforge/p16_6_vscode_distribution_packaging_test.py`,
`docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md`.

All fifteen incoming hashes remain identical. Branch/HEAD/P15 branch/tag remain
the baseline refs. Tracked and staged diffs are empty; all eighteen intended
P16 candidates remain untracked. No ignored/generated VSIX/node/build residue.
No staging, commit, tag, push, installation, publication, P16.7 work or frozen
predecessor edit. Exact final status follows:

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/p16_2_release_versioning_compatibility_test.py
?? apexforge/p16_3_reproducible_release_build_test.py
?? apexforge/p16_4_release_manifest_provenance_test.py
?? apexforge/p16_5_python_distribution_packaging_test.py
?? apexforge/p16_6_vscode_distribution_packaging_test.py
?? apexforge/tooling/python_distribution.py
?? apexforge/tooling/release_architecture.py
?? apexforge/tooling/release_build.py
?? apexforge/tooling/release_manifest.py
?? apexforge/tooling/release_versioning.py
?? apexforge/tooling/vscode_distribution.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
?? docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
?? docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
?? docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
?? docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
?? docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md
```

## Boundary and required markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_6_REDEFINES_CORE_SEMANTICS=False
P16_6_REDEFINES_EXISTING_VSCODE_PACKAGING=False
P16_6_VSCODE_VERSION_DOMAIN_DISTINCT=True
P16_6_DISTRIBUTION_EXACT_RELEASE_BOUND=True
P16_6_PUBLISHER_METADATA_AUTHENTICATES=False
P16_6_METADATA_REPOSITORY_DERIVED=True
P16_6_DYNAMIC_VERSION_FABRICATION=False
P16_6_VSCODE_ENGINE_REQUIREMENT_CHANGED=False
P16_6_DUPLICATE_VSIX_PACKAGER_ADDED=False
P16_6_VSIX_EVIDENCE_BYTE_BACKED=False
P16_6_VSIX_LOCAL_BUILD_AVAILABLE=False
P16_6_ONLY_VSCODE_PACKAGING_TOOLCHAIN=True
P16_6_ARBITRARY_COMMAND_EXECUTION=False
P16_6_AUTOMATIC_DEPENDENCY_INSTALL=False
P16_6_PUBLIC_NETWORK_REQUIRED=False
P16_6_VSIX_ARCHIVE_PATHS_SAFE=True
P16_6_SOURCE_VSIX_BYTE_CONTINUITY=True
P16_6_EXTENSION_CODE_EXECUTED=False
P16_6_LANGUAGE_SERVER_EXECUTED=False
P16_6_REDEFINES_EDITOR_SEMANTICS=False
P16_6_GENERATED_RESIDUE_PACKAGED=False
P16_6_RAW_BYTE_REPRODUCIBILITY_CLAIM_EVIDENCE_BASED=True
P16_6_REDEFINES_RELEASE_ARCHITECTURE=False
P16_6_BUILD_GRANTS_COMPATIBILITY=False
P16_6_REDEFINES_VERSION_POLICY=False
P16_6_REDEFINES_GENERIC_BUILD=False
P16_6_REDEFINES_RELEASE_MANIFEST=False
P16_6_REDEFINES_PYTHON_DISTRIBUTION=False
P16_6_GLOBAL_EXTENSION_INSTALLATION_PERFORMED=False
P16_6_MARKETPLACE_PUBLICATION_PERFORMED=False
P16_6_CREDENTIAL_ACQUISITION=False
P16_6_ARTIFACT_SIGNING_IMPLEMENTED=False
P16_6_CRYPTO_TRUST_FABRICATED=False
P16_6_VALID_VSIX_GRANTS_TRUST=False
P16_6_VSIX_GRANTS_AUTHORITY=False
P16_6_PACKAGE_EVIDENCE_DETERMINISTIC=True
CRYPTO_PROVIDER_UNAVAILABLE
P16_5_WHEEL_LOCAL_BUILD_AVAILABLE=False
P16_5_SDIST_CONTENT_REPRODUCIBLE=True
P16_5_SDIST_RAW_BYTES_REPRODUCIBLE=False
P16_VSCODE_DISTRIBUTION_MODEL=PASS
P16_VSCODE_EXTENSION_METADATA=PASS
P16_VSCODE_VERSION_BINDING=PASS
P16_VSCODE_VSIX_MODEL=PASS
P16_VSCODE_VSIX_ARCHIVE=PASS
P16_VSCODE_VSIX_CONTENT=PASS
P16_VSCODE_VSIX_SOURCE_CONTINUITY=PASS
P16_VSCODE_VSIX_REPRODUCIBILITY=NOT_EVALUATED_LOCAL_BUILD
P16_VSCODE_FIXTURE_MEMBER_REPRODUCIBILITY=PASS
P16_VSCODE_VSIX_SECURITY=PASS
P16_VSCODE_PACKAGE_RELEASE_BINDING=PASS
P16_VSCODE_PACKAGE_MANIFEST_INTEGRATION=PASS
P16_VSCODE_PACKAGE_TRUST_BOUNDARY=PASS
P16_VSCODE_PACKAGE_AUTHORITY_BOUNDARY=PASS
P16_5_REGRESSION=PASS
P16_4_REGRESSION=PASS
P16_3_REGRESSION=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P16_AGGREGATE_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
P16_6_INCOMING_HASHES_PRESERVED=True
P16_6_CANDIDATES=18
PATCH_MATRIX=PASS
P16_6_READY_FOR_REVIEW=True
```

P16.5 facts are carried forward from its reviewed report and passing unchanged
suite, not re-resolved or modified. `VSIX_EVIDENCE_BYTE_BACKED=False` above concerns
actual local packaging, not the byte-backed inspection fixtures. Contract review
must keep the explicit VSCE environment dependency and checkout byte boundary.
