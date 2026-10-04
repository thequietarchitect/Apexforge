# P13.12 — Integrated Debugger Closure and Freeze Readiness

Status: **ready for owner review**, conditional on the final validation and preservation results recorded below. This is a closure-readiness evidence artifact, not a declaration of milestone completion, freeze, canonization or release.

## Authorization and baseline

The owner's current roadmap state authorizes P13.12 only. P13.1 defines P13.12 as closure/freeze-readiness review with freeze/release authority reserved to the owner. This slice therefore adds only this document, reviews existing evidence and reruns existing validation. It does not stage, commit, tag or push, implement deferred capabilities, or start P14. The current roadmap supersedes the stale P11.4A stage in AGENTS.md; its stable engineering/security/owner-authority policies remain binding.

Branch: `p13-1-debugger-architecture`.
HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.
Incoming candidate count: **30**. Tracked and staged diffs were empty. The P13.11 final CLI repair hash matches the current incoming file. No new production code, test, registry, transport or extension is introduced.

## Incoming file-byte inventory

SHA-256 below records candidate file bytes, not canonical semantic identity. All 30 incoming hashes must remain unchanged; this document is the sole new candidate and has no self-referential hash requirement.

| Incoming file | SHA-256 |
| --- | --- |
| `apexforge/p13_10_semantic_ide_views_tdp_preview_test.py` | `48CFE891070E8152D1E53E23F4596E0743E87E7342CC394E8DC3EA3B83C26B07` |
| `apexforge/p13_11_cross_target_debugger_validation_test.py` | `A61858337AE4368E5F90658F06E11F7B687D98C95B8DF3BD6DDD8A415519E62A` |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/p13_6_deterministic_replay_trace_comparison_test.py` | `5770090A9040527ABA26EADF5FF46457B8FE8211389244AF5066F6CBFE9BCF9B` |
| `apexforge/p13_7_cli_debugger_test.py` | `BB8C014C44288A05450477D33BEA57AC236EF06987BE758AC6D9BBBDF56154A8` |
| `apexforge/p13_8_dap_vscode_debugger_test.py` | `2189C9401B669855127D8EE3F2EB4AA5DC5DAE4D73691E870D4CCB23FEF70ED5` |
| `apexforge/p13_9_visual_studio_debugger_integration_test.py` | `829A299882F29CCD7674C0E4DE4888E21ED9B0BED68C07C54B8F87A1E8F071A4` |
| `apexforge/tooling/debug_cli.py` | `0B0631BA8240F051EA123F0E11B45E8D07437BD79A3A044CCD470749B0CCCDE6` |
| `apexforge/tooling/debug_correlation.py` | `981E6FEC0A2B4CEA1F044D565805506EC75D0C1E6150313076867254EFB9339B` |
| `apexforge/tooling/debug_dap.py` | `67C70E700A0BF059CFBC28053A60B4AA4374DD809B6182FF8741BF990B6E49D4` |
| `apexforge/tooling/debug_evidence.py` | `ED2A67EF80B8765EDB810137C86EB3E569B7EA022EADC9878ABEF9E9B478FC72` |
| `apexforge/tooling/debug_inspection.py` | `409099E910F5D5313DF5EA4949DBB6A1BAFFB6CA037554A22D373651B152D466` |
| `apexforge/tooling/debug_replay.py` | `44E06F35955279E0C5A7D0048050AB74D2D36512C3E88C834687C98DEDEFF8C5` |
| `apexforge/tooling/debug_session.py` | `22C530D30A9E0D87276DA1CBB39D38ADA8C34B78A00F3DD1216F1BEF3AEBE774` |
| `apexforge/tooling/debug_views.py` | `BF9D6C2E6D31EF53C8D5169990A53881E0E0C72D80F7EE3C8EDCE1DD340F0771` |
| `apexforge/tooling/debug_visualstudio.py` | `9B4F05CA0F6AC9048903516062FFFFEE247E93660013652703BCC204410593FF` |
| `docs/p13/P13_10_SEMANTIC_IDE_VIEWS_TDP_PREVIEW.md` | `35C1D4B30E11C7A56170924793195140FA11676A946469E7F98C1C06CEDCF1A9` |
| `docs/p13/P13_11_CROSS_TARGET_DEBUGGER_VALIDATION.md` | `4F0D10090F9EE66CC85418701217EBCC444F2F7833D6D183E063B909E51901BB` |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |
| `docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md` | `F7B62CD5C668E7B5D14FD02BD3003CBC91652B1F714D27CE880A13C75CDFACE4` |
| `docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md` | `8975BE6FBD6E3DDA654A98FBC9C11FAE5A996D47F91C63AA58064114C48DBF3F` |
| `docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md` | `8F849F358D85B1B6FDD5E9433BE0C13EA57FF822BF8D794FDCA246612A01F163` |
| `docs/p13/P13_6_DETERMINISTIC_REPLAY_TRACE_COMPARISON.md` | `1C8235AF503E484D04EBF106104B18BA54FB4AB5704C58FFD992FF1BB652E3B1` |
| `docs/p13/P13_7_CLI_DEBUGGER.md` | `24795ACDA46D654224543924C1E602D81C3E37460CB6C4AA0CF72B9E023FDCDA` |
| `docs/p13/P13_8_DAP_VSCODE_DEBUGGER_FOUNDATION.md` | `4FC56C5F0FE16EEDF9B977BC0F242643BDE7C4A6E9E96D7E0951A0D9F1659F0E` |
| `docs/p13/P13_9_VISUAL_STUDIO_DEBUGGER_INTEGRATION_FOUNDATION.md` | `869B1E66CE5316796DC0F8417FFF4B8E7D47E0F3939FF5201B6F10DF90DF91BA` |

## Integrated architecture and evidence coverage

`Canonical execution/evidence -> P13 observation/session/inspection/correlation/evidence/replay tooling -> CLI/DAP/VS command client/portable views`.

Canonical AIR remains the sole semantic authority. Debugger references, transport handles, view-local IDs, cursor positions and terminal/DAP responses remain projections. A capability is not authorization; an accepted request is not an observed runtime effect.

| Section | Implemented and validated contract | Retained limitation |
| --- | --- | --- |
| P13.1 | Observation architecture, identity separation, event/version/capability contracts | Architecture alone implements no runtime capability |
| P13.2 | Immutable session/execution references, scoped authorization adapter, lifecycle/control request ownership and sequencing | No runtime pause/resume integration |
| P13.3 | Immutable typed state, directive/principal/program-authority/plan/result inspection, availability/redaction | No independent state, authority or routing evaluator; retained semantic stack not universally captured |
| P13.4 | Validated source/AIR/generated-C references and pure semantic/source/native-correlation target planning | No branch prediction, runtime stepping, CPU addresses/PDB mapping or ordinary compiler-source/native full admission |
| P13.5 | Concrete compiler TAM TraceRecord/TraceMap and retained TAMEvidence, trace/provenance graph and explicit scope/plan/result/execution bindings | Partial evidence remains partial; ambiguous causal occurrence remains ambiguous |
| P13.6 | Retained observation navigation, structural comparison and reconstruction descriptors | Replay is not execution; reconstruction is input/profile/toolchain-conditioned |
| P13.7 | Isolated CLI dispatcher/shell over supplied P13 objects | No host execution, top-level frozen CLI registration or external live transport |
| P13.8 | Bounded DAP framing/lifecycle and read-only/custom projection | Adapter-only; no safe external retained-target provisioning/VS Code registration |
| P13.9 | Visual Studio in-process command client reusing DAP | No installed VS debugger, independent debug engine or arbitrary process attachment |
| P13.10 | Portable immutable semantic views, resource custody, preview-only TDP composition | No host UI registration or operational TDP subsystem |
| P13.11 | Managed/native evidence × direct/CLI/DAP/VS/views consistency matrix | Tested supported domain, not universal compatibility |

Compiler TAM traceability does not replace governance-level Concordat TAM-v3. Tap Check remains user-controlled, diagnostic-only, read-only and non-activating.

## Cross-target, security and determinism acceptance

Two axes remain separate: execution/evidence target (managed retained or frozen bounded native retained) and presentation target (substrate, CLI, DAP, VS command client, portable views). The 28-case matrix tests real retained fixtures through every applicable surface and preserves canonical identity while allowing different UI text.

Acceptance covers typed state/key/order/availability, whole-evidence and per-value redaction, program versus debugger-control authority, exact evidence/producer/scope/plan/result associations, mapping ambiguity, recorded causal alternatives/selection, replay ordering domains, comparison divergence domains, pure step targets, capability honesty, session binding and retained lifetime after disconnect. Static AST/import and dynamic guards reject a second executor, host/eval/PID/path access, authority bypass and producer mutation.

No producer fingerprints withheld by redaction are exposed through a client. Missing evidence is not negative evidence. State difference is not causal proof; recorded selected path is not debugger-inferred causation; provenance and divergence do not establish human/actor attribution. `EVIDENCE_BEFORE_ATTRIBUTION=True` remains binding across all views.

Native equivalence remains limited to the established P12.7 common domain and frozen `apexforge.native.win-x64.i64-literal-state-set/v1` profile. Exact artifacts are qualified by tested toolchain conditions; no cross-machine binary equivalence is claimed. Native evidence uses actual build receipts and retained result-input associations; no separate execution receipt is invented.

## Resource and lifecycle custody

`Retained Resource => Known Owner + Known Purpose + Known Lifetime + Valid Binding`.

Session-local records, replay indexes and projection handles are operational/ephemeral resources under their existing owner and lifetime. Canonical retained evidence/provenance references retain existing CER/SHR custody where applicable. Closing CLI/DAP/VS projections invalidates local handles and does not imply evidence deletion or execution termination. Closed sessions do not gain live control through retained replay.

MSC remains a resource-continuity analytical lens, with no semantic-engine dependency. TDP preview keeps SENTINEL, TDP, CONTAINMENT, MEDIC and VERIFICATION roles distinct, and reports deferred telemetry/FAME/Varenic/containment/Medic/policy-throttle providers honestly.

## Final validation

Focused existing integration gate:

```text
python -X utf8 -B apexforge/p13_11_cross_target_debugger_validation_test.py
28/28 PASS
```

Final aggregate:

```text
python -X utf8 -B -m unittest discover -s apexforge -p p13_*_test.py
255/255 PASS (124.953 seconds)
```

| Section | Test count |
| --- | ---: |
| P13.2 | 21 |
| P13.3 | 21 |
| P13.4 | 21 |
| P13.5 | 23 |
| P13.6 | 25 |
| P13.7 | 32 |
| P13.8 | 30 |
| P13.9 | 23 |
| P13.10 | 31 |
| P13.11 | 28 |
| Total | 255 |

There is no production behavior change requiring another test file. P13.11 is the focused integrated gate; the aggregate reruns every owning P13 section, including the 32-case CLI section. No frozen/shared module changed, so the full P12 closure and unrelated frozen IDE acceptance stacks were not rerun.

## Failure ledger and Patch Matrix

Current-run `ENVIRONMENTAL_CONSTRAINT`: restricted PowerShell could not resolve `python`, before collection. Retried the unchanged focused command through the environment's explicit approval mechanism; 28 tests passed. No execution policy, authority, assertion, source or frozen file was changed. Initial repository discovery also named absent optional .agents/.codex directories; this was an inspection invocation issue, corrected by searching existing repository paths.

P13.11 historical repairs remain explicit: whole-evidence CLI state redaction (`CROSS_CLIENT_REDACTION_GAP`) and retained CLI execution rebinding (`CROSS_CLIENT_SESSION_BINDING_GAP`), both owned by debug_cli.py and already included in this incoming baseline. The first binding guard's CREATED-session rejection was classified `IMPLEMENTATION_DEFECT` and repaired before this baseline. Existing fixture defects and all prior failures remain documented in P13.11; this slice does not rewrite their history.

Historical P13.5 full P11 TAM-B owner-freeze invocation remains `TEST_INVOCATION_DEFECT`, `HISTORICAL_P11_OWNER_FREEZE_CHECK_NOT_APPLICABLE_TO_P12_8_DERIVED_WORKSPACE`; the five applicable TAM behavioral groups passed. The transient Windows trace-provenance PermissionError remains `ENVIRONMENTAL_CONSTRAINT`, `TRANSIENT_WINDOWS_FILE_ACCESS_CONDITION_CAUSE_UNCONFIRMED`, `ISOLATED_UNCHANGED_RERUN=PASS`.

Frozen P10 Visual Studio byte-hash coexistence failures remain a CRLF/LF `ENVIRONMENTAL_CONSTRAINT` as documented in P13.9, not a PASS. No checkout normalization or frozen audit weakening was performed.

Patch Matrix disposition for this slice: **no implementation patch required**. Owning-section and cross-section regression cells are exercised by the existing focused matrix and aggregate; dependency selection is limited to current P13 because no frozen/shared contract changed. Preservation is audited below. This readiness decision is bounded by recorded exclusions, not a claim that deferred capabilities are implemented.

## Deferred capabilities and owner decisions

| Remaining gap | Disposition |
| --- | --- |
| Safe persistent authorized target provisioning and installed IDE registration | Deferred; arbitrary paths/executables are not an acceptable substitute |
| Live transport/control, pause/resume, breakpoint execution and raw machine stepping | Unimplemented; no success/effect claim |
| Universal semantic stack/workflow planning, machine-address/PDB mapping | Unavailable/unsupported under current evidence |
| Ordinary compiler-source -> native full-chain admission | Unestablished; separate source-managed and hand-built-native fixtures preserve the limit |
| Perfect replay/universal reconstruction/cross-machine binary identity | Not claimed |
| Operational TDP and domain policy/remediation/containment/telemetry | Deferred domain-platform scope; preview composition only |
| Actual freeze, staging, commit, tag, release or push | Requires owner authorization; not performed here |

Historical documents retain stage-local facts (for example DAP not yet implemented at P13.5). Current truth is the integrated inventory: bounded DAP projection is present, installed VS Code/VS registration is absent. No earlier evidence file is retroactively rewritten.

## Evidence-supported review markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_ROLE=OBSERVATIONAL_CLIENT
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_P10_VSCODE_REOPENED=False
P13_P10_VISUAL_STUDIO_REOPENED=False
P13_P11_VISUAL_STUDIO_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_CROSS_CLIENT_SECOND_EXECUTOR=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_VSCODE_DEBUGGER_REGISTERED=False
P13_VISUAL_STUDIO_DEBUGGER_REGISTERED=False
P13_TDP_UI_PREVIEW_MODEL=True
P13_TDP_OPERATIONAL_PLATFORM_IMPLEMENTED=False
P13_CROSS_MACHINE_BINARY_EQUIVALENCE_CLAIM=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_INTEGRATED_DEBUGGER_REVIEW=PASS
P13_12_READY_FOR_REVIEW=True
P13_FREEZE_PERFORMED=False
```

PASS applies to the tested bounded observation/client contracts and preservation gate. The repository owner retains the final closure/freeze decision.

## Exact final Git status and preservation

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
?? docs/p13/P13_12_INTEGRATED_DEBUGGER_CLOSURE_FREEZE_READINESS.md
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

Final candidate count: **31** (30 preserved incoming files plus this report). All 30 incoming file-byte hashes are preserved. Branch/HEAD/peeled freeze remain unchanged; tracked and staged diffs are empty; frozen P10/P11/P12 files remain unchanged in Git. Generated binary/cache scans and the build-directory listing are empty.. No stage, commit, tag, push, P14, registration or operational TDP work is performed.

