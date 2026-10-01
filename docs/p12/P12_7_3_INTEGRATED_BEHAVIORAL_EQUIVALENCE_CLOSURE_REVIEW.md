# P12.7-3 — Integrated Behavioral Equivalence Coverage and Closure Review

## Outcome and authority

**Outcome A: the bounded behavioral-equivalence test implementation satisfies the reviewed P12.7 charter. No further P12.7 implementation/test stage is required by the evidence reviewed here.** All remaining limitations below are explicit, non-blocking for the actual claim, or deferred. Full closure regression and freeze readiness remain a separate, unperformed next stage; this review does not declare the milestone frozen, canonized or released.

Canonical AIR remains the sole semantic authority. The justified claim is:

~~~text
canonical AIR runner == managed-retained RuntimeEngine path == bounded native execution
~~~

This means matching success and complete typed named final state on the nine tested common-domain fixtures admitted by apexforge.native.win-x64.i64-literal-state-set/v1, each repeated twice from equivalent default initial conditions. It is executable sampled evidence, not a universal proof over every admitted graph or I64 value. Canonical and managed-retained share RuntimeEngine; neither the claim nor the implementation implies three independent semantic engines or independent .NET AIR execution.

## Frozen baseline and incoming artifacts

- Branch: p12-7-equivalence.
- HEAD and expected P12.6 predecessor commit: 56d3ed08a553277b68640d501a5e28b53a8170d3.
- afp-p12.6-freeze peeled to that exact commit. The worktree diff against the frozen commit and the index diff were empty before review.
- Incoming Git status contained exactly the three requested untracked P12.7-1/P12.7-2 paths.

Captured and rechecked SHA-256 values:

| Preserved artifact | SHA-256 |
| --- | --- |
| docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md | 7725d77ec2fe1f95e072367452453b011da78701d358b557be5cde075a81fe3a |
| apexforge/p12_7_2_bounded_behavioral_equivalence_test.py | a83117f202937a2607fd0dbe02fd328f537a882ecc994d99339e4590f922b9cf |
| docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md | 04ee41b9c74f228b17295c14dd3d41ae3797bd359a772c0eca02d850897f6239 |

The latter two match the hashes captured at the end of P12.7-2, as does the census. No production file or predecessor test was modified by P12.7. This slice creates exactly this review document.

## Integrated census and implementation review

P12.7-1 identified a nonempty comparison domain for the P12.6 Python managed-retained path and the native v1 profile, while explicitly separating that path from the .NET admission/representation layer. It found a joining-test coverage gap, not a need for a new semantic evaluator or result schema. It excluded ordinary compiler AIR with nonempty CausalPath.actions and retained authentic missing source correspondence for legacy hand-authored fixtures.

P12.7-2 closes that joining gap using existing P12.5 fixture/plan_for/with_path helpers, canonical constructors, AIRVerifier and the existing admission and retention APIs. The test-only compare_case orchestration verifies once, builds the exact plan and associates it with verified content identity; it checks admitted initial values against the canonical default context, then runs the following paths twice:

| Path | Actual owner/API and reviewed evidence |
| --- | --- |
| Canonical | workflow/air_runner.py run_air_program reverifies the same program, uses build_default_context and RuntimeEngine.execute with the exact plan entry. |
| Managed-retained | tooling/trace_integration.py execute_managed_retained executes that same RuntimeEngine semantic owner once, using the same verified program/entry and default context; ManagedRetention.validate checks returned owner result and context association. |
| Native-retained | execute_native_retained delegates to source_mapping.build_native_with_mapping and native_execution.build_native/dispatch_native. Real MSVC C compilation and native image dispatch remain unmocked; NativeRetention.validate_snapshot checks retained evidence after cleanup. |

The native chain re-admits inputs, verifies backend issuance and receipt/source/image identity, holds the existing Windows image lock through child exit, and launches only the issued executable with shell=False. It has no interpreter/managed result-producing fallback. The P12.7 positive native calls guard RuntimeEngine.execute with a failure trap; all 18 positive native-retained executions passed that guard and produced validated receipts/results. The trap is a test guard, not added runtime instrumentation or an alternative executor. P12.5 predecessor acceptance also passed actual execution and no-fallback negative gates.

Native membership is delegated to the unchanged admit_native_profile. require_common_domain converts only NATIVE_PROFILE_UNSUPPORTED into OutsideCommonDomain/NATIVE_PROFILE_LIMIT. Other errors propagate; the test does not invent eligibility or treat build/dispatch/retention errors as an equivalent successful run.

No action-removal API or rewrite exists in the test. Positives are genuine legacy fixtures already carrying empty ordered actions. Full verified transport is compared before/after; the nonempty-actions negative remains nonempty and rejected. Frozen compiler action behavior and P12.6 source/native association contracts remain unchanged. Legacy positives are explicitly UNMAPPED_SOURCE, not falsely compiler-produced.

## Common domain and coverage boundaries

The native profile remains apexforge.native.win-x64.i64-literal-state-set/v1. Admission requires exact reviewed canonical dataclasses/field shapes and tuple containers; canonical verification; one directive (order zero)/principal; exact entry and identical owning/program transport; 1–256 explicit canonical INT states initialized by exact int or AIRIntegerLiteral within signed-I64 bounds; 1–4096 singleton max_weight decisions, each referenced once in directive order; 1–4096 total literal set_int assignments. An individual path may be empty if total stores remain positive. Ordered actions, emits, effects and invocations are empty, as are unsupported program authority/event/function/workflow surfaces and role/authority attachments.

The tested intersection additionally uses the default canonical context, portable metadata identities and successful complete-mode retention within the existing limits. No custom initial state/policy/runtime or broader source-language executability is implied. The harness does not silently expand admission when a different path supports more language constructs.

### Nine supported fixtures

| Fixture | Proven dimensions |
| --- | --- |
| zero | Singleton state, one set_int; -7 initial to 0. Signed-I64 has one canonical zero; no distinct -0 semantics. |
| positive | Singleton state, one set_int; 0 initial to 42. |
| negative | Singleton state, one set_int; 7 initial to -42. |
| i64_minimum | Singleton state; maximum initial to -9223372036854775808. |
| i64_maximum | Singleton state; minimum initial to 9223372036854775807. |
| multiple_reversed_names | Three states, two independent mutations (11/-11), untouched minimum state, declaration order differing from name order. |
| multiple_reversed_declarations | Same behavior with reversed declaration order; exact same canonical final projection as preceding fixture. |
| repeated_overwrite_untouched | P12.5 two-state fixture; two stores (41 then 42) to one state, untouched maximum state. |
| decision_reference_order_and_empty_path | Three singleton decisions, references ordered differently from declaration order, empty individual path, repeated target mutation and positive total stores. |

Every fixture checks shared per-fixture AIR/routing/entry identity, equivalent initial named state, final-name/type/value bijection, success, canonical name ordering, native declaration-order output, repeat equality and unchanged AIR/context. The two declaration variants legitimately have different AIR identities but equal final behavior; different programs are not forced to share an identity.

These cases cover all required P12.7-2 dimensions: singleton/multiple state mutation, admitted repeated assignment, zero, positive/negative I64, both extrema and canonical/deterministic state ordering. They do not exhaust I64 values, graph sizes, identity strings or combinations. Existing native acceptance separately covers Unicode and the 256-state/4096-store maximum; it is not relabeled a nine-case three-path test. Identical repeated stores were a census suggestion; the explicit P12.7-2 requirement was admitted repeated assignment, which overwrite cases demonstrate. This review does not elevate suggestions or exhaustive enumeration into a new closure requirement.

### Four unsupported boundaries

| Fixture | Exact demonstrated exclusion |
| --- | --- |
| bool_state | An additional BOOL state causes native-v1 rejection; not proof of every non-I64 type. |
| add_int | An add_int store causes rejection; not proof of every unsupported operator. |
| alternative_paths | Two paths in a causal decision cause rejection; not all causal-policy/branch forms. |
| ordered_actions | Nonempty ordered actions consisting of the fixture assignments cause rejection; actions are not stripped. |

All four first pass AIR verification. Native admission then raises NATIVE_PROFILE_UNSUPPORTED; the harness classifies them outside the common domain before execution, compiler discovery or native dispatch, with those seams guarded. Transport remains unchanged. Outside the guards, canonical and managed-retained execution both succeed and full returned owner results agree. Native rejection does not incorrectly require those paths to fail. These four classes are the exact P12.7 negative coverage; the broader frozen rejection matrix is predecessor coverage, not a fabricated new blanket claim.

## Comparator audit

Audited functions: snapshot_projection, managed_projection, native_projection and require_equal_projections. compare_case is orchestration and identity/provenance checking, not the comparator or an AIR evaluator. supported_cases constructs inputs; it does not create predicted outputs.

The projection is:

~~~text
(success_boolean, ((exact_state_name, "I64", canonical_decimal_string), ...))
~~~

| Audit requirement | Finding |
| --- | --- |
| No AIR execution/interpretation in projection | Functions read returned fields, sort names, check exact types and invoke existing carrier validators. They receive no program/plan/verified argument and contain no execute/apply/path-selection/operator handling. |
| No independent assignment/expected-state semantics | Expected final behavior comes from run_air_program. No store loop calculates final state, arithmetic computes an answer, or source syntax is interpreted. Constructed mismatch rows are deliberately invalid equality examples, not program oracles. |
| No hidden type/representation divergence | Snapshot requires type(value) is int, excluding bool; str encodes that already-returned integer. Existing I64 validator enforces signed range/canonical decimal. Native outputs must already be validated I64. INT-to-I64 is justified only inside the admitted bounded domain, not generalized to all Apex integers. |
| No silent state loss | All cells/values are retained in tuples; no filter/intersection/key rewriting/case folding. Existing payload validates duplicates. Equality covers full rows, and compare_case separately checks complete declared state names and native producer order. |
| No silent failure loss | Managed result.ok and validated native SUCCESS/FAILURE become the success boolean. Positive cases additionally require True. Exceptions propagate; unexpected events/effects or invalid types reject. Only explicit profile rejection is excluded before comparison. |
| Ordering normalization is observational | Sorting returned names matches frozen StateSnapshot/name-sorted payload contracts. Operation/decision/store order is untouched. Native wire order remains declaration order and is separately asserted. |
| Executable audit support | P12.7-2 passed AST checks excluding execution/evaluation/apply/type-resolution calls and AIR input dependencies, mismatch rejection for status/names/types/values, and exact bool/native BOOL rejection. Manual review traced the validators rather than relying solely on a forbidden-call list. |

Conclusion: P12_7_COMPARATOR_SEMANTIC_IMPLEMENTATION=False. The comparator introduces no second semantic implementation and does not weaken fail-closed behavior. Test assertions were reviewed under the recorded normal Python invocation; no optimized-Python test invocation or new production comparison surface is authorized by this record.

The comparison surface is complete final typed named state plus success for this domain. There is no common scalar-return or user-output-text concept here. Managed event/effect absence is guarded; intermediate delta/trace parity with native is not promised.

## Intentionally non-equivalent evidence and determinism

Native result.input_fingerprint binds the build receipt; managed retention hashes different context/result/diagnostic material. Receipt/image/generated-C/toolchain hashes, backend/source mapping associations, temporary paths, timing, trace-carrier representation and non-behavior-changing diagnostic display are outside cross-path equality. Provenance integrity is checked independently, not discarded. A diagnostic changing ok remains behaviorally visible.

P12.7-2 repeat evidence proves:

- For each of nine fixed fixtures, two canonical executions, two managed-retained executions and two real native executions produce exactly the same semantic projection (18 of each path in the supported-case method).
- AIR transport identity remains unchanged across orchestration; receipt/binding checks tie both native runs to the same verified content/routing. Content identity is not a unique physical-run ID or an assertion that reordered fixtures have equal AIR fingerprints.
- Native signed output decoding produces identical final named I64 values and success on repeated executions under the recorded environment. This does not prove timing, machine-instruction, allocation or cross-toolchain equality.

P12.7 itself does not compare native image bytes, full receipts or temporary paths between repetitions. The unchanged P12.5 acceptance suite independently checks its frozen same-toolchain repeated build/image/receipt/result determinism contract. Those checks remain valid predecessor evidence, not an expanded cross-backend requirement. Generated C ranges are static correspondence; no executed-step trace inference is made.

## Regression evidence reconciliation

P12.7-2 evidence and the recorded execution results are consistent. Source method counts match the recorded selections, and all sources remain unchanged. No rerun was warranted; P12.7-3 performed source/evidence/Git/hash review only.

| Recorded suite | Methods passed |
| --- | --- |
| P12.7-2 bounded equivalence | 4/4 |
| P12.5 native profile | 7/7 |
| P12.5 native acceptance NativeTests | 13/13 |
| P12.6 metadata identity | 8/8 |
| P12.6 source/native mapping | 11/11 |
| P12.6 trace/provenance | 12/12 |
| P12.6 controlled integration | 12/12 |

Six predecessor suites sum to 63/63; with the new suite there are 67 passing top-level methods. Subcases/nested checks are not added to those totals. P12.7-2 verified LYRA Python 3.9.13, 64-bit, used -X utf8 -B, ran the new suite before predecessors, and reported zero test failures/errors. The native acceptance class was selected with unittest rather than its report-writing __main__, preserving the tracked JSON report without changing assertions. No production correction or frozen-file modification occurred. Initial tool/server orchestration interruptions produced no claimed pass and were superseded by the successful execution recorded in P12.7-2.

This review does not convert those targeted predecessor passes into a full closure-regression pass. No historical full regression, full P12.7 closure regression, freeze preparation or machine configuration work was performed in P12.7-3.

## .NET and stronger-claim limits

Live ManagedRuntimeHost.cs admits/validates envelope, payload, result and handoff. Runtime.Host/Program.cs starts/stops lifecycle; it does not execute AIR. Frozen RCV-48 records structural decoder construction and deferred execution/host payload wiring. No P12.7 artifact adds a .NET executor. This is a real missing execution capability, not measured .NET semantic divergence. It would block AIR == independent .NET == native, but that is not the explicitly authorized P12.7 three-path claim.

The following stronger claims remain unproven and are not made: whole-language equivalence; arbitrary AIR equivalence; independent managed semantic-engine equivalence; independent .NET AIR execution; native intermediate-step trace equality; machine-instruction equality; performance equality; memory-behavior equality. A shared semantic owner is stated explicitly rather than silently renamed as independent managed semantics.

## Remaining-gap matrix and closure impact

One primary classification is used per row. Non-blocking means non-blocking for this precise tested final-behavior charter, not acceptance of broader claims.

| Limitation/finding | Classification | Blocks bounded P12.7? | Disposition |
| --- | --- | --- | --- |
| Census joining-test gap | NO_GAP | No | Closed by P12.7-2 same-fixture three-path comparisons; no additional test stage required. |
| Shared RuntimeEngine for canonical/managed paths | NO_GAP | No | Honest architectural qualification; independence was explicitly not required. |
| No exhaustive I64/graph/identity enumeration or every possible joined fixture | TEST_COVERAGE_GAP | No | Samples satisfy required dimensions. No universal theorem or mandated additional in-domain observable is claimed. |
| Native intermediate per-operation traces absent | OBSERVABILITY_GAP | No | Final state/success are exposed; static C regions are not runtime traces. Trace equality is outside charter. |
| Wider types/operators/functions/authority/events/effects/causal forms/nonempty actions/platforms | NATIVE_PROFILE_LIMIT | No | Existing rejection stays intact; language support elsewhere does not expand native v1. |
| Independent .NET AIR execution absent | SEMANTIC_GAP | No | Blocks a stronger .NET claim only; no executor is created or represented as proven. |
| Different receipt/image/context/trace/mapping identities | PROVENANCE_ONLY_DIFFERENCE | No | Validate owner association; do not equate dissimilar hash preimages or backend evidence. |
| General CLI target selector, custom owners and broader automatic metadata/trace coverage | OBSERVABILITY_GAP | No | Tests use approved APIs/default owners/portable supported retention; public consumer expansion is not required. |
| Whole-backend performance/security/memory equivalence and broader assurance | DEFER_TO_P12_8 | No | Separate backend review responsibility, not promised equality or feature implementation. Existing authority, validation, artifact locks and fail-closed security remain mandatory and preserved. |
| Machine-instruction equality as an additional proof obligation | OBSERVABILITY_GAP | No | Existing native provenance and real final outputs are sufficient for this behavioral claim; no instruction-level oracle is required. |
| Debugger/native step or machine-address mapping, PDBs and runtime instrumentation | DEFER_TO_P13 | No | Outside final-behavior comparison; no debugger functionality added. |

Frozen docs/p12/P12_6_9_INTEGRATED_METADATA_TRACE_COVERAGE_AND_CLOSURE_REVIEW.md separately assigns whole-backend memory/performance/platform closure to P12.8 and per-operation tracing/machine-address/debugger controls to P13. No inspected frozen evidence makes performance/security/memory equivalence a current P12.7 requirement. DEFER_TO_P12_8 is a deferral of broader assurance, not proof of security equivalence or permission to weaken current security contracts. Wider native profile work would require separate authorization even if reviewed later.

No remaining row blocks the actual bounded implementation. No stale-association defect, state/type/failure omission, fabricated native result, fallback or second semantics was found. Full closure regression is pending as a separate acceptance gate; that fact does not create an additional implementation requirement or establish freeze readiness here.

## Decision and recommended next stage

Set P12_7_IMPLEMENTATION_COMPLETE=True **for the bounded test architecture and qualified behavioral claim only**. Set P12_7_CLOSURE_REVIEW=PASS because the integrated review found no blocking inconsistency. This is not whole-language completion, freeze approval or a release decision.

Recommend a separately authorized full P12.7 closure regression/freeze-readiness stage using the preserved artifacts and frozen predecessor contracts. It should validate that stage's explicitly chosen regression gates, preserve historical fixture limitations, and produce readiness evidence for human review. No additional bounded implementation stage is presently necessary. Do not automatically run that stage, prepare a freeze inventory, stage files or create Git objects.

## Repository preservation and final status

Final checks: branch/HEAD/peeled freeze unchanged; git diff --exit-code afp-p12.6-freeze^{commit} -- clean; index empty; all three incoming SHA-256 values identical; only this one review file added. No production/test/evidence corrections. No staging, commit, tag, release or push; no full closure regression or freeze preparation begun.

Exact git status --porcelain=v1 --untracked-files=all:

~~~text
?? apexforge/p12_7_2_bounded_behavioral_equivalence_test.py
?? docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md
?? docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md
?? docs/p12/P12_7_3_INTEGRATED_BEHAVIORAL_EQUIVALENCE_CLOSURE_REVIEW.md
~~~

## Explicit markers

Markers retain the tested-domain and recorded-validation qualifications above.

~~~text
P12_7_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_7_COMMON_EQUIVALENCE_DOMAIN=PASS
P12_7_THREE_PATH_EQUIVALENCE=PASS
P12_7_EQUIVALENCE_DOMAIN_BOUNDED=True
P12_7_NATIVE_PROFILE_EXPANDED=False
P12_7_NATIVE_FALLBACK_USED=False
P12_7_CAUSAL_ACTIONS_STRIPPED=False
P12_7_DETERMINISTIC_RESULT_PROJECTION=PASS
P12_7_OUT_OF_DOMAIN_FAILS_CLOSED=True
P12_7_COMPARATOR_SEMANTIC_IMPLEMENTATION=False
P12_7_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_7_THREE_INDEPENDENT_EXECUTORS_CLAIM=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
P12_7_WHOLE_LANGUAGE_EQUIVALENCE_CLAIM=False
P12_7_NATIVE_INTERMEDIATE_TRACE_EQUIVALENCE_CLAIM=False
P12_7_IMPLEMENTATION_COMPLETE=True
P12_7_CLOSURE_REVIEW=PASS
~~~
