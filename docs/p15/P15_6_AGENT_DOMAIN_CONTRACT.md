# P15.6 — Agent domain contract, session ledger and controlled action intents

Evidence for owner review; no release, freeze or milestone completion declaration.

## Baseline and incoming hashes

Branch remains `p15-1-domain-platform-contract-sdk`. HEAD and P14 frozen branch remain `0731e9c00b2858079007dbafdb0e052f497fb24c`. P14 tag `afp-p14.13-freeze` remains object `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`, peeled target HEAD. Before implementation exactly fifteen intended P15 candidates existed; tracked/staged diffs were empty and generated residue absent. All fifteen SHA-256 values were subsequently recaptured unchanged.

| Incoming path | SHA-256 |
| --- | --- |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/p15_5_narrative_domain_contract_test.py | FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E |
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

## Architecture census and reuse

| Existing concept | Classification / boundary |
| --- | --- |
| agents/model.py AgentIdentity, AgentDefinition, ProfessionalArchetype | REUSE / FROZEN_IDENTITY_CONTRACT: exact passive agent identity and descriptive archetype order retained |
| agents/catalog.py and resolution.py | REFERENCE_ONLY; no archetype resolution required for this ledger |
| agents/planning.py AgentPlan and effects/model.py EffectIntent | REFERENCE_ONLY: existing host-effect/AIR-related intents are not redefined or dispatched; P15 domain intent is typed session evidence and has no automatic mapping |
| agents/execution.py and plan_projection.py | REFERENCE_ONLY; no import or invocation |
| agents/character_binding.py | REFERENCE_ONLY; frozen explicit agent/character mapping remains separate, no narrative promotion |
| authority/model.py Principal, AuthorityCheck, AuthorityGrant and engine.py | FROZEN_AUTHORITY_CONTRACT; no production import, check or grant |
| tooling/debug_session.py retained session records | REFERENCE_ONLY / frozen P13 control contract; lineage/immutability is a pattern, debugger control/authority is not reused |
| P15.1 SDK and exact P14 package/reference identities | REUSE; authoritative typed bindings and canonical helpers |
| P15.2 interchange | REUSE; generic artifact/request/result transport owns its schema |
| Agent descriptor, task, context, observation/decision/receipt, session ledger | AGENT_DOMAIN_EXTENSION_POINT |
| Model/provider/tool adapters | DEFER_TO_EXTERNAL_ADAPTER |
| Delegation, spawning, multi-agent/background operation | DEFER_TO_ORCHESTRATION |

No second AgentIdentity was created. Production imports the exact frozen agents.model.AgentIdentity and AgentDefinition. Agent identity remains an opaque caller-supplied canonical ID, independent of descriptive archetypes, session, package, model, human, organization, principal, capability and authority. Even equal strings in different domains confer no relation or permission. Descriptive archetypes are preserved in their supplied order and never become authority roles. No human delegation, model affiliation or sentience inference exists.

## Platform, descriptor and tasks

Agent platform `apexforge.agent`, kind agent, contract 1.0.0 uses the P15.1 DomainPlatformDescriptor with exact P14 package coordinate/content. Its only operations are agent.descriptor.describe and agent.session.describe; domain capability agent.describe is declarative. Individual AgentDescriptor binds the frozen AgentDefinition, exact platform descriptor/fingerprint and package, contract revision, declared action/observation names, required domain capabilities and passive provenance. Declaration collections canonicalize; duplicate or malformed entries fail. Unknown descriptor contract version fails closed. No hidden provider, execution permission, credential or authority field exists.

AgentTask binds a validated ID, explicit objective (1–4096 characters), canonical input references and provenance. Task construction is passive and grants no authority. Optional domain constraints can be carried by explicit reference evidence; no task solver or execution exists.

AgentSessionIdentity is a separate immutable typed identifier. AgentContext binds it to the exact agent descriptor fingerprint, frozen agent canonical ID and implementation package. There is no implicit environment or machine identity discovery.

## Observations, decisions and intents

AgentObservation binds ID, exact context, a declared observation kind, canonical evidence references and provenance. It is CALLER_SUPPLIED, not a verified fact or authenticated external event.

AgentDecision binds exact context, prior observation fingerprints, canonical explicit alternatives and optional caller-supplied selection. Selections must belong to declared alternatives. No private/internal reasoning trace, model prompt, chain-of-thought or cognition field exists. The audit record states private_reasoning_captured=False. Decision construction neither evaluates alternatives nor chooses one.

AgentActionIntent binds exact context, declared action, exact target CanonicalReference, typed ActionCapabilityRequirement, canonical argument/reference evidence, optional passive tool reference, optional prior decision fingerprint and provenance. Arguments are references only, not arbitrary executable objects or callback payloads. An intent's execution is NOT_PERFORMED and authority false. ActionCapabilityRequirement is distinct from P15 DomainCapability and P14 package capabilities; neither constitutes a runtime grant. A tool reference is not imported or invoked.

AgentActionReceipt is an externally supplied claim: ID/context, exact intent fingerprint, bounded SUCCEEDED/FAILED/UNKNOWN status, output references and provenance. Even SUCCEEDED is labelled EXTERNALLY_SUPPLIED with execution_verified=False. No receipt is synthesized by the append operation. P15.6 does not claim any tool/action occurred or was authorized.

## Session ledger and lineage

AgentSessionSnapshot is immutable and contains exact context, task, ordered typed event tuple, optional predecessor fingerprint and provenance. Supported events are supplied observation, decision, intent and external receipt records. Task is separately bound at session creation. No status event, automatic completion, scheduling or event synthesis is implemented. The ledger is capped at 4096 records and uses one-based sequence positions derived from the explicitly supplied tuple order. Event IDs must be unique across categories, preventing duplicate/conflicting event substitution. Every event context must equal the session context. Decisions reference earlier observations; intent decision references must be earlier decisions; receipts must reference earlier exact intents. Dangling/forward/mismatched references fail with stable codes. Order is semantic and is never fingerprint-sorted.

`append_event(old, explicit_event)` constructs a new snapshot containing precisely the old ledger plus that event, retaining context/task/provenance and binding predecessor_fingerprint=old.fingerprint(). The old snapshot remains unchanged. Failed admission cannot mutate it. This is structural bookkeeping, not agent execution. Supplied batch snapshots may begin with an existing ledger; an externally supplied predecessor fingerprint is a passive syntactically validated reference. Without its predecessor object it is not proof of earlier history. The append function demonstrates the exact old/new transition; it does not authenticate imported session history. No recursive predecessor-object nesting or background loop exists.

Snapshot fingerprints bind all canonical event contents, event fingerprints, sequence, context, task, provenance and predecessor reference. Record identities are domain-separated under apexforge.agent descriptor/context/task/session/observation/decision/action-intent/action-receipt schemas. Frozen AgentIdentity retains its own structural identity owner rather than receiving a competing P15 identity algorithm. Canonical SDK JSON uses sorted keys, compact separators and UTF-8. No wall clock, random ID, thread, locale, host path or process identity participates.

## Artifacts, provenance and security

agent_artifact wraps descriptor or full snapshot as a P15.1 model artifact, with payload containing both canonical record and explicit record_fingerprint. The artifact retains exact platform/package/descriptor revision, raw byte digest, supplied semantic/AIR/symbol references and provenance. Observations/decisions/intents/receipts travel within the full ledger. P15.2 generic interchange preserves request/result/artifact bindings; there is no new top-level protocol, typed payload decoder or execution endpoint. SDK COMPLETE remains a passive declaration. Agent artifacts are not P14 package artifacts. Canonical AIR remains semantic authority.

Provenance references are canonical evidence, never real-world authorship, verified human identity, organizational representation, action success or consciousness proof. EVIDENCE_BEFORE_ATTRIBUTION=True. CRYPTO_PROVIDER_UNAVAILABLE remains preserved; no crypto/model dependency or signing software was installed. Git predecessor UNSIGNED is distinct from package verification availability.

Semantic inspection: production imports only dataclasses/re, frozen agents.model, passive SDK and P14 reference identities. Calls validate exact types/declarations/references, construct immutable records, serialize/fingerprint them and append supplied tuples. There is no AuthorityEngine invocation, runtime workload, AIR evaluation, native dispatch, tool/agent/domain code execution, compiler, shell/subprocess, model inference, callback execution, network, filesystem discovery, credentials, secret persistence, pickle or dynamic import. AST import/direct-call checks supplement semantic inspection. Test-only authority smoke invokes its existing RuntimeEngine fixture, not production agent records.

No spawning, multi-agent orchestration, delegation, autonomy loop, autonomous choices, narrative-character promotion, external adapter or later P15 feature exists. A valid record establishes only structural consistency; it grants no trust, permission, factual accuracy or sentience evidence.

## Focused validation, corrections and regressions

Two narrow pre-review corrections stayed within P15.6: AGENT_DESCRIPTOR_GAP corrected ExactVersion serialization to its frozen text() representation; AGENT_DOMAIN_MODEL_GAP added explicit record_fingerprint to artifact payload instead of relying solely on raw byte digest. Malformed declaration/reference collection admission was also guarded locally. No predecessor owning defect was found and no assertions were weakened. The final focused and P15 aggregate checks passed after the artifact correction.

Commands use `python -X utf8 -B`:

| Command | Result |
| --- | --- |
| apexforge/p15_6_agent_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_5_narrative_domain_contract_test.py | 29/29 PASS |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| apexforge/p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| apexforge/p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| -m unittest discover -s apexforge -p p15_*_test.py | 181/181 PASS |
| -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| apexforge/authority_consolidation_smoke_test.py | canonical identities, exact grant, wrong principal/capability/resource denial, authorized execution and transactional denial PASS |

Direct frozen identity check command:

```text
python -X utf8 -B -c "import sys, importlib; sys.path.insert(0, 'apexforge'); import p11_14b_minimal_immutable_agent_domain_model_smoke_test as checks; checks.assert_model_contract(importlib.import_module('agents.model')); checks.assert_package_surface(); print('Frozen agent identity/archetype/definition and package surface: PASS')"
```

Both selected frozen identity/package-surface behavioral checks PASS; inventory-sensitive historical gates were excluded. Production identity/role/capability/authority separation is also tested using exact frozen AgentIdentity, Principal, typed session/domain/action capability and NarrativeIdentity values. No authority semantics changed.

The 1,000-event test constructs equivalent iterative ledgers, obtains equal fingerprints, checks full serialization and appends one explicit event with exact predecessor binding. This is deterministic scale evidence, not a performance benchmark. Focused coverage includes immutable records, action/observation declarations, references and order, duplicate/conflicting events, cross-session contexts, invalid choices/status, canonical permutations, provenance and SDK/interchange.

Historical P15.5 limitations remain unchanged: the P11.5B field-expectation test predates authoritative P11.6K prose fields; the examples/P11Validation fixture is absent. Neither old test nor fixture was modified or made a dependency of P15.6. No new test failure was observed in P15.6.

## Final preservation and Git status

All fifteen incoming hashes preserved. Branch/HEAD, P14 frozen branch/tag object/peeled target unchanged. Empty tracked and cached diffs establish no frozen P14/P13/P12/P11/P10, authority, identity or narrative source changed. No generated residue found under apexforge/docs (cache directories or pyc/pyo/exe/dll/pdb/obj/vsix). Only three intended P15.6 files added, giving eighteen candidates. No staging, commit, tag, push, P15.7, provider/tool integration, orchestration or freeze work.

Exact final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/p15_5_narrative_domain_contract_test.py
?? apexforge/p15_6_agent_domain_contract_test.py
?? apexforge/tooling/agent_domain.py
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
?? docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md
```

## Evidence markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_6_INCOMING_CANDIDATES=15
P15_6_AGENT_USES_P15_DOMAIN_PLATFORM=True
P15_6_SESSION_IDENTITY_DISTINCT_FROM_AGENT_IDENTITY=True
P15_6_AGENT_SESSION_IMMUTABLE=True
P15_6_SESSION_LINEAGE_EXPLICIT=True
P15_6_SESSION_LEDGER_DETERMINISTIC=True
P15_6_STRUCTURAL_SESSION_TRANSITION_IMPLEMENTED=True
P15_6_REDEFINES_CORE_SEMANTICS=False
P15_6_AGENT_DESCRIPTOR_GRANTS_AUTHORITY=False
P15_6_CHAIN_OF_THOUGHT_CAPTURE_IMPLEMENTED=False
P15_6_ACTION_INTENT_EXECUTES=False
P15_6_ACTION_INTENT_GRANTS_AUTHORITY=False
P15_6_TOOL_EXECUTION_IMPLEMENTED=False
P15_6_AGENT_GRANTS_AUTHORITY=False
P15_6_AGENT_INVOKES_AUTHORITY_ENGINE=False
P15_6_AGENT_SPAWNING_IMPLEMENTED=False
P15_6_MULTI_AGENT_ORCHESTRATION_IMPLEMENTED=False
P15_6_BACKGROUND_AUTONOMY_IMPLEMENTED=False
P15_6_HUMAN_AGENT_DELEGATION_IMPLEMENTED=False
P15_6_AGENT_RECORD_PROVES_SENTIENCE=False
P15_6_MODEL_INVOCATION_IMPLEMENTED=False
P15_6_EXTERNAL_AFFILIATION_INFERRED=False
P15_6_REDEFINES_DOMAIN_PLATFORM=False
P15_6_REDEFINES_DOMAIN_INTERCHANGE=False
P15_6_NARRATIVE_CHARACTER_AUTO_PROMOTION=False
P15_6_VALID_AGENT_RECORD_GRANTS_TRUST=False
P15_6_EXECUTES_AIR=False
P15_6_EXECUTES_RUNTIME=False
P15_6_DISPATCHES_NATIVE=False
P15_6_EXECUTES_AGENT_CODE=False
P15_6_EXECUTES_TOOLS=False
P15_6_HOST_COMMAND_EXECUTION=False
P15_6_NETWORK_ACCESS=False
P15_6_FILESYSTEM_DISCOVERY=False
P15_6_INSTALLS_PACKAGES=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_AGENT_PLATFORM_MODEL=PASS
P15_AGENT_IDENTITY_MODEL=PASS
P15_AGENT_DESCRIPTOR_MODEL=PASS
P15_AGENT_SESSION_MODEL=PASS
P15_AGENT_SESSION_LINEAGE=PASS
P15_AGENT_OBSERVATION_MODEL=PASS
P15_AGENT_DECISION_MODEL=PASS
P15_AGENT_ACTION_INTENT_MODEL=PASS
P15_AGENT_EVENT_LEDGER=PASS
P15_AGENT_CAPABILITY_BOUNDARY=PASS
P15_AGENT_IDENTITY_BOUNDARY=PASS
P15_AGENT_AUTHORITY_BOUNDARY=PASS
P15_AGENT_PROVENANCE=PASS
P15_AGENT_DETERMINISM=PASS
P15_AGENT_SECURITY_BOUNDARY=PASS
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
P15_6_READY_FOR_REVIEW=True
```

