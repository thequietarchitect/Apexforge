# P12.7-2 — Bounded Three-Path Behavioral Equivalence

## Reviewed scope and frozen predecessor

This slice adds a test-only equivalence harness and this evidence document. Canonical AIR remains the sole semantic authority. No production implementation, language semantics, native profile, debugger capability or public target routing was changed. This is readiness for human review, not a milestone freeze, release or canonization.

- Branch: p12-7-equivalence.
- HEAD/base: 56d3ed08a553277b68640d501a5e28b53a8170d3.
- Frozen predecessor: afp-p12.6-freeze, peeled and verified to the same commit before work.
- Initial working tree contained only the untracked P12.7-1 census.
- P12.7-1 census SHA-256 preserved: 7725d77ec2fe1f95e072367452453b011da78701d358b557be5cde075a81fe3a.
- Interpreter verified first: C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe, Python 3.9.13, 64-bit; sys.executable matched that supplied path. The separate Owner-machine Visual Studio interpreter was not used.

New test: apexforge/p12_7_2_bounded_behavioral_equivalence_test.py. New document: docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md. No separate helper module was necessary.

## Concrete APIs inspected before writing

The harness follows the existing owners and result contracts:

- air/model.py: VerifiedAIRProgram(program), StateDefinition and StateAssignment; air/verify.py through AIRVerifier.verify(...).require_verified().
- workflow/air_runner.py: RegistryExecutionPlan, build_default_context and run_air_program(program, entry_directives=(entry,)). The canonical runner reverifies the same AIR and creates its default context.
- runtime/engine.py: ExecutionResult(delta, trace, diagnostics, final_state), ok and RuntimeEngine.execute; runtime/state.py StateSnapshot via its caller/returned contract.
- native_backend/native_execution_contract.py: admit_native_profile, NativeProfileAdmission, PROFILE and I64 bounds. This existing admission is the only domain classifier; it is not copied into test code.
- native_backend/lowering_input.py through existing identity calls: build_verified_air_lowering_input and its canonical transport/fingerprint.
- tooling/trace_integration.py: associate_plan, PlanMetadata, execute_managed_retained, ManagedRetention.validate, execute_native_retained and NativeRetention.validate_snapshot.
- tooling/trace_retention.py: typed evidence/provenance and NativeResultAssociation fields, including output_fingerprint. The comparison retains these associations independently of semantic projection.
- native_backend/source_mapping.py: admission-backed mapped builder, authentic UNMAPPED_SOURCE and generated regions. Hand-authored AIR receives no invented source span.
- native_backend/native_execution.py: real admission/build/dispatch, NativeExecutionEvidence, receipts, locked artifact checks and fixed result decoding. None of this code was duplicated.
- native_backend/result.py, payload.py and value.py: CanonicalExecutionResult/Payload/Value, validation, named I64 decimal representations and name-sorted canonical payloads.
- P12.5 native-profile fixture/plan_for/with_path helpers and native acceptance suite; P12.6 controlled integration tests. Existing fixtures and association validation are reused.

## Exact paths and tested domain

A. Canonical AIR runner: run_air_program on the verified fixture's identical program, with the plan's exact canonical entry.

B. P12.6 managed-retained path: associate_plan(verified, plan), build_default_context(program), execute_managed_retained(binding, context=context); validate returned retention against the canonical owner result and the same default context/runtime configuration.

C. Real bounded native-retained path: execute_native_retained(binding, temporary_build_root), delegating to existing native mapping/admission/build/dispatch, then validate_snapshot against its returned NativeExecutionEvidence. Native receipt, AIR/owner/routing/entry/state IDs, toolchain/source/image/receipt/output associations are checked.

A and B share the existing RuntimeEngine semantic execution owner. This is three execution paths, not three independent executors. No .NET execution is invoked or proven. A .NET carrier/result admission is not presented as execution.

Domain is unchanged apexforge.native.win-x64.i64-literal-state-set/v1: 1–256 explicit INT states, signed-I64 raw/exact AIRIntegerLiteral initializers and literal set_int values; 1–4096 total stores and 1–4096 singleton max_weight decisions; exactly one directive/order-zero and one principal; exact canonical plan ownership/entry; empty ordered actions, events/emissions/effects/invocations and all other excluded authority/function/workflow surfaces. Existing admission enforces all details and limits. Positive fixtures use portable identities within default retention limits.

Tests sample this bounded domain; they do not exhaust its Cartesian product. Existing native acceptance regression covers the 256-state/4096-store maxima and Unicode IDs. The new harness does not change admission or promise whole-language equivalence. It compares canonical initial-state extraction with admitted native initial_values by exact named I64 value, checks each managed context starts unchanged, and verifies AIR identity before/after execution. There is no arbitrary native initial-state override.

## Structural comparison projection

Projection is:

~~~text
(success_boolean, ((state_name, "I64", canonical_decimal_string), ...))
~~~

- Canonical/managed results: extract result.ok and final_state.cells; require exact Python int values (bool is rejected), encode their existing values with str, and delegate I64 range/representation and duplicate-name validation to existing CanonicalExecutionValue/CanonicalExecutionPayload contracts.
- Native results: validate the existing CanonicalExecutionResult, require I64 outputs, extract status == SUCCESS and existing value.name/representation/data.
- Sort extracted values by exact state name, matching canonical StateSnapshot ordering and existing payload canonical ordering. Native raw values remain in state declaration order and that producer order is separately asserted. Only the comparison view is sorted; AIR decisions/actions/stores are never reordered.
- Require exact equality of success, full state-name set, canonical type representation and value across all three paths; supported results must succeed. Managed events/effects must remain absent in this domain. There is no standalone return-value concept common to this profile beyond final named state.

The projector reads result fields only. It does not inspect AIR, apply assignments, predict a final state, evaluate expressions, select a path, resolve a name/type or interpret an operator. Expected behavior comes from the existing canonical runner. A focused AST audit excludes execution/evaluation/apply/resolution calls and program/verified/plan dependencies from projection functions.

Comparator rejection checks demonstrate status, missing-name, wrong-name, wrong-type and wrong-value mismatches fail equality. Exact bool state and native BOOL output are rejected by the domain projection rather than coerced to I64.

## Supported positive cases

Each of these nine cases executes A, B and C twice. No positive native build/dispatch/output is mocked, no native case is skipped, and no infrastructure failure is converted to success.

| Case | Coverage |
| --- | --- |
| zero | One state/one literal set_int, -7 initial to integer zero |
| positive | One state/one set_int, zero initial to 42 |
| negative | One state/one set_int, positive initial to -42 |
| i64_minimum | Maximum initial to -9223372036854775808 |
| i64_maximum | Minimum initial to 9223372036854775807 |
| multiple_reversed_names | Independent assignments to state:z and state:a, with unchanged state:untouched |
| multiple_reversed_declarations | Same program behavior with reversed state declaration order; same final canonical projection as prior case |
| repeated_overwrite_untouched | Existing P12.5 fixture: two successive stores to one state and an untouched maximum-valued state |
| decision_reference_order_and_empty_path | Three singleton decisions, directive reference order differing from declaration order, empty individual path and positive total stores |

Signed-I64 canonical decimal representation has a single zero, 0. No distinct negative-zero integer semantics or noncanonical -0 encoding was invented. All raw/native integer values are signed under the existing I64 contract.

Final state sorting is demonstrated independently of declaration order. Those two reordered fixtures legitimately have different AIR identities, while each fixture's identity is shared across its own three paths and its final behavior agrees with the other order variant.

## Determinism and native no-fallback evidence

New-suite result: 4 unittest methods passed, 9 supported subcases and 4 boundary subcases. The supported method completed 18 canonical runs, 18 managed-retained runs and 18 real native-retained executions/builds. For every case, the second three-path projection exactly equaled the first. Canonical/managed initial context and verified AIR transport remained unchanged. No new requirement equates temporary directories or native binary bytes across repeats.

During C only, RuntimeEngine.execute is guarded to raise AssertionError if called. The existing native execution APIs remain unmocked and return validated backend-issued build/dispatch evidence. Receipt checks bind profile, AIR, exact ownership/routing/entry/state declaration order, source digest, toolchain hashes, image digest and result input receipt fingerprint. Retained native validation checks output/result/provenance associations after normal temporary artifact cleanup. Generated-region count equals admitted states plus stores; admission/mapping preserve the existing schedule. There is no precomputed-answer emitter or test-owned compiler/dispatch implementation.

The guard passed for all 18 live C executions, establishing no RuntimeEngine fallback on tested positives. Existing unchanged native acceptance also passed its no-fallback failure gates and actual execution tests. This evidence supports P12_7_NATIVE_FALLBACK_USED=False for the tested bounded path; it is not a claim about arbitrary future targets.

Causal actions are never cleared. Supported legacy AIR already has empty actions; its entire transport identity remains unchanged. Nonempty ordered actions are a rejection boundary. Existing P12.6 predecessor tests freshly confirmed ordinary compiler actions remain intact and rejected by native v1.

## Unsupported-domain boundaries

All four programs first pass canonical AIR verification. Native admission raises NATIVE_PROFILE_UNSUPPORTED. require_common_domain delegates to admission and converts only that code to OutsideCommonDomain with classification NATIVE_PROFILE_LIMIT. Other native errors, such as invalid routing, remain errors and are not silently excluded.

| Boundary | Actual outcome |
| --- | --- |
| Additional BOOL state | Outside common domain; native rejects the state representation |
| add_int assignment | Outside common domain; native rejects the operation |
| Two alternative causal paths | Outside common domain; native rejects non-singleton paths |
| Nonempty ordered actions | Outside common domain; native rejects the carrier; actions remain unchanged |

RuntimeEngine.execute, native toolchain discovery and native dispatch are failure-trapped while invoking the harness on each excluded program: all classifications occurred before any execution/compiler/dispatch. Each program's AIR transport remained unchanged. After that guard, canonical runner and managed-retained execution both succeeded and their full owner results matched. Native rejection therefore does not impose a requirement for canonical/managed failure, and excluded input is never labeled equivalent or silently executed through fallback.

These are expected NATIVE_PROFILE_LIMIT outcomes, not semantic defects. Broader rejected surfaces remain covered by unchanged native-profile/native-acceptance tests instead of duplicating their full matrices.

## Intentionally excluded comparison surfaces

Only success and typed named final values enter the semantic projection. Receipt/input fingerprints, native image and generated-C hashes, toolchain identity/options, temporary artifact paths, backend provenance scopes, source/native association fingerprints, timing, trace carriers and non-behavior-changing diagnostics do not enter it. Their integrity is validated under their owning contracts rather than requiring cross-backend equality.

Managed result/retention hashes and native receipt-bound CanonicalExecutionResult hashes hash different material; equality would be an invalid equivalence criterion. Managed runtime/causal/authority traces and native artifact/output evidence differ intentionally. Generated C regions are static correspondence, not proof of per-store runtime trace. Native final state and SUCCESS are compared; no machine-address trace or debugger instrumentation is introduced. Diagnostics that change result.ok still change the behavioral success projection.

## Executed validation and predecessor regression

All test executions used the verified LYRA interpreter with -X utf8 -B. The new test ran first and passed before predecessor regression.

| Suite | Invocation / selection | Actual result |
| --- | --- | --- |
| New P12.7-2 bounded test | Direct script | 4 tests PASS; 9 supported cases repeated twice, 4 excluded cases; 67.035 s |
| P12.5 native profile | Direct p12_5_native_profile_contract_test.py | 7 tests PASS; 0.043 s |
| P12.5 native acceptance | Existing p12_5_native_execution_acceptance_test.NativeTests selected by unittest loader | 13 tests PASS; 12.229 s |
| P12.6 metadata identity | Direct p12_6_3_metadata_identity_association_test.py | 8 tests PASS; 0.049 s |
| P12.6 source/native mapping | Direct p12_6_4_source_native_mapping_test.py | 11 tests PASS; 8.899 s |
| P12.6 trace/provenance | Direct p12_6_6_trace_provenance_reference_test.py | 12 tests PASS; 4.103 s |
| P12.6 controlled trace integration | Direct p12_6_8_controlled_trace_integration_test.py | 12 tests PASS; 16.555 s |

All six predecessor suites finished in one fail-fast sequential invocation, exit 0: 63 top-level predecessor tests, no failures/errors. Total new plus predecessor top-level methods: 67; subcases and nested checks are not inflated into that count.

Exact direct command pattern:

~~~powershell
& 'C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe' -X utf8 -B apexforge/<suite>.py
~~~

The native acceptance selection used its unchanged NativeTests class to avoid its __main__ report writer overwriting the tracked p12_5_rcv_54_native_execution_acceptance.json:

~~~python
import sys, unittest
sys.path.insert(0, 'apexforge')
suite = unittest.defaultTestLoader.loadTestsFromName(
    'p12_5_native_execution_acceptance_test.NativeTests')
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
~~~

No assertions or coverage were modified. No historical full repository regression was run. No missing historical project fixture was synthesized or invoked as an extra gate.

## Failures, classifications and limitations

No SEMANTIC_FAILURE, IMPLEMENTATION_DEFECT or TEST_FIXTURE_DEFECT occurred in executed tests. No production edit was needed. The four negative boundaries are expected NATIVE_PROFILE_LIMIT classifications. The mismatch unit cases deliberately exercise SEMANTIC_FAILURE assertion paths without manufacturing failing native executions.

The initial unprivileged shell process setup failed in the tool environment, and the first new-suite call was interrupted by server restart before producing a result. Classification: ENVIRONMENTAL_BLOCKER for validation orchestration, not program semantics. Repository state was rechecked before the successful fresh test run; no interrupted run was counted as a pass. Normal approved shell execution with the supplied interpreter ran successfully. No environment policy bypass, interpreter substitution, dependency installation or toolchain modification was used.

OBSERVABILITY_GAP remains: native v1 has final-state/result provenance, not per-operation runtime traces. Test passes do not prove full intermediate trace equivalence. Independent .NET execution remains unproven/unsupported by these APIs; no .NET executor was added. Cross-toolchain binary identity, performance, persisted artifact admission, public target selection and wider AIR remain excluded. No PDB, machine-address debugging, runtime instrumentation or P13 feature is enabled.

## Final repository review

P12.6 tracked worktree diff and index diff are empty. P12.7-1 census remains byte-identical to the captured hash above. Native temporary directories are cleaned by their existing lifecycle APIs. No production files, predecessor tests or tracked acceptance reports were changed. The sole new P12.7-2 test and sole new P12.7-2 evidence document are the only additions to the incoming census file. Nothing is staged; no commit, tag, release or push was made. P12.7-3 was not begun.

Exact final git status --porcelain=v1 --untracked-files=all:

~~~text
?? apexforge/p12_7_2_bounded_behavioral_equivalence_test.py
?? docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md
?? docs/p12/P12_7_2_BOUNDED_THREE_PATH_BEHAVIORAL_EQUIVALENCE.md
~~~

## Evidence markers

~~~text
P12_7_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_7_CANONICAL_AIR_EQUIVALENCE=PASS
P12_7_MANAGED_RETAINED_EQUIVALENCE=PASS
P12_7_NATIVE_EQUIVALENCE=PASS
P12_7_THREE_PATH_EQUIVALENCE=PASS
P12_7_EQUIVALENCE_DOMAIN_BOUNDED=True
P12_7_NATIVE_PROFILE_EXPANDED=False
P12_7_NATIVE_FALLBACK_USED=False
P12_7_CAUSAL_ACTIONS_STRIPPED=False
P12_7_DETERMINISTIC_RESULT_PROJECTION=PASS
P12_7_OUT_OF_DOMAIN_FAILS_CLOSED=True
P12_7_THREE_INDEPENDENT_EXECUTORS_CLAIM=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
P12_7_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_7_2_READY_FOR_REVIEW=True
~~~
