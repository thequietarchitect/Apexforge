# P12.7-4 — Full Closure Regression and Freeze Readiness

## Baseline and scope

Closure validation was performed on LYRA on 2026-09-30. Branch: p12-7-equivalence. HEAD and peeled afp-p12.6-freeze both equal 56d3ed08a553277b68640d501a5e28b53a8170d3. Before testing, tracked worktree and index diffs were empty and exactly four expected P12.7 candidates were untracked. No unexpected untracked source, build output or cache existed. No production implementation, predecessor suite, project configuration or frozen report was edited.

The authorized claim remains canonical AIR runner == managed-retained RuntimeEngine path == bounded native execution, within the tested common domain of apexforge.native.win-x64.i64-literal-state-set/v1. It is not proof of three independent semantic engines or independent .NET AIR execution. Canonical AIR remains the sole semantic authority.

Common domain: 1–256 signed-I64 INT states; literal set_int; singleton causal paths; one directive/principal; empty ordered causal actions under frozen v1 admission. The fixtures sample this domain rather than enumerate every state count, I64 value or graph. No native profile expansion, causal-action rewriting, interpreter fallback or second evaluator was introduced.

## Incoming candidate integrity

The following SHA-256 values were captured before testing and matched after all tests and cleanup:

| Candidate | SHA-256 |
| --- | --- |
| apexforge/p12_7_2_bounded_behavioral_equivalence_test.py | a83117f202937a2607fd0dbe02fd328f537a882ecc994d99339e4590f922b9cf |
| docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md | 7725d77ec2fe1f95e072367452453b011da78701d358b557be5cde075a81fe3a |
| docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md | 04ee41b9c74f228b17295c14dd3d41ae3797bd359a772c0eca02d850897f6239 |
| docs/p12/P12_7_3_INTEGRATED_BEHAVIORAL_EQUIVALENCE_CLOSURE_REVIEW.md | 061895b8849d08962bd6de12f15112a0a02b598144785b5e45fb52c51dc35b53 |

Candidate count before validation: 4. This document is the sole new source/evidence path created in P12.7-4; final candidate count: 5. git diff --check was clean. Because candidates are untracked, each was additionally checked with git diff --no-index --check against NUL. Normal difference exit status and LF-to-CRLF warnings were not treated as whitespace failures; no line endings were rewritten.

## Interpreter and toolchain

Verified interpreter: C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe, Python 3.9.13, 64-bit; sys.executable matched the supplied LYRA path. All top-level Python tests used -X utf8 -B. The unchanged transitive scripts select sys.executable with -B and propagate PYTHONUTF8=1; some nested frozen subprocesses nevertheless generated caches, which were inventoried and removed. The separate Owner Visual Studio Python was not used.

.NET SDK: 10.0.400. Normal dotnet restore --nologo was performed for the unchanged ApexForge.Runtime, ApexForge.Runtime.Host and ApexForge.Runtime.Smoke projects because the authoritative stack builds with --no-restore. All three restores succeeded. No toolchain, project or Windows Application Control policy was altered.

Actual native receipt/tool discovery identifies MSVC 14.51.36231, HostX64/x64:

~~~text
C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\HostX64\x64\cl.exe
~~~

A separate real production execute_native invocation and existing _toolchain discovery were compared; discovered tool hashes equaled the actual receipt's toolchain entries. Identity evidence:

| Evidence | SHA-256 / fingerprint |
| --- | --- |
| cl.exe | E6D57100C82AE0310C18B16ABFE52BC0DF8FBB272CA6C5FB287D485807CFCE91 |
| link.exe | 3EF8FCF80D409FAB22DDD89EE19249F31A26AD9914D3E3E48573C30998FA24DE |
| kernel32.lib | 341C7D56125A03B458E4D5093E4C79B33123CCFDFD610FE236937B8E6F3134BB |
| Execution receipt | 47278AFED865903EACA8CEA25CFDFBD66AA5C88A74445FA47B7151C709DCA1B9 |
| AIR | E2BF031B6C1D82AC1FD83DAA1989A6F127EA3B286016479178A2115B3E96D77C |
| Native image | 1B75E5B4B507D9C96E440903877036992D777F16870F73A4AF64CA6A06B35D0A |

The frozen discovery also hashes companion DLLs. Its mspdb DLL identity is toolchain provenance, not activation of debugging. Native compiler options remain:

~~~text
/nologo /TC /W4 /WX /Od /GS- /Zl /Brepro program.c /Foprogram.obj /Feprogram.exe /link /Brepro /INCREMENTAL:NO /MACHINE:X64 /SUBSYSTEM:CONSOLE /ENTRY:apexforge_entry /NODEFAULTLIB kernel32.lib
~~~

No native PDB/debug/instrumentation option was enabled. Unchanged managed Release builds produced their ordinary PDB files; those were temporary generated artifacts and were removed, not added to the candidate.

## Authoritative P12.7 suite

Unchanged direct invocation: LYRA Python -X utf8 -B apexforge/p12_7_2_bounded_behavioral_equivalence_test.py.

Actual result: 4/4 unittest methods PASS, exit 0, unittest duration 59.383 seconds. Nine positive subcases each ran twice through canonical AIR, managed-retained and real native-retained execution: 18 executions per path. All THREE_PATH_REPEAT markers passed. Four unsupported subcases returned OUTSIDE_COMMON_DOMAIN=NATIVE_PROFILE_LIMIT.

Positive dimensions: singleton assignment; zero; positive and negative I64; minimum and maximum I64; independently assigned multiple states with untouched state preservation; reversed declarations with matching canonical output ordering; repeated assignment; directive decision reference order and an empty individual singleton path. This is sampled bounded behavioral coverage, not exhaustive I64 equivalence.

Unsupported boundaries: additional BOOL state, add_int, two alternative causal paths, and nonempty ordered causal actions. Native admission rejected each before execution/build/dispatch. Canonical and managed paths were not required to reject them and succeeded as tested. No case was silently relabeled equivalent or sent through fallback.

Projection remains structural: success plus the complete, sorted tuple of exact state name, I64 representation and canonical decimal value. Strict integer validation rejects bool. The projector extracts existing results, does not inspect/evaluate AIR or decide operator semantics, and does not discard states or failures. Expected behavior comes from the canonical owner. Same admitted AIR and logical initial state are checked for each path; reordered declaration fixtures can have distinct AIR identities while producing the same final projection.

RuntimeEngine.execute is failure-trapped during positive native execution; existing admission, lowering, compilation and dispatch remain live and unmocked. Native receipts/results/retention associations validate profile, AIR, routing, source, toolchain and image provenance. All 18 native comparisons passed this guard. Native fallback was not used. Existing ordered actions were preserved, including rejected nonempty actions.

Repeated runs prove deterministic semantic result projection and unchanged verified AIR identity for these fixtures. They do not require equal temporary paths, timing, native binary bytes, receipt hashes, toolchain metadata or trace-carrier representation across backends. Provenance and source/trace associations are validated under their owning contracts rather than made semantic equality criteria. No intermediate native trace, machine-instruction, performance or memory equivalence is claimed.

## Six unchanged predecessor suites

All used LYRA -X utf8 -B. Direct script invocation was used except native acceptance, whose existing NativeTests class was loaded with unittest to avoid overwriting the tracked p12_5_rcv_54_native_execution_acceptance.json report.

| File / selection | Successful closure result | Duration (s) |
| --- | --- | ---: |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS | 0.035 |
| apexforge/p12_5_native_execution_acceptance_test.py: NativeTests | 13/13 PASS | 15.400 |
| apexforge/p12_6_3_metadata_identity_association_test.py | 8/8 PASS | 0.045 |
| apexforge/p12_6_4_source_native_mapping_test.py | 11/11 PASS | 9.150 |
| apexforge/p12_6_6_trace_provenance_reference_test.py | 12/12 PASS on one unchanged retry | 2.402 |
| apexforge/p12_6_8_controlled_trace_integration_test.py | 12/12 PASS | 17.989 |

Successful aggregate: 63/63. This is not a claim that every first invocation passed. The first trace suite ran 12 tests in 3.931 seconds with 11 passes and one PermissionError at line 258 while appending a byte to its temporary program.exe. The fail-fast sequence stopped before controlled integration. Classification before retry: ENVIRONMENTAL_BLOCKER, temporary artifact access denial; no specific locking process or policy cause was established. One unchanged rerun passed 12/12, followed by the previously unrun integration suite passing 12/12. No assertion, code or expected result was weakened. No lingering semantic failure was found.

Non-mutating acceptance selection:

~~~python
import sys, unittest
sys.path.insert(0, 'apexforge')
suite = unittest.defaultTestLoader.loadTestsFromName(
    'p12_5_native_execution_acceptance_test.NativeTests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
~~~

## Adjacent semantic regression

Nine unchanged direct-script gates passed, each exit 0. Their assertion-based smoke scripts are counted as scripts, not inflated into unit-test totals.

| File under apexforge/ | Material coverage | Elapsed (s) |
| --- | --- | ---: |
| air_verifier_smoke_test.py | Canonical identifiers, principals, state/check and duplicate rejection; module-level assertions | 0.201095 |
| air_program_linker_smoke_test.py | main: canonical linked execution, ordering, collision/version/empty rejection | 0.259783 |
| runtime_state_consolidation_smoke_test.py | main: immutable typed state, bool/int distinction, state deltas | 0.248882 |
| authority_consolidation_smoke_test.py | main: principal/grant checks and transactional allowed/denied execution | 0.2519682 |
| causal_model_consolidation_smoke_test.py | main: causal identities, multiple causes/paths and invocation preservation | 0.2626826 |
| registry_linked_directive_execution_smoke_test.py | main: 13 named linked-execution tests below | 0.2455097 |
| p12_1e_deterministic_canonical_result_cross_target_smoke_test.py | main: value/result validation, fingerprints, static .NET carrier contract | 0.2246417 |
| p12_2c_verified_air_lowering_input_seam_smoke_test.py | main: verified transport ownership/fingerprint seam | 0.224635 |
| p12_2d_registry_execution_plan_binding_smoke_test.py | main: plan ownership, order, fingerprints and mismatch rejection | 0.2177967 |

The 13 registry-linked functions actually exercised were test_local_and_external_ordering_equivalence, test_child_failure_rolls_back_caller_and_unknown_is_run002, test_local_intermediate_discovers_external, test_nested_multi_program_dependency_closure, test_mixed_case_reference, test_registry_cycle_preserves_run003_and_rollback, test_unselected_paths_and_branches_do_not_execute, test_duplicate_invocations_execute_twice, test_exact_shared_principal_coalesces, test_conflicting_shared_principal_is_rejected, test_entered_child_authority_denial, test_role_derived_child_capability_requirement, and test_multi_directive_requirement_owner_is_ambiguous.

Native-profile rejection was also freshly covered by the predecessor profile/acceptance suites; their matrices were not duplicated. The lowering-seam smoke uses a structural wrapper fixture, not independent execution admission. Static .NET carrier checks do not prove a .NET AIR executor. No full historical repository discovery was launched for test volume.

## Authoritative RCV-51 / RCV-50 transitive stack

After normal restores, unchanged apexforge/p12_5_rcv_51_p12_5_recovery_terminal_closure_smoke_test.py was run using LYRA -X utf8 -B. Actual result: exit 0 with P12_5_RECOVERY_TERMINAL_CLOSURE=PASS, P12_5_MANAGED_RUNTIME_BUILD=PASS and P12_5_REGRESSION_STACK=PASS, plus semantic-authority, provenance, determinism and freeze-preservation markers.

RCV-51 invokes unchanged RCV-50, requires its exit 0 and P12_5_RCV_50_RECOVERY_CLOSURE_AUDIT=PASS before it can pass. RCV-50 checks and runs 46 recovery predecessor scripts and 25 P12 predecessor smoke scripts, builds/runs the three managed projects, and checks frozen ancestry, provenance/security boundaries, absence of hidden execution semantics and empty index. Therefore this invocation establishes the required 46/46 and 25/25 nested gate selections passed; these are script counts, not independent unit-method totals. RCV-51 captures RCV-50 stdout, so its child marker lines were not separately printed at the top-level terminal. No independent second RCV-50 invocation was necessary. A wall duration was not emitted by this unchanged terminal script and is not invented here.

Application Control status: no 0x800711C7 or other Application Control block occurred in this actual LYRA stack invocation. No policy weakening or bypass was performed. Historical frozen evidence in docs/p12/P12_6_10_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md separately records earlier LYRA blocks and a subsequent unchanged clean-machine PASS on DESKTOP-SOI356R. Those historical facts are retained; the present PASS is based on the new LYRA result, not substituted clean-machine evidence.

## Failure classification and historical boundary

| Event | Classification | Disposition |
| --- | --- | --- |
| Initial temporary native executable access denial in trace predecessor | ENVIRONMENTAL_BLOCKER | One unchanged retry passed; root cause not attributed beyond access denial. |
| First standalone toolchain inspector import selected apexforge.py rather than package | TEST_INVOCATION_DEFECT | Corrected only -c sys.path ordering, placing repository root ahead of apexforge; actual receipt inspection then passed. All nine regression scripts had already passed. |
| Restricted shell helper setup failure in validation orchestration | ENVIRONMENTAL_BLOCKER | Approved execution environment used; no failed setup counted as a test pass. |
| Four deliberately excluded native inputs | NATIVE_PROFILE_LIMIT | Expected fail-closed boundaries, not regressions. |
| Absent historical examples/P11Validation/apexforge.json | HISTORICAL_CONTRACT_BLOCKER | Remains absent; no fabrication or restoration, no historical full-suite PASS claimed. |

No SEMANTIC_FAILURE, IMPLEMENTATION_DEFECT, TEST_FIXTURE_DEFECT, GOVERNANCE_CONFLICT or UNSUPPORTED_TARGET required a code correction. No production edit or P12.7 test edit was made. Native intermediate tracing remains an OBSERVABILITY_GAP outside the bounded final-result claim. Broader native AIR support remains a NATIVE_PROFILE_LIMIT, independent .NET execution remains unproven, and deferred backend/debugger work was not begun.

## Cleanup and final repository preservation

Before testing, a hidden/no-ignore repository inventory (excluding .git and node_modules) found zero generated bin/obj/cache/binary files. After the transitive stack, 150 newly generated files were inventoried: outputs under six Runtime/Host/Smoke bin/obj directories and twelve Python __pycache__ directories. Every cleanup directory was absent from baseline files and had no tracked descendants. Absolute cleanup targets were checked to remain inside this repository before native PowerShell Remove-Item -LiteralPath -Recurse removed only those 18 generated directories. Existing native temporary artifacts follow their unchanged lifecycle cleanup. No source/evidence file was deleted.

Post-cleanup inventory found no generated artifacts and no new path beyond the incoming four candidates before this document was written. Final inventory contains only this one additional document. HEAD, branch and peeled freeze remain unchanged. Tracked worktree diff against afp-p12.6-freeze and cached diff are empty; all four incoming candidate hashes match. Tracked report files were preserved. No file is staged; no commit, tag or push was made. No P12.8 work was begun.

Exact final git status --porcelain=v1 --untracked-files=all:

~~~text
?? apexforge/p12_7_2_bounded_behavioral_equivalence_test.py
?? docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md
?? docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md
?? docs/p12/P12_7_3_INTEGRATED_BEHAVIORAL_EQUIVALENCE_CLOSURE_REVIEW.md
?? docs/p12/P12_7_4_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md
~~~

## Freeze-readiness decision

P12.7 is ready for human freeze review for its explicitly bounded test/evidence claim. The authoritative equivalence suite passed; all six predecessors passed with the disclosed resolved access error; materially adjacent semantic gates passed; and the authoritative unchanged transitive stack passed on LYRA itself. Frozen production and incoming candidates are unchanged. The absent historical fixture prevents a historical full-repository PASS claim, but does not invalidate the current bounded behavior or required native/managed transitive gates. Closure PASS here means the authorized P12.7 validation scope, not a universal or historical corpus PASS.

No unresolved in-domain semantic defect or implementation requirement blocks review. The native tracing, wider profile, independent .NET and stronger performance/memory claims remain excluded as in P12.7-3. Readiness is not freeze authorization or a milestone release declaration. The owner retains the commit/tag/freeze decision; this stage stops after evidence and review.

## Evidence markers

~~~text
P12_7_EQUIVALENCE_REGRESSION=PASS
P12_7_PREDECESSOR_REGRESSION=PASS
P12_7_ADJACENT_SEMANTIC_REGRESSION=PASS
P12_7_TRANSITIVE_FREEZE_STACK=PASS
P12_7_HISTORICAL_FULL_REGRESSION=BLOCKED_HISTORICAL_FIXTURE
P12_7_FULL_CLOSURE_REGRESSION=PASS
P12_7_READY_FOR_FREEZE_REVIEW=True
P12_7_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_7_THREE_PATH_EQUIVALENCE=PASS
P12_7_EQUIVALENCE_DOMAIN_BOUNDED=True
P12_7_NATIVE_PROFILE_EXPANDED=False
P12_7_NATIVE_FALLBACK_USED=False
P12_7_CAUSAL_ACTIONS_STRIPPED=False
P12_7_COMPARATOR_SEMANTIC_IMPLEMENTATION=False
P12_7_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_7_THREE_INDEPENDENT_EXECUTORS_CLAIM=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
P12_7_WHOLE_LANGUAGE_EQUIVALENCE_CLAIM=False
P12_7_NATIVE_INTERMEDIATE_TRACE_EQUIVALENCE_CLAIM=False
P12_7_IMPLEMENTATION_COMPLETE=True
~~~
