# P15.7 — Parametric design contract and deterministic parameter graph

Evidence for owner review, not a release/freeze or milestone completion declaration.

## Frozen baseline and hashes

Branch remains `p15-1-domain-platform-contract-sdk`. HEAD and P14 frozen branch remain `0731e9c00b2858079007dbafdb0e052f497fb24c`. Tag `afp-p14.13-freeze` object remains `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target equals HEAD. Exactly eighteen incoming P15 candidates, empty tracked/staged diffs and no generated residue were established before implementation. All eighteen SHA-256 hashes were recaptured unchanged before adding the report.

| Incoming path | SHA-256 |
| --- | --- |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/p15_5_narrative_domain_contract_test.py | FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E |
| apexforge/p15_6_agent_domain_contract_test.py | 1197B2D82E28EA4B91F240946387AECE8E41FEEE788F824E021DD630F65CF5C5 |
| apexforge/tooling/agent_domain.py | A56E46EF274C8A9B81E0E6D8B90933B30A17996C7FB752284C891D145E312864 |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/apexmotion_simulation.py | EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
| apexforge/tooling/narrative_domain.py | BA1284F04FC4DF4C63172E64AE8933E960C07979B1D597C7AB780253B85073DC |
| docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md | F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A |
| docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md | 4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A |
| docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md | F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4 |
| docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md | 861DD7D3409081569B31C2537702E4DE01E57A679369FCD817A4C08395A6D59D |
| docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md | BA359C40CFE4A61D56883C2A5F075719C7E36303B23F630B76890E2AA8EEE151 |
| docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md | AD9A937754E811461595B5D8488B515D4CFCF32CFB74E74C18D76F6A35FD4769 |

## Repository census and ownership

| Concept | Classification / decision |
| --- | --- |
| semantic_lattice/model.py ParametricSemanticLattice and SemanticLatticeParameter | FROZEN_CONTRACT / REFERENCE_ONLY: P11 compiler semantic evidence axes, not design geometry or physical parameter contracts; permits floats, therefore not a canonical exact physical-design numeric owner |
| language/semantic_decision_source.py and narrative_source.py source scalars | FROZEN_CONTRACT / REFERENCE_ONLY: passive source tokens/span-bearing syntax, not generic physical values |
| tooling/apexmotion.py MotionScalar, vectors, units and bounds | ADAPT arithmetic encoding strategy only; motion-specific identities/frame/unit semantics are not reused as generic design values |
| P15.1 domain platform, canonical models and artifact records | REUSE: authoritative domain/platform/package and passive capability bindings |
| P15.2 interchange | REUSE: generic request/result/artifact transport; no new protocol |
| P15.6 agent/session/intent separation | REFERENCE_ONLY: descriptive identity and intent do not authorize design mutation |
| P14 package/content/artifact/reference identities | REUSE / FROZEN_CONTRACT: package binding and reference syntax; domain design/artifact remain distinct |
| Parametric design/parameter identities, definitions, local constraints, assignments and variants | PARAMETRIC_EXTENSION_POINT |
| CAD/OpenSCAD adapters | DEFER_TO_EXTERNAL_ADAPTER |
| Fabrication, G-code and physical processes | DEFER_TO_P15_8 |

Repository file/content searches found no existing canonical physical geometry/CAD kernel, OpenSCAD execution integration, fabrication model or generic unit-aware exact design scalar suitable for reuse. “Parametric Semantic Lattice” naming does not make it a CAD contract. No historical OpenSCAD workflow was altered or executed, no executable installation was inspected, and no external environment was required. All new tests are in-memory and CAD-independent.

## Platform and identity

`apexforge.parametric`, kind parametric, contract 1.0.0 uses P15.1 DomainPlatformDescriptor and exact P14 implementation coordinate/content. Its only operations are parametric.design.describe, parametric.parameters.describe and parametric.variant.describe. Declared capability parametric.describe is not authority. Unknown/mismatched platform contract is rejected; no render/mesh/fabricate operation is declared.

ParametricDesignIdentity is a validated opaque caller ID, distinct from platform, package, language symbol and host filename. ParameterIdentity is independently typed and unique within each exact design revision. Display/presentation text is not identity. Canonical records explicitly carry v1 domain-separated schema labels. No new compiler, parser, AIR, authority or package semantics exist.

## Kinds, exact scalars, units and declarations

Supported kinds are scalar, integer, boolean and enumeration only. Arbitrary objects, callbacks, source expressions, floats and unknown kinds are rejected. ParametricScalar is an independent bounded exact decimal: at most 18 integer and nine fractional digits; plain signed decimal strings, no exponent/plus/leading-zero ambiguity, NaN or infinity. Trailing fractional zeros and negative zero normalize. Integer billionths permit exact comparisons without float conversion. Integers are exact signed 64-bit Python integers, rejecting Boolean/string/float substitutes. Boolean requires exact bool; enumerations use validated identifiers and declared alternatives.

The bounded unit contract is explicit:

| Kind/dimension | Unit |
| --- | --- |
| scalar length | m or mm |
| scalar angle | rad |
| scalar ratio | 1 |
| scalar explicitly unitless | 1 |
| integer count | count |
| boolean/enumeration | no unit or dimension |

A scalar cannot default to a physical unit; dimensional declarations require exact pairs. Assignment units must exactly match declaration units. m/mm are distinct, not converted. Units do not infer geometry, physical safety or manufacturing suitability. No dimensional-analysis/conversion engine exists.

ParameterDefinition contains typed identity/kind, exact dimension/unit, required flag, optional inclusive minimum/maximum, enumeration alternatives and optional presentation text. Numeric bounds must be exact values of the appropriate kind, within range and lower<=upper. Non-numeric bounds fail. Alternatives are canonical unordered declarations; duplicate/empty enum choices fail. Presentation is deliberately excluded from semantic serialization/fingerprints. It is not promised as portable canonical metadata; changing a display label does not change the design contract.

Defaults are deliberately unsupported. There is no implicit default resolver or zero/false/empty fallback. Every required declaration must have an explicit assignment. Optional omission remains recorded in omitted_optional and is not a supplied value. No unvalidated default can bypass checks.

## Parameter sets, graph and local constraints

ParameterAssignment binds exact typed parameter identity and validated ParameterValue. ParameterSet binds the full immutable design, exact design identity/fingerprint and canonical explicit assignments plus provenance. Duplicate/conflicting assignments, undeclared IDs, missing required values, wrong kind, wrong unit, disallowed enum values or out-of-bound numbers fail with deterministic codes. Assignments are sorted by parameter ID before local value validation, yielding order-independent diagnostics for equivalent invalid sets. No input value is changed, clamped, corrected or optimized.

Local constraints are presence, exact kind/unit, inclusive scalar/integer bounds and enumeration membership. Valid sets report SATISFIED; invalid sets do not become valid objects. There is no Boolean-only blanket result hiding why admission failed, and no general constraint solver or cross-parameter algebraic evaluation.

The graph is immutable ParameterReference edges nested in the design. Its sole relation is references: source parameter refers to target parameter. Nodes are the exact declared parameter identities. Edges canonicalize by source/target; duplicate pairs and dangling references fail. Cycles and self-references are permitted as passive reference structure, not interpreted as computable dependencies. An edge never supplies or derives a value. There is no expression AST evaluator, formula string execution, eval/exec, import hook or callback. General expressions and derived values remain deferred. All parameter/assignment/graph processing is iterative, without traversing recursive graph paths. Designs are capped at 4096 declared parameters.

## Variants, revisions and artifacts

ParametricVariant binds the complete canonical explicit assignment set, omitted optional IDs, exact parameter-set fingerprint, exact design identity/contract fingerprint and provenance. It means this exact contract under these assignments, not generated geometry. Changed semantic definitions yield a new contract fingerprint; changed assignments yield a new variant fingerprint. Original design and set remain unchanged. Equivalent construction/permutation yields identical canonical records/fingerprints. There is no silent revision mutation.

Fingerprints use separate domains for design/parameter identities, scalars, definitions, values, references, assignments, parameter sets and variants. Design identity/fingerprint includes exact SDK platform/package binding, declarations, graph, passive representation references and provenance. Variant identity is not an AIR, package, artifact-byte or interchange identity. Canonical JSON reuses the SDK sorted compact UTF-8 helper, with exact numbers/strings and no timestamps, random IDs, host paths or process/machine metadata.

Designs may retain supplied CanonicalReference representations (e.g. to a caller's model evidence). These are passive references only; no format-specific OpenSCAD parser or adapter is claimed. No inferred filename target or generated geometry exists.

parametric_artifact wraps design, parameter set or variant in a P15.1 model artifact containing exact record and record_fingerprint. It retains Parametric platform identity, exact implementation package, descriptor revision, payload digest, provenance and supplied canonical AIR/symbol inputs. Graph/constraints travel within the design. P15.2 serializes generic artifacts/requests/results, not a competing top-level format. No typed payload decoder or execution dispatch was added. SDK COMPLETE remains passive supplied declaration. Parametric artifacts are neither P14 package artifacts nor fabrication artifacts. Canonical AIR remains semantic authority.

## Deferred behavior, provenance, trust and authority

No geometry kernel, CSG execution, B-rep, NURBS, tessellation, mesh/STL export, rendering, OpenSCAD invocation, CAD-code execution, slicing, G-code, fabrication plan, toolpath or physical actuation exists. No external adapter or autonomous design agent exists. An agent action intent does not mutate a design or assignment; construction accepts only explicitly supplied records.

Provenance preserves exact supplied evidence references. A structural variant says only that contract/assignments bind its identity; it proves no human authorship, geometry rendering, external CAD approval or fabricated object. EVIDENCE_BEFORE_ATTRIBUTION=True. Structural admission is not package trust, engineering correctness, mechanical/medical/electrical safety, manufacturability, regulatory compliance or physical existence. No AuthorityEngine is invoked and no capability/name matching grants authority. CRYPTO_PROVIDER_UNAVAILABLE remains unchanged; no dependency installation or signature verification claim. Frozen Git signing state UNSIGNED remains distinct from package authentication availability.

Security audit combines AST imports/direct-call checks and semantic inspection. The production module imports only dataclasses/re and passive SDK/P14 identities. Its operations validate types, exact bounds, canonical declarations/references, construct immutable records and hash/serialize through existing helpers. There is no runtime/AIR/compiler/native/CAD invocation, subprocess/shell, network, filesystem discovery, installation, dynamic import, eval/exec, arbitrary callback, tool dispatch or authority grant. No private keys or credentials are introduced. Test-only frozen authority runtime execution is separate from this module.

## Validation and Patch Matrix

Focused tests passed on first execution: 31/31. No production or predecessor failure was discovered; no predecessor patch was required. Tests cover typed identities, numeric encoding and invalid forms, explicit units, all supported kinds, optional absence/no defaults, missing/undeclared/duplicate assignments, ranges without clamping, graph duplicate/dangling/cyclic references, immutable variants, exact revision/assignment identities, nonsemantic presentation, passive references, provenance, SDK/interchange and security. A 1,000-parameter/assignment case produces equal variant fingerprints after input reversal; this is deterministic scale evidence, not benchmark certification.

Exact command prefix: `python -X utf8 -B`.

| Command | Result |
| --- | --- |
| apexforge/p15_7_parametric_domain_contract_test.py | 31/31 PASS |
| apexforge/p15_6_agent_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_5_narrative_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| -m unittest discover -s apexforge -p p15_*_test.py | 212/212 PASS |
| -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| apexforge/authority_consolidation_smoke_test.py | canonical identities, exact grant, wrong principal/capability/resource denial, authorized execution and transactional denied execution PASS |

Historical P11 narrative limitations recorded in P15.5 remain unchanged: earlier scene-field expectation predates P11.6K prose; examples/P11Validation fixture remains absent. No old harness, missing fixture or external CAD program is a P15.7 dependency.

## Preservation and exact Git status

All eighteen incoming hashes preserved. Only three intended P15.7 files added, giving twenty-one untracked candidates. Branch/HEAD, P14 frozen branch/tag object/peeled target unchanged. Tracked and staged diffs empty; no frozen P14/P13/P12/P11/P10 file changed. No generated residue under apexforge/docs (cache directories or pyc/pyo/exe/dll/pdb/obj/vsix). Nothing staged, committed, tagged or pushed. No P15.8, external adapter or freeze work; no CAD execution, mesh, G-code or actuation.

Exact final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/p15_5_narrative_domain_contract_test.py
?? apexforge/p15_6_agent_domain_contract_test.py
?? apexforge/p15_7_parametric_domain_contract_test.py
?? apexforge/tooling/agent_domain.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/apexmotion_simulation.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/narrative_domain.py
?? apexforge/tooling/parametric_domain.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
?? docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
?? docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md
?? docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md
?? docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md
```

## Evidence markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_7_INCOMING_CANDIDATES=18
P15_7_PARAMETRIC_USES_P15_DOMAIN_PLATFORM=True
P15_7_CANONICAL_NUMERIC_MODEL_DETERMINISTIC=True
P15_7_MISSING_PARAMETER_VALUES_NOT_INFERRED=True
P15_7_PARAMETER_GRAPH_DETERMINISTIC=True
P15_7_LOCAL_CONSTRAINT_VALIDATION_IMPLEMENTED=True
P15_7_REDEFINES_CORE_SEMANTICS=False
P15_7_CAD_RENDERING_IMPLEMENTED=False
P15_7_IMPLICIT_PHYSICAL_UNIT_INFERENCE=False
P15_7_GENERAL_EXPRESSION_EVALUATION_IMPLEMENTED=False
P15_7_DERIVED_PARAMETER_EVALUATION_IMPLEMENTED=False
P15_7_GENERAL_CONSTRAINT_SOLVER_IMPLEMENTED=False
P15_7_OPENSCAD_EXECUTION_IMPLEMENTED=False
P15_7_OPENSCAD_RENDERING_IMPLEMENTED=False
P15_7_GEOMETRY_KERNEL_IMPLEMENTED=False
P15_7_MESH_GENERATION_IMPLEMENTED=False
P15_7_FABRICATION_PLANNING_IMPLEMENTED=False
P15_7_GCODE_GENERATION_IMPLEMENTED=False
P15_7_PHYSICAL_ACTUATION_IMPLEMENTED=False
P15_7_VARIANT_CONSTRUCTION_EXECUTES_GEOMETRY=False
P15_7_REDEFINES_DOMAIN_PLATFORM=False
P15_7_REDEFINES_DOMAIN_INTERCHANGE=False
P15_7_AGENT_DRIVEN_PARAMETER_MUTATION_IMPLEMENTED=False
P15_7_VALID_PARAMETRIC_RECORD_GRANTS_TRUST=False
P15_7_PARAMETRIC_VALIDATION_PROVES_ENGINEERING_SAFETY=False
P15_7_PARAMETRIC_GRANTS_AUTHORITY=False
P15_7_PARAMETRIC_INVOKES_AUTHORITY_ENGINE=False
P15_7_EXECUTES_AIR=False
P15_7_EXECUTES_RUNTIME=False
P15_7_DISPATCHES_NATIVE=False
P15_7_COMPILES=False
P15_7_EXECUTES_CAD_CODE=False
P15_7_NETWORK_ACCESS=False
P15_7_FILESYSTEM_DISCOVERY=False
P15_7_HOST_COMMAND_EXECUTION=False
P15_7_INSTALLS_PACKAGES=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_PARAMETRIC_PLATFORM_MODEL=PASS
P15_PARAMETRIC_DESIGN_IDENTITY=PASS
P15_PARAMETER_MODEL=PASS
P15_PARAMETER_NUMERIC_MODEL=PASS
P15_PARAMETER_UNIT_MODEL=PASS
P15_PARAMETER_ASSIGNMENT_MODEL=PASS
P15_PARAMETER_GRAPH_MODEL=PASS
P15_PARAMETER_CONSTRAINT_MODEL=PASS
P15_PARAMETRIC_VARIANT_MODEL=PASS
P15_PARAMETRIC_ARTIFACT_MODEL=PASS
P15_PARAMETRIC_PROVENANCE=PASS
P15_PARAMETRIC_DETERMINISM=PASS
P15_PARAMETRIC_TRUST_BOUNDARY=PASS
P15_PARAMETRIC_AUTHORITY_BOUNDARY=PASS
P15_PARAMETRIC_SECURITY_BOUNDARY=PASS
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
P15_7_READY_FOR_REVIEW=True
```

