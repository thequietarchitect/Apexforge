# P12.6-6 — Deterministic Trace/Provenance Reference Foundation

Ready for human review; no milestone freeze/release declaration. P12.6-5 controls this gate. This gate adds only tooling/trace_retention.py, p12_6_6_trace_provenance_reference_test.py and this report. Predecessor code/documents are preserved. No automatic pipeline retention or runtime instrumentation is installed.

## Immutable models and ownership

TraceFamily distinguishes TAM, core runtime, runtime diagnostic, causal selection, authority observation, narrative runtime and native evidence. Seven frozen typed evidence wrappers reference the existing owner-produced TraceRecord, TraceStep, Diagnostic, NarrativeExecutionTraceEvent or NativeExecutionEvidence contracts. RetainedRecord contains a typed evidence union, immutable ProvenanceScope, producer-stream ordinal and optional OperationAssociation. TraceCollection retains an exact tuple for one family/scope. NativeResultAssociation externally links a collection to a mapped artifact and actual native evidence/result. CanonicalExecutionResult is unchanged.

Nested canonical values are checked defensively: exact tuples, typed frozen records/facts/source positions, immutable string fields, exact booleans/integers where producer schemas require them, and finite primitive scalar facts. Mutable containers and opaque repr-based identities reject. Display messages are required to be immutable strings but deliberately excluded from canonical identity. Native output values must be an exact tuple of canonical frozen values. Caller mutation of accepted normal model inputs cannot change fingerprints.

TAM adapters and producer behavior remain unchanged. RuntimeEngine/CausalEngine/authority policy/narrative execution retain semantic ownership. The authority family references an already-produced runtime authority.check observation; the allowed boolean remains the supplied policy's decision, not a decision by the reference layer. No policy authenticity or complete policy/context fingerprint is fabricated.

## Identity and ordering

Schema is apexforge.trace-retention/v1. Record identity hashes schema, distinct family, allowlisted versioned producer signature, scope fingerprint, supplied producer-stream ordinal, stable typed payload, original TAM identity where applicable, and explicit operation association when validated. Collection fingerprints bind family/scope and the ordered record IDs. Equal evidence/order/scope constructs equal fingerprints; changed semantic payload changes identity. Display text changes do not. No public persistence format is added.

Every family collection preserves supplied owner order, including TAM's existing order. Ordinals must be contiguous zero-based indices into that supplied per-family sequence. Identical repeated runtime events are legal and distinct by ordinal. Original duplicate TAM IDs reject. There is no global sorting or inferred cross-family chronology. Any caller grouping/filtering must preserve original producer order and supply that grouping as its input contract; the foundation does not claim to reconstruct a full execution chronology from separated streams. The only set-like field is explicitly declared unresolved TAM edge IDs, stored as a sorted unique immutable tuple. Missing linked records require that declaration; no records or graph closure are inferred. Complete existing SourceMap TAM maps need no declarations.

Canonical identity excludes timestamps, durations, process/thread IDs, hostnames/usernames/machine identifiers, memory addresses, host/temporary/compiler paths, UUIDs, issuance tickets and environment dumps. The module introduces no telemetry producer or telemetry model. Existing display text is retained outside fingerprints; tests vary elapsed/PID/path display text without changing diagnostic identity. Unknown telemetry fact keys cannot masquerade as canonical runtime facts. Host-path contamination in canonical identity strings rejects rather than being normalized away.

## Provenance and operation references

ProvenanceScope binds an explicit governed input fingerprint and exact AIR fingerprint, with optional sidecar/source-map/plan-association/routing/native-map/profile/generated-C references according to stage. for_source delegates to existing SourceAIRMapping validation, optional MetadataAssociation, exact source bytes and verified AIR. for_native delegates to existing NativeSourceMapping validation. The reference layer never copies or reconstructs correspondence tables. Raw value construction alone is not proof of association: validation must consume expected authoritative scope and supplied owner evidence.

OperationAssociation is restricted to exact existing compiler TAM source-map-entry evidence. It checks original TAM entry identity, span and AIR ID against the explicitly supplied SourceMap index; exact membership of the existing OperationReference; and an existing sidecar evidence link. It does not match literals/names/state values or issue new operation IDs. Source-backed TAM spans validate against governed source snapshots and the referenced mapping. Missing snapshots/maps reject.

Runtime state.delta remains execution/input-scope evidence with no operation association: existing path/state/operator/value facts do not establish assignment occurrence. Repeated assignments remain legal; no heuristic operation lookup is performed. Core runtime, causal, authority, narrative and native evidence cannot claim operation-level association in this foundation. A false narrow claim rejects, not silently downgrades.

TAM signatures are allowlisted from existing source/token/declaration/ownership/resolution/type/authority/narrative adapters. Core runtime support is deliberately bounded to runtime start/finish, directive start/finish/skip, state.delta, event.emit, effect.intent and when.evaluate. Causal evaluate/select, supplied authority.check, diagnostic and narrative_transition records are separately typed. Unsupported runtime kinds, producers, payload types or schema versions fail closed. This is retention coverage, not a native-profile expansion.

## Native artifact/result association

NativeResultAssociation consumes an existing MappedNativeArtifact and trusted supplied NativeExecutionEvidence. It delegates artifact/mapping/image validation to P12.6-4; compares exact native scope and receipt; checks the result input fingerprint against the receipt digest; and binds collection/map/receipt/image/output/result fingerprints. validate compares against the expected actual producer evidence, rejecting substituted result/output/receipt/image/scope identities. For native-family collections the supplied record must match that evidence exactly in canonical fields.

Native dispatch is not invoked by retention. Backend-issued dispatch/ticket checks remain the existing native owner's responsibility. Supplied evidence is a trusted local producer boundary, not a signed authenticity protocol. NativeExecutionEvidence exposes an output fingerprint, not raw bytes; retention preserves that actual captured-output identity and does not reconstruct output bytes or independently re-run execution.

The foundation permits native evidence and applicable TAM collections at this artifact/result boundary. It rejects attaching interpreter/causal/authority/narrative runtime collections as native execution history without an established producer-scope contract. Static generated-C operation order remains lowering evidence; no region is asserted to have executed. CanonicalExecutionResult remains exactly input_fingerprint/status/outputs, and its canonical form/fingerprint is unchanged by external association. No trace field is added to results, receipts or AIR.

## Fail-closed tests and no-second-semantics audit

Tests cover stale source/AIR/native map, incorrect routing/profile, absent or wrong operations, insufficient runtime operation evidence, wrong source/span, image/receipt/output/result substitution, unavailable producer/collection, unknown schema/family/signature, duplicate original TAM identity, undeclared external TAM links, invalid ordinals/order, mutable nested values, malformed exact types and canonical machine paths. No mismatches are repaired or silently discarded.

Static call audit forbids resolver/type/evaluator/causal selector/authority/semantic execution/native dispatch/compiler/TAM fabrication calls. Runtime traps prove collection construction and validation do not invoke RuntimeEngine.execute, CausalEngine.select_path, AuthorityEngine.allows or recompilation. Mapping-owner validation is reused. No generated-C parsing, state-value decision reconstruction, semantic action reordering, source inference or runtime event production exists in the new layer.

## Executed validation and failure classifications

Exact interpreter for every Python command: C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe; version confirmed Python 3.9.13. Tests use -B. The runtime smoke rerun additionally uses -X utf8.

| Suite | Final evidence |
| --- | --- |
| P12.6-6 trace reference tests | 12/12 PASS |
| P12.6-4 mapping tests | 11/11 PASS |
| P12.6-3 identity tests | 8/8 PASS |
| P12.5 native profile contract | 7/7 PASS |
| P12.5 native acceptance discovery | 20/20 PASS, including seven imported profile tests |
| otherwise_runtime_smoke_test.py | PASS in UTF-8 mode |

The focused suite also runs 17 unmodified historical TAM behavioral assertion functions: SourceMap four, token five, authority eight; and three existing narrative transition/diagnostic/termination behavioral tests. These are targeted behavioral portions, not claims that obsolete milestone branch/whole-repository freeze assertions pass on a later roadmap slice. Live runtime/causal/authority/narrative producer evidence is consumed in additional focused tests.

Initial focused run: seven passing tests, one failure and one error; both TEST_FIXTURE_DEFECT (nonexistent narrative test module, and reversing identical records cannot change evidence). Fixtures corrected without weakening order rejection: distinct real-produced assignments now test order changes, while identical repeated events remain legal. A new focused exact-type negative exposed one IMPLEMENTATION_DEFECT: a string authority outcome was accepted instead of exact bool. Minimal correction added exact fact/provenance types and defensive immutable display-string checks; final suite passes. No predecessor/architecture change was needed.

The runtime smoke initially exited during emoji printing under CP1252, after successful assertions: ENVIRONMENTAL_BLOCKER. Same interpreter with -X utf8 passes; producer code was unchanged. No unresolved failures. No expensive full historical harness was run.

Repeated source records, native evidence, collection/record identities and associations are deterministic. Live native dispatch before/after retention has unchanged result canonical form; repeated native dispatch evidence/association matches. P12.6-4 again proves unchanged C, image/receipt/output/result equivalence and preserved CausalPath.actions with unchanged bounded rejection. The P12.5 acceptance suite confirms existing admission/execution behavior.

## Limits and exact next-gate recommendation

Automatic retention is not wired into compiler/project/runtime/native pipeline APIs. Full interpreter context/policy identity, unimplemented runtime event schemas, general operation locators, cross-family chronology, narrative-to-AIR/native correspondence, per-operation runtime identity and native instruction/address evidence remain absent or unsupported. Producer authenticity is not inferred from a hash. Source coverage and nonempty compiler CausalPath.actions admission limitations remain exactly as P12.6-4 established.

Recommend P12.6-7 — Controlled Trace-Retention Integration Scope and Coverage Review. Review the smallest opt-in tooling orchestration seam for supplying existing collections and exposing external result associations; establish authoritative input/context/grouping contracts and missing/unavailable behavior before pipeline integration. Keep instrumentation, new events, inference, AIR/result/profile/PDB changes and P12.7/P13 outside that gate unless separately authorized. P12.6-7 has not begun.

HEAD remains 6e71a1afae36c3b4984e949c707d3e6fae6cc269, exactly afp-p12.5-execution-freeze commit. P12.4, P12.5 and P12.5 execution tag objects/commits match P12.6-5. Predecessor artifacts remain unchanged. git diff --check passes. Nothing staged, committed, tagged or pushed.

P12_6_TRACE_MODEL=PASS
P12_6_TRACE_IDENTITY=PASS
P12_6_TRACE_PROVENANCE_ASSOCIATION=PASS
P12_6_TRACE_DETERMINISM=PASS
P12_6_TRACE_FAMILIES_REMAIN_DISTINCT=True
P12_6_CANONICAL_RESULT_REMAINS_TRACE_FREE=True
P12_6_STATE_DELTA_OPERATION_INFERENCE=False
P12_6_NATIVE_PER_OPERATION_TRACE_CLAIM=False
P12_6_STALE_TRACE_PROVENANCE_FAILS_CLOSED=True
P12_6_TRACE_RETENTION_SEMANTICALLY_OBSERVATIONAL=True
P12_6_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_6_RUNTIME_INSTRUMENTATION_ADDED=False
P12_6_NATIVE_PROFILE_EXPANDED=False
P12_6_PDB_ENABLED=False
P12_6_6_READY_FOR_REVIEW=True
