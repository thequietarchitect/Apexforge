# P13.6 — Deterministic Replay & Trace Comparison

Review candidate; repository owner and human reviewer retain final authority. This report does not freeze or release the milestone.

## Frozen baseline and incoming custody

Branch: `p13-1-debugger-architecture`. HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`. The initial tracked diff and staged diff were empty, with exactly 13 incoming untracked P13 candidates and no generated residue.

Before capturing this baseline, only the requested P13.5 documentation classification was normalized: the transient Windows native-file rewrite PermissionError is `ENVIRONMENTAL_CONSTRAINT`, `TRANSIENT_WINDOWS_FILE_ACCESS_CONDITION_CAUSE_UNCONFIRMED`, `ISOLATED_UNCHANGED_RERUN=PASS`. The historical P11 TAM-B full invocation remains `TEST_INVOCATION_DEFECT`, `HISTORICAL_P11_OWNER_FREEZE_CHECK_NOT_APPLICABLE_TO_P12_8_DERIVED_WORKSPACE`; its previously recorded five applicable behavioral assertion groups remain separate evidence. No production code or test changed for that correction.

The following SHA-256 baseline was captured after the correction and must remain unchanged:

| Incoming candidate | SHA-256 |
| --- | --- |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/tooling/debug_correlation.py` | `981E6FEC0A2B4CEA1F044D565805506EC75D0C1E6150313076867254EFB9339B` |
| `apexforge/tooling/debug_evidence.py` | `ED2A67EF80B8765EDB810137C86EB3E569B7EA022EADC9878ABEF9E9B478FC72` |
| `apexforge/tooling/debug_inspection.py` | `409099E910F5D5313DF5EA4949DBB6A1BAFFB6CA037554A22D373651B152D466` |
| `apexforge/tooling/debug_session.py` | `22C530D30A9E0D87276DA1CBB39D38ADA8C34B78A00F3DD1216F1BEF3AEBE774` |
| `docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md` | `D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8` |
| `docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md` | `ABEB987A4C828AD1E25292EB9830B9ACEDF5F6D9B97E76B1794BA71E717D21A8` |
| `docs/p13/P13_3_SEMANTIC_STATE_CONTEXT_AUTHORITY_INSPECTION.md` | `F7B62CD5C668E7B5D14FD02BD3003CBC91652B1F714D27CE880A13C75CDFACE4` |
| `docs/p13/P13_4_SOURCE_AIR_NATIVE_CORRELATION_STEP_PLANNING.md` | `8975BE6FBD6E3DDA654A98FBC9C11FAE5A996D47F91C63AA58064114C48DBF3F` |
| `docs/p13/P13_5_TAM_CAUSAL_TRACE_PROVENANCE_EVIDENCE_INSPECTION.md` | `8F849F358D85B1B6FDD5E9433BE0C13EA57FF822BF8D794FDCA246612A01F163` |

## Implementation and reused carriers

Exactly three P13.6 files are added: `tooling/debug_replay.py`, its focused test, and this report. Earlier tooling and frozen P12 modules are unchanged.

The module consumes P13.5 immutable EvidenceView/EvidenceNode graphs, retained family/interleaving indexes and validated session/execution binding; P13.3 InspectionSnapshot, typed state and explicit availability; P13.2 session references; and the immutable P12 ManagedContextIdentity and frozen native profile identifier. P13.4 operation relationships are consumed through already-validated evidence graph mapping edges. It does not replace trace retention, canonical result projection, provenance, source mapping, authority or execution ownership.

The inspected P12.7 evidence qualifies bounded equivalence and does not establish three independent semantic engines. P12.8 reproducibility establishes exact native image/receipt identity only under tested compatible toolchain/options/profile conditions.

## Replay taxonomy and records

`TRACE_REPLAY != RE-EXECUTION`
`VISUAL_REPLAY != RUNTIME_CONTROL`
`RECONSTRUCTION_PLAN != EXECUTION`
`TRACE_COMPARISON != SEMANTIC_AUTHORITY`
`DIVERGENCE != CAUSAL_ATTRIBUTION`

ReplayHistory captures an already-authorized EvidenceView and optional immutable inspection. It validates execution association and, when supplied and visible, the retained result binding. It holds no live runtime object or mutation callback. ReplayRecord contains a deterministic projection sequence, declared ordering domain, logical key, existing immutable evidence node/reference, and inspection fingerprint or explicit availability. No producer trace record is created.

ReplayTimeline indexes supplied records only. ReplayCursor supports first, last, previous, next, and bounded sequence seek; endpoints clamp, invalid sequences and stale timeline fingerprints reject. A reference seek returns all matching candidates when ambiguous and unavailable when absent. Broad program identity is not mistaken for a unique operation occurrence. Cursor position is observational navigation, not canonical semantic identity.

The serialization schema is `apexforge.debug-replay/v1`, a tooling value-model schema rather than a new transport protocol or DAP implementation. Canonical forms have explicit schema/kind and deterministic JSON serialization.

## Ordering and availability

All seven ordering domains remain named and distinct: SEMANTIC_ORDER, TRACE_FAMILY_ORDER, TRACE_STREAM_ORDER, DEBUGGER_EVENT_ORDER, CAUSAL_ORDER, SOURCE_ORDER and NATIVE_CORRELATION_ORDER.

This stage implements only supplied retained stream/interleaving order and selected trace-family order. It preserves producer parent indexes and family ordinals; the projection's contiguous replay sequence does not replace those logical keys. Other domains return UNSUPPORTED_MODE because a sufficient ordered observation contract is not supplied. A causal-selection trace family can be replayed in family order without claiming causal graph order. Native retained evidence has no invented stream interleaving: its supplied native family is replayable, while stream replay is unavailable.

Availability distinguishes COMPLETE_RETAINED, PARTIAL, UNAVAILABLE, UNSUPPORTED_MODE, AMBIGUOUS_REFERENCE and REDACTED. COMPLETE_RETAINED means complete for the supplied selected projection, not universal execution coverage. Partial compiler/TAM evidence remains partial. Missing slots/events are never filled. Missing evidence is not negative evidence. Partial trace comparison conservatively reports INSUFFICIENT_EVIDENCE rather than whole-history equality.

## Reconstruction descriptor and experiment

ReconstructionDescriptor records only supplied canonical identities and contract conditions. It includes AIR, routing, entry, profile, retained input scope, source-map fingerprint, expected retained output/receipt/artifact/family identities, and captured context identities where present.

For managed execution, validated ManagedContextIdentity supplies state/policy/configuration fingerprints and plan association. Fingerprints alone do not contain the original state and authority material: status remains INSUFFICIENT_INPUT_EVIDENCE. This descriptor does not falsely certify that an arbitrary historical run can be rerun.

For native execution, the exact supplied build-receipt JSON must hash to the retained receipt association and match AIR/routing/entry/profile/generated-C bindings. Captured toolchain hashes/options produce TOOLCHAIN_CONDITIONED status, requiring original canonical AIR and compatible captured tools. An absent receipt is insufficient; incompatible profile is UNSUPPORTED_PROFILE. Nothing is built or executed by descriptor construction. A build receipt is not renamed or invented as a separate execution receipt.

The focused harness independently constructs equivalent canonical input twice and invokes the existing managed retained execution owner twice. Their supplied outputs compare equal in selected semantic/evidence domains. It also independently builds and executes two supported hand-built native fixtures through existing owners under the frozen profile. Their state/result, native artifact, actual build receipt, mapping, provenance and selected native-family comparisons are identical; image bytes and receipt JSON are equal. Execution occurs in the test harness before replay inspection, never in the replay module.

Not all executions are perfectly replayable. Reconstruction depends on original captured inputs and compatible contracts/toolchains; volatile OS behavior and side effects outside canonical evidence may differ. Cross-machine binary identity and universal environmental reconstruction are unproven.

## Comparison domains and divergence

ComparisonResult contains left/right history identities, canonically ordered selected domain results, per-domain first supported difference, explicit trace ordering, supporting evidence references where available, and names of separate volatile differences. It has no global causal verdict.

Supported domains: input identity, AIR, state, directive observation, authority evidence, recorded causal evidence, result, trace, mapping, provenance, native artifact and build receipt. Each domain reports IDENTICAL, its corresponding structural divergence, INSUFFICIENT_EVIDENCE, REDACTED_COMPARISON_UNAVAILABLE or NOT_APPLICABLE. Native artifact is not applicable to the canonical managed profile; missing native evidence on other profiles remains unavailable.

State comparison reuses canonical key ordering, declared type, availability and supplied typed values. Boolean/integer differences are preserved; the debugger does not coerce mismatches away. Result status/fingerprint comes from P13.3's existing projection; retained association is compared separately as provenance. Trace comparison preserves selected logical keys and supplied payload/operation relationships; it separates scope-bound authority record identity from the actual recorded check content. Binding/provenance identity remains compared in its own domain rather than discarded.

Recorded selected paths can differ and produce CAUSAL_EVIDENCE_DIVERGENCE. Decision-occurrence ambiguity remains inherited from evidence; neither matching traces nor state differences select a path or prove a cause. Mapping/provenance comparison uses producer identities and scope associations, not similar display names. Provenance differences do not establish person/external-actor attribution.

`DIVERGENCE_CLASSIFICATION != CAUSAL_EXPLANATION`
`CAUSAL_EVIDENCE_DIFFERENCE != ROOT_CAUSE`
`PROVENANCE_DIVERGENCE != ACTOR_ATTRIBUTION`
`RECORDED_CAUSAL_SELECTION != DEBUGGER_INFERRED_CAUSATION`
`PROVENANCE != HUMAN_ATTRIBUTION`

First difference is an index in the selected structural comparison projection, not a universal semantic or causal first event. Stable producer fields are compared without normalization. Native identity is compared only under its frozen contractual qualification.

## Volatility, identity and redaction

Timestamps, PID, handles, memory addresses, elapsed duration, working set, temporary roots and transport identity are excluded from stable replay observation content. Session/execution occurrence IDs remain legitimate binding/history references; comparison reports their differing occurrences separately rather than treating them as semantic input changes. Equivalent content in distinct authorized occurrences can therefore compare semantically equal while the bound histories remain distinct.

VOLATILE_ONLY_DIVERGENCE is reported only when all selected stable domains are identical or not applicable and observational fields differ. It is not semantic failure. A deterministic comparison artifact still identifies its compared bound histories; no claim is made that different local session identities are the same session.

P13.5 producer hashes and graph evidence remain unchanged. Full redaction reuses its slot/reference view and suppresses snapshot identity/payload, producer fingerprints, reconstruction inputs and supporting raw references in client-facing comparison. Redacted comparison is unavailable rather than secret-hash equality. A partially redacted state snapshot with a visible evidence graph rejects as an unsafe mixed boundary. No unredaction or sensitive-value policy engine is added.

## Session, resource and security boundaries

Initial capture requires the original valid active session/execution association. LIVE_SESSION_REPLAY revalidates that binding during construction/navigation/reference lookup and rejects cross-session or closed-session access. RETAINED_EVIDENCE_REPLAY navigates already-authorized immutable retained observations after closure, without granting attachment or control authority. This is a structural foundation, not new authentication or a bypass of external access policy.

Retained Resource => Known Owner + Known Purpose + Known Lifetime + Valid Binding.

Replay indexes/cursors are session/application-local operational navigation (IRR or DHF according to caller retention); retained EvidenceView references preserve existing producer CER/SHR custody where applicable. The caller owns the replay index for the purpose of authorized inspection and must release it at its declared navigation/session lifetime. Closing a live session does not delete canonical retained evidence. No persistence store, automatic lifetime policy or new resource authority is introduced.

The module has no implicit filesystem/process queries, arbitrary artifact opening, process launching, artifact execution, producer writes, provenance rewrite, authority evaluation, state mutation or control requests. MSC remains an analytical resource-continuity lens only.

## Semantic passivity and focused validation

Command: `python -X utf8 -B apexforge/p13_6_deterministic_replay_trace_comparison_test.py`.

Result: **25/25 PASS**. Coverage consolidates deterministic record/order/navigation/reference ambiguity, producer immutability, partial/missing evidence, unsupported ordering, reconstruction input insufficiency and receipt validation, real managed/native equality, real state/type/result/trace/mapping/provenance/causal differences, recorded authority without reevaluation, deterministic first divergence, volatile separation, full/mixed redaction, closed/live/cross-execution binding and retained replay.

Static AST checks reject imports/calls to AIR/runtime/native execution, authority evaluation, compiler invocation, process launch and filesystem/mutation APIs. Guarded dynamic replay/capture/navigation/descriptor/comparison tests run against already-produced fixtures while those execution/mutation owners are trapped. Original retained results, inspection snapshots and evidence canonical forms remain unchanged.

No validation failure occurred in this P13.6 focused/regression run; no assertion or old contract was changed to obtain a pass.

The first final preservation-audit invocation failed before executing any check: Windows inline-command quoting removed the hash-list string literals, producing a Python SyntaxError. Classification: `TEST_INVOCATION_DEFECT`. The corrected single-literal invocation passed all preservation checks unchanged; no production code, test or baseline file was edited for this failure.

## Final predecessor validation

Executed against the exact passing implementation using Python UTF-8 and `-B`:

| Suite | Final result |
| --- | --- |
| P13.5 TAM/causal/trace/provenance inspection | 23/23 PASS |
| P13.4 source/AIR/native correlation and step planning | 21/21 PASS |
| P13.3 semantic state/authority inspection | 21/21 PASS |
| P13.2 session/control foundation | 21/21 PASS |
| P12.6-6 trace/provenance reference | 12/12 PASS |
| P12.6-8 controlled trace integration | 12/12 PASS |
| Selected P12.8-6 ReconstructionTests | 3/3 PASS |

P12.8-6 selection: `test_fresh_process_clean_root_reconstruction`, `test_fresh_metadata_source_mapping_and_trace_order`, and `test_rejection_classification_deterministic_no_issuance_or_fallback`. The fresh-process check compares independent clean build roots/processes, AIR/routing/mapping/native image/receipt/retention identities and cleanup under captured toolchain conditions. The additional 1/64/256 load-point matrix is not rerun because P13.6 adds no execution/load/profile behavior; independent retained owner runs and clean-process reconstruction exercise the materially reused identity contracts. The full P12 closure stack is not run.

Total: 25 focused tests and 113 selected predecessor tests, all PASS. Historical TAM-B full-owner freeze validation is not reinvoked as acceptance for this P12.8-derived workspace. Its P13.5 historical invocation defect and separate behavioral PASS remain documented unchanged after the requested environmental classification correction.

## Remaining gaps and explicit non-claims

| Classification | Scope |
| --- | --- |
| RECONSTRUCTION_EVIDENCE_GAP | Managed input fingerprints do not supply original state/policy material; native reconstruction requires original AIR and compatible tools. |
| REPLAY_MODEL_GAP | Semantic, causal, source, debugger-event and native-correlation ordered replay require additional supplied observation contracts. |
| TRACE_COMPARISON_GAP | Partial retained trace cannot certify full-history equality; absent stream order stays unavailable. |
| DEFER_TO_P13_7 | Client presentation/CLI and caller retention policy integration. |
| DEFER_TO_P13_8_PLUS | DAP/IDE/external-client access integration and broader retained-store policies. |

No discovered gap is classified as a frozen semantic defect. Ordinary compiler-source to native full-chain admission remains unestablished. No machine-address mapping, runtime stepping, breakpoint execution, replay execution, native profile expansion, causal inference, human attribution, universal replay or cross-machine binary claim is made.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_EVIDENCE_EXECUTES_AIR=False
P13_EVIDENCE_EXECUTES_RUNTIME=False
P13_EVIDENCE_DISPATCHES_NATIVE=False
P13_REPLAY_EXECUTES_AIR=False
P13_REPLAY_EXECUTES_RUNTIME=False
P13_REPLAY_DISPATCHES_NATIVE=False
P13_REPLAY_AUTHORITY_ENGINE=False
P13_REPLAY_MODULE_EXECUTES_RECONSTRUCTION=False
P13_REPLAY_FABRICATES_MISSING_EVENTS=False
P13_UNIVERSAL_DETERMINISTIC_REPLAY_CLAIM=False
P13_VOLATILE_DIVERGENCE_SEMANTIC_FAILURE=False
P13_CROSS_MACHINE_BINARY_REPLAY_PROVEN=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_DAP_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_VISUAL_REPLAY=PASS
P13_REPLAY_ORDERING=PASS
P13_RECONSTRUCTION_DESCRIPTOR=PASS
P13_STATE_COMPARISON=PASS
P13_TRACE_COMPARISON=PASS
P13_CAUSAL_EVIDENCE_COMPARISON=PASS
P13_PROVENANCE_COMPARISON=PASS
P13_NATIVE_EVIDENCE_COMPARISON=PASS
P13_VOLATILE_SEPARATION=PASS
P13_REDACTION_REPLAY_BOUNDARY=PASS
P13_RETAINED_EVIDENCE_REPLAY=PASS
P13_REPLAY_SEMANTICALLY_PASSIVE=True
P13_6_READY_FOR_REVIEW=True
```

## Preservation and exact Git status

Final audit: branch/HEAD/peeled freeze unchanged, all 13 incoming hashes preserved after normalization, all tracked files (including all P12 files) unchanged, index empty, exactly 16 untracked P13 candidates, build directory empty and no generated cache/binary artifacts. No stage, commit, tag, push, P13.7, CLI debugger, DAP, VS Code debugger, Visual Studio debugger or TDP UI work.

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/p13_3_semantic_state_authority_inspection_test.py
?? apexforge/p13_4_source_air_native_correlation_step_planning_test.py
?? apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py
?? apexforge/p13_6_deterministic_replay_trace_comparison_test.py
?? apexforge/tooling/debug_correlation.py
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
```
