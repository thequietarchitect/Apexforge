# P13.10 — Semantic IDE Views & TDP Preview Components

Status: **ready for human review** of portable presentation models. No host UI, operational TDP platform, roadmap closure, release or freeze is declared.

## Frozen baseline and incoming hashes

Branch: `p13-1-debugger-architecture`. HEAD and peeled `afp-p12.8-freeze` both equal `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.

Before implementation: 25 untracked P13 candidates; index empty; all tracked P12 and frozen P10/P11 IDE files unchanged; no generated residue. Incoming SHA-256 values below identify file bytes, not canonical semantics. All 25 remain preserved.

| Incoming candidate | SHA-256 |
| --- | --- |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/p13_6_deterministic_replay_trace_comparison_test.py` | `5770090A9040527ABA26EADF5FF46457B8FE8211389244AF5066F6CBFE9BCF9B` |
| `apexforge/p13_7_cli_debugger_test.py` | `BB8C014C44288A05450477D33BEA57AC236EF06987BE758AC6D9BBBDF56154A8` |
| `apexforge/p13_8_dap_vscode_debugger_test.py` | `2189C9401B669855127D8EE3F2EB4AA5DC5DAE4D73691E870D4CCB23FEF70ED5` |
| `apexforge/p13_9_visual_studio_debugger_integration_test.py` | `829A299882F29CCD7674C0E4DE4888E21ED9B0BED68C07C54B8F87A1E8F071A4` |
| `apexforge/tooling/debug_cli.py` | `84B2091E8A7FC294FEF24F786834D3E0BA806EEB7B03C438EDE64E1ABB168101` |
| `apexforge/tooling/debug_correlation.py` | `981E6FEC0A2B4CEA1F044D565805506EC75D0C1E6150313076867254EFB9339B` |
| `apexforge/tooling/debug_dap.py` | `67C70E700A0BF059CFBC28053A60B4AA4374DD809B6182FF8741BF990B6E49D4` |
| `apexforge/tooling/debug_evidence.py` | `ED2A67EF80B8765EDB810137C86EB3E569B7EA022EADC9878ABEF9E9B478FC72` |
| `apexforge/tooling/debug_inspection.py` | `409099E910F5D5313DF5EA4949DBB6A1BAFFB6CA037554A22D373651B152D466` |
| `apexforge/tooling/debug_replay.py` | `44E06F35955279E0C5A7D0048050AB74D2D36512C3E88C834687C98DEDEFF8C5` |
| `apexforge/tooling/debug_session.py` | `22C530D30A9E0D87276DA1CBB39D38ADA8C34B78A00F3DD1216F1BEF3AEBE774` |
| `apexforge/tooling/debug_visualstudio.py` | `9B4F05CA0F6AC9048903516062FFFFEE247E93660013652703BCC204410593FF` |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |
| `docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md` | `F7B62CD5C668E7B5D14FD02BD3003CBC91652B1F714D27CE880A13C75CDFACE4` |
| `docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md` | `8975BE6FBD6E3DDA654A98FBC9C11FAE5A996D47F91C63AA58064114C48DBF3F` |
| `docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md` | `8F849F358D85B1B6FDD5E9433BE0C13EA57FF822BF8D794FDCA246612A01F163` |
| `docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md` | `1C8235AF503E484D04EBF106104B18BA54FB4AB5704C58FFD992FF1BB652E3B1` |
| `docs/p13/P13_7_CLI_DEBUGGER.md` | `24795ACDA46D654224543924C1E602D81C3E37460CB6C4AA0CF72B9E023FDCDA` |
| `docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md` | `4FC56C5F0FE16EEDF9B977BC0F242643BDE7C4A6E9E96D7E0951A0D9F1659F0E` |
| `docs/p13/P13_9_VISUAL_STUDIO_DEBUGGER_INTEGRATION_FOUNDATION.md` | `869B1E66CE5316796DC0F8417FFF4B8E7D47E0F3939FF5201B6F10DF90DF91BA` |

Exactly three new files: `apexforge/tooling/debug_views.py`, `apexforge/p13_10_semantic_ide_views_tdp_preview_test.py`, and this report. Final candidate count: 28. No earlier P13 file or tracked frozen file is modified.

## Inspected conventions and architectural continuity

Repository inspection found existing immutable P13.5 EvidenceNode/EvidenceEdge/EvidenceGraph serialization, P13.6 ordering-domain timelines/comparisons, P13.3 explicit inspection fields and typed state, P13.4 correlation/step-planning references, P13.7 deterministic JSON rendering, P13.8 read-only DAP projections, and the P13.9 isolated command client. These remain the debugger algorithm owners.

Existing IDE work provides hierarchical documentSymbol projections in the VS Code language client and frozen Visual Studio editor/language-server command infrastructure. No safe debugger target-provisioning or portable semantic-dashboard host-registration seam was established. Generic view documents are preferable to modifying frozen extension/webview/tool-window registrations. Language/narrative graph ownership remains separate from debugger evidence graph projection.

P13.1 reserves TDP as a downstream observability consumer. Repository searches found no concrete operational TDP dashboard, telemetry, FAME, Varenic trajectory, containment, Medic or policy/throttle provider suitable for filling these panels. The supplied TDP reference architecture and role contract are preserved as preview composition requirements, not claimed implementations.

Architecture:

```text
Canonical semantics/evidence
  -> P13 debugger substrate
  -> portable semantic view documents
  -> future CLI / IDE / dashboard / domain presentation
```

## Common immutable view contract

Schema: `apexforge.debug-views/v1`. `ViewDocument` records kind, view-local ID, title, mode/session/execution context, availability, immutable nodes/edges, ordering domain and explicit limitations. `ViewBundle` composes documents without merging identities. `ViewNode` contains a local handle, kind/label, explicit availability, optional supplied reference and canonical JSON presentation data. `ViewEdge` contains local endpoints, the existing relation name and supporting evidence reference.

Availability distinguishes available, partial, unavailable, unsupported, not_applicable, redacted and ambiguous. Detailed source/inspection/replay availability remains explicit in supplied field records. Unavailable evidence is not negative evidence. A document's presence is not a claim of complete evidence coverage.

The v1 JSON shape is a presentation contract. Incompatible interpretation/field-shape changes require a new schema version; additive optional fields may be ignored by readers. It is not a new semantic or provenance protocol. No semantic fingerprint is assigned to a view.

Equivalent supplied debugger inputs produce equal detached documents and deterministic serialization. All JSON is primitive data, with stable key ordering; no live producer object, callback, arbitrary repr or mutable runtime handle is exposed. Returned record dictionaries are fresh presentation copies.

## Identity and session binding

```text
VIEW != SEMANTIC_OBJECT
VIEW_ID != SEMANTIC_IDENTITY
GRAPH_EDGE != NEW_SEMANTIC_RELATIONSHIP
TIMELINE_POSITION != EXECUTION_POSITION
DASHBOARD_STATE != RUNTIME_STATE
UI_SELECTION != AUTHORITY
VISUALIZATION != EVIDENCE
DISPLAYED_CAUSAL_LINK != INFERRED_CAUSATION
```

Graph handles are prefixed per view family and remain distinct from the underlying P13.5 evidence IDs. Evidence and provenance documents can point to the same producer references while keeping different local IDs. Local state/timeline item handles are presentation indexes.

Owner/session/history/correlation references must agree structurally on session and execution when supplied together. Resource input is also checked against the projected execution. Retained views can remain readable after producer-session closure under existing retention contracts; supplied live-session views require the existing active/observe binding checks. Neither path grants authorization. Provisioning and retained-material access authorization remain with the embedding owner.

A private in-process DAP projection delegates read-only scopes, correlation, comparison and step planning. Its local handles are closed after construction. Timeline construction uses P13.6 directly and never moves the client's replay cursor. The application, debugger session and producer evidence remain unchanged.

## Overview

The overview identifies retained versus supplied-session mode, separate session/execution references, sorted actual capabilities, evidence/replay availability, per-operation source/native mapping availability and AIR availability where supplied.

It prominently states **LIVE_RUNTIME_CONTROL=UNAVAILABLE**. An in-process supplied session does not imply continuous telemetry, external live transport, runtime pause/resume, executable breakpoint support or IDE registration.

## Semantic state

State uses the existing P13.8 projection of P13.3 entries. Key order, declared type, visible observed value, explicit unavailable/redacted value and readOnly hints are retained. There is no editing or mutation affordance.

Fully redacted evidence suppresses values even if a visible snapshot was also supplied. State-to-AIR reference records are projected separately from state values; missing associations are unavailable rather than guessed. No state assignment, operation evaluation or transition recomputation occurs.

## Directive/context

The directive/context document includes the supplied directive observation, P13.3 plan association and correlation reference. Entry/directive/plan facts remain the original inspection field records. No directive activation or declaration-order execution claim is inferred.

## Authority documents

Program authority and debugger authority are separate document kinds:

- **Observed Program Authority** retains existing authority evidence and supplied program principal/role reference.
- **Debugger Session Authorization** retains existing debugger context, session principal and capability information. Its control-authorization item explicitly says the view has not evaluated authorization and capability is not authorization.

They have no invented cross-authority edges. No AuthorityEngine evaluation, authority grant/revocation or permissions merge occurs.

`PROGRAM_AUTHORITY != DEBUGGER_CONTROL_AUTHORITY` remains binding.

## Source / AIR / generated-native correlation

The correlation document delegates P13.4 through the existing DAP/client projection. SOURCE, AIR, GENERATED_NATIVE_REGION and MACHINE_ADDRESS remain separate. Unmapped hand-built AIR, non-native not_applicable and ambiguous source candidates are preserved. No nearest-source fallback is introduced.

Real source-produced retained managed evidence supports source/AIR mapping and non-native classification; the existing bounded-native fixture supports generated-native regions with source unavailable. Machine addressing remains unsupported. Ordinary compiler-source -> native full-chain admission remains unestablished under the frozen profile. No PDB, instruction pointer, assembly or machine-code panel is fabricated.

## Evidence and provenance graph

Evidence/provenance documents project the supplied P13.5 graph. Node references and data retain existing availability and carrier identities. Every projected edge corresponds exactly to an existing edge and its supporting reference; only endpoints are translated to view-local handles. Deterministic node/edge ordering uses existing evidence IDs and relation/support tuples.

The graph may include concrete compiler TAM, trace families, authority observations, mapping associations, artifacts, actual native build receipts, execution/result associations and provenance scopes. Partial chains are valid. Native result-input/build-receipt associations are used as retained; no distinct execution receipt is invented.

The provenance graph is a different presentation of existing relationships, not a provenance producer or ownership authority. It cannot establish human or external-actor attribution.

## Recorded causal evidence

Causal nodes are restricted to supplied canonical decision/path nodes and recorded causal-selection trace nodes. Edges are only existing graph relations between selected nodes. Alternatives, recorded selections and ambiguous canonical-path association fields remain supplied payload data.

A controlled fixture with two real canonical decisions sharing path identities demonstrates preserved ambiguity: no selected_path edge is invented when association is ambiguous. No state difference, trace proximity or graph layout becomes causal proof.

```text
RECORDED_CAUSAL_SELECTION != DEBUGGER_CAUSAL_INFERENCE
CAUSAL_EVIDENCE != ROOT_CAUSE
PROVENANCE != HUMAN_ATTRIBUTION
EVIDENCE_UNAVAILABLE != EVIDENCE_FALSE
```

## Trace/replay timeline

Timeline entries identify deterministic replay sequence, explicit ordering domain, logical key, existing evidence reference and availability. P13.6 build_replay determines the supplied ordering projection.

Tests cover retained stream order, selected native trace-family order and an unavailable semantic-order projection. No universal timeline or timestamp-derived causal order is introduced. Unsupported/absent ordering produces no fabricated entries. Whole-view redaction suppresses producer-derived timeline references.

`REPLAY_POSITION != LIVE_EXECUTION_POSITION`. Constructing the timeline neither reexecutes nor changes the client cursor.

## Comparison

The comparison document renders P13.6 domain results separately: input/AIR, state, directive, authority, causal evidence, result, trace, mapping, provenance, native artifact and build receipt where supported. Insufficient/redacted domains remain explicit. Volatile differences have their own row; they do not become semantic divergence.

Tests show state divergence and volatile-only separation. The existing result contains no global causal verdict; CAUSAL_EXPLANATION and ACTOR_ATTRIBUTION remain not_inferred.

## Step planning

The planning document displays requested semantic/source/native-correlation mode, supplied planning result and correlated target data. Even an unavailable target retains prominent **STEP_PLAN_ONLY=True** and the limitation STEP_PLAN_NOT_EXECUTION_ADVANCEMENT.

All three modes delegate P13.4 through the existing client. No runtime button, execution advancement, breakpoint installation or raw-machine stepping is added.

## Resource continuity

`ResourceInput` is a thin immutable association of an existing P12.8 ResourceOwnership, a supplied execution reference, and explicit binding/cleanup InspectionFields. It is not a new resource authority or observer. No filesystem/process measurement is performed.

The resource view records class, scope, known/unknown owner, purpose, trigger, intended lifetime, cleanup boundary, supplied binding and supplied cleanup evidence. Unknown owner/purpose/lifetime or missing binding produces partial availability. Cleanup intent is not cleanup proof; a missing cleanup observation remains unavailable.

```text
Retained Resource => Known Owner + Known Purpose + Known Lifetime + Valid Binding
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
```

Resource records are sorted deterministically independent of input tuple order. Cross-execution association is rejected. No resource records are invented when none are supplied. The embedding owner remains responsible for the validity/authentication of supplied binding evidence; the view does not certify it.

View/DAP-local indexes are ephemeral operational presentation resources. Canonical retained evidence preserves its own owner, purpose, lifetime and binding. Closing local handles does not delete that evidence.

## Cross-view navigation

Navigation items expose existing graph source/target/support references only. Source-to-AIR, AIR-to-generated-region, result-to-execution/evidence and retained/provenance relations can be followed in either direction by a later client using these explicit associations. Following a recorded edge backward is navigation, not creation of an inverse semantic relationship.

State/AIR navigation separately preserves each supplied P13.3 source_air field. Missing links remain missing. There is no fuzzy match, name similarity, nearest-source heuristic or inferred link. Tests validate exact supplied support tuples and real result/mapping associations.

## Deterministic serialization and redaction

All documents and TDP composition serialize deterministically with explicit schema, stable keys, ordered nodes/edges/sections, availability, readOnly and limitations. View-local selections, timestamps, process data and transport sequences are outside this representation; session/execution references are contextual client bindings, not new canonical semantic fingerprints.

The distinctive sentinel `PRIVATE_CLI_SENTINEL_73` is absent from all view data, labels, repr and serialized dashboard composition in the redacted fixture. Producer result/state hashes are also withheld. Tests include fully redacted evidence combined with an otherwise visible supplied snapshot. Graph/timeline/navigation/resource content is conservatively suppressed on redacted input rather than exposing producer IDs or hashes. Producer hashes and evidence are never rewritten.

Diagnostics are fixed codes and do not interpolate supplied evidence payloads.

## TDP preview dashboard composition

`TDPPreview` composes generic document IDs, section status/reason and fixed distinct role contracts. It is a model for future UI, not an installed dashboard, operational service, telemetry provider or defensive engine.

| Section | Current status/meaning |
| --- | --- |
| Overview | Partial supplied debugger/session/evidence availability; not security posture |
| Live Monitor | Partial retained observations where available; never continuous telemetry |
| Transvergent Analytics | Deferred; DEFERRED_TDP_TELEMETRY_PROVIDER; no derivative/time-series computation |
| Mosaic / FAME | Deferred P15 TDP provider; no fabricated AUTH/NETWORK/FILESYSTEM/PROCESS/IDENTITY regions |
| Varenic Trajectories | Deferred P15 TDP provider; no inferred direction/convergence |
| Incidents & Containment | Partial evidence observation references only; no incident classification or containment |
| Medic Lab | Partial retained provenance/evidence references only; no diagnosis engine or remediation |
| Policy & Throttle | Deferred P15 provider; no policy/throttle execution |
| Reports | Available deterministic serialization of supplied views only |
| Simulation | Deferred P15 provider; no simulation results |
| System Health | Partial debugger-component availability only; not system-security health |

Unavailable or redacted underlying documents propagate that state into their preview sections. Unsupported panels have no synthetic metric or fake domain value.

Role contracts remain separate and provide no shared authority:

```text
SENTINEL -> observes/detects
TDP -> evaluates dynamics/response
CONTAINMENT -> isolates
MEDIC -> diagnoses/reconstructs
VERIFICATION -> proves recovery
```

Section presence is not subsystem implementation. Evidence-before-attribution and actorAttribution=not_inferred are serialized explicitly. No coloring, anomaly score, provenance relation or panel label establishes external actor identity.

## Security and host-registration status

No host UI is registered. VS Code and Visual Studio debugger registration remain false; no frozen IDE file is modified. A future host must provide authorized retained material through a bounded provisioning seam.

The module contains no AIR/RuntimeEngine/native execution, independent AuthorityEngine evaluation, shell/process launch, arbitrary file access, debugger session mutation, evidence writes or unredaction. It has no defensive action commands, authority bypass, expression evaluator or arbitrary host execution.

## Focused validation and failure ledger

Final focused command:

```text
python -X utf8 -B apexforge/p13_10_semantic_ide_views_tdp_preview_test.py
31/31 PASS
```

Coverage consolidates the requested cases: overview identities/capabilities; state types/order/unavailability/redaction; directive/plan context; separate program/debugger authority; mapped/unmapped/native/ambiguous correlation; exact supported graph relations; causal selection and ambiguity; explicit replay ordering and no cursor movement; comparison/volatile separation; all three planning modes; resource custody/order/binding; result/mapping/state navigation; immutable copies and deterministic serialization; complete TDP section order and deferred provider states; role separation/attribution; sentinel/hash protection; producer/session passivity; closed-live versus retained behavior; structural session/execution-label rejection; static and guarded dynamic separation.

Observed failures and review gaps were classified before edits:

- **TEST_FIXTURE_DEFECT:** initial mapped fixture omitted the existing required correlation_fingerprint anchor, causing two stale_correlation_evidence errors in a 28-test run. Corrected only the new fixture binding. No predecessor integrity check was weakened.
- **VIEW_MODEL_GAP:** review identified that graph presentation handles should be distinct from canonical evidence IDs. Added per-view prefixes in the new module and verified translation retains exact evidence relations.
- **SESSION_BINDING_GAP:** review identified possible mismatched supplied labels when owner/history/correlation objects are provided together. Added structural agreement checks in the new module and explicit rejection tests.
- **IMPLEMENTATION_DEFECT:** final review found a resource-order tie when custody fields matched but binding/cleanup evidence differed. Added those supplied fields to the deterministic sorting key and verified reversed input order yields identical serialization. Focused and aggregate validation were rerun after this final edit.

Source/causal ambiguity cases use the actual established carrier models and canonical execution owners in test setup. Existing guarded client/view construction runs after evidence is produced. No semantic execution is wrapped by debug_views.

## Final P13 regressions

```text
python -X utf8 -B -m unittest discover -s apexforge -p p13_*_test.py
227/227 PASS
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
| P13.9 Visual Studio foundation | 23 | PASS |
| P13.10 portable semantic views | 31 | PASS |

All eight requested predecessor suites pass **196/196** against the final files. Focused validation preceded the aggregate batch. No P10/P11 IDE/shared/frozen file changed, so older IDE audits and P12 closure were not rerun; P13.9's documented historical coexistence limitations are not erased or upgraded by this result.

AST inspection rejects semantic/host/mutation calls in the new module. Dynamic guards prohibit execution, authority evaluation, filesystem/process access and producer mutation during native retained view construction. Session canonical form, retained history canonical form, fake control owner's consumed requests and replay cursor remain unchanged.

## Remaining gaps and exclusions

| Classification | Remaining boundary |
| --- | --- |
| VIEW_MODEL_GAP | Future host layout/selection/interaction rendering; portable contracts only in this slice |
| TIMELINE_PROJECTION_GAP | Ordering domains not supported by supplied P13.6 evidence remain unavailable |
| GRAPH_PROJECTION_GAP | Missing relationships cannot be displayed as established links |
| DEFER_TO_P15_TDP | Operational telemetry, Transvergent metrics, FAME, trajectories, incident classification, containment, Medic, policy/throttle, simulation and recovery verification providers |
| DEFER_TO_P13_11 | Requested later cross-target/installed-client validation is not performed here |

No P13.11 cross-target closure, P13.12 freeze, P14 or full operational TDP work begins. No source/native admission expansion, runtime control, live breakpoint execution, machine stepping or IDE registration occurs.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_VIEWS_EXECUTE_AIR=False
P13_VIEWS_EXECUTE_RUNTIME=False
P13_VIEWS_DISPATCH_NATIVE=False
P13_VIEWS_AUTHORITY_ENGINE=False
P13_VIEWS_HOST_COMMAND_EXECUTION=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_VSCODE_DEBUGGER_REGISTERED=False
P13_VISUAL_STUDIO_DEBUGGER_REGISTERED=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_SEMANTIC_OVERVIEW_VIEW=PASS
P13_STATE_VIEW=PASS
P13_DIRECTIVE_VIEW=PASS
P13_AUTHORITY_VIEW=PASS
P13_CORRELATION_VIEW=PASS
P13_EVIDENCE_VIEW=PASS
P13_PROVENANCE_VIEW=PASS
P13_CAUSAL_VIEW=PASS
P13_REPLAY_TIMELINE_VIEW=PASS
P13_COMPARISON_VIEW=PASS
P13_STEP_PLANNING_VIEW=PASS
P13_RESOURCE_CONTINUITY_VIEW=PASS
P13_CROSS_VIEW_NAVIGATION=PASS
P13_VIEW_SERIALIZATION=PASS
P13_VIEW_REDACTION_BOUNDARY=PASS
P13_TDP_UI_PREVIEW_MODEL=True
P13_TDP_UI_IMPLEMENTED=False
P13_TDP_ROLE_SEPARATION_PRESERVED=True
P13_TDP_OPERATIONAL_PLATFORM_IMPLEMENTED=False
P13_TDP_LIVE_TELEMETRY_IMPLEMENTED=False
P13_TDP_FAME_ENGINE_IMPLEMENTED=False
P13_TDP_VARENIC_ENGINE_IMPLEMENTED=False
P13_TDP_CONTAINMENT_IMPLEMENTED=False
P13_TDP_MEDIC_IMPLEMENTED=False
P13_TDP_POLICY_THROTTLE_IMPLEMENTED=False
P13_10_HOST_UI_REGISTERED=False
P13_10_READY_FOR_REVIEW=True
```

PASS describes the demonstrated portable projection contract, not an installed host UI or operational defensive subsystem.

## Exact final Git status

```text
?? apexforge/p13_10_semantic_ide_views_tdp_preview_test.py
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
?? apexforge/tooling/debug_views.py
?? apexforge/tooling/debug_visualstudio.py
?? docs/p13/P13_10_SEMANTIC_IDE_VIEWS_TDP_PREVIEW.md
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

Final preservation audit: branch/HEAD/peeled freeze unchanged; all 25 incoming hashes preserved; all tracked P12 and frozen IDE files unchanged; empty index; no generated residue. No staging, commit, tag or push. Stop at P13.10.
