# P12.6-5 — Mapping Provenance and Trace-Retention Contract Review

Review outcome: PASS for this bounded contract; no retention implementation. P12.6-4 remains the accepted predecessor. Canonical AIR remains semantic authority; RegistryExecutionPlan remains routing authority. Compiler/tooling owns mapping sidecars; existing semantic owners produce decisions. Neither tracing nor native metadata becomes a semantic owner.

## Live producer census

The adapter implementation is tam/production.py; the producer/owner labels below identify the original evidence subsystem, not a claim that adapters are automatically invoked there. The repository call-site search still finds definitions/re-exports, not automatic attachment to compiler/project/native results. tam/integration.py composes already-produced maps without rewriting records. Existing adapters must be retained and referenced, not duplicated.

| Evidence | Actual adapter / record | Original producer and semantic owner | Retention role |
| --- | --- | --- | --- |
| Source and transformation | trace_map_from_source_map; source-span, source-map-entry | language.source / language.compiler | Compile collection; span/source evidence and exact existing entry reference |
| Token | trace_map_from_token_evidence; token | language.lexer | Source collection, lexer order; not an executed event |
| Declaration | trace_record_from_declared_identity | language.identities | Analysis collection; declared/current AIR identity |
| Ownership | trace_record_from_declaration_owner | language.declarations | Analysis collection; source/module declaration ownership, distinct from plan routing |
| Resolution | trace_map_from_resolution_observation; query, context, candidate, resolved/unresolved/ambiguous outcome | language.resolution_queries, resolution_context, resolution_candidates | Analysis collection; observe supplied outcome only; never invoke resolution |
| Type | trace_map_from_type_evidence | type_system.model, constraints, generics, inference, substitution, specialization | Existing type/signature/substitution/specialization evidence only; no new inference |
| Authority | trace_map_from_authority_evidence; principal, check, grant | authority.model | Passive policy-input evidence, NOT an allow/deny decision |
| Narrative | trace_map_from_narrative_evidence | language.narrative_model, narrative_graph, narrative_validation | Story/graph/validation evidence; not AIR/native execution |
| Core diagnostics | runtime.diagnostics.Diagnostic, appended by RuntimeEngine | runtime.engine and delegated error owners | Separate diagnostics collection: severity/code/node ID; messages are display data |
| Core execution | runtime.diagnostics.Trace/TraceStep in runtime.engine.ExecutionResult | RuntimeEngine | Already-produced ordered runtime observations, separate from TAM |
| Causal selection | CausalSelection.trace_steps: causal.evaluate, causal.select | causality.engine.CausalEngine | Actual selected-path observation; engine alone evaluates/selects |
| Authority outcome | authority.check runtime step | RuntimeEngine records result of supplied ExecutionContext authority policy; default authority.engine.AuthorityEngine | Existing allowed/check/principal/capability/resource facts; retain actual policy-owner context if available, never invent it |
| Narrative execution | NarrativeExecutionTraceEvent and NarrativeExecutionDiagnostic | runtime.narrative_observability delegates to runtime.narrative_transition | Separate narrative-runtime collection; explicit transition success/failure and choice/path evidence |
| Native execution | NativeExecutionEvidence(result, receipt_json, output_fingerprint) | native_backend.native_execution dispatch/decode | Receipt/output/result observation only; no per-operation runtime events |

RuntimeEngine produces runtime.start/finish; directive.start/finish/skip and invocation start/finish/abort/cycle/depth; authority.check; expression.error; state.delta; event.emit; effect.intent; when.evaluate; function call/local/return/conditional and stdlib call observations. CausalEngine adds causal.evaluate/select. State assignments are evaluated/applied by RuntimeEngine, authority outcomes come from its supplied policy, and causal selection comes from CausalEngine. Tracing must not repeat any of those behaviors. The same kind/message/Fact model is not a TAM TraceRecord and has no source span or operation locator.

Narrative observability emits narrative_transition with source scene, caller-selected choice/path index, outcome and optional destination/failure kind. terminate_narrative returns explicit termination state, not a termination trace event. NarrativeExecutionResult separately retains choice evidence, state, diagnostics and trace. SemanticDecision model identities/provenance are passive model data; their existence is not evidence of a native decision event. tools/trace_export.py is a display exporter, not a canonical trace identity contract. TAP's audit_trace_map recognizes exact transformation/authority signatures; retain its diagnostic-only projection and existing runtime/narrative adapters. Compiler TAM does not replace Concordat TAM-v3.

## Retained categories and exclusions

Retain source, token, transformation, declaration, ownership, resolution, type, authority and narrative TAM records in their original compiler/tooling collections when actually supplied. Their domains/representations and original IDs remain unchanged. Retain already-produced core runtime events and diagnostics in separate execution-scoped collections. Narrative runtime remains its own kind. Native execution may reference applicable supplied compile collections, but this only records provenance, not that a token, declaration, authority check or narrative choice executed.

For the native profile, source/transformation and explicitly mapped state/assignment evidence can explain admitted operations; declarations/ownership/types are contextual analysis evidence. Resolution candidates/failures, generic/function evidence, policy declarations, narrative graphs/transitions and conditional/invocation events are unsuitable as native execution events. They may remain compile-side evidence; they confer no admission. Exclude fabricated events, inferred source links, selected paths reconstructed from C, per-store native execution claims, machine-address maps, unproduced TAM, unsupported schemas/types and incomplete evidence presented as complete. Do not manufacture authority approval from an empty native authority surface.

## Identity, ordered collections and provenance contract

Proposed namespace: apexforge.trace-retention/v1. It describes external immutable references and validation, not a merged trace payload format. Keep distinct typed collection kinds TAM, CORE_RUNTIME, CORE_DIAGNOSTIC, NARRATIVE_RUNTIME and NATIVE_DISPATCH_OBSERVATION. Payloads remain existing owner records. Producer identity is the versioned, allowlisted adapter/owner signature, not a Python object ID or dynamically imported producer name.

Each collection has schema/kind/producer contract identity, an exact governed input-scope reference, ordered record identities and deterministic payload fingerprint. Preserve the owner's actual tuple order. Do not sort runtime events or derive semantic order from an unordered set; unordered/unproven production order is unsupported. For composed TAM maps retain explicit ordered component boundaries and compose_trace_maps behavior. Duplicate existing TAM identities reject as they do today; do not reissue them to conceal collisions.

A retained record reference identity is SHA-256 of a canonical typed tuple: retention schema, collection kind, producer contract, input-scope fingerprint, existing TAM ID when applicable, producer ordinal, stable typed payload digest and optional explicitly supplied mapping association. Runtime ordinals are zero-based indices into the actual owner-produced tuple, not counters inferred from matching values. Repeated identical runtime kinds/facts remain distinct by ordinal. Equivalent inputs/evidence/order yield identical IDs; an edit invalidates identities through content/AIR bindings. This is content identity, not edit-stable identity. Identical repeated runs can share an identity; physical run uniqueness is telemetry, not a random deterministic ID.

Avoid collection/record hash cycles: record IDs use input scope and payload, never their containing collection's final fingerprint. A later result association binds completed collections by fingerprint without rewriting their IDs. Source-only evidence can exist before AIR; later scope associations add AIR/plan/artifact/result references externally. No fake absent hashes or future execution fields are required at compilation.

TAM stable payload includes original schema/domain/producer/owner/representation/trace ID, optional canonical identity and span, explicit provenance and ordered upstream/downstream IDs. Canonical retention admits only portable governed strings/source names; original TAM IDs alone are insufficient because adapters do not hash source content. A host-path-contaminated record cannot enter the deterministic collection unchanged: reject it, do not normalize its ID or silently drop fields. Existing external graph IDs need an explicit external collection reference or an unresolved-reference declaration; this does not require changing TraceMap's deliberately permissive edge contract or inferring graph closure.

For runtime/diagnostic payloads use a versioned kind-specific whitelist of existing stable facts, typed exact scalars and canonical AIR identity fields. Preserve fact tuple order and reject unknown/unsupported value types rather than serializing repr, addresses, arbitrary exceptions or non-finite numbers. Free-text messages and exception text stay optional display diagnostics outside canonical identity. Severity/code/node ID and approved structured decision facts are canonical. A purported semantic fact cannot be moved to telemetry to evade mismatch checks. P12.6-6 must implement only its explicitly tested subset of producer signatures; all other signatures fail unsupported until reviewed.

## Minimal staged provenance envelope

Use a common schema/kind/producer-contract/collection fingerprint plus typed lifecycle references. Store common bindings once per collection; records only add ordinal/original ID and optional explicit correspondence. The following fields are justified at these stages:

| Stage | Required bindings | Optional only when established |
| --- | --- | --- |
| Source/TAM production | governed SourceIdentity/content hash for source-backed records; owner-produced evidence collection | Existing source span or SourceMap entry index; source-less analysis input collection digest |
| Source/AIR mapping | SourceAIRMapping and MetadataSidecar fingerprints, exact AIR fingerprint | Existing AIRMetadataIdentity/OperationReference; no locator invented for other records |
| Routing | MetadataAssociation fingerprint validated against exact plan | Entry directive and owner fingerprints already carried by association; no copy of routing logic |
| Generated C | NativeSourceMapping fingerprint with validated profile and generated-C fingerprint | Operation ID and region reference from that mapping |
| Artifact | Existing MappedNativeArtifact association, receipt fingerprint and receipt image hash | Original source correspondence may be explicitly UNMAPPED_SOURCE |
| Result | NativeExecutionEvidence receipt, output digest and CanonicalExecutionResult fingerprint | References to supplied compile/runtime collections with kind/execution scope |

References resolve to exact existing sidecars/envelopes, not copied correspondence tables. AIR/routing/profile/generated-C/image fields can be checked through referenced bindings rather than redundantly owned by every record. If carried redundantly for diagnostics they must equal the owner values. The collection is not cryptographic proof of producer authenticity: trusted supplied producer outputs and existing backend-issued dispatch/ticket validation remain prerequisites. Do not treat arbitrary hash-shaped data as an issued execution result. Result scope must include all owner-established execution inputs/context available; missing runtime-context identity is an explicit unsupported cross-run association, not a reason to hash a machine environment or replay execution.

## Decision association limits

Selected directive: plan entry is routing intent; directive.start is actual interpreter entry. Distinguish them. Selected causal path: preserve actual CausalEngine facts, but no new path chooser. Directive/check/path canonical IDs may be retained as owner-produced semantic references with the exact AIR scope; they are not new supported P12.6 operation locator kinds.

State assignment: state.delta has path/state/operator/value but lacks directive/decision/assignment occurrence. Repeated assignments and nested calls can be ambiguous. Do not zip these steps to sidecar operations or infer identity by value/state/path. Preserve execution-scope event ordinal; operation reference is unavailable unless the producer supplies exact established locator/operation identity. Condition steps lack sufficient structural location too. Native state initialization regions are static lowering evidence, not runtime initializer events.

Execution ordering: runtime tuple order is observed; native mapping region order is admitted lowering order. They must have distinct evidence labels. Authority TAM inputs are not authority decisions; runtime allowed facts record decisions already made, but complete policy fingerprinting is not currently provided. Termination: runtime.finish and actual result identity can be retained, without claiming completion on exceptions/aborts; narrative termination stays owner state/evidence. No records are fabricated to fill absent events.

## Native boundary and storage ownership

Without C instrumentation the bounded executable emits only ordered I64 result bytes. Retain pre-dispatch validated mapping/plan/artifact references and static admitted operation order; label these admission/lowering evidence. At successful post-run dispatch, bind the actual NativeExecutionEvidence receipt/output/result to that mapping/artifact envelope. This does not prove per-operation execution, selected-path history or intermediate state. Process failures/timeouts have NativeExecutionError code/detail, not a successful NativeExecutionEvidence; do not create a CanonicalExecutionResult or fabricated finish event for them. Failure diagnostics remain separate owner observations.

Compiler/tooling owns TAM collections and source/AIR association sidecars. Runtime owners retain their own execution event/diagnostic collections. An external execution-provenance envelope references validated mapping/artifact and result-associated observations. RegistryExecutionPlan owns none of these payloads. CanonicalExecutionResult remains input_fingerprint/status/outputs unchanged; its input fingerprint remains the receipt fingerprint. Do not absorb tracing into canonical result/output hashes. Generated C, native profile, AIR schema, receipt and dispatcher remain unchanged in this review.

## Deterministic fields versus optional telemetry

Deterministic: schema/kind/producer contract, governed logical source/content identity, validated spans, original producer identities/facts, owner-fixed ordinal, exact AIR/locator/operation and mapping references, association/routing/profile/generated-C hashes, receipt/image/output/result hashes. These follow lifecycle availability.

Excluded from canonical trace/collection/provenance fingerprints: wall-clock timestamps, durations, PID/thread ID, memory addresses, temporary directories, absolute host/source/compiler installation paths, machine identity, environment variables/dumps, random UUIDs and process-local issuance ticket identity. Timestamps/durations/PID/thread ID may be optional opt-in telemetry linked externally to deterministic evidence. Host/build/compiler paths and machine labels are local diagnostic-only, excluded from portable exports by default. Environment dumps are not retained; explicitly allowlisted nonsensitive diagnostic values may be local telemetry only. No current trace producer supplies a standard telemetry contract; none is invented here. Display messages may be retained separately; diagnostics cannot become canonical by accidentally including host-specific exception text.

## Fail-closed validation rules

Reject malformed/unknown schema/version/kind/producer signature, unsupported canonical payload types and unavailable claimed producer evidence. An absent optional producer must be declared unavailable before association; it cannot appear as a valid empty execution trace. An empty owner-produced tuple is distinct and may be valid.

Reject stale AIR/source/source-map/mapping/generated-C fingerprints, wrong or absent requested operation IDs, locator mismatch, wrong plan routing/entry/owner association, wrong profile/image/receipt/output/result association. Validate references through existing P12.6-3/4 owners; do not reimplement mapping inference. Reject duplicate retained identities, negative/noninteger/out-of-bounds ordinals and reordered expected producer records. Reject source spans inconsistent with governed content. Unsupported missing operation correspondence may be represented as explicitly UNMAPPED before validation; a claimed operation association that cannot be proven rejects. Never silently discard mismatched records, auto-repair hashes or switch to another artifact. Diagnostics should name the offending boundary and expected/observed identity without exposing host secrets.

## No-second-semantics review and next gate

The permitted retention dependency graph consumes already-produced typed records, validates hashes/indices/references with existing identity owners, and preserves order. It never calls resolution, type inference, evaluators, causal selection, authority policies or runtime execution to manufacture evidence. It never parses C to recover decisions or guesses source correspondence. Repeated-assignment mapping, missing context/policy identity, nested locators and absent native per-operation events are classified coverage/producer gaps; they are not solved here. Existing TAM adapters, CausalEngine, authority policy, runtime/narrative owners and native dispatch remain their respective authorities. This is a static architectural audit of the proposed contract, not an executable test of unimplemented retention code.

P12.6-6 recommendation: Deterministic Trace/Provenance Reference Models and Association Validation Foundation. Implement frozen, separate typed references/collections for existing TAM and a bounded explicitly allowlisted runtime/diagnostic subset; an external mapping/artifact/result association model; minimal canonical fingerprint preimages; positive determinism and all fail-closed negatives. Consume supplied records only, preserve existing payload contracts, require explicit missing/unmapped states. Start native coverage with validated pre-dispatch/static-map and actual post-run receipt/output/result associations. Test no semantic-engine calls and unchanged canonical execution/results. Do not add instrumentation, new runtime event producers, missing locator reconstruction, generic unified trace payloads, persistence protocols, AIR/profile changes, PDBs, P12.7 or P13. Runtime per-operation instrumentation needs a separate later authorized gate. P12.6-6 has not begun.

## Inspection and repository evidence

Inspected P12.6-1 census plus live tam/model.py, tam/production.py, tam/integration.py; runtime/diagnostics.py, engine.py, narrative_execution.py, narrative_observability.py; causality/engine.py; authority/engine.py; semantic_decision/model.py; workflow/air_runner.py; tools/trace_export.py; tap_check/projection.py; tooling/debug_metadata.py, source_air_mapping.py; native_backend/execution_plan_binding.py, source_mapping.py, native_execution.py and result.py. Repository call-site searches covered non-test Python trace producers. Existing predecessor executable results are accepted evidence, not rerun claims. No Python tests or full regression stack were needed for this documentation-only review. Two read-search invocations failed (regex escaping and absent directory); corrected read searches succeeded; no code or contract correction resulted.

HEAD remains 6e71a1afae36c3b4984e949c707d3e6fae6cc269 = afp-p12.5-execution-freeze commit. Freeze object/commit pairs remain:

- P12.4: 7c475986ed3ed1d58cc30148603fbfe8b09529ee / 13f7646f1052746f54f906076d66d29117ee2718.
- P12.5: 9e2d7a4f57a10e0499d788f8584ace477f624b07 / 542be090e193b3d931d27c08e16de3efd961a01e.
- P12.5 execution: 6ad3d33601a576c2b42e2fde16cd98c2c61980fd / 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

Only this review document was added in P12.6-5. Predecessor code/docs remain unchanged. No staging, commit, tag or push.

P12_6_TRACE_RETENTION_CONTRACT_REVIEW=PASS
P12_6_TRACE_RETENTION_IMPLEMENTATION_STARTED=False
