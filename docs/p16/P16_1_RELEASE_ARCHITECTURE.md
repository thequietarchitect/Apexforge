# P16.1 Release Architecture, Artifact Matrix & Distribution Contract Foundation

## Canonical phase authority and scope

**P16: Release Engineering & Distribution.** The preceding repository discovery
found no canonical P16 roadmap. Project-owner direction for this assignment
establishes the following canonical roadmap; this document records that authority.
P16.1 alone is implemented. P16.2–P16.13 remain unimplemented.

A release is a reproducible, provenance-bound projection of already-frozen
ApexForge artifacts; release engineering may package, verify, distribute, install,
upgrade and recover those artifacts, but may not redefine semantic identity.

| Slice | Canonical title | State |
| --- | --- | --- |
| P16.1 | Release Architecture, Artifact Matrix & Distribution Contract Foundation | Foundation for review |
| P16.2 | Versioning, Compatibility & Upgrade Policy | Deferred; not implemented |
| P16.3 | Reproducible Release Build & Artifact Assembly | Deferred; not implemented |
| P16.4 | Release Manifest, Checksums & Provenance Bundle | Deferred; not implemented |
| P16.5 | Python Distribution Packaging | Deferred; not implemented |
| P16.6 | VS Code Extension Release Packaging | Deferred; not implemented |
| P16.7 | Visual Studio Extension Release Packaging | Deferred; not implemented |
| P16.8 | Native win-x64 Release Packaging | Deferred; not implemented |
| P16.9 | Installation, Upgrade & Rollback Contracts | Deferred; not implemented |
| P16.10 | CI Release Pipeline & Publication Dry Run | Deferred; not implemented |
| P16.11 | Release Security, Signing & Verification Integration | Deferred; not implemented |
| P16.12 | Release Candidate Acceptance Matrix | Deferred; not implemented |
| P16.13 | Release Closure & Freeze | Deferred; not implemented |

No direct architectural contradiction required changing the owner's roadmap.
Later packaging slices compose existing owners; they do not replace them.

## Frozen baseline and preservation

Branch: `p16-1-release-baseline`.
HEAD / P15 freeze: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Parent: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Tag: `afp-p15.14-freeze`.
Annotated tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
Peeled target: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
P15 branch remains at that commit. Initial worktree, staged and tracked diffs empty.
No predecessor file is edited.

## Ownership census

| Evidence / owner | Classification | Release use |
| --- | --- | --- |
| pyproject.toml: setuptools, apexforge-language 10.1.3, Python >=3.9, no dependencies, tooling.cli entry point | RELEASE_EXTENSION_POINT; REFERENCE_ONLY | Python sdist/wheel declaration; no build or package-index publication |
| P15.1 CanonicalModel | REUSE | Existing deterministic canonical JSON / domain-separated fingerprint utility only; no new domain kind |
| P14 PackageCoordinate, PackageContentIdentity, PackagePath, CanonicalReference | FROZEN_PACKAGE_CONTRACT; REUSE | Exact package identity/content and passive lineage; safe logical filename; no replacement package identity |
| P14 artifact/trust/provenance and compatibility contracts | FROZEN_PACKAGE_CONTRACT; REFERENCE_ONLY | Integrity is not trust; exact supplied evidence; comparison is bounded and version is not compatibility proof |
| P12 native_execution_contract.PROFILE and P14 package_artifacts | FROZEN_NATIVE_CONTRACT; REUSE for PROFILE; REFERENCE_ONLY for packaging | Exact win-x64 i64-literal-state-set/v1 only; no admission/build/dispatch invocation |
| P10 tooling.vscode_package; package.json/CHANGELOG.md | FROZEN_EDITOR_CONTRACT; REFERENCE_ONLY | Existing @vscode/vsce local VSIX contract, version 0.1.0, VS Code ^1.85.0; no Marketplace promise |
| P10 Visual Studio packaging/integration/VSIX manifest | FROZEN_EDITOR_CONTRACT; REFERENCE_ONLY | Visual Studio 17+ Community amd64/arm64 extension targets, 0.1.0; no broad native support |
| run_apexforge_regressions.ps1 and existing focused/discovery suites | REFERENCE_ONLY | Existing regression script accepts all/p7/p8/p9/p10; not release CI |
| P10–P15 closure conventions | REFERENCE_ONLY | Exact source inventory, regression, parent, annotated-tag/remote identity and separate signing evidence |
| Release-version alignment, compatibility policy | DEFER_TO_P16_2 | No version change, unified version choice or compatibility guarantee |
| Artifact assembly and final bytes/checksums | DEFER_TO_P16_3 | Descriptors only; P16.4 owns later manifest/checksum/provenance bundle |
| Signing and authentication | DEFER_TO_P16_11 | CRYPTO_PROVIDER_UNAVAILABLE remains; no keys or signatures fabricated |
| Installation/update/recovery concepts | RELEASE_EXTENSION_POINT; REFERENCE_ONLY | Existing local editor install audit is preserved; release install/upgrade/rollback deferred to P16.9 |

The guessed native profile filename was absent; inspected the actual
native_execution_contract.py owner after repository search. No frozen patch was
needed. Compiler/language, AIR, authority, package and platform owners remain
unchanged. No release CI workflow or general installer/rollback owner was found
in the preceding discovery; their later roadmap slices are explicit extension points.

## Immutable release contract

FrozenSourceBaseline binds caller-supplied exact commit, tag name, annotated
tag object and parent. P15_BASELINE is the exact frozen record above.
Constructing a record does not inspect Git or authenticate the supplied reference.
Other explicitly supplied baseline records are representable; changing any of
their fields changes dependent release and descriptor fingerprints. The current
P16 baseline is P15_BASELINE; a different record is not silently equivalent.

ReleaseIdentity binds an explicit caller-supplied opaque version, release
identifier, declaration-only DEVELOPMENT/RELEASE_CANDIDATE/STABLE channel and
baseline. No wall clock, environment or metadata discovery sets the version.
The fixture version declared-review-1 is an architecture test label, not a selected
production version. Python 10.1.3 and editor 0.1.0 are independently retained in
surface_version. ExactVersion remains P14's numeric package version owner.
No release precedence/range/upgrade policy is implemented.

ReleaseTarget allows only python, vscode, visual-studio and native-win-x64.
Native target requires the imported frozen PROFILE exactly. The Visual Studio
arm64 declaration concerns the extension installation architecture, not an
ApexForge native arm64 backend. Python OS release qualification is deferred;
metadata alone does not certify every operating system.

ReleaseArtifactIdentity is a caller-supplied logical name scoped by its enclosing
release descriptor/matrix. It is not a byte-content identity. Exact baseline,
target, role, format, filename, surface version, availability, package evidence,
references and provenance are all bound by the descriptor fingerprint.

ReleaseArtifactDescriptor uses a bounded target-specific role/format pair.
A filename is a single safe logical PackagePath with a format-compatible suffix,
never a host path. A package coordinate and content identity are both supplied or
both absent. Existing Python/editor metadata has no inferred P14 package mapping;
the optional binding is exercised with an explicit P14 manifest fixture.
No package digest is fabricated from missing release bytes.

ReleaseArtifactMatrix canonically sorts bounded immutable supplied tuples,
rejects empty/mixed-release matrices, duplicate artifact IDs/filenames and dangling
references. Artifact references identify members of the exact matrix, whose
fingerprint binds all their descriptor contents. They are structural references,
not build dependencies, ordering/scheduling semantics or authority handoffs.

## Supported artifact matrix

SUPPORTED means an existing packaging surface contract, not produced release bytes.
PLANNED means the release assembly is deferred. UNAVAILABLE remains a valid explicit
state for any listed surface. Unknown targets are rejected, never advertised.

| Target | Role / formats | Packaging owner | Current declaration | Production owner | Security requirement |
| --- | --- | --- | --- | --- | --- |
| Python | PYTHON_DISTRIBUTION; wheel/sdist | pyproject.toml / setuptools | SUPPORTED metadata; 10.1.3 | P16.5 after P16.3 | Authentication/signing unresolved; P16.11 |
| VS Code | VSCODE_EXTENSION; vsix | tooling.vscode_package | SUPPORTED local packaging; 0.1.0 | P16.6 | No Marketplace identity authentication inferred; P16.11 |
| Visual Studio | VISUAL_STUDIO_EXTENSION; vsix | tooling.visualstudio_packaging | SUPPORTED local VSIX audit; 0.1.0 | P16.7 | No production signing claim; P16.11 |
| Native win-x64 | NATIVE_COMPONENT; dll | P14 package_artifacts and frozen P12 build contracts | PLANNED release assembly; exact PROFILE | P16.8 | Cryptographic trust unavailable; P16.11 |

Manifest/checksum/provenance bundle roles are deferred to P16.4 rather than
manufacturing unsupported bytes in P16.1. Documentation distribution can later be
defined with exact assembly evidence. No installer artifact is declared now.

## Provenance, diagnostics and determinism

Each descriptor retains baseline -> release -> target -> artifact declaration.
Optional exact P14 coordinate/content and canonical provenance references are
preserved without reidentification. Canonical JSON uses the reused owner utility;
each new model has its own apexforge.release-*/v1 fingerprint domain. Input order
does not affect descriptor references/provenance or matrix fingerprints.

Structured failure codes include RELEASE_VERSION_REQUIRED, RELEASE_BASELINE_INVALID,
RELEASE_TARGET_UNSUPPORTED, RELEASE_NATIVE_PROFILE_INVALID,
RELEASE_ARTIFACT_ROLE_FORMAT_INVALID, RELEASE_FILENAME_INVALID,
RELEASE_AVAILABILITY_INVALID, RELEASE_PACKAGE_BINDING_INVALID,
RELEASE_REFERENCE_INVALID/DANGLING, RELEASE_PROVENANCE_INVALID,
RELEASE_MATRIX_BASELINE_MISMATCH, RELEASE_ARTIFACT_DUPLICATE and
RELEASE_FILENAME_DUPLICATE. Codes, not exception prose, identify diagnostics.
No canonical dependence on time, hostname, path, PID, randomness, environment or
network state.

## Security, authority and semantic boundaries

A valid descriptor does not establish bytes, trust, signatures, correctness,
safety, publication or installation. record() reports artifact_bytes_exist and
authentication NOT_ESTABLISHED, checksum REQUIRED_AFTER_ARTIFACT_ASSEMBLY,
CRYPTO_PROVIDER_UNAVAILABLE, and grants_authority/grants_trust False.
Channels remain declarations, including STABLE; none perform release promotion.

No build, Git invocation, subprocess, shell, package manager, environment mutation,
credential discovery, filesystem discovery, network, publication, installer,
rollback or CI engine exists in production code. Side-effecting editor packaging
owners are named as reference strings, never imported/invoked. PROFILE is imported
from its frozen owner but no native admission, lowering or execution function
is called. Static exact dependency/class audit and runtime IO/process/network/
environment sentinels cover the foundation.

```text
RELEASE != LANGUAGE_SEMANTICS
RELEASE != CANONICAL_AIR
RELEASE != PACKAGE_IDENTITY
RELEASE != AUTHORITY
RELEASE != ORGANIZATION
RELEASE_ARTIFACT != SOURCE_IDENTITY
RELEASE_CHANNEL != TRUST_LEVEL
DISTRIBUTION != SEMANTIC_OWNERSHIP
INSTALLATION != AUTHORITY_GRANT
SIGNED_ARTIFACT != CORRECT_ARTIFACT
CHECKSUM != AUTHENTICATION
CHECKSUM != SIGNATURE
NATIVE_RELEASE_TARGET != WHOLE_LANGUAGE_NATIVE_SUPPORT
RELEASE_ARTIFACT_DESCRIPTOR != RELEASE_ARTIFACT_BYTES
RELEASE_PROVENANCE != AUTHENTICATION
EVIDENCE_BEFORE_ATTRIBUTION=True
CANONICAL_SEMANTIC_AUTHORITY=CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE
```

## Validation and Patch Matrix

Focused P16.1: 25/25 PASS, including exact existing metadata and all thirteen
canonical roadmap rows (twelve later slices explicitly deferred).
Commands use python -X utf8 -B; no builds/publication or new runtime workloads.
Frozen P15 aggregate: 428/428 PASS.
Frozen P14 aggregate: 330/330 PASS.
Native profile: 7/7 PASS.
Authority coexistence: canonical identities, exact grant, wrong
principal/capability/resource denial, authorized RuntimeEngine execution and
transactional denied execution PASS. That runtime fixture belongs only to the
unchanged predecessor smoke test, not to P16.1 production behavior.

Executed focused command: python -X utf8 -B
apexforge/p16_1_release_architecture_contract_test.py.
Executed aggregate commands: python -X utf8 -B -m unittest discover -s apexforge
-p p15_*_test.py and -p p14_*_test.py; native and authority checks used the
requested unchanged p12_5_native_profile_contract_test.py and
authority_consolidation_smoke_test.py.

Final preservation audit: branch/HEAD/tag object/peeled P15 tag and P15 branch
remain exact. Tracked and staged diffs empty; no frozen P15/P14/earlier file
changed. Exactly three intended untracked candidates, no generated residue.
No commit, tag, push, publication or P16.2 implementation occurred.

Exact Git status:

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/tooling/release_architecture.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
```

Patch Matrix:
FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

No focused failure or owning-contract defect occurred. P16.2 versioning and P16.3
assembly remain explicitly deferred; crypto/provider integration remains
DEFER_TO_P16_11. No predecessor change or assertion weakening.

One report-update invocation contained an unrelated context line and was rejected
without mutation. Classification: TEST_INVOCATION_DEFECT (documentation patch
invocation). Corrected the context in this report only; no contract patch.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_CANONICAL_SCOPE_FOUND=True
P16_PHASE=RELEASE_ENGINEERING_AND_DISTRIBUTION
P16_1_TITLE=Release Architecture, Artifact Matrix & Distribution Contract Foundation
P16_1_RELEASE_VERSION_EXPLICIT=True
P16_1_VERSION_DOMAINS_DISTINCT=True
P16_1_EXACT_P15_FREEZE_BOUND=True
P16_1_UNSUPPORTED_TARGETS_NOT_ADVERTISED=True
P16_1_UNAVAILABLE_CAPABILITIES_REMAIN_UNAVAILABLE=True
P16_1_RELEASE_MATRIX_DETERMINISTIC=True
P16_1_RELEASE_PROVENANCE_EXPLICIT=True
P16_1_NATIVE_PROFILE_REDEFINED=False
P16_1_RELEASE_CHANNEL_GRANTS_TRUST=False
P16_1_PYTHON_PUBLICATION_PERFORMED=False
P16_1_VSCODE_MARKETPLACE_PUBLICATION_PERFORMED=False
P16_1_VISUAL_STUDIO_PUBLICATION_PERFORMED=False
P16_1_NATIVE_RELEASE_BUILD_PERFORMED=False
P16_1_RELEASE_SIGNING_IMPLEMENTED=False
P16_1_RELEASE_AUTHENTICATION_FABRICATED=False
P16_1_INSTALLATION_PERFORMED=False
P16_1_PUBLICATION_PERFORMED=False
P16_1_RELEASE_CI_IMPLEMENTED=False
P16_1_ROLLBACK_IMPLEMENTED=False
P16_1_NEW_COMPATIBILITY_GUARANTEES_ADDED=False
P16_1_REDEFINES_LANGUAGE_SEMANTICS=False
P16_1_REDEFINES_CANONICAL_AIR=False
P16_1_REDEFINES_PACKAGE_IDENTITY=False
P16_1_REDEFINES_DOMAIN_PLATFORM=False
P16_1_RELEASE_DESCRIPTOR_GRANTS_AUTHORITY=False
P16_1_VALID_RELEASE_DESCRIPTOR_GRANTS_TRUST=False
P16_1_NETWORK_ACCESS=False
P16_1_HOST_COMMAND_EXECUTION=False
P16_1_CREDENTIAL_ACQUISITION=False
P16_1_ARTIFACT_BUILD_EXECUTION=False
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_ARCHITECTURE_MODEL=PASS
P16_RELEASE_IDENTITY=PASS
P16_RELEASE_VERSION_BOUNDARY=PASS
P16_RELEASE_TARGET_MODEL=PASS
P16_RELEASE_ARTIFACT_DESCRIPTOR=PASS
P16_RELEASE_MATRIX=PASS
P16_RELEASE_BASELINE_BINDING=PASS
P16_RELEASE_NATIVE_PROFILE_BOUNDARY=PASS
P16_RELEASE_PROVENANCE=PASS
P16_RELEASE_TRUST_BOUNDARY=PASS
P16_RELEASE_AUTHORITY_BOUNDARY=PASS
P16_RELEASE_CRYPTO_BOUNDARY=PASS
P16_RELEASE_DETERMINISM=PASS
P16_RELEASE_SECURITY_BOUNDARY=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_1_READY_FOR_REVIEW=True
```
