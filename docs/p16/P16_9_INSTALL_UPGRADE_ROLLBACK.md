# P16.9 Installation, Upgrade & Rollback Contracts — Review Evidence

## Frozen baseline and incoming census

Branch `p16-1-release-baseline`; HEAD
`c9c5ca186c9d942ce336ac1ebfe1287b16953200`.
Frozen predecessor `afp-p15.14-freeze`; annotated tag object
`d7761c04e4422bfb91d9582275a60912874678f4`; peeled target equals HEAD.
Initial inventory: exactly 24 incoming untracked P16 candidates, no tracked or
staged diff, no ignored/generated residue. P15_REOPENED=False.
The accepted P16.1 native formats (dll, exe) and wasm rejection test are the
incoming baseline, not reopened defects.

SHA-256 incoming census:
```text
D8849A290CF65A0FAB56416CFE0D6DD4588CAD28425E2B218BB604F918EEF869  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
F12B0E26ED0589CBD11DF8F6729A8D10801EF3900E438000B422BAE4012F7DDE  apexforge/p16_6_vscode_distribution_packaging_test.py
3D3CEA0DA2FD2F1E8F779EB40628B6E7E4DA0E3B6854057360B12B4AAC3DB616  apexforge/p16_7_visualstudio_distribution_packaging_test.py
01639541D42E0F9814897F73EEABE54C6E78F064F593613AFEAD000D238D1C5E  apexforge/p16_8_native_distribution_packaging_test.py
F2070A9831DD461321342CBCC8AC79CDB41BE6F59E41375471FDBD4A3DE88D3B  apexforge/tooling/native_distribution.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
9662672BA7CFE5FDD0C1DDD71B02B6C8804D8C2EA58FE4DF8E6D2E3F0B7679AC  apexforge/tooling/release_architecture.py
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
9187091909FF50B12D3A6F4321CBBC2E5A13D433D4CFC716AC2B609E16C282AF  docs/p16/P16_8_NATIVE_WIN_X64_DISTRIBUTION_PACKAGING.md
```

P16.9 adds only release_installation.py, its focused test, and this report.
No frozen or earlier P16 owner is redesigned.

## Owner census

| Owner / evidence | Classification | Relationship |
| --- | --- | --- |
| P16.1 release identities, target/descriptor matrix | REUSE | Exact release and scoped target |
| P16.2 compatibility findings and ReleaseUpgradeAssessment | REUSE | Sole upgrade-eligibility owner |
| P16.3 byte-backed artifacts / COPY_BYTES | REUSE | Exact opaque bytes, no build |
| P16.4 manifest/checksum/provenance | REUSE | COMPLETE scoped evidence required |
| P16.5–P16.8 target packaging wrappers/reports | REFERENCE_ONLY | No new build, package inspection, or environment repair |
| P14 package_lock RestorePlan / plan_restore | FROZEN_PACKAGE_RESTORE_CONTRACT / REFERENCE_ONLY | Package dependency restore remains separate |
| P14 package_cache explicit-root immutable content store | FROZEN_PACKAGE_RESTORE_CONTRACT / REFERENCE_ONLY | Integrity/read-only views do not become an installer |
| P14 package_publishing / registry records | REFERENCE_ONLY | No publication or authenticated publisher inference |
| vscode_package.install_vscode_extension/check_vscode_installation | FROZEN_INSTALLATION_HELPER / REFERENCE_ONLY | Real code --install-extension and discovery path deliberately not invoked |
| visualstudio_packaging.audit_visualstudio_installed_copy | FROZEN_INSTALLATION_HELPER / REFERENCE_ONLY | Real profile traversal not invoked |
| build_artifact.write_build_artifact_atomic; narrative_session atomic writer | REFERENCE_ONLY | Existing per-file replace convention; not multi-file transactions |
| .gitignore .apexforge_backups/ | REFERENCE_ONLY | Ignored backup namespace; no matching installer/rollback owner found in inspected tooling/editor sources |
| New isolated projection and compensation | INSTALLATION_EXTENSION_POINT / ISOLATED_TEST_ONLY | No real platform installation |
| CI/publication, signing, acceptance | DEFER_TO_P16_10 / DEFER_TO_P16_11 / DEFER_TO_P16_12 | No implementation |

The historical AGENTS.md P11 program text is superseded for scope by the explicit
P16.9 assignment; its engineering, safety and human-review requirements remain
observed. No global helper is called merely because it exists.

## Models and exact evidence binding

DeploymentTarget is immutable and bounded to PYTHON_ENVIRONMENT,
VSCODE_EXTENSION_ROOT, VISUAL_STUDIO_EXTENSION_ROOT and NATIVE_APPLICATION_ROOT,
mapped to the existing four P16 targets. Destination is a logical identifier;
it is not a host path or an installer command.

InstallationIdentity binds target, exact release, exact scoped P16.4 manifest
fingerprint, and the fixed apexforge.isolated-exact-projection/v1 policy.
Only COMPLETE manifests with artifacts matching the deployment surface are
accepted. Completeness is consumed from P16.4, not reinterpreted.

FileProjection binds a PackagePath to an exact P16.3 artifact. All scoped manifest
artifacts must occur exactly once; each must equal the manifest's byte-backed
artifact and pass the existing P16.4 checksum verification. Filename-only input,
substituted artifacts and contradictory/missing manifest evidence reject.
Bytes remain opaque. A complete generic-artifact fixture is not a claim of a
final platform package or production release readiness.

InstallationPlan is immutable and performs no filesystem operation. It binds the
installation identity, deterministic file projection, exact expected current
DeploymentState, conflict/precondition policy, provenance-bundle fingerprint and
P16.2 assessment where needed. Its fingerprint is the transaction reference.
Modes are CLEAN_INSTALL, EXACT_REINSTALL and UPGRADE.

DeploymentState is explicit: logical target, exact installation identity,
installed inventory with artifact/digest/length references, receipt-plan
fingerprint, predecessor-state fingerprint. Artifacts retain the supplied bytes
needed for exact rollback. Empty state has no release or files. State is never
inferred through recursive filesystem scanning.

InstallationReceipt binds the exact plan, previous state, result state and logical
inventory. It records COMMITTED_ISOLATED, not real Python/IDE/system installation.
A state points to a plan fingerprint rather than its own receipt fingerprint,
avoiding a circular identity. Exact reinstall emits a receipt but preserves the
previous state fingerprint and release identity.

## Physical-root isolation and path safety

Execution requires an active opaque IsolatedRoot yielded by isolated_root.
The caller must supply an absolute disposable parent named
apexforge-install-test-* and explicitly assert test_controlled=True. The factory
creates a fresh owned child in that parent. Arbitrary Path handles, forged/inactive
root objects and unmarked parents are rejected. No real IDE/Python/registry/PATH/
Program Files destination is discovered. The caller is responsible for placing
the explicitly disposable parent appropriately; the naming assertion is not
authentication of a workstation directory. The executor never projects into the
parent itself or a preexisting installed extension tree.

An active context registers physical root device/inode separately from canonical
records. Root ancestors and destination components are checked with lstat for
symlink/reparse redirection and expected directory/regular-file types.
Exact-case sibling matching rejects Windows aliases. Logical PackagePath rules
reject absolute/drive/traversal/device-name/unsafe-separator paths. Projection
validation also rejects duplicate paths, file/directory prefixes and inconsistent
case in directory prefixes. Broken entries are checked via lstat rather than
silently treated as absent. Only bounded immediate sibling lists for declared
paths are inspected; no recursive discovery of arbitrary files.

Internal staging/backup slots and cleanup paths are owned and bounded. Root and
staging directory/regular-slot checks precede moves and cleanup. No recursive
delete is exposed by the transaction implementation. The isolated context's
standard TemporaryDirectory cleanup destroys its own disposable child at context
exit; caller parent content outside that child is untouched. Unrelated files
inside the child are preserved during transactions, not promised persistence
after the caller closes the disposable sandbox.

## Transactions and failure recovery

Execution is cooperative/exclusive within the isolated root. A fixed exclusive
lock file prevents concurrent applies using this API. The process-local current
state ledger must match the plan; prior receipt fingerprints are recorded only
after verified transactions. Files matching a supplied unrecorded nonempty state
do not establish an installation.

Sequence:
1. Validate immutable manifest/artifact/policy inputs and executable eligibility.
2. Validate active root, acquire isolated lock, match recorded current state.
3. Verify exact previous owned bytes and reject unknown destination content.
4. Stage exact new bytes and copies of prior bytes into owned slots; verify bytes.
5. Recheck current destination state after staging, before mutation.
6. Replace individual files atomically with os.replace, or remove only recorded
   obsolete owned files; record touched paths before the OS call.
7. Verify the committed inventory against the expected exact state.
8. Record result/receipt in the root-local ledger; remove owned scratch/lock.

On a commit/verification failure, compensation restores old bytes from verified
backup slots and removes introduced-only files. Touched-path accounting also
handles injected failures occurring immediately after a successful OS move.
Recovery verifies the old inventory before returning FAILED_RECOVERED.
Unrelated files are never included in delete/replace operations.

REJECTED means preconditions/eligibility failed; FAILED_RECOVERED means the
transaction failed and prior owned state was verified; RECOVERY_FAILED means
restoration could not be proved. No success receipt is emitted for these results.
Recovery failure retains the bounded owned scratch path as noncanonical
operational evidence and marks the sandbox recovery-required, blocking further
transactions. It does not pretend the prior state was restored.

This is not a globally atomic multi-file swap. Readers outside this API may see
intermediate file states. It is not crash/power-loss recovery, a durable journal,
an adversarial concurrent-filesystem defense, ACL/ownership restoration, or a
general workstation recovery service. Compensating recovery requires functioning
filesystem operations; failure is explicit rather than an unconditional promise.
The lock/ledger apply only to cooperating operations in the current isolated
context. Filesystem teardown/cleanup errors may surface instead of success.
No atomicity or recovery property beyond the demonstrated model is claimed.

## Compatibility and upgrade gate

Upgrades bind exact current state and source/target releases through the existing
P16.2 ReleaseUpgradeAssessment. Required surfaces must belong to the deployment
target and include its primary version domain. Supplied primary version mappings
must match exact descriptor surface versions; native mappings retain the full
frozen profile rather than comparing profile-v1 numerically.

Only DIRECT assessments execute. UNKNOWN/INCOMPLETE, INCOMPATIBLE/UNSUPPORTED and
MIGRATION_REQUIRED plans remain non-executable. Migration references stay in the
bound assessment; there is no callback, executable script or migration runner.
Version magnitude, same-major, channel and filename imply no permission. A
metadata-only explicit-policy upgrade may record a new deployment state without
rewriting identical file bytes.

Current-state substitution, stale bytes, unrecorded state and state changes during
staging fail before destination mutation. Concurrency after checks is outside the
host-adversary guarantee stated above; no permissive fallback exists.

## Rollback anchor and exact restoration

RollbackPlan binds the exact current state and an InstallationReceipt anchor.
Only a prior successful non-reinstall InstallationPlan receipt can anchor it;
the current state must equal the anchor's recorded result. At execution, the
anchor must be recorded in the same isolated context, and recorded current state
must match. A caller-created advisory receipt or arbitrary older version cannot
satisfy this operational history gate.

Rollback targets precisely anchor.previous, including its original release,
manifest, file bytes/digests, receipt-plan and predecessor references. Newer-only
files are removed; prior files restored; unrelated files retained. Successful
rollback produces exactly the prior state fingerprint. Clean-install rollback
restores the empty logical deployment state. Directory scaffolding is not part of
the canonical file inventory; empty directories need not be globally reconstructed
or removed. Rollback failures use the same compensation/result model, and do not
report restored state falsely. All history/backup operation is isolated and
process-local, not persisted for real system rollback.

## Bounds, determinism and static audit

Limits: 64 projected files, 1 MiB per artifact through P16.3, 8 MiB total per state,
at most 16 logical path components / 512 logical characters through PackagePath,
4096 immediate directory entries, 1024 recorded transaction fingerprints and
64 logical deployment slots per active root. Staging is bounded by old plus new
inventories; receipt/state records reference fingerprints rather than recursively
serializing historical states. Equivalent independently constructed plans and
transactions in different physical test roots produce identical receipt/state
fingerprints. Host paths, clocks, usernames, environment and random staging names
are not canonical identity.

Static audit: no subprocess/shell, network clients, registry APIs, environment/PATH
mutation, credential acquisition, dynamic loading, pickle/eval/exec, artifact
execution, global installer calls or arbitrary recursive deletion. os is used
only for bounded file replacement; no environment lookup is used. Existing
global-install and installed-profile helpers are neither imported nor invoked.

INSTALLATION != RELEASE_IDENTITY
INSTALLATION != PACKAGE_IDENTITY
INSTALLATION != CANONICAL_AIR
INSTALLATION != AUTHORITY_GRANT
INSTALLED != TRUSTED
INSTALLED != COMPATIBLE
UPGRADE_AVAILABLE != UPGRADE_ALLOWED
UPGRADE_ALLOWED != UPGRADE_EXECUTED
ROLLBACK_PLAN != ROLLBACK_EXECUTED
ROLLBACK != DOWNGRADE_BY_VERSION_ORDER
ROLLBACK_TARGET != ARBITRARY_OLDER_VERSION
DEPLOYMENT_STATE != RELEASE_MANIFEST
FILES_PRESENT != VALID_INSTALLATION
VALID_INSTALLATION_PLAN != INSTALLED
NEWER_VERSION != UPGRADE_PERMISSION
CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE

## Validation and Patch Matrix

Focused P16.9: 40 tests run; 39 PASS, one host-limited real-symlink test SKIPPED
(errno 22 creating a directory symlink). Do not report 40/40 PASS. Actual Windows
reparse-attribute rejection is explicitly fault-injected; case aliases, unknown
files, exact bytes, partial moves and recovery run against real isolated files.
The real symlink construction limitation is retained, not repaired with privilege
changes. No production assertion is weakened because of the skip.

Injected phases: pre-staging rejection, staging write error, corrupted staged
bytes, stale state after staging/before commit, commit failure, successful partial
move followed by error, post-commit verification mismatch, rollback commit error,
and commit plus recovery failure. Tests prove old bytes, empty clean state,
newer-only removal, unrelated-file preservation, no false receipt and explicit
recovery-required behavior.

Predecessor focused PASS: P16.8 36, P16.7 38, P16.6 33, P16.5 35, P16.4 41,
P16.3 31, P16.2 31, P16.1 25.
P16 aggregate: 310 tests run, 309 PASS / one host-limited SKIP, no failures.
P14 aggregate: 330/330 PASS.
Frozen native profile: 7/7 PASS.
Authority coexistence: canonical identities/exact grant/wrong principal-capability-
resource denial/authorized RuntimeEngine execution/transactional denied execution
PASS. Only the unchanged authority smoke exercises RuntimeEngine; P16.9 does not.
P15 aggregate: 428/428 PASS.

Patch route:
FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES -> PATCH SURFACE
-> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION
-> CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

| Finding | Classification / owner | Resolution |
| --- | --- | --- |
| Initial commit/recovery fault tests changed only metadata, so no move occurred | INSTALLATION_TRANSACTIONALITY_GAP; P16.9 test fixtures | Changed fixtures to require actual byte replacement; retained recovery assertions; focused PASS |
| Passive receipts alone were insufficient as operational rollback history | ROLLBACK_ANCHOR_GAP; P16.9 | Added verified root-local state/receipt history and unrecorded-current rejection; no authority/trust model |
| Broken reparse entries/staging cleanup needed lstat guards | INSTALLATION_PATH_SAFETY_GAP; P16.9 | Bounded explicit lstat checks for destination and owned staging nodes |
| History and state count needed explicit bounds | INSTALLATION_STATE_GAP; P16.9 | Bounded transaction/slot counts; fail closed before mutation |
| Host refuses actual symlink creation | INSTALLATION_ISOLATION_GAP; ISOLATED_TEST_ONLY environment evidence | One test explicitly skipped; structural reparse rejection remains tested; no host-policy repair |

No P16.1–P16.8 or frozen owner patch was required. Remaining limitations are the
explicit host skip and bounded isolation/atomicity/recovery scope, not hidden
production-release readiness claims.

## Carry-forward facts

P16.5 sdist build/content reproducibility PASS; archive timestamps differ; wheel
unavailable; no tool installation. P16.6 VSIX model/archive/source-continuity PASS,
exact Git blob projection for CRLF differences, real offline VSCE unverified.
P16.7 cache-only VSIX construction/assembly continuity/genuine P16.3/P16.4
integration PASS; raw/member/assembly reproducibility DEFERRED with PE/debug/
generated/archive metadata differences. P16.8 exact frozen native profile, genuine
AMD64 EXE build and measured raw-byte reproducibility/continuity/integration PASS;
generated native artifact not executed. None of these results is reinterpreted or
repaired by this slice.

## Preservation and exact Git state

Final inventory audit: exactly 27 intended untracked P16 candidates. All 24
incoming SHA-256 hashes match the census byte-for-byte; no predecessor correction
or earlier-slice change occurred. Branch remains p16-1-release-baseline; HEAD and
P15 branch remain c9c5ca186c9d942ce336ac1ebfe1287b16953200. P15 tag object remains
d7761c04e4422bfb91d9582275a60912874678f4 and peels to the same freeze commit.
Tracked/staged diffs are empty, with no ignored/generated repository residue.
Isolated test contexts closed and cleaned their owned roots, including retained
fault-injection backup scratch. No real Python/IDE/native installation or system
rollback, credential access, artifact execution, publication, staging, commit,
tag, push, or P16.10 work occurred.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_9_INCOMING_CANDIDATES=24
P16_9_REDEFINES_CORE_SEMANTICS=False
P16_9_GLOBAL_INSTALL_HELPERS_INVOKED=False
P16_9_DEPLOYMENT_TARGET_BOUNDED=True
P16_9_REAL_INSTALL_ROOT_DISCOVERY=False
P16_9_INSTALLATION_EXACT_RELEASE_BOUND=True
P16_9_PLAN_HAS_NO_SIDE_EFFECTS=True
P16_9_INSTALL_INPUT_EXACT_EVIDENCE_BOUND=True
P16_9_UPGRADE_REQUIRES_EXPLICIT_POLICY=True
P16_9_UNKNOWN_COMPATIBILITY_FAILS_CLOSED=True
P16_9_ARBITRARY_MIGRATION_EXECUTION=False
P16_9_INSTALL_RECEIPT_GRANTS_TRUST=False
P16_9_DEPLOYMENT_STATE_EXPLICIT=True
P16_9_INSTALLATION_TRANSACTIONAL=True
P16_9_FAILED_INSTALL_PRESERVES_PRIOR_STATE=True
P16_9_INSTALLED_BYTES_EXACT=True
P16_9_INSTALL_PATHS_SAFE=True
P16_9_DESTINATION_ESCAPE_REJECTED=True
P16_9_UNKNOWN_EXISTING_CONTENT_OVERWRITE=False
P16_9_EXACT_REINSTALL_IDEMPOTENT=True
P16_9_UPGRADE_EXACT_CURRENT_STATE_BOUND=True
P16_9_CURRENT_STATE_MISMATCH_FAILS_CLOSED=True
P16_9_ROLLBACK_EXACT_STATE_BOUND=True
P16_9_ROLLBACK_NOT_VERSION_GUESS=True
P16_9_REAL_SYSTEM_ROLLBACK_PERFORMED=False
P16_9_ROLLBACK_RESTORES_EXACT_STATE=True
P16_9_ROLLBACK_FAILURE_NOT_MASKED=True
P16_9_UNRELATED_FILES_PRESERVED=True
P16_9_REAL_PYTHON_INSTALL_PERFORMED=False
P16_9_REAL_VSCODE_INSTALL_PERFORMED=False
P16_9_REAL_VISUAL_STUDIO_INSTALL_PERFORMED=False
P16_9_REAL_NATIVE_INSTALL_PERFORMED=False
P16_9_REGISTRY_MUTATION=False
P16_9_ENVIRONMENT_MUTATION=False
P16_9_INSTALLED_ARTIFACT_EXECUTED=False
P16_9_NETWORK_ACCESS=False
P16_9_CREDENTIAL_ACQUISITION=False
P16_9_SIGNING_IMPLEMENTED=False
P16_9_INSTALLATION_GRANTS_TRUST=False
P16_9_INSTALLATION_GRANTS_AUTHORITY=False
P16_9_INSTALLATION_GRANTS_RELEASE_APPROVAL=False
P16_9_REDEFINES_RELEASE_ARCHITECTURE=False
P16_9_REDEFINES_COMPATIBILITY_POLICY=False
P16_9_REDEFINES_GENERIC_BUILD=False
P16_9_REDEFINES_RELEASE_MANIFEST=False
P16_9_REDEFINES_PYTHON_DISTRIBUTION=False
P16_9_REDEFINES_VSCODE_DISTRIBUTION=False
P16_9_REDEFINES_VISUAL_STUDIO_DISTRIBUTION=False
P16_9_REDEFINES_NATIVE_DISTRIBUTION=False
P16_9_INSTALLATION_EVIDENCE_DETERMINISTIC=True
P16_9_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_9_STALE_PLAN_FAILS_CLOSED=True
P16_9_ATOMICITY_CLAIM_EVIDENCE_BASED=True
P16_9_STATIC_SECURITY_AUDIT=PASS
CRYPTO_PROVIDER_UNAVAILABLE
P16_5_WHEEL_LOCAL_BUILD_AVAILABLE=False
P16_5_SDIST_CONTENT_REPRODUCIBLE=True
P16_5_SDIST_RAW_BYTES_REPRODUCIBLE=False
P16_6_REAL_VSCE_BUILD_VERIFIED=False
P16_7_REAL_VISUAL_STUDIO_VSIX_BUILD=True
P16_7_RAW_BYTES_REPRODUCIBLE=False
P16_8_NATIVE_ARTIFACT_BYTE_BACKED=True
P16_8_NATIVE_RAW_BYTES_REPRODUCIBLE=True
P16_INSTALLATION_MODEL=PASS
P16_INSTALLATION_TARGET_MODEL=PASS
P16_INSTALLATION_EVIDENCE_BINDING=PASS
P16_INSTALLATION_PATH_SAFETY=PASS
P16_INSTALLATION_TRANSACTIONALITY=PASS
P16_INSTALLATION_STATE_MODEL=PASS
P16_INSTALLATION_RECEIPT_MODEL=PASS
P16_INSTALLATION_STALE_PLAN_HANDLING=PASS
P16_UPGRADE_POLICY_BINDING=PASS
P16_UPGRADE_TRANSACTIONALITY=PASS
P16_ROLLBACK_ANCHOR_MODEL=PASS
P16_ROLLBACK_STATE_BINDING=PASS
P16_ROLLBACK_TRANSACTIONALITY=PASS
P16_INSTALLATION_TRUST_BOUNDARY=PASS
P16_INSTALLATION_AUTHORITY_BOUNDARY=PASS
P16_INSTALLATION_SECURITY_BOUNDARY=PASS
P16_8_REGRESSION=PASS
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
P16_9_READY_FOR_REVIEW=True
```

True transactional/rollback markers describe the demonstrated recoverable
cooperative isolation model above; RECOVERY_FAILED explicitly withholds restoration.
Aggregate PASS means no failed tests with the separately reported one SKIP.
