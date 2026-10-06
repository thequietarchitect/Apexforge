# P16.12 Release Candidate Acceptance Matrix — Review Evidence

## Baseline and incoming inventory

Branch: p16-1-release-baseline.
HEAD / P15 freeze: c9c5ca186c9d942ce336ac1ebfe1287b16953200.
Tag: afp-p15.14-freeze.
Annotated tag object: d7761c04e4422bfb91d9582275a60912874678f4.
Peeled target equals HEAD. Initial inventory exactly 33 untracked P16 candidates,
tracked/staged diffs empty, no ignored/generated residue. Accepted incoming
P16.1 DLL/EXE correction and wasm negative test remain untouched.

Incoming SHA-256 census:
```text
E145F5836FC652533050C501C289C740A3E62AFF2AD26E4AC0448E2A44B4E0E7  apexforge/p16_10_ci_release_pipeline_dry_run_test.py
D6FEE238055F6234E56545CAF36BE8B3F93930E8738D21A132684CB238DBF946  apexforge/p16_11_release_security_signing_verification_test.py
D8849A290CF65A0FAB56416CFE0D6DD4588CAD28425E2B218BB604F918EEF869  apexforge/p16_1_release_architecture_contract_test.py
72F967A103FA768DA4FC6202A491032B700C0E8A7AF392CFA323C9834BAC0F3B  apexforge/p16_2_release_versioning_compatibility_test.py
FE69072FB7749510A6FC2FA79E5D96622D35C0434840A402A6B9839ADF555FFC  apexforge/p16_3_reproducible_release_build_test.py
1161A6BE8AB4DCA1434E6DD5C7D76549F5730DF0C2A3A5CC3FACCE04EA78332B  apexforge/p16_4_release_manifest_provenance_test.py
8F3D05AF732B5779BB5D4BB4153F996043D438E2074091B33F7BA53064BD4621  apexforge/p16_5_python_distribution_packaging_test.py
F12B0E26ED0589CBD11DF8F6729A8D10801EF3900E438000B422BAE4012F7DDE  apexforge/p16_6_vscode_distribution_packaging_test.py
3D3CEA0DA2FD2F1E8F779EB40628B6E7E4DA0E3B6854057360B12B4AAC3DB616  apexforge/p16_7_visualstudio_distribution_packaging_test.py
01639541D42E0F9814897F73EEABE54C6E78F064F593613AFEAD000D238D1C5E  apexforge/p16_8_native_distribution_packaging_test.py
FB928F16E828F5013074EFB697262C54A76E7E6E88D9708E3CBA14CD99411E72  apexforge/p16_9_install_upgrade_rollback_test.py
F2070A9831DD461321342CBCC8AC79CDB41BE6F59E41375471FDBD4A3DE88D3B  apexforge/tooling/native_distribution.py
219242747171DE29D7A24F81BA4C018A8F70CFFADEE0F0496959914A55D2219F  apexforge/tooling/python_distribution.py
9662672BA7CFE5FDD0C1DDD71B02B6C8804D8C2EA58FE4DF8E6D2E3F0B7679AC  apexforge/tooling/release_architecture.py
1D6A99FBF877A0761A99948CEC295E149AA3A7ABB4CB8E39605A5CFB1DF43A6E  apexforge/tooling/release_build.py
8024EBC81C3910B188D741BBE6EBBF23F423782628546EF2C700FF391FC19219  apexforge/tooling/release_installation.py
75C97D8132DA40FD4D25D2D1BC49873D297156BF24B1ED802E58B95505AE9A54  apexforge/tooling/release_manifest.py
CCC0778130E5D08687DAE8A63803059B8CE4C6B0032A3427FF0595A00DEC8778  apexforge/tooling/release_pipeline.py
E9B5276F3F351946F6441266706D0014D9EA1AC5302631E9EB2F2DCCFDE9E788  apexforge/tooling/release_security.py
0B7F1BF949A1803637F826F4F31FC7F68D384CFF6C2CD3EEE6C9D4024FED52CB  apexforge/tooling/release_versioning.py
D92139A8BD491347762A488AEFBDF3C50E945E8F4923A5A339C7D6084F4E474F  apexforge/tooling/visualstudio_distribution.py
60040C7E90D99BC14771D9CC93DA7F8D518BB25157A6E17F9AFB3ADDCBB6EBB8  apexforge/tooling/vscode_distribution.py
068D6B31DAF200DB06054A269ABB10F260F686994B3C86F06B2AD4BE80116A72  docs/p16/P16_10_CI_RELEASE_PIPELINE_DRY_RUN.md
79CC659A32184FA9CE39D134D0377DEF1E79B9EBDBF9E36EEB7CE9DF4FD74B60  docs/p16/P16_11_RELEASE_SECURITY_SIGNING_VERIFICATION.md
1CCFB01BA43A4A178DEF2BA99FE10176F07FB9021C1D91F45F60B90600BA16A1  docs/p16/P16_1_RELEASE_ARCHITECTURE.md
F00CB44333888CF58575C5715441B53D9488CDF802F839B26B04C09D29EF647D  docs/p16/P16_2_VERSION_COMPATIBILITY_UPGRADE_POLICY.md
BE85A9B19D370E4DDABF5A3125838DE892855DC3FC5969A8AB41B982E6877B07  docs/p16/P16_3_REPRODUCIBLE_RELEASE_BUILD.md
97A124306C8EB86AEF07BA8BFBB95804FDA04D96B0771F78E77DAE7838AD0C39  docs/p16/P16_4_RELEASE_MANIFEST_PROVENANCE.md
478EE3227FEA029B7C1F9193F66D83D7D93D1A68E214AC0B9B29C18299B22BF6  docs/p16/P16_5_PYTHON_DISTRIBUTION_PACKAGING.md
0FB837164A660844374A7C8534FD4AC88C36DC79CCAC7988736351B56D064F4F  docs/p16/P16_6_VSCODE_DISTRIBUTION_PACKAGING.md
0F83C51FB2C9B8E93B4D39CBDA03ACC82DCF12B6CD08DF031960A7D324DD4E90  docs/p16/P16_7_VISUAL_STUDIO_DISTRIBUTION_PACKAGING.md
9187091909FF50B12D3A6F4321CBBC2E5A13D433D4CFC716AC2B609E16C282AF  docs/p16/P16_8_NATIVE_WIN_X64_DISTRIBUTION_PACKAGING.md
47D54B944421C67339DA74DACFC51EE451C84F858BDE6E35236EC0BE61835657  docs/p16/P16_9_INSTALL_UPGRADE_ROLLBACK.md
```

Only release_acceptance.py, its focused test and this document are added.
No P16.13 closure/freeze, publication, installation, signing or credential work.

## Acceptance-owner and waiver census

| Inspected evidence / owner | Classification | Relationship |
| --- | --- | --- |
| AGENTS.md | REFERENCE_ONLY | Human authority, frozen behavior, inspection/testing/safety rules; active P16.12 assignment supersedes historical P11 stage text |
| P11 SRC-H final integration acceptance matrix | FROZEN_ACCEPTANCE_CONVENTION | Evidence by owning layer and explicit expected outcome, not release authority |
| P12.6/P12.7/P12.8 acceptance/closure matrices | FROZEN_ACCEPTANCE_CONVENTION / REFERENCE_ONLY | Explicit missing/failed/historical evidence; no waiver of current failures |
| P13.12 freeze readiness | FROZEN_ACCEPTANCE_CONVENTION | Owner reserves actual freeze/release authorization |
| P14.13 and P15.14 closure evidence | FROZEN_ACCEPTANCE_CONVENTION / REFERENCE_ONLY | Regression/preservation gates and exact refs remain frozen |
| P15.13 platform acceptance | REFERENCE_ONLY | Contract PASS can correctly observe denied/incomplete outcomes; not a proof authenticator |
| P16.1 target/descriptor matrix | REUSE | Exact release architecture and four current surfaces |
| P16.2 compatibility assessment | REUSE | Existing exact decisions, no version-order inference |
| P16.3/P16.4 build/manifest/checksum/provenance | REUSE | Exact typed evidence / producer references |
| P16.5–P16.8 packaging reports/models | REUSE / REFERENCE_ONLY | Historical owner-build and per-format reproducibility facts retained |
| P16.9 installation/rollback models | REUSE | Passive receipt and contract evidence only, no execution |
| P16.10 pipeline and publication dry runs | REUSE | Exact blockers, counts and readiness remain authoritative for that snapshot |
| P16.11 signature bundle/results | REUSE | Structural security PASS is not production signing |
| New candidate/evidence/criterion/matrix/verdict | RELEASE_CANDIDATE_EXTENSION_POINT | Pure acceptance decision over supplied evidence |
| Waiver schema/API for current release blockers | NO_WAIVER_OWNER | None found; no override or waiver mechanism added |
| Actual closure/freeze | DEFER_TO_P16_13 | No Git operation or freeze preparation here |

The historical absent-fixture exclusions in P12 are scoped historical conventions;
they explicitly do not waive new current failures. They are not portable release
waivers and are not used to accept the wheel, VSCE, reproducibility, signing or
symlink blockers. No canonical criterion-specific waiver contract was found in
P16/tooling/acceptance sources.

## Candidate identity and exact evidence snapshot

ReleaseCandidateIdentity is immutable and binds explicit logical ID, exact
ReleaseIdentity/P15 baseline, exact evidence-snapshot fingerprint and exact
acceptance-policy schema/fingerprint. Policy fingerprint commits to all default
criteria. No automatic version/sequence, host path, date or CI job identity exists.
The review example p16-current-review / install-review 1.0.0 DEVELOPMENT is a
declared model context, not a production version/tag.

ReleaseCandidateEvidence is immutable and binds:
- P16.1 architecture, P16.10 pipeline result and exact regression inputs;
- per-slice ContractReview evidence for P16.1–P16.11;
- all typed pipeline packaging/source/build/manifest/version/installation refs;
- optional exact P16.4 manifests/checksums/provenance, P16.2 assessments,
  P16.3 artifacts, P16.9 receipts and P16.11 signature bundle.

Optional owned models must be linked to the same pipeline's exact release,
descriptor, owner references and owner status. Signature artifact subjects must
match the pipeline descriptor and actual build reference; signed manifest subjects
must be among the supplied exact manifests. Foreign build/manifest/receipt/security
substitution rejects. Present conflicting evidence is not silently discarded.
Optional absence is not converted into availability.

ContractReview composes the existing P16.10 RegressionEvidence type for a bounded
slice ID, retaining passed/skipped/failed/discovered counts and source reference.
It is supplied review/test evidence, not authenticated human approval.
Snapshots and verdicts do not authenticate the truth of external reports.

Changing a required report reference, artifact, manifest, policy, signature bundle,
count or pipeline fingerprint changes snapshot/candidate/matrix/verdict identity.
Equivalent independently constructed/permuted models canonicalize identically.
No old verdict remains valid_for a changed matrix.

## Criteria, levels and status semantics

AcceptanceCriterion is immutable and has bounded category, scope, source, subject
and REQUIRED/INFORMATIONAL level. Sources are fixed existing owner dimensions,
not predicates, commands or callbacks. Categories are BASELINE, REGRESSION,
ARTIFACT, REPRODUCIBILITY, COMPATIBILITY, INSTALLATION, ROLLBACK, SECURITY, SIGNING,
PUBLICATION_READINESS.

Default policy: full P16 platform acceptance, all four current surfaces, and
wheel + sdist for Python. VS Code/Visual Studio require VSIX; native requires the
EXE representation actually produced by the frozen P12.5/P16.8 owner. This does
not change P16.1's allowed format vocabulary. Dropping a wheel descriptor does not
remove the Python coverage requirement; the coverage row becomes INCOMPLETE.

All default criteria are REQUIRED. No repository evidence supports demoting the
current host-limited skip or other blockers to informational. Additional
INFORMATIONAL rows are allowed only as views of existing bounded criterion
semantics. They cannot replace, relabel or satisfy a required row. Existing
required IDs/semantics/levels are locked; duplicate/conflicting criteria reject.
Missing required specifications produce explicit INCOMPLETE rows.

CriterionResult states are PASS, FAIL, BLOCKED, DEFERRED, INCOMPLETE, SKIPPED,
NOT_APPLICABLE. Only exact PASS satisfies REQUIRED, with reference evidence.
PENDING upstream evidence is explicitly INCOMPLETE. Missing targets/evidence do
not become NOT_APPLICABLE. No waived/ignored/override state exists.

## Regression and per-surface matrix

The representative incoming snapshot retains P16 378 PASS + one SKIP / 379;
P15 428, P14 330, native 7 and authority smoke PASS. Authority count one denotes
one successful smoke invocation, not its individual assertions. Per-slice focused
counts remain explicit, including P16.9 39 PASS + one SKIP. Skips remain SKIPPED,
not folded into passing totals.

Each descriptor gets independent required artifact, owner-build, source-continuity,
content-reproducibility and raw-reproducibility rows. Each surface gets required
format-coverage, exact manifest, explicit compatibility and publication-readiness
rows. Global rows cover baseline, regression dimensions, reviewed slice tests,
installation/host coverage/rollback, security architecture, production signing,
native-profile scope and pipeline readiness.

| Dimension | Current evidence state | Acceptance effect |
| --- | --- | --- |
| Python sdist owner build/content | PASS | Preserved owner evidence, not a substitute for wheel/current manifest |
| Python wheel | INCOMPLETE, PYTHON_WHEEL_UNAVAILABLE | Required artifact family cannot pass |
| Python sdist raw reproducibility | DEFERRED, SDIST_ARCHIVE_TIMESTAMP_GAP | Required reproducibility unsatisfied |
| VS Code structural/source continuity | PASS | Does not prove a real VSCE package |
| Real VSCE owner build | INCOMPLETE, VSCODE_REAL_VSCE_UNVERIFIED | Required artifact gate unsatisfied |
| Visual Studio owner build/assembly continuity | PASS historical evidence | Artifact existence distinct from reproducibility |
| Visual Studio member/content and raw reproducibility | DEFERRED | Required rows remain unsatisfied |
| Native measured owner build/raw reproducibility/profile | PASS | Only apexforge.native.win-x64.i64-literal-state-set/v1, no wider native claim |
| Current exact release artifact/manifest bundle | INCOMPLETE in supplied review snapshot | Historical integrations do not fabricate a unified current release bundle |
| Explicit compatibility | INCOMPLETE in supplied snapshot | No numeric/channel inference |
| Isolated installation and rollback contract | PASS | No real host operations |
| P16.9 focused/global skip and host coverage | SKIPPED | Required; no waiver owner or convenience demotion |
| P16.11 security architecture | PASS | Cannot satisfy production signature criterion |
| Production signing | BLOCKED, CRYPTO_PROVIDER_UNAVAILABLE | No valid authenticated production signature |
| P16.10 publication targets/readiness | BLOCKED / false | Preserved without contradiction |

The native row preserves the exact profile and scope even when its measured build
and reproducibility rows PASS. Canonical AIR remains the semantic authority.

Installation and rollback consume existing contract/receipt evidence without
calling apply. Compatibility consumes P16.2 without re-solving or inferring.
Security consumes P16.11: rejected bundles/failure observations remain FAIL,
incomplete signature sets remain INCOMPLETE, unavailable production signing
remains BLOCKED. Production signing could satisfy its criterion only from the
owner's positive signed/verified/trusted evidence; those flags are all false in
the current approved model, and no positive fixture is fabricated.

The matrix consumes publication blockers and readiness directly from P16.10.
Its current version contains unresolved signing/acceptance prerequisites; this
slice does not patch earlier pipeline semantics, simulate missing approval, or
promise that a future ready path exists without owning-layer evidence changes.

## Current matrix and verdict

Actual pure evaluation over the accepted incoming evidence:
```text
Candidate:
262D272F7AA83764EB23271FB2D42923EE0139F19E653849883A2B8A8ACB14C5
Snapshot:
23589B2F95E2661E8C965E2D7412E354DB5818D03768AFF0B8EDE7ADBAE3A5D7
Matrix:
7E906531AA55FCA49D3D0BA184F30E00910745481FF97F3D222E9BA7053AA79B
Verdict evidence:
6DF8DBAE786324A7C11F8D35E09C44759CA887E2247D592E5F3E02F139FCB928

Required criteria=65
Satisfied=35
Unsatisfied=30
Verdict=BLOCKED
grants_release_approval=False
grants_authority=False
grants_trust=False
publication_performed=False
freeze_performed=False
```

Explicit DEFERRED criteria:
- content-reproducibility-visual-studio-vsix
- raw-reproducibility-python-sdist
- raw-reproducibility-visual-studio-vsix

Explicit SKIPPED criteria:
- contract-P16-9 (focused tests/review evidence counts)
- installation-host-coverage
- regression-P16

ReleaseCandidateVerdict is immutable, exact-candidate/snapshot/matrix bound and
includes satisfied/unsatisfied required IDs, sorted blocker codes, deferred/skipped
IDs, logical approval and non-effect flags. FAIL takes REJECTED precedence;
BLOCKED/DEFERRED/SKIPPED yields BLOCKED; missing/incomplete-only evidence yields
INCOMPLETE; only all required PASS yields ACCEPTED. Approval is evidence-only,
never trust/authority/publication/install/signature/freeze.

Criterion results are computed from the bound snapshot; callers cannot submit
arbitrary result rows as the matrix. No Boolean verdict override or manual waiver
argument exists. A missing required signing criterion cannot be replaced by an
informational baseline PASS. The actual current candidate is not accepted.

After final regressions, re-evaluation with 410 PASS + one SKIP / 411 produced:
snapshot 18177E010567EF389EDFACE4351A26778A5C210DD0464EF2847CCA6E09AE6151;
candidate 4EBBCA153F6E235C8D1FAD62C1CBECCDB4EC2A398F8BDD69C55C418EFB7FD2D1;
matrix 15ECDAF8DBDB1A7FC9AA50B9EBC0A1093E9C3604BE1001734E6C1C948D438911;
verdict evidence DE3DA3C5233CF994B9BF956133E5188E63279999D0FA2C1E0BBD868AD06E69AB.
The prior verdict was invalid for this changed matrix. Status remained BLOCKED,
35 required criteria satisfied / 30 unsatisfied, grants_release_approval=False.
The fresh count reference is supplied deterministic review evidence, not a new
test execution by the production acceptance evaluator.

P16_12_CONTRACT_PASS != CURRENT_CANDIDATE_ACCEPTED.
Acceptance-engine PASS means it correctly refuses incomplete evidence.

## Stale evidence, determinism and security

Canonical ordering is deterministic for reviews, owner models, criteria, rows,
blockers and per-surface matrices. Candidate policy fingerprint includes exact
required criterion semantics, while optional information views affect matrix
identity. An old verdict.valid_for(new_matrix) returns False whenever exact
candidate/snapshot/matrix evidence changes.

Bounds: 128 criteria/blockers, 64 optional models per class, 512 source/owner
references, 32 bounded structured diagnostic identifiers per row; slice IDs 1–11;
existing owner data/graph/reference bounds remain in force. No recursive policy
language or arbitrary callbacks, time, process/host/environment lookup,
filesystem discovery, suite runner, signing, installer, publication or Git API
exists in production. SHA-256 is canonical identity hashing only.

Static AST audit and evaluation with filesystem access trapped demonstrate pure
acceptance behavior. Optional typed owner fixture integration preserves exact
build/manifest/compatibility/install/security references without executing them.
It is explicitly generic/structural fixture evidence, not genuine package or
production signature creation.

ACCEPTANCE_MATRIX != RELEASE_ARTIFACT
ACCEPTANCE_MATRIX != RELEASE_MANIFEST
ACCEPTANCE_MATRIX != TRUST_POLICY
ACCEPTANCE_PASS != PUBLICATION
ACCEPTANCE_PASS != P16_FREEZE
ACCEPTANCE_PASS != AUTHORITY
ACCEPTANCE_PASS != INSTALLATION
ACCEPTANCE_PASS != SIGNATURE
BLOCKER_PRESENT != ACCEPTED
DEFERRED_REQUIRED_GATE != ACCEPTED
SKIPPED_REQUIRED_TEST != PASS
UNKNOWN_REQUIRED_GATE != ACCEPTED
CANONICAL_AIR
CRYPTO_PROVIDER_UNAVAILABLE

## Validation and Patch Matrix

Focused P16.12: 32/32 PASS.
Predecessor focused: P16.11 35, P16.10 34, P16.9 39 PASS + one host-limited SKIP;
P16.8 36, P16.7 38, P16.6 33, P16.5 35, P16.4 41, P16.3 31, P16.2 31,
P16.1 25 PASS.
Final P16 aggregate: 411 discovered, 410 PASS + one unchanged SKIP, no failures.
P14: 330/330 PASS. Native: 7/7 PASS. Authority coexistence PASS, including wrong
principal/capability/resource denial, authorized RuntimeEngine execution and
transactional denial. Only that unchanged smoke executes RuntimeEngine.
P15: 428/428 PASS.

FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES -> PATCH SURFACE
-> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

No executed test failure or earlier-slice owning defect required a patch.
Pre-test owner inspection corrected the new compatibility adapter's surface
access and strengthened PASS-reference/failure preservation. Final model review
retained incomplete-signature status and avoided unnecessary repeated fingerprint
work; focused and aggregate tests then passed. All work stays in the new P16.12
surface. Known missing wheel, unverified VSCE, reproducibility, host skip and
provider constraints are evidence blockers, not defects to repair here.

Waiver boundary: NO_WAIVER_OWNER. Historical exception conventions are not imported
as release waivers. No default gate was waived, weakened or converted to PASS.

## Preservation and exact Git state

Final audit: exactly 36 intended untracked P16 candidates, with all 33 incoming
SHA-256 hashes preserved byte-for-byte. Branch remains p16-1-release-baseline;
HEAD and P15 branch remain c9c5ca186c9d942ce336ac1ebfe1287b16953200. P15 tag
object remains d7761c04e4422bfb91d9582275a60912874678f4 and peels to the same
freeze commit. Tracked/staged diffs are empty; no ignored/generated release,
build, installation, signing, cache or temporary repository residue exists.
No frozen or P16.1–P16.11 file changed. No publication, installation, rollback,
signing, credential acquisition, staging, commit, tag, push, branch mutation,
or P16.13 work occurred. Frozen owner regressions alone exercised their previously
authorized test behavior; production acceptance performs none of those actions.

## Evidence-supported markers

```text
P16_BASELINE=P15_14_FREEZE
P15_REOPENED=False
P16_12_INCOMING_CANDIDATES=33
P16_12_REDEFINES_CORE_SEMANTICS=False
P16_12_WAIVER_MECHANISM_FABRICATED=False
P16_12_GENERAL_POLICY_LANGUAGE_IMPLEMENTED=False
P16_12_REDEFINES_COMPATIBILITY_POLICY=False
P16_12_INSTALLATION_EXECUTION_PERFORMED=False
P16_12_ROLLBACK_EXECUTION_PERFORMED=False
P16_12_CURRENT_CANDIDATE_ACCEPTED=False
P16_12_ARBITRARY_WAIVER_SUPPORTED=False
P16_12_FREEZE_PERFORMED=False
P16_12_PUBLICATION_PERFORMED=False
P16_12_REAL_INSTALLATION_PERFORMED=False
P16_12_SIGNING_PERFORMED=False
P16_12_CREDENTIAL_ACQUISITION=False
P16_12_NETWORK_ACCESS=False
P16_12_PRODUCTION_EVALUATOR_RUNS_COMMANDS=False
P16_12_ARBITRARY_POLICY_CALLBACKS_SUPPORTED=False
P16_12_ACCEPTANCE_GRANTS_TRUST=False
P16_12_ACCEPTANCE_GRANTS_AUTHORITY=False
P16_12_REDEFINES_RELEASE_ARCHITECTURE=False
P16_12_REDEFINES_GENERIC_BUILD=False
P16_12_REDEFINES_RELEASE_MANIFEST=False
P16_12_REDEFINES_PYTHON_DISTRIBUTION=False
P16_12_REDEFINES_VSCODE_DISTRIBUTION=False
P16_12_REDEFINES_VISUAL_STUDIO_DISTRIBUTION=False
P16_12_REDEFINES_NATIVE_DISTRIBUTION=False
P16_12_REDEFINES_INSTALLATION_POLICY=False
P16_12_REDEFINES_RELEASE_PIPELINE=False
P16_12_REDEFINES_RELEASE_SECURITY=False
P16_12_CANDIDATE_EXACT_RELEASE_BOUND=True
P16_12_EVIDENCE_SNAPSHOT_EXACT_BOUND=True
P16_12_EVIDENCE_SUBSTITUTION_REIDENTIFIES=True
P16_12_INFORMATIONAL_CANNOT_SATISFY_REQUIRED=True
P16_12_ACCEPTANCE_STATUS_BOUNDED=True
P16_12_REQUIRED_GATE_PASS_ONLY=True
P16_12_SKIPPED_EVIDENCE_NOT_AUTO_PASS=True
P16_12_PER_SURFACE_ACCEPTANCE=True
P16_12_PYTHON_MISSING_WHEEL_BLOCKS_COMPLETE_ARTIFACT_GATE=True
P16_12_VSCODE_UNVERIFIED_BUILD_NOT_ACCEPTED=True
P16_12_VISUAL_STUDIO_REPRODUCIBILITY_DEFERRED_VISIBLE=True
P16_12_NATIVE_PROFILE_SCOPE_PRESERVED=True
P16_12_UNSIGNED_REQUIRED_RELEASE_NOT_ACCEPTED=True
P16_12_SECURITY_ARCHITECTURE_PASS_NOT_SIGNATURE_PASS=True
P16_12_PIPELINE_BLOCKERS_PRESERVED=True
P16_12_VERDICT_EXACT_MATRIX_BOUND=True
P16_12_ACCEPTANCE_ENGINE_PASS_DISTINCT_FROM_VERDICT=True
P16_12_BLOCKER_ORDER_DETERMINISTIC=True
P16_12_UNKNOWN_REQUIRED_EVIDENCE_FAILS_CLOSED=True
P16_12_CONFLICTING_EVIDENCE_FAILS_CLOSED=True
P16_12_STALE_ACCEPTANCE_INVALID=True
P16_12_RELEASE_APPROVAL_IS_EVIDENCE_ONLY=True
P16_12_HOST_STATE_NOT_CANONICAL_IDENTITY=True
P16_12_ACCEPTANCE_EVIDENCE_DETERMINISTIC=True
P16_12_STATIC_SECURITY_AUDIT=PASS
CRYPTO_PROVIDER_UNAVAILABLE
P16_RELEASE_ACCEPTANCE_MODEL=PASS
P16_RELEASE_CANDIDATE_IDENTITY=PASS
P16_RELEASE_ACCEPTANCE_EVIDENCE_BINDING=PASS
P16_RELEASE_ACCEPTANCE_CRITERION_MODEL=PASS
P16_RELEASE_ACCEPTANCE_STATUS_MODEL=PASS
P16_RELEASE_ACCEPTANCE_REQUIRED_GATE_MODEL=PASS
P16_RELEASE_ACCEPTANCE_SURFACE_MATRIX=PASS
P16_RELEASE_ACCEPTANCE_REGRESSION_MATRIX=PASS
P16_RELEASE_ACCEPTANCE_ARTIFACT_MATRIX=PASS
P16_RELEASE_ACCEPTANCE_REPRODUCIBILITY=PASS
P16_RELEASE_ACCEPTANCE_INSTALLATION=PASS
P16_RELEASE_ACCEPTANCE_SECURITY=PASS
P16_RELEASE_ACCEPTANCE_SIGNING=PASS
P16_RELEASE_ACCEPTANCE_PIPELINE=PASS
P16_RELEASE_ACCEPTANCE_WAIVER_BOUNDARY=PASS
P16_RELEASE_ACCEPTANCE_STALE_EVIDENCE=PASS
P16_RELEASE_ACCEPTANCE_DETERMINISM=PASS
P16_RELEASE_ACCEPTANCE_TRUST_BOUNDARY=PASS
P16_RELEASE_ACCEPTANCE_AUTHORITY_BOUNDARY=PASS
P16_RELEASE_ACCEPTANCE_SECURITY_BOUNDARY=PASS
P16_CURRENT_RELEASE_CANDIDATE_ACCEPTED=False
P16_11_REGRESSION=PASS
P16_10_REGRESSION=PASS
P16_9_REGRESSION=PASS_WITH_HOST_LIMITED_SKIP
P16_8_REGRESSION=PASS
P16_7_REGRESSION=PASS
P16_6_REGRESSION=PASS
P16_5_REGRESSION=PASS
P16_4_REGRESSION=PASS
P16_3_REGRESSION=PASS
P16_2_REGRESSION=PASS
P16_1_REGRESSION=PASS
P16_AGGREGATE_REGRESSION=PASS_WITH_HOST_LIMITED_SKIP
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P16_AUTHORITY_COEXISTENCE=PASS
P15_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P16_12_READY_FOR_REVIEW=True
```

PASS denotes acceptance-contract behavior; current release-candidate acceptance is
False. P16.13 closure/freeze remains a separately authorized milestone.
