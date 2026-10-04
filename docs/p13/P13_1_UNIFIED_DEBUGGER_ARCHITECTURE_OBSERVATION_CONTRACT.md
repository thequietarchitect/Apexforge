# P13.1 — Unified Debugger Architecture & Observation Contract

## Status, baseline, and charter

Architecture proposal for human review; this document does not declare P13 released, frozen, or canonized. The single authorized artifact is this document. No implementation or test is introduced.

Verified incoming branch: `p13-1-debugger-architecture`. Incoming HEAD and peeled `afp-p12.8-freeze` both equal `c8b7b47f9377ed3da7e91fc46567a9bc572c57a4`. Incoming `git status --porcelain=v1` was empty. Tracked-file and directory discovery found no existing P13 slice artifacts. Thus incoming P12 files equal the frozen tree. The AGENTS.md current-stage text still names P11.4A; the owner's explicit P13.1 instruction supplies the active slice and preserves its engineering and authority restrictions.

P13 defines a shared debugger architecture/protocol, execution control, semantic inspection, source/AIR/native correlation, TAM/causal/provenance views, replay/comparison, CLI, VS Code, Visual Studio, semantic IDE views, cross-target validation, and eventual closure review. P13.1 specifies their common observation contract only. Subsequent milestones require their own authorization and focused validation.

## Frozen evidence and reuse decisions

Paths below are repository-relative. Existing canonical forms described as fingerprint preimages are not already public debugger wire formats.

| Foundation inspected | Reuse and established boundary |
| --- | --- |
| `apexforge/tooling/debug_metadata.py` | Reuse `SourceIdentity`, `AIRMetadataIdentity`, `OperationReference`, `MetadataSidecar`, and `MetadataAssociation`. Exact UTF-8 snapshot fingerprints, AIR transport fingerprints, structural locators, `af-meta-op:` IDs, explicit producer evidence, routing and owning-program bindings are available. Current operation locators cover state initialization and assignments; they are not universal instruction IDs. |
| `apexforge/tooling/source_air_mapping.py` | Reuse `SourceAIRMapping`, correspondence and structural lineage. Producer-recorded mapping is bounded to original unlinked/untransformed single-directive compiler AIR. `SOURCE_BACKED` and `UNMAPPED` remain distinct; synthetic/container/metadata lineage must not be displayed as physical source syntax. |
| `apexforge/native_backend/source_mapping.py` | Reuse `NativeSourceMapping`, `GeneratedRegion`, mapped artifact validation and profile associations. Emission records exact generated `program.c` spans for admitted operations. Hand-built AIR carries `UNMAPPED_SOURCE`. No universal machine-address/PDB mapping exists. |
| `apexforge/tooling/trace_retention.py` | Reuse `ProvenanceScope`, `RetainedRecord`, `TraceCollection`, `OperationAssociation`, `NativeResultAssociation` and `af-trace:` identities. Seven families retain supplied evidence. Exact operation association is currently supported for compiler TAM source-map-entry evidence, not inferred for runtime events. |
| `apexforge/tooling/trace_integration.py` | Reuse compiler/plan attachment, managed input/result identities, family collections, `StreamReference` interleaving, coverage declarations, native pre/post/result associations and retention limits. Execution remains delegated once to existing owners. `ObservationError.owner_result` preserves already-produced results. This is opt-in retained observation, not a live stop/control session. |
| `apexforge/native_backend/native_execution.py` | Preserve native admission, issuance tickets, receipts, source/image hashes, image locking through child exit, bounded output decoding and no semantic fallback. These remain backend responsibilities; debugger clients cannot issue or replace artifacts. |
| `apexforge/tooling/resource_observability.py` | Reuse immutable ownership/availability evidence, snapshots/deltas, lifecycle boundaries and volatility exclusion. Resource inventory requires authorized quiescent roots and rejects links/reparse traversal; it does not prove safety against arbitrary concurrent hostile namespace changes. |

Supporting inspected evidence: P12.6-9 integrated metadata/trace review; P12.7-3 bounded equivalence review; P12.8-7 closure review; focused test coverage in `apexforge/p12_6_3_metadata_identity_association_test.py`, `p12_6_4_source_native_mapping_test.py`, `p12_6_6_trace_provenance_reference_test.py`, `p12_6_8_controlled_trace_integration_test.py`, `p12_7_2_bounded_behavioral_equivalence_test.py`, `p12_8_2_resource_observability_ownership_test.py`, `p12_8_5_security_resource_lifetime_test.py`, and `p12_8_6_reproducibility_determinism_test.py` (all under `apexforge/`). Inspected assertions cover unmapped/stale source, unchanged actions/admission, retention failures preserving results, validation without re-execution, custody/release, and exclusion of volatile readings from identity. These are historical foundation evidence, not newly executed test results.

P12.7 establishes matching success and complete typed named final state for nine sampled common-domain fixtures repeated twice per path. Canonical and managed-retained paths share RuntimeEngine; this is not three independent semantic implementations or independent .NET AIR execution. The unchanged native profile is `apexforge.native.win-x64.i64-literal-state-set/v1`, with bounded I64 literal state/set execution and existing exclusions. Compiler source mapping does not imply arbitrary compiled source is native-admitted: nonempty ordered actions remain excluded. P12.8 establishes sampled resource continuity and compatible local-tool reconstruction, not universal resource ceilings, cross-machine binary equality, or perfect replay. Its historical full-harness missing-fixture boundary remains unclaimed here.

## Semantic authority and architecture

The debugger is an observer of canonical semantics, never a semantic authority. Canonical verification, runtime/authority/causal owners, execution-plan binding, and native admission/dispatch retain their existing responsibilities. The debugger may expose, correlate, navigate and compare their supplied evidence. It must not execute AIR independently, infer alternative results, rewrite canonical state, broaden native semantics, normalize mismatches away, become an authority or provenance engine, or silently substitute backends.

```text
Canonical execution/evidence
          ↓
Debugger Observation Adapter
          ↓
Versioned Debugger Protocol
          ↓
CLI / DAP / Visual Studio / Semantic Views / Domain Consumers
```

The future adapter validates supplied bindings through existing owners and projects immutable evidence into protocol values. It does not reproduce selection, assignment evaluation, policy decisions or routing. Missing evidence produces explicit availability/coverage information. Transport failure and canonical execution failure remain separate. Observation must remain optional and the compiler/runtime usable without AI services.

Concordat TAM-v3 remains the governance Token Analysis Map; compiler TAM supplies traceability and does not replace it. Tap Check remains user-controlled, diagnostic-only, read-only and non-activating. Quad-Vector, AETHER-AIR, Varenic Theory, rich-storytelling and ApexMotion continuity is preserved without introducing new semantics.

## Debugger Observation Model and reference identity

The public model consists of immutable references, evidence snapshots, correlations, events, coverage declarations and failures. Public protocol values must not contain implementation object pointers, mutable runtime objects, issuance tickets, or private engine internals.

Identity law is mandatory:

```text
AGENT != IDENTITY != ROLE != CAPABILITY != AUTHORITY
HUMAN != AGENT
ARTIFACT != SOURCE
PACKAGE != ORGANIZATION
DEBUG_SESSION != EXECUTION
DEBUGGER_VIEW != SEMANTIC_OBJECT
REPRESENTATION != IDENTITY
```

A reference points to an object; it does not become that object. A displayed name, generated representation or redacted value does not replace canonical identity.

Each debugger reference has `reference_version` (initially 1), `kind`, and explicitly separated `canonical` and `local` components. `canonical` is either an existing identity with its owner/schema and containing fingerprint, or explicitly unavailable with a reason. `local`, when needed, contains execution/session scope and producer occurrence; it cannot impersonate canonical identity. Optional `source_refs`, `provenance_refs`, and typed `relationships` link evidence. Relationships name their basis (owner binding, containment, source correspondence, invocation occurrence, result association); no unproven parent or causal edge is inserted. At least one scoped canonical or local identity is required. Resolution validates fingerprints and scope, never display-name matching. Unknown or unsupported kinds remain opaque/unavailable to clients.

| Observable kind | Reference basis / availability rule |
| --- | --- |
| Debug session | Opaque adapter-local session ID, scoped to protocol lifetime; not a semantic fingerprint. |
| Execution instance | Owner-issued execution-local ID bound to exact inputs, plan/routing/profile and available result evidence. Equal inputs may execute repeatedly with distinct instances. |
| Source document / source span | Existing source logical name and exact content identity; span preserves producer positions and containing source identity. No host-path identity. |
| AIR program / AIR operation | Existing verified transport fingerprint; operation ID and structural locator where supported. Repeat invocation occurrences additionally need execution-local identity. |
| Directive / workflow / state cell | Exact owner ID within owning AIR fingerprint; workflow references only where canonical evidence exists. State name is display information alongside its owner binding. |
| Principal / role / authority check | Distinct owner IDs within canonical scope; attach grants/capabilities/observed decisions as separate evidence. Principal does not confer debugger authorization. |
| Causal decision | Canonical decision/path IDs and owning program plus observed selection occurrence; debugger does not select a path. |
| Execution plan / routing target | Existing plan/association/routing fingerprints, entry and owner bindings; target/profile remains explicit. |
| Native artifact / generated-native region | Receipt/image/profile/mapping fingerprints; region references generated-source identity and span plus associated AIR operation. Artifact and generated source remain separate. |
| Trace record / provenance reference | Existing retained-record ID, collection fingerprint/family/ordinal, original TAM identity where present, and provenance-scope/association fingerprints. |
| Execution result | Owner result identity and execution association, retaining target-specific representation and status. No new canonical result inferred by debugger. |
| Diagnostic / failure | Producer code/severity/node and available evidence identity; local occurrence if no stable owner record identity exists. Display message is not semantic identity. |
| Lifecycle/resource observation | Existing snapshot/measurement/ownership evidence and lifecycle scope; live readings explicitly volatile or unavailable. |

Stable identities include AIR fingerprints, scoped directive/principal IDs, source-map fingerprints and profile identities. A bare directive ID is not globally unique across programs. Session IDs, execution IDs and stop/event occurrence numbers are local. Process IDs, memory addresses, wall time and object identity are never canonical semantic identity.

Session lifetime and execution lifetime are independent. A session may observe several authorized executions; an execution may outlive a disconnected session and be observed later under fresh authorization. A session close is not execution termination. Reattachment creates a new session ID, preserves the execution identity only with owner evidence, and does not reuse stale local references. A view's selection/filter/index has its own lifetime and no semantic ownership.

## Versioned event envelope

The proposed initial protocol identifier is `apexforge.debug.protocol/v1`. It follows existing `apexforge.<domain>/v1` schema naming; the dotted domain identifies a distinct debugger protocol rather than relabeling a P12 carrier. This is a documented initial compatibility contract, not a frozen wire implementation.

| Field | Contract |
| --- | --- |
| `protocol` | Required exact major identifier. |
| `event_kind` | Required dotted lowercase name following existing `runtime.start`, `directive.start`, `authority.check` conventions. |
| `session_ref` / `event_sequence` | Required session reference and nonnegative integer sequence, strictly increasing within session; first event is 0. It is delivery/observation order, not canonical operation order. |
| `execution_ref` | Required for execution-scoped events; explicitly absent for session-only events. |
| `semantic_ref` | Reference to subject if supported; otherwise explicit unavailable reason. Session events may mark this not applicable. |
| `correlation` | Explicit source/AIR/native references and per-link status/basis; no implicit complete chain. |
| `payload` | Immutable, kind-versioned observational values; producer/owner and coverage declared. No callable/mutable implementation objects. |
| `provenance_refs` | List of validated evidence references, empty with reason if unavailable; not a debugger-authored attribution claim. |
| `order_refs` | Optional supplied operation, trace, causal or region positions; their domains and scopes remain distinct. |
| `timestamp` | Optional observation timestamp with clock basis; volatile and excluded from stable identity. |

Envelope field absence is allowed only where this contract declares optional/not applicable; evidence unavailability is represented explicitly. Payloads declare `payload_version=1`, availability (`available`, `unavailable`, `redacted`, `not_applicable`), and completeness (`complete`, `partial`, `unknown`) with reasons and unsupported producer kinds when needed. Required trace omissions or retention overflow cannot be hidden behind `complete`. Reconnection/discontinuity must declare coverage loss; clients cannot infer consecutive semantic execution from consecutive event numbers. Duplicate deliveries may be deduplicated using session plus sequence, without merging identical semantic observations from repeated executions.

| Initial event kind | Meaning and emission prerequisite |
| --- | --- |
| `debug.session.start` / `debug.session.finish` | Adapter session lifecycle and scoped capability/coverage declaration. |
| `debug.execution.start` / `debug.execution.finish` | Owner-backed execution occurrence and result/status; retained records must be labeled retrospective, not live notifications. |
| `debug.directive.enter` | Observed directive-entry evidence such as `directive.start`; no inferred invocation frame. |
| `debug.operation.observe` | Explicit producer operation occurrence; metadata existence alone does not prove execution. |
| `debug.state.transition` | Owner-supplied state/delta evidence; before/after only when supplied or validated immutable snapshot evidence establishes them. |
| `debug.authority.check` / `debug.causal.decision` | Supplied `authority.check` or causal evaluation/selection evidence; original producer kind retained. |
| `debug.trace.observe` | Retained record/family/ordinal with existing provenance. |
| `debug.native.region` | Validated static or observed region correspondence, labeled as such; static C mapping does not prove that region ran. |
| `debug.diagnostic.observe` | Original execution diagnostic or separate debugger failure, explicitly identified by domain. |
| `debug.stop.observe` | Reserved for a future control owner to supply an actual stop and reason; never emitted merely because a client pauses its view. |

No event producer is implemented here. Existing trace names remain original evidence fields; the public namespace distinguishes adapter envelopes from canonical producer events. New typed lifecycle/resource observations can use additive optional payloads or negotiated future event kinds with explicit capability discovery.

## Ordering model

| Order | Authority / meaning |
| --- | --- |
| Semantic operation order | Canonical execution owner determines actual execution schedule. P12 metadata ordinal is a bounded structural/emission schedule, not proof of every live occurrence. |
| Debugger event sequence | Observational adapter delivery order within a session; may combine retrospective evidence and session lifecycle. |
| Trace order | Supplied collection family ordinals and, where available, managed `StreamReference.parent_index` interleaving. Diagnostic collection order does not establish interleaving with runtime steps. |
| Source order | Producer spans/declaration positions in an exact source snapshot; lexical location does not imply execution order. |
| Causal order | Explicit canonical decision evidence, invocation/causal links where supplied; partial order or unknown if evidence is insufficient. |
| Native-region correlation order | Emitter-recorded generated-C regions and operation associations within the admitted profile; not universal machine execution order. |

Clients may sort for display, but must label that presentation order. They cannot derive causal order from wall-clock timestamps alone, zip independently ordered families into fabricated edges, or turn repeated state names into unique operation occurrences.

## Source ↔ AIR ↔ native correlation

Public chain: `SourceLocation -> AIROperationReference -> NativeRegionReference`, with independent availability and evidence on each edge. `SourceLocation` contains source identity and producer span; AIR references carry verified program identity and supported locators; native region references carry mapping/profile/generated-source identity and span. Machine address is a separate optional observational extension, unavailable in the established foundation.

| Case | Required presentation |
| --- | --- |
| Source-mapped AIR | Validate original compiler evidence and exact source content. Show supported `SOURCE_BACKED` associations and explicit `UNMAPPED` operations. |
| Hand-built AIR | AIR identity remains usable; language-source edge is `UNMAPPED_SOURCE`. Never infer spans from names, literals or generated C. |
| Admitted AIR mapped to generated C | Show operation → generated region from native owner's mapping, with receipt/profile/source bindings. Language-source edge may still be unavailable. |
| Native region known, machine address unavailable | Generated C region navigation is available; CPU address/PDB navigation remains unavailable. |
| Transformed, linked, or wider AIR | Reject stale associations or declare unsupported coverage; P12's bounded mapping does not automatically transfer across transformations. |

Preserve `COMPILER_SYNTHETIC`, `GENERATED_CONTAINER`, and `METADATA_ONLY` lineage. Originating-declaration lineage is not a physical span for synthetic syntax. No fabricated complete bijection, universal PDB support, arbitrary CPU address stepping, native profile expansion or backend substitution is permitted.

## Immutable semantic-state observation

Future state views carry execution and observation occurrence, owning state reference/name, canonical type/representation, immutable encoded value, availability/redaction status, and supporting snapshot/delta/result references. Boolean and integer values remain distinct; native I64 decimal representation remains explicit. Unsupported opaque/mutable values are unavailable, not stringified into purported canonical values.

Before/after snapshots must be supplied by an execution owner or its validated retained snapshot evidence; missing before values remain unavailable. A debugger must not evaluate assignment expressions, replay mutations itself to manufacture state, or reconstruct policy/causal outcomes to fill gaps. Directive context includes supported directive identity and invocation occurrence; a trace depth alone is not a complete stack. Authority context exposes supplied principal/check/capability/resource/allowed evidence separately from inspector permissions. Causal context exposes supplied evaluation, selected path and weights without reselection. Results retain their owner binding and target representation; bounded cross-target comparison preserves any mismatch.

Snapshots are immutable evidence with capture point and completeness, never live mutable runtime objects. No state-write, expression-evaluation-as-semantics, authority-write or provenance-write API is defined.

## Execution-control boundary

Future request categories are `OBSERVE`, `REQUEST_STOP`, `REQUEST_CONTINUE`, `REQUEST_STEP`, and `REQUEST_TERMINATE`. Only observation architecture is defined here; no category is implemented by P13.1.

Future control requests must go through an explicit execution-control owner. That owner validates authorization, target capability, current execution state, request ID and stop generation, and reports accepted/rejected/completed status. Protocol request acceptance must not imply execution has stopped. Owner-issued safe-point/stop evidence is required before a stop event. Disconnect policy, concurrent request handling, termination effects, safe points and transactional behavior require P13.2 design/tests. The protocol does not directly mutate runtime internals. External observation clients acquire no implicit control rights.

## Future breakpoint and stepping taxonomy

| Breakpoint kind | Architectural binding; implementation deferred |
| --- | --- |
| Source | Exact source snapshot/span and proven AIR association; unresolved if unmapped. |
| Directive entry | Scoped directive identity plus owner entry safe point. |
| Workflow | Canonical workflow reference and supported owner transition. |
| AIR operation | Supported operation reference and owner occurrence boundary. |
| Semantic-state predicate | Owner-controlled, bounded, side-effect-free predicate contract to be reviewed later; debugger may not become an evaluator. |
| Authority check | Supplied check identity and owner observation boundary; no authority decision override. |
| Failure/diagnostic | Producer diagnostic/failure classification at a supported boundary. |
| Native correlation | Validated AIR/generated region relationship and advertised owner boundary; no implicit CPU breakpoint. |

A semantic breakpoint concerns canonical semantic boundaries. A machine instruction breakpoint concerns CPU execution addresses and requires separate future target support and validation. Breakpoint binding and hit occurrences must remain distinct references; unresolved/multiple associations cannot be silently selected.

Future modes: `SOURCE_STEP` (next supported source-correlated boundary), `SEMANTIC_STEP` (next supported canonical operation boundary), `DIRECTIVE_STEP` (supported directive boundary), `WORKFLOW_STEP` (supported workflow boundary), and `NATIVE_CORRELATION_STEP` (supported boundary with generated-native correlation). Granularity, enter/over/out rules, repeated invocations and target parity remain future owner contracts. `NATIVE_CORRELATION_STEP != RAW_MACHINE_INSTRUCTION_STEP` unless a separately authorized milestone adds and validates that capability. No stepping or breakpoint engine is implemented or promised across all targets.

## TAM, trace and provenance integration

Expose existing retained families distinctly: `tam`, `core-runtime`, `runtime-diagnostic`, `causal-selection`, `authority-observation`, `narrative-runtime`, and `native-evidence`. Preserve original producer, schema, retained identity, ordinal, completeness and unresolved TAM links. Use P12 scope/association/receipt/image/generated-source/output/result fingerprints rather than a competing provenance carrier. Original TAM identity and retained-record identity are separate.

Source-map-entry TAM records can carry exact supported operation association. Runtime trace records currently lack universal producer operation locators; association must remain unavailable where not supplied. Native retention establishes pre-dispatch and result evidence, not per-operation runtime tracing. Unsupported kinds and partial retention must be visible. Diagnostic display text remains outside existing stable fingerprints.

Views may answer what happened, where supplied evidence originated, which canonical object it references, and what validates a correlation. They cannot infer actor attribution, provenance custody, causality or authority from unsupported associations. `EVIDENCE_BEFORE_ATTRIBUTION=True`. Receipts are evidence within existing trusted issuance/binding contracts, not debugger-issued signatures or universal provenance attestations.

## Replay distinctions

| Concept | Contract and limit |
| --- | --- |
| Deterministic reconstruction | Execution owner re-executes equivalent verified inputs, initial state, policy, configuration, plan/profile and compatible tool contracts. Produces a new execution instance; compatible fingerprints/results are compared without normalization. |
| Trace replay | Present retained events in their supplied logical order, preserving family and interleaving limitations; no execution and no invented missing observations. |
| Visual replay | Navigate immutable retained snapshots/correlations and view positions without re-execution; UI pause is not execution stop. |

P12.8 fresh-process/root/hash-seed reconstruction supports bounded compatible local-tool evidence, not perfect replay for all executions or external effects. Missing inputs, partial traces, unsupported policies, tool mismatch and unavailable external evidence constrain replay. P13.6 must define comparison projections and report divergence; no replay engine is implemented here.

## Clients and TDP continuity

One observation model serves CLI, future DAP/VS Code, Visual Studio, semantic IDE views, future TDP dashboard components and domain platforms. Clients negotiate capabilities, resolve scoped references and render evidence; they must not redefine semantics, duplicate execution engines or reinterpret missing evidence as successful mapping. DAP is a future translation layer, not the canonical model. IDE workspace filenames must be checked against source content identity before presenting live-source correlation.

TDP is a downstream observability consumer. Live Monitor can consume session/execution observations; Transvergent Analytics can compare supported retained evidence; FAME views and Varenic trajectories can consume supplied references and causal evidence; Incident timeline can navigate explicit logical order; Medic Lab evidence can inspect retained provenance/results; System Health can consume ownership/lifecycle measurements with availability and volatility. These are reserved reuse opportunities, not evidence that TDP-specific metrics, attribution or semantic models exist. Full TDP remains a later domain-platform objective. P13.10 previews require separate authorization; no TDP UI or debugger semantics are introduced here.

## Protocol compatibility and capability discovery

Major version changes are required for changed required fields, reference identity meaning, ordering guarantees, mandatory payload interpretation, authorization/control meaning, or incompatible event semantics. Optional additive fields and new optional event kinds may remain v1 if older clients can retain/skip them without changing understood meaning. Required capabilities/extensions must be negotiated explicitly; silently ignoring a required extension is prohibited. Existing P12 schema versions remain independent and cannot be rewritten by protocol negotiation.

Unknown optional fields are ignored or retained opaquely; unknown optional events are reported as unsupported/opaque with their sequence and coverage preserved, never interpreted as an authority/control/state event. Unknown required schemas or incompatible major versions fail negotiation before attachment/control. Lossless evidence inspection may remain possible separately if independently authorized. Capability reduction is reported explicitly and graceful degradation keeps known evidence navigable without inventing missing views.

Discovery is scoped to session, authorized execution and target, independent of protocol major. Each sorted capability record contains name, capability-contract version, status (`available`, `unavailable`, `restricted`), reason, coverage/target limits and required authorization. Changes during a session require an explicit updated declaration; version v1 alone promises no stepping or control.

Initial vocabulary: `source_mapping`, `air_mapping`, `native_correlation`, `semantic_state`, `authority_view`, `causal_view`, `trace_view`, `provenance_view`, `source_stepping`, `semantic_stepping`, `native_correlation_step`, `replay`, `execution_control`, and `redaction`. Replay records distinguish reconstruction/trace/visual modes; control records distinguish request categories; native correlation distinguishes generated C from machine addresses. Stable ordering is lexical by capability name and contract version. Capability presence does not imply semantic authority or permission; availability depends on actual evidence and authorization, not optimistic target labels. Discovery implementation is deferred.

## Security and resource/lifecycle boundaries

Debugger sessions do not inherit unrestricted execution authority. Inspection is scoped to explicitly authorized executions and evidence; attachment/control requires explicit authorization. Policy decisions remain with existing/future authorized owners. Observation cannot mutate authority records, provenance, artifacts or state. External clients cannot silently gain control rights. Sensitive value redaction must be explicitly supported and represented as `redacted`, not false empty/null semantic values. Redacted projections have distinct view identity and must not masquerade as canonical fingerprints. Authentication, transport security and redaction implementation are deferred, not claimed established by P12.

Do not export local filesystem paths, process credentials, issuance tickets or unrelated execution data as protocol identity. Native custody/receipt validation and image locks remain with the backend. Client-supplied filenames/addresses do not authorize observation. P12 authorized quiescent-root and trusted-process assumptions remain visible; no remote signature, hostile-root race protection or unrestricted process attachment claim is added.

Reuse P12 ownership evidence, resource classes and lifecycle boundaries as analytical labels. Ephemeral observation buffers and session-local indexes are session-owned IRR candidates with explicit cleanup boundaries. Retained trace evidence may use CER/DHF labels according to declared purpose/custody; canonical references may use SHR continuity analysis, without becoming semantic objects or extending their owner's lifetime implicitly. These are classifications, not new runtime resource semantics.

Every retained debug record requires `Known Owner + Known Purpose + Known Lifetime + Valid Binding`; additionally preserve trigger and cleanup-boundary evidence from P12. Unknown ownership/availability remains explicit. Session close releases session resources and does not delete canonical evidence or revoke its owner's independent retention. Retention transfer needs an explicit new owner/lifetime and validated binding. Released native artifacts cannot be redispatched merely because retained debug evidence survives. Future buffers/indexes need bounded retention, explicit overflow/discontinuity reporting and cleanup/failure validation; no aggregate resource ceiling is inferred from P12 measurements. MSC remains a resource-continuity analytical lens, not a semantic engine or runtime dependency.

## Determinism and failure model

Deterministic candidate surfaces are semantic reference serialization, stable envelope fields and evidence payloads, source/AIR/native references, sorted capability declarations and trace/provenance references under equivalent inputs/contracts. Stable projection must exclude timestamp, session/execution-local IDs, session-specific sequences, UI layout, process IDs, memory addresses and timings. Full event bytes are not necessarily deterministic. Preserve existing P12 canonical forms/fingerprints; define and validate any future wire canonicalization separately, including encoding, exact types, ordered lists, unsupported values and schema domain separation. Do not hash volatile wrappers into canonical semantic identities.

| Debugger failure class | Required response |
| --- | --- |
| `unsupported_capability` | Report target/authorization/coverage limits and retain available views. |
| `unavailable_mapping` | Explicit missing edge; not semantic execution failure. |
| `stale_execution_reference` | Reject lookup/control until owner-backed rebinding; no automatic reassignment. |
| `stale_artifact_reference` | Reject substitution/stale binding; retain separately valid historical evidence. |
| `authorization_failure` | Deny attachment/inspection/control as scoped; disclose no forbidden values. |
| `protocol_incompatibility` | Fail incompatible required negotiation; no guessed schema interpretation. |
| `disconnected_session` | Declare delivery/coverage discontinuity; execution lifetime follows owner policy. |
| `execution_completed` | Report lifecycle state; reject impossible control while allowing authorized retained inspection. |
| `observer_unavailable` | Declare missing/partial observation; preserve canonical owner result and original failures. |
| `native_correlation_unavailable` | Degrade to supported AIR/source/generated evidence; no implicit fallback or CPU mapping. |

Failure records contain domain, code, request/event occurrence, scoped subject, availability/coverage impact and supported provenance. Canonical diagnostics keep original codes/results. Adapter failures do not replace them or convert successful execution into invented canonical failure. Mismatch evidence stays visible; stale/substituted data fails validation rather than being normalized.

## Gap matrix and minimum sequence

Classifications below describe architecture and future capability gaps, not implementation defects merely because P13 is unimplemented. Primary classification and explicit deferral are separate. `NO_GAP` is bounded to the stated reuse/contract.

| ID / finding | Classification | Disposition / required evidence |
| --- | --- | --- |
| G01 immutable bounded metadata identities | `NO_GAP` | Reuse P12 identities; wider public kinds use scoped references rather than replacement carriers. |
| G02 shared debugger identity/envelope lacked public contract | `DEBUGGER_CONTRACT_GAP` | Defined by this review artifact; adapter validation remains `DEFER_TO_P13_2`. |
| G03 session/control owner, stops and authorization enforcement absent | `DEFER_TO_P13_2` | Owner session lifecycle, safe points, request validation and immutable stop evidence; no state writes. |
| G04 complete state/stack and operation occurrence observations unavailable universally | `OBSERVABILITY_GAP`, `DEFER_TO_P13_3` | Reuse retained state/results; add only owner-backed supported capture, declare missing before values/frames. |
| G05 linked/transformed/multi-directive source correspondence beyond bounded producer | `SOURCE_MAPPING_GAP`, `DEFER_TO_P13_4` | Preserve unsupported coverage; require new producer evidence and compatibility tests before extending mapping. |
| G06 live native per-operation events and CPU-address/PDB coverage absent | `NATIVE_CORRELATION_GAP`, `DEFER_TO_P13_4` | Generated-C mapping reusable; arbitrary machine stepping remains excluded unless separately authorized/validated. |
| G07 retained family/provenance carriers | `NO_GAP` | Reuse bounded family/scope/result associations; do not claim universal attachment. |
| G08 runtime record → operation association and complete causal/attribution edges missing | `TRACE_PROVENANCE_GAP`, `DEFER_TO_P13_5` | Require exact producer occurrences/evidence; preserve unresolved links and unsupported attribution. |
| G09 reconstruction/replay/comparison product absent | `DEFER_TO_P13_6` | Define compatible input contracts, partial replay and mismatch reporting; reuse bounded P12 reconstruction evidence. |
| G10 attachment/client authorization and sensitive-value redaction absent | `AUTHORIZATION_GAP` | `DEFER_TO_P13_2` for owner authorization; later clients require scoped transport/redaction tests. P12 custody is not authentication. |
| G11 debugger version/discovery contract absent | `PROTOCOL_VERSIONING_GAP` | Defined here; implementation/compatibility tests `DEFER_TO_P13_2`; client negotiation `DEFER_TO_P13_7_PLUS`. |
| G12 debugger buffers/indexes/retention custody not implemented | `RESOURCE_LIFECYCLE_GAP`, `DEFER_TO_P13_2` | Reuse P12 analytical model; validate bounded session resource ownership and close/disconnect behavior. |
| G13 CLI/DAP/VS Code/Visual Studio/semantic views absent | `CLIENT_INTEGRATION_GAP`, `DEFER_TO_P13_7_PLUS` | Consume common contract; no independent semantic engines. |
| G14 TDP dashboard/platform absent | `DEFER_TO_P13_7_PLUS` | Downstream dependency recognized; preview/domain work needs separate scope, no TDP semantic engine. |
| G15 cross-target debugger parity and closure evidence absent | `DEFER_TO_P13_7_PLUS` | Validate supported intersections, explicit degradation and preserved freezes; no universal parity claim. |

Recommended sequence follows the requested roadmap; repository evidence supports separation of retained observation, owner control, mapping and client translation rather than a broader redesign.

| Stage | Minimum authorized future slice and dependencies |
| --- | --- |
| P13.1 | Architecture/observation contract, this document only. |
| P13.2 | Execution session and stop/control foundation: explicit owner seam, scoped authorization/capability negotiation, execution/session lifecycle, supported safe-point and request/stop identities, observation delivery/failures and resource custody. No arbitrary backend semantics, client UI, state-write API or broad stepping/breakpoint implementation. |
| P13.3 | Immutable semantic state/stack/directive/authority inspection; supported capture and missing evidence semantics on P13.2 owner boundaries. |
| P13.4 | Source/AIR/generated-native correlation and supported stepping/breakpoint binding; mapping expansion only with producer evidence and compatibility validation. CPU stepping is not implied. |
| P13.5 | TAM/causal/provenance views and supported exact occurrence links; evidence before attribution. |
| P13.6 | Compatible deterministic reconstruction, trace/visual replay and explicit comparison divergence. |
| P13.7 | CLI debugger consuming negotiated common model. |
| P13.8 | DAP translation and VS Code integration; transport/client authorization and degradation tests. |
| P13.9 | Visual Studio integration consuming the same model. |
| P13.10 | Semantic IDE views and separately scoped TDP preview components, not the full TDP domain platform. |
| P13.11 | Cross-target debugger validation over supported contracts and exclusions. |
| P13.12 | Closure/freeze-readiness review; owner alone authorizes freeze/release. |

Open implementation decisions: concrete safe points and concurrency rules, wire serialization/canonicalization, transport/authentication, redaction policy, buffer limits, stack coverage, operation occurrence enrichment and target-specific control support require later evidence. They are explicit gaps rather than implicit P13.1 promises. No later work is activated by this sequence.

## Exclusions and validation record

Excluded: production code, new tests, stepping, breakpoints, DAP, VS Code/Visual Studio debugger integration, replay implementation, TDP operator UI/platform, authentication implementation, state mutation APIs, semantic engines, native profile expansion, arbitrary CPU-address/PDB support, P12 reopening, staging/commits/tags/pushes, P13.2 implementation and P14/P15/P16 work.

Only this documentation artifact changes. Validation is repository baseline/preservation inspection and document contract/marker review, not runtime regression execution. No behavioral contract or production diagnostics changed, so no new tests or full regression harness run is claimed. The initial search for a top-level `tests` directory reported it absent; focused tests were found under `apexforge` and inspected there. The command runner's sandbox setup failed; read-only repository inspection used approved escalation. No test failure is concealed. Remaining risks are unsupported live/native coverage, unresolved future control/security design, and client implementations accidentally interpreting views as semantic authority; the contract requires explicit degradation and owner validation.

Expected preservation after document creation: HEAD remains the exact baseline, tracked and cached diffs are empty, all P12 files unchanged, and the sole untracked artifact is this path. No release/freeze decision is made by the architecture marker below; it records coverage of the requested document contract for review.

## Evidence-supported markers

```text
P13_SEMANTIC_AUTHORITY=CANONICAL_AIR
P13_DEBUGGER_ROLE=OBSERVATIONAL_CLIENT
P13_DEBUGGER_SEMANTIC_ENGINE=False
P13_SECOND_SEMANTIC_IMPLEMENTATION=False
P13_P12_REOPENED=False
P13_NATIVE_PROFILE_EXPANDED=False
P13_EXECUTION_CONTROL_IMPLEMENTED=False
P13_BREAKPOINTS_IMPLEMENTED=False
P13_STEPPING_IMPLEMENTED=False
P13_DAP_IMPLEMENTED=False
P13_VSCODE_DEBUGGER_IMPLEMENTED=False
P13_VISUAL_STUDIO_DEBUGGER_IMPLEMENTED=False
P13_TDP_UI_IMPLEMENTED=False
P13_TDP_OBSERVABILITY_DEPENDENCY_RECOGNIZED=True
P13_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P13_MSC_SEMANTIC_ENGINE=False
P13_EXISTING_DEBUG_METADATA_REUSABLE=True
P13_EXISTING_SOURCE_MAPPING_REUSABLE=True
P13_EXISTING_TRACE_PROVENANCE_REUSABLE=True
P13_EXISTING_RESOURCE_OBSERVABILITY_REUSABLE=True
P13_DEBUGGER_IDENTITY_MODEL_DEFINED=True
P13_EVENT_CONTRACT_DEFINED=True
P13_PROTOCOL_VERSIONING_DEFINED=True
P13_CAPABILITY_MODEL_DEFINED=True
EVIDENCE_BEFORE_ATTRIBUTION=True
P13_1_ARCHITECTURE_CONTRACT_COMPLETE=True
```

Reuse values mean reusable within inspected P12 bounds, not universal coverage. Defined values mean specified in this document, not implemented/frozen. Stop after P13.1.
