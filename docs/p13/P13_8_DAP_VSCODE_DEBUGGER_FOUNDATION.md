# P13.8 — DAP Adapter & VS Code Debugger Foundation

Review candidate for the bounded adapter foundation. Repository owner/human review retains final authority; this document does not declare a freeze or release. VS Code registration is explicitly deferred under the permitted adapter-only option.

## Baseline and incoming custody

Branch: `p13-1-debugger-architecture`.

HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.

Before implementation: exactly 19 untracked incoming P13 candidates, empty tracked/staged diffs, empty build directory, no generated residue. SHA-256 baseline:

| Incoming candidate | SHA-256 |
| --- | --- |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/p13_6_deterministic_replay_trace_comparison_test.py` | `5770090A9040527ABA26EADF5FF46457B8FE8211389244AF5066F6CBFE9BCF9B` |
| `apexforge/p13_7_cli_debugger_test.py` | `BB8C014C44288A05450477D33BEA57AC236EF06987BE758AC6D9BBBDF56154A8` |
| `apexforge/tooling/debug_cli.py` | `84B2091E8A7FC294FEF24F786834D3E0BA806EEB7B03C438EDE64E1ABB168101` |
| `apexforge/tooling/debug_correlation.py` | `981E6FEC0A2B4CEA1F044D565805506EC75D0C1E6150313076867254EFB9339B` |
| `apexforge/tooling/debug_evidence.py` | `ED2A67EF80B8765EDB810137C86EB3E569B7EA022EADC9878ABEF9E9B478FC72` |
| `apexforge/tooling/debug_inspection.py` | `409099E910F5D5313DF5EA4949DBB6A1BAFFB6CA037554A22D373651B152D466` |
| `apexforge/tooling/debug_replay.py` | `44E06F35955279E0C5A7D0048050AB74D2D36512C3E88C834687C98DEDEFF8C5` |
| `apexforge/tooling/debug_session.py` | `22C530D30A9E0D87276DA1CBB39D38ADA8C34B78A00F3DD1216F1BEF3AEBE774` |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |
| `docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md` | `F7B62CD5C668E7B5D14FD02BD3003CBC91652B1F714D27CE880A13C75CDFACE4` |
| `docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md` | `8975BE6FBD6E3DDA654A98FBC9C11FAE5A996D47F91C63AA58064114C48DBF3F` |
| `docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md` | `8F849F358D85B1B6FDD5E9433BE0C13EA57FF822BF8D794FDCA246612A01F163` |
| `docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md` | `1C8235AF503E484D04EBF106104B18BA54FB4AB5704C58FFD992FF1BB652E3B1` |
| `docs/p13/P13_7_CLI_DEBUGGER.md` | `24795ACDA46D654224543924C1E602D81C3E37460CB6C4AA0CF72B9E023FDCDA` |

Exactly **three new files**, making **22 P13 candidates**: `apexforge/tooling/debug_dap.py`, `apexforge/p13_8_dap_vscode_debugger_test.py`, and this document. All 19 incoming hashes are preserved.

## Existing VS Code architecture and frozen boundary

Inspected `editors/vscode-apexforge/package.json`, `extension.js`, `runtime/lsp-client.js` architecture through its registration/import boundary, the README/packaging inventory, prior P10-T3 packaging/foundation test conventions, and the P13.2–P13.7 model/client APIs. The frozen language extension is `gravitas-studios.apexforge-language`, uses CommonJS JavaScript, recognizes .apex through language/grammar contributions, activates language-server behavior on language/workspace events, and registers language-server commands. It has no debugger contribution or authorized retained-P13-target provider. Its configurable Python/server-path LSP wiring is not adopted as debugger launch authority.

**FROZEN_VSCODE_BOUNDARY:** registration in that extension would reopen frozen P10 files. A separate P13 extension would still need safe retained-input provisioning across the Python/extension boundary. No persisted authorized descriptor loader or external live transport currently supplies that seam. Adding a manifest that launches an unprovisioned adapter would not demonstrate a working retained debugger.

Decision: permitted **adapter-only implementation**, with VS Code registration deferred. No new extension/package, arbitrary configurable executable, socket, daemon, IPC, VSIX installation, or frozen extension edit is made. P13.8 is not claimed as a working VS Code debugger UI. No unrelated P10 smoke/packaging suite is rerun because there is no new/changed extension payload or registration to validate; tracked-byte preservation verifies coexistence. Older P12 tests are likewise not rerun because no shared/frozen module changes.

## Architecture, identity and provisioning

Canonical ApexForge execution/evidence -> P13 debugger substrate -> P13.7 DebuggerCLI -> DAPAdapter -> supplied binary streams.

DAPAdapter requires an already-provisioned exact DebuggerCLI object. Canonical execution, authorization, retention, mapping and evidence production remain upstream. No request loads an artifact or executes a program to obtain a target.

One serial adapter instance owns an opaque DAP session ID, lifecycle, connection-local message sequence and projection handles. The embedding owner allocates distinguishable IDs when multiple instances coexist. The default ID is a local fixture label, not a globally canonical identity. DAP session, P13 debug session, execution, principal, transport stream and process are separate. Projection thread ID 1, optional frame ID 1, source IDs starting at 100 and variable handles 10–15 are local presentation references, not semantic identities or authority tokens. Sequence/handle values enter no canonical semantic fingerprint.

The adapter captures immutable client input anchors and rejects rebinding of history, inspection, correlation, position, ordering, comparison, mode or owner. Mutable P13 replay cursor position is deliberately observational. Live access also revalidates the current P13 active session, OBSERVE grant and supplied inspection/evidence/correlation bindings. Retained authorized input can outlive closure of its original debug session.

## Transport

The framing strategy follows the official [DAP base protocol overview](https://microsoft.github.io/debug-adapter-protocol/overview.html): ASCII Content-Length header, CRLF separator and UTF-8 JSON body. Response/event field shapes, source references and read-only variable hints were checked against Microsoft's [protocol schema](https://raw.githubusercontent.com/microsoft/debug-adapter-protocol/main/debugAdapterProtocol.json).

FramingParser incrementally accepts fragmented frames and bounded concatenated messages. It supports the required single Content-Length header, rejects malformed/duplicate/extra headers, invalid lengths, malformed UTF-8/JSON, duplicate JSON keys, non-object messages, nonfinite constants and incomplete EOF. JSON recursion failure becomes a deterministic protocol error. Header limit is 4096 bytes; payload limit is 1 MiB; cumulative buffered feed is bounded by their sum. This intentionally bounded subset does not promise arbitrary batched stream sizes or optional header extensions.

A framing failure clears the parser buffer and makes that parser terminal. Invalid request envelopes cannot be assigned invented request identity and raise a deterministic transport/owner error. Valid request envelopes with unsupported operations receive DAP error responses. Request sequences must be positive signed-32-bit-range integers and increase monotonically; bool is not an integer identity. Responses/events use their own increasing adapter sequence.

frame serializes stable sorted-key JSON and measures encoded byte length. serve consumes supplied binary streams using bounded read1 where available, handles clean/partial EOF, emits framed responses/events and flushes output. It has no process launcher, target loader or logging. EOF, transport failure and disconnect invalidate only local adapter state/handles. Embedding owns the supplied streams and retained model lifetime.

## Lifecycle and modes

Lifecycle: new -> initialized -> bound -> ready -> closed.

initialize responds before the initialized event. Launch/attach binds the already supplied target; configurationDone marks the projection inspectable and emits an adapter-local stopped event. Queries before ready, repeated initialization/configuration, target changes, stale sequence and queries after closure reject deterministically.

Retained launch requires `mode: retained` and supplied retained history, inspection or correlation. Its response explicitly says projectionOnly=true, executesProgram=false and externalTargetLoading=false. It never treats launch as permission to execute arbitrary source.

Attach requires `mode: supplied-session` and an already-authorized in-process P13.2 live owner. PID, process enumeration, injection and arbitrary program/module/executable/path fields are rejected. This is not external live transport.

Stopped reason is entry, with description identifying supplied/offline inspection and stating runtime pause was not observed. Namespaced fields identify OFFLINE_INSPECTION_POSITION and runtimePauseObserved=false. No breakpoint-hit, continued, exit-code or runtime pause event is manufactured.

Disconnect terminates the DAP projection only. terminateDebuggee/suspendDebuggee/restart=true are unsupported; omitted or false options may close the projection. The terminated event means the adapter session ended, not execution termination. The ApexForge debug session, runtime and retained evidence are unchanged.

## Capabilities and standard request behavior

initialize advertises configurationDone, read-only hover lookup only when inspection exists, loaded-source queries only when supplied mapped sources exist and are visible, and an ApexForge-owned custom request list. Mutation, restart, termination, reverse step, memory read/write, instruction/function/conditional/hit-conditional breakpoints and log-point capabilities are false; exception filters are empty. Source breakpoint verification/execution and live pause/continue/step are not advertised as implemented. The custom capability object explicitly says runtimeControl=false, breakpointExecution=false and readOnly=true. Standard DAP has no universal live-control-disable flag; unsupported standard requests therefore return errors.

| Request | Bounded behavior |
| --- | --- |
| initialize | Truthful capabilities, then initialized event. |
| launch | Bind supplied retained projection; no program execution or external loading. |
| attach | Bind supplied authorized in-process session only. |
| configurationDone | Make observation projection ready; offline-position stopped event. |
| threads | One explicitly named debugger inspection projection, not OS/semantic thread. |
| stackTrace | Genuine supplied P13.3 frame projection, or empty stack with explicit unavailable/redacted metadata. |
| scopes | Only for a genuine frame; otherwise semantic_frame_unavailable. |
| variables | Issued read-only context handles; deterministic order, paging, explicit availability/type/redaction. |
| evaluate | Exact known state-key lookup, never expression evaluation. An optional frameId must identify genuine supplied frame evidence. |
| loadedSources/source | Supplied mapping reference discovery and authorized in-memory content only. |
| setBreakpoints | Structurally validated unverified planning/correlation; no installation. |
| continue/pause/next/stepIn/stepOut/terminate | Error; no successful live-control or effect event. |
| setVariable/setExpression/restart/readMemory/writeMemory | Error; no mutation. |
| disconnect | Close DAP projection, never terminate execution. |
| Unknown request | Deterministic unsupported_request response. |

Response success denotes projection/query success only. DAP_RESPONSE != CANONICAL_EVIDENCE.

## Frames, contexts and variables

P13.3 retained results do not universally capture activation stacks. No stack is reconstructed from trace depth, directive nesting or host frames. Optional supplied `inspect_frame` evidence must have the pure-function-frame shape, same AIR identity and legitimate function/depth fields. The frame carries that canonical reference and explicit unavailable source location, rather than invented source coordinates. Paging a genuine single frame is supported. Redaction suppresses frame names/references.

Without frame evidence, stackTrace returns an empty stack and scopes rejects a fabricated frame ID. `apexforge/inspection` exposes explicitly projection-only context scopes independent of a call-frame claim:

State; Directive Context; Observed Program Authority; Debugger Execution Context; Evidence; Provenance — only when the corresponding supplied P13 input exists.

State variables preserve canonical state-key order, declared type record and typed observed value. Unavailable/unsupported/redacted values remain explicit. Other scopes delegate to the existing client presentation and label program authority separately from debugger-control authorization. VariablesReference is zero for expanded scalar projections; every variable carries a readOnly presentation hint. Scope handles are issued only by scopes/custom inspection and invalidated at closure.

Scope values refer to the supplied snapshot/context, not a synthesized state for every replay cursor position. No setVariable/setExpression implementation exists.

## Source and breakpoint projection

Mapped SourceIdentity objects come only from supplied P13.4 correlation chains, ordered deterministically. The adapter optionally accepts immutable owner-provided source-content pairs, validating their content through the existing SourceIdentity validator and rejecting unrelated/stale content. It performs no filesystem read.

loadedSources omits filesystem paths and returns local sourceReference plus logical display name. source resolves only an issued mapping reference, rejects path-based access and mismatched references, and returns content only if that exact authorized content was supplied. A known mapping with unavailable text is not fabricated into source content. Redacted source requests fail without display/content/hash leakage.

setBreakpoints accepts a bounded list of source locations, validates coordinate origin and rejects unsupported conditions/log fields. It projects candidates from existing correlation spans. A line request preserves all overlapping supported line candidates; a column request checks the supplied end-exclusive source position. Line/source-position granularity is explicit. Every result is verified=false, planningOnly=true, with runtime breakpoint execution unavailable. All candidates/ambiguity remain deterministic; no breakpoint ID/hit/installation or runtime hook is created.

NATIVE_REGION != MACHINE_ADDRESS; ordinary compiler-source to native full-chain admission remains unestablished under the frozen profile.

## Custom ApexForge namespace and delegation

| Custom request | Existing service/client delegation |
| --- | --- |
| apexforge/inspection | Read-only context scopes; no synthetic frame. |
| apexforge/correlate | P13.7 correlate over P13.4 index. |
| apexforge/planStep | P13.7 plan-step over P13.4 planner; planningOnly=true. |
| apexforge/evidence | Existing list/show/predecessors/successors graph navigation. |
| apexforge/provenance | Existing supported graph links only. |
| apexforge/causal | Existing recorded decisions/path evidence, preserving ambiguity. |
| apexforge/compare | Existing P13.6 comparison through the client; no global causal verdict. |
| apexforge/replayFirst/Next/Previous/Last/Seek | Existing P13.6 cursor through P13.7; reexecution=false. |

The remaining response is a bounded structured list of client presentation rows, labelled projectionOnly. These rows are DAP presentation, not a new evidence schema/producer. The adapter does not duplicate replay, comparison, routing, mapping or evidence algorithms.

Current active-session step-planning prerequisites remain inherited from P13.7; retained-only planning without those supplied prerequisites returns unavailable. Standard DAP stepping is never repurposed as replay/planning success. Unsupported ordering/replay availability remains unchanged.

## Redaction, attribution and security

A distinctive PRIVATE_CLI_SENTINEL_73 fixture and its result/input fingerprints are tested across variables, evaluate, frame labels, source errors/display, custom evidence/provenance/comparison/causal/correlation, replay, events and adapter repr. DAP state/evaluate additionally suppress all values when the evidence view is fully redacted, even if an embedding owner supplied a visible snapshot alongside it. Redacted lookup reports unavailable/redacted presentation rather than comparing secret hashes. Producer evidence and fingerprints are unchanged.

Diagnostics use fixed codes and omit expression/reference arguments or producer exception text. No adapter logs or debug-console events expose producer repr. The protocol command field still identifies the request, not a canonical semantic object.

EVIDENCE_BEFORE_ATTRIBUTION=True. Program authority remains observed evidence, not debugger-control permission. Causal selection is shown only if recorded; causal occurrence ambiguity remains ambiguous. Correlation/state difference/divergence/provenance does not infer root cause, ownership authority, human identity or external actor attribution. Missing evidence is not negative evidence.

No AIR/runtime/native execution, independent AuthorityEngine evaluation, process launch, shell escape, arbitrary import/eval/exec, arbitrary file access/write, authentication bypass, unsafe fallback or unredaction occurs. Standard control requests are not even submitted to P13.2 in this stage; actual control ownership remains outside the adapter.

## Focused validation and review classifications

Final command: `python -X utf8 -B apexforge/p13_8_dap_vscode_debugger_test.py`.

**30/30 PASS** against the final implementation. Consolidated tests cover framing fragmentation/multiple messages/limits/JSON/EOF; initialization and illegal sequencing; retained launch/supplied attach and prohibited PID/program fields; projection thread; genuine/absent frame; scopes/variables/unavailability; lookup-only evaluate; authorized source and arbitrary-path rejection; unverified breakpoint line/column/origin behavior; unsupported standard control/mutation; all custom planning/replay/evidence/provenance/comparison families; sentinel/hash redaction; disconnect/EOF/failure cleanup; live closure/rebinding; stale/unknown requests; deterministic protocol projection; unchanged producers; and static/dynamic separation.

Fixtures reuse existing P13 managed/native retained, divergent, causal, redacted and session-owner inputs. Existing execution owners run only in the test harness before DAP projection. Static AST tests reject execution/policy/process/eval/filesystem calls/imports; dynamic guarded projection traps those owners. No genuine VS Code host/installation/registration test is claimed.

No focused or predecessor test failure occurred. Review findings were classified before changes:

| Classification | Resolution or preserved gap |
| --- | --- |
| FROZEN_VSCODE_BOUNDARY | Adapter-only option selected; frozen extension remains untouched. |
| VSCODE_INTEGRATION_GAP | Authorized retained-provider/adapter startup seam absent; registration explicitly deferred, not called a semantic defect. |
| DAP_PROJECTION_GAP | Initial column requests used line candidates; refined against actual supplied positions and added a targeted regression. Optional evaluate frame context also validates genuine evidence. |
| DAP_LIFECYCLE_GAP | Added adapter-only handle invalidation on transport EOF/failure, with producer-custody regression. |

Earlier focused iterations passed 28 and 29 tests; the final suite passed 30. No assertions were weakened and no frozen module was modified.

## Final predecessor regressions

After final focused PASS, all requested relevant predecessors were rerun against the exact final files:

| Suite | Final result |
| --- | --- |
| P13.7 CLI debugger | 32/32 PASS |
| P13.6 replay/comparison | 25/25 PASS |
| P13.5 evidence inspection | 23/23 PASS |
| P13.4 correlation/planning | 21/21 PASS |
| P13.3 inspection | 21/21 PASS |
| P13.2 session/control | 21/21 PASS |

**143 predecessor tests PASS; 30 focused tests PASS.** No shared/frozen changes require older P12 closure. No VS Code package contribution was created, so unrelated historical P10 packaging tests were not run as adapter acceptance.

## Remaining scope and non-claims

VSCODE_INTEGRATION_GAP: no registration, fixed startup/provisioning bridge or authorized persisted loader. DAP_PROJECTION_GAP: complete retained semantic stacks/source-for-call-frame are not generally captured; custom context inspection preserves this limitation. These are explicit foundation limitations, not implementation defects in canonical semantics.

DEFER_TO_P13_9: Visual Studio integration is untouched. DEFER_TO_P13_10: richer semantic IDE/domain presentation is untouched. No such milestone has begun. Runtime control, breakpoint execution, raw machine stepping and TDP UI remain absent. Native artifact reproducibility remains toolchain-qualified; this adapter establishes no broader replay/binary/profile claims.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_P10_VSCODE_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_DAP_EXECUTES_AIR=False
P13_DAP_EXECUTES_RUNTIME=False
P13_DAP_DISPATCHES_NATIVE=False
P13_DAP_AUTHORITY_ENGINE=False
P13_DAP_HOST_COMMAND_EXECUTION=False
P13_DAP_LAUNCH_EXECUTES_PROGRAM=False
P13_DAP_OS_PROCESS_ATTACH=False
P13_DAP_VARIABLE_MUTATION=False
P13_DAP_EVALUATE_EXECUTES_EXPRESSIONS=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_VISUAL_STUDIO_DEBUGGER_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_DAP_TRANSPORT=PASS
P13_DAP_LIFECYCLE=PASS
P13_DAP_CAPABILITY_ADVERTISEMENT=PASS
P13_DAP_INSPECTION_PROJECTION=PASS
P13_DAP_VARIABLES=PASS
P13_DAP_SOURCE_PROJECTION=PASS
P13_DAP_BREAKPOINT_PLANNING=PASS
P13_DAP_STEP_PLANNING=PASS
P13_DAP_REPLAY=PASS
P13_DAP_EVIDENCE=PASS
P13_DAP_PROVENANCE=PASS
P13_DAP_REDACTION_BOUNDARY=PASS
P13_DAP_ATTRIBUTION_BOUNDARY=PASS
P13_DAP_THREAD_IS_DEBUGGER_PROJECTION=True
P13_DAP_SYNTHETIC_SEMANTIC_STACK=False
P13_DAP_EXTERNAL_LIVE_TRANSPORT_IMPLEMENTED=False
P13_DAP_BREAKPOINTS_PLANNING_ONLY=True
P13_DAP_STOPPED_EVENT_CAN_BE_OFFLINE_PROJECTION=True
P13_VSCODE_DEBUGGER_REGISTERED=False
P13_8_READY_FOR_REVIEW=True
```

## Preservation and exact Git status

Final audit verifies branch/HEAD/peeled freeze unchanged, all 19 incoming hashes preserved, all tracked P12/frozen P10 VS Code files unchanged, empty staged index, exactly 22 untracked P13 candidates, empty build and no generated cache/binary residue. No stage, commit, tag, push, P13.9/P13.10, Visual Studio debugger, semantic IDE views or TDP UI work.

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/p13_3_semantic_state_authority_inspection_test.py
?? apexforge/p13_4_source_air_native_correlation_step_planning_test.py
?? apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py
?? apexforge/p13_6_deterministic_replay_trace_comparison_test.py
?? apexforge/p13_7_cli_debugger_test.py
?? apexforge/p13_8_dap_vscode_debugger_test.py
?? apexforge/tooling/debug_cli.py
?? apexforge/tooling/debug_correlation.py
?? apexforge/tooling/debug_dap.py
?? apexforge/tooling/debug_evidence.py
?? apexforge/tooling/debug_inspection.py
?? apexforge/tooling/debug_replay.py
?? apexforge/tooling/debug_session.py
?? docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md
?? docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md
?? docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md
?? docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md
?? docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md
?? docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md
?? docs/p13/P13_7_CLI_DEBUGGER.md
?? docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md
```

