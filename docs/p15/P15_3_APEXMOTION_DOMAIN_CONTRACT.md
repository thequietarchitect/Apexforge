# P15.3 ApexMotion Domain Contract & Motion Model Foundation

## Baseline, incoming hashes and preservation

Branch: `p15-1-domain-platform-contract-sdk`.
HEAD / peeled `afp-p14.13-freeze`: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
P14 annotated tag object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`.
Frozen branch `p14-1-package-identity-manifest` remains at the same commit.

Initial six P15 candidates enumerated with empty tracked/staged diffs and no generated residue. Incoming SHA-256 values:

| Incoming file | SHA-256 |
|---|---|
| `apexforge/p15_1_domain_platform_contract_sdk_test.py` | `0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62` |
| `apexforge/p15_2_domain_interchange_contract_test.py` | `E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2` |
| `apexforge/tooling/domain_interchange.py` | `31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC` |
| `apexforge/tooling/domain_platform.py` | `3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3` |
| `docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md` | `F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A` |
| `docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md` | `4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A` |

All six hashes preserved. Only apexmotion.py, its focused test and this report added: nine intended candidates. No stage/commit/tag/push; HEAD remains frozen P14. No frozen P10/P11/P12/P13/P14 path changed.

CRYPTO_PROVIDER_UNAVAILABLE remains active. No dependency/provider installed. P14 Git signing remains UNSIGNED, distinct from package signing.

## Existing architecture census

| Evidence | Classification | Treatment |
|---|---|---|
| P15.1 domain_platform.py identity, package binding, descriptor, capabilities, request/result/artifact | REUSE | Authoritative generic SDK carriers unchanged |
| P15.2 domain_interchange.py | REUSE; FROZEN_CONTRACT for this slice | Sole generic envelope/parser owner; no new document kinds or parser |
| P14 package_manifest.py exact identity, reference and version carriers | REUSE; FROZEN_CONTRACT | Exact distribution/content binding, canonical AIR/symbol/provenance references |
| Quad-Vector ResultantVector / lanes | REFERENCE_ONLY; FROZEN_CONTRACT | Symbolic two-dimensional motor-derived lane products, not a physical frame/unit-aware 3D position |
| incremental_cache/resonance.py numeric canonicalization | REFERENCE_ONLY | Finite float representation and Decimal support are evidence serialization conventions, not a motion scalar/solver model |
| language_server/formatting.py Decimal formatting | REFERENCE_ONLY | Source formatting remains unrelated to physical quantities; no compiler utility imported for motion values |
| P11 continuity/rich-document ApexMotion references | REFERENCE_ONLY | ApexMotion canonical animation-software name and later motion/simulation interoperability direction |
| Physical frame/unit/geometry utilities | No reusable matching model found in inspected repository | Introduce bounded domain-only values; no competing canonical language/math identity |
| Simulation, transforms, dynamics, interpolation, rendering and actuation | DEFER_TO_P15_4 / later applicable slice | No execution or numerical engine |

Inspection searched existing motion, vector, frame, unit, transform and numeric references before implementation. No existing physical geometry model was duplicated; frozen Quad-Vector meaning was not reinterpreted.

## ApexMotion platform and generic SDK binding

apexmotion_platform(manifest) produces the existing DomainPlatformDescriptor with:

- DomainPlatformIdentity: apexforge.apexmotion;
- kind: motion;
- SDK schema: apexforge.domain-platform/v1;
- ApexMotion contract version: 1.0.0;
- exact P14 coordinate and package content identity from the supplied admitted manifest;
- one declarative capability: motion.describe;
- existing manifest provenance references.

The ID conveys no organization ownership or package identity. No coordinate-only lookup, registry discovery, signing/trust or installation.

Declared operations are exactly motion.state.describe, motion.trajectory.describe, motion.constraint.describe and motion.plan.describe. No integrate/simulate/solve/collide/step/actuate operation. Transform description was unnecessary for this minimal contract and is deferred rather than implying a transform implementation.

Profile use validates the exact platform identity/kind, contract version, operation/capability set and absence of unimplemented domain dependencies. The descriptor fingerprint still binds its exact package/provenance and all generic SDK fields. Changed revisions or another platform profile fail APEXMOTION_PLATFORM_BINDING_INVALID. No new SDK hierarchy or domain-kind semantics.

## Entity, frames and vector context

MotionEntity and FrameIdentity are distinct frozen opaque caller-supplied identifiers, bounded lowercase ASCII segments. No generated UUID, display-name inference, package/language/agent identity reuse or host path.

ReferenceFrame records identity, explicit right/left handedness, exact dimensionality 3 and optional parent FrameIdentity. Self-parent rejects. Parent is a declared relation only: no composition, global frame discovery, parent existence proof, frame-graph solving or physical/world truth. Cycles across independently supplied frames are not resolved by a nonexistent frame graph.

MotionVector has exact x/y/z scalar objects, explicit unit and full ReferenceFrame record. No frame-less position or rendering-coordinate inference. State components and bounds must match exact frame identity plus handedness/dimensionality/parent declaration; same ID with different frame metadata is not silently equivalent.

Orientation/angular velocity are deferred. No quaternion/Euler/axis-angle conversion or rotation mathematics, and no unsupported orientation fields manufactured for a test count.

## Numeric and unit model

MotionScalar accepts only an exact bounded decimal string:

- optional minus sign;
- 1–18 integer digits, no ambiguous leading zeros;
- optional 1–9 fractional digits;
- no exponent, plus sign, whitespace, float, boolean, NaN or infinity.

Canonicalization removes trailing fractional zeros and normalizes negative zero to 0. No rounding, binary floating conversion or Decimal context dependence. Exact scaled integer ticks (one-billionth of the scalar unit) support only structural comparison/order. Maximum absolute scalar is 999999999999999999.999999999. Values requiring greater precision/range fail rather than round.

This is descriptive exact data, not numerical stability, integrator accuracy or physical solver evidence. It does not alter ApexForge scalar/type semantics.

The read-only unit table admits only:

| Component | Canonical unit |
|---|---|
| Position | m |
| Velocity | m/s |
| Acceleration | m/s2 |
| Domain time | s |

No bare ambiguous quantity, alternate cm/ms representation, unit conversion or dimensional-analysis engine. Vector records explicitly carry units; state/constraint component validation enforces the expected unit. Handedness is explicit and does not imply a rotation or coordinate conversion.

## Time and state

MotionTime binds a scalar value, caller-supplied domain timeline origin and unit s. Relative negative times are permitted. No wall-clock lookup or implicit epoch. Same numerical value on another origin is a different time context.

MotionState binds entity, required time/position and optional velocity/acceleration with exact common frame. None remains unavailable/not supplied, never zero. Acceleration does not infer velocity. Canonical state records retain provenance and semantic_authority=CANONICAL_AIR.

origin_status=CALLER_SUPPLIED is a structural provenance label, not measured, derived or simulated. Even planned target values are caller-supplied descriptions; a plan does not fabricate simulated or authenticated measurement provenance.

## Trajectory

MotionTrajectory is a nonempty immutable set of supplied samples canonicalized into exact chronological order. All samples must share entity, exact frame and domain timeline origin. Duplicate canonical time coordinates reject, including negative-zero aliases. Numeric ticks order avoids lexical sorting errors.

Canonical output is strictly monotonic after ordering; reversed equivalent sample input yields the same bytes/fingerprint. This operation organizes supplied evidence; it is not time stepping or interpolation. Samples are not an execution trace. Frame changes require an explicit future transform model and currently reject.

Records state interpolation=NOT_IMPLEMENTED and execution=NOT_PERFORMED. No extrapolation, resampling, spline, numerical integration or stochastic model.

## Declarative constraints and motion plans

MotionConstraint describes axis-aligned lower/upper bounds on position, velocity or acceleration for one entity/frame/unit. Each lower coordinate must be <= the corresponding upper coordinate. This validates interval structure only. Unsupported force categories, wrong units/frame and reversed bounds reject.

Constraint satisfaction is NOT_EVALUATED. The contract deliberately permits describing a plan whose target is outside its bounds; it neither solves nor silently claims validity under those bounds.

MotionPlan retains supplied initial/target states, optional trajectory, constraints and provenance. Entity/frame/timeline must agree and target time may not precede initial time. Included trajectory endpoints must equal the exact retained initial/target states. Constraint entity/frame must match; duplicate constraints reject; unordered constraints canonicalize by fingerprint.

No feasibility, kinematics, physical continuity, speed/force limits, collision behavior or permission inference. A same-time target description is not evidence that instantaneous displacement is physically possible. Plan records say execution=NOT_PERFORMED and grants_authority=false.

## Artifacts, requests/results and interchange

motion_payload(record) returns canonical bytes containing the complete versioned motion record plus domain-separated record_fingerprint. It accepts only the supported typed state/trajectory/constraint/plan, never arbitrary raw JSON. No motion JSON parser was introduced.

motion_artifact(descriptor,record,semantic_inputs,symbols) returns the existing P15.1 DomainArtifact. States/trajectories/constraints use generic model; plans use generic plan. Motion-specific schema remains in the explicit caller-held payload, not a new P15.2 kind.

The artifact binds ApexMotion platform, exact implementation package, operation, exact descriptor fingerprint, digest of the full payload bytes, canonical semantic/symbol references and supplied provenance. Record fingerprint, raw artifact-byte digest, artifact-record fingerprint, package identity, AIR identity and descriptor revision remain distinct.

motion_request returns the existing DomainRequest with the artifact reference, declared describe operation, requested motion.describe declaration and explicit semantic/symbol/provenance references. SDK capability membership grants no permission.

Caller-declared DomainResult can carry the same artifact through existing SDK validation. COMPLETE remains declaration-only and does not prove description code, motion simulation or domain operations executed. Exact output descriptor/package/operation/input lineage uses P15.1 without modification.

P15.2 serializes/reconstructs descriptor, request, result and artifact references exactly. The raw typed motion payload bytes remain separately caller supplied and digest-verifiable via DomainArtifact.verify_bytes; P15.2 does not parse or recreate typed motion states from them. Frame dimensionality inside that opaque payload is not a new generic interchange numeric field. No second envelope/transport/parser or hidden domain dispatch.

## Determinism, provenance and authority

Motion record schemas/fingerprint domains are apexforge.apexmotion.frame/vector/time/state/trajectory/constraint/plan/v1. SHA-256(domain + NUL + canonical UTF-8 bytes), uppercase hex. JSON uses sorted keys, compact separators and ASCII escaping. Decimal values are canonical strings; dimensions are the explicit integer 3.

No timestamp, random value, process ID, host path, locale or machine identity. State ordering is chronological; constraints sort by fingerprint; provenance references sort by canonical reference record and duplicates reject. All production models are frozen; detached records cannot mutate them.

Existing CanonicalReference/SymbolReference objects preserve exact identity. Canonical AIR remains semantic authority. Motion records do not replace source, AIR, language semantics, package artifacts or runtime permission.

MOTION_PROVENANCE != REAL_WORLD_ATTRIBUTION. Matching bytes/records does not establish sensor authenticity, physical truth, measurement accuracy, authorship, package trust or runtime authorization. EVIDENCE_BEFORE_ATTRIBUTION=True. No AuthorityEngine import/invocation or grant.

## Security and deferrals

No time integration, physics/simulation engine, ODE/numerical solver, forces, collision detection/response, rigid-body/fluid/particle/stochastic dynamics, constraint solver, interpolation, frame transform or rendering. No motors, robots, CAN/serial/GPIO/device access or machine-control commands.

No AIR/RuntimeEngine execution, native dispatch, compiler/build, shell/subprocess, network, arbitrary filesystem discovery, registry access, package installation or domain-code dispatch. Production imports only passive SDK/package carriers and dataclasses/hashlib/json/re/types. Static call/import audit and dynamic authority/registry/solver/file/process/network traps pass. Canonical JSON production is serialization only.

P15.4 and later applicable slices own execution or richer domain behavior. No narrative/agents/parametric/fabrication/external adapter/governance/orchestration/security integration or P15 freeze work.

## Patch Matrix

Initial focused 30/30 PASS. Review exposed APEXMOTION_UNIT_GAP: a mutable module unit table could alter admitted component-unit semantics. Classified before patch; owner P15.3; patch only the new production/test pair; frozen dependencies P15.1/P15.2/P14/core unchanged. Converted table to MappingProxyType and asserted mutation rejection. Focused remains 30/30 PASS; scale fixture additionally verifies a 1,000-state payload digest and generic artifact interchange.

No failing assertion was hidden, weakened or removed. No predecessor owning defect. Final regressions and preservation pass.

One hash-capture orchestration attempted to parse truncated mixed tool output as JSON and failed. Classification TEST_INVOCATION_DEFECT; repeated the isolated hash capture successfully before implementation. No source/test repair was needed for that tooling-output error.

```text
APEXMOTION_UNIT_GAP=CLOSED
PATCH_MATRIX=PASS
```

## Validation

| Exact command | Final result |
|---|---|
| python -X utf8 -B apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| python -X utf8 -B apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| python -X utf8 -B apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py | 100/100 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| python -X utf8 -B apexforge/authority_consolidation_smoke_test.py | PASS |

P15 aggregate observed 1.870s; P14 aggregate observed 25.093s. Engineering observations only, not performance SLA/benchmark certification. Authority smoke preserves wrong principal/capability/resource denial, authorized existing RuntimeEngine fixture execution and transactional denial; ApexMotion invokes no runtime.

A 1,000-state forward/reversed trajectory yields identical fingerprint, payload verification and generic interchange artifact. This is passive ordering/scale evidence, not simulation or numerical accuracy.

## Final preservation and exact Git status

Branch/HEAD/P14 branch/tag object/peeled target unchanged. All six incoming hashes preserved. Tracked/staged diffs empty across the repository. No generated bytecode/cache/native outputs, unrelated candidates, package installation, physical actuation or P15.4 execution. Only nine intended candidates; nothing staged.

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
```

## Truth markers

```text
P15_BASELINE=P14_13_FREEZE
P15_3_INCOMING_CANDIDATES=6
P14_REOPENED=False
P15_3_APEXMOTION_USES_P15_DOMAIN_PLATFORM=True
P15_3_SIMULATION_EXECUTION_IMPLEMENTED=False
P15_3_FRAME_TRANSFORM_EXECUTION_IMPLEMENTED=False
P15_3_NUMERICAL_SOLVER_IMPLEMENTED=False
P15_3_UNIT_CONVERSION_ENGINE_IMPLEMENTED=False
P15_3_MISSING_MOTION_COMPONENTS_ARE_NOT_INFERRED=True
P15_3_TRAJECTORY_EXECUTES=False
P15_3_TRAJECTORY_INTERPOLATION_IMPLEMENTED=False
P15_3_CONSTRAINT_SOLVER_IMPLEMENTED=False
P15_3_MOTION_PLAN_EXECUTION_IMPLEMENTED=False
P15_3_MOTION_PLAN_GRANTS_AUTHORITY=False
P15_3_PHYSICAL_ACTUATION_IMPLEMENTED=False
P15_3_TIME_INTEGRATION_IMPLEMENTED=False
P15_3_COLLISION_DETECTION_IMPLEMENTED=False
P15_3_COLLISION_RESPONSE_IMPLEMENTED=False
P15_3_FORCE_SOLVER_IMPLEMENTED=False
P15_3_REDEFINES_DOMAIN_INTERCHANGE=False
P15_3_VALID_MOTION_RECORD_GRANTS_TRUST=False
P15_3_APEXMOTION_GRANTS_AUTHORITY=False
P15_3_APEXMOTION_INVOKES_AUTHORITY_ENGINE=False
P15_3_EXECUTES_AIR=False
P15_3_EXECUTES_RUNTIME=False
P15_3_DISPATCHES_NATIVE=False
P15_3_COMPILES=False
P15_3_NETWORK_ACCESS=False
P15_3_FILESYSTEM_DISCOVERY=False
P15_3_HOST_COMMAND_EXECUTION=False
P15_3_INSTALLS_PACKAGES=False
P15_3_EXECUTES_DOMAIN_CODE=False
CRYPTO_PROVIDER_UNAVAILABLE
EVIDENCE_BEFORE_ATTRIBUTION=True
P15_APEXMOTION_PLATFORM_MODEL=PASS
P15_APEXMOTION_ENTITY_IDENTITY=PASS
P15_APEXMOTION_FRAME_MODEL=PASS
P15_APEXMOTION_NUMERIC_MODEL=PASS
P15_APEXMOTION_UNIT_MODEL=PASS
P15_APEXMOTION_TIME_MODEL=PASS
P15_APEXMOTION_STATE_MODEL=PASS
P15_APEXMOTION_TRAJECTORY_MODEL=PASS
P15_APEXMOTION_CONSTRAINT_MODEL=PASS
P15_APEXMOTION_PLAN_MODEL=PASS
P15_APEXMOTION_ARTIFACT_MODEL=PASS
P15_APEXMOTION_PROVENANCE=PASS
P15_APEXMOTION_DETERMINISM=PASS
P15_APEXMOTION_SECURITY_BOUNDARY=PASS
P15_2_REGRESSION=PASS
P15_1_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P15_AUTHORITY_COEXISTENCE=PASS
P14_FROZEN_PREDECESSOR_PRESERVED=True
P15_CANDIDATE_COUNT=9
P15_3_READY_FOR_REVIEW=True
```

Stop at P15.3 review readiness.
