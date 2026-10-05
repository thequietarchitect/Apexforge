# P15.8 — Fabrication contract and deterministic manufacturing-plan foundation

Evidence for owner review; no release/freeze or milestone completion declaration.

## Baseline and incoming hashes

Branch remains `p15-1-domain-platform-contract-sdk`. HEAD and frozen P14 branch remain `0731e9c00b2858079007dbafdb0e052f497fb24c`. Tag `afp-p14.13-freeze` remains object `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target equals HEAD. Exactly 21 intended incoming untracked P15 candidates were captured before implementation. Tracked/staged diffs were empty and generated residue absent. All incoming SHA-256 values were subsequently recaptured unchanged.

| Incoming path | SHA-256 |
| --- | --- |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/p15_5_narrative_domain_contract_test.py | FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E |
| apexforge/p15_6_agent_domain_contract_test.py | 1197B2D82E28EA4B91F240946387AECE8E41FEEE788F824E021DD630F65CF5C5 |
| apexforge/p15_7_parametric_domain_contract_test.py | BF70EBF1ABD171685330F6D2800878E721B6882CDE20108447EB20E7067945A8 |
| apexforge/tooling/agent_domain.py | A56E46EF274C8A9B81E0E6D8B90933B30A17996C7FB752284C891D145E312864 |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/apexmotion_simulation.py | EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
| apexforge/tooling/narrative_domain.py | BA1284F04FC4DF4C63172E64AE8933E960C07979B1D597C7AB780253B85073DC |
| apexforge/tooling/parametric_domain.py | 1F8E096C3CC78ED89C8452445C8456215735F4165AAC71BC2C55EADED09D3036 |
| docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md | F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A |
| docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md | 4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A |
| docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md | F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4 |
| docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md | 861DD7D3409081569B31C2537702E4DE01E57A679369FCD817A4C08395A6D59D |
| docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md | BA359C40CFE4A61D56883C2A5F075719C7E36303B23F630B76890E2AA8EEE151 |
| docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md | AD9A937754E811461595B5D8488B515D4CFCF32CFB74E74C18D76F6A35FD4769 |
| docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md | C27D8D09E1DB62DFE751B60A4796478BA1D178545C6974A7BEAA2CE881E38EFD |

## Architecture census

| Concept | Classification / use |
| --- | --- |
| P15.1 platform/request/result/artifact and capability declarations | REUSE: exact SDK identity/package/revision and passive evidence carriers |
| P15.2 interchange | REUSE: generic byte/reference exchange; no second protocol or payload decoder |
| P15.7 ParametricScalar | REUSE: exact unit-neutral decimal encoding and integer-billionths comparison; its owner remains unchanged |
| P15.7 ParametricVariant/design/parameter set | REFERENCE_ONLY / FROZEN_CONTRACT: exact variant fingerprint reference and unchanged object, never inferred geometry |
| P14 package artifacts and member/raw digest convention | REFERENCE_ONLY / FROZEN_CONTRACT: separate package/artifact domains, SHA-256 exact bytes; no archive, cache or publication change |
| Frozen authority/runtime contracts | REFERENCE_ONLY / FROZEN_CONTRACT: no production imports or invocation |
| Assembly process/material/machine profiles, plan and validation | FABRICATION_EXTENSION_POINT |
| Slicers, external CAD, device adapters | DEFER_TO_P15_9 / DEFER_TO_EXTERNAL_TOOLING |

Searches of repository production Python found no existing fabrication/material/machine/slicer/device implementation to activate or reuse, only the generic fabrication domain-kind declaration and earlier deferral boundaries. No historic external workflow, hardware/software installation or device was inspected live. P15.8 is completely testable with caller-supplied in-memory evidence.

## Bounded process and platform

The initial metadata-only profile is `apexforge.fabrication.assembly/v1`. It declares assembly planning evidence, not an industrial assembly procedure or executable process. No FFF temperature/infill/speed model, subtractive cutting model or machine command is invented. Other processes fail FABRICATION_PROCESS_UNSUPPORTED; no process is inferred from filenames.

Fabrication platform `apexforge.fabrication`, kind fabrication, contract 1.0.0 uses the exact P15.1 descriptor and P14 implementation coordinate/content identity. Operations are fabrication.plan.describe, fabrication.compatibility.validate and fabrication.result.describe. The compatibility function computes only comparisons of supplied metadata. Capability fabrication.describe is declarative, not permission. Platform identity is distinct from job, machine, material and package domains.

## Inputs and parametric coexistence

FabricationInput is immutable and carries explicit logical kind (part-evidence, geometry-evidence or mesh), uppercase raw SHA-256, optional exact supplied bytes, optional exact ParametricVariant object and passive provenance. Supplied bytes are admitted only if the digest matches. Malformed digest, wrong byte type or corruption fails before a valid input/plan can exist. Digest-only input is labelled BYTES_NOT_SUPPLIED and leads to incomplete input-integrity evidence, never a successful byte check. Bytes are opaque: no mesh parser, CAD evaluation, geometry safety or physical existence claim.

A ParametricVariant reference binds its exact fingerprint; the existing immutable variant is retained without modification. No input bytes are inferred from it, and no geometry is generated. Tests capture design/variant fingerprints and variant canonical record before fabrication reference construction and prove them unchanged afterwards. P15.7 source hashes and 31/31 tests remain unchanged; no fabrication operation was added to its platform.

## Material, machine and process-parameter profiles

MaterialProfile has a validated opaque ID, separately declared family, optional explicit supported-process tuple and provenance. Family is a supplied classification, not composition inferred from a marketing name. None means declaration absent; an empty tuple means explicitly no declared supported process. No chemical/mechanical/medical/fire/food/aerospace certification is inferred. Record material_certified=False.

MachineRequirementProfile declares the exact process, positive three-dimensional required working envelope, required feature identifiers and provenance. Required features are structural strings in this profile, not runtime grants. It is explicitly declarative_only and grants_authority=False. There is no endpoint, host device, operator, USB path, serial port or connection field.

MachineProfile is a caller-supplied opaque machine ID plus optional process/envelope/material-family/feature declarations and provenance. Identity implies no owner, human, organization, location or authenticity. Record evidence_origin=CALLER_SUPPLIED and live_machine_state=False. None means absent evidence; empty tuples are explicit declarations with no support. No machine discovery or query occurs.

BuildEnvelope reuses exact ParametricScalar values with explicit mm or m units, all axes positive. ProcessParameters contains a nonnegative explicit clearance declaration with mm or m unit and exact process. It is not applied to geometry and generates no toolpath. Plan admission requires clearance and required-envelope units match; no implicit conversion is performed. Scalar encoding remains bounded to 18 integer and nine fractional digits with canonical negative-zero/trailing-zero handling and no binary float. Unsupported unit/value encodings fail closed. There are no physical temperature, force or control calculations.

## Job, plan and deterministic compatibility

FabricationJobIdentity is a validated immutable opaque typed ID, distinct from design, variant, machine, platform and package identity. FabricationPlan binds job, exact SDK platform/package/revision, input/digest/variant reference, exact material profile, exact machine requirements, explicit process parameters and provenance. Its domain-separated apexforge.fabrication.plan/v1 fingerprint binds all canonical fields. Record execution=NOT_PERFORMED, canonical AIR semantic authority and authority false. No hidden device access exists.

FabricationValidation immutably binds a plan and optional supplied MachineProfile. Findings are independently retained for:

1. input byte/digest evidence;
2. material process declaration;
3. machine process declaration;
4. machine material-family declaration;
5. required machine features;
6. working envelope;
7. admitted process parameters.

Each finding contains stable dimension, COMPATIBLE/INCOMPATIBLE/UNKNOWN and reason code. None evidence is UNKNOWN; explicit absent support or too-small envelope is INCOMPATIBLE. Missing features are never inferred. An empty requirement needs no feature and therefore does not assert a feature exists. Exact same-unit axes compare integer billionths; different machine/required units yield UNKNOWN/UNIT_CONVERSION_UNSUPPORTED because conversion is not implemented. No machine setting or plan value is adjusted.

Overall status is INVALID if any explicit incompatibility exists; otherwise INCOMPLETE if any UNKNOWN exists; otherwise VALID. Unknown findings remain visible even when an incompatibility takes overall precedence. Malformed/contradictory raw input fails typed record admission with deterministic FabricationError codes, separately from compatibility findings. Material names do not determine matching; only explicit family/process declarations do.

VALID means only that these bounded structural/integrity checks passed. It is not manufacturability certification, geometric validation, part safety, engineering correctness, machine safety certification, execution permission or physical-job receipt. No unsupported temperature/tool/nozzle or geometry suitability checks are claimed.

## External results and domain artifacts

FabricationResultRecord holds an exact plan, externally supplied REPORTED_COMPLETED/REPORTED_FAILED/REPORTED_ABORTED status, output references and provenance. It binds the exact plan fingerprint and labels evidence_origin=EXTERNALLY_SUPPLIED, physical_fabrication_verified=False. No result is generated by compatibility validation, and no claimed completed action is internally fabricated.

fabrication_artifact wraps plan, validation or result into a P15.1 model artifact with canonical record plus explicit record_fingerprint, exact Fabrication platform/implementation package/descriptor, payload SHA-256, supplied AIR/symbol references and provenance. Material, machine requirements and parameters travel inside the plan; there is no separate standalone transport API claimed for them. P15.2 retains ownership of generic request/result/artifact serialization. SDK COMPLETE is a passive declaration, not proof of manufacture. No new top-level protocol or fabrication-byte parser is introduced. Fabrication artifacts remain distinct from P14 package artifacts, Parametric artifacts and physical objects.

## Provenance, trust, authority and deferred execution

Evidence lineage binds input, material, process, requirement and plan references without proving an operator approved them, a material was certified, a machine connected or a physical object exists. EVIDENCE_BEFORE_ATTRIBUTION=True. Structural compatibility supplies no package/machine trust, operator identity, physical truth or authority. Canonical AIR remains semantic authority. P15.6 agent intents are not imported, executed or promoted into machine actions.

CRYPTO_PROVIDER_UNAVAILABLE remains preserved; no provider/dependency was installed and no signature verification is claimed. Frozen Git signing UNSIGNED remains distinct from the package authentication limitation.

Deferred: CAD/OpenSCAD evaluation, geometry generation/repair/meshing, slicing, toolpath production, G-code generation/parsing into operations/execution, all printer/CNC/laser control, heaters/motors/extruders/spindles, GPIO/serial/CAN/USB/network machine commands, device discovery and external software adapters. No opaque G-code input kind was added merely for feature count. No P15.9 or freeze work exists.

## Determinism and security audit

Canonical records use the frozen SDK sorted compact UTF-8 JSON and domain-separated v1 fingerprints. Exact bytes remain raw-digest-bound rather than embedded in canonical records. Unordered declarations/provenance canonicalize; diagnostics/finding dimensions sort deterministically. No wall clock, random state, thread, machine hostname, local port, host path, process ID or locale participates.

Production semantic inspection confirms only dataclass/hash/re and passive SDK/Parametric/P14 records are imported. Functions validate exact types/declared strings/digests, hash supplied bytes, compare fixed exact scalar fields, construct records and serialize evidence. No RuntimeEngine/AIR/compiler/native execution, arbitrary callback/import, shell/subprocess, network, filesystem/device discovery, CAD/slicer, installation, credential/private-key access or authority invocation exists. AST import/direct-call tests supplement semantic inspection; they are not the sole evidence. Frozen authority smoke's test-only runtime execution is separate from fabrication production behavior.

## Focused validation and Patch Matrix

Initial focused suite: 32/32 PASS. Final review identified FABRICATION_SECURITY_BOUNDARY_GAP in the new P15.8 process-field comparison: exact type guards were needed before equality to reject caller comparison hooks. The production module was patched locally and a raising-comparison-object test added. Final focused suite is 33/33 PASS and P15 aggregate 245/245 PASS after the correction. No predecessor contract or assertion was changed. Owning surface P15.8; frozen dependencies remained untouched; focused/cross-section/aggregate regressions and preservation all pass.

Coverage includes explicit process/platform/package identities, exact input integrity, passive unchanged variant, material/machine identity boundaries, explicit units, immutable plan/profile/report records, exact bindings, compatible/incompatible/unknown dimensions, missing bytes/declarations, same-unit envelope bounds, no implicit conversion, collection permutation, external result claims, artifact/request/result interchange, provenance, safety/authority flags and static/caller-hook audits.

A 1,000-feature requirement/profile case yields equivalent plan and validation fingerprints after reversal. All processing is iterative over supplied collections. This is deterministic scale evidence, not performance certification.

Exact command prefix `python -X utf8 -B`:

| Command | Final result |
| --- | --- |
| apexforge/p15_8_fabrication_domain_contract_test.py | 33/33 PASS |
| apexforge/p15_7_parametric_domain_contract_test.py | 31/31 PASS |
| apexforge/p15_6_agent_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_5_narrative_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| -m unittest discover -s apexforge -p p15_*_test.py | 245/245 PASS |
| -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| apexforge/authority_consolidation_smoke_test.py | canonical identities, exact grant, wrong principal/capability/resource denial, authorized execution and transactional denied execution PASS |

P15.5's documented historical P11 limitations remain unchanged: old scene-field expectation predates P11.6K; missing examples/P11Validation is not a new dependency. No historical external hardware/software test was run or weakened.

## Preservation and final status

All 21 incoming hashes preserved; only three intended P15.8 files added, giving 24 untracked candidates. Branch/HEAD, P14 branch/tag object/peeled target unchanged. Tracked and staged diffs empty; no frozen P14/P13/P12/P11/P10 or earlier P15 file changed. Generated-residue audit under apexforge/docs found no cache directories or pyc/pyo/exe/dll/pdb/obj/vsix. Nothing staged, committed, tagged or pushed. No P15.9, device discovery, CAD/slicer/G-code/physical actuation or freeze work.

Exact final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/p15_5_narrative_domain_contract_test.py
?? apexforge/p15_6_agent_domain_contract_test.py
?? apexforge/p15_7_parametric_domain_contract_test.py
?? apexforge/p15_8_fabrication_domain_contract_test.py
?? apexforge/tooling/agent_domain.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/apexmotion_simulation.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/fabrication_domain.py
?? apexforge/tooling/narrative_domain.py
?? apexforge/tooling/parametric_domain.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
?? docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
?? docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md
?? docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md
?? docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md
?? docs/p15/P15_8_FABRICATION_DOMAIN_CONTRACT.md
```

## Evidence markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_8_INCOMING_CANDIDATES=21
P15_8_FABRICATION_USES_P15_DOMAIN_PLATFORM=True
P15_8_FABRICATION_INPUT_INTEGRITY_BOUND=True
P15_8_MACHINE_REQUIREMENTS_ARE_DECLARATIVE=True
P15_8_PROCESS_PARAMETERS_HAVE_EXPLICIT_UNITS=True
P15_8_CANONICAL_NUMERIC_MODEL_DETERMINISTIC=True
P15_8_FABRICATION_RESULT_IS_EXTERNAL_EVIDENCE=True
P15_8_REDEFINES_CORE_SEMANTICS=False
P15_8_MACHINE_EXECUTION_IMPLEMENTED=False
P15_8_PROCESS_INFERRED_FROM_FILENAME=False
P15_8_GEOMETRY_GENERATION_IMPLEMENTED=False
P15_8_MESH_GENERATION_IMPLEMENTED=False
P15_8_MACHINE_DISCOVERY_IMPLEMENTED=False
P15_8_UNKNOWN_COMPATIBILITY_FAILS_OPEN=False
P15_8_COMPATIBILITY_PROVES_ENGINEERING_SAFETY=False
P15_8_TOOLPATH_GENERATION_IMPLEMENTED=False
P15_8_GCODE_GENERATION_IMPLEMENTED=False
P15_8_GCODE_EXECUTION_IMPLEMENTED=False
P15_8_SLICER_INVOCATION_IMPLEMENTED=False
P15_8_OPENSCAD_EXECUTION_IMPLEMENTED=False
P15_8_PHYSICAL_ACTUATION_IMPLEMENTED=False
P15_8_MUTATES_PARAMETRIC_VARIANT=False
P15_8_AGENT_INTENT_EXECUTION_IMPLEMENTED=False
P15_8_REDEFINES_DOMAIN_PLATFORM=False
P15_8_REDEFINES_DOMAIN_INTERCHANGE=False
P15_8_VALID_FABRICATION_RECORD_GRANTS_TRUST=False
P15_8_FABRICATION_GRANTS_AUTHORITY=False
P15_8_FABRICATION_INVOKES_AUTHORITY_ENGINE=False
P15_8_EXECUTES_AIR=False
P15_8_EXECUTES_RUNTIME=False
P15_8_DISPATCHES_NATIVE=False
P15_8_COMPILES=False
P15_8_EXECUTES_CAD_CODE=False
P15_8_NETWORK_ACCESS=False
P15_8_DEVICE_DISCOVERY=False
P15_8_FILESYSTEM_DISCOVERY=False
P15_8_HOST_COMMAND_EXECUTION=False
P15_8_INSTALLS_PACKAGES=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_FABRICATION_PLATFORM_MODEL=PASS
P15_FABRICATION_PROCESS_MODEL=PASS
P15_FABRICATION_INPUT_MODEL=PASS
P15_FABRICATION_INPUT_INTEGRITY=PASS
P15_FABRICATION_MATERIAL_MODEL=PASS
P15_FABRICATION_MACHINE_REQUIREMENT_MODEL=PASS
P15_FABRICATION_PROCESS_PARAMETER_MODEL=PASS
P15_FABRICATION_PLAN_MODEL=PASS
P15_FABRICATION_COMPATIBILITY_MODEL=PASS
P15_FABRICATION_EVIDENCE_COMPLETENESS=PASS
P15_FABRICATION_ARTIFACT_MODEL=PASS
P15_FABRICATION_PROVENANCE=PASS
P15_FABRICATION_DETERMINISM=PASS
P15_FABRICATION_TRUST_BOUNDARY=PASS
P15_FABRICATION_AUTHORITY_BOUNDARY=PASS
P15_FABRICATION_SECURITY_BOUNDARY=PASS
P15_7_REGRESSION=PASS
P15_6_REGRESSION=PASS
P15_5_REGRESSION=PASS
P15_4_REGRESSION=PASS
P15_3_REGRESSION=PASS
P15_2_REGRESSION=PASS
P15_1_REGRESSION=PASS
P15_AGGREGATE_REGRESSION=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P15_AUTHORITY_COEXISTENCE=PASS
PATCH_MATRIX=PASS
P14_FROZEN_PREDECESSOR_PRESERVED=True
P15_8_READY_FOR_REVIEW=True
```

