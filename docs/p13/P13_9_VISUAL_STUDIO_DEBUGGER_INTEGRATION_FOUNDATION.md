# P13.9 — Visual Studio Debugger Integration Foundation

Status: ready for human review of the bounded command-client foundation. This report does not declare the milestone frozen, released, or canonized. No installed Visual Studio debugger is claimed.

## Baseline and preservation

Branch: `p13-1-debugger-architecture`. HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.

Before implementation, the 22 incoming P13 candidates were hashed; the index and tracked tree were unchanged and no generated residue was present. The following SHA-256 values are the incoming byte hashes, not semantic identities. All 22 were rechecked unchanged after implementation. All tracked P12, P10/P11 Visual Studio, and P10 VS Code files remain unchanged.

| Incoming candidate | SHA-256 |
| --- | --- |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/p13_6_deterministic_replay_trace_comparison_test.py` | `5770090A9040527ABA26EADF5FF46457B8FE8211389244AF5066F6CBFE9BCF9B` |
| `apexforge/p13_7_cli_debugger_test.py` | `BB8C014C44288A05450477D33BEA57AC236EF06987BE758AC6D9BBBDF56154A8` |
| `apexforge/p13_8_dap_vscode_debugger_test.py` | `2189C9401B669855127D8EE3F2EB4AA5DC5DAE4D73691E870D4CCB23FEF70ED5` |
| `apexforge/tooling/debug_cli.py` | `84B2091E8A7FC294FEF24F786834D3E0BA806EEB7B03C438EDE64E1ABB168101` |
| `apexforge/tooling/debug_correlation.py` | `981E6FEC0A2B4CEA1F044D565805506EC75D0C1E6150313076867254EFB9339B` |
| `apexforge/tooling/debug_dap.py` | `67C70E700A0BF059CFBC28053A60B4AA4374DD809B6182FF8741BF990B6E49D4` |
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
| `docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md` | `4FC56C5F0FE16EEDF9B977BC0F242643BDE7C4A6E9E96D7E0951A0D9F1659F0E` |

Only three P13-owned files are added in this slice: `apexforge/tooling/debug_visualstudio.py`, `apexforge/p13_9_visual_studio_debugger_integration_test.py`, and this report. Final candidate count: 25.

## Repository evidence and integration decision

The inventory covers the Visual Studio solution/project, VSIX manifest, VSCT menu resource, AsyncPackage, three command classes, MEF content type/classification components, language client/locator/trace components, packaging/integration/language-feature documentation, Python Visual Studio contracts and auditors, and the P11 SRA-D historical acceptance ledger/test. Searches found no existing debugger contribution, IDebugEngine/Concord implementation, or OpenDebugAD7/DAP debugger bridge in the extension.

The frozen extension is a net472 SDK-style VSIX project for Visual Studio 17.x, with package and MEF assets for amd64/arm64. Its AsyncPackage registers Extension Status, Restart Language Server and Open Language Server Log. Its MEF ILanguageClient is language-server integration; its process-launch support is not an ApexForge execution-control or debugger provisioning seam. The existing P11 equivalence evidence preserves the rule that the IDE cannot become a second semantics implementation. That historical freeze test binds a different branch/base and release delta; it was inspected, not invoked as a P13 acceptance test.

Selected mechanism: **VISUAL_STUDIO_COMMAND_CLIENT**. The new Python client is an owner-injected, in-process integration boundary for a future Visual Studio embedding. It delegates through the existing P13.8 DAPAdapter to P13.7 client commands and P13.2–P13.6 models. This is not proof that Visual Studio natively consumes this DAP adapter. No C# package, debug engine, MEF export, VSCT command, VSIX or IDE registration was created.

The reviewed P13 carriers remain their respective owners: debug_session owns session/authorization contracts; debug_inspection projects supplied semantic values; debug_correlation plans supplied mapping targets; debug_evidence projects retained evidence; debug_replay navigates/compares observations; debug_cli orchestrates client commands; debug_dap projects their responses. The new module contains no competing algorithms.

**TARGET_PROVISIONING_GAP:** no safe persistent retained-target loader suitable for IDE activation exists. Provisioning remains dependency injection of an already-authorized DebuggerCLI plus optional immutable source identity/content pairs validated by the existing DAP owner. There are no arbitrary file, executable, PID, module-import or connection fields. Registration remains deferred; frozen P10/P11 files are not reopened.

## Client identities, operating modes and lifecycle

`VisualStudioClient` has a read-only local `vs_session_id`, a separate DAP connection identifier, and connection-local request sequence. Neither is canonical semantic identity. The injected application's P13 execution/session bindings remain intact:

```text
VS_SESSION != DEBUG_SESSION
VS_PROCESS != APEXFORGE_EXECUTION
VS_THREAD != SEMANTIC_THREAD
VS_FRAME != SEMANTIC_FRAME
IDE_SELECTION != EXECUTION_STATE
VISUAL_STUDIO_PROJECTION != SECOND_DEBUGGER_MODEL
```

Lifecycle: created -> connected -> closed; connect initializes the existing adapter, binds retained launch or authorized supplied-session attach, then completes configuration. Failure closes local projection state. Reconnect after closure is rejected. No external live transport or process attachment is introduced.

Retained mode consumes existing immutable histories and may survive producer-session closure under the retention contract. Supplied-session mode is only an in-process projection; active-session/observe checks and all binding validation remain in P13.8. Cross-session owner replacement, cross-execution history replacement and queries against closed live sessions are rejected.

Disconnect closes adapter-local handles and the client only. It does not close the ApexForge session, terminate execution, delete retained evidence or revoke provenance. No stopped/terminated adapter event is reinterpreted as producer execution evidence.

## Command and presentation contract

Client version: `apexforge.debug.visualstudio/v1`. This identifies the local command-client API, not a registered Visual Studio protocol. Existing DAP capabilities are returned by connect; capability advertisement and ordering are delegated.

| Client command | Existing projection |
| --- | --- |
| Inspect | apexforge/inspection |
| State / Directive Context | Read-only existing inspection scopes and variables |
| Observed Program Authority | Existing program-authority scope |
| Debugger Session Authorization | Existing debugger execution context/status; capability presence does not grant authority |
| Projection Threads / Semantic Stack | Existing explicitly labeled DAP projection thread and supplied frame evidence |
| Watch Lookup / Tooltip Lookup | Existing exact known-state lookup; no expression evaluator |
| Sources / Source Content | Existing authorized source references and supplied content |
| Correlate | P13.4 through apexforge/correlate |
| Plan Breakpoints | Existing unverified DAP location-correlation planning |
| Plan Semantic Step / Plan Source Step / Plan Native Correlation | P13.4 through apexforge/planStep |
| Evidence / Provenance / Causal Evidence | P13.5 graph queries through existing client |
| Replay First / Previous / Next / Last / Seek | P13.6 observational replay |
| Compare | Existing P13.6 comparison domains |

These are library command labels for a future embedding, not installed Visual Studio menu entries, Watch/Immediate Window providers, tool windows or semantic IDE views.

Responses are frozen `Projection(success, code, payload)` records. Payload is deterministic JSON of the existing adapter response body; `view()` returns a fresh presentation copy. Connection sequences and producer objects are not embedded. Local edits to that copy cannot change retained evidence. Fixed failure codes omit request text and producer repr. The client does not keep logs.

## Inspection, authority and result context

State preserves existing key order, type, availability and read-only presentation hints. Unavailable values remain explicit. Directive/result/execution information is obtained from the existing supplied inspection/evidence/compare projections, without calculating semantics.

Program authority and debugger/session authorization are separate named command surfaces. Displaying an authority observation neither reevaluates AuthorityEngine nor grants control authority. No variable editing, expression mutation, principal changes, directive activation or route changes exist.

## Source, AIR and generated-native navigation

Correlation uses P13.4 unchanged. SOURCE, AIR, GENERATED_NATIVE_REGION and MACHINE_ADDRESS remain separate fields; unavailable and ambiguous associations remain explicit. Source contents resolve only by an issued authorized reference and an owner-supplied identity/content binding, not by IDE filesystem paths.

Generated-native regions are not machine addresses, instruction pointers or PDB symbols. The bounded native fixture exposes the generated region while machine addressing remains unsupported. Ordinary compiler-source -> native full-chain admission remains unestablished under the frozen profile. No native profile expansion or source-mapping fabrication occurs.

## Breakpoint and step planning

Plan Breakpoints delegates P13.8's existing source-location correlation. Returned breakpoints remain unverified, explicitly planning-only, with runtime breakpoint execution unavailable; ambiguity is preserved by the underlying projection. The client installs no breakpoint.

Plan Semantic Step, Plan Source Step and Plan Native Correlation delegate P13.4 and return planningOnly=true and reexecution=false. No conventional Step Into/Over/Out, Continue, Pause or Immediate Window operation is exposed. A planned target is not execution advancement, and native correlation is not CPU-instruction stepping.

## Replay, comparison, evidence and provenance

Replay commands navigate retained observations through the existing cursor. They do not create trace records or execute again. Replay position is not live execution position.

Evidence and provenance navigation delegates supplied graph queries, not implicit filesystem/OS inspection. Compare renders existing divergence classes, not a new comparison algorithm or root-cause verdict. Causal selection is displayed only when recorded; ambiguous causal associations remain ambiguous.

```text
EVIDENCE_BEFORE_ATTRIBUTION=True
PROVENANCE != HUMAN_ATTRIBUTION
CORRELATION != CAUSATION
STATE_DIFFERENCE != CAUSAL_PROOF
RECORDED_CAUSAL_SELECTION != DEBUGGER_INFERRED_CAUSATION
REPLAY_POSITION != LIVE_EXECUTION_POSITION
EVIDENCE_UNAVAILABLE != EVIDENCE_FALSE
```

Native evidence continues to use actual retained build-receipt/result-input associations, not an invented execution receipt. No producer evidence, retained result or provenance association is rewritten.

## Stack, thread and evaluate boundaries

Semantic Stack returns no frames when none are supplied. A genuine supplied pure-function frame is projected with its existing canonical association. No trace-depth or Python/.NET/native host stack becomes an ApexForge stack.

Projection Threads returns the existing explicitly named debugger inspection projection, labeled “not OS thread.” Its local ID does not identify an ApexForge execution or semantic thread.

Watch Lookup and Tooltip Lookup use exact known-state lookup only. Unknown expressions, arithmetic, shell syntax and code snippets fail. No ApexForge/C#/Python/JavaScript interpreter or host command facility is introduced.

## Security, redaction, determinism and custody

The client has a fixed command allowlist and no authority bypass. Arbitrary process attach, executable launch, file execution, shell commands, mutation and live-control button names are rejected. Source navigation is reference-bound. The actual access/authorization decision for injected retained material remains with the embedding owner; this slice adds neither authentication nor a permissions engine.

The distinctive sensitive fixture `PRIVATE_CLI_SENTINEL_73` is suppressed across State, Tooltip/Watch lookup, evidence, provenance, correlation/error responses, comparison, replay, source, stack and client/result repr. The stronger case supplies a visible inspection snapshot alongside fully redacted evidence; existing DAP redaction still suppresses values. Producer result fingerprints do not leak through that client-visible redacted projection. Canonical producer fingerprints are not modified.

Equivalent inputs yield equal capabilities and command projections. State/evidence/correlation/replay ordering and JSON canonicalization remain with existing owners; meaningful ambiguity is not normalized away. Local IDE/DAP IDs and navigation state are observational, outside semantic fingerprints.

Local client sequences/handles are ephemeral operational resources owned by this projection, used only for presenting supplied evidence, valid until disconnect. Closing invalidates adapter-local handles. Canonical retained evidence keeps its existing owner, purpose, lifetime and binding. No retained producer evidence is copied into a new semantic carrier. MSC remains an analytical resource-continuity lens, not a runtime dependency.

## Validation and failure classifications

Focused command:

```text
python -X utf8 -B apexforge/p13_9_visual_studio_debugger_integration_test.py
23/23 PASS
```

The tests cover identity separation; stable capabilities; retained state/order/types/unavailable values; separate authority surfaces; authorized source navigation; AIR/native-region mapping; unverified breakpoint planning; all three step plans; evidence/provenance/causal/compare boundaries; all replay movements; absent and genuine stack evidence; explicitly local thread projection; watch/tooltip lookup; host/process/mutation rejection; local disconnect; cross-execution/session rejection; closed-live versus retained behavior; distinctive redaction sentinel and producer-hash protection; immutable presentation copies; deterministic projections; native retained passivity; AST separation.

Initial focused run: **TEST_FIXTURE_DEFECT**. Three assertions used the wrong existing accessors/labels: session identity is session.reference.session_id; capabilities is a property; the native layer is GENERATED_NATIVE_REGION and machine availability is unsupported. Only those new assertions were corrected; no production or predecessor code changed. Final focused rerun passed.

Final combined regression command:

```text
python -X utf8 -B -m unittest discover -s apexforge -p p13_*_test.py
196/196 PASS
```

| Suite | Tests | Result |
| --- | ---: | --- |
| P13.2 session/control | 21 | PASS |
| P13.3 inspection | 21 | PASS |
| P13.4 correlation/planning | 21 | PASS |
| P13.5 evidence | 23 | PASS |
| P13.6 replay/comparison | 25 | PASS |
| P13.7 CLI | 32 | PASS |
| P13.8 DAP | 30 | PASS |
| P13.9 command client | 23 | PASS |

Thus all seven requested predecessor suites passed 173/173 against the final new code. No frozen/shared production module changed, so unrelated P12 closure was not run.

Static AST inspection finds no AIR/RuntimeEngine/native/AuthorityEngine/process-launch/eval/exec/host execution imports or calls in the new module. Dynamic guards trap semantic execution, native build/dispatch, authority evaluation, producer mutation and filesystem/process access during client operations; the native retained history remains byte-canonical unchanged. Real execution occurs only in existing controlled fixture setup, outside the client.

### Frozen Visual Studio coexistence

- P10-T5.1 foundation smoke: PASS, including source/solution/SDK/MEF/package contracts and synthetic temporary VSIX audits. No VSIX was built or installed.
- Initial runpy batch omitted the ApexForge import root: **TEST_INVOCATION_DEFECT**, ModuleNotFoundError(language_server). Rerun with sys.path rooted at apexforge reached the audits.
- P10-T5.3 bridge smoke and standalone P10-T5.6 commands smoke: **ENVIRONMENTAL_CONSTRAINT**, existing T5.2 byte-hash audit rejected five Classification C# checkout files. The checkout uses CRLF whereas the committed and expected audit bytes use LF. Representative ApexForgeClassifier.cs: checkout SHA-256 `6D271923E82F699E818D6A7C820751F2A0EA3D72247525C7FB33EBFE1ECD4902`, HEAD/expected `AF7BCA59BA5004F9652184E8B91CEC2FA1AC46EFD567398C049D733A7FC16E29`; 320 CRLF sequences in checkout versus zero in HEAD; LF-normalized bytes are equal. Git reports no tracked change. These failing audit results are retained, not called PASS, weakened, patched or hidden.
- Historical P11 SRA-D acceptance was inspected for coexistence doctrine and frozen boundaries, not reused to claim P13 registration. No historical branch/release-delta checks were invoked.

### Remaining gaps and exclusions

| Classification | Evidence/status |
| --- | --- |
| TARGET_PROVISIONING_GAP | Persistent authorized retained-target descriptor/loader remains absent; no arbitrary-path fallback. |
| VISUAL_STUDIO_INTEGRATION_GAP | Actual IDE registration/host binding deferred; Python command-client foundation only. No claim of native VS DAP consumption. |
| FROZEN_VISUAL_STUDIO_BOUNDARY | Earlier package/MEF/menu/editor files are preserved; no convenience registration change. |
| ENVIRONMENTAL_CONSTRAINT | Frozen byte-level bridge/command coexistence audits fail on unchanged CRLF checkout; no frozen-file repair in this slice. |
| DEFER_TO_P13_11 | Actual installed IDE/cross-target validation remains later work; existing editor acceptance is not debugger acceptance. |

No P13.10 semantic IDE views, TDP UI, cross-target closure or freeze work was started. No live pause/resume, runtime breakpoint execution, raw-machine stepping, process suspension, native dispatcher, independent authority engine or alternate semantics was added.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_P10_VISUAL_STUDIO_REOPENED=False
P13_P11_VISUAL_STUDIO_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_VS_EXECUTES_AIR=False
P13_VS_EXECUTES_RUNTIME=False
P13_VS_DISPATCHES_NATIVE=False
P13_VS_AUTHORITY_ENGINE=False
P13_VS_HOST_COMMAND_EXECUTION=False
P13_VS_OS_PROCESS_ATTACH=False
P13_VS_VARIABLE_MUTATION=False
P13_VS_EVALUATE_EXECUTES_EXPRESSIONS=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_TDP_UI_IMPLEMENTED=False
P13_VS_INTEGRATION_MECHANISM=VISUAL_STUDIO_COMMAND_CLIENT
P13_VS_INSPECTION_PROJECTION=PASS
P13_VS_STATE_PROJECTION=PASS
P13_VS_AUTHORITY_PROJECTION=PASS
P13_VS_CORRELATION_PROJECTION=PASS
P13_VS_BREAKPOINT_PLANNING=PASS
P13_VS_BREAKPOINTS_PLANNING_ONLY=True
P13_VS_STEP_PLANNING=PASS
P13_VS_RUNTIME_STEPPING=False
P13_VS_REPLAY=PASS
P13_VS_EVIDENCE=PASS
P13_VS_PROVENANCE=PASS
P13_VS_REDACTION_BOUNDARY=PASS
P13_VS_ATTRIBUTION_BOUNDARY=PASS
P13_VS_SYNTHETIC_SEMANTIC_STACK=False
P13_VS_THREAD_IS_DEBUGGER_PROJECTION=True
P13_VISUAL_STUDIO_DEBUGGER_REGISTERED=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
P13_9_READY_FOR_REVIEW=True
```

PASS describes the demonstrated bounded in-process client foundation, not installed Visual Studio debugger acceptance.

## Exact final Git status

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/p13_3_semantic_state_authority_inspection_test.py
?? apexforge/p13_4_source_air_native_correlation_step_planning_test.py
?? apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py
?? apexforge/p13_6_deterministic_replay_trace_comparison_test.py
?? apexforge/p13_7_cli_debugger_test.py
?? apexforge/p13_8_dap_vscode_debugger_test.py
?? apexforge/p13_9_visual_studio_debugger_integration_test.py
?? apexforge/tooling/debug_cli.py
?? apexforge/tooling/debug_correlation.py
?? apexforge/tooling/debug_dap.py
?? apexforge/tooling/debug_evidence.py
?? apexforge/tooling/debug_inspection.py
?? apexforge/tooling/debug_replay.py
?? apexforge/tooling/debug_session.py
?? apexforge/tooling/debug_visualstudio.py
?? docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md
?? docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md
?? docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md
?? docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md
?? docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md
?? docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md
?? docs/p13/P13_7_CLI_DEBUGGER.md
?? docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md
?? docs/p13/P13_9_VISUAL_STUDIO_DEBUGGER_INTEGRATION_FOUNDATION.md
```

The index is empty and HEAD/tag unchanged. All 22 incoming hashes are preserved; all tracked frozen files are unchanged; there is no generated residue. No staging, commit, tag or push occurred. Stop at P13.9.

