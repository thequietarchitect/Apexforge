# P12.6-10 — Full Closure Regression / Freeze Readiness

Status: READY_FOR_FREEZE_REVIEW. The exact transferred 21-file P12.6 candidate passed the unchanged authoritative RCV-51/RCV-50 transitive stack on a separate clean machine. The known historical fixture blocker remains separate. Earlier local failures below are preserved as historical evidence and superseded for final closure by the clean-machine result. No implementation/test/predecessor correction, staging, commit, tag, push or later gate.

## Baseline and original local interpreter

HEAD = afp-p12.5-execution-freeze^{commit} = 6e71a1afae36c3b4984e949c707d3e6fae6cc269. Unchanged objects / peeled commits:
- afp-p12.4-freeze: 7c475986ed3ed1d58cc30148603fbfe8b09529ee / 13f7646f1052746f54f906076d66d29117ee2718
- afp-p12.5-freeze: 9e2d7a4f57a10e0499d788f8584ace477f624b07 / 542be090e193b3d931d27c08e16de3efd961a01e
- afp-p12.5-execution-freeze: 6ad3d33601a576c2b42e2fde16cd98c2c61980fd / 6e71a1afae36c3b4984e949c707d3e6fae6cc269

Direct Git checks additionally confirmed expected P10 final, P11 SRA final and P12.0c/1/2/3/4/5/execution freeze commits and ancestry (nine tags). This direct PASS is not a claim that the interrupted RCV stack reached its final ancestry/security phase. No P12.7/P12.8/P13 candidate appeared.

Every original local Python command used exactly C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe; --version returned Python 3.9.13. Test invocations used -X utf8 -B. Existing subprocess runners inherit that sys.executable; PYTHONUTF8=1 was set for child Unicode output. NO_COLOR was removed only from the broader test process environment, matching the documented color-test invocation contract. No production changes for console encoding or machine security.

## Exact executed suites and results

For each script below the direct command was:
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/<script>

| Suite | Executed result |
|---|---|
| p12_6_3_metadata_identity_association_test.py | 8/8 PASS |
| p12_6_4_source_native_mapping_test.py | 11/11 PASS |
| p12_6_6_trace_provenance_reference_test.py | 12/12 PASS |
| p12_6_8_controlled_trace_integration_test.py | 12/12 PASS |
| p12_5_native_profile_contract_test.py | 7/7 PASS |
| -m unittest discover -s apexforge -p p12_5_native_execution_acceptance_test.py -v (instead of script) | 20/20 PASS; includes 7 imported profile cases |

P12.6 focused total: 43/43. P12.5 profile/acceptance total: 27/27 executions. Combined: 70 executions / 63 distinct unittest cases. Native acceptance __main__ was not invoked; frozen acceptance JSON was not regenerated.

These adjacent direct scripts all returned exit 0 (14/14):
- source_diagnostics_smoke_test.py
- compiler_smoke_test.py
- air_verifier_smoke_test.py
- p7_function_conditional_smoke_test.py
- p7_function_runtime_smoke_test.py
- p8_compiler_type_checking_smoke_test.py
- project_builder_smoke_test.py
- registry_linked_directive_execution_smoke_test.py
- runtime_state_consolidation_smoke_test.py
- otherwise_runtime_smoke_test.py
- directive_invocation_runtime_smoke_test.py
- runtime_directive_entry_guard_smoke_test.py
- causal_model_consolidation_smoke_test.py
- authority_consolidation_smoke_test.py

This covers source/deterministic diagnostics, duplicate declaration provenance, AIR/source separation, conditionals/functions/type checking/project builds, state updates, directive invocation/order/rollback/cycles, causal alternatives, exact authority grants/denials and transactional denial.

The following unchanged historical entry scripts each returned exit 1:
- p11_tam_c_deterministic_trace_production_foundation_smoke_test.py
- p11_tam_d_declaration_identity_ownership_trace_production_smoke_test.py
- p11_tam_e_reference_scope_resolution_evidence_trace_production_smoke_test.py
- p11_tam_f_type_evidence_trace_production_smoke_test.py
- p11_tam_g_authority_evidence_trace_production_smoke_test.py
- p11_tam_h_narrative_evidence_trace_production_smoke_test.py
- p11_tam_i_token_evidence_trace_production_smoke_test.py
- p11_tam_k_deterministic_whole_map_composition_smoke_test.py
- p11_6e_narrative_trace_diagnostics_termination_semantics_smoke_test.py

All nine are classified HISTORICAL_CONTRACT_BLOCKER, not hidden or rewritten. Eight assert broad unchanged-file comparisons against old P11 TAM tags; Git comparison of those tags to the untouched P12.5 execution-freeze HEAD already shows the same changed path sets, before P12.6 modifications. The narrative entry requires branch p11.6e-narrative-trace-diagnostics-termination-semantics while this worktree is p12-6-debug-metadata. None demonstrates a new producer behavior defect.

To validate actual producer behavior without claiming those old scripts passed, an ignored local driver invoked their original functions unchanged as unittest.FunctionTestCase:
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B build/p12_6_10_validation/producer_behaviors.py

Result: 53/53 PASS. The driver explicitly invokes all _assert_* functions except old predecessor/whole-file ownership guards; retains the frozen TAM model-reuse check; invokes narrative success, failure, termination and public API/documentation tests, excluding only the obsolete branch/baseline guard. It does not monkeypatch assertions, producers or Git. Thus source/token/declaration/ownership/resolution/type/authority/narrative TAM production, composition, deterministic IDs, type guards and observational ownership pass. P12.6-6 also executes its unchanged 17 TAM and 3 narrative behavioral functions internally.

Top-level unittest/function-case total is 123/123 executions (70 + 53), with duplicate imported/nested behavior coverage explicitly not counted as new distinct functionality.

## Original local transitive stack — historical environmental blocker

Command, attempted twice unchanged:
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/p12_5_rcv_51_p12_5_recovery_terminal_closure_smoke_test.py

RCV-51 invokes RCV-50's 46 recovery scripts, 25 P12 predecessor scripts, managed builds/runs and final provenance/security/ancestry checks. Both attempts returned exit 1:

1. First attempt: RCV-50 completed 14 recovery entry scripts then failed RCV-18, whose transitive RCV-15 managed probe was blocked by Windows Application Control. System.IO.FileLoadException / 0x800711C7 identifies the probe DLL as blocked.
2. Normal isolated retry:
   C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation_smoke_test.py
   returned exit 0, including runtime build/behavior and handoff/host admission markers.
3. Second RCV-51 attempt: RCV-50 completed 3 recovery entry scripts then failed RCV-7, whose transitive RCV-6 host DLL was blocked by the same Application Control policy/code.

Classification: ENVIRONMENTAL_BLOCKER for both RCV-51 attempts. Different newly built managed DLLs are intermittently rejected despite unchanged source. The passing RCV-15 retry does not establish a passing full stack. The 25 P12 predecessor loop and final RCV-50 managed-build/security/provenance phase were not reached. No machine policy, authority rule, build source, test assertion or frozen artifact was changed or bypassed.

At this original local stage, no RCV-50/51 PASS markers were reached. The final clean-machine evidence below supersedes this environmental blocker; these failed attempts remain recorded.

## Broader repository discovery and known historical fixture

Commands:
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/regression_harness.py --phase all --list
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/regression_harness.py --phase all

Discovery returned exit 0 with 362 smoke scripts. Unchanged fail-fast execution returned exit 1 after:
- 8 PASS: AIR linker/verifier, authority, causal, compiler, directive invocation, CLI color and CLI error styling.
- 1 FAIL: experimental_cli_human_presentation_smoke_test.py.
- 353 NOT_EXECUTED by that runner.

Failure is the same missing examples/P11Validation/apexforge.json, confirmed absent in git ls-tree HEAD and the worktree. CLI reports no manifest. Classification: HISTORICAL_CONTRACT_BLOCKER (pre-existing historical TEST_FIXTURE_DEFECT), under the preserved RCV-50 supplemental policy RECORDED_NOT_WEAKENED_NOT_USED_AS_CURRENT_BRANCH_CLOSURE_GATE. No fixture was invented, test weakened or full historical PASS asserted.

The harness failure is solely that known fixture; the nine separately invoked old milestone guards are separately recorded historical-contract failures. The original local RCV-51 environmental blocker was independent and was not waived by historical-fixture policy. The unchanged stack subsequently passed on the clean machine as recorded below.

Counts are reported by layer, not misleadingly summed across nested runs: 123 passing unittest/function cases; 14 passing adjacent smoke commands / 9 historical-guard failures; 1 passing isolated RCV-15 retry / 2 failed RCV-51 attempts; broader harness 8 PASS / 1 FAIL / 353 unexecuted. No implementation-defect correction occurred.

## Final architectural, source-map, trace and provenance audits

Focused executable checks freshly confirm:
- Canonical AIR remains semantic authority; compiler/tooling owns sidecars; plan owns routing; native owner performs admission/lowering/build/dispatch.
- CausalPath.actions remain unchanged/nonempty in the real compiler fixture and continue to fail bounded native admission. No operator reinterpretation, normalization or profile expansion.
- Bounded source→AIR and admitted AIR→generated-C maps exist. Generated C is unchanged/deterministic. Missing source correspondence stays explicit. Synthetic/container structures receive no invented physical span.
- No ordinary compiler-source→native executability or machine-address mapping is claimed; no PDB/debug switches/instrumentation.
- TAM/runtime/causal/authority evidence remains typed and producer-owned. Native retained evidence is artifact/output/result provenance, not per-operation execution.
- Runtime state.delta is execution scoped. No assignment-occurrence or operation inference. No fabricated global chronology; original producer order/returned interleaving remains intact.
- Unsupported schemas remain explicit; complete-mode failure and partial-mode coverage preserve raw owner results.
- Managed ExecutionResult and native CanonicalExecutionResult are unchanged and externally associated; native canonical result remains trace-free.
- Static dependency/AST audits and runtime traps prove no independent name resolution, type inference, evaluation, causal selection, policy replay, execution replay, C reverse inference, TAM fabrication or action reordering.

Negative tests freshly reject stale/substituted source/AIR/plan/routing/mapping/operation/producer/context/policy/generated-C/image/receipt/output/result, malformed/duplicate/reordered/mutable nested evidence and machine-path contamination. Deterministic fingerprints exclude time/PIDs/thread IDs/host/user labels/temp paths/environment dumps/random UUIDs/tickets. Exact generated/image byte hashes remain unmodified.

Resource/lifecycle tests confirm immutable sharing, per-result ownership, visible retention limits without silent truncation, pre-dispatch validation and post-dispatch capture before cleanup, and fingerprint-only validation after cleanup. No correctness-threatening P12.6 lifecycle problem was observed. Existing producer allocations before return and performance tuning remain outside this gate.

## Diff, artifacts and provisional freeze inventory

Tracked diff consists only of approved observational compiler ledger hooks/additive API and optional emitter region-sink capture; no semantic model/producer/result/profile changes. Their bytes and all predecessor uncommitted artifacts were rechecked unchanged after validation. No correction or line-ending normalization was made.

git diff --check: PASS. Supplementary untracked no-index checks reported no whitespace errors; Git emitted existing LF→CRLF conversion warnings and normal difference exit status. Original LF/CRLF bytes were preserved.

No tracked generated binaries/intermediates/PDBs/caches and no such files in the prospective source set. Tests generated untracked runtimes/dotnet/ApexForge.Runtime/bin and obj; after test completion their resolved absolute paths were checked within the workspace, tracked-file absence confirmed and only those generated directories removed. Native temporary cleanup passes its focused assertions. Ignored local drivers/logs remain under build/p12_6_10_validation, excluded from any candidate.

Original prospective source/evidence inventory (historical snapshot; no staging authorization):
- 2 modified production files.
- 5 new production files.
- 4 focused tests.
- 10 evidence/review documents, including this gate's validation record.
- Total 21 files; 4099 insertions / 7 deletions, including new-file lines (index remains untouched).
- Staged count: 0.

Recommended future commit subject: P12.6: add deterministic debug metadata, source maps, and observational trace retention
Recommended future annotated tag name: afp-p12.6-freeze
Suggested annotation: Freeze reviewed bounded P12.6 metadata, generated-source mapping and observational trace retention; preserve documented coverage limits.
Neither commit nor tag is created or authorized here. Current closure validation subsequently passed as recorded below; any commit or tag still requires explicit human authorization.


### Exact prospective file list

- apexforge/language/compiler.py
- apexforge/native_backend/native_execution.py
- apexforge/native_backend/source_mapping.py
- apexforge/p12_6_3_metadata_identity_association_test.py
- apexforge/p12_6_4_source_native_mapping_test.py
- apexforge/p12_6_6_trace_provenance_reference_test.py
- apexforge/p12_6_8_controlled_trace_integration_test.py
- apexforge/tooling/debug_metadata.py
- apexforge/tooling/source_air_mapping.py
- apexforge/tooling/trace_integration.py
- apexforge/tooling/trace_retention.py
- docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
- docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md
- docs/p12/P12_6_3_IMMUTABLE_METADATA_IDENTITY_ASSOCIATION_FOUNDATION.md
- docs/p12/P12_6_4_DETERMINISTIC_SOURCE_AIR_NATIVE_MAPPING.md
- docs/p12/P12_6_5_MAPPING_PROVENANCE_AND_TRACE_RETENTION_CONTRACT_REVIEW.md
- docs/p12/P12_6_6_DETERMINISTIC_TRACE_PROVENANCE_REFERENCE_FOUNDATION.md
- docs/p12/P12_6_7_CONTROLLED_TRACE_RETENTION_INTEGRATION_SCOPE_REVIEW.md
- docs/p12/P12_6_8_CONTROLLED_AUTOMATIC_TRACE_RETENTION_INTEGRATION.md
- docs/p12/P12_6_9_INTEGRATED_METADATA_TRACE_COVERAGE_AND_CLOSURE_REVIEW.md
- docs/p12/P12_6_10_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md

### Preserved P12.6-1 through P12.6-9 SHA-256

- docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md: 496eee7b666586074869b69c27e91363f9d141692c35b460341581eda38fb1b5
- docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md: 357a76cd34524bb35290bbb9b1dc4aaf5a3a1214c267c781fe67e25369f5d353
- docs/p12/P12_6_3_IMMUTABLE_METADATA_IDENTITY_ASSOCIATION_FOUNDATION.md: aa1479a30309ecf3137dce115c6a5280d45bad99f9ae8ba80ce779bd38a9e883
- docs/p12/P12_6_4_DETERMINISTIC_SOURCE_AIR_NATIVE_MAPPING.md: ff88305cd7bdd05b314e257667d75aeab4a0ca37e9e17fd6b4b8bee0d652a2a0
- docs/p12/P12_6_5_MAPPING_PROVENANCE_AND_TRACE_RETENTION_CONTRACT_REVIEW.md: 02a97d06adf115385cde79d957822ba4d2cfbd64cc7f6320b85ddd7168bd8ab4
- docs/p12/P12_6_6_DETERMINISTIC_TRACE_PROVENANCE_REFERENCE_FOUNDATION.md: 7da47b401c486c075e160526584ce23e6ade5997eb7f1d7c504a261148345dae
- docs/p12/P12_6_7_CONTROLLED_TRACE_RETENTION_INTEGRATION_SCOPE_REVIEW.md: 0fd5fffdfdf3db08ed78482da2ccbca6b4cb575abf6b0bf2572b70628109cbdc
- docs/p12/P12_6_8_CONTROLLED_AUTOMATIC_TRACE_RETENTION_INTEGRATION.md: f907a5bc9e04adc5a5fae0505a13093cfc97a10920dfb2ebbd08af2a6b6ac7f6
- docs/p12/P12_6_9_INTEGRATED_METADATA_TRACE_COVERAGE_AND_CLOSURE_REVIEW.md: c9d23dcdab68f1f555fb627d596591acc4f57e772c6ec44205e66a5dd4a29706

### Exact Git status

```text
 M apexforge/language/compiler.py
 M apexforge/native_backend/native_execution.py
?? apexforge/native_backend/source_mapping.py
?? apexforge/p12_6_3_metadata_identity_association_test.py
?? apexforge/p12_6_4_source_native_mapping_test.py
?? apexforge/p12_6_6_trace_provenance_reference_test.py
?? apexforge/p12_6_8_controlled_trace_integration_test.py
?? apexforge/tooling/debug_metadata.py
?? apexforge/tooling/source_air_mapping.py
?? apexforge/tooling/trace_integration.py
?? apexforge/tooling/trace_retention.py
?? docs/p12/P12_6_10_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md
?? docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
?? docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md
?? docs/p12/P12_6_3_IMMUTABLE_METADATA_IDENTITY_ASSOCIATION_FOUNDATION.md
?? docs/p12/P12_6_4_DETERMINISTIC_SOURCE_AIR_NATIVE_MAPPING.md
?? docs/p12/P12_6_5_MAPPING_PROVENANCE_AND_TRACE_RETENTION_CONTRACT_REVIEW.md
?? docs/p12/P12_6_6_DETERMINISTIC_TRACE_PROVENANCE_REFERENCE_FOUNDATION.md
?? docs/p12/P12_6_7_CONTROLLED_TRACE_RETENTION_INTEGRATION_SCOPE_REVIEW.md
?? docs/p12/P12_6_8_CONTROLLED_AUTOMATIC_TRACE_RETENTION_INTEGRATION.md
?? docs/p12/P12_6_9_INTEGRATED_METADATA_TRACE_COVERAGE_AND_CLOSURE_REVIEW.md
```

P12_6_FOCUSED_REGRESSION=PASS
P12_6_DEBUG_METADATA_COVERAGE=PASS
P12_6_SOURCE_MAP_COVERAGE=PASS
P12_6_SEMANTIC_TRACE_RETENTION=PASS
P12_6_TAM_TRACE_RETENTION=PASS
P12_6_DETERMINISM=PASS
P12_6_PROVENANCE_SECURITY=PASS
P12_6_EXECUTION_SEMANTICS_UNCHANGED=True
P12_6_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_6_P12_5_EXECUTION_FREEZE_PRESERVED=True
P12_6_PDB_ENABLED=False
P12_6_NATIVE_PROFILE_EXPANDED=False
P12_6_IMPLEMENTATION_COMPLETE=True
P12_6_FULL_CLOSURE_REGRESSION=PASS
P12_6_HISTORICAL_FULL_REGRESSION=BLOCKED_HISTORICAL_FIXTURE
P12_6_READY_FOR_FREEZE_REVIEW=True

## P12.6-10 original local environmental continuation — historical result

Before any validation action, all 21 candidate file SHA-256 values matched the continuation snapshot. Live Git numstat confirmed 4099 insertions / 7 deletions; staged count 0; HEAD and all three P12.4/P12.5 tag objects/peeled commits matched the baseline above. No generated candidate files. The only subsequent candidate edit is this validation-evidence addition; implementation, tests and P12.6-1 through P12.6-9 remain byte-identical.

Authoritative interpreter again returned Python 3.9.13. Normal initial command:
- dotnet restore runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj
- dotnet build runtimes/dotnet/ApexForge.Runtime.Host/ApexForge.Runtime.Host.csproj -c Release --no-restore --nologo

Then two clean normal restore/build rounds used the same commands for that host project and build/p12_6_10_validation/rcv15_normal_build/Rcv15Probe.csproj. This ignored diagnostic project uses the unchanged RCV-15 PROBE_CS constant and original project XML/properties/reference, obtained with the exact Python interpreter. It is supplementary hash evidence, not a substituted historical test. No signing, project metadata, framework, security or debug-symbol changes. All five restores and five builds succeeded; every build reported 0 warnings / 0 errors.

DLL paths relative to repository root, SHA-256 identical in both clean rebuild rounds at the same project paths:
- runtimes/dotnet/ApexForge.Runtime/bin/Release/net10.0/ApexForge.Runtime.dll: 8eb020cfa394f9766b7c712bbd1ddf2258a2915200b28c84733eda1960b7cc16
- runtimes/dotnet/ApexForge.Runtime.Host/bin/Release/net10.0/ApexForge.Runtime.Host.dll: 4040e55ccc5f782f1e0c46da78f208c6a330edefe459025e5ff88acff2940da4
- build/p12_6_10_validation/rcv15_normal_build/bin/Release/net10.0/Rcv15Probe.dll: 40c7ab9b6e02b2caa9c552588574fbe7f916e82d877a2762dd3d16c97ebcc6c8

Prior exact blocked artifacts were checked and no longer exist after their original TemporaryDirectory cleanup; their original hashes cannot be recovered or claimed equal to the diagnostic rebuilds:
- RCV-51 → RCV-50 → RCV-18 → RCV-17 → RCV-16 → RCV-15: C:\Users\corte\AppData\Local\Temp\apexforge-rcv15-kwvgjjrq\bin\Release\net10.0\Rcv15Probe.dll
- RCV-51 → RCV-50 → RCV-7 → RCV-6: C:\Users\corte\AppData\Local\Temp\apexforge-p12-5-rcv-6-w2xwmt6l\ApexForge.Runtime.Host\bin\Release\net10.0\ApexForge.Runtime.Host.dll

Original producing commands were dotnet run --project <that temporary Rcv15Probe.csproj or ApexForge.Runtime.Host.csproj> -c Release --nologo, with implicit supported restore/build. Each error is a CLR System.IO.FileLoadException explicitly reporting Application Control at load, not a compiler diagnostic. Prior RCV-15 isolated retry passed; RCV-6 passed within the first earlier stack before the RCV-15 failure. Their same error code establishes the same failure category, not proof of the exact same policy rule; no rule identity or permanent environmental resolution is claimed.

Fresh original unchanged isolated invocations (exact Python executable, -X utf8 -B):
- apexforge/p12_5_rcv_6_managed_host_project_skeleton_smoke_test.py: exit 0, HOST_BUILD=PASS, HOST_EXECUTION=PASS, DEDICATED_MANAGED_HOST_PROJECT_SKELETON=PASS.
- apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation_smoke_test.py: exit 0, RUNTIME_BUILD_AND_BEHAVIOR=PASS, TARGET_NEUTRAL_HANDOFF_IMPLEMENTATION_FOUNDATION=PASS.

Because both passed, the original authoritative RCV-51 entry was retried exactly once. It returned exit 1: RCV-51 → RCV-50 → RCV-22 → RCV-21 → RCV-20. RCV-20 reported RCV19_REGRESSION=PASS, then its newly built managed compatibility probe failed to load:
- C:\Users\corte\AppData\Local\Temp\apexforge-rcv20-qk0i0hdy\bin\Release\net10.0\Rcv20Probe.dll
- System.IO.FileLoadException: An Application Control policy has blocked this file. (0x800711C7)
- Producing command: dotnet run --project C:\Users\corte\AppData\Local\Temp\apexforge-rcv20-qk0i0hdy\Rcv20Probe.csproj -c Release --nologo.
- Classification: ENVIRONMENTAL_BLOCKER at assembly load. This exact artifact was also absent after the unchanged test cleanup; no hash is available. No RCV-50/51 terminal PASS markers were reached. No additional stack retry, source workaround or policy bypass was attempted.

Only these six unique generated directories were removed (relative to repository root):
- runtimes/dotnet/ApexForge.Runtime/bin
- runtimes/dotnet/ApexForge.Runtime/obj
- runtimes/dotnet/ApexForge.Runtime.Host/bin
- runtimes/dotnet/ApexForge.Runtime.Host/obj
- build/p12_6_10_validation/rcv15_normal_build/bin
- build/p12_6_10_validation/rcv15_normal_build/obj

The first four were removed before rebuild round 1; all six before round 2 and after final validation (16 recorded removal operations). Every removal checked the resolved absolute path within the workspace and absence of tracked files. No source/evidence directories or broad git clean. Diagnostic setup and logs remain ignored under build/p12_6_10_validation. Logs: normal_rebuild.log, rcv6_clean_retry.log, rcv15_clean_retry.log, rcv51_clean_retry.log.

The historical examples/P11Validation/apexforge.json absence remains independently HISTORICAL_CONTRACT_BLOCKER. No fixture reconstruction, semantic-suite reruns, implementation corrections, source/test changes, machine-policy changes or Git mutations. Final candidate still has 21 source/evidence files, zero staged files and no generated candidate files; insertions increase only by this final validation record. The prior 4099/7 statistic describes the preserved incoming snapshot.

P12_6_TRANSITIVE_FREEZE_STACK=PASS
P12_6_FULL_CLOSURE_REGRESSION=PASS
P12_6_HISTORICAL_FULL_REGRESSION=BLOCKED_HISTORICAL_FIXTURE
P12_6_READY_FOR_FREEZE_REVIEW=True

## P12.6-10 clean-machine validation — final closure evidence

A separate clean validation clone on DESKTOP-SOI356R verified the exact transferred 21-file P12.6 candidate byte-for-byte against its LYRA SHA-256 manifest:

- Base/HEAD: 6e71a1afae36c3b4984e949c707d3e6fae6cc269
- FILES_VERIFIED=21
- Transfer hashes: PASS
- Python: C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe
- Python version: 3.9.13, 64-bit
- .NET SDK: 10.0.302
- Authoritative entry point: apexforge/p12_5_rcv_51_p12_5_recovery_terminal_closure_smoke_test.py
- Entry point unchanged from HEAD.

The first invocation reached the final managed Smoke project but failed before compilation. Classification: TEST_INVOCATION_DEFECT; diagnostic: NETSDK1004: project.assets.json not found. The repository-compatible command succeeded:

~~~text
dotnet restore runtimes\dotnet\ApexForge.Runtime.Smoke\ApexForge.Runtime.Smoke.csproj --nologo
~~~

The unchanged authoritative RCV-51 command was then rerun and exited 0. RCV-6: PASS. RCV-15: PASS. RCV-20: PASS. No FileLoadException, 0x800711C7, or Application Control block occurred on the clean machine.

RCV-50 terminal markers:

~~~text
P12_5_RCV_50_RECOVERY_TESTS=46/46
P12_5_RCV_50_P12_PREDECESSOR_TESTS=25/25
P12_5_RCV_50_MANAGED_BUILD_AND_RUN=PASS
P12_5_RCV_50_P10_P11_P12_FREEZE_ANCESTRY=PASS
P12_5_RCV_50_PROVENANCE_OWNERSHIP_SECURITY_AUDIT=PASS
P12_5_RCV_50_RECOVERY_CLOSURE_AUDIT=PASS
~~~

RCV-51 terminal markers:

~~~text
P12_5_RECOVERY_TERMINAL_CLOSURE=PASS
P12_5_LANGUAGE_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_5_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_5_P12_4_FREEZE_PRESERVED=True
P12_5_PROVENANCE_PRESERVED=True
P12_5_DETERMINISM=PASS
P12_5_MANAGED_RUNTIME_BUILD=PASS
P12_5_REGRESSION_STACK=PASS
P12_5_HISTORICAL_IDENTITY_CLAIM=False
P12_5_READY_FOR_FREEZE_REVIEW=True
~~~

After validation, the clean environment removed generated Runtime/Host/Smoke bin/obj directories and ignored Python caches. A cleanup command temporarily deleted 16 previously clean tracked root files on the validation clone, but those exact files were restored from HEAD. Final verification showed no deletion or byte change, and none of the 21 candidate files was affected. The transferred candidate remained byte-identical after validation.

The known missing historical fixture, examples/P11Validation/apexforge.json, remains separate. No historical full-regression PASS is claimed. The clean-machine evidence establishes current transitive-stack and full-closure regression PASS and readiness for human freeze review; it does not declare a freeze or authorize Git mutations.

This sync updates only this existing P12.6-10 evidence document. Production code, tests, predecessor P12.6 evidence, historical fixtures and Git state remain unchanged. No validation suites were rerun during this documentation sync; the final evidence above records the supplied clean-clone validation.

Final P12.6 status:

~~~text
P12_6_TRANSITIVE_FREEZE_STACK=PASS
P12_6_FULL_CLOSURE_REGRESSION=PASS
P12_6_HISTORICAL_FULL_REGRESSION=BLOCKED_HISTORICAL_FIXTURE
P12_6_READY_FOR_FREEZE_REVIEW=True
~~~
