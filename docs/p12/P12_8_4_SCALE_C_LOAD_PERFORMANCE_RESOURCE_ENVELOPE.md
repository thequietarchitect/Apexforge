# P12.8-4 — Scale C Load Scaling and Performance/Resource Envelope

## Baseline and scope

Branch `p12-8-backend-closure`; HEAD and peeled predecessor `afp-p12.7-freeze`:
`e25b98699098f9b3d61d1478c42ea27b54aea78f`. Initial tracked and staged diffs were empty;
six incoming P12.8 candidates were hashed before implementation. This candidate adds
only the Scale C test and this evidence document. Production semantics and the observer
remain unchanged. This is review evidence, not final closure, freeze preparation or P13.

The canonical AIR runner supplies every expected final-state projection. The managed
path is retained RuntimeEngine execution, not independent .NET execution. Native builds
and dispatch are real; RuntimeEngine.execute is prohibited during native lifecycles.

```text
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_7_THREE_INDEPENDENT_EXECUTORS_CLAIM=False
P12_7_DOTNET_INDEPENDENT_EXECUTION_PROVEN=False
P12_8_MSC_SEMANTIC_ENGINE=False
P12_8_MSC_RUNTIME_DEPENDENCY=False
```

## Confirmed frozen domain and fixture construction

Live `native_backend/native_execution_contract.py` admission requires the exact
`apexforge.native.win-x64.i64-literal-state-set/v1` profile: 1–256 explicit INT states,
1–4096 total literal set_int stores, signed I64 values [-2^63, 2^63-1], one directive,
one principal, 1–4096 decisions, one path per decision, max_weight policy, and each
decision referenced exactly once by the directive. Actions, emits, effects and
invocations are empty. Events, checks, requirements, authorities, roles, functions and
workflows are empty. Native admission also requires exact owner/routing association
and revalidation of verified AIR; state/decision counts alone do not guarantee admission.
Individual paths may contain no stores provided the program has at least one store.
Identifiers are validated and bounded; this is not a universal bound on all metadata strings.

The test derives programs with dataclasses.replace and the existing P12.5 fixture and
with_path helper. State declarations are deliberately reversed; names are portable,
initials and assignments are deterministic signed-I64 literals. Existing principal,
directive and singleton path structure are preserved; no causal actions are stripped.
No independent set_int evaluator exists in the harness.

Primary points are 1, 8, 32, 64, 128 and 256 states, with one store per state. Secondary
points hold eight states fixed: the primary eight-store baseline and 128 stores. This
separates store pressure from state pressure without expanding admission. The
4096-store contractual limit is inspected, not claimed as a measured secondary load.
The joint 256-state/4096-store pressure corner and exhaustive state/store combinations
are not measured. Maximum-scale PASS below refers to the primary state dimension,
with 256 stores. This preserves the census's bounded qualification.

## Observational method and timing boundaries

The unchanged P12.8-2 observer supplies immutable snapshots, ownership, counts,
existing canonical byte lengths, monotonic elapsed measurements, filesystem inventory,
Windows current-process readings, opt-in Python allocation readings, deltas and DBLs.
No metric is a semantic evaluator or fallback.

Each configuration has one warm-up plus five measured canonical executions and one
warm-up plus five measured managed-retained executions. Three sequential native
samples each perform a fresh real build and dispatch. Expected results are obtained
before measuring; retained validation and projection assertions follow the timed
canonical/managed owner call. Context/runtime construction is included in the managed
timing. Timing is descriptive, never a pass/fail latency threshold.

Native compiler timing wraps the existing subprocess.run with a plain passthrough
function, counting only the cl.exe call including link. Dispatch timing wraps the real
dispatch_native owner (admission, custody/hash checks, launch, decoding). It is not
machine-code-only execution time. Neither wrapper retains call arguments or substitutes
outputs. Build-owner timing includes mapping generation/validation, tool discovery,
hashing, compilation and receipt issuance. Total native time includes build, retained
dispatch/validation, inventories, assertions, filesystem cleanup and ticket release.
These inclusive timings overlap and must not be added as a phase partition.

One separate preparation probe includes construction, verification, planning, admission
and plan association. One separate lowering probe times the existing source/mapping
emitter. They are untraced, single observations, not repeated statistical phase samples;
high-level build/dispatch owners repeat some of that work. Pure internal validation,
planning-only and machine-code-only timing are unavailable without deeper instrumentation.

Python tracemalloc is restricted to one additional bounded canonical probe per
configuration; before-current, after-current and peak are recorded. It is stopped before
measured loops. Subsequent Python-memory readings are explicitly unavailable, never
zero. Windows working set, lifetime peak working set and handles are recorded throughout.
All live metrics and elapsed time are volatile and excluded by the observer from
deterministic snapshot identity. Peak working set is cumulative for the current process,
not a per-scale isolated peak or a compiler-child reading.

## MSC ownership and continuity lens

MSC is an engineering vocabulary: Mnemo-Pressure is the vector `(Wp,H,At,Tb,Cb,Pc)`;
Narrative Pulse is validate → plan → lower → build → dispatch → retain → cleanup;
DBL is a test-owned release boundary; SSV describes surviving semantic/provenance identity.
There is no scalar score, runtime dependency, semantic layer, debugger or quantum claim.

| Class/surface | Owner and purpose | Lifetime and release evidence |
| --- | --- | --- |
| IRR generated C/image/obj/discovery command | Test-owned fresh child root; one admitted build | Child TemporaryDirectory exits after dispatch/validation; parent entries and files/bytes return to empty |
| DHF mapped/retained wrappers | Sample scope; association and semantic validation | Local references explicitly released; weak issuance ticket disappears |
| DHF issuance table | Existing native weak-key table; artifact authorization | Entry exists only while artifact ticket is reachable; sample restores original count |
| DHF process readings | Current test process; aggregate observations | Process lifetime; individual allocator/OS constituents remain unresolved |
| DHF numeric evidence ledger | Test configuration; descriptive comparisons | Bounded declared sample count; no retained live execution objects |
| CER evidence | This review document and existing canonical receipts/forms | Intentional evidence retention; not treated as ephemeral artifact residue |
| SHR continuity identities | Existing AIR/routing/profile and provenance contracts | Reconstructed and checked independently of incidental paths and allocation identity |

No persistent compilation/discovery cache participates in the inspected path. Toolchain
discovery and hashing recur per build. OS/Python/library retention is not inferred to be
a backend-owned cache. Aggregate OS growth does not prove unauthorized retention.

## Semantic, deterministic and cleanup criteria

Each configuration reconstructs identical AIR twice, comparing canonical transport/form,
fingerprint, routing, emitted C bytes, mapping fingerprint and canonical semantic
projection. All measured canonical and managed runs preserve raw canonical state-key
ordering; complete canonical/managed/native typed projections must agree. AIR, routing
and mapping identities legitimately vary across different workloads; repeated identical
construction and execution must preserve them. Directive/principal/profile identities
remain the same across configurations. Native receipts bind AIR, routing, entry and
profile; retained association validators run before and after physical cleanup.

Before DBL each fresh child has generated C and a real native image. Artifact inventory
uses the observer's authorized-root containment and link/reparse rejection. After DBL,
the child is absent and the parent has no entries, zero files and zero bytes. Three
fresh roots per configuration have identical residue fingerprints and artifact/metadata
structural quantities. Tickets disappear without forcing GC or deleting canonical
evidence. This is bounded deterministic custody evidence, not a universal leak proof.

Tb uses existing mapping/result canonical forms and receipt JSON plus operation,
region, trace-record and association counts. Managed trace carriers have no exposed
canonical textual form: their byte size is unavailable; no substitute serialization is
invented. Receipt bytes describe retained logical evidence, not an extra on-disk file.
Cb here observes issuance count restoration, not a cache manufactured by the harness.
Wp/H remain observational; Pc and artifact custody provide deterministic release evidence.
These are hand-built AIR fixtures: native mapping uses the existing UNMAPPED_SOURCE
association, with AIR-operation/generated-C region correspondence rather than a
language-source correspondence claim. Artifact sizing covers the selected owned build
roots, not every compiler-internal allocation, pipe or file-backed dispatch capture.
Native image sizes are compared; this stage does not newly prove cross-machine image
byte reproducibility. Frozen predecessor evidence and its qualifications remain intact.

## Diagnostic classifications and limitations

An initial diagnostic exposed TEST_FIXTURE_DEFECT: timing MagicMocks retained argument
history and hence an artifact ticket. Replacing them with plain passthrough functions
removed the test-created owner. No observer or backend implementation was changed.
Interrupted exploratory runs left test-owned temporary roots (TEST_INVOCATION_DEFECT:
external interruption bypassed normal Python cleanup); those exact resolved roots were
removed only after checking containment within this repository's build directory.
No interrupted/failed run contributes to the final statistics.

Full-lifecycle allocation tracing was unnecessarily expensive for retained metadata
validation. The final fixture bounds it to the canonical probe and keeps the secondary
experiment at 128 stores. This changes observational scope, not semantic admission or
sample counts at any final selected point. It provides no defect or performance-budget claim.

Remaining MEASUREMENT_GAP: compiler/linker child peak memory and handles; the observer
only measures current process. Pure internal phase timing and managed trace canonical
bytes are also unavailable. Remaining RESOURCE_BOUND_GAP: no aggregate parent/child
working-set, Python allocator, handle or artifact-byte budget is supplied by admission.
Empirical maxima below cannot become contractual ceilings. PERFORMANCE_EVIDENCE_GAP:
no frozen acceptance budget, isolated cold-process matrix or repeated phase probes.
Separate-machine/toolchain reproducibility and final determinism/security/freeze closure
are outside this stage. No implementation defect is claimed from volatile growth.

Contractual controls include state/store/decision/I64 and profile admission limits,
native exact output size 8 bytes/state (maximum 2048), zero stderr, finite-positive
timeouts at most 300 seconds (build default 60; dispatch default 10), and existing
retained evidence limits (default source bytes 4 MiB, records 10000). These are separate
controls, not a total lifecycle latency/memory budget. Tool discovery has existing
30/60-second invocation timeouts. Output/retention checks do not cap every allocation
made before validation. Managed/canonical general execution is not newly resource-bounded.

## Measured results and verification

Final measurements, regressions, preservation hashes and evaluated markers follow below.

## Final Scale C measurements

Seven configurations passed. Each row has five measured canonical and five managed runs,
plus three fresh native builds/dispatches: 35/35/21 measured runs in total. The focused
suite ran four test methods in 1104.011 seconds. Warm-ups, separate probes and identity
reconstruction are additional untimed/sample-excluded work. All three-path projections,
raw canonical/managed ordering, receipt associations and no-fallback assertions passed.

All timing values below are milliseconds (nanosecond observations divided by 1,000,000).

| States | Stores | Timed scope | Samples | Minimum ms | Median ms | Maximum ms |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | canonical | 5 | 0.090800 | 0.109900 | 0.468900 |
| 1 | 1 | managed-retained | 5 | 2.769200 | 2.878500 | 2.900800 |
| 1 | 1 | compiler | 3 | 97.474900 | 118.236100 | 148.289800 |
| 1 | 1 | dispatch-owner | 3 | 84.687300 | 102.489600 | 104.656800 |
| 1 | 1 | native-build-owner | 3 | 2151.388700 | 2665.739400 | 2858.005700 |
| 1 | 1 | native-total | 3 | 2310.513500 | 2890.095200 | 3097.859400 |
| 8 | 8 | canonical | 5 | 1.054300 | 1.151300 | 1.621100 |
| 8 | 8 | compiler | 3 | 103.975700 | 131.067500 | 188.854800 |
| 8 | 8 | dispatch-owner | 3 | 91.617000 | 110.237200 | 128.554300 |
| 8 | 8 | managed-retained | 5 | 25.451100 | 27.324700 | 28.683800 |
| 8 | 8 | native-build-owner | 3 | 3065.904900 | 3388.230100 | 3980.006700 |
| 8 | 8 | native-total | 3 | 3704.044400 | 4019.364800 | 4640.692600 |
| 32 | 32 | canonical | 5 | 6.151800 | 6.568100 | 8.348200 |
| 32 | 32 | compiler | 3 | 124.185500 | 134.514200 | 145.084500 |
| 32 | 32 | dispatch-owner | 3 | 112.940400 | 120.073100 | 145.724000 |
| 32 | 32 | managed-retained | 5 | 79.093000 | 82.480300 | 88.187100 |
| 32 | 32 | native-build-owner | 3 | 3172.197800 | 3416.407700 | 4034.592700 |
| 32 | 32 | native-total | 3 | 7225.830700 | 8001.193600 | 8092.082700 |
| 64 | 64 | canonical | 5 | 19.641500 | 21.430200 | 22.771400 |
| 64 | 64 | compiler | 3 | 150.935900 | 159.848000 | 192.116500 |
| 64 | 64 | dispatch-owner | 3 | 124.811100 | 160.246900 | 162.554300 |
| 64 | 64 | managed-retained | 5 | 147.648400 | 152.028800 | 165.352700 |
| 64 | 64 | native-build-owner | 3 | 4725.084400 | 4792.954700 | 4897.338000 |
| 64 | 64 | native-total | 3 | 18375.073800 | 18885.018900 | 19112.875600 |
| 128 | 128 | canonical | 5 | 68.322900 | 74.033600 | 77.312500 |
| 128 | 128 | compiler | 3 | 109.474300 | 118.609100 | 126.774300 |
| 128 | 128 | dispatch-owner | 3 | 161.214900 | 206.919500 | 1382.660300 |
| 128 | 128 | managed-retained | 5 | 328.973200 | 332.132500 | 355.332900 |
| 128 | 128 | native-build-owner | 3 | 9707.872600 | 9774.491900 | 9808.156800 |
| 128 | 128 | native-total | 3 | 62154.226100 | 62677.248800 | 63005.378900 |
| 256 | 256 | canonical | 5 | 264.890100 | 272.556600 | 308.140800 |
| 256 | 256 | compiler | 3 | 122.955900 | 138.068300 | 138.487500 |
| 256 | 256 | dispatch-owner | 3 | 202.158100 | 208.212100 | 891.839500 |
| 256 | 256 | managed-retained | 5 | 755.627900 | 768.167300 | 787.957300 |
| 256 | 256 | native-build-owner | 3 | 29949.050500 | 29957.468500 | 30369.419900 |
| 256 | 256 | native-total | 3 | 231569.274000 | 235304.272100 | 238969.921100 |
| 8 | 128 | canonical | 5 | 10.671600 | 11.344600 | 16.276500 |
| 8 | 128 | compiler | 3 | 121.252300 | 157.655700 | 181.126500 |
| 8 | 128 | dispatch-owner | 3 | 127.925700 | 140.907600 | 889.507400 |
| 8 | 128 | managed-retained | 5 | 160.524900 | 172.336900 | 223.537300 |
| 8 | 128 | native-build-owner | 3 | 4676.187700 | 4683.003300 | 5137.460200 |
| 8 | 128 | native-total | 3 | 17640.312600 | 17660.081400 | 19168.389300 |

Single, untraced probes; these overlap work included in high-level native owners:

| States | Stores | Construction/verify/plan/admission/association ms | Source/mapping emission ms |
| --- | --- | --- | --- |
| 1 | 1 | 1.319200 | 1.461100 |
| 8 | 8 | 11.910600 | 30.669200 |
| 32 | 32 | 33.146500 | 293.342100 |
| 64 | 64 | 64.013600 | 903.514400 |
| 128 | 128 | 106.089300 | 3389.376500 |
| 256 | 256 | 216.026800 | 13015.768500 |
| 8 | 128 | 51.502300 | 833.632400 |

Artifact bytes and counts are identical across the three fresh native scopes at each
configuration. Other products are the directly owned object and discovery command;
receipt bytes are logical retained JSON, excluded from the on-disk total.

| States | Stores | Files | C files | C bytes | Image bytes | Other bytes | Total owned bytes | Receipt bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 4 | 1 | 757 | 2560 | 1607 | 4924 | 4516 |
| 8 | 8 | 4 | 1 | 1170 | 2560 | 1873 | 5603 | 4600 |
| 32 | 32 | 4 | 1 | 2660 | 3584 | 2971 | 9215 | 4888 |
| 64 | 64 | 4 | 1 | 4676 | 4608 | 4475 | 13759 | 5272 |
| 128 | 128 | 4 | 1 | 8821 | 7168 | 7483 | 23472 | 6040 |
| 256 | 256 | 4 | 1 | 17514 | 11776 | 13499 | 42789 | 7576 |
| 8 | 128 | 4 | 1 | 3195 | 3584 | 2953 | 9732 | 4600 |

| States | Stores | Operations / regions | Mapping canonical bytes | Managed trace steps / records | Native evidence records | Native associations |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 2 / 2 | 897 | 7 / 7 | 1 | 3 |
| 8 | 8 | 16 / 16 | 4494 | 14 / 14 | 1 | 3 |
| 32 | 32 | 64 / 64 | 16974 | 38 / 38 | 1 | 3 |
| 64 | 64 | 128 / 128 | 33724 | 70 / 70 | 1 | 3 |
| 128 | 128 | 256 / 256 | 67444 | 134 / 134 | 1 | 3 |
| 256 | 256 | 512 / 512 | 135451 | 262 / 262 | 1 | 3 |
| 8 | 128 | 136 / 136 | 37414 | 134 / 134 | 1 | 3 |

Managed collection count is four and managed plan-association count one at every point.
Native result-evidence canonical form is 137 bytes at every point; it is not a dump of
all state outputs. Managed trace canonical bytes remain unavailable.

Windows current-process readings and bounded Python probes (all byte units):

| States | Stores | Working-set sampled range | Final working set | Maximum lifetime peak reading | Handle sampled range | Python current before → after | Python probe peak |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 33861632–34648064 | 34648064 | 50221056 | 162–168 | 98214 → 118626 | 120228 |
| 8 | 8 | 34664448–35389440 | 35389440 | 50782208 | 168–168 | 11068 → 27376 | 28978 |
| 32 | 32 | 35614720–38617088 | 38617088 | 53731328 | 168–168 | 11068 → 22856 | 65922 |
| 64 | 64 | 36352000–38621184 | 38379520 | 53731328 | 168–168 | 11068 → 27123 | 116997 |
| 128 | 128 | 36859904–38383616 | 38133760 | 54116352 | 168–168 | 11068 → 33544 | 232914 |
| 256 | 256 | 37965824–41885696 | 41324544 | 56942592 | 168–168 | 11644 → 44360 | 449690 |
| 8 | 128 | 40366080–41324544 | 40710144 | 56942592 | 168–168 | 11068 → 46552 | 176362 |

All final owned roots returned to files=0, bytes=0 and entries=0. All 21 samples
restored issuance count 0→0 and released their weak ticket. Deterministic residue
fingerprint was `84DC5952DF22BECB1FA1DD95A48B8679A47383C6137E0461300CA64E5490E1FB`
at every point, including each maximum-state sample. No deterministic residue growth
was observed. Handles stabilized at the sampled value 168 after initial library activity;
aggregate working set fluctuated. Neither sequence is used for a leak conclusion.

## Empirical growth and acceptance boundary

For primary 128→256 states/stores, generated C grows 8821→17514 bytes (1.985×), mapping
67444→135451 bytes (2.008×), and total owned artifacts 23472→42789 bytes (1.823×).
C and mapping bytes are approximately proportional over the larger tested points;
fixed overhead and image/object alignment are visible in total bytes and small points.
Mapping operation/region counts are exactly states+stores in these fixtures. The
per-state C bytes decline from 757 at one state to 68.414 at 256; mapping bytes/state
at 32/64/128/256 are approximately 530.44/526.94/526.91/529.11.

Over 128→256, median canonical execution grows about 3.68×, managed-retained 2.31×,
native build owner 3.06×, and full retained native lifecycle 3.75× for twice the load.
These costs are super-proportional over that interval. Compiler medians are irregular
across the primary points (about 118–160 ms); fixed/toolchain/OS overhead dominates
that small sample. Dispatch medians increase overall but maxima contain substantial
variation. No asymptotic complexity, isolated cause or future latency bound is inferred.
The growing difference between inclusive lifecycle time and the compiler/dispatch
measurements warrants later targeted phase evidence; this stage does not optimize it.

With eight states fixed, 8→128 stores increases C 1170→3195 bytes, mapping 4494→37414,
operations/regions 16→136 and managed trace records 14→134. This is distinct store
pressure evidence; association counts remain fixed. Byte growth is sub-proportional
to the 16× store increase because state and fixed overhead remain. Observed maxima
are local empirical values, not contractual memory/artifact/performance budgets.

No frozen performance threshold was found or introduced. Timings do not establish
that the backend is fast enough, and this stage emits no performance acceptance claim.

## Focused and predecessor regression results

All were run sequentially with
`C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe -X utf8 -B apexforge/<suite>`.
The focused suite preceded regressions; none overlapped measured load executions.

| Exact suite | Methods | Duration seconds | Result |
| --- | --- | --- | --- |
| p12_8_4_scale_c_load_performance_resource_test.py | 4 | 1104.011 | PASS |
| p12_8_3_execution_continuity_resource_pressure_test.py | 8 | 90.883 | PASS |
| p12_8_2_resource_observability_ownership_test.py | 19 | 7.984 | PASS |
| p12_7_2_bounded_behavioral_equivalence_test.py | 4 | 60.196 | PASS |
| p12_6_4_source_native_mapping_test.py | 11 | 12.028 | PASS |
| p12_6_8_controlled_trace_integration_test.py | 12 | 16.754 | PASS |

Total: 58 passing methods, no failures or skips in these final runs. The new suite's
two envelope methods contain seven measured configuration subtests. P12.6 suites were
included because source mapping and controlled trace-retention owner APIs are directly
reused. No full closure harness was run; historical-fixture closure remains outside scope.
P12.7's nine supported equivalence cases and four out-of-domain boundary cases retain
their original interpretation and limitations.

## Remaining gaps and scope boundaries

| Classification | Remaining evidence | P12.8-4 disposition |
| --- | --- | --- |
| MEASUREMENT_GAP | Compiler/linker child peak resources, pure internal phase timings, managed trace canonical byte size | Explicitly unavailable; does not invalidate selected-root cleanup or measured owner timings |
| RESOURCE_BOUND_GAP | Aggregate process/Python/child memory, handle and artifact-byte budgets; lifecycle-wide bound | Empirical readings are not contractual ceilings; requires later closure decisions |
| PERFORMANCE_EVIDENCE_GAP | Frozen speed acceptance budget, isolated cold/warm matrix, exhaustive/joint-max pressure combinations | No speed acceptance claim; sampled envelope only |
| REPRODUCIBILITY_GAP | New resource/timing envelope on separate Windows machines or toolchains | Existing predecessor evidence reusable within its original scope; no new cross-machine claim |

No semantic/backend implementation defect was observed under tested inputs. No observer
correction was necessary. The diagnosed test-fixture/invocation issues were resolved
before final measurements. No working-set or handle leak is claimed; no unauthorized
deterministic residue growth was observed within selected sample scopes. These results
do not establish universal absence of leaks, full security/resource-lifetime closure,
full determinism/reproducibility closure or backend performance acceptability.

## Preservation and exact Git status

Before implementation and after final regressions, SHA-256 values matched:

| Incoming candidate | Preserved SHA-256 |
| --- | --- |
| apexforge/tooling/resource_observability.py | BDAA6A4CCBB24B8122FA1CA658134F2741EB13926AC5940A70D186A3EBB92D54 |
| apexforge/p12_8_2_resource_observability_ownership_test.py | 473D57CB22C32141C72A1F0A673B8746891A62CEA7932BEF3CC97E26767C9769 |
| apexforge/p12_8_3_execution_continuity_resource_pressure_test.py | 638EBFB10A6DD6CCA11E097CAEE171FC69CA50792A28D2F0337F7BCC8E1A003E |
| docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md | CE792211422D0F3242D97474B918F71E35FBFD2965225814F10DFF7C158C02FB |
| docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md | 12CDC7BE19E72B6D656EC28936D5CC45365C3DD2CB08D28FBB8EB86CA810A071 |
| docs/p12/P12_8_3_EXECUTION_CONTINUITY_RESOURCE_PRESSURE_VALIDATION.md | D414ED0A3543AF70C203D30372AD358F29A2E5ACF346BDC5958CCD640E4D6988 |

Branch, HEAD and peeled freeze remain the baseline stated above. Tracked diff and cached
diff are empty. Repository scans found no native executable/DLL/object/PDB, pyc or
bin/obj/__pycache__ residue; build has zero entries. Nothing was staged, committed,
tagged or pushed. Only the two requested P12.8-4 candidate files were added. No final
backend closure, freeze preparation, security/resource-lifetime next stage or P13 began.

`git status --porcelain=v1 --untracked-files=all`:

```text
?? apexforge/p12_8_2_resource_observability_ownership_test.py
?? apexforge/p12_8_3_execution_continuity_resource_pressure_test.py
?? apexforge/p12_8_4_scale_c_load_performance_resource_test.py
?? apexforge/tooling/resource_observability.py
?? docs/p12/P12_8_1_BACKEND_CLOSURE_CAPABILITY_CENSUS.md
?? docs/p12/P12_8_2_RESOURCE_OBSERVABILITY_AND_OWNERSHIP_FOUNDATION.md
?? docs/p12/P12_8_3_EXECUTION_CONTINUITY_RESOURCE_PRESSURE_VALIDATION.md
?? docs/p12/P12_8_4_SCALE_C_LOAD_PERFORMANCE_RESOURCE_ENVELOPE.md
```

## Evidence-supported markers

```text
P12_8_SCALE_C_LOAD_VALIDATION=PASS
P12_8_MINIMUM_SCALE=PASS
P12_8_INTERMEDIATE_SCALE=PASS
P12_8_MAXIMUM_SUPPORTED_SCALE=PASS
P12_8_THREE_PATH_EQUIVALENCE_UNDER_LOAD=PASS
P12_8_NATIVE_NO_FALLBACK_UNDER_LOAD=PASS
P12_8_PERFORMANCE_SCALING_MEASURED=True
P12_8_PERFORMANCE_THRESHOLD_DEFINED=False
P12_8_PERFORMANCE_ACCEPTANCE_CLAIM=False
P12_8_ARTIFACT_PRESSURE_MEASURED=True
P12_8_TRACE_METADATA_SCALING_MEASURED=True
P12_8_VOLATILE_MEMORY_SCALING_OBSERVED=True
P12_8_RESOURCE_PRESSURE_SCALAR_USED=False
P12_8_MAX_LOAD_CLEANUP=PASS
P12_8_DETERMINISTIC_RESIDUE_GROWTH_OBSERVED=False
P12_8_NATIVE_PROFILE_EXPANDED=False
P12_8_SEMANTIC_AUTHORITY=CANONICAL_AIR
P12_8_CHILD_PROCESS_PEAK_RESOURCE_VISIBILITY=MEASUREMENT_GAP
P12_8_WORKING_SET_LEAK_CLAIM=False
P12_8_HANDLE_LEAK_CLAIM=False
P12_8_P13_DEBUGGER_SCOPE_ENTERED=False
P12_8_4_READY_FOR_REVIEW=True
```

Stop boundary: P12.8-4 candidate is ready for human review. No later stage is activated.
