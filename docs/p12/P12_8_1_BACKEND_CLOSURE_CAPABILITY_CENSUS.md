# P12.8-1 — Backend Closure Capability Census

## Authority, baseline, and method

This is a documentation-only capability census, dated 2026-09-30. It recommends evidence work for human review; it does not declare P12.8 frozen, released, or otherwise close the six-pillar program. The user's explicit P12.8-1 instruction supersedes the stale P11.4A current-stage text in AGENTS.md for this slice. All other repository authority and preservation rules apply.

Before inspection, Git established:

- Branch: `p12-8-backend-closure`.
- HEAD: `e25b98699098f9b3d61d1478c42ea27b54aea78f`.
- Peeled `afp-p12.7-freeze`: exactly that HEAD.
- `git status --porcelain=v1`: empty, including index and untracked paths.

Read-only ancestry checks also established that `afp-p12.6-freeze` and `afp-p12.5-execution-freeze` are ancestors of HEAD. Existing tags were inspected, not created or altered. Tracked and cached diffs remained empty before writing this document.

Method: inspect production owners, focused tests, and frozen reports; distinguish implementation inspection, previously executed evidence, and proposed measurement. No execution suite, restore, native compilation, benchmark, or pressure experiment was run in this census. Existing PASS results below are attributed historical evidence, not fresh census passes. The initial restricted command helper failed during setup; approved command execution then performed the read-only inspection. Two searches used nonexistent/glob paths; corrected explicit-file/directory searches supplied the relevant evidence. No failed search was treated as negative implementation evidence.

The sole deliverable is this file. No production behavior, test assertion, fixture, CLI, runtime, AIR, grammar, or toolchain configuration changes.

## Preserved P12.7 claim and qualifications

`canonical AIR runner == managed-retained RuntimeEngine path == bounded native execution`

The claim is confined to `apexforge.native.win-x64.i64-literal-state-set/v1`, successful complete typed named final-state projection, and the sampled P12.7 fixtures under equivalent default initial conditions. Canonical and managed-retained share the Python RuntimeEngine owner; there is no claim of three independent semantic engines or independent .NET AIR execution.

The unchanged admission contract permits 1–256 explicit INT states with signed-I64 literal initial values, one directive/principal, 1–4096 singleton max_weight decisions referenced once in directive order, and 1–4096 total literal set_int stores. An individual singleton path may have no assignments if the total remains positive. Exact reviewed schemas/tuples, entry identity, canonical verification and owning-program transport agreement are required. Ordered actions, emits, effects and invocations are empty; authority-bearing programs and other unsupported program surfaces remain excluded. IDs subject to the profile identity check have a 256-character bound. Metadata strings are not thereby all byte-bounded.

P12.7 tested nine positive fixtures twice per path and four explicit outside-domain classes: BOOL state, add_int, alternative paths, and nonempty ordered actions. It did not exhaust the admitted domain. Native RuntimeEngine fallback was failure-trapped during the 18 native positive executions. Source-language compiler AIR with nonempty actions remains rejected; actions must not be stripped to create native fixtures. Hand-authored AIR can legitimately be UNMAPPED_SOURCE.

No intermediate native trace, instruction equivalence, performance equivalence, memory equivalence, arbitrary platform, persistent artifact import, or toolchain-independent binary equality follows. Native receipts are trusted-process provenance, not remote signatures or protection from arbitrary hostile Python in the issuing process. Build roots and installed tools remain trusted inputs.

Evidence: [P12.7-3](P12_7_3_INTEGRATED_BEHAVIORAL_EQUIVALENCE_CLOSURE_REVIEW.md), [P12.7-4](P12_7_4_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md), and [native admission](../../apexforge/native_backend/native_execution_contract.py).

## Six-pillar P12.8 charter

The official P12.8(1–6) dimensions remain performance; security; memory/resource behavior; reproducibility; determinism; and full regression/freeze closure. Stages proposed below are work ordering, not replacement roadmap dimensions.

| Pillar | Current capability | Missing closure evidence |
| --- | --- | --- |
| 1. Performance | Advisory P11 project timings; callable backend phase boundaries; test durations | Native phase sampling, supported-size curves, observer overhead, repeat/cold/warm evidence |
| 2. Security | Fail-closed admission, issuance/image binding, provenance and stale-association rejection | Lifecycle review under repetition/faults; trusted-root/toolchain and authority-lifetime evidence |
| 3. Memory/resource | Scoped native files/handles, fixed output, retention record limits, explicit cache owners | Parent/child peaks, handle/process accounting, post-release plateaus, aggregate retained-byte bounds |
| 4. Reproducibility | Local identical-toolchain PE/receipt/results; deterministic mappings; clean-machine stack evidence | Controlled reconstruction matrix separating semantic and binary products |
| 5. Determinism | Canonical serialization, routing, ordered stores, immutable traces, repeated projections | Semantic/provenance invariance under measured resource cycling and permitted load |
| 6. Regression/freeze | Named authoritative predecessor gates and cleanup/ancestry reports | Integrated P12.8 evidence with fresh required gates and preserved historical blocker policy |

## MSC Resource Continuity Lens — engineering only

MSC / MSC-2 is an analytical resource-lifecycle and information-continuity vocabulary. It evaluates:

`Resources may expand, contract, move, cache, and disappear; canonical semantic identity must not.`

`Retained Resource => Known Owner + Known Purpose + Known Lifetime`

An unidentified owner, purpose, or lifetime is a candidate resource-closure gap. Persistence or an increasing working set alone does not prove a leak. Intentional retained evidence and allocator high-water behavior require different analysis from unintended live ownership.

| MSC term | Operational correspondence in this census |
| --- | --- |
| Mnemo-Pressure | Current working set, allocations, processes/handles, buffers, traces, caches, temporary/generated artifacts and metadata |
| Narrative Pulse | `validate → plan → lower → build → dispatch → retain → cleanup`; phases can repeat validation and observation without another semantic execution |
| Spatial Tensor of Recall | The ownership topology in the inventory below; caller, compiler, verifier, planner, runtime, native backend, tooling, tests and evidence custodian remain distinct |
| Memory Potency Gradient | `ephemeral → operational/reusable → canonical`; persistence is intentional only under a stated owner/purpose/lifetime |
| Sovereign Stability Vector | Semantic/provenance identities that survive incidental resource replacement |
| Decoherence Boundary Layer | Scope exit, child exit/reaping, file/handle close, invalidation or explicit caller release where authorization to retain a temporary resource ends |
| Trigger-Topology Dynamics | Build/admission/dispatch/retention/cache lookup/dependency change/release events, not an alternate scheduler |
| RCI-2 / continuity | Reconstruction preserves governed semantic identity and reproducibility without preserving a PID, object address, handle or temporary path |

MSC is not a semantic evaluator, execution engine, runtime dependency, AIR interpretation layer, substitute for OS/runtime evidence, or literal quantum-hardware claim. No repository structure is renamed. Concordat TAM-v3 remains governance-level TAM; compiler TAM traceability does not replace it. Tap Check remains user-controlled, diagnostic-only, read-only and non-activating. Quad-Vector, AETHER-AIR, Varenic Theory, rich-storytelling and ApexMotion continuity is preserved without extending this slice.

### Retention classes

| Class | Meaning and expected property | Evidence-supported application |
| --- | --- | --- |
| IRR — Ephemeral | Ends at a defined lifecycle boundary | Local parser/verifier/runtime work lists; wrapper-owned generated C/object/image/discovery script; dispatch capture files and image lock |
| CER — Canonical | Intentionally deterministic persisted product/evidence | Committed contracts/reports, verified AIR content identity, canonical result content and governed hashes; persistence still requires a custodian |
| DHF — Operational retained | Reusable resources with bounded ownership and invalidation | Caller-owned compiler/plan/trace associations, cache entries/session indexes, process-local live issuance records |
| SHR — Continuity invariants | Identity survives reconstruction independently of incidental resources | Freeze/provenance roots, principal/directive identity, profile and contract fingerprints |

A Python result object is not automatically permanent CER storage: its semantic content can be canonical while its live wrapper is caller-retained DHF. A hash string is not an allocation ownership policy. Objects with uncertain downstream custody remain unclassified beyond the observed boundary; no forced class assignment.

### Resource-pressure vector and measurable surfaces

`M_r = (Wp, H, At, Tb, Cb, Pc)` is a vector, not a score. No scalar weighting or numerical pressure observation is invented here.

| Coordinate | Observable today | Current repository support / proposed adapter limitation |
| --- | --- | --- |
| Wp — working-set/process-memory | Windows process working set/private-memory counters; Python traced allocations can be observed separately | No backend collector found in inspected owners. Future Windows adapter must distinguish parent, short-lived native child and compiler/linker tree. Python tracemalloc would miss native/CLR allocations; snapshots miss short-lived peaks |
| H — handles/processes/threads | Windows process/handle/thread snapshots and explicit launch/reap/close events | Launches and scoped handles are visible in code/tests; OS sampling not integrated. Need permissions, race/missed-child reporting and observer-handle accounting |
| At — temporary artifacts | Directory file counts/bytes/extensions and source/object/image hashes | Existing temporary roots, actual files, acceptance image bytes; future inventory must sample before cleanup and count capture/discovery files, not merely source/exe |
| Tb — traces/debug/metadata | len(trace.steps), diagnostics, records, operations, regions, source bytes; governed serialization lengths where available | Existing immutable tuples, canonical forms and RetentionLimits. Count is not deep allocated bytes; no machine-address/native per-operation trace exists |
| Cb — retained/cache | CacheCollection.entries, session indexes/observations, retained result counts, native issuance count | Explicit owners and immutable entry identities; no aggregate-byte budget or pressure sampler. Weak issuance table should be checked after artifact references are released |
| Pc — post-cleanup residue | Root existence/listing/bytes, surviving owned children, handle delta, logical live-entry delta | Native deletion assertions and closure artifact inventories exist. No sustained post-release memory/handle plateau series |

Latency uses an independent monotonic duration surface (`perf_counter_ns` exists in P11 tooling). Physical paths/PIDs needed privately for attribution are observation data, excluded from governed semantic fingerprints and shareable personal-data output. OS API availability is a design option, not a new installed dependency or tested collector.

## Resource ownership and lifetime inventory

References below name current production owners and existing test coverage. Quantities are measurable surfaces or inspected bounds, not measurements from this census. IRR ends when live references/scopes end; Python allocator RSS need not immediately shrink.

| Resource / category | Owner, trigger, purpose | Intended lifetime / cleanup boundary; class | Quantity / known limit | Existing evidence; missing evidence |
| --- | --- | --- | --- | --- |
| Source text, tokens, AST and compile work lists — Python | language compiler/parser when compiling; build AIR | Call-local intermediates end on return/error; returned CompiledSource held by caller. IRR / returned DHF | Input bytes, tokens/nodes/map entries; general compiler has no global memory budget established here | Compiler smoke; P12.6 compiler neutrality. Allocation peaks and exceptional-release measurements absent |
| Compiler SourceMap and optional operation ledger — Python/logical metadata | compiler producer; exact source correspondence | Immutable products shared by compiler metadata/consumer; release when consumers release. DHF | Entries/evidence/source bytes; opt-in tooling caps source at default 4 MiB and records at 10,000 | P12.6-3/4/8; limits apply to tooling, not a general parser allocation bound |
| Verifier diagnostics/indexes and verified graph — Python | AIRVerifier.verify / RuntimeValidator; validation | Local validation work IRR; VerifiedAIRProgram caller-owned, canonical content CER/SHR identity | Graph and diagnostic counts, transport bytes | AIR verifier and lowering seam; no peak-memory/cost series |
| Registry dependency queue, owner indexes and execution plan — Python | workflow.air_runner.build_registry_execution_plan; reachable ownership/routing | Construction IRR; plan and ownership mapping retained by caller/session, DHF | Reachable graph/owner count and routing fingerprint | Plan binding, linked execution and P12.6 association gates; aggregate retained size unmeasured |
| Canonical lowering transport/admission relocation — Python | native lowering_input / native admission after verification | Temporary serialized graph/maps IRR; caller may retain lowering/admission product DHF | JSON bytes; native states ≤256, decisions/stores ≤4096 | P12.2C/D, profile tests; repeated revalidation/serialization costs unmeasured |
| Execution indexes, assignments/events/effects, trace lists and working state — Python | RuntimeEngine.execute; semantic execution | Call-local lists IRR; returned immutable ExecutionResult/StateDelta/Trace/state caller-retained DHF with canonical content | State/trace/delta counts; invocation depth default 32, conditional/function bounds 64; no general trace-byte cap established | State/authority/causal/registry regressions; Python allocation plateau and pre-return trace pressure unmeasured |
| Metadata sidecars, SourceAIRMapping, PlanMetadata, source content and TAM attachment — logical retained/Python | tooling association/compiler adapters; observational links | Caller owns product and source references; invalidate/rebuild when source/AIR/plan identity changes; DHF | Bytes, operations and map records; RetentionLimits checks source and selected record counts | P12.6-3/4/8 stale rejection and immutable sharing; total transitive bytes/consumer release policy absent |
| Managed retention collections, interleaving, context/result fingerprints and owner_result on error — Python/logical retained | trace_integration after exactly one RuntimeEngine call | Caller owns returned retention or exception-held original result until released; DHF | Runtime trace+diagnostics checked against records default 10,000 AFTER owner returns | P12.6-6/8 order/context/partial/limit tests. Retention limit does not bound producer allocation or retained results across calls |
| Incremental cache entries and dependency observations — Python retained | incremental_cache/operational.CacheCollection; explicit store/lookup/invalidate | Caller retains immutable collections; dependency invalidation returns replacement, old snapshots live if caller keeps them. DHF | Entry/dependency counts; no capacity/byte quota found | P11.12F dependency-aware cache gate; pressure, old-snapshot custody and caller budget missing |
| Incremental build session indexes/configuration fingerprints — Python retained | IncrementalProjectBuildSession; reusable builds | Session owns collection, key/slot/trusted indexes and configuration cache; current work cleared in finally; last observations retained. DHF | Entries/index/configuration counts and owner invocation counters | P11.12G and Stability reuse gates; lifecycle ends when session/references released. Workload-churn upper bound not established |
| Tool discovery env, tool hashes, companion-DLL byte reads, pipes — Python/subprocess | native _toolchain per build; bind trusted installed MSVC | Discovery processes finish under 30/60-second timeouts; buffers/env IRR, hashes copied to receipt DHF/canonical content | Captured stdout/stderr and DLL bytes; no discovery-result cache in this chain | Native provenance/failure tests; full byte reads/capture_output not aggregate-byte bounded; process-tree/pipe peaks absent |
| discover.cmd, program.c, program.obj, program.exe and build directory — filesystem | native build_native; compile admitted stores | execute_native / execute_native_retained own TemporaryDirectory, cleanup on exit. Low-level build_native does NOT own directory cleanup: caller obligation. IRR for wrappers / explicitly retained caller DHF | File counts/bytes; generated source region count states+stores | P12.5 repeated builds and P12.6 wrapper deletion assertions; fault/timeout/locked-cleanup pressure matrix missing |
| Compiler and linker processes — subprocess/native | build_native structured compiler argv, explicit cwd/env; build PE | subprocess.run timeout handles direct child; descendants not explicitly tracked by backend. IRR | Process count/CPU/private bytes/capture bytes; build timeout default 60, allowed ≤300 s | Build failure fault injection; real descendant teardown/buffer peak evidence missing, no demonstrated orphan defect |
| Native issuance ticket/table — Python retained | build_native records exact artifact/receipt tuple in WeakKeyDictionary | Live artifact owns ticket; weak entry vanishes when ticket unreachable; no explicit authority-revocation timer. DHF | Live issuance entries/receipt bytes | Forged/substituted ticket tests; sustained GC/release plateau not measured |
| Locked image descriptor/Windows handle — OS resource | dispatch_native._locked_image; deny replacement/write through child exit | fdopen context closes descriptor/handle; conversion failure closes raw handle. IRR | Open handle count, duration | Live image-write-lock test; repeated/failure handle-count measurements absent |
| Dispatch child, stdout/stderr capture files, 8-byte-per-state wire buffer — native process/files/Python | _run for issued digest-checked image only | Child waited; timeout kill+wait; TemporaryFile contexts close on all scoped exits. IRR | Output exact 8×states, ≤2048 bytes; stderr must be empty; timeout default 10, allowed ≤300 s | Native fault injection checks timeout kill/reap and malformed output. Disk capture has no universal hostile-output quota; trusted generated code is the boundary |
| Native result, receipt, output hash, pre/post association and mapping — Python/logical retained | decode and tooling native capture; preserve result/provenance | Caller retains snapshots after files disappear; DHF wrapper, CER semantic content / SHR roots | Result state count, receipt bytes/map regions; native region retention limit enforced | P12.6 snapshot validation after cleanup, stale result/image/receipt negatives; retained aggregate bytes unmeasured |
| .NET carrier decoding/runtime-host lifecycle — CLR | managed decoder/host; admission/representation/start-stop | JsonDocument disposed with using; carrier/host objects GC-owned. IRR/DHF | CLR allocations/process working set, transport size | RCV-43–49 and managed stack; no independent .NET AIR execution or CLR pressure benchmark implied |
| Legacy native lifecycle DLL registry / ABI SafeHandles — native/CLR | P12.4 native register/release; ManagedNativeAbi wrappers | Native owner releases registered resource through disposer, clears slot before callback; SafeHandle ReleaseHandle/ReleaseBuffer delegates. Operational entries DHF until release, fixed registry module-lifetime | 64 slots, kind/length/live status; actual OS allocation depends on disposer | P12.3 ownership and P12.4 lifecycle/DLL gates in transitive stack; not the P12.5 executable dispatch path, no new integration assumed |
| Test probe projects, executables/DLLs and temporary directories — .NET/native/filesystem | focused/RCV test harnesses; contract probes | Scoped TemporaryDirectory/probe cleanup; generated repository bin/obj and caches require harness/validation-owner cleanup. IRR | File bytes/count/extensions, subprocesses | P12.7-4 records 150 generated files removed from 18 directories. Repeated harness residue not characterized |
| Python __pycache__, managed bin/obj/PDB/restore assets — filesystem | interpreter / dotnet tooling | Build-operational artifacts; validation owner reclaims generated outputs after gates, never tracked source. DHF during build, IRR for closure cleanup | Inventory bytes/files | -B on top-level tests does not guarantee transitive absence; P12.7 explicit cleanup evidence. Not language-semantic persistence |
| Contracts, canonical hashes, freeze reports/tags — canonical persisted evidence | repository/human reviewer; intentional provenance preservation | CER evidence, SHR identities; retention intentional and versioned | Git objects/source hashes/report bytes | Frozen reports/ancestry stack; no incidental PID/temp path equality requirement |

Inventory completeness is **False** for a repository-wide ownership/lifetime claim: major backend boundaries are identified, but transitive OS/compiler descendants, consumer-held snapshots, aggregate cache/metadata custody and exceptional resource measurements remain unresolved. This is not evidence of a leak. Frozen lifecycle ABI evidence is reused separately from executable v1 evidence.

## Performance census

[performance_baseline.py](../../apexforge/tooling/performance_baseline.py) already measures project load, validated project build, internal execution and total with perf_counter_ns, default one warmup/five measured samples, min/median/mean/max, fixed fixture ordering and advisory-only output. [P11.1A test](../../apexforge/p11_1a_performance_baseline_smoke_test.py) is existing infrastructure, not a new native benchmark. Its project fixtures and authority setup cannot be relabeled native-v1 workloads.

| Requested timing | Current evidence / minimum future observation |
| --- | --- |
| End-to-end latency | P11 pipeline total exists; P12 wrapper duration can be externally timed from admission through cleanup. Report retention and cleanup included/excluded explicitly |
| Validation/planning | P11 validated build aggregates work; AIRVerifier, plan builder and association boundaries callable separately. No authoritative native phase samples |
| Lowering | admission and _source/emitter boundaries visible; externally observed seam timing must include repeated validations or label their exclusion |
| Compilation | build_native includes discovery/hash work and compiler/linker. Distinguish discovery from subprocess build; no compiler-only benchmark currently recorded |
| Native dispatch | dispatch_native includes readmission/hash lock/launch/wait/decode. Child-only duration needs OS evidence, not total relabeled as child time |
| Managed execution | P11 internal execute; P12 RuntimeEngine and execute_managed_retained separable. Report context creation/validation/retention overhead separately |
| Repeated execution | P12.5/6/7 repeat correctness exists; not a timed continuity series |
| State/store scaling | Native maximum tested at 256 states/4096 stores; no latency curve |
| Trace/metadata scaling | Existing count/limit tests; no byte-cost or overhead curve |
| Cold/warm | P11 explicit warmups; native chain rediscovers/hashes tools for each build. New process, fresh directory, reused issued image and repeated full build are different conditions. OS cache coldness cannot be inferred from directory novelty |

P12.7 unittest/smoke elapsed times establish invocation duration only; setup, compilation, assertions and scheduling are mixed. They are not trustworthy performance closure thresholds or backend speed comparisons. No applicable frozen native performance threshold was found. Missing phase/pressure sampling is infrastructure/evidence work, not a demonstrated performance defect (G01/G02).

## Security census

Reusable defenses: exact closed-schema admission before side effects; canonical principal/directive/owner transport checks; authority-bearing native programs rejected; current-process issuance only; deterministic receipt binding AIR/routing/source/options/tools/image; digest recheck under read-only sharing lock through exit; shell=False artifact dispatch, explicit cwd, minimal SystemRoot/WINDIR environment and closed stdin; exact result length/type; timeout failure; no semantic fallback. Tool discovery alone uses a generated batch wrapper and validated installation string, and strips ambient CL/_CL_/LINK/_LINK_ overrides. That is an intentionally separate trust surface from artifact dispatch.

P12.6 rejects stale source/AIR/plan/mapping/context/policy/producer/order/result/image/receipt/output associations. It captures provenance before dispatch and after dispatch before cleanup; post-cleanup snapshot validation reads no deleted image. Reusing an artifact still re-admits inputs and verifies issuance/image; a stale receipt cannot import an arbitrary executable into a new process. Native CanonicalExecutionResult remains trace-free; observation failures preserve owner results and do not rewrite semantic success/failure.

Limits needing explicit review (G03/G04/G05): trusted build-root access/ownership is a precondition, not a newly proven ACL guarantee; no general untrusted persistent-artifact admission or remote signing; subprocess environment/discovery buffers and compiler descendants need lifecycle accounting; cancellation/cleanup denial outcomes lack repeated fault-pressure evidence. Resources retained as evidence can outlive an execution/principal context intentionally, but must not authorize another execution. Native v1 has principal identity but no authority grants/revocation semantics: revocable authority lifetime cannot be tested by adding unsupported grants. Context validation in managed retention detects mismatched policy/state; it does not define external credential expiry. Resource reuse does not inherently extend authorization, and no incorrect extension was directly demonstrated. Do not characterize these qualifications as exploits or implementation defects.

## Memory/resource census

Python-managed allocations, native child/compiler resources, files, CLR build/runtime resources, logical retained metadata and canonical persisted evidence are separate accounting domains. A Python allocation sample cannot establish child memory bounds; a deleted executable cannot establish no leaked handle; a record cap cannot establish a byte cap; a canonical hash cannot justify retaining a large graph forever.

Known bounds are specific: native 256 states/4096 stores/decisions, wire output ≤2048 bytes; tooling default source 4 MiB and record limit 10,000 (positive configured values capped at 16 MiB numerically); native timeouts ≤300 seconds; legacy ABI registry 64 slots. Source generation produces one region per initial state/store and one emitted output per state. These do not bound MSVC memory, all metadata string bytes, cumulative caller-retained results, cache history, or owner allocations before post-execution retention checks.

Resource production repeats verification, serialization, mapping and digest work in association/build/dispatch validation. It preserves owner authority but increases temporary allocation opportunity; no cost or defect follows without measurement. Weak issuance ownership and scoped files/handles are credible lifecycle mechanisms, not measured plateau guarantees. Cache invalidation is content/dependency governed, not an aggregate budget or background eviction service. User-retained old immutable collections can legitimately keep old values alive. G03–G07 distinguish lifecycle/aggregate-bound/measurement needs.

## Reproducibility census

| Product | Reused evidence | Reconstruction qualification / missing evidence |
| --- | --- | --- |
| Semantic final result | P12.7 complete sorted typed named projection repeated twice; native acceptance repeats outputs/results | Expected invariant with same admitted AIR/default state; separate process IDs/temp paths irrelevant. Broader graph universe remains sampled |
| AIR fingerprint | Canonical air_to_dict transport, sorted JSON keys, compact separators, uppercase SHA-256 | Same exact ordered AIR content reconstructs; declaration reorder can legitimately change AIR hash despite equal final state |
| Metadata/mapping/trace fingerprint | P12.6 repeated immutable identities and portable logical source labels; stale association negatives | Same source/logical labels/AIR/plan/context/producer sequence required. Changing governed logical source name or policy is not incidental |
| Generated C | Deterministic admitted literal/store emission; source mapping determinism tests | Same admitted content/order; emitter excludes physical build paths; no general source-to-machine-address correspondence |
| Native image bytes | P12.5 independent build directories compare full PE bytes, same recorded toolchain; /Brepro compile/link | Local identical-toolchain evidence only. Tool version/library/companion DLL or options changes may legitimately change bytes |
| Build receipt | Repeated receipt equality; receipt excludes build paths/time and binds source/options/tool hashes/image | Equality conditional on identical bound inputs/tools/image. Not a cross-toolchain invariant or remote authenticity proof |
| Execution receipt/evidence | Native evidence reuses build receipt plus output fingerprint/canonical result; P12.6 pre/post association | No invented independent receipt schema. Native result.input_fingerprint binds receipt; therefore varies legitimately when receipt does |
| Freeze artifacts | Versioned contracts/reports/source hashes and tag identities | Git contents reconstruct identically; observations, elapsed time and report prose need not be rerun into identical bytes |

Changed temporary paths are directly represented by independent local native builds and wrapper cleanup/rebuilds; temporary paths are excluded from receipts/portable identities. PID/time/thread identity exclusion is inspected/tested in P12.6 contracts, not a full matrix of freshly sampled OS identities. A clean-machine P12.6 transitive-stack PASS proves that transferred candidate passed there, not equal PE bytes across machines. P12.6 recorded managed same-path clean rebuild DLL equality; do not extrapolate it to path-independent CLR/PDB bytes. P12.7-4's local stack PASS and earlier Application Control blocks coexist.

Future matrix (G08): repeat same process; new process; fresh build roots; clean worktree of same source; separate Windows machine with identical tool hashes; separate machine/toolchain with different hashes. Require semantic/AIR invariants where input contracts match, check portable metadata identities under same logical content, and make image/receipt equality conditional on identical toolchain and build contract. Record toolchain-different variants as provenance variation, not semantic drift. No universal cross-machine/native-byte reproducibility claim yet.

## Determinism census and Sovereign Stability Set

The **P12.8 Sovereign Stability Set** is an engineering label for the following existing identities; canonical repository structures remain named as before.

| Identity | Invariant under incidental resource cycling? | Legitimate variation |
| --- | --- | --- |
| Verified AIR transport fingerprint | Yes for exactly identical verified content/order | Different program/declaration order/content/version |
| Directive identity | Exact canonical ID survives rebuild | Different entry/reference/product |
| Principal/authority identity | Same governed program/context; native v1 preserves sole principal | Changed grants/policy/roles in supported managed domains; native authority-bearing domain excluded |
| Execution plan/routing | Yes for same AIR, exact entry, owners and governed routing | Changed dependency closure/owner/entry; object identity irrelevant |
| Semantic final result | Same admitted execution/input context; sampled three-path proof reused | Different initial state/program/context; error/environment may prevent result |
| Required provenance chain | Same roots/associations must validate through release/reconstruction | Toolchain/image/source/logical-label/context changes require new associations; not necessarily equal receipt hash |
| Profile identity | Exact frozen v1 string | Different supported profile would require separate authorization; none introduced |

Deterministic canonical serialization uses sorted keys but preserves semantically relevant tuple/sequence order. Registry binding sorts owner IDs and binds exact entry/AIR. Native lowering preserves stores including overwritten stores and output declaration order; final comparison sorts complete returned names without reordering operations. Metadata locators bind AIR content and producer correspondence. Trace records retain family, ordinal/duplicates and producer order; no fabricated global chronology. Runtime diagnostics are sorted in the inspected return path; native infrastructure errors have stable codes independent of details. P12.6 complete/partial retention policy is explicit and does not silently truncate.

Semantic determinism is separate from artifact reproducibility. Toolchain/image receipt changes can change native result input fingerprints without changing projected final state. Resource limits can cause visible observation/infrastructure failure; they must not be normalized into semantic equality or hidden success. The inspected owners have no branch selecting assignment semantics from measured pressure, but no empirical pressure-invariance series proves all failure/ordering behavior. Cleanup is structurally scoped; OS locks/policy can vary its outcome. Required cleanup success/residue must be tested, not declared deterministic across all environments (G09/G10).

## Existing P12.5–P12.7 evidence reused

| Evidence | Already established within its limits | Reuse, without duplication |
| --- | --- | --- |
| [RCV-54](../../apexforge/p12_5_rcv_54_native_execution_acceptance.md), [RCV-55](../../apexforge/p12_5_rcv_55_execution_completion_review.md), native profile/acceptance tests | Seven profile tests; thirteen acceptance tests, actual execution, I64 extrema, Unicode and profile maximum; repeated full PE/receipt/output/result equality; live substitution/lock tests; injected process/build faults | Preserve contract; add pressure/lifetime conditions only where stronger evidence needed |
| P12.6-3 metadata suite | Immutable identity, source/AIR/plan associations and stale rejection | Use original negatives/validators; no new association schema |
| P12.6-4 mapping suite | Bounded source→AIR and admitted AIR→generated-C correspondence, deterministic emission, explicit unmapped coverage | Count/size existing maps; do not infer spans/machine addresses |
| P12.6-6 trace suite | Typed family/producer ownership, repeat/ordinal identity, stale scope/result/receipt/image negatives | Preserve exact sequence and portable identity; no replay evaluator |
| P12.6-8 integration suite | Exactly-once execution, result neutrality, visible limits and partial coverage, pre/post capture, wrapper cleanup and validation after cleanup | Extend repetition/resource observation, retaining owner_result on observation error |
| [P12.6-10](P12_6_10_FULL_CLOSURE_REGRESSION_FREEZE_READINESS.md) | Integrated security/determinism/lifecycle review, original Application Control failures, subsequent unchanged clean-machine RCV-51/50 PASS | Reusable architecture/cross-machine validation evidence; not universal byte or policy stability |
| P12.7-2/3/4 | Nine sampled three-path fixtures twice, full typed state/success, native no-fallback traps, four outside-domain cases | Keep equivalence oracle/strict projector; no new semantic logic |
| P12.7-4 current regression record | 4/4 equivalence methods; 63/63 successful predecessor methods across six suites; nine adjacent smoke scripts; RCV-51→50 with 46 recovery/25 predecessor script gates and managed builds/runs | Historical executed evidence, counts separated by layer; no summing nested gates as independent coverage |
| P12.7-4 cleanup and failure record | 150 newly generated files removed from 18 verified directories; no final generated residue; one temporary-exe access-denial trace failure then unchanged retry PASS | Evidence of cleanup at that gate, not a sustained leak test. Exact lock/policy cause was not established |

Windows Application Control is a real environmental constraint, not something to weaken: P12.5/6 record managed load blocks (0x800711C7); later clean-machine/current P12.7 runs passed unchanged. P12.7 recorded no Application Control block in its actual stack. Reuse neither erases failures nor substitutes another machine's PASS for a required current failing gate.

## Scale A/B/C measurement design — not implemented

### Scale A — execution

Start from a verified admitted fixture and named roots. Snapshot baseline parent resources and root inventory; record entry/exit durations around existing validation, planning, lowering/mapping, discovery/build, dispatch, retention and cleanup. Treat inclusive times as nested, not additive independent work. Observe actual child/tree lifetimes and OS peaks where a supported collector exists; mark missed/unsupported samples. Inventory source/object/image/capture footprint before deletion; count traces/maps/receipts/results. Observe after cleanup and after releasing caller-retained objects. Compare original owner projection and governed identities, excluding timings/paths/PIDs from semantic equality.

Peak evidence must state sampling interval, parent/child scope and collector overhead; sampled maxima are lower bounds if short-lived children were missed. Count process creation independently from simultaneous process count. Do not insert production hooks or change frozen code to obtain phase metrics without a later approved implementation slice. External wrappers/test adapters can label coarse boundaries; exact internal timing may remain unavailable.

### Scale B — continuity

Repeat identical full wrapper executions in one process with fresh temporary children and separately repeat dispatch of a deliberately retained issued image. Also use fresh parent processes to separate module/allocator warmup from cumulative live objects. Keep an explicit retention ledger: no retained results; a fixed-size retained window; intentional all-result retention only as a separately labeled experiment. Reuse vs rebuild of compiler/cache/plan products is another labeled mode.

Collect M_r coordinates and latency per cycle, warmup and post-cleanup/release snapshots, plus semantic/provenance validation. A bounded cache rise followed by plateau can be authorized. Monotonic retained growth requires tracing to owner/purpose/lifetime before calling it a leak; intentional retained windows and allocator reserved memory are not equivalent to live unauthorized objects. Require root residue checks each cycle; verify children reaped and weak issuance entries disappear when artifact references end. Distinguish normal reference release from optional explicit GC diagnostics; do not mandate artificially forced GC as runtime correctness.

No iteration count, plateau tolerance, memory budget or performance threshold is imposed here. Future evidence must declare sample count, stabilization rule and noise treatment before drawing conclusions. A semantic drift or unowned residual resource is never explained away by warmup.

### Scale C — supported load

Vary states within 1–256, total assignments and singleton decision count within 1–4096, decision-reference order, admitted repeated overwrites, and identical repeated executions. Keep one directive/principal, I64 literals/set_int, and empty ordered actions. Validate every fixture with existing native admission before measurement. Include min/max and interior points using frozen canonical fixture construction; source-language compilation remains a separate supported managed exercise if it produces native-ineligible actions.

Metadata volume scales by actual emitted regions (states+stores) and supported producer records within existing RetentionLimits. Do not append fabricated traces or expand native semantics to increase size.

| Quantity | Expected growth supported by inspection | Qualification |
| --- | --- | --- |
| Wire output/result state rows | Linear in state count, bounded by 256 / 2048 wire bytes | Result object byte size has representation overhead |
| Generated initialization/store regions | Exactly states+stores; output statements proportional to states | Source bytes also depend on literal digit length; not a compiler-memory claim |
| Native lowering sequence storage | One initial per state / ordered store per assignment | Whole admission/verification/mapping runtime complexity not established |
| Legacy ABI registry storage | Fixed 64 slots | Separate lifecycle profile, not executable state capacity |
| Repeated full-build filesystem residue | Expected zero wrapper-owned build children after successful cleanup | Exception/denial coverage and actual measurements still required |
| Cache/retained result footprint | Bounded only by chosen caller workload/retention policy where defined; otherwise unknown | No universal collection capacity found |
| Compiler memory, phase latency, deep trace/metadata bytes | Unknown | Mapping searches/revalidation and toolchain work prevent unjustified whole-pipeline linear-time claims |

## Gap matrix

Every row has exactly one classification from the requested vocabulary. No implementation defect was directly demonstrated by this documentation census. A blocking entry means evidence needed before the corresponding P12.8 closure claim, not that P12.8-1 cannot produce a census.

| ID | Finding | Classification | Blocking status / minimum disposition |
| --- | --- | --- | --- |
| G00 | Existing semantic authority, frozen admission and sampled equivalence remain sound within reviewed bounds | NO_GAP | Reuse and preserve; no production change indicated |
| G01 | No backend M_r collector / parent-child peaks / lifecycle sample series | MEASUREMENT_GAP | Blocks measurable pressure claims; add external observation foundation |
| G02 | Native phase, repeated/cold/warm and supported-load latency evidence absent | PERFORMANCE_EVIDENCE_GAP | Blocks performance closure; extend existing advisory methodology, no thresholds yet |
| G03 | Major owners known, but downstream custody/exception cleanup/compiler-descendant lifetimes not fully evidenced | RESOURCE_LIFECYCLE_GAP | Blocks complete lifecycle claim; ledger plus focused release/fault observations |
| G04 | Aggregate trace/result/cache/discovery capture bytes and workload-churn budgets not established | RESOURCE_BOUND_GAP | Blocks bounded-resource claims for those surfaces; measure before choosing a cap/change |
| G05 | Trusted-root/toolchain and resource-vs-authority lifetime review not demonstrated under stronger continuity conditions | SECURITY_EVIDENCE_GAP | Blocks that security closure claim; defensive review/tests within frozen trust boundary |
| G06 | Cache/session invalidation correctness does not establish a sustained retained-byte plateau | RESOURCE_BOUND_GAP | Blocks warm-cache bound claim; fixed workload and explicit snapshot custody experiments |
| G07 | Python, OS child, CLR, logical metadata and filesystem accounting not jointly attributed | MEASUREMENT_GAP | Blocks aggregate attribution; separate domain counters rather than one memory total |
| G08 | Clean-worktree/new-process/cross-machine controlled product matrix incomplete | REPRODUCIBILITY_GAP | Blocks broader reconstruction claims; toolchain-conditioned matrix |
| G09 | Repeated resource cycling/load not joined to semantic/provenance/ordering checks | DETERMINISM_GAP | Evidence gap, not observed nondeterminism; blocks pressure-invariance claim |
| G10 | Actual fault/timeout/cleanup-denial continuity and full P12.8 integrated regression absent | REGRESSION_COVERAGE_GAP | Blocks final current-branch closure; run focused additions then authoritative stack |
| G11 | Windows policy/access locks may block generated executable/managed load or cleanup | ENVIRONMENTAL_CONSTRAINT | Conditional run blocker; preserve diagnostics, normal prerequisite setup, no policy bypass |
| G12 | examples/P11Validation/apexforge.json absent at HEAD and worktree | HISTORICAL_CONTRACT_BLOCKER | Blocks universal historical harness PASS; existing supplemental policy keeps it separate from current gate |
| G13 | Native authority-bearing/wider AIR and ordinary nonempty-action compiler fixtures unsupported | NATIVE_PROFILE_LIMIT | Non-blocking for bounded P12.8; no profile expansion |
| G14 | Native per-operation/machine-address/intermediate debug trace absent | DEFER_TO_P13 | Non-blocking for final-state/resource evidence; debugger scope not entered |
| G15 | Receipts cannot import persistent binaries or provide hostile-process/remote signature security | NATIVE_PROFILE_LIMIT | Non-blocking within trusted process/profile; preserve qualification |
| G16 | Separate-machine stack PASS and local repeated builds do not establish toolchain-independent PE equality | REPRODUCIBILITY_GAP | Non-blocking for conditional byte claim; blocks any broader byte claim |

G01–G10 are closure evidence work; their surfaces should be scoped, measured and reviewed before deciding whether any production correction is needed. G11 is an environmental execution constraint. G12 remains a recorded historical contract blocker under `RECORDED_NOT_WEAKENED_NOT_USED_AS_CURRENT_BRANCH_CLOSURE_GATE`; it cannot waive a new failure. G13–G15 are exclusions, not bugs to fix during P12.8. G16 requires qualified claims rather than unconditional binary equality. No found rise is labeled a leak.

## Regression/freeze census

Final P12.8 validation must preserve the authoritative layers below. Avoid rerunning them now: reports and code were consistent enough to establish a census, and suites can generate tracked reports/artifacts.

1. P12.5 native profile contract (7 methods), then native acceptance NativeTests (13). Select NativeTests without the acceptance script report-writing main to preserve tracked RCV-54 JSON, as P12.7-4 did.
2. P12.6 metadata identity (8), source/native mapping (11), trace provenance (12), controlled integration (12), plus newly authorized P12.8 focused resource/security/reconstruction checks. Do not aggregate nested coverage counts misleadingly.
3. P12.7 bounded equivalence (4 methods, sampled cases), preserving strict full-state projection, owner result and no-fallback guards.
4. Adjacent AIR verifier/linker, runtime state, authority, causal, registry linked execution, P12.1E result determinism, P12.2C lowering seam and P12.2D plan binding. Include P11 performance/cache operational/session/reuse gates when new observations exercise them.
5. Unchanged RCV-51 invokes RCV-50; verify terminal markers for 46 recovery and 25 predecessor script selections, three managed project Release build/run gates, provenance/security/semantic-authority and frozen ancestry. Normal restore prerequisites precede --no-restore gates; no substitute script counts or policy bypass.
6. Historical supplemental harness policy: report the absent fixture and fail-fast unexecuted remainder if invoked; never claim whole historical PASS or recreate fixtures solely to pass.
7. Generated native/build/probe/bin/obj/PDB/cache inventory and scoped cleanup, preserving baseline and tracked files; final worktree/index integrity, source/evidence hashes, unchanged frozen tag identities and required ancestry. No broad destructive cleanup or automatic freeze action.

What P12.8 must add beyond P12.5–P12.7: measured ownership-attributed resource use, normal/fault release evidence over repetition, explicit cache/retention plateau analysis, native phase/load timing, a conditioned reproducibility matrix, and simultaneous stability/provenance assertions under those conditions. Predecessors prove mechanisms and sampled correctness, not these sustained operating conditions. Full regression/freeze closure remains a future human-reviewed evidence gate; no release or tag is authorized.

## Minimum recommended P12.8 sequence

Derive work from gaps rather than require production work in every pillar:

1. **Recommended P12.8-2: resource-observability and ownership evidence foundation.** A test/tooling-only scoped adapter/report contract for M_r, monotonic latency, normal lifecycle inventory and baseline/post-cleanup snapshots. Separate Python/OS/CLR/files/logical counters, report unavailable/missed data, exclude incidental identity from semantic hashes, reuse existing admission/result/provenance validators. Resolve major custody ambiguities and demonstrate observer neutrality on a small admitted fixture. No threshold, optimization, new evaluator, runtime dependency, profile change or debugger work.
2. Use that foundation for bounded continuity/load and fault-release evidence, combining the security resource-lifetime review with explicit cache/result retention modes. Prioritize G03/G04/G05/G06/G09/G10; only measured incorrect behavior justifies a separately scoped production fix.
3. Reuse those observations for conditioned reconstruction and native phase/performance scaling. Combine reproducibility/determinism checks with the same fixtures rather than duplicate semantic tests. Resolve G02/G08/G16 with calibrated claims; do not invent cross-toolchain equal bytes.
4. Integrated evidence review and focused-then-authoritative regression/cleanup/ancestry run. Report remaining exclusions and historical/environmental failures, and present to the human reviewer without automatically freezing.

Only P12.8-2 is a concrete recommended next slice; later grouping/naming depends on its evidence. This does not invent symmetric implementation milestones for all six pillars. Tests, measurement and documentation are the default where current implementation is already supported.

## Explicit exclusions and unresolved assumptions

- No production implementation, optimization, grammar/AIR/runtime/CLI change, second semantic engine, semantic replay, MSC dependency, scalar pressure score or invented measurement.
- No native-profile expansion, action stripping, persistent artifact importer, new authority-bearing native support, exploit development, signing/policy weakening, native debug symbols/instrumentation or P13 debugger scope.
- Trusted installed tools/build roots/current Python issuing process remain frozen assumptions. Concurrent/adversarial in-process execution, external credential expiry and compiler descendant guarantees are not established by this census.
- No universal memory bound, leak-free declaration, performance threshold, exhaustive equivalence, cross-toolchain binary reproducibility or historical full-regression PASS.
- No staging, commit, tag, push, release, outside-repository file inspection or automatic P12.8-2 work.

## Evidence-supported boundary values

```text
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_8_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P12_8_MSC_SEMANTIC_ENGINE=False
P12_8_MSC_RUNTIME_DEPENDENCY=False
P12_8_RESOURCE_PRESSURE_SCALAR_REQUIRED=False
P12_8_RESOURCE_OWNERSHIP_MODEL_REQUIRED=True
P12_8_NATIVE_PROFILE_EXPANDED=False
P12_8_P13_DEBUGGER_SCOPE_ENTERED=False
P12_8_PRODUCTION_IMPLEMENTATION_STARTED=False
P12_8_RESOURCE_LIFECYCLE_INVENTORY_COMPLETE=False
P12_8_MEASURABLE_RESOURCE_SURFACES_IDENTIFIED=True
P12_8_EXISTING_SECURITY_EVIDENCE_REUSABLE=True
P12_8_EXISTING_REPRODUCIBILITY_EVIDENCE_REUSABLE=True
P12_8_EXISTING_DETERMINISM_EVIDENCE_REUSABLE=True
P12_8_CLOSURE_GAPS_CLASSIFIED=True
P12_8_1_CAPABILITY_CENSUS_COMPLETE=True
```

The final value denotes the requested census deliverable, not completion/freeze of P12.8. Inventory False preserves the unresolved custody/OS scope above; reusable True values are bounded by attributed prior evidence and qualifications.

## Preservation and validation record

Changed files: exactly one new document, this path. Production/tests/fixtures unchanged; no execution tests run because this slice changes no behavior and contradictory evidence did not require a suite rerun. Documentation checks cover required sections/boundaries, relative references, whitespace and repository integrity. There is no fresh regression PASS claim. Risks/remaining work are the gap matrix and recommended future scope.

Post-write checks verified branch/HEAD and peeled freeze remain `p12-8-backend-closure` / `e25b98699098f9b3d61d1478c42ea27b54aea78f`. Tracked worktree and index diffs are empty; tracked and untracked no-index whitespace checks reported no whitespace errors. Git's LF-to-CRLF warning did not change document bytes. All Markdown file references resolve, and all required boundary values are present. Sole untracked path / verified exact status:

```text
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
```

Stop at P12.8-1; no P12.8-2 work has begun.
