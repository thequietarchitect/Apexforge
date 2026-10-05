# P15.4 — bounded deterministic simulation kernel

Review evidence only; final milestone authority remains with the owner.

## Baseline and preservation

Branch: `p15-1-domain-platform-contract-sdk`. HEAD and frozen P14 branch remain `0731e9c00b2858079007dbafdb0e052f497fb24c`. Frozen tag `afp-p14.13-freeze` object remains `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target remains HEAD. Git signing stays UNSIGNED, independently of the unavailable package crypto provider.

Before implementation exactly nine intended untracked P15 candidates existed; tracked and staged diffs were empty, and no generated residue was found. All nine SHA-256 hashes below were recaptured unchanged after implementation. No frozen tracked file or predecessor candidate was patched.

| Incoming file | SHA-256 |
| --- | --- |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
| docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md | F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A |
| docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md | 4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A |
| docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md | F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4 |

## Reuse and bounded model

P15.3 scalars, seconds-based MotionTime, MotionState, vectors, explicit three-dimensional frames, bounds and passive provenance are REUSE and P15_3_FROZEN_FOR_THIS_SLICE. Its supplied trajectories and plans are REFERENCE_ONLY for simulation results. P15.1 exact descriptor/package identity and domain artifacts and P15.2 interchange are REUSE. Interpolation, orientation, frame composition and richer physics are DEFER_TO_LATER_SIMULATION. No parallel motion-state model or second interchange parser was introduced.

The only model is `apexforge.apexmotion.kinematics.constant-acceleration/v1`. For every axis, x' = x + v·dt + a·dt²/2 and v' = v + a·dt. Time advances by dt. Acceleration remains supplied and constant. Velocity and acceleration are mandatory; absence fails admission rather than becoming zero. Model/profile, exact platform descriptor revision and exact P14 implementation package, initial state and its fingerprint, timestep, count, constraints and fixed policy are bound by the immutable specification.

The explicit timestep is a positive MotionScalar in seconds. Domain origin comes from the initial MotionTime, never wall clock. Counts are exact integers from 0 through 4096 (Boolean rejected). Zero steps return an empty computed-step set and separately bound initial state. No end-time inference, adaptive stepping or parallel execution exists.

## Arithmetic, frames and diagnostics

P15.3 decimal strings support up to 18 integer and nine fractional digits. Values are converted directly to integer billionths; Python Fraction performs exact arithmetic without binary float or context-dependent Decimal rounding. Results must be integral billionths and within ±(10²⁷−1) ticks. Excess precision returns SIMULATION_NUMERIC_PRECISION_ERROR; excess range returns SIMULATION_NUMERIC_RANGE_ERROR. There is no rounding, wrapping, saturation or clamping. The exact constant-acceleration expression is not a numerical-stability or physical-accuracy guarantee.

Entity, frame (including handedness/parent declaration), time origin and supplied acceleration remain unchanged. Cross-context evolution and constraints are rejected. No frame transform, angular evolution or unit conversion is implemented. Stable admission codes distinguish unsupported model, missing components, invalid timestep/count, bad platform, duplicate constraints and context mismatch. Numeric failure yields a failed-step code and only the valid prefix, never a completed trace.

## Steps, traces, provenance and constraints

Steps are one-based and bind spec fingerprint, prior-state fingerprint, resulting P15.3 state fingerprint, ordered bound checks and SIMULATED origin. The trace separately contains the caller-supplied initial state and computed steps; generated times increase strictly because dt is positive. Trace admission rechecks each transition, ordering, predecessor identity and check results. Failed prefixes must reproduce the declared numeric failure on their next step.

The passive P15.3 MotionState record has a fixed CALLER_SUPPLIED carrier marker. P15.4 does not rewrite that frozen type: computed step serialization uses `state_fields` with that carrier marker removed, retains the exact P15.3 state fingerprint, and explicitly assigns the step's origin SIMULATED. The projection is not claimed to be the original state's canonical record. The enclosing spec/prior chain establishes derivation; old provenance references remain unchanged. No conversion to a supplied MotionTrajectory is offered that could erase this distinction. Simulated is neither measured nor observed; no physical event or real-world authorship is proven.

Position, velocity and acceleration axis bounds are checked inclusively for the initial state and every computed state. Constraint identities are ordered canonically; duplicates and frame/entity conflicts fail. The sole policy is REPORT_AND_CONTINUE. Any violated axis yields CONSTRAINT_VIOLATION; computed values remain unchanged. Bounds are evaluated, never solved. Numeric failure takes precedence while prior step check evidence remains visible.

## SDK, artifacts and authority

SimulationSpec, SimulationStep, ConstraintCheck and SimulationTrace use domain-separated v1 schemas and deterministic sorted compact UTF-8 JSON inherited from P15.3. Descriptor identity, package content identity, state identity, spec/step/trace fingerprints and artifact digest remain distinct.

The typed local `simulate(spec)` function performs the bounded calculation. The generic SDK has no new execution dispatch: specification/trace bytes are exposed as domain plan/model artifacts under the already-declared motion.plan.describe and motion.trajectory.describe operations. Those operations describe supplied simulation evidence; they do not request execution. P15.1 requests/results and P15.2 interchange round-trip the artifact reference with exact platform/package/descriptor bindings. Caller-supplied payload bytes remain separate; no new typed wire decoder is claimed. SDK COMPLETE remains a passive declaration, distinct from the kernel's computed trace.

Canonical AIR remains semantic authority. Simulation artifacts are domain artifacts, not P14 package artifacts. Simulation neither queries registries nor solves dependencies nor alters manifests, lockfiles, cache or publication. Package trust is not inferred. CRYPTO_PROVIDER_UNAVAILABLE remains unchanged; no signing dependency was installed.

## Deferred physics and security audit

Unsupported: force/mass/torque models, gravity inference, friction/drag, rigid bodies, collision detection/response, fluids, particles, joints/contact manifolds, stochastic methods, angular dynamics, interpolation, frame transformations, constraint solving and physical actuation. No external adapter, device operation, later P15 domain or freeze work exists.

Semantic inspection of the production module confirms only dataclass/Fraction and passive P15 SDK/motion imports. Calls construct/validate records, perform exact arithmetic, hash/serialize through existing helpers, or compute bound comparisons. There is no AIR evaluator, RuntimeEngine, compiler, native dispatch, AuthorityEngine, installation, network, filesystem discovery, shell/subprocess, dynamic import, caller-code execution or private-key persistence. The AST audit additionally checks imports and prohibited direct call names; the claim does not rely on text matching alone. Test-only frozen authority execution is separate from production simulation behavior.

## Validation and Patch Matrix

First focused execution exposed a new test-fixture keyword override collision, classified APEXMOTION_SIMULATION_MODEL_GAP, owned entirely by the P15.4 focused test. The fixture was corrected without weakening assertions. Final model admission guards reject mutable step/check collections and cross-context evolution. No predecessor defect was discovered.

Exact commands and final results:

| Command (prefix: python -X utf8 -B) | Result |
| --- | --- |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| -m unittest discover -s apexforge -p p15_*_test.py | 123/123 PASS |
| -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| apexforge/authority_consolidation_smoke_test.py | canonical identities, exact grant, wrong principal/capability/resource denial, authorized runtime execution and transactional denied execution PASS |

Final focused and P15 aggregate checks were repeated after admission guards. A 1,000-step iterative repeated trace has byte-identical output and expected final x=1001000; this is determinism/scale evidence, not benchmark certification. Fractional/multi-axis transitions, missing components, precision/range failure, valid-prefix failure, immutable models, prior-state chain, bound violations without clamping, canonical constraint permutations and SDK/interchange integration are tested.

Preservation audit: all nine incoming hashes unchanged; only three new P15.4 files; twelve intended untracked candidates; tracked/cached diffs empty; branch/HEAD/P14 branch/tag unchanged. No generated residue in apexforge/docs (cache directories or pyc/pyo/exe/dll/pdb/obj/vsix). No staging, commit, tag or push. No P15.5 or physical actuation work.

Exact final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/apexmotion_simulation.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
?? docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
```

## Evidence markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_4_INCOMING_CANDIDATES=9
P15_4_SIMULATION_PROFILE_BOUNDED=True
P15_4_SIMULATION_TIME_IS_DOMAIN_TIME=True
P15_4_TIME_STEP_CALLER_SUPPLIED=True
P15_4_SIMULATION_LOOP_BOUNDED=True
P15_4_CONSTRAINT_EVALUATION_IMPLEMENTED=True
P15_4_TRACE_PROVENANCE=SIMULATED
P15_4_FRAME_TRANSFORM_IMPLEMENTED=False
P15_4_CROSS_FRAME_SIMULATION_IMPLEMENTED=False
P15_4_ANGULAR_DYNAMICS_IMPLEMENTED=False
P15_4_CONSTRAINT_SOLVER_IMPLEMENTED=False
P15_4_GENERAL_NUMERICAL_ACCURACY_CLAIM=False
P15_4_REDEFINES_DOMAIN_PLATFORM=False
P15_4_REDEFINES_DOMAIN_INTERCHANGE=False
P15_4_SIMULATION_PROVES_PHYSICAL_EVENT=False
P15_4_SIMULATION_GRANTS_TRUST=False
P15_4_SIMULATION_GRANTS_AUTHORITY=False
P15_4_SIMULATION_INVOKES_AUTHORITY_ENGINE=False
P15_4_PHYSICAL_ACTUATION_IMPLEMENTED=False
P15_4_COLLISION_DETECTION_IMPLEMENTED=False
P15_4_COLLISION_RESPONSE_IMPLEMENTED=False
P15_4_FORCE_SOLVER_IMPLEMENTED=False
P15_4_RIGID_BODY_DYNAMICS_IMPLEMENTED=False
P15_4_FLUID_DYNAMICS_IMPLEMENTED=False
P15_4_PARTICLE_DYNAMICS_IMPLEMENTED=False
P15_4_STOCHASTIC_SIMULATION_IMPLEMENTED=False
P15_4_PARALLEL_SIMULATION_IMPLEMENTED=False
P15_4_EXECUTES_AIR=False
P15_4_EXECUTES_RUNTIME=False
P15_4_DISPATCHES_NATIVE=False
P15_4_COMPILES=False
P15_4_INSTALLS_PACKAGES=False
P15_4_EXECUTES_ARBITRARY_DOMAIN_CODE=False
P15_4_NETWORK_ACCESS=False
P15_4_FILESYSTEM_DISCOVERY=False
P15_4_HOST_COMMAND_EXECUTION=False
P15_4_BINARY_FLOAT_REQUIRED=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_APEXMOTION_SIMULATION_MODEL=PASS
P15_APEXMOTION_SIMULATION_PROFILE=PASS
P15_APEXMOTION_SIMULATION_TIME=PASS
P15_APEXMOTION_SIMULATION_NUMERIC_MODEL=PASS
P15_APEXMOTION_SIMULATION_STATE_TRANSITION=PASS
P15_APEXMOTION_SIMULATION_TRACE=PASS
P15_APEXMOTION_SIMULATION_PROVENANCE=PASS
P15_APEXMOTION_SIMULATION_DETERMINISM=PASS
P15_APEXMOTION_SIMULATION_SECURITY_BOUNDARY=PASS
P15_3_REGRESSION=PASS
P15_2_REGRESSION=PASS
P15_1_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P15_AUTHORITY_COEXISTENCE=PASS
PATCH_MATRIX=PASS
P14_FROZEN_PREDECESSOR_PRESERVED=True
P15_4_READY_FOR_REVIEW=True
```

