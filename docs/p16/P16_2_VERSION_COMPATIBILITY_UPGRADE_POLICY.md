# P16.2 Versioning, Compatibility & Upgrade Policy

## Frozen baseline and incoming inventory

Branch: `p16-1-release-baseline`.
HEAD / frozen P15 commit: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
P15 annotated tag: `afp-p15.14-freeze`.
Tag object: `d7761c04e4422bfb91d9582275a60912874678f4`.
Peeled target: `c9c5ca186c9d942ce336ac1ebfe1287b16953200`.

Before implementation: exact branch/HEAD/tag matched, exactly the three expected
P16.1 paths were untracked, tracked/staged diffs empty and no generated residue.
Incoming SHA-256 census:

```text
P16_BASELINE=P15_14_FREEZE
P16_2_INCOMING_CANDIDATES=3
P15_REOPENED=False
77C69F98C842CAA3073E0D3CA36C2C042ED1FC97F90BC3A721288B4BB61D72F8  apexforge/p16_1_release_architecture_contract_test.py
5BF82BF285BE9C353D2F853432B3D4059702019CC1FE8E0740EBEC6A23F8F82A  apexforge/tooling/release_architecture.py
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
```

P16.2 adds only its module, focused tests and this report. P16.1's stored
version_policy=DEFER_TO_P16_2 field remains unchanged: P16.2 composes that reviewed
identity contract instead of retroactively altering it. No P16.3/later work.

## Existing owners and classification

| Owner / repository fact | Classification | Policy treatment |
| --- | --- | --- |
| P16.1 ReleaseIdentity, ReleaseTarget, FrozenSourceBaseline | REUSE | Immutable exact identities; opaque explicit release version retained |
| P15.1 CanonicalModel and canonical JSON utility | REUSE | Domain-separated deterministic record fingerprints only |
| P14.1 ExactVersion, PackageCoordinate, manifest schema apexforge.package/v1 | FROZEN_VERSION_CONTRACT; REFERENCE_ONLY | Numeric package triples stay owned by P14; no ranges/precedence inferred |
| P14.2 solver, exact coordinate candidates and deterministic numeric sort keys | FROZEN_VERSION_CONTRACT; REFERENCE_ONLY | Sorting candidates is not selecting newer versions; no release override |
| P14.3 lock/restore exact content and graph binding | FROZEN_VERSION_CONTRACT; REFERENCE_ONLY | No lock refresh, resolve or restoration performed |
| P14.10 compare_packages / CompatibilityReport / MigrationPlan | FROZEN_PACKAGE_COMPATIBILITY_CONTRACT; REFERENCE_ONLY | Existing structural classifications, unknown behavior and passive migration semantics preserved |
| CanonicalReference | REUSE | Caller-supplied passive evidence/provenance, not authentication |
| pyproject.toml | REFERENCE_ONLY | apexforge-language 10.1.3; Python >=3.9 unchanged |
| VS Code package.json / P10 packaging | REFERENCE_ONLY | Extension 0.1.0, engine ^1.85.0; no Marketplace promise |
| Visual Studio VSIX manifest / P10 packaging | REFERENCE_ONLY | Extension 0.1.0, Community 17+, amd64/arm64 editor installation declarations |
| native_execution_contract.PROFILE | FROZEN_VERSION_CONTRACT; REUSE through P16.1 | apexforge.native.win-x64.i64-literal-state-set/v1 only |
| language/compiler.py / air/types.py | FROZEN_VERSION_CONTRACT; REFERENCE_ONLY | Compiler emits owner AIR_VERSION=0.2; not a new release/language semantics version |
| CLI P10_T1_CLI_VERSION=10-T1.2 and contract/schema constants | REFERENCE_ONLY | Distinct surface/component versions, not unified release version |
| New exact release-pair compatibility declarations / upgrade assessment | RELEASE_POLICY_EXTENSION_POINT | P16.2-owned passive policy |
| Existing local editor install/audit routines | REFERENCE_ONLY; DEFER_TO_P16_9 | No general release update/rollback execution adopted |
| Builds, checksum/provenance bundles and packaging | DEFER_TO_P16_3 | No bytes manufactured or build calls |
| Release installation/migration/rollback operational handling | DEFER_TO_P16_9 | References and assessments only |

Initial guessed compiler paths were absent; rg --files located the actual
language/compiler.py and its AIR_VERSION owner. This is discovery path correction,
not an owning-contract defect. Historical package migration evidence is structural
and declarative, not automatic source rewrite or a release upgrade guarantee.

## Version model and domains

No second numeric release-version owner is introduced. P16.1 already requires an
explicit immutable opaque release-version string; P14 ExactVersion is deliberately
package-specific. Reusing its numeric triple as the release policy would restrict
review labels and conflate domains. Therefore release ordering is NOT_DEFINED,
with no semver/lexicographic/chronological/ancestry ordering or direction inference.

A release version, Python package version, VS Code extension version, Visual
Studio extension version, P14 package coordinate version, schema/contract version
and native profile are distinct. Exact P14 package versions continue to reside in
PackageCoordinate; the policy does not duplicate dependency compatibility.
LANGUAGE_SEMANTICS is an explicit caller-declared mapping domain, not proof of
language behavior or a new authoritative compiler version.

ReleaseVersionSurface binds exact P16.1 target, bounded version domain and
component identity. Primary domains PYTHON_PACKAGE, VSCODE_EXTENSION,
VISUAL_STUDIO_EXTENSION and NATIVE_PROFILE must match their owning target.
PACKAGE_CONTRACT, SCHEMA_CONTRACT and LANGUAGE_SEMANTICS are separately scoped
caller declarations, never promises inferred from release numbers.

ReleaseSurfaceVersion binds exact ReleaseIdentity, surface, declared version and
canonical provenance. The native primary mapping must equal the target's imported
frozen PROFILE exactly. Mappings neither imply compatibility nor force versions
equal. The fixture keeps Python 10.1.3 and editor 0.1.0 separate from release
2.0.0/2.1.0; all are test declarations, not a chosen production release.

## Bounded compatibility policy and explicit evidence

ReleaseCompatibilityPolicy is immutable and binds identifier/revision, exact source
and target ReleaseIdentity, nonempty required surface set, exact source/target
mappings, explicit declarations and provenance. Inputs are bounded immutable
tuples, canonically sorted. No predicates, expressions, callbacks or policy engine.

Each ReleaseCompatibilityDeclaration retains the exact mapping pair, one of
COMPATIBLE / MIGRATION_REQUIRED / INCOMPATIBLE / UNKNOWN, and supplied canonical
evidence references. Non-UNKNOWN assertions require evidence. These references
are caller-supplied policy declarations, not cryptographic authentication or
independently verified compatibility proof. No new ABI/API promise is made.
An explicit migration-required assertion also requires an exactly matching
ReleaseMigrationReference.

Matching channels, names, filenames, same-major versions, identical surface
versions, Git ancestry or adjacent schema numbers do not generate declarations.
COMPATIBLE means this exact policy declares compatibility for this exact surface
and pair; it does not establish identity, package dependency compatibility,
engineering safety or successful installation.

Missing source/target mappings yields UNKNOWN with
RELEASE_VERSION_MAPPING_MISSING. Present mappings without a declaration yield
UNKNOWN / RELEASE_COMPATIBILITY_UNKNOWN. Explicit UNKNOWN stays distinct.
Two declarations for the same surface are rejected, including identical duplicates,
with RELEASE_COMPATIBILITY_CONFLICT; no permissive result is selected.
Conflicting mappings produce RELEASE_VERSION_MAPPING_CONFLICT.
Contradictory source/target evidence produces RELEASE_SOURCE_MISMATCH or
RELEASE_TARGET_MISMATCH.

## Findings, matrix and exact policy binding

ReleaseCompatibilityFinding is an immutable policy/surface reference. Its
deterministic projection includes exact policy fingerprint, source and target
release fingerprints, exact mappings, declaration/migration evidence, provenance,
status and reason code. Changing release baseline, identity/version/channel,
mapping, component, policy revision, evidence or policy requirements re-identifies
the policy and dependent findings. Old findings remain bound to the old policy.

compatibility_matrix returns a canonical immutable tuple over the required
surfaces. Each row retains source/target versions, compatibility and local upgrade
status. Mixed Python-compatible / VS Code-migration-required / Visual Studio-
incompatible / native-unknown evidence stays dimensional.

| Compatibility | Reason | Local upgrade status |
| --- | --- | --- |
| COMPATIBLE | RELEASE_COMPATIBILITY_EXPLICIT | DIRECT |
| MIGRATION_REQUIRED | RELEASE_MIGRATION_REQUIRED | MIGRATION_REQUIRED |
| INCOMPATIBLE | RELEASE_INCOMPATIBLE | UNSUPPORTED |
| UNKNOWN | RELEASE_COMPATIBILITY_UNKNOWN or RELEASE_VERSION_MAPPING_MISSING | INCOMPLETE |

## Passive upgrade and migration boundaries

ReleaseUpgradeAssessment binds the exact policy and supplied immutable findings.
A finding from another policy is rejected with RELEASE_POLICY_MISMATCH.
Missing findings are INCOMPLETE; they are never silently generated by the
assessment. Duplicate findings are rejected. Explicit incompatibility takes
precedence as UNSUPPORTED; otherwise incomplete/unknown evidence remains
INCOMPLETE; only complete known evidence can be MIGRATION_REQUIRED or DIRECT.

DIRECT requires all required surfaces explicitly COMPATIBLE. It describes advisory
policy eligibility for that scope, never execution authorization. Package
dependencies still require their separate frozen owner evidence; a release policy
cannot override solver/lock/package compatibility. Tests pair COMPATIBLE release
policy with P14 BREAKING_STRUCTURAL_CHANGE to retain this separation.

No version-order direction is computed. Selecting an apparently newer or older
numeric label without declarations stays INCOMPLETE. An explicitly policy-covered
older target may be DIRECT, but this is not an automatic downgrade or rollback.
No general downgrade permission is inferred.

ReleaseMigrationReference contains identity, exact source/target mappings,
owning component and passive provenance. No script, callback, executable payload
or migration executor. P14.10 remains package migration owner; P16.9 will own later
release installation/upgrade/rollback contracts. No migration, rollback,
installation, uninstall or update operation occurs here.

## Domain/security boundaries and determinism

Schema adjacency does not imply compatibility. Frozen native PROFILE cannot be
substituted or broadened; unsupported target/profile construction fails closed
through P16.1 or P16.2. Visual Studio arm64 means editor installation metadata,
not native backend support. Existing Python >=3.9, VS Code ^1.85.0 and VS Community
17+ requirements are unchanged and are not release-wide platform certification.

Compatibility and upgrade records grant no authority or trust; findings report
CRYPTO_PROVIDER_UNAVAILABLE. Provenance is lineage, not authentication. Policy
cannot create package trust, runtime safety, upgrade success or permission.
No signing, credential acquisition, release publication, build, installation,
filesystem/network/process discovery or environment mutation.

Static dependency audit permits only dataclasses, re, P16.1 release_architecture,
the existing canonical utility and frozen CanonicalReference. No RuntimeEngine,
AuthorityEngine, subprocess, HTTP/socket client, package manager, Git, dynamic
import, pickle, eval/exec, installer or plugin dependency/call appears in production.
Dynamic traps cover file IO, process creation, socket creation and environment
reads while construction/findings/assessment projection completes.

Fingerprints use separate apexforge.release-version-surface,
release-surface-version, release-migration-reference, release-compatibility-
declaration/policy/finding and release-upgrade-assessment /v1 domains.
Canonical tuple ordering is independent of construction order.
No wall clock, hostname, PID, cwd, environment, locale, network or randomness.

Scale: 1,000 distinct policy/finding/assessment cases cover all four statuses,
then are independently reconstructed in reverse construction order and compared
by exact fingerprints. Iterative processing; determinism evidence, not benchmark.

```text
VERSION_ORDER != COMPATIBILITY
NEWER_VERSION != SAFE_UPGRADE
SAME_MAJOR_VERSION != COMPATIBILITY_PROOF
COMPATIBLE != IDENTICAL
UPGRADE_ALLOWED != UPGRADE_EXECUTED
MIGRATION_REQUIRED != MIGRATION_EXECUTED
DOWNGRADE_PATH != ROLLBACK_EXECUTION
RELEASE_VERSION != PYTHON_PACKAGE_VERSION
RELEASE_VERSION != VSCODE_EXTENSION_VERSION
RELEASE_VERSION != VISUAL_STUDIO_EXTENSION_VERSION
RELEASE_VERSION != PACKAGE_CONTRACT_VERSION
RELEASE_VERSION != LANGUAGE_SEMANTICS_VERSION
COMPATIBILITY_POLICY != CANONICAL_AIR
COMPATIBILITY_POLICY != AUTHORITY
RELEASE_COMPATIBLE != PACKAGE_DEPENDENCY_COMPATIBLE
TARGET_GREATER_THAN_SOURCE != UPGRADE_ALLOWED
NEW_COMPATIBILITY_POLICY != RETROACTIVE_MUTATION
CANONICAL_SEMANTIC_AUTHORITY=CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE
```

## Validation and Patch Matrix

Final focused P16.2: 31/31 PASS.
Unchanged focused P16.1: 25/25 PASS.
P16 aggregate: 56/56 PASS.
P14 aggregate: 330/330 PASS.
Native profile: 7/7 PASS.
Authority coexistence: canonical identities, exact grant, wrong
principal/capability/resource denial, authorized RuntimeEngine execution and
transactional denied execution PASS. The runtime execution belongs only to the
unchanged frozen smoke fixture, not P16.2 production.

Executed with python -X utf8 -B:
- apexforge/p16_2_release_versioning_compatibility_test.py
- apexforge/p16_1_release_architecture_contract_test.py
- -m unittest discover -s apexforge -p p16_*_test.py
- -m unittest discover -s apexforge -p p14_*_test.py
- apexforge/p12_5_native_profile_contract_test.py
- apexforge/authority_consolidation_smoke_test.py

Frozen P15 aggregate: 428/428 PASS, using
python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py.

Final preservation: branch remains p16-1-release-baseline; HEAD and P15 branch/
tag object/peeled identity unchanged. All three incoming P16.1 SHA-256 values
match the ledger; no owning defect or prior-slice edit. Six intended candidates,
empty tracked/staged diffs, no generated residue. No frozen P15/P14/earlier file
changed. No staging, commit, tag, push, production release, publication,
installation, signing or P16.3/later implementation.

Exact Git status:

```text
?? apexforge/p16_1_release_architecture_contract_test.py
?? apexforge/p16_2_release_versioning_compatibility_test.py
?? apexforge/tooling/release_architecture.py
?? apexforge/tooling/release_versioning.py
?? docs/p16/P16_1_RELEASE_ARCHITECTURE.md
?? docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
```

Inspection identified RELEASE_UPGRADE_POLICY_GAP in the new P16.2 matrix
projection: each row needed its local upgrade status in addition to aggregate
status. Owning section P16.2; patch surface new module/test only; added bounded
status projection and mixed-surface assertion. Focused 31/31 and aggregate 56/56
passed after patch. No predecessor repair, assertion weakening or unresolved
owning-contract defect.

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_2_INCOMING_CANDIDATES=3
P16_2_RELEASE_VERSION_EXPLICIT=True
P16_2_VERSION_DOMAINS_DISTINCT=True
P16_2_COMPATIBILITY_REQUIRES_EXPLICIT_POLICY=True
P16_2_UNKNOWN_COMPATIBILITY_DISTINCT=True
P16_2_COMPATIBILITY_EXACT_RELEASE_BOUND=True
P16_2_EXACT_P15_FREEZE_BOUND=True
P16_2_SCHEMA_COMPATIBILITY_NOT_INFERRED_FROM_VERSION_DISTANCE=True
P16_2_EDITOR_COMPATIBILITY_NOT_FABRICATED=True
P16_2_COMPATIBILITY_DETERMINISTIC=True
P16_2_DECISION_EXACT_POLICY_BOUND=True
P16_2_CONFLICTING_COMPATIBILITY_FAILS_CLOSED=True
P16_2_COMPATIBILITY_MATRIX_DETERMINISTIC=True
P16_2_REDEFINES_CORE_SEMANTICS=False
P16_2_VERSION_ORDER_IMPLIES_COMPATIBILITY=False
P16_2_VERSION_MAPPING_GRANTS_COMPATIBILITY=False
P16_2_GENERAL_COMPATIBILITY_LANGUAGE_IMPLEMENTED=False
P16_2_UPGRADE_EXECUTION_IMPLEMENTED=False
P16_2_NEWER_VERSION_AUTO_UPGRADE=False
P16_2_DOWNGRADE_AUTO_ALLOWED=False
P16_2_ROLLBACK_EXECUTION_IMPLEMENTED=False
P16_2_MIGRATION_EXECUTION_IMPLEMENTED=False
P16_2_REDEFINES_P14_MIGRATION_SEMANTICS=False
P16_2_EXECUTABLE_MIGRATION_SCRIPT_MODEL=False
P16_2_NATIVE_PROFILE_REDEFINED=False
P16_2_UNSUPPORTED_NATIVE_PROFILE_COMPATIBILITY_INFERRED=False
P16_2_PYTHON_RUNTIME_REQUIREMENT_CHANGED=False
P16_2_RELEASE_CHANNEL_IMPLIES_COMPATIBILITY=False
P16_2_REDEFINES_P14_PACKAGE_COMPATIBILITY=False
P16_2_RELEASE_POLICY_OVERRIDES_PACKAGE_SOLVER=False
P16_2_COMPATIBILITY_GRANTS_AUTHORITY=False
P16_2_UPGRADE_POLICY_GRANTS_AUTHORITY=False
P16_2_COMPATIBILITY_GRANTS_TRUST=False
P16_2_CRYPTO_AUTHENTICATION_IMPLEMENTED=False
P16_2_ARTIFACT_BUILD_EXECUTION=False
P16_2_INSTALLATION_EXECUTION=False
P16_2_PUBLICATION_PERFORMED=False
P16_2_NETWORK_ACCESS=False
P16_2_FILESYSTEM_DISCOVERY=False
P16_2_HOST_COMMAND_EXECUTION=False
P16_2_CREDENTIAL_ACQUISITION=False
P16_2_DYNAMIC_POLICY_EXECUTION=False
P16_2_MISSING_COMPATIBILITY_FAILS_OPEN=False
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_VERSION_MODEL=PASS
P16_RELEASE_VERSION_DOMAINS=PASS
P16_RELEASE_VERSION_MAPPING=PASS
P16_RELEASE_COMPATIBILITY_POLICY=PASS
P16_RELEASE_COMPATIBILITY_BINDING=PASS
P16_RELEASE_COMPATIBILITY_UNKNOWN_STATE=PASS
P16_RELEASE_COMPATIBILITY_CONFLICT_HANDLING=PASS
P16_RELEASE_UPGRADE_POLICY=PASS
P16_RELEASE_MIGRATION_BOUNDARY=PASS
P16_RELEASE_NATIVE_COMPATIBILITY_BOUNDARY=PASS
P16_RELEASE_EDITOR_COMPATIBILITY_BOUNDARY=PASS
P16_RELEASE_PACKAGE_COMPATIBILITY_BOUNDARY=PASS
P16_RELEASE_VERSION_DETERMINISM=PASS
P16_RELEASE_VERSION_SECURITY_BOUNDARY=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_2_READY_FOR_REVIEW=True
```
