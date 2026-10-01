# P12.7-1 — Behavioral Equivalence Capability Census

## Scope and verified baseline

This is a documentation-only census of the frozen P12.6 repository, not a milestone release or an implementation change. The explicit P12.7-1 request supersedes the stale P11.4A stage text in AGENTS.md; its authority, safety, frozen-contract and reporting rules remain applicable.

- Branch: p12-7-equivalence.
- HEAD and expected base: 56d3ed08a553277b68640d501a5e28b53a8170d3.
- Annotated tag afp-p12.6-freeze: object 0c1b1fb722bf76bc5df3f7ffc67dc1d4d82f1577; peeled commit 56d3ed08a553277b68640d501a5e28b53a8170d3.
- Initial git status --short: empty. Tracked worktree/index diff against the peeled freeze: empty.
- No existing tracked P12.7 implementation or test artifact was found by the repository file census.

All architecture findings below derive from this checkout. Historical P12.6-10 validation is contextual evidence, not a fresh test pass on this machine.

## Semantic authority and the meaning of managed

Canonical AIR is the semantic authority. AIR is a representation and validation contract, not a third independent executable engine. The existing canonical runtime is the allowed executable oracle; no test must implement another AIR evaluator, select causal paths independently, or calculate a new semantic model.

Two managed meanings must be distinguished explicitly:

1. P12.6 tooling's execute_managed_retained is a Python RuntimeEngine execution path. It executes the existing canonical runtime once and retains its returned ExecutionResult. This path is executable today, and can participate in canonical-runner / managed-retained / native comparisons. Canonical and managed executions share the same semantic implementation; they are not independent engines.
2. The first-class CSHARP_DOTNET_MANAGED_RUNTIME target has .NET admission, immutable representations, structural decoding, host lifecycle and result validation. It does not execute the admitted AIR program. ManagedRuntimeHost.AdmitResult validates a caller-supplied result; it does not produce that result by execution. Runtime.Host/Program.cs starts/stops the host only. ManagedExecutableCarrierDecoder constructs function representations, not state execution. RCV-48 explicitly defers execution dispatch and host payload wiring; RCV-49 proves representational equivalence only.

Consequently the frozen repository supports a nonempty common domain for the P12.6 managed path. It does not support a nonempty demonstrated AIR / .NET program-execution / native intersection. Do not advertise the former as evidence of .NET execution. If P12.7 requires .NET execution specifically, safe three-way behavioral implementation is blocked by that actual capability gap; resolving it is a separate explicitly authorized contract, not an incidental test convenience.

## Component and concrete data-structure census

Paths below are repository-relative. Python packages under apexforge retain canonical import owners such as air.model and runtime.engine.

| Responsibility | Exact component/API | Input, output and boundary |
| --- | --- | --- |
| AIR construction | apexforge/language/compiler.py: compile_source_with_map, compile_source_with_operation_evidence, compile_actions, _compile_directive_with_map | CompiledSource(program, source_map); CompilerOperationEvidence ledger; AIRProgram, StateDefinition, StateAssignment, AIRDirective, CausalDecision and CausalPath. Ordered actions are preserved alongside legacy projections. |
| Linking/project construction | apexforge/air/linker.py (used by workflow/air_runner.py); language/project.py: ProjectBuilder, ProjectBuild | Linked AIRProgram; ProjectBuild carries its identical program/VerifiedAIRProgram and executes through RuntimeEngine. |
| Validation | apexforge/air/model.py, air/verify.py: AIRVerifier.verify, VerificationResult.require_verified | VerificationResult(program, diagnostics), VerifiedAIRProgram(program). Verifier checks version, IDs/references, shapes, policies and ownership. A publicly constructed wrapper alone is not proof of verification. |
| Verified content identity | native_backend/lowering_input.py: build_verified_air_lowering_input; air/serialization.py: air_to_dict | VerifiedAIRLoweringInput(verified, transport_json, transport_fingerprint, source_owner). SHA-256 uppercase over UTF-8 canonical JSON, sorted object keys, retained sequence order. Identity serialization does not execute or reverify AIR. |
| Execution planning | workflow/air_runner.py: build_registry_execution_plan, RegistryExecutionPlan.owner_of | RegistryExecutionPlan(program, entry_directive, directive_owners). Resolves reachable invocation graph, links programs and tracks canonical ownership; not a resolved opcode graph or native admission. |
| Routing identity | native_backend/execution_plan_binding.py: bind_registry_execution_plan | RegistryExecutionPlanBinding(lowering_input, execution_plan, entry_directive, directive_owner_ids, routing_fingerprint); compares complete program transport, incorporates sorted owners and entry. |
| Structural lowering/handoff | native_backend/target_neutral_lowering.py, managed_handoff_projection.py | TargetNeutralLoweringProduct(binding, canonical_json, product_fingerprint, schema); ManagedHandoffProjection(schema, verified_air_fingerprint, routing_fingerprint, entry_directive, directive_owner_ids, product_fingerprint). Structural transport/projection only. |
| Canonical executable oracle | workflow/air_runner.py: run_air_program, build_default_context | Reverification, StateSnapshot.from_program_initials, ExecutionContext(state, authority), then RuntimeEngine.execute with explicit entry. |
| Managed runtime execution | runtime/engine.py: RuntimeEngine.execute; runtime/state.py; causality/engine.py: CausalEngine.select_path | ExecutionResult(delta, trace, diagnostics, final_state), StateDelta(assignments, events, effects), StateSnapshot(cells), StateCell(key, value). Actions execute in order; empty actions use legacy assignments/emits/invocations/effects. Singleton max_weight selection needs no competing branch. |
| Managed canonical result production | runtime/engine.py; tooling/trace_integration.py: managed_result_fingerprint | Runtime produces ExecutionResult, whose ok means no error diagnostic. No scalar return field or native CanonicalExecutionResult conversion. Tooling hashes ordered evaluated assignments/events/effects, final cells and diagnostic severity/code/node; trace hashes are separate. |
| .NET admission/representation | runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs, ManagedExecutableCarrier.cs, ManagedExecutableCarrierDecoder.cs, TargetNeutralLoweringHandoff.cs; Runtime.Host/RuntimeHostIngress.cs and Program.cs | CanonicalExecutionEnvelope, CanonicalExecutionPayload/Value/Result, TargetNeutralLoweringHandoff; ManagedExecutableFunction/expression/statement/type records. Host ingress delegates handoff validation. No executable state/decision consumer or result-producing dispatch. |
| Native eligibility | native_backend/native_execution_contract.py: admit_native_profile | NativeProfileAdmission(air_fingerprint, routing_fingerprint, entry, state_ids, initial_values, stores, profile). Exact class/field/schema/container checks; canonical reverification and full owner transport equality; store relocations, never final-state evaluation. |
| Native lowering/generated C | native_backend/native_execution.py: _source, _constant | Admission to ASCII C bytes; volatile __int64 initializations and every admitted store, then WriteFile output. No state IDs enter C identifiers; overwritten stores remain present. Optional region_sink observes generated ranges only. |
| Native compilation | native_execution.py: _toolchain, build_native, OPTIONS | MSVC cl/link x64, fixed /Brepro options, no PDB switches; program.c, program.obj, program.exe. NativeArtifact(image, receipt_json, receipt_fingerprint, _ticket), with process-local issuance registry. |
| Native dispatch | native_execution.py: dispatch_native, _locked_image, _run, execute_native | Re-admission, issuance/receipt/source/image checks, Windows read lock through exit, exact image launch shell=False, bounded file capture and timeout. No managed/interpreter fallback. |
| Native result production | native_execution.py: _decode; native_backend/result.py, payload.py, value.py | NativeExecutionEvidence(result, receipt_json, output_fingerprint); CanonicalExecutionResult(input_fingerprint, status, outputs), CanonicalExecutionPayload(values), CanonicalExecutionValue(name, representation, data). Exactly 8 little-endian signed bytes per declared state; I64 decimal strings, SUCCESS only on successful dispatch. |
| Receipt/provenance | build_native, dispatch_native | Canonical receipt binds profile, AIR, routing, entry, owner_air, state IDs, generated source, toolchain hashes/options and image. Result input_fingerprint is receipt SHA-256; output_fingerprint hashes raw bytes. Ticket/path are dispatch authorization details, not semantics. |
| P12.6 source/AIR metadata | tooling/debug_metadata.py, source_air_mapping.py; compiler producer ledger | SourceIdentity, StateLocator, AssignmentLocator, AIRMetadataIdentity, OperationReference, EvidenceReference, MetadataSidecar, MetadataAssociation; SourceCorrespondence, StructuralLineage, SourceAIRMapping. Exact occurrences, source bytes and producer evidence; UNMAPPED remains explicit. |
| P12.6 native metadata | native_backend/source_mapping.py: emit_native_source_mapping, build_native_with_mapping | GeneratedRegion, NativeSourceMapping, MappedNativeArtifact. Exact admitted initialization/store schedule associated with generated-C byte ranges; no machine-address or executed-operation assertion. |
| P12.6 managed/native trace association | tooling/trace_retention.py, trace_integration.py | ProvenanceScope, typed TAM/Runtime/Causal/Authority/Diagnostic/Native evidence, OperationAssociation, RetainedRecord, TraceCollection, NativeResultAssociation; CompilerMetadata, PlanMetadata, ManagedContextIdentity, ManagedRetention, StreamReference, NativePreDispatch, NativeRetention, NativeFailureObservation. Association remains external to canonical results. |
| Unsupported rejection | native_execution_contract.require/NativeExecutionError; native execution adapters; AIR verifier; .NET admission/decoder; tooling/cli.py | Native profile rejection precedes compiler/filesystem effects. AIR/routing/platform/toolchain/build/dispatch/result errors remain classified exceptions. .NET invalid contracts/shapes throw validation exceptions, not execution outcomes. Public CLI has no general managed/native target selector; absence of dispatch must not be reported as successful unsupported execution. |
| Deterministic comparison opportunities | ExecutionResult.final_state, ok and delta; native result.outputs/status; lowering/plan identity; P12.6 retention validators | Compare already-produced typed named state values and success, validate each provenance chain independently, repeat same input. Existing hashes bind different material and cannot all be equated. |

## Current bounded native profile and exact common domain

Profile remains apexforge.native.win-x64.i64-literal-state-set/v1. Membership is exactly existing admit_native_profile acceptance plus successful execution on its supported Windows x64/MSVC environment; a new test helper must call admission, not duplicate its semantic checks.

Concrete domain constraints from native_execution_contract.py:

- Exact canonical dataclass types and reviewed field inventories; canonical tuples, valid AIR version and verifier acceptance. IDs checked by the profile are nonblank strings of at most 256 characters.
- One directive and one principal. Directive order is exact integer zero; exact canonical entry ID; one casefolded owner key; plan program and sole owner serialize identically to verified AIR. Principal/display and directive-name metadata retain their existing string checks.
- 1–256 states, each explicit canonical INT, with raw exact Python int or exact AIRIntegerLiteral initializers in [-2^63, 2^63-1]; bool is excluded even though Python equality can equate it with int.
- 1–4096 causal decisions. Each has exactly one CausalPath, exact integer weight, string cause/rationale, policy max_weight. Directive references every decision exactly once; no repeated/unused decision. Decision order follows directive.causal_decisions, not program declaration order.
- 1–4096 assignments in total; a particular singleton path may have zero assignments when the total remains positive. Exact StateAssignment, operation set_int, exact verified state ID and signed-I64 literal value. Preserve path assignment order, repeated/identical stores and overwrites.
- Empty program events, authority_checks, requirements, authorities, roles, functions and workflows; no principal roles/authorities or directive checks/authorities. Every path has empty actions, emits, effects and invocations.
- Default canonical initial state and policy/context; no caller-supplied altered state, custom runtime/causality/policy/standard library, entry guard or host effects. Native has no external initial-state input.

| Construct in domain | AIR representation | P12.6 managed path | Native v1 | Canonical final comparison |
| --- | --- | --- | --- | --- |
| Signed-I64 INT literal initial state, including extrema | Yes | Yes | Yes | Exact state ID/type/integer, including untouched states |
| Literal set_int assignment | Yes | Yes | Yes | Exact final integer and SUCCESS/ok |
| Repeated, identical or overwriting stores | Yes | Yes; ordered evaluated delta | Yes; every store emitted | Exact final values; independently check preserved input/store schedule |
| Multiple singleton decisions, including reordered references and empty individual paths | Yes | Yes | Yes within total limits | Directive-reference order and final values |
| One principal/directive without authority requirements | Yes | Yes | Yes | Same explicit entry, canonical state and no events/effects |
| Unicode/case-sensitive canonical state identities | Yes | Yes | Yes (no names in C identifiers) | Exact IDs and typed values; no alias normalization |
| .NET execution of any above construct | AIR can represent | No .NET executor found | Native supports | No three-independent-target claim is available |

P12.6 retained observation imposes additional portability/schema/resource limits, separate from native membership: managed state/fact identities must be retainable, names must satisfy portable metadata checks, records/source size must fit RetentionLimits and complete-mode trace schemas must be supported. Choose portable fixtures/default limits for retained comparisons; reject or explicitly record observation failure without changing owner behavior. Do not silently shrink or broaden the production native profile to fit metadata.

Ordinary compiler source is not a common native domain: compiler-produced CausalPath.actions is nonempty, including for simple literal stores, and native admission rejects it. Use authentic verified legacy AIR fixtures with absent source correspondence. Never clear actions, transplant a source map, or pretend a hand-authored fixture was compiler-produced.

## Behavioral observables and permitted differences

| Observable | Legitimate contract today | Category/limit |
| --- | --- | --- |
| Initial/final state | Same exact initial IDs and signed integer values; final named state set, type and value must agree, including untouched cells | Semantic/result equivalence |
| State paths | Exact canonical state IDs and admitted relocation target; no prefix removal, alias substitution or case folding of state keys | Semantic identity; nested traversal is excluded |
| Result value/type | In this subset the externally observable result is all final INT cells, represented as native I64 strings. No standalone scalar return, void/null value, function-return or stdout-text contract | Result equivalence |
| Operators/causal schedule | set_int only; same directive decision order and path assignment order, no removal of repeated stores; one path means canonical selection is unambiguous | Semantic equivalence plus structural preservation; final state alone cannot prove every intermediate store ran |
| Deterministic ordering | StateSnapshot sorts cells by key; native raw output/values follow AIR state declaration order; payload canonical_form sorts names. Compare bijective named typed cells in a common sorted view, separately check producer order | Representation difference; do not reorder operations |
| Success/failure | Managed ExecutionResult.ok=True agrees with native SUCCESS on admitted positives; compare no events/effects and no error diagnostics | Result equivalence on common domain only |
| Unsupported AIR/target | Native explicitly rejects outside profile before compile/dispatch, no fallback. Managed may legitimately execute that AIR. No .NET execution API exists to exercise | Capability outcome, not required semantic equality outside intersection |
| Exceptions/errors | NativeExecutionError.code distinguishes profile/AIR/routing/platform/toolchain/build/artifact/launch/timeout/process/result failures. Managed diagnostics and RuntimeExpressionError/verification failures are different contracts | Classify semantic failure versus admission/infrastructure/observation failure; do not force identical exception types/text or fabricate FAILURE results |
| AIR fingerprints | Same canonical transport bytes/fingerprint and routing/entry/owner associations for the actual fixture | Shared input identity, not behavioral proof by itself |
| Execution-result fingerprints | Native result hashes receipt input + status + payload hash; managed_result_fingerprint hashes evaluated delta/final cells/diagnostic identities. Repeat each within its path; compare normalized typed cells directly across paths | Full hashes intentionally unequal; output hash is raw bytes, not payload hash |
| Provenance associations | Validate AIR/routing/entry/owners, generated C/receipt/image/output/result links against their actual owners | Correct path associations required; backend-specific scopes/receipts may differ |
| Causal action preservation | AIR transport and original actions remain unchanged. Admitted positives already have empty actions; nonempty actions remain a rejection negative | Structural invariant; no semantic rewriting for native convenience |
| Runtime traces | Managed has runtime/causal/authority trace steps, evaluated delta and diagnostic tuples; retention preserves stream ordinals/interleaving | Diagnostic metadata may differ from native; no cross-backend trace-count/record equality |
| Native traces/results | Native returns final-state evidence and artifact/output/result provenance only; no per-store runtime trace, assignment-occurrence execution association or machine address | Intentionally non-equivalent observability; C regions are static mappings, not execution traces |

Timing, temporary paths, backend trace records, generated-C identity, build receipts and nonsemantic machine/toolchain metadata may differ across paths. Native repeated whole-image/receipt identity is only asserted under its existing same-toolchain determinism policy. A changed toolchain receipt does not itself imply a changed program result. Diagnostic display text is not program semantics; a diagnostic changing success/failure is not excused as presentation metadata.

## Existing tests: actual proof and limits

The repository census read all tracked P12.5 test scripts and all four P12.6 test scripts. No existing single test compares canonical runner, P12.6 managed-retained execution and native execution for the same fixture. No test supplies three independent program executors.

| Existing test(s) | What inspected assertions prove | What they do not prove |
| --- | --- | --- |
| p12_5_native_profile_contract_test.py (7 test methods) | Exact profile acceptance, order/extrema, canonically verified rejection matrix, routing/invalid AIR, subclass/container rejection, bool/int ownership trap, no evaluator/process dependency | Native live output or managed/native final agreement |
| p12_5_native_execution_acceptance_test.py: test_actual_execution_and_canonical_oracle | Live native named final values equal run_air_program final cells; receipt AIR/routing/image/source binding | Managed-retained path comparison, .NET execution, full result/trace equality |
| Same file: determinism, minimum, maximum/Unicode, store-preservation and negative tests | Real native output, repeated image/receipt/result determinism, extrema/limits, stores retained in C, artifact tamper/write lock, timeout/build/capture rejection and no fallback | Every boundary fixture is not separately compared with canonical/managed; final values do not prove intermediate native trace |
| p12_5_execution_completion_census_test.py | Wrapper/plan shapes, verifier rejection, structural lowering determinism and plan mismatch; lifecycle-only DLL exports | Historical structural census predates bounded executable native addition; not current native incapability or behavioral equivalence |
| P12.5 RCV-2 and RCV-5 through RCV-14 | Lineage, host topology/startup/ingress and handoff contracts/type choice | Program execution |
| RCV-15 through RCV-27 | Managed handoff/projection implementation and compatibility probes, transport/ingress contracts and structural admission | A handoff is not an executable program; host lifecycle success is not semantic output |
| RCV-28 through RCV-43 | Carrier shapes, derivation boundaries and decoder contract/implementation | Executing represented functions or state |
| RCV-44/45/46/47/48/49 | Positive/negative decoder conformance, structural derivation, recursive graph determinism, explicit deferred execution scope, representational equivalence | Behavioral three-way equivalence; RCV-49 forbids Execute/Dispatch/Evaluate/Interpret additions |
| RCV-50/51 | Transitive recovery/current predecessor acceptance and authority audits | Behavioral executor completion; nested PASS totals are not three-way evidence |
| p12_6_3_metadata_identity_association_test.py | Source/verified content/occurrence/plan association, immutable structures, stale/substitution rejection; real compiler actions unchanged and native rejection | Source-native executable equivalence |
| p12_6_4_source_native_mapping_test.py: MappingTests and NativeNeutralityTests.test_live_mapped_build_preserves_image_receipt_output_result | Producer mapping/order, missing spans explicit, byte-identical frozen C; mapped/unmapped native image/receipt/result neutrality; native outputs equal run_air_program final state | Managed-retained same-fixture comparison or machine-address/per-operation runtime trace |
| p12_6_6_trace_provenance_reference_test.py | Typed supplied evidence, deterministic scoped identities, rejection of stale/malformed evidence; live native result association separated from canonical result | Trace equality between paths or semantic execution by metadata |
| p12_6_8_controlled_trace_integration_test.py | Managed retained result equals direct RuntimeEngine result on compiled SOURCE, exactly-once execution/selection/policy checks, context/order/limit rejection and result preservation; native retained equals direct native evidence on a separate admitted legacy fixture | Same AIR across managed and native positives; compiled SOURCE is native-unsupported; no common three-way test |
| p12_1e_deterministic_canonical_result_cross_target_smoke_test.py (adjacent precedent) | Python result validation/fingerprint and static .NET contract checks | A .NET-produced executed program result |

Avoid duplicating the broad native rejection/failure matrix, metadata tamper suites or managed-neutrality tests. Reuse their fixtures and run them as predecessor gates. New coverage should join actual comparable owner results on one verified common-domain fixture.

## Minimal deterministic equivalence contract

1. Construct/reuse one authentic canonical legacy AIR fixture; verify with AIRVerifier. Capture its canonical transport, entry and owner/routing identity. Require existing native admission, never a test-defined replacement admission policy.
2. Use the same canonical initial state from program literals and the default canonical context/policy. Use exactly the same canonical entry; no custom managed initial state unsupported by native.
3. Execute canonical run_air_program, P12.6 execute_managed_retained (with the same verified AIR/plan), and real native execute_native or execute_native_retained. Canonical/managed share RuntimeEngine; document this fact in every claim.
4. Require managed ok, native SUCCESS, identical complete final named typed integer states with valid signed-I64 native representation. No dropped/extra/duplicate names, coerced bools, truncated integers or omitted untouched states. Confirm empty event/effect outputs for this domain. Native stdout is its binary state encoding, not user text.
5. Compare only already-produced values. A test adapter may sort exact state IDs and parse validated I64 decimal strings; it must not evaluate AIR, apply stores, resolve names/types, select paths or build predicted final state. The existing canonical runtime supplies the oracle.
6. Assert AIR transport/actions unchanged before/after; verify admission stores and generated regions preserve order/occurrences without precomputing results. Native never calls/falls back to RuntimeEngine or an interpreter. Structural preservation and final agreement are distinct evidence.
7. Repeat executions on the same verified input; compare behavioral observations and path-local fingerprints. Independently validate each receipt/context/mapping/result association. Do not require native receipt-bound result hash to equal managed result hash.
8. For excluded AIR and invalid routing, reuse explicit fail-closed gates and compiler/dispatch traps. Distinguish native admission rejection, infrastructure failure, canonical semantic error and retention error. Never relabel unsupported input as an equivalent successful run or manufacture a semantic FAILURE result from a process exception.

## Architectural gap classification

| Finding | Classification | Consequence |
| --- | --- | --- |
| Existing canonical runtime and admitted native subset expose complete final typed named state | NO_GAP | A test-only common-state comparison can use existing owners; no new evaluator/result schema needed |
| No joined canonical / P12.6 managed-retained / native same-fixture test | TEST_COVERAGE_GAP | Add focused joining coverage, not duplicate independent layer tests |
| Canonical runner and P12.6 managed path share RuntimeEngine | NO_GAP | Valid wrapper/path neutrality comparison; explicitly limited independence, not three separately implemented semantics |
| .NET target admits representations but has no program executor/result-producing consumer | SEMANTIC_GAP | Actual missing execution capability, not observed semantic divergence. Blocks claims of AIR/.NET/native behavioral equality. Do not solve by creating a second semantic implementation |
| Ordinary compiler actions, richer AIR and other targets outside native v1 | NATIVE_PROFILE_LIMIT | Preserve rejection and compiler actions; never normalize to legacy assignments to obtain a pass |
| Native supplies no intermediate per-operation runtime observations | OBSERVABILITY_GAP | Final behavior is comparable; intermediate execution chronology/trace parity is not. Static C stores/regions are not runtime proof |
| Different managed/native hash inputs and provenance scopes | PROVENANCE_ONLY_DIFFERENCE | Validate associations and compare typed outputs; no need to redesign canonical result hashes |
| No general CLI cross-target executor/selector; .NET ingress is structural | OBSERVABILITY_GAP | Use existing opt-in APIs in tests. Do not invent public unsupported-target parity or CLI dispatch |
| Optimization, performance, instrumentation or broader result/trace normalization for convenience | DEFER_TO_P12_8 | Outside this slice; classification is a deferral, not authorization or a claim about a specific P12.8 implementation |
| PDBs, machine addresses, debugger stepping and P13 runtime instrumentation | DEFER_TO_P13 | Explicitly excluded; no debugging expansion needed for final-state comparison |

No demonstrated semantic mismatch within native admission was found by inspection. This is not a freshly executed exhaustive equivalence proof. Lack of native trace detail and different receipt hashes do not justify an architecture change.

## Recommended minimal P12.7-2 scope and readiness

Test-only implementation may safely begin for the existing P12.6 managed path, with the explicit shared-RuntimeEngine limitation. Recommended P12.7-2 is a small common-domain test harness/contract using existing fixtures, verification/admission and owner APIs; no production changes, profile widening, compiler normalization, second evaluator, new trace schema or new transport.

Start with the existing two-state overwrite/untouched-state fixture joined across all three API surfaces; add only missing cross-path cases: reversed state declaration order, reordered multiple decision references, identical repeated stores, zero/negative/min/max I64 values, and an empty individual path with positive total stores. Existing maximum/Unicode acceptance can be reused rather than duplicated unless a joined comparison is needed. Verify same initial context, typed final-cell bijection, success, repeated deterministic outputs, preserved AIR and independent provenance validation. Negative coverage should reference/reuse existing actions/expression/routing/profile gates and explicitly confirm no fallback.

If the required managed target means .NET, implementation of a claimed three-way behavioral suite cannot safely begin as a passing suite using this freeze. Record unsupported/missing capability; require human review of a narrowly scoped execution contract before any separate capability work. This census neither broadens the roadmap slice nor authorizes that work. A fabricated .NET result, carrier admission, or forwarded Python result is not .NET execution evidence.

Explicit exclusions: whole-language equivalence; expressions/arithmetic/add_int and overflow semantics; bool/float/string states; functions/calls/generics; workflow/narrative/Quad-Vector execution; conditions/alternative causal paths; authority/requirements/roles; events/effects/invocations; nonempty ordered actions; multiple directives/principals; profile-limit violations; external/custom initial state; custom semantic owners; non-Windows-x64 execution; arbitrary or persisted foreign artifacts; public CLI target expansion; PDBs/machine-address debugging/runtime instrumentation/P13. Existing language capability in a different path does not bring these into native equivalence.

## Validation and repository impact

No production code, tests, existing evidence, grammar, compiler, AIR, runtime, CLI or tooling were edited. Exactly one new evidence artifact is created: docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md. No staging, commit, tag, release or push.

Read-only validation: HEAD/tag peeling, clean initial status, freeze tracked diff, empty index diff, repository/test inventories and live source inspection. Focused test attempted first: py -B apexforge/p12_5_native_profile_contract_test.py failed before test collection (exit 103, no default Python). python was unavailable (ENOENT); the Python39 interpreter recorded in frozen P12.6 evidence was also absent (ENOENT). At that initial attempt no test assertion ran and no pass was claimed. The supplied-interpreter continuation below supersedes the interpreter blocker; no full regression harness was run. Shell exec tooling itself initially failed process setup; repository inspection proceeded through the available Node process/filesystem tool. These environment/tool failures are not classified as language behavior failures.

Documentation-only regression impact: none expected on executable behavior; the focused profile gate passed in the continuation below, while broader execution/regression remains unverified in this session. Frozen P12.6-10 records predecessor/closure passes and a separate historical full-harness fixture blocker; those records do not replace fresh execution. Remaining work is human review of this contract/managed-target distinction, then separately authorized P12.7-2 tests and focused-before-regression validation with the now-verified repository-compatible interpreter and an available native toolchain.

Final expected git status --porcelain=v1 --untracked-files=all:

~~~text
?? docs/p12/P12_7_1_BEHAVIORAL_EQUIVALENCE_CAPABILITY_CENSUS.md
~~~

### Supplied-interpreter validation continuation

The user supplied the LYRA Python interpreter after the initial census. Identity verification returned Python 3.9.13, 64-bit, and the exact supplied executable. Initial sandbox access was denied; the normal escalated shell invocation then succeeded. No interpreter installation or environment configuration was changed.

Focused command: the supplied interpreter with -X utf8 -B apexforge/p12_5_native_profile_contract_test.py. Result: exit 0, 7 tests run, all PASS, 0 failures/errors. This verifies profile admission, ordering/boundaries, unsupported-surface rejection, routing/invalid AIR, exact types/containers, owner transport identity and no-evaluator dependency checks. It does not prove live native output, joined three-way equivalence or .NET program execution. No broad regression or native build/dispatch was run in this continuation.

Only this census document was updated. Final tracked/index diffs remain empty; the sole untracked file remains this document. P12.7-2 implementation remains unstarted.

## Files inspected

The following inventory records files actually read during this census, including focused excerpts and the full P12.5 test inventory. Linked dependencies described above were traced from their live callers; this list distinguishes files read directly.

- AGENTS.md
- apexforge/air/model.py
- apexforge/air/serialization.py
- apexforge/air/verify.py
- apexforge/apexforge_cli.py
- apexforge/causality/engine.py
- apexforge/incremental_cache/stability.py
- apexforge/language/compiler.py
- apexforge/language/project.py
- apexforge/native_backend/envelope.py
- apexforge/native_backend/execution_plan_binding.py
- apexforge/native_backend/lowering_input.py
- apexforge/native_backend/managed_handoff_projection.py
- apexforge/native_backend/model.py
- apexforge/native_backend/native_execution.py
- apexforge/native_backend/native_execution_contract.py
- apexforge/native_backend/payload.py
- apexforge/native_backend/result.py
- apexforge/native_backend/source_mapping.py
- apexforge/native_backend/target_neutral_lowering.py
- apexforge/native_backend/value.py
- apexforge/p12_0c_execution_target_architecture_contract_smoke_test.py
- apexforge/p12_1e_deterministic_canonical_result_cross_target_smoke_test.py
- apexforge/p12_5_execution_completion_census_test.py
- apexforge/p12_5_native_execution_acceptance_test.py
- apexforge/p12_5_native_profile_contract_test.py
- apexforge/p12_5_rcv_10_host_ingress_contract_decision_smoke_test.py
- apexforge/p12_5_rcv_11_target_neutral_managed_handoff_reconstruction_contract_smoke_test.py
- apexforge/p12_5_rcv_12_target_neutral_handoff_representation_census_smoke_test.py
- apexforge/p12_5_rcv_13_target_neutral_handoff_field_mapping_contract_smoke_test.py
- apexforge/p12_5_rcv_14_historical_managed_type_selection_confirmation_smoke_test.py
- apexforge/p12_5_rcv_15_target_neutral_handoff_implementation_foundation_smoke_test.py
- apexforge/p12_5_rcv_16_target_neutral_handoff_projection_bridge_census_smoke_test.py
- apexforge/p12_5_rcv_17_projection_bridge_ownership_contract_smoke_test.py
- apexforge/p12_5_rcv_18_projection_bridge_representation_decision_smoke_test.py
- apexforge/p12_5_rcv_19_projection_value_object_implementation_foundation_smoke_test.py
- apexforge/p12_5_rcv_20_projection_value_object_compatibility_census_smoke_test.py
- apexforge/p12_5_rcv_21_cross_runtime_transport_architecture_census_smoke_test.py
- apexforge/p12_5_rcv_22_cross_runtime_transport_contract_decision_smoke_test.py
- apexforge/p12_5_rcv_23_managed_host_ingress_implementation_census_smoke_test.py
- apexforge/p12_5_rcv_24_managed_host_ingress_implementation_contract_smoke_test.py
- apexforge/p12_5_rcv_25_managed_host_ingress_implementation_foundation_smoke_test.py
- apexforge/p12_5_rcv_26_managed_host_ingress_integration_census_smoke_test.py
- apexforge/p12_5_rcv_27_managed_host_program_integration_contract_smoke_test.py
- apexforge/p12_5_rcv_28_managed_executable_carrier_historical_census_smoke_test.py
- apexforge/p12_5_rcv_29_managed_executable_carrier_corrected_type_shape_contract_smoke_test.py
- apexforge/p12_5_rcv_2_recovered_lineage_provenance_smoke_test.py
- apexforge/p12_5_rcv_30_managed_executable_carrier_implementation_foundation_smoke_test.py
- apexforge/p12_5_rcv_31_managed_executable_carrier_derivation_boundary_census_smoke_test.py
- apexforge/p12_5_rcv_32_managed_executable_carrier_derivation_source_decision_smoke_test.py
- apexforge/p12_5_rcv_33_managed_executable_carrier_derivation_mapping_census_smoke_test.py
- apexforge/p12_5_rcv_34_managed_executable_carrier_derivation_mapping_contract_smoke_test.py
- apexforge/p12_5_rcv_35_managed_executable_carrier_decoder_architecture_census_smoke_test.py
- apexforge/p12_5_rcv_36_managed_executable_carrier_decoder_architecture_decision_smoke_test.py
- apexforge/p12_5_rcv_37_canonical_air_transport_json_shape_census_smoke_test.py
- apexforge/p12_5_rcv_38_managed_executable_carrier_json_parsing_policy_contract_smoke_test.py
- apexforge/p12_5_rcv_39_managed_executable_carrier_decoder_input_root_census_smoke_test.py
- apexforge/p12_5_rcv_40_managed_executable_carrier_decoder_input_root_decision_smoke_test.py
- apexforge/p12_5_rcv_41_managed_executable_carrier_decoder_public_api_contract_smoke_test.py
- apexforge/p12_5_rcv_42_managed_executable_carrier_structural_ambiguity_census_smoke_test.py
- apexforge/p12_5_rcv_43_managed_executable_carrier_decoder_implementation_smoke_test.py
- apexforge/p12_5_rcv_44_managed_executable_carrier_decoder_positive_conformance_smoke_test.py
- apexforge/p12_5_rcv_45_managed_executable_carrier_decoder_negative_conformance_smoke_test.py
- apexforge/p12_5_rcv_46_canonical_air_transport_to_managed_carrier_derivation_bridge_acceptance_smoke_test.py
- apexforge/p12_5_rcv_47_managed_carrier_derivation_determinism_recursive_graph_acceptance_smoke_test.py
- apexforge/p12_5_rcv_48_managed_carrier_integration_scope_decision.json
- apexforge/p12_5_rcv_48_managed_carrier_integration_scope_decision_smoke_test.py
- apexforge/p12_5_rcv_49_managed_carrier_representational_equivalence_acceptance_smoke_test.py
- apexforge/p12_5_rcv_50_recovery_closure_audit_smoke_test.py
- apexforge/p12_5_rcv_51_p12_5_recovery_terminal_closure_smoke_test.py
- apexforge/p12_5_rcv_53_native_dispatch_result_contract.md
- apexforge/p12_5_rcv_54_native_execution_acceptance.md
- apexforge/p12_5_rcv_5_runtime_host_topology_ownership_smoke_test.py
- apexforge/p12_5_rcv_6_managed_host_project_skeleton_smoke_test.py
- apexforge/p12_5_rcv_7_host_lifecycle_startup_contract_smoke_test.py
- apexforge/p12_5_rcv_8_host_lifecycle_startup_implementation_smoke_test.py
- apexforge/p12_5_rcv_9_host_ingress_architecture_census_smoke_test.py
- apexforge/p12_6_3_metadata_identity_association_test.py
- apexforge/p12_6_4_source_native_mapping_test.py
- apexforge/p12_6_6_trace_provenance_reference_test.py
- apexforge/p12_6_8_controlled_trace_integration_test.py
- apexforge/pipeline/execution_pipeline.py
- apexforge/runtime/diagnostics.py
- apexforge/runtime/engine.py
- apexforge/runtime/state.py
- apexforge/tooling/build_artifact.py
- apexforge/tooling/cli.py
- apexforge/tooling/debug_metadata.py
- apexforge/tooling/source_air_mapping.py
- apexforge/tooling/trace_integration.py
- apexforge/tooling/trace_retention.py
- apexforge/workflow/air_runner.py
- docs/p12/P12_6_10_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md
- runtimes/dotnet/ApexForge.Runtime.Host/Program.cs
- runtimes/dotnet/ApexForge.Runtime.Host/RuntimeHostIngress.cs
- runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionEnvelope.cs
- runtimes/dotnet/ApexForge.Runtime/CanonicalExecutionResult.cs
- runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrier.cs
- runtimes/dotnet/ApexForge.Runtime/ManagedExecutableCarrierDecoder.cs
- runtimes/dotnet/ApexForge.Runtime/ManagedRuntimeHost.cs
- runtimes/dotnet/ApexForge.Runtime/TargetNeutralLoweringHandoff.cs

## Explicit markers

~~~text
P12_7_BASELINE_P12_6_FREEZE_VERIFIED=True
P12_7_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_7_NATIVE_PROFILE_EXPANDED=False
P12_7_COMMON_EQUIVALENCE_DOMAIN_IDENTIFIED=True
P12_7_COMMON_EQUIVALENCE_DOMAIN=P12_6_PYTHON_MANAGED_PATH_AND_NATIVE_V1_LEGACY_I64_SET_INT
P12_7_DOTNET_THREE_WAY_EXECUTABLE_DOMAIN=NONE_DEMONSTRATED
P12_7_EXISTING_THREE_WAY_EQUIVALENCE_TESTS=NONE_FOUND
P12_7_EQUIVALENCE_GAPS_CLASSIFIED=True
P12_7_SECOND_SEMANTIC_IMPLEMENTATION_REQUIRED=False
P12_7_1_CAPABILITY_CENSUS_COMPLETE=True
P12_7_IMPLEMENTATION_STARTED=False
~~~

The required census-complete marker records delivery of this slice's evidence, not milestone completion, freeze, canonization or release.
