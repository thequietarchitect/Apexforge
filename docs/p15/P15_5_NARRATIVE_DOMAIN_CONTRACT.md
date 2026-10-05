# P15.5 — Narrative domain contract and state graph foundation

Review evidence; the owner retains milestone authority. No completion/freeze or release declaration is made.

## Frozen baseline and incoming evidence

Branch `p15-1-domain-platform-contract-sdk`; HEAD `0731e9c00b2858079007dbafdb0e052f497fb24c`. P14 branch remains at that commit. Tag `afp-p14.13-freeze` object `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target equals HEAD. Exactly twelve intended untracked P15 candidates were captured before implementation, with empty tracked/staged diffs and no generated residue. All twelve hashes were recaptured unchanged. Package crypto stays CRYPTO_PROVIDER_UNAVAILABLE; Git-signing UNSIGNED is a distinct predecessor state.

| Incoming file | SHA-256 |
| --- | --- |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/apexmotion_simulation.py | EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
| docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md | F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A |
| docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md | 4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A |
| docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md | F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4 |
| docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md | 861DD7D3409081569B31C2537702E4DE01E57A679369FCD817A4C08395A6D59D |

## Frozen narrative census and ownership

| Contract | Classification and use |
| --- | --- |
| language/narrative_model.py, P11.5B and P11.6K | REUSE / FROZEN_NARRATIVE_CONTRACT: all thirteen exact immutable types, NarrativeIdentity(kind,path), character, scene/prose, dialogue, choice/path, perspective, timeline, state/fact, continuity and story |
| language/narrative_graph.py, P11.5C | REUSE / FROZEN_NARRATIVE_CONTRACT: unchanged deterministic graph builder, declared/referenced nodes and fixed relation vocabulary |
| language/narrative_validation.py, P11.5D | REFERENCE_ONLY: passive findings, not an execution or external-truth validator |
| narrative source/parser/lowering and P11.5E–I | FROZEN_NARRATIVE_CONTRACT / REFERENCE_ONLY; no parser/lowering invocation or semantic change |
| P11.6 execution/session/transition | REFERENCE_ONLY; no domain transition implemented and no runtime import |
| P11.6K prose and P11.6L content ordering | REUSE: authored text and semantic tuple order preserved exactly |
| P11.14 agent-character binding | DEFER_TO_P15_6; narrative characters do not create agents |
| P15.1 descriptor/artifact/request/result; P15.2 interchange | REUSE; exact package/revision binding and passive exchange |
| Domain event declarations, causal references and branch lineage | DOMAIN_EXTENSION_POINT; bounded ecosystem records, not new language identity kinds |

P11 owns narrative semantics and canonical identities. P15 owns only these domain containers. No competing character, scene, choice, perspective, timeline or language-state definitions were added. Existing roles remain NarrativeStateFact narrative declarations, never authority roles. Character is not human identity or agent; story/state is not package, organization or physical world.

## Platform and records

`apexforge.narrative` has explicit domain kind narrative, contract revision 1.0.0 and exact P14 implementation coordinate/content binding through P15.1. Its minimal operations are narrative.state.describe, narrative.graph.describe and narrative.branch.describe; capability narrative.describe is a typed declaration, not permission. No generic dispatch executes these operations.

NarrativeSnapshot contains one exact frozen NarrativeStory, supplied domain events, supplied causal relations and canonical provenance references. Story identity is the world identity; frozen narrative_state identities identify declared states. Scenes, character participants, choices, alternative destinations, perspectives and timeline scene order remain P11 objects. Scene titles/bodies and dialogue text are projected verbatim, including whitespace/LF. Snapshot fingerprints include both the exact frozen story projection and its frozen graph. The domain fingerprint is distinct from any P11 artifact/material identity and does not replace it.

NarrativeEvent is a domain-only declaration with caller-supplied validated opaque identifier, existing scene identity, declared character participants, exact ordinal from 0 through 2^63−1, and passive provenance. It is not a new P11 event identity kind and executes nothing. Event participants are an unordered set canonicalized by frozen kind/path; duplicate participants fail. Event IDs and ordinals must be unique. Events are canonically ordered by ordinal; no wall-clock time is consulted.

The frozen graph's source tuple order remains meaningful and is preserved. Permuting a frozen timeline, choice path list, scene/prose collection or other semantic tuple is not assumed equivalent. Only domain event and causal collections are unordered at admission. No sorting rewrites frozen semantic content. Graph construction and domain collection processing are iterative; generic projection recursion follows the fixed bounded P11 record hierarchy, not graph edges.

## Validation, relationships and choices

The domain snapshot requires a closed declared narrative universe: duplicate declared identities, referenced-only/dangling frozen references, duplicate state subject/name facts and duplicate choice labels fail with deterministic domain codes. This is a narrow domain admission requirement; P11 still accepts its passive duplicate/unresolved evidence unchanged. Domain events must reference declared scenes/characters. Duplicate event IDs/ordinals, dangling causal endpoints, duplicate causal pairs (including differing evidence), invalid types and mutable collections fail closed.

The domain does not redefine frozen graph relation semantics or validate every narrative continuity claim. It preserves P11 relations such as contains, occurs_in, spoken_by, participant, leads_to, viewpoint, timeline_scene, precedes, state_subject and continuity_subject. Repeated frozen relation evidence is not reinterpreted or erased. No blanket cycle rejection is added. Supplied narrative-cause edges may form cycles or self-reference and remain assertions; no verified external cause or temporal ordering is inferred from them. Temporal continuity analysis remains with frozen P11 validators, not a new domain semantic engine.

Choices and their ordered alternatives are the frozen NarrativeChoice/Path objects. No automatic selection, condition evaluation, consequence execution or branch merge exists. NarrativeBranch is a passive caller-supplied lineage record: branch ID, complete parent snapshot reference, selected frozen choice and explicit alternative index, declared state reference and provenance. Parent fingerprint, world, alternative contents and state identity are bound. Missing choice/state or out-of-range alternative fails. Parent history remains unchanged; a branch records a supplied selection, not an executed transition or inferred action. Structural state advancement is deferred to avoid duplicating P11 transition ownership.

Perspective/viewpoint reuses frozen NarrativePerspective, whose optional character reference does not imply a human mental state. Every event/snapshot is marked NARRATIVE_DECLARATION; no verified external fact, authorship, participant authentication, causation or physical truth is produced. Provenance references retain evidence identity only. EVIDENCE_BEFORE_ATTRIBUTION=True.

## SDK, interchange, identity and security

narrative_artifact wraps a validated snapshot/branch's deterministic UTF-8 bytes in a P15.1 model artifact using an existing describe operation. Exact platform identity, descriptor revision, implementation coordinate/content, provenance and caller-supplied semantic/AIR/symbol references remain SDK-owned. The payload digest binds exact bytes; the domain record fingerprint is domain-separated. P15.2 transports the generic artifact/request/result reference; no new top-level protocol or typed payload parser exists. Scene/event/choice records travel within the snapshot. SDK COMPLETE remains passive caller declaration and does not prove execution. Narrative artifacts are not P14 package artifacts.

Fingerprints use the P15.1 canonical model helper with distinct domains apexforge.narrative.event/v1, causal-relation/v1, state-graph/v1 and branch/v1. Sorted compact JSON keys, UTF-8 and explicit ordered collections yield stable records, diagnostics and hashes. There are no timestamps, random IDs, host paths or process identities. Canonical AIR remains semantic authority; domain content cannot supersede it.

Semantic production inspection shows only frozen dataclass records, graph projection, explicit SDK constructors/validators and package/reference identities are called. No RuntimeEngine, AIR evaluator, native dispatch, compiler, AuthorityEngine, shell/subprocess, dynamic import, filesystem discovery, network, installation, narrative-code execution, agent creation, AI service or physical operation exists. AST import/direct-call checks supplement this inspection. No package trust, publication status, authority or real-world attribution is inferred. P15.6 agent work, generation, adapters and freeze remain untouched.

## Validation and historical-check classification

Focused P15.5: 29/29 PASS. Tests cover exact SDK/package binding, frozen identities/order/prose, immutable models, event order/permutation, duplicate/dangling records and edges, cyclic narrative relations, ordered choices, branch references/history, fact/perspective boundaries, provenance, artifacts through request/result/interchange, deterministic fingerprints, 1,000-event collection and static security. Scale evidence is not benchmark certification.

Commands use prefix `python -X utf8 -B`:

| Command | Final result |
| --- | --- |
| apexforge/p15_5_narrative_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| -m unittest discover -s apexforge -p p15_*_test.py | 152/152 PASS |
| -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| apexforge/authority_consolidation_smoke_test.py | canonical identities, exact grant, wrong principal/capability/resource denial, authorized RuntimeEngine execution, transactional denial PASS |

Selected P11 checks were invoked with `-c`, adding apexforge to sys.path and calling named functions directly, excluding inventory-sensitive main gates:

* p11_5c_narrative_semantic_graph_construction_smoke_test.test_public_graph_model_contract and test_deterministic_projection_and_duplicate_evidence: PASS.
* p11_5d_passive_narrative_graph_validation_smoke_test.test_public_result_model_contract and test_experimental_classification_contract: PASS.
* p11_6k_canonical_narrative_prose_model_smoke_test.test_model_source_and_exact_prose_contract: PASS, independently rerun.

Two attempted historical invocations are explicitly not PASS:

1. P11.5B test_public_api_fields_and_frozen_records expects NarrativeScene(identity) only and fails because title/body were deliberately added by frozen P11.6K. CLASSIFICATION=NARRATIVE_DOMAIN_MODEL_GAP (historical evidence applicability, not a production regression). The later authoritative P11.6K prose contract resolves the apparent contradiction. The remaining functions in that combined command were not reached.
2. A combined P11.6K/L command passed K, then P11.6L test_existing_order_artifact_material_and_rendering failed because the historical examples/P11Validation/apexforge.json fixture is absent. CLASSIFICATION=NARRATIVE_DOMAIN_MODEL_GAP (historical fixture applicability). Its subsequent determinism check was not reached. No fixture was created, assertions weakened or frozen source patched. The report makes no full P11 harness PASS claim.

The architecture-preserving path was to retain frozen sources, record historical limitations, execute directly applicable graph/prose checks and establish hash equality. No P15.5 production failure was discovered. PATCH_MATRIX=PASS applies to the active slice and preservation gates; it does not erase those historical failures.

## Frozen-source and preservation audit

Frozen P11 source identities: git hash-object equals HEAD:path for each source:

| Source | HEAD and working-tree Git blob | Current SHA-256 |
| --- | --- | --- |
| language/narrative_model.py | f0d3cb2a93cf4867610fd7c84efc3f096bcb5a68 | CEA560E3277C2340A66BF7423D46B29386589BB4CD21D3AA1DCE0FE7F648FC8D |
| language/narrative_graph.py | 0db2203a5fca3de7cdfbbbcd9e374dcc7803201b | 0373CE16722784DDE988A2B15BD04B544DCB3A3D2094B36444C55201F24C5B2A |
| language/narrative_validation.py | 0e1ae9743f900e4a685901f488c23fc61d8330d0 | 83B6F9D361BDB0BDC3D30C3627B4632EB1322FEE6D9A4C0B4273B97F25FEFD6A |

Tracked diff and staged diff are empty; therefore no frozen P14/P13/P12/P11/P10 file changed. P14 branch, tag object, peeled target and HEAD remain unchanged. All twelve incoming hashes match. Only the three intended P15.5 files were added, giving fifteen untracked candidates. No generated residue was found under apexforge/docs (cache directories or pyc/pyo/exe/dll/pdb/obj/vsix). Nothing staged, committed, tagged or pushed. No later domain, agent, generation, adapter or freeze work was done.

Exact final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/p15_5_narrative_domain_contract_test.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/apexmotion_simulation.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/narrative_domain.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
?? docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
?? docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md
```

## Evidence markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_5_INCOMING_CANDIDATES=12
P15_5_NARRATIVE_USES_P15_DOMAIN_PLATFORM=True
P15_5_NARRATIVE_GRAPH_DETERMINISTIC=True
P15_5_REDEFINES_FROZEN_NARRATIVE_SEMANTICS=False
P15_5_AUTONOMOUS_NARRATIVE_GENERATION_IMPLEMENTED=False
P15_5_NARRATIVE_EVENT_EXECUTION_IMPLEMENTED=False
P15_5_NARRATIVE_CAUSALITY_GRANTS_FACT_STATUS=False
P15_5_AUTONOMOUS_CHOICE_SELECTION_IMPLEMENTED=False
P15_5_AUTOMATIC_BRANCH_MERGE_IMPLEMENTED=False
P15_5_NARRATIVE_RECORD_PROVES_REAL_WORLD_FACT=False
P15_5_REDEFINES_DOMAIN_PLATFORM=False
P15_5_REDEFINES_DOMAIN_INTERCHANGE=False
P15_5_AGENT_EXECUTION_IMPLEMENTED=False
P15_5_AUTONOMOUS_CHARACTERS_IMPLEMENTED=False
P15_5_GENERATIVE_MODEL_INVOCATION=False
P15_5_VALID_NARRATIVE_GRANTS_TRUST=False
P15_5_NARRATIVE_GRANTS_AUTHORITY=False
P15_5_NARRATIVE_INVOKES_AUTHORITY_ENGINE=False
P15_5_EXECUTES_AIR=False
P15_5_EXECUTES_RUNTIME=False
P15_5_DISPATCHES_NATIVE=False
P15_5_COMPILES=False
P15_5_EXECUTES_NARRATIVE_CODE=False
P15_5_NETWORK_ACCESS=False
P15_5_FILESYSTEM_DISCOVERY=False
P15_5_INSTALLS_PACKAGES=False
P15_5_HOST_COMMAND_EXECUTION=False
P15_5_STRUCTURAL_STATE_TRANSITION_IMPLEMENTED=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_NARRATIVE_PLATFORM_MODEL=PASS
P15_NARRATIVE_ENTITY_MODEL=PASS
P15_NARRATIVE_SCENE_MODEL=PASS
P15_NARRATIVE_EVENT_MODEL=PASS
P15_NARRATIVE_GRAPH_MODEL=PASS
P15_NARRATIVE_CHOICE_MODEL=PASS
P15_NARRATIVE_BRANCH_MODEL=PASS
P15_NARRATIVE_CAUSALITY_BOUNDARY=PASS
P15_NARRATIVE_PROVENANCE=PASS
P15_NARRATIVE_FACT_BOUNDARY=PASS
P15_NARRATIVE_DETERMINISM=PASS
P15_NARRATIVE_SECURITY_BOUNDARY=PASS
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
P15_5_READY_FOR_REVIEW=True
```

