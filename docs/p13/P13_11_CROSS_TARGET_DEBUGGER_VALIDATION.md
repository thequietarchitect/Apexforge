# P13.11 — Cross-Target Debugger Validation

Status: **ready for human closure review**. This report does not begin P13.12 or declare closure, freeze, release, or operational IDE/TDP integration.

## Frozen baseline and incoming candidates

Branch: `p13-1-debugger-architecture`. HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.

Before validation, 28 incoming P13 files were hashed, nothing was staged, all tracked P12 and frozen P10/P11 IDE files were unchanged, and no generated residue was present.

| Incoming candidate | Incoming SHA-256 |
| --- | --- |
| `apexforge/p13_10_semantic_ide_views_tdp_preview_test.py` | `48CFE891070E8152D1E53E23F4596E0743E87E7342CC394E8DC3EA3B83C26B07` |
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
| `apexforge/tooling/debug_views.py` | `BF9D6C2E6D31EF53C8D5169990A53881E0E0C72D80F7EE3C8EDCE1DD340F0771` |
| `apexforge/tooling/debug_visualstudio.py` | `9B4F05CA0F6AC9048903516062FFFFEE247E93660013652703BCC204410593FF` |
| `docs/p13/P13_10_SEMANTIC_IDE_VIEWS_TDP_PREVIEW.md` | `35C1D4B30E11C7A56170924793195140FA11676A946469E7F98C1C06CEDCF1A9` |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |
| `docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md` | `F7B62CD5C668E7B5D14FD02BD3003CBC91652B1F714D27CE880A13C75CDFACE4` |
| `docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md` | `8975BE6FBD6E3DDA654A98FBC9C11FAE5A996D47F91C63AA58064114C48DBF3F` |
| `docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md` | `8F849F358D85B1B6FDD5E9433BE0C13EA57FF822BF8D794FDCA246612A01F163` |
| `docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md` | `1C8235AF503E484D04EBF106104B18BA54FB4AB5704C58FFD992FF1BB652E3B1` |
| `docs/p13/P13_7_CLI_DEBUGGER.md` | `24795ACDA46D654224543924C1E602D81C3E37460CB6C4AA0CF72B9E023FDCDA` |
| `docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md` | `4FC56C5F0FE16EEDF9B977BC0F242643BDE7C4A6E9E96D7E0951A0D9F1659F0E` |
| `docs/p13/P13_9_VISUAL_STUDIO_DEBUGGER_INTEGRATION_FOUNDATION.md` | `869B1E66CE5316796DC0F8417FFF4B8E7D47E0F3939FF5201B6F10DF90DF91BA` |

These are file-byte hashes, not semantic identities. Twenty-seven incoming hashes are preserved. The one justified exception is the owning CLI module:

| Repaired candidate | Incoming hash | Final hash |
| --- | --- | --- |
| `apexforge/tooling/debug_cli.py` | `84B2091E8A7FC294FEF24F786834D3E0BA806EEB7B03C438EDE64E1ABB168101` | `0B0631BA8240F051EA123F0E11B45E8D07437BD79A3A044CCD470749B0CCCDE6` |

Only two new files are created: `apexforge/p13_11_cross_target_debugger_validation_test.py` and this report. Final candidate count: 30. No new production projection module is introduced.

## Validation axes and matrix

“Cross-target” has two distinct axes:

1. **Execution/evidence target:** canonical/managed retained evidence versus the frozen bounded native retained profile.
2. **Presentation target:** direct P13 substrate, CLI, DAP, Visual Studio command client, portable semantic views.

Each matrix uses the same immutable inspection/history/correlation/evidence anchors. Independent client instances preserve separate observational replay cursors. Test helpers only decode existing presentation records and normalize JSON tuples/lists; they do not evaluate semantics, infer relationships or calculate expected state.

| Execution/evidence target | Direct substrate | CLI | DAP | VS command client | Portable views |
| --- | --- | --- | --- | --- | --- |
| Real managed retained | PASS | PASS | PASS | PASS | PASS |
| Real bounded native retained | PASS | PASS for supported retained domains | PASS for supported retained domains | PASS for supported retained domains | PASS for supported retained domains |

The VS column is an in-process command-client foundation, not installed Visual Studio debugger registration. DAP is an injected retained projection, not a live transport or arbitrary launch loader. No VS Code/VS UI is registered.

## Fixtures and common-domain qualification

The suite reuses controlled P13.6/P13.7 fixtures. Managed and bounded native inputs are independently constructed/executed twice by the existing canonical execution, retention and native owners during fixture setup. Client/view operations run afterward under semantic/host/mutation guards.

Managed retained evidence includes source-produced AIR, compiler metadata/TAM, real runtime trace families, directive observation, final state/result, authority observations and retained provenance. Its validated P13.4 source/AIR correlation is supplied to all clients.

Native retained evidence includes the actual bounded native result, generated-C mapping, build receipt, artifact image identity, result-input associations, retained result association and native-evidence trace family. The real generated content is checked through the existing correlation/retention validators. No artifact loader, machine-address mapper or native-admission expansion is added.

A separate experiment uses one already-admitted P12.7 common-domain native program through the existing canonical and managed owners and its retained native output. The existing P12.7 managed_projection/native_projection functions establish matching success/final typed state. The native profile admission check is reused. This is only the frozen integer/constant-assignment common domain; it is not equivalence for arbitrary AIR, managed/native targets, operating systems or toolchains. No independent .NET semantic executor is claimed.

## Identity parity

```text
SAME_SEMANTIC_OBJECT -> SAME_CANONICAL_REFERENCE
CLIENT_HANDLE != CANONICAL_IDENTITY
SAME_SEMANTIC_OBJECT does not require identical UI text
```

Across applicable surfaces, the tests verify supplied session/execution reference IDs, AIR and routing fingerprints, directive/plan/result records, state keys/types, source/native mapping associations, evidence node/producer identities, provenance scopes, trace-family identity and replay evidence references.

Some fields are presented through an evidence reference rather than repeated directly in every scope. A displayed evidence node ID is resolved against the same supplied graph to verify its full producer/program/scope/execution association. CLI/DAP/VS evidence rows retain the same node ID, kind, producer ID and payload. Portable view references retain the exact existing EvidenceReference canonical form while their local node IDs have per-view prefixes.

DAP variable references, VS projection handles, connection sequences and view-local IDs are presentation handles. They are not AIR/program/state/authority/provenance identities. DAP determinism compares payload bodies, excluding connection-local envelope sequences.

## State/type/availability parity

For both managed and native evidence, one supplied inspection snapshot is compared with CLI state rows, DAP read-only variables, VS State and the portable State document. Canonical key ordering and declared types match. Visible values match the existing inspection field representation. Unavailable values remain explicit; no zero/default state is fabricated.

CLI encodes typed InspectionField records; DAP/VS/view variables display deterministic JSON text for an available value and bracketed unavailable/redacted status. Validation decodes those formats rather than demanding identical terminal/UI strings. Native producer-specific representation is retained within its target; cross-target semantic equality uses the existing qualified P12.7 projection rather than a new debugger conversion engine.

## Redaction parity and owning-module repair

The sentinel `PRIVATE_CLI_SENTINEL_73` is tested across CLI state/inspect/authority/evidence/provenance/causal/replay/compare/error output, DAP variables/lookup/custom responses/source errors, VS projections and errors, portable document JSON and TDP preview serialization. Withheld producer result/state fingerprints remain withheld.

The stronger fixture supplies a visible inspection snapshot alongside fully redacted retained evidence. Direct producer objects remain unchanged, but every presentation must honor the enclosing evidence redaction boundary.

**CROSS_CLIENT_REDACTION_GAP:** the initial matrix found that CLI state rendered visible snapshot values while DAP, VS and views suppressed them. The owning `debug_cli.py` state renderer now accepts the existing client-wide redaction flag and emits explicit redacted observation/capture records. State identity and declared type are preserved. No producer value, evidence fingerprint or semantic result is rewritten.

The existing P13.7 focused suite passes 32/32 after the final repair. P13.11 validates both ordinary per-state redaction and whole-evidence redaction with a visible snapshot.

## Program authority versus debugger control authority

Direct inspection authority records match CLI observed-program-authority rows and the DAP/VS authority scope. Portable program/debugger authority documents remain separate.

Observed authority does not grant debugger control. CLI explicitly reports the separate debug-session-owner check; the portable debugger authority document says authorization was not evaluated by the view. No authority evaluator is invoked to generate inspection evidence. Capabilities remain separate from execution-scoped authorization.

## Correlation and ambiguity parity

Every correlation surface agrees with the same P13.4 chain on:

- SOURCE availability and all supported candidate canonical forms;
- AIR canonical operation reference;
- GENERATED_NATIVE_REGION availability/canonical regions;
- MACHINE_ADDRESS=unsupported.

Managed source-produced evidence has available source/AIR and native not_applicable. Hand-built native AIR preserves source unavailable while its generated-native region is available. This does not establish ordinary compiler-source -> native full-chain admission.

An existing ambiguous mapping fixture supplies two legitimate source candidates for one operation. CLI, DAP, VS and portable documents preserve ambiguous status and both candidates. No client selects one for display convenience. Synthetic/unmapped origin handling remains the supplied correlation owner's contract; no nearest-source or fabricated mapping is introduced.

There is no instruction pointer, PDB, machine-code position or CPU-step claim.

## Evidence/provenance/artifact associations

For managed and native graphs, CLI evidence list, DAP custom evidence, VS Evidence and portable evidence nodes resolve to the exact supplied canonical node/reference/payload. Provenance LINK rows and translated view edges match the exact supplied relationship kind, endpoints and support reference.

Tests verify real managed provenance scope and plan/result/trace/compiler-TAM associations. Native checks additionally validate the retained artifact image fingerprint, build-receipt fingerprint, native mapping fingerprint and result-association fingerprint against actual retention carriers.

The native execution receipt field remains unsupported because no distinct execution receipt was retained. Existing build-receipt/result-input associations are not renamed into a fabricated receipt. Partial chains remain valid.

## Attribution and recorded causal evidence

All evidence/provenance/causal surfaces preserve EVIDENCE_BEFORE_ATTRIBUTION=True and actor attribution not_inferred. Portable views carry corresponding limitations; TDP composition serializes evidence-before-attribution explicitly.

Real retained causal records expose recorded alternatives/selected paths, not debugger-selected paths. Canonical selected_path graph relations remain supported by the actual selection record. A controlled owner-executed fixture with two decisions sharing path identities preserves ambiguous occurrence association across all clients; no selected_path edge is invented.

```text
CAUSAL_EVIDENCE != ROOT_CAUSE
RECORDED_CAUSAL_SELECTION != DEBUGGER_INFERRED_CAUSATION
STATE_DIFFERENCE != CAUSAL_PROOF
PROVENANCE != HUMAN_ATTRIBUTION
DIVERGENCE != CAUSAL_ATTRIBUTION
```

## Replay parity

Direct P13.6 replay is compared with CLI replay, custom DAP replay requests, VS Replay commands and portable timeline records for both targets.

Ordering domain, first/last record, seek position, boundary behavior and evidence node IDs agree. Managed evidence uses retained stream order; native evidence uses the selected native-evidence family order. The portable timeline retains the same domain/record references, not a universal timestamp timeline.

REPLAY_POSITION != LIVE_EXECUTION_POSITION. Navigation is observational and does not execute or recreate evidence. Projection disconnect does not delete retained history.

## Comparison parity

The suite compares managed state/result/trace/provenance divergence, actual recorded causal-selection divergence and volatile-only observational differences. CLI/DAP/VS domain records match the direct P13.6 DomainComparison records. Portable comparison nodes preserve those same records and separate volatile-difference rows.

VOLATILE_ONLY_DIVERGENCE is demonstrated through the supported semantic comparison domain set. An all-domain summary also contains unavailable/not_applicable domains, so it need not produce that optional global volatile classification; it still reports the PID difference separately and no semantic divergence. No client turns it into semantic failure.

Causal explanations and actor attribution remain not_inferred. Comparison does not determine root cause or what a result should have been.

## Step-plan parity

For semantic, source and native-correlation planning, direct P13.4 plan_next targets match CLI TARGET rows, DAP custom planning, VS named planning commands and portable planning nodes.

All surfaces retain STEP_PLAN_ONLY=True/planningOnly and the same target ordering/correlation reference. Named VS commands encode their mode rather than accepting an extra mode argument. No execution advancement, live step, breakpoint installation or machine instruction is claimed.

## Capability and standard-request honesty

CLI status/capabilities, DAP initialize, VS connect, portable overview and TDP composition agree on current limits:

```text
LIVE_RUNTIME_PAUSE_RESUME=False
BREAKPOINT_EXECUTION=False
RAW_MACHINE_STEP=False
EXTERNAL_LIVE_TRANSPORT=False
```

Standard DAP continue/pause/next/stepIn/stepOut/terminate/setVariable/setExpression return errors without effect events. setBreakpoints returns an unverified planning-only source-location correlation, consistent with VS Plan Breakpoints. Structural request support never implies runtime effects.

No client-level --force, arbitrary shell, expression interpreter, process attach or unsafe launcher appears.

## Session/lifecycle parity and owning-module repair

Constructors reject mismatched session/execution and correlation/inspection provision. Bound DAP/VS adapters reject replaced evidence/owner anchors. Portable views reject mismatched session labels.

A strengthened retained CLI probe found a second real owning-client defect:

**CROSS_CLIENT_SESSION_BINDING_GAP:** an already-bound retained CLI could replace its history with another execution's evidence and render it under the original session context. The owning CLI now checks its provisioned session/execution references before commands, verifies history/inspection consistency and rejects wrong owner/history/correlation associations with a fixed client_target_rebound code.

The check is structural reference integrity, not a new authority engine. Independent comparison input is deliberately not the target execution. Volatile metadata and local cursors can change without changing canonical target references.

CREATED sessions may acquire their first execution only through the same existing session owner; once established, that target stays fixed. ACTIVE -> CLOSING -> CLOSED transitions preserve references and the existing owner remains responsible for request dispositions.

After closure, live inspection rejects and a CLI structural control request reports the actual rejected disposition with CONTROL_EFFECT_OBSERVED=False. A successful CLI transport/command status does not mean request acceptance. Retained evidence/replay remain readable under the retention contract. VS/DAP disconnect closes local projections and leaves producer history unchanged.

## Security parity and semantic passivity

Controlled checks reject arbitrary expression text, host commands, arbitrary executable fields, PID attach, source paths, mutation and authority bypass across applicable clients. Known-state lookup is read-only. Source access is authorized-reference resolution, not arbitrary filesystem access.

Static AST/import inspection covers debug_cli, debug_dap, debug_visualstudio and debug_views: no direct AIR/RuntimeEngine execution, native dispatch/build, independent AuthorityEngine evaluation, eval/exec or host/process execution ownership exists. Dynamic guards cover matrix construction/queries and compare session/history/correlation canonical forms before/after. Fake control owners consume no execution requests.

The test harness executes through existing canonical/retention/native owners only to produce controlled fixtures. No new production debugger layer or second executor is created.

## Determinism matrix

Two independently produced managed inputs/results and two independently produced bounded-native inputs/results are projected independently. Tests compare direct inspection, correlation, evidence graph, replay history, comparison canonical forms, CLI responses, DAP response bodies, VS Projection results and portable serialization.

Connection-local envelope sequences and IDE-local handles remain outside semantic identity. Native equality is conditioned on the tested host/toolchain/profile; no cross-machine binary equivalence is asserted.

## TDP preview and resource fidelity

The TDP preview references the actual semantic overview and current capabilities, not fabricated operational health. Live Monitor labels retained observations and denies continuous telemetry. Transvergent Analytics, FAME, Varenic, Policy/Throttle and Simulation remain deferred; Incidents & Containment provide observation references without classification/containment; Medic provides evidence references without remediation.

No operational telemetry, defensive engine, policy execution or registration is added.

The resource test supplies existing ResourceOwnership plus explicit binding/cleanup evidence and verifies exact resource class, owner/purpose/trigger/lifetime/cleanup-boundary records, binding and missing cleanup observation in the portable view. No other client is claimed to expose that full resource document. MSC remains an analytical resource-continuity lens.

## Focused validation and failure ledger

Final commands/results:

```text
python -X utf8 -B apexforge/p13_7_cli_debugger_test.py
32/32 PASS

python -X utf8 -B apexforge/p13_11_cross_target_debugger_validation_test.py
28/28 PASS
```

The 28 focused cases consolidate managed/native state/type/availability, identities, authority distinction, mapped/unmapped/ambiguous correlation, graph/receipt/artifact/result associations, causal selection/ambiguity, attribution, replay/domain/seek/boundaries, comparison/volatility, three planning modes, capability truth, standard DAP honesty, redaction/error/hash parity, security, binding/closure, independent determinism, TDP/resource fidelity, P12.7 common-domain relationship and static/dynamic passivity.

Observed failures were classified before edits:

| Classification | Observation and correction |
| --- | --- |
| CROSS_CLIENT_REDACTION_GAP | Two initial matrix failures exposed CLI whole-evidence state leakage. Corrected only owning CLI presentation, retaining producer evidence. |
| TEST_FIXTURE_DEFECT | Initial 28-test matrix also had three assertion failures and two errors from VS named-mode arguments, tuple/list comparison, CLI transport versus rejected disposition, optional volatile-only classification with unsupported domains, and a test helper argument-name collision. Corrected the new fixture expectations/invocation to the existing contracts. |
| CROSS_CLIENT_SESSION_BINDING_GAP | Strengthened targeted retained CLI test failed 1/1 before repair; retained history rebinding was accepted. Added owning-client target-reference integrity checks. |
| IMPLEMENTATION_DEFECT | First binding guard rejected existing CREATED -> ATTACHED behavior, producing one failure in the owning 32-test suite. Preserved first-owner attachment and reran the unchanged owner suite successfully. |

Initial complete matrix: 28 tests, five failures and two errors. The first redaction repair yielded a 28/28 pass after fixture corrections; the stronger binding gate then exposed the additional real defect. Final owner and full matrix reruns both pass against the final repair. No old assertion was weakened, no frozen test was edited and no canonical semantic contract was changed.

## Aggregate P13 regression

```text
python -X utf8 -B -m unittest discover -s apexforge -p p13_*_test.py
255/255 PASS
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
| P13.9 VS command client | 23 | PASS |
| P13.10 semantic views | 31 | PASS |
| P13.11 cross-target matrix | 28 | PASS |

All 227 predecessor tests and all 28 new cases pass after the final production correction. No P12 production file changed; full P12 closure was not run.

## Existing IDE coexistence and remaining gaps

Frozen P10/P11 IDE files remain unchanged. No new IDE acceptance run was needed. P13.9's known CRLF/LF historical byte-hash environmental qualification is preserved; no frozen file was normalized or repaired.

| Boundary | Status |
| --- | --- |
| Installed VS Code/Visual Studio registration and safe persisted target provisioning | Remain unimplemented; this validation covers actual in-process clients only |
| Ordinary compiler-source -> native full-chain admission | Unestablished; managed source mapping and hand-built native mapping validated separately |
| Machine addresses/PDB/instruction stepping | Unsupported/unimplemented |
| Universal semantic stack / universal ordering / distinct native execution receipt | Unavailable or unsupported according to existing carriers |
| Cross-machine binary equality | Not claimed; existing tested toolchain qualification retained |
| Operational TDP providers | Deferred domain-platform work; preview truth only |
| DEFER_TO_P13_12 | Human closure review and any later explicitly authorized freeze action; not started here |

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_CROSS_CLIENT_SECOND_EXECUTOR=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_VSCODE_DEBUGGER_REGISTERED=False
P13_VISUAL_STUDIO_DEBUGGER_REGISTERED=False
P13_TDP_OPERATIONAL_PLATFORM_IMPLEMENTED=False
P13_CROSS_TARGET_MANAGED_VALIDATION=PASS
P13_CROSS_TARGET_NATIVE_VALIDATION=PASS
P13_CROSS_CLIENT_IDENTITY=PASS
P13_CROSS_CLIENT_STATE=PASS
P13_CROSS_CLIENT_REDACTION_PARITY=PASS
P13_CROSS_CLIENT_AUTHORITY_SEPARATION=PASS
P13_CROSS_CLIENT_CORRELATION=PASS
P13_CROSS_CLIENT_AMBIGUITY_PRESERVED=True
P13_CROSS_CLIENT_EVIDENCE=PASS
P13_CROSS_CLIENT_PROVENANCE=PASS
P13_CROSS_CLIENT_CAUSAL_EVIDENCE=PASS
P13_CROSS_CLIENT_ATTRIBUTION_BOUNDARY=PASS
P13_CROSS_CLIENT_REPLAY=PASS
P13_CROSS_CLIENT_COMPARISON=PASS
P13_CROSS_CLIENT_STEP_PLANNING=PASS
P13_CROSS_CLIENT_CAPABILITY_TRUTH=PASS
P13_CROSS_CLIENT_SESSION_BINDING=PASS
P13_CROSS_CLIENT_SECURITY_BOUNDARY=PASS
P13_CROSS_CLIENT_DETERMINISM=PASS
P13_TDP_PREVIEW_CAPABILITY_TRUTH=PASS
P13_RESOURCE_CONTINUITY_FIDELITY=PASS
P13_CROSS_MACHINE_BINARY_EQUIVALENCE_CLAIM=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_11_READY_FOR_CLOSURE_REVIEW=True
```

PASS refers to the demonstrated supported execution/evidence/presentation matrix, not universal target compatibility or installed IDE functionality.

## Exact final Git status

```text
?? apexforge/p13_10_semantic_ide_views_tdp_preview_test.py
?? apexforge/p13_11_cross_target_debugger_validation_test.py
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
?? docs/p13/P13_11_CROSS_TARGET_DEBUGGER_VALIDATION.md
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

Final preservation: branch, HEAD and peeled freeze unchanged; 27 incoming hashes preserved and the one classified CLI repair recorded above; all tracked P12 and frozen IDE files unchanged; empty index; no generated residue. No staging, commit, tag or push. No P13.12, P14 or operational TDP work. Stop at P13.11.

