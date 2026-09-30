# P12.6-8 — Controlled automatic trace-retention integration

Review candidate only, controlled by P12.6-7. No later gate started.

## Additive files and APIs

New production file: apexforge/tooling/trace_integration.py. New acceptance file: apexforge/p12_6_8_controlled_trace_integration_test.py. This report is the only new documentation artifact. All predecessor files remain unchanged.

Frozen wrappers: CompilerMetadata, PlanMetadata, ManagedContextIdentity, StreamReference, ManagedRetention, NativePreDispatch, NativeFailureObservation, NativeRetention and RetentionLimits. ObservationError preserves an already-produced owner result when retention fails. Existing compiler/runtime/native APIs and opt-out behavior are unchanged. No global activation, trace registry or thread-local semantic context.

## Compiler and plan

compile_with_metadata accepts governed bytes and a project-relative logical name. It calls the existing compiler-with-ledger producer once, verifies through AIRVerifier, consumes SourceMap/P12.6 mapping, and uses the existing TAM SourceMap adapter. Exact producer ledger entries justify TAM operation references. No token replay or fabrication of other TAM families. Unsupported compiler forms reject; absent physical correspondence remains explicitly unmapped under the existing contract. No arbitrary source-file discovery/read.

associate_plan creates external PlanMetadata binding exact verified AIR, actual entry/routing, source sidecar and available mapping. Without compiler evidence it uses an AIR-bound empty sidecar and claims no source correspondence. Mutable plan-owner substitutions reject on validation. RegistryExecutionPlan remains routing authority, not metadata owner.

## Managed context and retention

Supported provenance contract: exact RuntimeEngine, exact CausalEngine, DEFAULT_STANDARD_LIBRARY, exact ExecutionContext/StateSnapshot and exact AuthorityEngine with immutable supplied grants. Identity includes AIR/plan/metadata references, actual initial scalar state, actual grants, entry and maximum invocation depth. Default-owner version labels are governed compatibility contracts, not code authentication hashes. Object comparison checks the accepted library owner; object identity is not fingerprinted. Unsupported custom owner/policy/library provenance rejects before execution.

execute_managed_retained performs exactly one normal runtime.execute. It consumes already-returned runtime, causal, authority and diagnostic records without replay, independent selection or policy calls. Runtime ExecutionResult remains unchanged. Its external tooling fingerprint covers evaluated delta, final state and semantic diagnostic fields; no native canonical-result conversion. Display text is outside deterministic identity.

Family-local ordinals and parent indices preserve actual returned runtime/causal/authority interleaving. Diagnostics retain producer ordering. state.delta stays execution scoped; repeated identical assignments have distinct producer ordinals and operation claims reject. Unsupported schemas are explicit index/kind coverage gaps. Complete mode raises ObservationError carrying the unchanged owner result. Opt-in partial mode preserves the raw result and explicit gaps, never fabricated completeness. No global chronology across TAM/runtime/narrative/native.

## Native lifetime

NativePreDispatch validates AIR/routing/source sidecar/mapping/profile/generated C/receipt/image before actual dispatch. Existing admission/build/mapping/dispatch owners perform canonical work. One normal dispatch is followed by image/mapping revalidation while the artifact exists. NativeRetention holds mapping, existing NativeExecutionEvidence and external NativeResultAssociation binding pre-dispatch identity, output and canonical result. Native errors retain existing code/message and an external pre-dispatch observation; no new failure-event schema.

execute_native_retained owns the temporary directory. Post-dispatch association completes before cleanup; files are gone before the caller receives the result. validate_snapshot checks retained evidence without artifact-file reads. No artifact paths or extended file lifetime are retained. Region membership does not claim execution. Generated C remains byte-identical. No per-operation native trace, address map, instrumentation, PDB or debug flags.

## Immutability, limits and security

Build metadata is shared by reference; per-execution evidence belongs to returned wrappers. Source bytes, mapping/trace collections, parent indices and unsupported-coverage pairs are immutable. Caller-owned positive limits bound source bytes, SourceMap/TAM retention, returned runtime records/diagnostics and native mapping regions. Failures are visible, not silently truncated, and preserve already-produced results. Limits do not bound allocation inside the existing runtime before it returns; P12.8 memory/performance closure remains deferred.

Canonical material excludes time/duration, PID/thread ID, host/user/machine identity, environment dumps, temporary/absolute paths and random UUIDs/tickets. Owner diagnostic display text stays outside fingerprints; this is not a general text-redaction feature. Hash integrity does not authenticate hostile in-process monkeypatching. Exact producer/family allowlists and owner validation reject supported-boundary forgery and substitutions. Existing native issuance/cleanup protections remain authoritative.

Standalone narrative attachment remains deferred: narrative may have no AIR while ProvenanceScope requires AIR. No fabricated AIR or scope change. Broader compiler/linker correspondence, custom-context contracts, unsupported schemas, operation-occurrence instrumentation, native failure schemas, global chronology, PDB/debugger/address work remain outside scope.

## Executed evidence

Interpreter for every Python command:
C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe
Version: Python 3.9.13. Suites used -X utf8 -B.

| Final suite | Result |
|---|---|
| p12_6_8_controlled_trace_integration_test.py | 12/12 PASS |
| p12_6_6_trace_provenance_reference_test.py | 12/12 PASS |
| p12_6_4_source_native_mapping_test.py | 11/11 PASS |
| p12_6_3_metadata_identity_association_test.py | 8/8 PASS |
| p12_5_native_profile_contract_test.py | 7/7 PASS |
| unittest discover -s apexforge -p p12_5_native_execution_acceptance_test.py -v | 20/20 PASS (includes 7 imported profile cases) |
| source_diagnostics_smoke_test.py | PASS: seven reported categories |
| otherwise_runtime_smoke_test.py | PASS: true/otherwise cases |
| authority_consolidation_smoke_test.py | PASS: five reported categories |
| causal_model_consolidation_smoke_test.py | PASS: four reported categories |

Final unittest total: 70 executed cases including duplicated imported profile coverage, plus four passing smoke commands. P12.6-6 also invokes existing TAM source/token/authority behavioral functions and three narrative trace/diagnostic/termination behavioral functions. No full historical milestone/freeze regression stack.

Failure classification before correction:
- Initial integration 11 PASS/1 ERROR: TEST_FIXTURE_DEFECT. NativeExecutionError exposes code and exception text, not a detail attribute. Corrected the assertion to existing exception text.
- Added nested-immutability negative 0/1 FAIL: IMPLEMENTATION_DEFECT. Unsupported-coverage tuple accepted a nested mutable list. Added only nested tuple/index/kind validation; retained assertion passes in final full suite.
No unresolved final failures, weakened assertions or predecessor changes.

Negatives cover stale source/sidecar/AIR/plan/routing/mapping, mutable plan-owner substitution, context/policy/config substitution, unsupported custom runtime/causal/policy/library, forged TAM producer, changed runtime payload, duplicate trace identity, state.delta operation claims, parent-order/result substitution, native image/receipt/output/result/post-dispatch substitution, host paths, mutable nested coverage and retention limits. Preflight spies prove stale evidence rejects before dispatch. Post-image mutation fails retention while preserving actual owner evidence.

Repeated equivalent inputs produce identical compiler/plan/context/trace/collection/native pre/post fingerprints. Enabled-versus-disabled comparisons preserve compiled AIR, verification, routing/entry, causal/policy decisions, managed state/result/trace/diagnostics, native result/output/generated C/image/receipt. Fixture call counts equal normal execution: runtime, causal selection and authority each once. Compiler CausalPath.actions remain unchanged/nonempty and native admission rejects them before build.

Static AST audit forbids semantic resolution/evaluation/selection/policy/reconstruction calls and requires one managed execute call. Runtime traps prove revalidation does not execute runtime, causal selection or policy. AIR/result schemas, compiler semantics, producers, profile and PDB behavior are unchanged. All predecessor uncommitted files were SHA-256 checked unchanged. git diff --check passes; nothing staged.

## Checkpoint and next gate recommendation

HEAD = afp-p12.5-execution-freeze^{commit} = 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

Unchanged tag object / commit:
- afp-p12.4-freeze: 7c475986ed3ed1d58cc30148603fbfe8b09529ee / 13f7646f1052746f54f906076d66d29117ee2718
- afp-p12.5-freeze: 9e2d7a4f57a10e0499d788f8584ace477f624b07 / 542be090e193b3d931d27c08e16de3efd961a01e
- afp-p12.5-execution-freeze: 6ad3d33601a576c2b42e2fde16cd98c2c61980fd / 6e71a1afae36c3b4984e949c707d3e6fae6cc269

Recommend P12.6-9 — Integrated Metadata/Trace Coverage and Closure Review: review bounded coverage, resource limits/lifecycle, public opt-in contracts and accepted unsupported boundaries; decide which gaps block P12.6 closure and which remain explicitly deferred. Start as review only. No implicit authorization for schemas, narrative AIR-free scope, instrumentation, profile expansion, PDB/debugger work or P12.7. No staging, commit, tag or push.

P12_6_COMPILER_METADATA_ATTACHMENT=PASS
P12_6_PLAN_METADATA_ASSOCIATION=PASS
P12_6_MANAGED_CONTEXT_IDENTITY=PASS
P12_6_MANAGED_TRACE_RETENTION=PASS
P12_6_NATIVE_PRE_DISPATCH_RETENTION=PASS
P12_6_NATIVE_POST_DISPATCH_RETENTION=PASS
P12_6_TRACE_INTEGRATION_DETERMINISM=PASS
P12_6_INTEGRATION_PROVENANCE=PASS
P12_6_STALE_INTEGRATION_FAILS_CLOSED=True
P12_6_EXECUTION_SEMANTICS_UNCHANGED=True
P12_6_STATE_DELTA_OPERATION_INFERENCE=False
P12_6_NATIVE_PER_OPERATION_TRACE_CLAIM=False
P12_6_GLOBAL_CHRONOLOGY_CLAIM=False
P12_6_CANONICAL_RESULT_REMAINS_TRACE_FREE=True
P12_6_MANAGED_RESULT_TYPE_UNCHANGED=True
P12_6_NARRATIVE_STANDALONE_ATTACHMENT_DEFERRED=True
P12_6_RUNTIME_INSTRUMENTATION_ADDED=False
P12_6_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_6_NATIVE_PROFILE_EXPANDED=False
P12_6_PDB_ENABLED=False
P12_6_8_READY_FOR_REVIEW=True
