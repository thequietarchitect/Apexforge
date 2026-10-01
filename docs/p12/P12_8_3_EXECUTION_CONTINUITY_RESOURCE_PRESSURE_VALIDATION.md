# P12.8-3 — Scale A / Scale B Execution and Continuity Resource-Pressure Validation

## Frozen baseline and scope

Validation on LYRA, 2026-09-30. Branch `p12-8-backend-closure`; HEAD and peeled `afp-p12.7-freeze` both verified as `e25b98699098f9b3d61d1478c42ea27b54aea78f`. Initial tracked and index diffs were empty. Exactly four incoming P12.8 paths were untracked. No generated bin/obj/__pycache__ directories or .pyc/.exe/.dll/.obj/.pdb files were found outside .git/node_modules.

Incoming SHA-256 preservation inventory:

| Path | SHA-256 |
| --- | --- |
| docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md | CE792211422D0F3242D97474B918F71E35FBFD2965225814F10DFF7C158C02FB |
| apexforge/tooling/resource_observability.py | BDAA6A4CCBB24B8122FA1CA658134F2741EB13926AC5940A70D186A3EBB92D54 |
| apexforge/p12_8_2_resource_observability_ownership_test.py | 473D57CB22C32141C72A1F0A673B8746891A62CEA7932BEF3CC97E26767C9769 |
| docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md | 12CDC7BE19E72B6D656EC28936D5CC45365C3DD2CB08D28FBB8EB86CA810A071 |

Only [the new continuity test](../../apexforge/p12_8_3_execution_continuity_resource_pressure_test.py) and this evidence document are added. No observer correction was needed. No frozen execution/semantic module, fixture, predecessor test, incoming P12.8 artifact or toolchain setting was changed.

Every Python test used exactly `C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe` with `-X utf8 -B`; interpreter verification returned Python 3.9.13, 64-bit. PowerShell wrappers checked `$LASTEXITCODE` and threw on failure; they used no `exit` statements. No alternate Python, restore, full closure stack, Scale C experiment, commit/tag/push or P13 work.

## P12.8-2 APIs reused

The exact [observer implementation](../../apexforge/tooling/resource_observability.py) was read before implementation. The new test reuses ResourceOwnership/OwnershipEvidence, ResourceClass, Measurement construction through observe_count/observe_bytes/unavailable, ResourceSnapshot ordering/fingerprint, inventory_artifacts, observe_current_process, observe_python_memory, elapsed, compare_snapshots, and LifecycleBoundary. No measurement, snapshot, delta, ownership, filesystem or Windows/Python-memory primitive was reimplemented.

Small test-local helpers compose those APIs, bind a fixed fixture to frozen owners, collect immutable pulse reports, and assert release. Pulse contains immutable measurements, scalar identity/projection/provenance tuples and snapshot values; it contains no live execution product, native ticket, callback or process handle. JSON emitted to stdout is a validation report, not a new trace/metadata canonical serialization or measured semantic representation.

The observer remains opt-in, tooling-only and non-semantic. Canonical AIR remains the sole semantic authority; execution belongs to the unchanged canonical/RuntimeEngine/native owners. MSC does not evaluate AIR or execute anything.

## Fixed fixture and domain

The unchanged P12.5 `fixture()`/`plan_for()` helpers supply P12.7's `repeated_overwrite_untouched` case: two INT/I64 states, two literal set_int assignments in a single singleton path, one directive/principal, empty ordered actions and no authority-bearing/native-ineligible surfaces. Default initial conditions are identical for each call. The canonical owner supplies the expected full typed named result; the existing P12.7 projectors are reused without another evaluator.

Profile: `apexforge.native.win-x64.i64-literal-state-set/v1`. Final projection in every measured execution:

```text
(True, ((state:unchanged, I64, 9223372036854775807),
        (state:value, I64, 42)))
```

There is no workload-size variation: same states, assignments, decision, entry and initial context throughout. No action stripping, native-profile expansion, source-language native executability claim or unsupported input normalization. Legacy AIR is authentically UNMAPPED_SOURCE. Canonical and managed-retained share RuntimeEngine and are not independent .NET execution.

## MSC lifecycle and ownership continuity

Engineering-only correspondences remain Mnemo-Pressure = multidimensional measurements; Narrative Pulse = one applicable `validate → plan → lower → build → dispatch → retain → cleanup` lifecycle; DBL = explicit release boundary; SSV = semantic/provenance content identities; IRR/CER/DHF/SHR = analytical retention labels.

The verified program, plan, binding and canonical oracle are deliberately retained as fixed test fixtures. Plans are prepared once and validated by frozen admission/association contracts; the report does not claim each pulse reconstructs a registry plan from scratch. Non-native paths have no native lowering/build/dispatch stages. Native pulses validate admission, lower/build a fresh image, dispatch it once, retain/validate provenance, remove the child scope, validate the retained snapshot, and release local owner products.

| Resource / class | Known owner + purpose + lifetime | Observed DBL / evidence |
| --- | --- | --- |
| Native build child and C/object/image/discovery script — IRR | Test-owned TemporaryDirectory; one fresh build/dispatch; one pulse through validation | Existing context-manager exit removes child. Image parent must be that new empty child; after exit child does not exist |
| Result, retention wrapper, context/runtime and mapped artifact — DHF | Pulse function holds owner products for comparison/provenance; pulse-local lifetime | Explicit local reference release; weak witnesses show zero directly tracked live products, without forced GC |
| Native issuance entry — DHF | Frozen weak issuance table; admit current-process artifact; reachable ticket lifetime | Baseline 0, exactly one extra while fresh artifact is owned, back to baseline 0 after last mapped/ticket reference release |
| Prepared AIR/plan/context identity and result/provenance content — CER / SHR content | Test/reviewer preserves semantic reference and required identity; fixture/evidence lifetime | Never deleted by native artifact cleanup. Their content survives reconstruction/release of incidental wrappers |
| Pulse observation ledger — DHF | Sequence test holds bounded immutable reports for continuity comparison; declared sequence/test lifetime | Exactly 20 records for each canonical/managed round and 10 for native; intentionally retained, released with test references |
| Current process and Python tracing session — operational observations | Aggregate current Python process; constituent allocation/handle owners unresolved. Each sequence owns an opt-in tracing session if none already exists | Process readings copied, no handles retained. Tracing started/stopped in try/finally only by its test owner |

Each measured record has explicit owner/purpose/lifetime evidence. These fields establish custody of the selected resources, not ownership of every transitive Python/OS allocation. No persistent incremental/toolchain-result cache participates in these calls. The fixed verified plan and standard-library owner are intentional reused fixture/process products; no cache activity was manufactured. The process-local issuance table is the relevant retained native registry and is inspected through a test-only count/weak witness; only numeric observations enter snapshots.

## Scale A — individual execution results

Scale A ran one canonical, one managed-retained and one real-native execution. Pre/post current-process readings, full semantic projection, SSV and applicable trace/provenance observations were checked. Python tracing was explicitly disabled for Scale A and therefore unavailable, never zero.

| Path | Applicable structural evidence | Outcome |
| --- | --- | --- |
| Canonical AIR | Eight actual trace steps, zero diagnostics; direct result release witness | Same expected complete state/success and verified identities; PASS |
| Managed-retained | Eight trace steps, four family collections, eight retained records, eight interleaving references, one actual plan association | Context/result/trace association validated against canonical owner; PASS |
| Real native-retained | Real mapped build/dispatch, source/image/receipt/map/result sizes, native evidence and associations, explicit test-owned cleanup | All native execution owners live/unmocked; fallback trap never called; PASS |

Canonical/managed pulse reports have artifacts/residue set to absent rather than invented native filesystem metrics. Separate clean test-harness roots are checked by the continuity driver; that is harness custody evidence, not a claim that those paths emit native files.

Scale A current Python process working set/handles:

| Path | Working set before → after (bytes) | Handles before → after |
| --- | --- | --- |
| Canonical | 32,350,208 → 32,546,816 | 160 → 160 |
| Managed-retained | 32,624,640 → 32,665,600 | 160 → 160 |
| Native | 32,665,600 → 34,029,568 | 160 → 166 |

The native process-lifetime peak reading after Scale A was 48,967,680 bytes. This is the parent Python process peak, not the native child or compiler peak. The six-handle first-native increase is observed, not attributed to particular handles; subsequent measured sequences remained at 166. No handle or working-set leak claim follows.

## Scale B — counts and clean-root reproduction

Each path ran two consecutive sequences, each beginning with a fresh empty test-owned root. Native iterations were strictly sequential with no concurrent pressure activity. Each pulse follows `pre → execute → retained result → cleanup → post` and validates identities/results before discarding live products.

| Path | Round 1 | Round 2 | Total Scale B | Scale A + B |
| --- | ---: | ---: | ---: | ---: |
| Canonical | 20 | 20 | 40 | 41 |
| Managed-retained | 20 | 20 | 40 | 41 |
| Real native | 10 | 10 | 20 | 21 |

All required minimum counts were met without reduction or skip. New-stage measured executions: 103 (3 Scale A + 100 Scale B). These are execution counts, not unittest method counts, and exclude the separate fixed oracle setup and later predecessor executions.

For every repetition, projected state/success and SSV match the canonical reference; each path's provenance/fingerprint tuple and structural footprint match its first pulse. Every native build uses a fresh empty child, and native receipts bind the currently admitted AIR/routing/profile/entry and current mapped image. Native RuntimeEngine.execute is failure-trapped throughout real build/dispatch/retention; no fallback occurs.

After every pulse, weak witnesses show tracked result/retention/context/runtime/mapped wrapper references released. The native ticket is unreachable and issuance count is zero. No old mapped artifact or retained result is carried to the next pulse; reports retain measurements/content identities only. Equal content-addressed provenance across runs does not invent a unique temporal execution identity and is legitimate under frozen contracts.

Round 1 and round 2 ordered deterministic evidence tuples match exactly for each path, including projection, SSV, provenance, footprint snapshot fingerprint, release snapshot fingerprint and native artifact/residue snapshot fingerprints. Working set, peak, handle count, traced allocation values, elapsed time, absolute temp paths and PIDs are excluded. The driver also compares each actual harness-root post state to its empty baseline, including entry count to detect empty orphan directories.

## Resource-pressure vector observed

`M_r = (Wp, H, At, Tb, Cb, Pc)` remains multidimensional; no scalar weighting or combined score.

| Coordinate | Observed evidence | Limit |
| --- | --- | --- |
| Wp | Actual current/peak parent working set and opt-in Python traced current/peak | Volatile; not private commit, child/CLR memory, allocation attribution or an execution-specific sampled peak |
| H | Actual current-process Windows handle count before/after and per-pulse post sequence | No individual handle identity/owner or child handle accounting |
| At | Native child file count/bytes, .c/.exe footprint and existing receipt text bytes | Selected scope only; extensions establish size categories, not execution trust |
| Tb | Actual trace/record/collection/operation/region/association counts; existing native map/result canonical bytes | Managed Trace/TraceCollection have public fingerprints but no public canonical textual representation; bytes explicitly unavailable |
| Cb | Native live issuance count and intentionally retained bounded pulse ledger | No persistent cache workload; no deep/transitive retained-byte budget |
| Pc | Empty native root file/byte/entry baseline after each DBL; zero direct product witnesses and native ticket release | Normal successful scope/release only; no exceptional/cancellation/security stress matrix |

Builtin live memory/handle measurements are volatile. The full record preserves those readings; deterministic identity excludes them. A separate integrity test uses explicitly synthetic increases to verify that deltas do not generate leak/cleanup verdicts and that volatile changes do not change deterministic fingerprints. Synthetic values are not used as measured pressure evidence in any table here.

## Trace/metadata and generated-artifact footprint

The following structural values were constant across both rounds, with each path measured only where applicable:

| Measurement | Canonical | Managed-retained | Native-retained |
| --- | ---: | ---: | ---: |
| Owner trace steps | 8 | 8 | Not a native per-operation trace |
| Trace-family collections | Not retained | 4 | One native evidence collection |
| Retained producer records | Not retained | 8 | 1 native evidence record |
| Interleaving references | Not retained | 8 | Not applicable |
| Actual plan association count | Not attached | 1 | Included in the 3 plan/mapping/result associations |
| Native operation metadata / generated regions | Not applicable | Not applicable | 4 / 4 |
| Existing mapping canonical bytes | Not applicable | No compiler mapping attached | 1,417 |
| Existing native result canonical bytes | Not applicable | Not applicable | 137 |
| Existing receipt UTF-8 bytes | Not applicable | Not applicable | 4,536 |
| Trace canonical text bytes | Unavailable | Unavailable | No invented collection serializer |

The native 137-byte result canonical form is the frozen result fingerprint preimage (including payload fingerprint), not a claim of deep payload allocation size. Mapping bytes are supplied by the existing mapping.canonical_form. Receipt is existing build/dispatch evidence text; no new receipt schema or disk receipt is created.

Each real native child contained 4 files totaling 5,035 bytes, including generated C 824 bytes and native image 2,560 bytes; remaining footprint is the object/discovery script. Native emission/provenance owners validate trust, not the observer. Size/relative-file inventory was unchanged across dispatch while owned. Child deletion and root entry-count checks provide the cleanup criterion; no longer artifact retention was introduced for convenient measurement.

## DBLs and deterministic resource residue

DBL 1: native TemporaryDirectory child scope exits after real dispatch and live provenance validation. The same root before DBL legitimately contains files; LifecycleBoundary records arithmetic decreases after existing cleanup. Child path no longer exists, root files/bytes/entries are all zero. The outer sequence root remains intentionally present (`root_present=1`) until its own scope exits.

DBL 2: pulse-local result/context/runtime/mapped references are released after projection/provenance comparison. Weak witnesses and issuance count establish zero selected live pulse products/tickets without forcing GC. This establishes release of the directly witnessed wrappers; it does not exhaust their former transitive allocation graph or imply working set must drop.

DBL 3: the sequence test returns/releases its bounded report/temporary-root custody; tracing session is stopped by its owner in finally. Intentional canonical/provenance content remains in returned deterministic comparison tuples for the paired-round check and in this evidence document. Cleanup never targets CER/SHR source/evidence files.

Native post-cleanup state was identical for all 21 executions:

```text
files=0
total_bytes=0
generated_c_bytes=0
native_image_bytes=0
root_entries=0
root_present=1
live_pulse_products=0
issued_artifacts=0
```

Native post-cleanup residue snapshot fingerprint:

`2665015EEB12B7E32B6E4C4A989B45A6744A9A3BD8599C2F72EBE3101F61F538`

Structural footprint fingerprints:

- Canonical: `8278F068B2967C07AF0DAE771268E9C6B6D40DB786F97385E5CB933D4E531436`.
- Managed-retained: `A89FC75521A49AB9EA5079672E3AD3A1ECFD513DF8C0D0BF0F34795A199681E6`.
- Native-retained: `AA45BFB39BA14D6DEDE1B80332154F88375808EC72D73A49AADA6906FFA74A12`.

No deterministic residue accumulation or unauthorized monotonic retention was observed in these selected domains. The evidence ledger itself intentionally grows to the declared finite 20/10 records, with known test owner/purpose/lifetime. It is not falsely counted as a leaked runtime result or an unbounded cache. No universal leak-free assertion or live-memory plateau is established.

## Sovereign Stability Set

Same identities before/after and across every new-stage execution:

| Identity | Value / validation |
| --- | --- |
| Verified AIR transport fingerprint | E2BF031B6C1D82AC1FD83DAA1989A6F127EA3B286016479178A2115B3E96D77C |
| Directive | directive:main |
| Principal | principal:main |
| Routing/plan fingerprint | BB33622DD20CBDD9F1988CAB43D41CD020FC209BD28D5A130D3CC886F5BB7D0C |
| Native profile | apexforge.native.win-x64.i64-literal-state-set/v1 |
| PlanMetadata fingerprint / association root | 27F806257B38C010E889ECCF365065FD771C6EBBC9D77D7FB58C26A3BF265C45 |
| Semantic final result / success | Complete existing P12.7 projection above; True throughout |
| Required provenance | Frozen managed context/scope/result and native pre/post/receipt/output/result validators; per-path provenance tuples equal across repeats |

Observation did not change these content identities. Incidental temporary paths, object/ticket identities and timing legitimately change. Native receipts/result input identity remain equal here because the fixed source/toolchain/profile inputs match; no cross-machine or toolchain-independent binary reproducibility follows. Stale evidence is not substituted: current retained evidence is validated against the current binding/artifact, and prior live products/images are released before the next build.

## Timing summaries — descriptive only

Durations use the P12.8-2 elapsed facility. They include owner call, retained evidence/SSV validation, structural measurement and selected release work; native timing includes discovery/hash/build/dispatch/mapping and artifact cleanup. They exclude preliminary pre-reading/SSV setup, final live post-reading and outer driver's comparison/report/root checks. They are measured instrumented pulse durations, not pure engine/compiler latency. Scale B tracing is enabled while Scale A tracing is disabled, so cross-scale speed comparison is not justified.

| Scale / path / round | Count | Minimum (ms) | Median (ms) | Maximum (ms) |
| --- | ---: | ---: | ---: | ---: |
| A canonical | 1 | 1.2286 | 1.2286 | 1.2286 |
| A managed-retained | 1 | 6.3195 | 6.3195 | 6.3195 |
| A native | 1 | 2963.0165 | 2963.0165 | 2963.0165 |
| B canonical 1 | 20 | 9.0372 | 16.6481 | 22.8986 |
| B canonical 2 | 20 | 11.3314 | 16.88745 | 20.3552 |
| B managed-retained 1 | 20 | 96.0987 | 114.03385 | 183.4774 |
| B managed-retained 2 | 20 | 101.0375 | 107.33005 | 164.2036 |
| B native 1 | 10 | 3707.4092 | 3894.7167 | 4204.3525 |
| B native 2 | 10 | 3786.4467 | 3946.93825 | 4599.38 |

No threshold, regression budget, speed-acceptance claim, optimization or semantic conclusion from timing differences. Native continuity was not run in parallel; predecessor regressions began only after these observations completed.

## Volatile resource sequences and Python memory

All Scale B current-process readings returned available Wp/H. All owned Python tracing sessions returned available current/peak values. Each sequence starts a new bounded tracing session and stops it in finally; tracing excludes allocations that already existed when that session started, including retained comparison tuples from a prior sequence. This is Python-managed allocation evidence only.

| Path / round | Working set baseline → post-loop (bytes) | Peak working set post-loop | Python traced baseline current | Python traced post-loop current | Python session peak post-loop |
| --- | --- | ---: | ---: | ---: | ---: |
| Canonical 1 | 34,123,776 → 35,205,120 | 48,967,680 | 15,174 | 713,943 | 715,545 |
| Canonical 2 | 34,791,424 → 35,893,248 | 48,967,680 | 15,174 | 574,030 | 597,017 |
| Managed-retained 1 | 36,020,224 → 36,847,616 | 48,967,680 | 13,414 | 738,640 | 740,242 |
| Managed-retained 2 | 36,118,528 → 37,142,528 | 48,967,680 | 15,174 | 1,055,374 | 1,062,620 |
| Native 1 | 36,610,048 → 39,419,904 | 54,599,680 | 13,414 | 828,090 | 16,076,960 |
| Native 2 | 37,654,528 → 38,416,384 | 54,599,680 | 13,414 | 437,457 | 15,686,146 |

Post-cleanup working-set sequences in iteration order, bytes:

```text
canonical-1: 34152448,34152448,34234368,34234368,34234368,34299904,34349056,34377728,34439168,34676736,34676736,34742272,34775040,34906112,34906112,34938880,34975744,35061760,35205120,35205120
canonical-2: 34947072,34963456,35037184,35037184,35168256,35434496,35434496,35467264,35495936,35516416,35565568,35631104,35659776,35758080,35758080,35758080,35758080,35823616,35889152,35889152
managed-1: 36093952,36110336,36122624,36139008,36159488,36184064,36204544,36274176,36286464,36286464,36352000,36352000,36368384,36380672,36380672,36380672,36450304,36519936,36589568,36847616
managed-2: 36171776,36233216,36233216,36265984,36392960,36405248,36413440,36413440,36438016,36438016,36765696,36765696,36765696,36835328,36835328,36904960,36986880,37076992,37076992,37142528
native-1: 37650432,37797888,37949440,37998592,38080512,38146048,38211584,39088128,39391232,39419904
native-2: 38232064,38301696,38236160,38088704,38166528,38166528,38342656,38350848,38350848,38416384
```

Post-cleanup Python traced-current sequences, bytes (whole-process memory is not measured by these values):

```text
canonical-1: 68321,96208,123599,171726,196317,246684,273147,298106,346321,370152,418474,444730,469780,514731,531682,576633,592496,637511,653910,698861
canonical-2: 61165,76340,123571,140218,183249,203288,243532,255059,294970,306193,350736,361727,401685,412676,452169,463328,503015,513038,552923,562514
managed-1: 66730,91977,128514,179299,202492,233303,278336,297197,342230,359983,405016,422057,467090,310359,378600,447969,518984,587865,654558,723412
managed-2: 83731,150564,215941,273302,330663,396953,462666,519303,573976,622289,680010,721785,764031,806282,848263,890981,932958,984399,1007672,1043950
native-1: 193048,340784,437840,556062,626618,669162,711520,752484,793678,834150
native-2: 104117,150661,156447,197921,240870,281858,322234,362498,402826,443517
```

Post-cleanup parent peak working set was constant 48,967,680 in both canonical/managed rounds, and constant 54,599,680 in native round 2. Native round 1 peak sequence was `52092928,53760000,53948416,54038528,54165504,54231040,54231040,54448128,54448128,54599680` bytes. All post-cleanup handle sequences and Scale B baseline/post-loop handle values were exactly 166 (20/20 values in each canonical/managed round, 10/10 in each native round). No persistent directional accumulation was observed in this sample. The differing working-set/Python series are deliberately not reproducibility invariants or leak verdicts. Python current measurements include the known observation ledger and runtime/observer allocation behavior; attribution of every remaining byte has not been established. Reported peak readings are their owning process/session peaks, not sampled native/compiler peaks. The stdout reports emit per-pulse Python current/peak and parent peak sequences as well as these table summaries.

These observations are `VOLATILE_OBSERVATION`. Empty files/bytes/entries and released selected live owner products are `DETERMINISTIC_RESOURCE_RESIDUE` evidence. Rising volatile values alone do not negate the deterministic DBL result, establish a plateau, prove unauthorized retention, or prove a leak. Full allocation/handle ownership attribution remains missing evidence.

## Child-process visibility and security limits

The reused observer only supports current-process Windows metrics and traced Python allocations. It cannot measure compiler/linker/native-child peak memory or enumerate/reap entire process trees. No invasive process enumeration or new dependency was added. Child peak status remains MEASUREMENT_GAP for native execution; the uniform stdout capability-gap field does not imply a compiler child exists in canonical/managed paths. Deterministic artifact/ticket/product release evidence remains valid despite this visibility limit.

Existing trusted-root and trusted-toolchain boundaries are preserved. Observer lstat/containment and link/reparse rejection apply to these quiescent test-owned roots. No hostile namespace race, remote authenticity, authority-bearing native program, offensive exploit or external credential-expiry behavior is tested. Resource custody remains fixed throughout a pulse; cleanup targets only temporary native/test resources, never canonical evidence. Actual compiler/build/dispatch faults propagate rather than becoming a fabricated semantic success.

## Required coverage and regressions

Eight new unittest methods cover the twenty requested validation concerns through substantive per-pulse assertions: three Scale A paths; three two-round continuity sequences; explicit volatile-growth/no-verdict handling; and structural/immutable observer ledger checks. Every pulse asserts success/projection/SSV, explicit owner/purpose/lifetime, product release and provenance. Native pulses additionally assert actual artifacts before DBL, root/child baseline after DBL, issuance release and no fallback. Reproducibility compares both complete ordered deterministic sequences, not just the first result.

All commands used the exact LYRA Python with `-X utf8 -B`, direct script invocation:

| Suite | Result | Unittest duration |
| --- | --- | ---: |
| apexforge/p12_8_3_execution_continuity_resource_pressure_test.py | 8/8 PASS, exit 0, no skips | 91.823 s |
| apexforge/p12_8_2_resource_observability_ownership_test.py | 19/19 PASS, exit 0, no skips | 5.455 s |
| apexforge/p12_7_2_bounded_behavioral_equivalence_test.py | 4/4 PASS, exit 0 | 60.857 s |
| apexforge/p12_6_8_controlled_trace_integration_test.py | 12/12 PASS, exit 0 | 16.980 s |
| apexforge/p12_6_4_source_native_mapping_test.py | 11/11 PASS, exit 0 | 7.947 s |

Distinct selected methods: 8 new + 46 predecessor = 54 PASS. Later predecessor execution counts are not mixed into Scale A/B resource/timing observations. The mapping suite is additional because the new test directly uses mapped build, canonical mapping form and mapping/result provenance; other predecessor suites were not broadened without need. The four regression scripts ran independently after the Scale A/B suite completed; their possible overlap is not a native continuity concurrency experiment or performance measurement.

P12.7's nine repeated three-path positives and four native profile exclusions remained PASS. P12.6's ordering/trace/result/partial-limit/provenance/cleanup contracts remained PASS. No full RCV-51/50, historical harness or freeze-readiness run was performed. No tracked acceptance report-writing main was invoked.

### Failure classification

No test failure, count shortfall, skip, native fallback, Application Control failure, observer implementation defect or semantic/backend defect occurred. No code was changed after execution to obtain passing output. Initial/final empty generated-artifact rg searches use the normal no-match exit, not a test failure.

Unavailable managed trace text/child peaks are MEASUREMENT_GAP; disabled Scale A Python tracing is explicit unavailability by design. These do not fabricate zero. No implementation fix or architecture change was needed. The historical fixture/Application Control qualifications in P12.8-1/P12.7 remain preserved; this stage does not claim those broader issues are resolved.

## Remaining gaps

| Classification | Remaining evidence |
| --- | --- |
| MEASUREMENT_GAP | Child/compiler/linker/CLR/private-memory/thread peaks, deep retained-byte allocation/handle attribution, producer trace canonical text not exposed |
| RESOURCE_LIFECYCLE_GAP | Exceptional cleanup, cancellation, descendant ownership and consumer-retained graph custody beyond direct witnesses |
| RESOURCE_BOUND_GAP | No aggregate memory/cache budget, lifetime-byte bound, live-allocation plateau or churn study; intentional finite evidence ledger is known |
| PERFORMANCE_EVIDENCE_GAP | Instrumented pulse timings only; no phase-exclusive native timing, observer-overhead calibration, speed budget or supported-load curve |
| SECURITY_EVIDENCE_GAP | Broader resource-vs-authority lifetime review, malicious concurrent namespace and external authority expiry remain outside tested boundaries |
| REPRODUCIBILITY_GAP | Paired local clean-root structural evidence only; no clean-worktree/cross-machine/toolchain-conditioned matrix |
| DETERMINISM_GAP | This fixed supported fixture is stable; no exhaustive input, resource-exhaustion or broader profile pressure proof |
| NATIVE_PROFILE_LIMIT | Frozen v1 restrictions unchanged; compiler-source nonempty actions and authority-bearing native execution remain unsupported |
| ENVIRONMENTAL_CONSTRAINT | Future OS access, locking/policy/cleanup availability can vary despite successful current runs |

These results support the requested normal Scale A/B execution and continuity claims for selected deterministic surfaces. They do not justify a universal memory-leak-free assertion. Scale C and later stages require separately named authorization; none is started here.

## Evidence-supported markers

```text
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_8_MSC_ROLE=RESOURCE_CONTINUITY_ANALYTICAL_LENS
P12_8_MSC_SEMANTIC_ENGINE=False
P12_8_MSC_RUNTIME_DEPENDENCY=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
P12_8_SCALE_A_EXECUTION_OBSERVABILITY=PASS
P12_8_SCALE_B_CONTINUITY_VALIDATION=PASS
P12_8_RESOURCE_OWNERSHIP_CONTINUITY=PASS
P12_8_TEMPORARY_ARTIFACT_LIFECYCLE=PASS
P12_8_POST_CLEANUP_RESIDUE=PASS
P12_8_SEMANTIC_STABILITY_UNDER_REPETITION=PASS
P12_8_NATIVE_CONTINUITY_NO_FALLBACK=PASS
P12_8_TRACE_METADATA_PRESSURE_OBSERVED=True
P12_8_DETERMINISTIC_RESIDUE_GROWTH_OBSERVED=False
P12_8_UNAUTHORIZED_MONOTONIC_RETENTION_OBSERVED=False
P12_8_WORKING_SET_LEAK_CLAIM=False
P12_8_HANDLE_LEAK_CLAIM=False
P12_8_RESOURCE_PRESSURE_SCALAR_USED=False
P12_8_OBSERVER_SEMANTICALLY_PASSIVE=True
P12_8_NATIVE_PROFILE_EXPANDED=False
P12_8_SCALE_C_STARTED=False
P12_8_P13_DEBUGGER_SCOPE_ENTERED=False
P12_8_3_READY_FOR_REVIEW=True
```

PASS/True apply to this fixed-workload normal-boundary sample and reviewed deterministic evidence. False growth/retention observations concern measured artifact/issuance/direct-product domains; they do not deny unknown transitive allocations. Ready for review does not declare P12.8 complete, frozen or released.

## Preservation and final status

Final fail-closed checks verified unchanged branch/HEAD/peeled freeze and all four incoming hashes; empty tracked/index diffs; no generated bin/obj/__pycache__ or binary/cache artifacts; resolved document references; and clean tracked/new-file whitespace checks. Git emitted only LF-to-CRLF warnings, without rewriting bytes. Verified exact status contains the following six candidate paths, all untracked:

```text
?? apexforge/p12_8_2_resource_observability_ownership_test.py
?? apexforge/p12_8_3_execution_continuity_resource_pressure_test.py
?? apexforge/tooling/resource_observability.py
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
?? docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md
?? docs/p12/P12_8_3_EXECUTION_CONTINUITY_RESOURCE_PRESSURE_VALIDATION.md
```

Only two new files for this stage. No staging, commit, tag, push, production semantic implementation, Scale C or P13 work. Stop after P12.8-3.
