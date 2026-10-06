# P16.5 — Python Distribution Packaging

## Scope, baseline and limitations

This slice adds the Python-specific distribution identity, frozen metadata
projection, bounded archive inspectors, controlled offline backend runner and
adaptation into the existing P16.3/P16.4 owners. It does not change project
metadata, language/AIR semantics, P14 package identity, release architecture,
version policy, authority or trust. No publication, installation, signing,
CI automation, editor/native packaging or freeze work is performed.

Branch: `p16-1-release-baseline`.
HEAD/P15 freeze: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Tag: `afp-p15.14-freeze`.
Annotated tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
Peeled target: the same P15 commit. Tracked/staged diffs were empty and exactly
twelve intended untracked P16 candidates existed before implementation.

**Actual local sdist construction and inspection pass. Actual wheel construction
is unavailable because the installed toolchain has no wheel command. Independent
sdists have identical contents but different archive bytes/timestamps. No raw
byte-reproducibility PASS or actual wheel-build PASS is claimed.**

## Incoming SHA-256 census

These twelve incoming files are preserved without predecessor modifications:

```text
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
```

## Packaging-owner census

| Evidence/owner | Classification | Treatment |
| --- | --- | --- |
| pyproject.toml project/build-system/setuptools declarations | FROZEN_PROJECT_METADATA | Exact supplied byte digest and TOML projection; unchanged |
| setuptools package discovery and sdist/wheel backend hooks | REUSE | Existing packaging owner determines package content |
| .gitignore and .gitattributes | REFERENCE_ONLY | Existing cache/build exclusions and conformance LF policy unchanged |
| P10 project/scaffold helpers | REFERENCE_ONLY | Project/scaffold artifacts are not Python distribution owners |
| Existing Python build frontend | ENVIRONMENT_DEPENDENCY | build is only a namespace; python -m build cannot run |
| Setuptools 65.5.0 | REUSE / ENVIRONMENT_DEPENDENCY | Already-installed backend meets setuptools>=61; no installation |
| wheel module/command | ENVIRONMENT_DEPENDENCY | Missing; PYTHON_BUILD_ENVIRONMENT_DEPENDENCY retained |
| PythonProjectMetadata / PythonDistributionIdentity / archive inspectors | PYTHON_PACKAGING_EXTENSION_POINT | New bounded Python release contract only |
| P16.1 release identity, target and artifact descriptor | REUSE | Exact Python descriptor and current P15 baseline |
| P16.2 version-domain/compatibility policy | REFERENCE_ONLY | Packaging never grants compatibility |
| P16.3 generic build artifact, recipe and digest | REUSE | COPY_BYTES adapter preserves existing generic evidence semantics and bounds |
| P16.4 checksums, provenance and manifest | REUSE | Exact owner evidence; no second manifest format |
| P14 package/artifact/manifest/trust contracts | REFERENCE_ONLY | Python distribution remains distinct from a P14 package |
| Installation/update/rollback | DEFER_TO_P16_9 | No package installation or runtime validation |
| Publication/release CI | DEFER_TO_P16_10 | No uploads, GitHub Release or publication tooling |
| Signing/authentication | DEFER_TO_P16_11 | CRYPTO_PROVIDER_UNAVAILABLE |

Existing release_build.py, release_architecture.py and release_manifest.py were
inspected, along with their focused tests and P16 predecessor reports. Frozen
P14 identity/artifact/trust owners remain the same owners inspected in P16.4.
No mature Python wheel/sdist release helper was found to duplicate.

## Exact repository metadata

pyproject.toml SHA-256:
`68934BACB869FCACB4B90F7E37173C891DEBECBE9A0F7FAAF24F2CAF95D9044E`.
The frozen Git blob and working metadata bytes have the same digest.

```toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "apexforge-language"
version = "10.1.3"
description = "ApexForge language, runtime, and project tooling"
requires-python = ">=3.9"
dependencies = []

[project.scripts]
apexforge = "tooling.cli:main"

[tool.setuptools]
package-dir = {"" = "apexforge"}
include-package-data = false

[tool.setuptools.packages.find]
where = ["apexforge"]
```

There is no declared readme, license, optional-dependency or package-data field,
and no dynamic version declaration. Missing declarations remain missing.
The backend's generated sdist bookkeeping is not treated as a declaration of
license, authorship or trust. No version, dependency, package discovery, entry
point, runtime requirement, backend or Git configuration was rewritten.

PythonProjectMetadata holds exact supplied pyproject bytes and rejects a changed
profile digest. Its projection is derived by the standard TOML reader. On a host
without tomllib, inspection explicitly reports
PYTHON_METADATA_ENVIRONMENT_DEPENDENCY; no parser dependency is installed.
This environment limitation does not change the distribution's declared
Requires-Python >=3.9 or certify execution on all such interpreters.

## Distribution identity and version continuity

PythonDistributionIdentity binds the normalized name apexforge-language,
Python project version 10.1.3, exact project-metadata fingerprint, exact
ReleaseIdentity and P15 baseline, and its own packaging contract domain
apexforge.python-distribution-identity/v1.

The development evidence release uses explicitly declared version
declared-release-16. It is not the Python package version and not a production
release/version decision. A changed release re-identifies the distribution;
a Python version/name inconsistent with the frozen metadata is rejected.
Nothing derives a version from Git, the clock, branch or environment.

All identity/evidence records are frozen. Exact-type checks reject hostile
caller objects before invoking their methods. SHA-256 fingerprints follow
existing domain-separated CanonicalModel conventions.

## Wheel contract and inspection

The current unsigned pure-Python profile expects
apexforge_language-10.1.3-py3-none-any.whl. Inspection requires valid bounded ZIP
data, the exact dist-info directory, METADATA, WHEEL, RECORD, entry_points.txt and
mandatory tooling/__init__.py and tooling/cli.py source modules.

METADATA must match name, version, summary and Requires-Python exactly, without
duplicate identity headers or unexpected dependencies/extras. WHEEL must describe
Wheel-Version 1.0, Root-Is-Purelib true and Tag py3-none-any. The console entry
point must remain apexforge = tooling.cli:main.

RECORD is parsed as bounded UTF-8 CSV. Every archive file must have exactly one
row. Every non-RECORD row must carry matching URL-safe unpadded SHA-256 and exact
length; RECORD itself has empty hash/size. Hash/length/coverage/duplicate
mismatches fail closed. This is integrity evidence only, not publisher
authentication or a signature.

The implementation follows the
[PyPA wheel specification](https://packaging.python.org/en/latest/specifications/binary-distribution-format/)
for the represented filename, metadata and RECORD structure. Its supported
inspection profile is deliberately narrower than a general wheel installer:
no compiled-platform wheel, optional signed RECORD envelope or installation
scheme is introduced.

Wheel fixtures independently exercise metadata, RECORD, safety and evidence
integration. They are explicitly test-created archive bytes, not a claim that
the host produced an ApexForge wheel.

## Sdist contract, source selection and archive safety

The represented sdist uses apexforge-language-10.1.3.tar.gz (the normalized
underscore spelling is also accepted). The archive must have one exact root
matching its filename, PKG-INFO, exact pyproject bytes and mandatory package
sources. PKG-INFO is checked against the same immutable metadata identity.

The data-only tar inspection follows the represented
[PyPA source distribution structure](https://packaging.python.org/en/latest/specifications/source-distribution-format/).
Nothing is extracted to disk during inspection. Gzip expansion is bounded before
tar/PAX parsing. Metadata text must be bounded UTF-8 without NUL; timestamps must
be finite and nonnegative. Symlinks, hardlinks, device/special entries, malformed
archives, absolute/drive-qualified paths, backslashes, traversal, duplicates,
portable case aliases and file/directory conflicts fail closed.

Prohibited residue includes .git, pyc/pyo, caches, environments, IDE caches,
previous wheels/sdists and credential-like paths. The frozen logical PackagePath
owner classifies malformed dot paths (including .env/.git) as invalid paths;
portable names such as secrets are rejected as residue.

Backend-generated egg-info and setup.cfg within a source distribution are
intentional sdist metadata, not accidental worktree cache inclusion. Caller
source projections cannot supply root setup.py/setup.cfg, their case variants,
egg-info, previous distributions or source path aliases.

Optional explicit expected-source digest tuples verify exact Python file
inventory and bytes. No filesystem discovery populates these expectations.
The local acceptance projection included pyproject plus 769 frozen Python files:
770 input records, 7,577,027 bytes. The packaging metadata selected 344 nested
package modules, all of which matched archive paths and content digests. Root
standalone files not selected by package discovery were not silently added.
Distribution content ownership remains PYTHON_PACKAGING_METADATA.

This is packaging evidence, not runtime qualification: omitted non-Python data
or standalone modules must not be silently assumed available after installation.
No new runtime/upgrade compatibility promise follows from archive validity.

## Controlled local backend execution

Python 3.11.9 and setuptools 65.5.0 were inspected. python -m build --version
failed because build is a namespace with no __main__. Neither wheel nor the
setuptools bdist_wheel command is installed. No pip install, dependency restore
or network access was attempted.

The repository-supported fallback invokes only the frozen setuptools.build_meta
build_sdist/build_wheel hook through a fixed Python argv:
the current interpreter, -I, -B, -c and one constant trusted backend script.
There is no caller command/callback API, shell interpolation, publication client,
editor/native toolchain or project-code import. The working source root is
explicit and disposable; timeout is 120 seconds and stdout/stderr are captured.
Outputs must be one regular non-symlink bounded artifact of the requested format.

The child environment is stripped, with PIP_NO_INDEX and no automatic dependency
installation. Empty disposable HOME/USERPROFILE and TEMP/TMP directories prevent
reading user packaging configuration. On Windows only the non-secret SystemRoot
loader setting is additionally preserved: omitting it caused WinError 10106.
Omitting a home caused the backend's configuration reader to fail. These
operational paths do not enter canonical artifact or distribution identity.
No credential variable or store is queried and the parent environment is unchanged.

The acceptance harness used git archive solely to read the exact frozen commit,
then supplied explicit bytes to the runner. Production does not invoke Git or
discover the worktree. Builds never include untracked P16 candidates. All
temporary source, backend build/egg-info/output products are cleaned; no package
is globally installed, imported, executed, signed or published.

## Actual local evidence and independent comparison

A real local wheel attempt fails with PYTHON_BUILD_ENVIRONMENT_DEPENDENCY.
It creates no wheel evidence and no local wheel metadata PASS is claimed.

Two independently projected and built sdists were inspected successfully:

| Evidence | Build one | Build two |
| --- | --- | --- |
| Filename | apexforge-language-10.1.3.tar.gz | same |
| Byte length | 574,059 | 574,074 |
| SHA-256 | 29B777737E961DA21C02ED90E08543B838457DB7B01D14E98561270BE61AC892 | 1A28432163664A1CC816D31BF4CCB8859BF694FCEB0BA5F8DBF7495CDC3F5576 |
| Evidence fingerprint | B2C03547198BEAE256D726247FA9EA6CAD2530764529968C38F7D0773163238D | 491385855B96765EA8E590948A9AE1A8F9FDF54EDEDD606199817AC26BC89570 |
| Inventory | 352 files | identical contents |
| Expected source modules | 344 exact source digests | same |

PythonReproducibilityEvidence reports content=PASS, raw_bytes=MISMATCH and
timestamp_metadata_equal=False. The retained classification is
PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP. The runner intentionally does not alter
the backend archive timestamps or disguise different raw bytes. Later build
hardening can address that fact; signing, publication and acceptance cannot be
inferred from content equality.

Local outputs were measured and verified while bytes existed, then discarded
with their controlled temporary directories. These are actual local build
measurements, not retained production release packages.

## P16.1–P16.4 continuity

The exact Python descriptor binds release, P15 baseline, role, target, filename,
format and Python surface version. Packaging grants no compatibility and does
not reinterpret P16.2 policy.

generic_evidence adapts inspected actual bytes through P16.3's existing
COPY_BYTES recipe/input/artifact contracts. The input source reference binds
the exact PythonPackageEvidence fingerprint; provenance additionally binds the
PythonDistributionIdentity fingerprint. Existing 1 MiB generic artifact bounds
remain unchanged (the actual 574,059-byte sdist fits). Larger future artifacts
explicitly report PYTHON_GENERIC_BUILD_SIZE_UNSUPPORTED rather than weakening
the owning contract or fabricating an artifact.

For the actual first sdist, the adapter and P16.4 checksum/provenance construction
produce these exact owner references:

```text
RECIPE=902CBA0F6A0A4999C784F22E76C79F88F775B15524BEDB6D77CA31C6E2A35843
ARTIFACT=2784C764D1DFE2BC43D532AAA55764D18A56087300D252B0722F35F748D5D35C
CHECKSUM=06499574C569CC2D9D81954EA4EAEAECAEEBC234F235E9D67173D3E1C27C1187
SCOPED_MANIFEST=A2225E38E85ED156D62367C81A585A846BE92E70A76E3EF37927B43D51C525CC
SCOPED_MANIFEST_STATUS=COMPLETE
```

That manifest scope contains only the supplied sdist descriptor. It is not a
complete release matrix or approval of the unavailable wheel. P16.4 owns all
checksum/provenance/completeness semantics; no competing manifest is created.
Unit fixtures also prove wheel evidence can feed the same owners without a
claim of actual host wheel construction.

## Determinism, bounds and static security audit

Equivalent archive inspection yields identical sorted inventory, metadata,
checksums, references, timestamps-as-observed and diagnostics. Content
comparison deliberately distinguishes this from reproducible raw archive bytes.

Archives are limited to 16 MiB compressed; expanded members to 64 MiB total,
8 MiB per member and 8,192 members. Metadata is capped at 256 KiB. Tar expansion
is bounded before extended-header parsing. Sources are explicit, bounded
tuples, not recursive discovery. Bytes are never pickle-loaded, executed or
imported. Duplicate CSV/config/metadata identities fail closed with fixed codes.

AST audit finds exactly one subprocess invocation, the fixed Python backend
command. It forbids eval/exec/dynamic import, extraction, shell launch, credential
lookup and networking/publication libraries. Dynamic traps prove inspection
never invokes the toolchain. Tests verify empty temporary cleanup, offline argv,
minimal child environment, non-symlink outputs, hostile object rejection and
case-alias protections. A trusted packaging backend is allowed to run; the built
ApexForge package is not.

CRYPTO_PROVIDER_UNAVAILABLE is preserved. Archive validity, RECORD hashes and
SHA-256 equality grant no trust, signing, authentication, runtime authority,
installation safety, compatibility or publisher/organization identity.

## Patch Matrix and dispositions

| Finding | Classification | Owning patch / disposition |
| --- | --- | --- |
| .env expected residue code versus frozen PackagePath's invalid-path code | PYTHON_ARCHIVE_SECURITY_GAP | P16.5 test oracle aligned to inspected path owner; denial assertion retained |
| Unsafe source path diagnostic lacked build-input context | PYTHON_PACKAGE_SECURITY_BOUNDARY_GAP | P16.5 runner reports structured source-input rejection |
| Windows loader/home missing under stripped environment | PYTHON_BUILD_ENVIRONMENT_DEPENDENCY | Preserve non-secret SystemRoot and supply empty disposable home/scratch; no inherited credentials |
| Root setup script or source collision through case variants | PYTHON_PACKAGE_SECURITY_BOUNDARY_GAP | Reject case aliases and case-insensitive setup names before executing the backend |
| Linked output/nonfinite timestamp/path conflict | PYTHON_ARCHIVE_SECURITY_GAP | Local output/archive guards and focused tests |
| Actual wheel toolchain absent | PYTHON_BUILD_ENVIRONMENT_DEPENDENCY | Retained explicit host limitation; no dependency install or artifact fabrication |
| Raw sdists differ, contents equal | PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP | Retained measured gap; no raw PASS claimed; future hardening evidence |

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

All corrections are confined to new P16.5 files. No P16.1–P16.4 or frozen
predecessor contract was patched and no safety assertion was weakened. Matrix
PASS/readiness means this bounded contract and its evidence are reviewable;
it does not resolve the explicitly unavailable wheel or raw-byte gap, and does
not assert complete release packaging or release-candidate readiness.

## Final validation and preservation

| Check | Result |
| --- | --- |
| python -X utf8 -B apexforge/p16_5_python_distribution_packaging_test.py | 35/35 PASS |
| python -X utf8 -B apexforge/p16_4_release_manifest_provenance_test.py | 41/41 PASS |
| python -X utf8 -B apexforge/p16_3_reproducible_release_build_test.py | 31/31 PASS |
| python -X utf8 -B apexforge/p16_2_release_versioning_compatibility_test.py | 31/31 PASS |
| python -X utf8 -B apexforge/p16_1_release_architecture_contract_test.py | 25/25 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p16_*_test.py | 163/163 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py | 428/428 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| python -X utf8 -B apexforge/authority_consolidation_smoke_test.py | PASS |
| Actual frozen-source local sdist build/inspection/integration | PASS |
| Actual frozen-source local wheel construction | PYTHON_BUILD_ENVIRONMENT_DEPENDENCY |
| Independent sdist content comparison | PASS |
| Independent sdist raw-byte comparison | PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP |

The authority smoke retains canonical identity/exact grant PASS; wrong
principal/capability/resource denial PASS; authorized RuntimeEngine execution
PASS; transactional denial PASS. That unchanged frozen test alone exercises
runtime execution; P16.5 never invokes RuntimeEngine.

Final parser review additionally classified PYTHON_PACKAGE_SECURITY_BOUNDARY_GAP:
public data helpers require exact plain argument types before accessing caller
methods, and direct RECORD ingestion enforces per-member/total byte bounds.
Hostile object and oversized ingestion tests pass. The final focused/aggregate
runs include these corrections.

All twelve incoming hashes match the initial census. P15 branch, tag object,
peeled target, current branch and HEAD remain unchanged. Tracked and staged
diffs are empty; no generated or ignored worktree files were introduced. Only
the three intended P16.5 paths were added. No P16.6 work, stage, commit, tag,
push, publication or global installation occurred.

Exact final Git status:

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/p16_2_release_versioning_compatibility_test.py
?? apexforge/p16_3_reproducible_release_build_test.py
?? apexforge/p16_4_release_manifest_provenance_test.py
?? apexforge/p16_5_python_distribution_packaging_test.py
?? apexforge/tooling/python_distribution.py
?? apexforge/tooling/release_architecture.py
?? apexforge/tooling/release_build.py
?? apexforge/tooling/release_manifest.py
?? apexforge/tooling/release_versioning.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
?? docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
?? docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
?? docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
?? docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
```

## Evidence-supported markers

Wheel availability/metadata markers below describe the actual frozen-source host
build, not test-created fixture bytes. False means not demonstrated because no
host-built wheel exists; it does not describe a detected metadata mismatch.
Wheel model/RECORD PASS means the data-only contract is tested with fixtures.
Reproducibility PASS refers to normalized content evidence, not raw archive bytes.

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_5_INCOMING_CANDIDATES=12
P16_5_ALL_INCOMING_HASHES_PRESERVED=True
P16_5_REDEFINES_CORE_SEMANTICS=False
P16_5_PYTHON_VERSION_DOMAIN_DISTINCT=True
P16_5_DISTRIBUTION_EXACT_RELEASE_BOUND=True
P16_5_METADATA_REPOSITORY_DERIVED=True
P16_5_DYNAMIC_VERSION_FABRICATION=False
P16_5_PYTHON_RUNTIME_REQUIREMENT_CHANGED=False
P16_5_BUILD_BACKEND_CHANGED=False
P16_5_WHEEL_EVIDENCE_BYTE_BACKED=False
P16_5_SDIST_EVIDENCE_BYTE_BACKED=True
P16_5_ONLY_PYTHON_PACKAGING_TOOLCHAIN=True
P16_5_ARBITRARY_COMMAND_EXECUTION=False
P16_5_AUTOMATIC_DEPENDENCY_INSTALL=False
P16_5_PUBLIC_NETWORK_REQUIRED=False
P16_5_GENERATED_RESIDUE_PACKAGED=False
P16_5_PACKAGE_CONTENT_OWNER=PYTHON_PACKAGING_METADATA
P16_5_WHEEL_CODE_EXECUTED=False
P16_5_WHEEL_RECORD_GRANTS_TRUST=False
P16_5_SDIST_PATH_TRAVERSAL_REJECTED=True
P16_5_ARCHIVE_PATHS_SAFE=True
P16_5_WHEEL_METADATA_EXACT=False
P16_5_SDIST_METADATA_EXACT=True
P16_5_REDEFINES_RELEASE_ARCHITECTURE=False
P16_5_BUILD_GRANTS_COMPATIBILITY=False
P16_5_REDEFINES_VERSION_POLICY=False
P16_5_REDEFINES_GENERIC_BUILD=False
P16_5_REDEFINES_RELEASE_MANIFEST=False
P16_5_RAW_BYTE_REPRODUCIBILITY_CLAIM_EVIDENCE_BASED=True
P16_5_WORKTREE_BUILD_RESIDUE=False
P16_5_GLOBAL_INSTALLATION_PERFORMED=False
P16_5_PUBLICATION_PERFORMED=False
P16_5_CREDENTIAL_ACQUISITION=False
P16_5_ARTIFACT_SIGNING_IMPLEMENTED=False
P16_5_CRYPTO_TRUST_FABRICATED=False
P16_5_VALID_PACKAGE_GRANTS_TRUST=False
P16_5_PACKAGE_GRANTS_AUTHORITY=False
P16_5_BUILT_PACKAGE_CODE_EXECUTED=False
P16_5_PACKAGE_EVIDENCE_DETERMINISTIC=True
CRYPTO_PROVIDER_UNAVAILABLE
P16_PYTHON_DISTRIBUTION_MODEL=PASS
P16_PYTHON_PROJECT_METADATA=PASS
P16_PYTHON_VERSION_BINDING=PASS
P16_PYTHON_BUILD_BACKEND=PASS
P16_PYTHON_WHEEL_MODEL=PASS
P16_PYTHON_WHEEL_METADATA=NOT_DEMONSTRATED_LOCAL_BUILD
P16_PYTHON_WHEEL_RECORD=PASS
P16_PYTHON_SDIST_MODEL=PASS
P16_PYTHON_ARCHIVE_SECURITY=PASS
P16_PYTHON_PACKAGE_CONTENT=PASS
P16_PYTHON_PACKAGE_REPRODUCIBILITY=PASS
P16_PYTHON_RAW_BYTE_REPRODUCIBILITY=PYTHON_PACKAGE_BYTE_REPRODUCIBILITY_GAP
P16_PYTHON_LOCAL_WHEEL_BUILD=PYTHON_BUILD_ENVIRONMENT_DEPENDENCY
P16_PYTHON_PACKAGE_RELEASE_BINDING=PASS
P16_PYTHON_PACKAGE_MANIFEST_INTEGRATION=PASS
P16_PYTHON_PACKAGE_TRUST_BOUNDARY=PASS
P16_PYTHON_PACKAGE_AUTHORITY_BOUNDARY=PASS
P16_PYTHON_PACKAGE_SECURITY_BOUNDARY=PASS
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
P16_5_READY_FOR_REVIEW=True
```

