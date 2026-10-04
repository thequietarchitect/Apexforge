# P13.2 — Debug Session, Authorization & Execution-Control Foundation

## Review result and preserved baseline

`CONTROL_CONTRACT_DEFINED_AND_VALIDATED` for the controlled, trusted in-process foundation described below. No runtime pause/resume, general termination integration, breakpoint execution, stepping, semantic-state inspection, DAP, IDE debugger, replay or TDP UI is implemented. This is a candidate for owner review, not a declaration of release, freeze or canonization. Stop after P13.2.

Incoming branch: `p13-1-debugger-architecture`. HEAD and peeled `afp-p12.8-freeze` both equal `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`. Initial status contained only the untracked P13.1 architecture document. Its SHA-256 was captured before implementation and rechecked after focused tests/regressions:

```text
D7EBA45B850A6F934586AFB30CE7BEDB7FD3184B8417637BDAA5C80F7CDB82E8
```

The P13.1 document remains byte-identical. Tracked tree and index are unchanged relative to P12.8. Initial and final inventories found no generated `.pyc`, `.exe`, `.dll`, `.obj`, or `.pdb` residue, or generated cache/bin/obj directories; test-owned native build contents were cleaned by unchanged predecessor tests. No P12 file was edited. No stage/commit/tag/push was performed.

AGENTS.md retains its historical P11.4A current-stage wording; the owner's explicit P13.2 instruction supplies this active slice while preserving its authority, determinism and engineering requirements.

## Inspected ownership patterns and implementation shape

Inspected canonical `authority/model.py` and `authority/engine.py`: Principal IDs, explicit AuthorityCheck/AuthorityGrant values and immutable, sorted, deny-by-default AuthorityEngine. The latter already implements principal/capability/resource matching, including its established explicit wildcard grants. Debugger capabilities do not create a competing permissions engine.

Inspected `tooling/narrative_session.py` for immutable exact-type session values, versioned schemas and stable failure codes. Its initialization/termination is bound to narrative execution/material; it is not a general AIR/native pause/resume seam and was not reused as control implementation. Inspected runtime diagnostics and existing cancellation/termination usages: LSP process cancellation and narrative termination do not authorize generic debugger process control. No safe existing general production control seam was identified or integrated.

Revisited P12 metadata association, execution-plan/routing references, trace retention/integration and resource-observability conventions. References carry existing uppercase fingerprints as immutable scalar bindings; this module does not import metadata association, retained result or plan implementation objects, invoke validators as a substitute for authority, or invent new canonical result/provenance carriers. Trusted embedding owners must supply validated execution identity. No automatic attachment to arbitrary constructed AIR or external processes occurs.

Exactly three new P13.2 files:

| File | Responsibility |
| --- | --- |
| `apexforge/tooling/debug_session.py` | Frozen session/execution/request/disposition/stop/event values, explicit session manager and designated execution-control-owner Protocol. |
| `apexforge/p13_2_debug_session_control_foundation_test.py` | Controlled fake-owner security, lifecycle, sequencing, determinism, custody and static separation tests. |
| This evidence document | Contract, current validation, preservation and limitations. |

No existing module, package export surface, grammar, compiler, AIR, runtime, native backend or CLI is modified. Consumers import the new module directly. The preferred one-module implementation shape is retained.

## Identity and execution references

`SessionReference` contains an explicit opaque session ID, canonical principal ID reference, nonnegative creation sequence and exact `apexforge.debug.protocol/v1`. The embedding session owner must allocate unique session IDs; this foundation is not a global ID registry or authentication service. Session canonical form and fingerprint address this local reference's contents, not canonical language semantics.

`ExecutionReference` separates its execution-local ID from stable AIR fingerprint, routing fingerprint, entry directive, profile and optional provenance fingerprint. `semantic_form()` excludes the execution-local ID; `canonical_form()`/fingerprint bind it as well. Repeated equal-input executions therefore share semantic binding contents while retaining distinct instance scopes. The authorization resource is `debug.execution:<execution-reference-fingerprint>`, including the instance identity. Profile is a caller-supplied owner contract label, not native admission. Optional absent provenance means unavailable, not validated provenance inferred by the debugger.

These are bindings to owner-supplied evidence, not proof that execution occurred, canonical object replacements or bearer authorization tokens. They contain no PID, timestamp, OS handle, memory address, client connection or UI state. Preserve:

```text
DEBUG_SESSION != EXECUTION
DEBUG_SESSION != PRINCIPAL
DEBUG_SESSION != PROCESS
DEBUG_CLIENT != AUTHORITY
AGENT != IDENTITY != ROLE != CAPABILITY != AUTHORITY
```

The session stores a principal ID extracted from an exact existing `Principal`; it does not embed arbitrary `Principal.authorities` implementation values or infer permissions from role/display names. Human/agent/client identity remains outside the session reference. Artifact/source/package/organization distinctions from P13.1 remain unchanged.

## Session lifecycle and attachment

The explicit mutable `DebugSessionOwner` owns immutable `DebugSession` snapshots. Snapshots include reference, canonically ordered requested/granted capabilities, ownership evidence, lifecycle, optional attached execution and monotonic lifecycle revision. Clients cannot update the manager by replacing a snapshot. One target execution and one designated control owner are bound at manager creation; there is no retarget/reopen API.

```text
CREATED -> ATTACHED -> ACTIVE -> CLOSING -> CLOSED
CREATED ---------------------> CLOSING -> CLOSED
           ATTACHED ---------> CLOSING -> CLOSED
```

Attach requires exact target match, granted ATTACH and canonical authority approval. Activation requires ATTACHED, granted OBSERVE and separate authority approval. Each lifecycle change produces a new snapshot with incremented revision and a local event. Begin-close is allowed from CREATED/ATTACHED/ACTIVE, invalidates the pending request immediately and emits closing evidence; finish-close requires CLOSING. CLOSED cannot reactivate or attach. There is no execution termination implied by session closure. Attached execution identity remains in retained closed evidence.

Illegal transitions and malformed shapes raise `SessionError` with stable debugger-domain codes. Lifecycle failures do not mutate the prior snapshot. Session manager APIs require serial trusted in-process use; thread safety, simultaneous clients and authenticated transport are not claimed.

## Capabilities and canonical authorization integration

Implemented capability vocabulary: `debug.attach`, `debug.observe`, `debug.request_stop`, `debug.request_continue`, `debug.request_terminate`. Requests/grants are exact enum tuples, duplicate-free and sorted lexically; granted must be a subset of requested. No stepping, breakpoint, state-write or replay capability is exposed.

Requested/granted capabilities declare allowed debugger surface, not permission. The thin adapter constructs an existing `AuthorityCheck` using principal ID, exact capability and execution-instance resource, then calls `AuthorityEngine.allows`. The canonical engine remains deny-by-default and retains its wildcard semantics. Permissions require explicit engine grants; no implicit observer-to-control or attach-to-terminate escalation exists. The authority engine is frozen and bound at manager creation; a policy change requires a separately constructed manager rather than a silent mutable policy swap.

The authorization binding fingerprint includes session reference, execution resource and canonical sorted grant fields. It is a stale/substitution binding, not a signature or secret. Copying that fingerprint does not confer rights: every valid action is evaluated through the canonical engine, and foreign session/target requests are rejected. External clients cannot directly create a manager with self-selected principal/grants; that is a trusted embedding responsibility. Authentication, caller identity proof, grant issuance/revocation service and remote transport security remain deferred.

## Immutable requests, sequencing and dispositions

`ControlRequest` contains session/execution references, one of the three control actions, nonnegative session-local sequence, expected lifecycle/state revision, authorization binding and an optional observational timestamp. No runtime handle, executable callback or state mutation is present. Exact type validation rejects bool-as-int sequences, negative sequences, unsupported actions and malformed fingerprints.

`submit()` checks session identity, closure, target, sequence, ACTIVE expected lifecycle/revision, authorization binding, granted capability, canonical authority, advertised control-owner support and absence of another pending request. Accepted requests occupy one pending slot; there is no growing request queue. Matching active-scope fresh attempts consume sequence numbers even when denied, so retrying the same denied attempt cannot later become accepted. Foreign target/session and stale lifecycle attempts do not poison the valid session's high-water mark. Gaps are allowed; fresh sequences must strictly exceed the high-water mark. Equality is duplicate, lower is stale. No wall-clock ordering is used.

`ControlDisposition` contains request fingerprint, structural status and stable reason. Status vocabulary: accepted, rejected, unsupported, stale, session_closed, execution_mismatch and authorization_denied. Constructing an accepted value or receiving acceptance causes no control-owner call and no canonical execution mutation. Request events and disposition events are separate debugger observations.

## Execution-control-owner boundary and stop evidence

```text
Client immutable request
    -> DebugSessionOwner.submit
    -> existing AuthorityEngine check
    -> structural acceptance / rejection
    -> explicit DebugSessionOwner.deliver for accepted pending request
    -> designated ExecutionControlOwner.consume
```

`ExecutionControlOwner` is a Protocol with explicit owner ID, exact execution binding, advertised supported control capabilities and `consume(request)`. P13.2 supplies no production implementation. The test fake records calls and can return controlled evidence; it does not pause/resume a runtime. Empty support is valid and yields unsupported dispositions.

`deliver()` requires the exact pending immutable request, ACTIVE session, unchanged target/session, authorization binding and a fresh canonical permission check. It checks designated owner's ID/execution/support again, consumes the pending slot before the callback and never automatically retries a thrown owner exception. A forged accepted disposition is not a pending authorization receipt and cannot dispatch. Owner exceptions propagate without conversion into canonical execution failure; delivery outcome may be unknown and cannot be assumed successful. The trusted designated owner alone may perform future target control.

`StopObservation` is independent evidence: execution reference, designated control-owner ID, monotonic stop sequence, explicit producer evidence reference and generic reason (`requested`, `diagnostic`, `boundary`, `execution_complete`). Only a separately returned owner observation yields `debug.stop.observe`. Wrong owner/target and repeated/regressed stop evidence are rejected. A stop request or delivered request does not prove stop/resume/termination. Evidence is trusted in-process producer binding, not independently authenticated runtime proof. Breakpoint and step-hit interpretation are absent.

## Event relationship and determinism

Local session/control event records use the P13.1 protocol identifier and dotted event conventions: `debug.session.start`, `.attach`, `.activate`, `.closing`, `.finish`; `debug.control.request`, `.accept`, `.reject`, `.deliver`; and `debug.stop.observe`. Explicit `start_event()` may emit the creation observation once before lifecycle activity; all emitted events share one monotonically increasing session sequence beginning at 0. The manager returns immutable events without retaining a growing stream. Their record forms preserve session/request/disposition/stop binding; they are not canonical AIR operations or execution ordering.

This is the lifecycle/control submodel, not a complete external wire codec or implementation of P13.1 semantic correlation/payload/provenance envelopes. No source/AIR/native operation evidence is fabricated. External payload negotiation, unknown-event handling and transport adaptation remain future work; incompatible SessionReference protocol identifiers fail shape validation now.

Schema-separated deterministic forms use UTF-8 JSON fingerprint preimages, exact scalar types and uppercase SHA-256. Equivalent records with the same local inputs produce identical session/execution/request/disposition/event forms; capability order is canonical. Different execution instances remain different authorization scopes even with equal stable AIR inputs. Request timestamps are omitted from canonical forms/fingerprints. Session IDs, instance IDs and sequences belong to local record identity and must not be included in stable AIR semantic fingerprints. PID, OS handles, working set, network/UI state and timings are absent. Display names are not authority bindings. No wire parser/persistence format or universal semantic fingerprint is claimed.

## Resource custody

Reuse P12.8 `ResourceOwnership`, `OwnershipEvidence`, `EvidenceStatus` and `ResourceClass`; there is no MSC runtime semantic engine. The manager's operational session snapshot is DHF-labeled with known principal/session owner, explicit purpose, creation trigger, lifetime and close/caller-release boundary. Snapshot construction verifies its custody owner binding against the session reference and requires known evidence fields.

The pending request slot is bounded to one IRR-style transient item bound to that session/execution; close clears it. Returned event/request/disposition evidence is caller-owned transient evidence until explicitly retained; the manager stores no event list, external resource, file, connection, process or artifact. Counters are fixed-count state (integer storage may grow with use; no universal byte ceiling). Immutable closed snapshots and reference values may outlive the manager under caller custody. Retained canonical provenance reference strings are CER/SHR continuity candidates under the existing owner, not ownership of underlying objects. Closing does not delete canonical evidence or dispatch/revoke native issuance.

`Known Owner + Known Purpose + Known Lifetime + Valid Binding` is enforced for managed session custody and documented for caller-held evidence. There is no persistent evidence store or automatic custody transfer. Tests validate known ownership fields, wrong session binding rejection, immutable snapshots and pending invalidation. P12 regressions validate their underlying resource and retained native custody contracts. Claims do not extend to remote clients, aggregate resource budgets or hostile concurrent namespace manipulation.

## Current tests and semantic separation

All commands below ran with CPython 3.11.9, `-X utf8 -B`, preserving bytecode-free execution. Focused tests passed before frozen regressions. No test was weakened, deleted, skipped or rewritten to hide a failure.

| Current command (from repository root) | Actual result |
| --- | --- |
| `python -X utf8 -B apexforge/p13_2_debug_session_control_foundation_test.py` | 21 methods PASS, 0.026 seconds. |
| `python -X utf8 -B apexforge/authority_consolidation_smoke_test.py` | Script PASS: canonical identities/exact grant, principal/capability/resource denial and transactional authorized/denied execution. |
| `python -X utf8 -B apexforge/p12_8_5_security_resource_lifetime_test.py` | 3 methods PASS, 9.982 seconds; three real controlled native lifecycles report missing-image rejection, ticket release and retained validity. |
| `python -X utf8 -B apexforge/p12_8_2_resource_observability_ownership_test.py` | 19 methods PASS, 5.757 seconds; real native passivity/no-fallback and cleanup included. |

Focused security evidence covers observer-only denial; missing capability; granted capability with wrong principal or execution-resource authority; wrong execution; stale/duplicate/regressed sequence; foreign-session requests and high-water isolation; closing/closed requests; immutable attachment; independent attach/observe permissions; accepted request not invoking owner; explicit at-most-once delivery; one pending slot; owner substitution; wrong/stale stop evidence; owner exception preservation; and known resource binding.

Determinism evidence covers fresh equivalent sessions, distinct equal-input execution occurrences, capability ordering, request/disposition/event forms and timestamps excluded from request fingerprints. Exact-shape tests reject unsupported protocol and invalid request values. Lifecycle tests exercise the full valid path and illegal attach/activate/close transitions. Static AST inspection restricts direct imports to standard library plus canonical authority and resource-observation types and forbids AIR runner/runtime/native dispatcher/expression evaluator/OS suspension calls.

The new module directly imports no RuntimeEngine, AIR runner or native dispatch owner, and invokes none. Existing `tooling` package initialization may load predecessor tooling definitions transitively; no initializer/export edit or semantic execution is added. Canonical authority permission checks are intentionally invoked; these are not AIR execution or debugger-owned semantic evaluation. Regression runtimes execute only in unchanged predecessor tests, not debug-session tooling.

P12.6 metadata/trace identity regressions were considered but not rerun: the new module does not reuse their implementation types or change their carriers. Scalar owner-supplied references preserve their fingerprints without reserializing a competing carrier. Authority and P12.8 resource/lifetime suites are materially relevant and were rerun. No P12 module changed, so no full P12 closure stack or historical full harness was launched or reported PASS.

## Failure classification and remaining gaps

No implementation, fixture or invocation failure occurred in this P13.2 test run. All rejection/error tests are expected negative contract cases, not regressions. The previously encountered sandbox command-runner setup failure is an `ENVIRONMENTAL_CONSTRAINT`; repository-only inspection/testing used approved escalation. Nothing in P12 was changed to obtain passes.

| Finding | Classification / disposition |
| --- | --- |
| General production pause/resume/termination seam absent | `CONTROL_OWNERSHIP_GAP`: owner contract validated, runtime integration deferred to a separately authorized control slice. No OS suspension/injection. |
| Authenticated remote callers, grant issuance/revocation and transport security absent | `AUTHORIZATION_GAP`, `DEFER_TO_P13_7_PLUS`; trusted in-process canonical grant evaluation is implemented, not external authentication. |
| Serial-only manager; no distributed ID allocation or concurrent request arbitration | `SESSION_LIFECYCLE_GAP`: explicit embedding responsibility; broader lifecycle/control work requires separate scope/tests. |
| Generic stop representation lacks real runtime stop producer | `OBSERVABILITY_GAP`; no accepted/delivered request is reported as stop without separately supplied designated-owner evidence. |
| Semantic state/stack inspection absent | `DEFER_TO_P13_3`; no state-write API or semantic view introduced. |
| Breakpoint/step execution and target safe-point semantics absent | `DEFER_TO_P13_4`; generic boundary reason does not implement semantic or machine stepping. |
| Complete external codec/capability negotiation absent | `PROTOCOL_VERSIONING_GAP`, `DEFER_TO_P13_7_PLUS`; exact v1 local reference validation and sorted capability values are present. |
| Persistent retention/transfer and external resource budgets absent | `RESOURCE_LIFECYCLE_GAP`: current bounded slot and returned immutable evidence custody validated; persistent store is outside this slice. |
| DAP/CLI debugger/IDE/replay/TDP integrations absent | `DEBUGGER_CONTRACT_GAP`, `DEFER_TO_P13_7_PLUS`; no implementation defect inferred from deliberate absence. |

The contract's stable debugger-domain errors/statuses preserve failures without normalizing mismatches. No new canonical diagnostic code or execution result is synthesized. P13.3 and all later work remain unstarted.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_DEBUG_SESSION_EXECUTES_AIR=False
P13_SESSION_EXECUTION_IDENTITY_SEPARATE=True
P13_CAPABILITY_AUTHORITY_SEPARATE=True
P13_CONTROL_REQUEST_RUNTIME_MUTATION=False
P13_STOP_REQUEST_OBSERVATION_SEPARATE=True
P13_BREAKPOINTS_IMPLEMENTED=False
P13_STEPPING_IMPLEMENTED=False
P13_DAP_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
P13_DEBUG_SESSION_MODEL=PASS
P13_SESSION_LIFECYCLE=PASS
P13_CONTROL_REQUEST_MODEL=PASS
P13_AUTHORIZATION_BOUNDARY=PASS
P13_CONTROL_OWNERSHIP_BOUNDARY=PASS
P13_CONTROL_REQUEST_ORDERING=PASS
P13_RESOURCE_CUSTODY=PASS
P13_RUNTIME_PAUSE_RESUME_IMPLEMENTED=False
P13_EXECUTION_CONTROL_RUNTIME_INTEGRATED=False
P13_2_READY_FOR_REVIEW=True
```

PASS values apply to tested trusted in-process boundaries, not implemented live runtime control, remote security or universal debugger coverage. Readiness is for human review only.

## Exact final Git status

```text
?? apexforge/p13_2_debug_session_control_foundation_test.py
?? apexforge/tooling/debug_session.py
?? docs/p13/P13_1_UNIFIED_DEBUGGER_ARCHITECTURE_OBSERVATION_CONTRACT.md
?? docs/p13/P13_2_DEBUG_SESSION_AUTHORIZATION_EXECUTION_CONTROL_FOUNDATION.md
```

Four P13 candidate files; nothing staged. HEAD remains `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`. No generated residue, P13.1/P12 modification, commit/tag/push, P13.3, breakpoint/stepping/DAP or TDP UI work.
