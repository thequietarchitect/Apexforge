# P13.7 — ApexForge CLI Debugger

Review candidate. The repository owner and human reviewer retain final authority. No freeze, release or canonization is declared.

## Baseline and custody

Branch: `p13-1-debugger-architecture`.

HEAD and peeled `afp-p12.8-freeze`: `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`.

Before implementation, all 16 incoming candidates were untracked, the staged and tracked diffs were empty, build was empty and no generated cache/binary residue existed. The following SHA-256 hashes were captured before writing P13.7 files; they were reconfirmed after the server interruption, before file creation resumed.

| Incoming file | SHA-256 |
| --- | --- |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | `87CC9B7D699F78A6E585B32C0C51DE941483CD40676CDF51A19266A96BDACBDA` |
| `apexforge/p13_3_semantic_state_authority_inspection_test.py` | `4EF2B94D7225FC13D8B2F1FF0AC2DA4C44B475D0DCE2433749C2A141BF7DCB5B` |
| `apexforge/p13_4_source_air_native_correlation_step_planning_test.py` | `074F86FB26083386425A6A7B7CA51C5D1A9EAB6ADA32BEC41C22EF61A1E927A6` |
| `apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py` | `B93972DD1DD7EEA6DAB8158B695504B434CBCDAC7653636DFDB5B6EB4AF8CACE` |
| `apexforge/p13_6_deterministic_replay_trace_comparison_test.py` | `5770090A9040527ABA26EADF5FF46457B8FE8211389244AF5066F6CBFE9BCF9B` |
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

Only three files are added: `apexforge/tooling/debug_cli.py`, `apexforge/p13_7_cli_debugger_test.py` and this report. No earlier P13 or tracked P12 file changes.

## Existing CLI conventions and integration decision

Inspected `apexforge/apexforge_cli.py`, `tooling/cli.py`, and the P10-T1 CLI smoke test. The existing entry point delegates to a thin argparse adapter, customizes parser errors, accepts injected stdin/stdout/stderr, returns stable process codes and retains compilation/project loading under existing owners.

P13.7 follows argparse and stream injection, with success `0` and usage/unavailable-client-contract error `2`. It does not import the frozen CLI's broad execution adapters merely to obtain constants. Those two conventional numeric statuses are documented locally. Producer semantic failures are displayed as supplied inspection/evidence, not converted to command parse failure.

The frozen top-level command registry has no retained debugger-object loading or external session-transport seam. Registration would require that extra integration design. P13.7 therefore supplies an isolated debugger application/dispatcher, minimal shell and module entry point. `apexforge_cli.py` and `tooling/cli.py` remain unchanged. No external live transport, persistence loader, network service or IPC is invented.

From the repository root, the isolated help entry point was verified with the existing two import roots:

```powershell
$env:PYTHONPATH='.;apexforge'
python -X utf8 -B -m tooling.debug_cli help
```

This standalone entry point starts without supplied evidence: help/status work; evidence-dependent commands return explicit unavailability. Authorized embedding supplies the actual objects:

```python
from tooling.debug_cli import DebuggerCLI, main

app = DebuggerCLI(history=authorized_history, comparison=other_authorized_history)
main(("state",), application=app)
main(("--interactive",), application=app)
```

These variables represent already-produced, owner-authorized P13 models. The client does not load or execute artifacts to obtain them.

## Client architecture and modes

Canonical execution/evidence -> existing P13 tooling -> DebuggerCLI -> terminal presentation.

DebuggerCLI receives P13.6 ReplayHistory, optional comparison history, P13.3 inspection, P13.4 CorrelationIndex/ObservedPosition/KnownObservationOrder and optional P13.2 DebugSessionOwner. It validates supplied associations before rendering. It does not create a mapping, state, provenance, authority, comparison or replay engine.

Retained/offline mode navigates already-authorized immutable retained observations without requiring an active session. An owner can be supplied at initial capture to validate standalone inspection/correlation. Such retained views may survive closure under the existing retention contract. Retained mode cannot submit control requests or invoke active step planning.

Live-session mode requires an in-process P13.2 owner. It displays the owner's current lifecycle, execution and granted capabilities; observation commands revalidate active session, inspection, evidence and correlation binding. Step planning uses that active binding. Status/help/quit remain usable when closed, and structural request rejection still goes through the session owner. No client transport exists.

The embedding owner supplies identity allocation, authorization/loading and retention lifetime. Model construction and displayed fingerprints are not authentication or bearer tokens.

## Command grammar

| Command | Behavior |
| --- | --- |
| `help` | Deterministic grammar and explicit limitations. |
| `status`, `session` | Client/protocol, mode, supplied lifecycle/execution, capabilities, unsupported live pause/resume and absent external transport. |
| `capabilities` | Sorted actual client features and separately sorted granted P13.2 capabilities; capability is not authorization. |
| `inspect` | Supplied immutable inspection fields; no semantic recomputation. |
| `state` | Canonically ordered keys, declared types, typed observed values and availability/redaction. |
| `directive`, `result` | Supplied observation fields only. |
| `authority` | Observed program authority explicitly separate from debugger-control authorization. |
| `correlate current` or `correlate <operation-id>` | Existing P13.4 chain lookup; current requires a supplied observed position. |
| `evidence list` | Supplied graph nodes in its deterministic order. |
| `evidence show/predecessors/successors <id>` | Existing P13.5 graph query methods. |
| `provenance [<id>]` | All supplied graph links or links incident on the known node; partial chain remains partial. |
| `causal` | Existing decision/path and retained causal-selection nodes; occurrence ambiguity remains explicit. |
| `replay first/previous/next/last`, `replay seek <sequence>` | Existing P13.6 timeline/cursor navigation. |
| `compare summary/state/trace/causal/provenance` | Existing P13.6 comparison, selected actual domains, no global verdict. |
| `plan-step semantic/source/native-correlation` | Active-session P13.4 planned observation target only. |
| `request-stop/continue/terminate <sequence>` | Actual command names are `request-stop`, `request-continue`, `request-terminate`; submit one immutable P13.2 request. |
| `quit` | Exit command loop; no execution termination, session reopening or evidence deletion. |

Argument counts and choices are explicit. Parser errors never echo untrusted arguments. Request sequences are caller-supplied nonnegative session-local integers, leaving duplicate/stale/pending validation under P13.2. There are no bare `step` or `continue` aliases, breakpoint commands, workflow-step commands, state-write APIs, shell escapes, eval/exec or authority bypass flags.

The minimal shell reuses the same dispatcher, quotes/tokenizes with shlex, prints a fixed prompt, survives malformed commands, and exits on EOF or quit. It is available through `--interactive` and injected stream APIs. No arbitrary host command execution is possible.

## Presentation model and determinism

Commands return deliberate primitive rows to one renderer, then a Response containing stdout/stderr/status/quit. Data projection is separate from presentation. Human output uses `LABEL=<quoted value>` lines with deterministic JSON escaping for values; it is not a new machine-readable protocol endpoint or semantic evidence format. No additional JSON-output mode is introduced.

Capabilities are sorted, state keeps its canonical key order, correlation candidates retain P13.4 canonical ordering and ambiguity, graph nodes/edges keep P13.5 deterministic order, comparison domains keep P13.6 order, and replay uses its supplied logical ordering projection. No timestamps, PID, memory addresses or OS probes are added to presentation. Existing stable identities remain meaningful; independently supplied identical bound observations produce identical output.

Terminal control characters and embedded newlines are escaped, preventing producer strings from changing terminal layout. Producer repr is never used. Application repr includes only mode.

## Inspection and correlation

Inspection prints supplied directive/principal/authority/plan/result/provenance/correlation/diagnostic/stack fields and existing state entries. Unavailable values remain explicit; declared types and boolean/integer distinctions are preserved.

Authority output labels OBSERVED_PROGRAM_AUTHORITY and DEBUG_SESSION_CONTROL_AUTHORIZATION separately, and states OBSERVED_AUTHORITY_GRANTS_DEBUGGER_CONTROL=false. Reading authority evidence does not evaluate policy or grant control. Structural request authorization is delegated only to DebugSessionOwner.

Correlation shows SOURCE, AIR and GENERATED_NATIVE_REGION separately, including available, unavailable, not_applicable and ambiguous evidence. Every supplied source candidate is retained; no nearest span is substituted. MACHINE_ADDRESS=unsupported is explicit. Native region is not machine address. Hand-built AIR has unavailable source; ordinary compiler-source to native full-chain admission remains unestablished under the frozen native profile.

## Evidence, provenance and attribution

Evidence commands delegate to the existing supplied graph. Provenance displays only actual supported links and support-node references, not an inferred complete chain or ad hoc filesystem provenance. Causal display exposes only recorded selection/path evidence and states occurrence may be ambiguous.

Every evidence/provenance renderer identifies EVIDENCE_BEFORE_ATTRIBUTION=true and ACTOR_ATTRIBUTION=not_inferred. Temporal proximity, graph similarity, state difference or provenance association does not identify a human, organization or external actor. Recorded causal selection is not debugger-inferred causation. Missing evidence is not negative evidence.

Native inspection uses actual retained artifact/build-receipt/result associations; it invents no execution receipt and admits no broader native semantics.

## Replay and comparison

Replay calls build_replay and uses ReplayCursor directly. The selected projection is supplied in the application: retained trace stream by default, or a declared family order such as native-evidence. Unsupported order/unavailable timeline stays explicit. First/last/previous/next use P13.6 endpoint behavior; out-of-range seek is a contract error, and the old cursor remains unchanged. Output prints ordering domain, replay sequence, logical key and evidence reference, with RE_EXECUTION=false. It creates no new trace records.

Compare invokes compare_histories rather than implementing another algorithm. Summary selects its supported P13.6 domains, while state/trace/causal/provenance select individual domains. Insufficient/redacted/not-applicable domains remain explicit. Per-domain divergence and supporting references are rendered; volatility is listed separately. CAUSAL_EXPLANATION=not_inferred and ACTOR_ATTRIBUTION=not_inferred prevent a structural difference from becoming a root-cause or attribution verdict.

Native artifact/receipt equality remains qualified by the tested frozen toolchain conditions. The client claims no universal deterministic reconstruction, cross-machine binary identity, live replay or independent semantic authority.

## Step and control presentation

plan-step delegates to P13.4 plan_next over supplied observed position and resolved ordering evidence. Output identifies STEP_PLAN_ONLY=true and PLANNED_OBSERVATION_TARGET. A missing resolved order returns needs_runtime_observation; the CLI never predicts a branch. Native-correlation planning selects the generated region for an observed semantic operation, never a CPU instruction. No execution advancement occurs.

Request commands construct ControlRequest with current session/execution, action, sequence, lifecycle revision/state and the owner's authorization binding, then call owner.submit. Capability, authority, target, lifecycle, stale sequence, unsupported and pending checks remain in P13.2. The client does not call deliver or an execution-control callback.

A structurally accepted disposition is printed together with STRUCTURAL_REQUEST_ONLY=true, CONTROL_EFFECT_OBSERVED=false and RUNTIME_CONTROL_INTEGRATED=false. Rejected/authorization_denied/unsupported/stale/session_closed dispositions are displayed as actual owner results. Returning command success means a response was rendered; it does not mean the request was accepted or its effect occurred.

CONTROL_REQUEST_ACCEPTED != CONTROL_EFFECT_OBSERVED.
CLI_STEP != LIVE_EXECUTION_STEP.
CLI_REPLAY != RE_EXECUTION.
CLI_OUTPUT != AUTHORITY.

## Lifecycle, error, redaction and security boundaries

CREATED/ATTACHED/ACTIVE/CLOSING/CLOSED status is supplied by the owner, never reconstructed by the client. Live observation/step access is rejected after closure. Control goes through owner rejection. Previously captured retained evidence stays readable without reopening the closed session.

Errors distinguish missing/unknown/malformed command, missing supplied inspection/evidence/comparison, no active session, closed/inactive session, unavailable mapping/observed position/planning, and invalid binding/projection/request scope. Substrate exceptions are sanitized to debugger_contract_rejected, rather than exposing producer values or untrusted exception messages. These client errors return code 2 and stderr, not invented semantic failure. Supplied availability and request dispositions are normal stdout responses.

State entries honor P13.3 visible/redacted/unavailable values. When sensitive state or a redacted history is supplied, associated inspection/evidence/provenance/correlation renderers conservatively suppress unsafe payload/identity presentation. P13.6 redacted replay/comparison continues to supply safe slot references or REDACTED_COMPARISON_UNAVAILABLE. Errors never echo reference arguments. Producer hashes are not modified to create the view and never leak from a redacted view. The distinctive sensitive-string test checks both the literal and result/input hashes across all renderers/errors/repr.

The client does not execute AIR/runtime/native artifacts, reevaluate authority, select causal paths, invoke a compiler, read arbitrary paths, launch processes or use eval/exec. No --force/--unsafe/--ignore-authority exists. Serial embedding owns safe access and retention; this is not new authentication or a public network endpoint. Quitting releases navigation responsibility to the embedding owner, without changing producer custody.

## Focused validation and failure history

Final command: `python -X utf8 -B apexforge/p13_7_cli_debugger_test.py`.

Final result: **32/32 PASS**. Controlled fixtures reuse P13 owner paths and retained carriers: managed, bounded native, real divergent and causal comparison pairs, redacted sensitive string and closed-session evidence. AST checks and dynamic owner/filesystem/process traps verify semantic/host passivity; request tests separately allow established P13.2 authority evaluation and trap delivery. Fixtures execute only through existing owners before CLI consumption. Existing result/evidence/inspection canonical forms remain unchanged.

The tests consolidate help/capability/status/lifecycle, supplied state/type/unavailability/redaction, authority separation, real source/native/unmapped/ambiguous correlation, graph queries/links, replay/seek/bounds, existing comparison/divergence, step-only presentation, acceptance/denial/unsupported/duplicate/closed requests, malformed commands, safe shell behavior, terminal escaping, determinism and cross-session binding.

Observed issues are retained:

| Classification | Observation and resolution |
| --- | --- |
| ENVIRONMENTAL_CONSTRAINT | The workspace process helper initially failed during setup; read-only inspection continued using approved command execution. The server later restarted during file creation; state check confirmed no partial CLI file existed before resuming. |
| REDACTION_GAP | Review found numeric-only privacy fixtures insufficiently distinctive; added a sensitive-string renderer/error/hash test. No earlier tooling changed. |
| TEST_FIXTURE_DEFECT | First sensitive-string fixture omitted declared type, defaulted to int, and correctly failed APX-TYPE-011 during setUpClass (0 tests ran). Corrected only the fixture to established `state secret : string` syntax; compiler unchanged. |
| TEST_INVOCATION_DEFECT | First isolated module smoke test ran from apexforge without the repository import root and failed ModuleNotFoundError. Retried with both existing roots; help passed. No package or frozen CLI changed. |
| SESSION_BINDING_GAP | Review found live correlation needed per-command revalidation in addition to construction checks. Added the P13.4 validate_session call and a client-owner rebinding test, only in new P13.7 files. |

The initial 30-test run passed; the corrected sensitive-string suite passed 31; the final binding-strengthened suite passed 32. Assertions were not weakened, and no failing historical test was hidden or rewritten.

## Final predecessor regressions

After final focused PASS, reran the exact final implementation's relevant predecessors:

| Suite | Result |
| --- | --- |
| P13.6 deterministic replay/trace comparison | 25/25 PASS |
| P13.5 TAM/causal/trace/provenance inspection | 23/23 PASS |
| P13.4 correlation/step planning | 21/21 PASS |
| P13.3 semantic state/authority inspection | 21/21 PASS |
| P13.2 session/control foundation | 21/21 PASS |

Total: **111 predecessor tests PASS**, plus **32 focused tests PASS**. The isolated module help smoke check also passed with both import roots. No old/shared file changed; older P12 suites and the full closure stack were not rerun. All 16 incoming P13 hashes are preserved.

## Remaining gaps and exclusions

| Classification | Remaining scope |
| --- | --- |
| CLI_CONTRACT_GAP | Caller must supply already-authorized immutable models; no retained-file loader or external live transport. |
| DEFER_TO_P13_8 | Top-level registration/transport integration needs its own evidence-loading and client contract; DAP remains unimplemented. |
| DEFER_TO_P13_9_PLUS | Visual Studio, broader IDE/domain platform presentation and persistence/access-policy integration remain later work. |

Live pause/resume, runtime control integration, breakpoint execution, raw machine stepping, DAP, VS Code debugger, Visual Studio debugger and TDP UI remain absent. No P13.8 work is begun.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_CLI_EXECUTES_AIR=False
P13_CLI_EXECUTES_RUNTIME=False
P13_CLI_DISPATCHES_NATIVE=False
P13_CLI_AUTHORITY_ENGINE=False
P13_CLI_HOST_COMMAND_EXECUTION=False
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_BREAKPOINT_EXECUTION_IMPLEMENTED=False
P13_RAW_MACHINE_INSTRUCTION_STEPPING=False
P13_DAP_IMPLEMENTED=False
P13_VSCODE_DEBUGGER_IMPLEMENTED=False
P13_VISUAL_STUDIO_DEBUGGER_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_CLI_COMMAND_MODEL=PASS
P13_CLI_INSPECTION=PASS
P13_CLI_CORRELATION=PASS
P13_CLI_EVIDENCE_NAVIGATION=PASS
P13_CLI_PROVENANCE_VIEW=PASS
P13_CLI_REPLAY=PASS
P13_CLI_COMPARISON=PASS
P13_CLI_STEP_PLANNING=PASS
P13_CLI_CONTROL_REQUEST_PRESENTATION=PASS
P13_CLI_REDACTION_BOUNDARY=PASS
P13_CLI_ATTRIBUTION_BOUNDARY=PASS
P13_CLI_DETERMINISTIC_OUTPUT=PASS
P13_CLI_TOP_LEVEL_REGISTERED=False
P13_CLI_EXTERNAL_LIVE_TRANSPORT=False
P13_7_READY_FOR_REVIEW=True
```

## Preservation and exact Git status

Branch/HEAD/peeled freeze unchanged; all 16 incoming hashes preserved; all tracked files including P12 unchanged; index empty; exactly 19 untracked P13 candidates; build empty and no generated residue. No stage, commit, tag, push or later milestone work.

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/p13_3_semantic_state_authority_inspection_test.py
?? apexforge/p13_4_source_air_native_correlation_step_planning_test.py
?? apexforge/p13_5_tam_causal_trace_provenance_inspection_test.py
?? apexforge/p13_6_deterministic_replay_trace_comparison_test.py
?? apexforge/p13_7_cli_debugger_test.py
?? apexforge/tooling/debug_cli.py
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
?? docs/p13/P13_7_CLI_DEBUGGER.md
```

