# P12.8-2 — Resource Observability and Ownership Evidence Foundation

## Baseline and authorized scope

Validation date: 2026-09-30, LYRA. Branch `p12-8-backend-closure`. HEAD and peeled `afp-p12.7-freeze` both verified as `e25b98699098f9b3d61d1478c42ea27b54aea78f` before implementation. Initial tracked/index diffs were empty. Initial exact Git status:

```text
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
```

The existing [P12.8-1 census](P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md) was hashed before implementation and rechecked after tests:

`CE792211422D0F3242D97474B918F71E35FBFD2965225814F10DFF7C158C02FB`

This stage supplies an opt-in tooling/test foundation for observations and review. It does not establish pressure/stress, performance budgets, plateau criteria, leak conclusions, or full regression/freeze closure. Canonical AIR remains the sole semantic authority. The explicit P12.8 instruction governs the slice despite the stale P11.4A stage text in AGENTS.md; other authority/frozen-contract protections remain applicable.

## Existing facilities inspected and reused

Inspection preceded creation. Existing facilities were sufficient for owner execution and representation, but no general resource snapshot/delta/ownership helper was found in the inspected backend/tooling paths.

| Facility | Finding / reuse |
| --- | --- |
| tooling/performance_baseline.py | Existing P11 monotonic `perf_counter_ns`, warmups/samples and advisory timings. Its project pipeline is not a generic resource ledger; use the same standard-library clock, leave mature baseline unchanged |
| native_backend/native_execution.py | Frozen testable admission/build/dispatch APIs, receipt text, scoped wrapper temporary directories, file-backed capture and image lock. No observer hooks added |
| native_backend/source_mapping.py | Existing native mapping canonical_form, region tuples and caller-owned mapped-artifact API reused directly |
| tooling/trace_integration.py | Existing opt-in compiler/plan/managed/native retention, source bytes, owner trace collections, pre/post provenance and post-cleanup validation reused |
| tooling/debug_metadata.py and trace_retention.py | Existing immutable associations/trace record tuples and fingerprints. Count supplied tuples; do not invent carrier serialization |
| incremental_cache/operational.py and integration.py | Explicit collections/indexes/invalidation with caller/session custody; generic tuple count can observe collection entries later, without another cache implementation |
| Native lifecycle and managed ABI sources | Existing ownership/release mechanisms remain independent from the bounded executable path; no new integration |
| P12.5 fixture/plan helpers; P12.7 projectors | Reuse admitted legacy fixture and exact existing result projectors as test-only oracle/comparator |
| Generated artifact/cleanup evidence | Existing scoped temporary roots and P12.7 cleanup report retained. No reusable OS current-process or Python allocation resource collector found in inspected owners |

The new [resource_observability.py](../../apexforge/tooling/resource_observability.py) imports only standard-library facilities. It does not import AIR, runtime, workflow, native execution, subprocess, semantic validators or evaluators. Tests import execution owners independently. No existing production module imports this optional helper; no runtime requirement or external dependency was added.

Exactly two implementation/test paths are added, plus this report. The existing census remains unchanged. No grammar, AIR, runtime, CLI, compiler, metadata/trace implementation, native profile or frozen suite was edited.

## MSC analytical mapping and resource classes

The supported role remains `observe lifecycle → classify ownership → measure pressure → verify release → preserve semantic identity`. MSC is engineering vocabulary only, with no evaluator, AIR layer, literal quantum behavior, runtime dependency or substitute for returned OS evidence.

| Mapping | Foundation use |
| --- | --- |
| Mnemo-Pressure | Numeric measurements attributed separately to Wp/H/At/Tb/Cb/Pc |
| Narrative Pulse | Test-owned before/build/dispatch/after-cleanup observation around existing owner calls |
| Spatial Tensor of Recall | Explicit owner/purpose/trigger/lifetime/boundary declarations |
| Memory Potency Gradient | IRR/CER/DHF/SHR analytical class labels, not AIR types |
| Sovereign Stability Vector | Test checks governed identity before/after measurement and compares unobserved/observed native evidence |
| Decoherence Boundary Layer | Explicit LifecycleBoundary with before/after snapshots at test-owned directory release |
| Trigger-Topology Dynamics | Supplied evidence for creation/retention/release events; no scheduling or hooks |
| RCI-2 / continuity | Deterministic fixture inventories and unchanged semantic/provenance identity across incidental paths |

`ResourceClass` contains IRR (ephemeral), CER (canonical retained evidence), DHF (operational/reusable retained), and SHR (continuity invariant). All four are validated by record-construction tests. No repository object/type is renamed. A class declaration does not authorize retention or prove correctness. The central invariants remain:

`Resources may expand, contract, move, cache, and disappear; canonical semantic identity must not.`

`Retained Resource => Known Owner + Known Purpose + Known Lifetime`

## Ownership model

`ResourceOwnership` holds a portable logical scope, class and five immutable `OwnershipEvidence` fields: owner, purpose, trigger, intended lifetime and cleanup boundary. Each field explicitly distinguishes KNOWN (a nonempty supplied evidence value), UNKNOWN (unresolved with reason), and UNAVAILABLE (evidence inaccessible with reason). Unknown/unavailable values cannot contain a guessed identity. The observer does not discover ownership from path proximity.

Test caller custody is known because tests construct and explicitly retain/release these resources; semantic producer ownership remains with frozen modules:

| Observed resource | Owner/purpose evidence | Lifetime and boundary |
| --- | --- | --- |
| Controlled artifact tree and intentionally injected residue | Test creates exact files; footprint/containment verification | TemporaryDirectory test scope; intentionally recreated residue is reclaimed by outer scope |
| Actual native build directory/files | Test owns low-level build directory; native backend produces/validates contents | Test-owned TemporaryDirectory exit; low-level build API does not independently reclaim caller directory |
| Native receipt, mapping, result/provenance snapshots | Frozen producer owns meaning; test caller holds immutable returned evidence for comparison | Local test references, retained after directory deletion for validation; no permanent artifact retention |
| Compiler metadata and managed trace evidence | Frozen compiler/RuntimeEngine/tooling producers; test caller owns observed references | Test-local references; measurements capture lengths, not carriers |
| Current-process OS readings | Windows API reports aggregate current Python process only | Reading copied into immutable records; pseudo-handle never stored in snapshot. Individual resource owners inside the aggregate remain unresolved |
| Python allocation readings | Test explicitly owns tracemalloc session | Test starts/stops it in try/finally; helper never starts, clears or stops another owner's tracing |

Test fields identify the fixture purpose/custody rather than imply every transitively allocated object has been inventoried. No complete repository-wide lifecycle claim is made; the census's incomplete-inventory qualification remains.

## Measurements implemented

`Measurement` is frozen and validates scope/metric labels, explicit ownership, optional pressure coordinate, nonnegative exact integer values, one of bytes/count/ns, source text, availability and volatility. Booleans/floats/negative sizes, invalid names/units and fabricated numeric values for UNAVAILABLE are rejected. Unavailable means `value=None` with a reason, never zero.

| Primitive / vector surface | Actual behavior and boundaries |
| --- | --- |
| Elapsed time (outside vector) | `elapsed(ownership, started_ns)` takes a caller's perf_counter_ns reading and a new reading, returns nonnegative ns, rejects invalid/reversed inputs; volatile, no callback execution or threshold |
| Filesystem At / cleanup Pc | inventory_artifacts stats selected contained file/tree; sorted immutable relative path/size rows, files/total_bytes/generated_c_bytes/native_image_bytes/root_present observations |
| Python Wp | observe_python_memory requires explicit enabled=True and an already-active caller-owned tracemalloc session; current/peak traced allocation bytes. Disabled/inactive state explicit |
| Windows Wp | Current-process WorkingSetSize and PeakWorkingSetSize from GetProcessMemoryInfo through ctypes/psapi |
| Windows H | GetProcessHandleCount for GetCurrentProcess pseudo-handle; no PID argument/OpenProcess/content inspection |
| Native/build At | Selected test-owned tree provides .c bytes, .exe/.dll bytes and produced file counts; receipt UTF-8 bytes measured from existing receipt text, not an invented disk receipt |
| Metadata/trace Tb | observe_count counts supplied immutable tuples: trace steps, source-map entries, trace-family collections, existing association; observe_bytes sizes existing source bytes or mapping.canonical_form text |
| Retained/cache Cb | Structural tuple length, demonstrated with an explicit retained-result tuple; reusable for existing cache entries without implementing a cache or new serializer |

Extension-based .c/.exe/.dll sums are footprint categories only: existence/extension does not prove a valid generated program or authorize execution. Native owners separately verify the real artifacts. The helper never reads file contents, hashes executable content, dispatches observed files, or interprets receipts/traces/AIR.

Absent contained observation roots yield measured `root_present=0` and zero footprint only after authorized namespace validation establishes absence. Permission/I/O/special-entry failures discard partial rows and mark all inventory metrics unavailable. Path/link boundary violations raise ObservationPathError; no valid footprint is returned.

No `.NET` or native/compiler-child memory, process-tree enumeration, thread count, private commit, allocation attribution, sampling/peak collector, deep Python object size, aggregate cache-byte budget or per-operation native trace is implemented. Snapshot tuple counts are structural, not whole-process memory. Python traced peak is tracing-session-wide; Windows peak is process-lifetime-wide, not native-execution peak. The helper never resets those peaks.

## Snapshot, deterministic identity and delta

`ResourceSnapshot` contains only an ordered immutable tuple of Measurement values. Construction sorts complete attribution keys (scope/class/ownership, coordinate, metric/unit/source/volatility), rejects duplicate keys, and retains no caller carrier, mutable handle, live process, evaluator or callback.

Its canonical_form/fingerprint describe deterministic supplied observations only. Every volatile observation is excluded, including its availability/reason; snapshot equality still retains all readings. Consequently equal fingerprints do not mean equal live working sets or equal complete snapshots. Caller-created generic measurements must truthfully declare volatility; builtin time/OS/Python adapters always mark volatile. This is a tooling observation schema, not a language/semantic fingerprint.

`ArtifactInventory` additionally canonicalizes sorted relative path/size rows. Its fingerprint distinguishes file renaming even when aggregate snapshot totals match. Neither structural identity includes timestamps, physical absolute roots, PIDs or machine labels. Content hashes are intentionally not invented: equal path/size inventory does not establish equal file contents. Two unchanged controlled fixture observations produce equal inventory/snapshot identities.

`compare_snapshots` returns an immutable tuple of MeasurementDelta values. Matched available integer measurements yield an arithmetic difference and INCREASE, DECREASE or UNCHANGED; missing/unavailable measurements yield difference=None and UNAVAILABLE. Full attribution must match; changed ownership/unit/source creates separate unmatched rows rather than unsafe subtraction. Delta records validate their arithmetic. No positive delta is called a leak; no negative delta is called cleanup success.

## Lifecycle-boundary model

`LifecycleBoundary` supplies a named boundary, explicit ownership with known cleanup boundary, and before/after resource snapshots. Snapshot observations must belong to that declared ownership. The boundary exposes structural deltas, without a lifecycle verdict or semantic execution hook. Caller assertions establish that a required test-owned boundary has been crossed and which resources should disappear.

Tests observe a populated temporary tree, let its existing context manager remove it, then observe actual absence. An intentionally recreated residual file produces a positive byte footprint, proving residue detection does not silently normalize leftovers away. Native passivity testing uses the low-level artifact API in a test-owned scope and validates retained evidence after the image/root has gone; artifacts are not held beyond their declared test purpose.

## Path and security boundaries

- Callers must explicitly supply an absolute authorized root and absolute selected root; lexical parent traversal (`..`) and selection outside that authority are rejected before inventory.
- Every authorized-root ancestor is checked with lstat before traversing it; selected-root components and discovered entries are checked without following symlinks. Symlinks and Windows reparse entries, including junctions, are rejected. No resolve-through-link target access is used.
- Tests cover outside/relative/parent traversal, a real link or Windows junction, nested authority under a link, and the reparse attribute. The real link/junction test passed on LYRA without skips; it uses test-only setup and explicitly removes the link entry.
- The declared authority is a caller contract, not inferred permission or an OS access-control policy. Trusted, quiescent test-owned roots are required. lstat/scandir inventory is not an atomic sandbox against malicious concurrent path replacement; such inspection is unsupported. Hard links are not followed as directories and do not confer content trust; no contents are read.
- Arbitrary PIDs, unrelated process contents, child injection, executable file reads/launches, permanent instrumentation and telemetry are absent. Optional API/I/O failures cannot become valid zeros. Observation failure cannot change frozen owner semantics because owner execution is independent and the helper is optional.

The observer is intended for small explicitly bounded test roots. It performs stat/traversal and sorts finite rows; it has no timed threshold or scalability claim for arbitrarily large roots. No premature optimization or permanent production hook was added.

## Semantic-passivity evidence — real bounded native execution

The focused suite uses one unchanged P12.5 legacy fixture within `apexforge.native.win-x64.i64-literal-state-set/v1`. It executes a real unobserved native-retained wrapper baseline and a real observed mapped build/retained dispatch in a caller-owned directory. Native build/dispatch are not mocked. RuntimeEngine.execute is trapped only to prohibit fallback during both native calls; canonical oracle execution occurs outside the trap.

The observed call measures actual .c/image/file footprint, existing receipt/mapping bytes and region count, elapsed duration, optional current-process metrics, and explicit disabled Python tracing. It validates actual native retained provenance before and after directory removal. Both native executions have equal complete evidence, equal native retention fingerprints and matching full typed named state/success projection with the canonical owner. Native output is not calculated by the observer.

The test's before/after Sovereign Stability tuple remains unchanged:

- Verified AIR transport fingerprint.
- Exact directive ID and sole principal ID.
- Admitted routing/plan identity.
- Exact native v1 profile identity.
- Existing PlanMetadata association fingerprint.

It also checks native result/receipt/output/provenance equality and snapshot validation after cleanup. The builder's mapping canonical representation is supplied, never reconstructed by the observer. This proves passivity for that fixture under the tested measurement composition; it does not establish pressure invariance or exhaustive equivalence. The focused metadata/trace test additionally confirms retained managed evidence fingerprint remains unchanged after structural measurement.

## Windows observations and availability

Interpreter: `py -3.9`, Python 3.9.13, 64-bit; tests used `-X utf8 -B`. No interpreter/toolchain/policy changes or new package installation.

The final focused run returned the following actual current Python process readings, not thresholds or native-child peaks:

| Metric | Value | Availability |
| --- | ---: | --- |
| working_set | 31,911,936 bytes | available |
| peak_working_set | 32,321,536 bytes | available |
| handles | 163 count | available |

The first focused run also returned available readings (31,772,672 / 32,624,640 bytes; 163 handles); their variation is expected and excluded from deterministic identity. On unsupported platforms these adapters explicitly report unavailable, not zero. Tests permit unsupported/failed optional reads; this LYRA run actually returned all three metrics.

Fault-injection tests verify partial OS availability (available handle value 0 while memory unavailable), failed OS reads, filesystem permission failure, disabled/inactive Python tracing, and unavailability in snapshot deltas. Those are adapter-integrity fixtures, not hidden execution failures. The opt-in Python test owns its tracing session, observes current/peak values, verifies session remains active during observation, then stops it in finally. Existing tracing sessions would be left alone; none existed and no skip occurred.

## Focused and predecessor validation

Commands are direct script invocations with `py -3.9 -X utf8 -B apexforge/<file>`. No full closure/historical harness, stress loop, scaling curve, benchmark budget, restore or .NET build was run in this stage.

| File / selection | Result | Unittest duration |
| --- | --- | ---: |
| p12_8_2_resource_observability_ownership_test.py — initial run | 19/19 PASS, exit 0, no skips | 7.282 s |
| p12_8_2_resource_observability_ownership_test.py — final corrected run | 19/19 PASS, exit 0, no skips | 5.868 s |
| p12_6_3_metadata_identity_association_test.py | 8/8 PASS, exit 0 | 0.044 s |
| p12_6_4_source_native_mapping_test.py | 11/11 PASS, exit 0 | 8.525 s |
| p12_6_6_trace_provenance_reference_test.py | 12/12 PASS, exit 0 | 2.355 s |
| p12_6_8_controlled_trace_integration_test.py | 12/12 PASS, exit 0 | 18.212 s |
| p12_7_2_bounded_behavioral_equivalence_test.py | 4/4 PASS, exit 0; nine positive cases twice, four expected native limits | 61.439 s |

Final distinct selected methods: 19 new focused + 43 P12.6 + 4 P12.7 = 66 passing methods. The initial 19-method run is a separate attempt, not additional distinct coverage. Predecessor selections were launched independently after the corrected focused suite passed; durations include their normal assertions/setup and possible overlap, and are not performance comparisons.

Predecessors selected because their carriers, native fixtures/provenance and P12.7 projectors are reused directly. No P12.5 acceptance report-writing main was invoked, and no full RCV-51/50 stack was required by this additive observer. Current Windows reads succeeded; no native execution/Application Control failure occurred in these actual runs. Historical environmental/fixture limitations remain as recorded in the census.

### Failure/review classification before correction

There were no failing test methods in either focused run or selected predecessors. Review found and classified two new-tooling issues as IMPLEMENTATION_DEFECT before editing: initial authorized-root validation used resolve before link rejection, and a test labeled trace-family collection count as association count. Corrected ancestor lstat checks and separate collection/actual association counts; added nested linked-authority assertion, then reran all 19 focused methods. No semantic module correction, assertion weakening or fixture rewrite to conceal failure occurred.

Unavailable/permission/partial-reading cases are deliberate adapter fixtures with MEASUREMENT_GAP outcomes; a refused outside/link root is an expected defensive rejection. Platform-specific native execution is UNSUPPORTED_TARGET on non-Windows platforms and skipped there; it ran here. Empty rg generated-artifact searches use the normal no-match exit, not a regression failure. Escalated command execution was used because the prior stage established restricted-helper setup failure; no authority/security checks were bypassed.

## Remaining gaps and limitations

| Classification | Remaining work / limit |
| --- | --- |
| MEASUREMENT_GAP | No child/compiler/CLR/private-memory or thread attribution, sampled peaks, deep retained bytes, sampler interval or observer overhead study |
| RESOURCE_LIFECYCLE_GAP | Complete downstream ownership/custody and exceptional descendant/cleanup lifetime evidence remain outstanding |
| RESOURCE_BOUND_GAP | No aggregate cache/result byte budget, sustained plateau, authorized retention window or churn experiment |
| SECURITY_EVIDENCE_GAP | Trusted roots/tools remain assumptions; no malicious concurrent namespace guarantee, external authority-expiry policy or broader lifetime review |
| REPRODUCIBILITY_GAP | Controlled snapshots demonstrated, but clean-worktree/cross-machine/toolchain-conditioned reconstruction matrix remains future work |
| DETERMINISM_GAP | One-fixture passivity proved; semantic/provenance invariance under later pressure/continuity/load conditions untested |
| ENVIRONMENTAL_CONSTRAINT | OS availability, permissions, Application Control and cleanup locks may vary; optional absence stays explicit |
| NATIVE_PROFILE_LIMIT | Frozen native v1 only; no authority-bearing AIR, nonempty actions, persistent artifact imports or other platforms added |

The six-vector foundation does not mean all six coordinates were simultaneously fully measured on every execution. Current-process Wp/H, selected file At/Pc and structural Tb/Cb are distinct surfaces. CER/SHR labels are supported analytical evidence, not claims of completed freeze/persistence tests. P13 debugger/per-operation native tracing scope was not entered.

## Evidence-supported markers

```text
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_8_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P12_8_RESOURCE_OBSERVABILITY_FOUNDATION=PASS
P12_8_RESOURCE_OWNERSHIP_MODEL=PASS
P12_8_RESOURCE_CLASSES=IRR_CER_DHF_SHR
P12_8_RESOURCE_PRESSURE_VECTOR_SUPPORTED=True
P12_8_RESOURCE_PRESSURE_SCALAR_REQUIRED=False
P12_8_OBSERVATION_SEMANTICALLY_PASSIVE=True
P12_8_MEASUREMENT_SEMANTIC_ENGINE=False
P12_8_RUNTIME_DEPENDENCY_ADDED=False
P12_8_NEW_EXTERNAL_DEPENDENCY_ADDED=False
P12_8_PATH_OBSERVATION_FAILS_CLOSED=True
P12_8_UNAVAILABLE_METRICS_EXPLICIT=True
P12_8_LEAK_CLASSIFICATION_AUTOMATIC=False
P12_8_VOLATILE_METRICS_EXCLUDED_FROM_DETERMINISTIC_IDENTITY=True
P12_8_NATIVE_PROFILE_EXPANDED=False
P12_8_P13_DEBUGGER_SCOPE_ENTERED=False
P12_8_2_READY_FOR_REVIEW=True
```

PATH_OBSERVATION_FAILS_CLOSED covers tested static/quiescent namespace boundaries, not adversarial concurrency. PASS/READY_FOR_REVIEW are this foundation's evidence/review status, not a declaration of P12.8 closure/freeze/release. No Scale A/B/C pressure tests have begun.

## Repository preservation and exact status

Post-test inventory found no generated .pyc/.exe/.dll/.obj/.pdb products in the repository outside .git/node_modules; scoped test roots were reclaimed. No cleanup of pre-existing/source files was needed. All frozen tracked files and index remain untouched. Census SHA-256 matches baseline. HEAD and peeled freeze remain the expected commit; no staging, commit, tag, push or P13 work.

Final integrity checks verified empty tracked/index diffs, unchanged branch/HEAD/peeled freeze and census hash, resolved Markdown references, and all required markers. Tracked and untracked no-index whitespace checks reported no whitespace errors; Git's LF-to-CRLF warnings did not rewrite bytes. Verified exact four-path candidate status:

```text
?? apexforge/p12_8_2_resource_observability_ownership_test.py
?? apexforge/tooling/resource_observability.py
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
?? docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md
```

Stop after P12.8-2. Later pressure/continuity/load stages require a separately named authorized slice.
