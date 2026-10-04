# P13.3 — Semantic State, Context & Authority Inspection Foundation

## Review result and baseline

Read-only inspection foundation implemented and validated for the supplied canonical carriers below. This is a review candidate, not an owner release/freeze/canonization decision. No breakpoint, stepping, native step correlation, DAP, IDE debugger, replay, TDP UI or P13.4 work is begun.

Branch: `p13-1-debugger-architecture`. Incoming HEAD and peeled `afp-p12.8-freeze` both equal `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`. Incoming Git status contained exactly four untracked P13 candidates, nothing staged, and no tracked changes against P12.8. All four incoming SHA-256 values were captured before new-file implementation and verified unchanged after focused tests and regressions:

| Preserved incoming file | SHA-256 |
| --- | --- |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `apexforge/tooling/debug_session.py` | `22C530D30A9E0D87276DA1CBB39D38ADA8C34B78A00F3DD1216F1BEF3AEBE774` |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |

Exactly three P13.3 files are added: `apexforge/tooling/debug_inspection.py`, `apexforge/p13_3_semantic_state_authority_inspection_test.py`, and this document. No change to debug_session.py was necessary. No P12 module, existing export surface, compiler, grammar, AIR, runtime, backend or client file changed. AGENTS.md's historical P11.4A stage text is superseded for active scope by the owner's explicit P13.3 instruction; its preservation/engineering rules remain applicable.

## Inspected and reused semantic carriers

Repository-relative paths below are under `apexforge/`.

| Existing carrier / evidence | Reuse and boundary |
| --- | --- |
| `runtime/state.py`: StateCell, StateSnapshot | Consume already-produced immutable primitive values and canonical keys. Never call apply/from_program_initials or use declaration initializers to fill missing values. |
| `air/model.py`, `type_system/model.py` | Preserve StateDefinition declared ApexType identity, directive/principal/check/causal references and canonical program scope. No new state/type system or effective-permission calculation. |
| `authority/model.py`, `authority/engine.py` | Read Principal, roles and AuthorityCheck declarations; consume recorded allowed/denied decisions. Inspector never imports or calls AuthorityEngine. P13.2 separately retains canonical debugger-authorization evaluation. |
| `workflow/air_runner.py`, `native_backend/execution_plan_binding.py` | Inspect plan/routing conventions; consume already-created PlanMetadata association/entry/owner fingerprints. No registry lookup, route choice or plan construction in inspector. |
| `runtime/engine.py`: ExecutionResult | Inspect result carrier shape, owner ok classification, final state and diagnostic references via ManagedRetention. No direct import or invocation of RuntimeEngine. |
| `native_backend/result.py`, `payload.py`, `value.py` | Preserve CanonicalExecutionResult status and typed named output representation via NativeRetention. Existing value validation/fingerprint functions are pure representation checks, not execution or decoding. |
| `tooling/trace_integration.py`, `trace_retention.py` | Consume PlanMetadata, ManagedRetention, NativeRetention, RetainedRecord, existing result fingerprints, provenance scopes, trace family/collection references and native pre/post associations. No retained execution wrapper is called by inspector. |
| `tooling/debug_metadata.py`, `source_air_mapping.py`, `native_backend/source_mapping.py` | Reuse source identities, AIR metadata/operation IDs, StateLocator, producer evidence and generated C spans. No inferred source links, C re-emission, native admission or machine-address mapping. |
| `native_backend/lowering_input.py` | Reuse pure existing AIR serialization/fingerprint seam to reject stale/substituted program content. This wraps existing canonical transport; it does not verify/evaluate language semantics or route execution. |
| `runtime/call_stack.py` and runtime invocation traces | Genuine canonical pure-function CallFrame/CallStack and internal directive invocation stack exist. Retained ExecutionResult/ManagedRetention/NativeRetention do not expose captured activation stacks. Trace depth is not a complete stack. |
| P13.2 `tooling/debug_session.py` | Reuse exact ExecutionReference, SessionReference and immutable DebugSession for target/session validation; no control API change. |

P12 producers and embedding owners remain responsible for canonical validation, evidence authenticity, authorization and custody. Inspection adds explicit cross-carrier consistency checks; it is not a replacement verifier, provenance authority or authentication service. Legacy retained evidence has no P13 execution-local ID; the embedding owner must bind that occurrence correctly. Matching content alone cannot prove which repeated equal-input execution produced it.

## Inspection model and availability

`InspectionSnapshot` is frozen and contains an execution reference, StateView and explicit InspectionFields for directive, principal, authority, plan, result, provenance, correlation, diagnostics and stack. It does not retain input PlanMetadata, StateSnapshot, runtime policy, retained carrier, live handle or callback. Values are copied into exact immutable scalar/tuple projections.

`InspectionField` distinguishes `available`, `unavailable`, `unsupported`, `not_applicable`, and `redacted`. Available data has an immutable primitive/tuple payload; all missing statuses have no payload and a nonempty reason. Missing nested records preserve that status/reason; null is not an unlabeled semantic value. An available empty tuple means supplied empty evidence, not missing evidence. Lists, dictionaries, arbitrary objects/callbacks and nonfinite floats cannot enter projection payloads.

Optional inputs are None only at the constructor boundary; output fields always state their availability. Known declared states remain visible with unavailable values if no snapshot is supplied. No zero, default initializer, empty policy, active directive or successful result is fabricated.

## State and before/after observations

`inspect_state` consumes StateSnapshot or CanonicalExecutionPayload alongside canonical program declarations and ExecutionReference. Each StateEntry preserves exact key, structural declared ApexType name/arguments where supplied, observed type/representation and value, mapping reference and availability. Entries are sorted lexically by exact key, with no case folding or namespace aliases. Extra observed keys remain visible with explicitly unavailable declarations.

Runtime primitive observations preserve exact Python storage type tags (`int`, `bool`, `str`, `float`); declarations retain canonical ApexType identities such as `string`. Native payloads preserve `I64`/`BOOL`/`UTF8` data exactly rather than decoding/converting them into an independent runtime state system. Boolean and integer observations remain distinct; a declaration/value mismatch is not normalized. Unsupported opaque/nonfinite values are explicitly unsupported. AIR initializers are never evaluated or copied as missing observations.

`state_difference` compares supplied StateView values structurally for the same exact execution. Fully available visible snapshots yield a sorted changed-key tuple; incomplete, unsupported or redacted values produce unavailable difference evidence. It never applies StateDelta/StateAssignment or reconstructs intermediate state. Its cause field is explicitly unavailable: `STATE_DIFFERENCE != CAUSAL_EXPLANATION`. No causal edge, source operation or transition reason is inferred from a changed key.

## Directive, principal and observed authority

Directive context comes only from an explicitly supplied retained `directive.start` record contained in the retained evidence's collections. Identity/name/principal are checked against program declarations. The view preserves scoped directive ID, name, principal ID, entry identity comparison, causal-decision/check references and retained record identity. Its capture label is `retained_entry_observation_not_live_activation`: an entry record is not proof that a directive is currently active. Without such evidence, directive context remains unavailable; the plan's entry directive remains separately known.

The principal view preserves canonical principal ID and sorted explicit role references. It does not infer effective authorities, expand arbitrary principal implementation attachments or merge program principal identity with the debugger inspector's principal. `inspect_principal` also deliberately projects a separately supplied canonical Principal.

`inspect_authority` projects existing authority-family evidence: retained record identity, AIR scope, check ID, principal, requested capability, resource and original boolean allowed result. A matching declared AuthorityCheck is structurally associated; role/requirement-derived runtime checks without a declaration have an explicitly unavailable declared-check reference. Declared checks never manufacture a decision. Existing check facts are validated against the declaration when present, and existing retained producer schema checks are reused. No policy decision is rerun.

```text
PRINCIPAL != ROLE
ROLE != CAPABILITY
CAPABILITY != AUTHORITY
OBSERVED_AUTHORITY != DEBUGGER_AUTHORIZATION
```

A test binds observed program authority to an observer-only session with a different principal and demonstrates no added control grants or fake-control-owner calls. P13.2 authority evaluation at session creation/activation is outside inspection and is trapped during inspection tests.

## Plan, routing, result and diagnostic inspection

Plan view preserves existing PlanMetadata fingerprint, MetadataAssociation fingerprint, routing fingerprint, entry directive, owner-program fingerprints and supplied profile label. Pure canonical AIR fingerprint checks reject mislabeled program content; association comparisons reject wrong AIR/routing/entry bindings. No registry resolution, target selection, admission or routing execution occurs. Native retained scope additionally supplies and validates native profile. A managed profile label is an embedding contract label, not a new independently proven .NET execution target.

Managed result view preserves `runtime.ExecutionResult`, the owner's `ok` boolean, existing result fingerprint and retention association. Native result view preserves `CanonicalExecutionResult`, its unchanged SUCCESS/FAILURE status, result/profile/post association. State comes from the owner's final_state or typed output payload. Conflicting separately supplied final state is rejected. Managed result fingerprints are checked through the existing pure fingerprint function; native result/scope/collection/receipt/image/output/mapping links are compared structurally. No native output decoder or semantic comparator is implemented.

Native mapping sidecar association and plan sidecar association may legitimately differ while AIR/routing identity agrees. The inspector uses the mapping's actual association for native retained scope and the plan association for managed retained scope, preserving P12 carrier ownership rather than forcing artificial identity equality.

Managed diagnostics project supplied severity/code/node references, including owner RUN001 denial evidence; display text is not copied into client view identity. Native result's absent diagnostic collection is unsupported, not an invented empty diagnostic list. Exceptions are not converted into semantic SUCCESS/FAILURE or fabricated canonical results. Inspector shape/binding errors have stable debugger-domain codes without interpolating sensitive values.

## Source/AIR/generated-native and trace/provenance references

`inspect_mapping` consumes exact SourceAIRMapping or NativeSourceMapping. It projects mapping fingerprint, existing operation ID/AIR locator, producer-linked source identity/span, generated source identity/region where available, and explicit unsupported machine address. State entries associate only existing StateLocator operations; declaration/assignment names are not used to fabricate operation links. Mapping AIR/routing/profile/entry and retained mapping fingerprint relationships are checked where applicable.

Source-backed compiler metadata remains bounded to original supported producer evidence. Hand-built admitted AIR retains `UNMAPPED_SOURCE`; generated C correlation may be available independently. Known C regions do not establish machine execution or CPU addresses. No mapping re-emission, breakpoint resolution or native stepping is performed. Missing mapping is unavailable, and machine-address mapping remains unsupported.

Provenance projections retain scope/retention fingerprints and trace family/collection fingerprints, plus declared unsupported coverage. Native projections additionally retain receipt, image, mapping and result-association fingerprints. Entire trace bodies, source text, generated C text, artifact paths and runtime objects are not copied. Deliberate constructors (`inspect_mapping`, `inspect_authority`, `inspect_principal`, `inspect_frame`) allow bounded expansion of supplied evidence. No arbitrary retained-trace browser, attribution engine, TAM graph reconstruction or P13.5 view implementation is added.

## Semantic frame and stack availability

The runtime has real immutable pure-function CallFrame/CallStack carriers and internal directive invocation tuples. Pure-function entry traces report function/name/depth/argument count; they do not capture full frames/locals, and retained outputs do not carry a stack snapshot. The implementation therefore records `P13_SEMANTIC_STACK_AVAILABLE=False` for an execution inspection's captured stack.

`inspect_frame` defines a bounded semantic frame projection from an explicitly supplied genuine CallFrame: kind, owning AIR reference, canonical function ID/name and depth. Capture scope is unavailable unless the producer supplies it elsewhere; arbitrary Any-typed local binding values are deliberately unsupported and not retained. This is not a reconstructed activation stack or independently validated live frame capture. The test uses the existing canonical frame constructor, not Python/.NET/native host frames. Richer owner-backed stack capture remains an inspection gap, not a claim that ApexForge lacks semantic nesting.

## Redaction and deterministic representation

Redaction is an explicit selected-key projection option, not a permission/policy engine and not automatic for ordinary values. `redacted` fields contain no original value or value digest. The full snapshot conservatively withholds value-dependent result/provenance/trace/diagnostic projections when selected keys are redacted. Redacted state comparisons cannot disclose a changed-key result. The execution binding is omitted from public repr, and its value-dependent provenance fingerprint is excluded from a redacted snapshot's stable view form. Original sensitive values are not retained in projected objects or error text.

Tests compare different dummy private values under identical public canonical input references and verify identical redacted state forms, absent values in repr/serialization/error text, withheld result/scope fingerprints and stable client-view fingerprint under volatile timestamp changes. This is value-projection redaction, not a guarantee that all canonical input identity, state names, source-map identities or program metadata are secret. Those public input references remain intact for correlation and require embedding authorization. Reference-hiding policy, broad metadata redaction and remote authentication remain future boundaries. Raw upstream evidence stays under its original owner's custody; the inspector does not rewrite it.

Stable projection forms are schema-separated UTF-8 JSON preimages under `apexforge.debug-inspection/v1`; fingerprint is uppercase SHA-256. State/role ordering and reference forms are deterministic. Existing owner fingerprints retain their own schemas and authority. Equivalent supplied semantic observations produce equal forms; no universal cross-target value normalization is claimed. Optional observation timestamp is excluded from equality, repr, canonical form and fingerprint. PID/handles/addresses/timings/UI/transport state are absent.

Stable view forms omit execution-local ID/session transport identity. `SessionInspection.binding_form` deliberately includes session/local execution reference to bind delivery to the right occurrence; it is a separate local association, not semantic identity or a redacted public value serialization. View identity never replaces AIR, canonical results or provenance identity.

## Session binding, passivity and custody

`bind_inspection` requires a matching P13.2 DebugSession target, ACTIVE lifecycle and granted OBSERVE surface. It returns a frozen SessionInspection with exact session/execution/snapshot association. `validate_session` rejects a different session, target or closing/closed snapshot. InspectionSnapshot requires StateView's exact execution binding, so replacing only its target with another execution fails; bound snapshots likewise cannot silently retarget.

These are trusted in-process structural checks. The inspector does not re-evaluate session authorization or grant control. The caller must present the current owner session snapshot; old immutable snapshots do not implement revocation or a live session handle. Legacy retained evidence's execution-local labeling remains the embedding owner's responsibility. References and projection fingerprints are not bearer tokens or cryptographic producer attestations.

Managed/native passivity tests execute through existing owners first, retain evidence, capture result/metadata/provenance fingerprints, then install traps for runtime execution, assignment/expression evaluation, authority evaluation, state application, causal selection, routing/plan construction, native dispatch and generated-source emission. Projection succeeds under these traps, and all original supplied objects/fingerprints remain unchanged afterward. Real native artifact scopes are cleaned before inspection; the inspector consumes retained references without reading or extending live artifact custody.

Returned snapshots are caller-owned immutable observations with explicit execution/evidence binding and inspection purpose. No files, transport sessions, execution hooks or growing caches are allocated by the inspector. Long-lived retention/transfer remains the embedding owner's resource-continuity responsibility; no universal memory ceiling or automatic canonical evidence deletion is claimed. MSC remains analytical and has no new runtime dependency.

## Focused validation, corrections and regressions

CPython 3.11.9; commands run from repository root with `-X utf8 -B`. Focused tests passed before predecessor regressions. No existing assertion, expected output, P12 carrier or incoming P13 file was edited to obtain a pass.

First focused invocation ran 21 methods and reported 16 errors (3.270 seconds). Classified before correction as `IMPLEMENTATION_DEFECT` in the new inspector: its immutable payload validator rejected explicit nested missing-field records, and native retention validation assumed plan and generated-mapping sidecar associations were identical. The validator now admits only exact missing-status/null/reason records; native validation preserves the actual mapping-owned association. The same 21 methods passed afterward (2.927 seconds). Final representation/passivity hardening hid execution binding hashes from repr and added assignment/expression traps without weakening assertions; final focused run passed 21/21 in 2.858 seconds.

| Current final validation | Result |
| --- | --- |
| `python -X utf8 -B apexforge/p13_3_semantic_state_authority_inspection_test.py` | 21 methods PASS; 2.858 seconds. |
| `python -X utf8 -B apexforge/p13_2_debug_session_control_foundation_test.py` | 21 methods PASS; 0.024 seconds. |
| `python -X utf8 -B apexforge/authority_consolidation_smoke_test.py` | Script PASS, canonical grants and transactional denial preserved. |
| `python -X utf8 -B apexforge/p12_6_3_metadata_identity_association_test.py` | 8 methods PASS; 0.043 seconds. |
| `python -X utf8 -B apexforge/p12_6_4_source_native_mapping_test.py` | 11 methods PASS; 13.069 seconds. |
| `python -X utf8 -B apexforge/p12_6_6_trace_provenance_reference_test.py` | 12 methods PASS; 2.682 seconds. |
| `python -X utf8 -B apexforge/p12_6_8_controlled_trace_integration_test.py` | 12 methods PASS; 20.125 seconds. |
| `python -X utf8 -B apexforge/p12_8_5_security_resource_lifetime_test.py` | 3 methods PASS; 12.375 seconds; three real lifecycle missing-image/ticket-release/retained-validity markers. |

Final selection: 88 unittest methods plus one authority smoke script PASS. Retried earlier focused invocations are not added to the distinct final count. Relevant native predecessor suites ran in separate processes with independently owned temporary scopes; all exited zero. No full P12 closure or historical full-harness PASS is claimed.

Focused coverage consolidates the requested properties: exact deterministic typed state, immutable projections, explicit missing/redacted/unsupported evidence, structural difference without causal attribution, directive/principal/role/check identities, observed authority distinct from session authorization, no authority/routing/execution evaluation, plan/result/source/native/provenance references, session/cross-execution rejection, native machine address unavailable, owner-result passivity and static absence of mutation APIs. Static inspection forbids direct imports of RuntimeEngine/AuthorityEngine/AIR runner/native dispatcher and calls to execution/mutation/permission/routing/emission owners. Existing tooling carrier imports may transitively load execution definitions; neither import nor constructor invokes execution. Pure existing serialization and fingerprinting are intentional read-only dependencies.

A search initially named nonexistent `runtime/function_execution.py`; classified `TEST_INVOCATION_DEFECT` in inspection discovery, corrected to the actual `runtime/call_stack.py`. It was not a test failure or a missing semantic carrier. Repository shell commands used the previously approved outside-sandbox runner after earlier session setup failures; no new environmental constraint prevented validation. All identified test defects are corrected; no unresolved test failure remains.

## Remaining gaps and exclusions

| Gap | Classification / disposition |
| --- | --- |
| Captured live directive/function/workflow stack and intermediate state absent from retained carriers | `INSPECTION_MODEL_GAP`, `SEMANTIC_STATE_GAP`; expose unavailable, require future explicit owner capture. No runtime instrumentation added. |
| Retained entry context does not prove currently active directive | `AUTHORITY_OBSERVATION_GAP`, `INSPECTION_MODEL_GAP`; capture-point label explicit, no activation API. |
| Wider linked/transformed/multi-directive source correspondence and machine addresses | `SOURCE_MAPPING_GAP`, `DEFER_TO_P13_4`; preserve P12 mapping limits, no stepping implementation. |
| Universal exact runtime-operation association, causal attribution and rich TAM/provenance browsing | `TRACE_PROVENANCE_GAP`, `DEFER_TO_P13_5`; supplied references only, evidence before attribution. |
| Legacy evidence lacks local execution occurrence ID; immutable session snapshot is not live revocation | `SESSION_BINDING_GAP`; trusted embedding binding/current session required, remote authentication `DEFER_TO_P13_7_PLUS`. |
| Broad policy-driven metadata/reference redaction and remote sensitive-data controls | `REDACTION_GAP`, `DEFER_TO_P13_7_PLUS`; selected observed-value representation is tested, no policy engine. |
| Persistent retained inspection custody, transfer and resource budgets | `RESOURCE_LIFECYCLE_GAP`; caller ownership, no live artifact retention or automatic deletion. |
| Full external protocol codec, clients and integrations | `DEBUGGER_CONTRACT_GAP`, `DEFER_TO_P13_7_PLUS`; immutable local projections only. |

No mutation methods (`set_state`, `mutate_state`, `change_principal`, `grant_authority`, `activate_directive`, `change_route`, `overwrite_result`) exist. No second semantics, authority/routing evaluator, native profile expansion, pause/resume, breakpoints, stepping, native step correlation, DAP, VS Code/Visual Studio debugger, replay, TDP UI, P13.4 or later roadmap work is included.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_ROLE=OBSERVATIONAL_CLIENT
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_DEBUG_SESSION_EXECUTES_AIR=False
P13_CONTROL_REQUEST_RUNTIME_MUTATION=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_STATE_INSPECTOR_EXECUTES_SEMANTICS=False
P13_INSPECTION_AUTHORITY_ENGINE=False
P13_INSPECTION_ROUTING_ENGINE=False
P13_INSPECTION_MUTATION_API=False
P13_BREAKPOINTS_IMPLEMENTED=False
P13_STEPPING_IMPLEMENTED=False
P13_DAP_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
P13_SEMANTIC_STATE_INSPECTION=PASS
P13_DIRECTIVE_CONTEXT_INSPECTION=PASS
P13_AUTHORITY_CONTEXT_INSPECTION=PASS
P13_EXECUTION_PLAN_INSPECTION=PASS
P13_RESULT_INSPECTION=PASS
P13_SOURCE_AIR_CORRELATION_INSPECTION=PASS
P13_TRACE_PROVENANCE_REFERENCE_INSPECTION=PASS
P13_SESSION_INSPECTION_BINDING=PASS
P13_INSPECTION_SEMANTICALLY_PASSIVE=True
P13_SEMANTIC_STACK_AVAILABLE=False
P13_3_READY_FOR_REVIEW=True
```

PASS and True values refer to tested supplied-evidence projections and passivity, not live debugger capabilities, universal mapping, remote authorization or an owner milestone freeze.

## Exact final Git status and preservation

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/p13_3_semantic_state_authority_inspection_test.py
?? apexforge/tooling/debug_inspection.py
?? apexforge/tooling/debug_session.py
?? docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md
?? docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md
?? docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md
```

Seven P13 candidates, nothing staged. HEAD remains `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`, all four incoming hashes remain unchanged, tracked P12.8 tree/index diffs are empty, and generated artifact inventory is empty. No commit, tag or push. Stop after P13.3.
