# P15.10 Domain Governance, Policy & Registration — Review Evidence

P15.10 implements deterministic structural policy conformance and immutable registration catalogs. This report requests review; it does not declare a release, canonization or freeze. No staging, commit, tag or push was performed.

## Baseline

Branch: `p15-1-domain-platform-contract-sdk`.
HEAD and frozen P14 branch `p14-1-package-identity-manifest`: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Frozen predecessor: `afp-p14.13-freeze`; annotated object `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target `0731e9c00b2858079007dbafdb0e052f497fb24c`.

Baseline audit demonstrated exactly 27 incoming candidates, empty tracked/staged diffs and no generated residue. All incoming SHA-256 hashes below are preserved. No frozen P10–P14 or earlier P15 file changed.

| Incoming file | SHA-256 |
|---|---|
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/p15_5_narrative_domain_contract_test.py | FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E |
| apexforge/p15_6_agent_domain_contract_test.py | 1197B2D82E28EA4B91F240946387AECE8E41FEEE788F824E021DD630F65CF5C5 |
| apexforge/p15_7_parametric_domain_contract_test.py | BF70EBF1ABD171685330F6D2800878E721B6882CDE20108447EB20E7067945A8 |
| apexforge/p15_8_fabrication_domain_contract_test.py | 8C07880ACD1B05014DBD31FB6B8AD261C6E9EEFBC35D695D3EEE332EBA1612C8 |
| apexforge/p15_9_external_adapter_contract_test.py | 3542D42D2C6E9D6921CE709911BB060450DC811DD38E7096862ECEF508E45CAE |
| apexforge/tooling/agent_domain.py | A56E46EF274C8A9B81E0E6D8B90933B30A17996C7FB752284C891D145E312864 |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/apexmotion_simulation.py | EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
| apexforge/tooling/external_adapter.py | 16A22CA591AB15D9EC0EBEF57019AD11C1536FC7C46808D72B4237DCDCC9BFD1 |
| apexforge/tooling/fabrication_domain.py | 402328AC62FA4E2D767D35290842EC056ADD7D5B6C1F60F01EE1D8D8A005B829 |
| apexforge/tooling/narrative_domain.py | BA1284F04FC4DF4C63172E64AE8933E960C07979B1D597C7AB780253B85073DC |
| apexforge/tooling/parametric_domain.py | 1F8E096C3CC78ED89C8452445C8456215735F4165AAC71BC2C55EADED09D3036 |
| docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md | F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A |
| docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md | 4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A |
| docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md | F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4 |
| docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md | 861DD7D3409081569B31C2537702E4DE01E57A679369FCD817A4C08395A6D59D |
| docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md | BA359C40CFE4A61D56883C2A5F075719C7E36303B23F630B76890E2AA8EEE151 |
| docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md | AD9A937754E811461595B5D8488B515D4CFCF32CFB74E74C18D76F6A35FD4769 |
| docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md | C27D8D09E1DB62DFE751B60A4796478BA1D178545C6974A7BEAA2CE881E38EFD |
| docs/p15/P15_8_FABRICATION_DOMAIN_CONTRACT.md | 8E9FA8E8EE830C3A67C1ADEFEBA28B133A8D71F3D83C91AADAECC66F8E65904D |
| docs/p15/P15_9_EXTERNAL_ADAPTER_CONTRACT.md | C890336E3B28E6CF28A14F2719FE89E67EAF21F8A6EE44CC480686CFE2A45326 |

## Architecture census

| Existing owner | Classification | P15.10 relationship |
|---|---|---|
| P15.1 DomainPlatformDescriptor, ImplementationPackage, CanonicalModel | REUSE | Authoritative descriptor/package types and deterministic serialization/fingerprints |
| P14 CanonicalReference and ExactVersion | REUSE | Supplied evidence lineage and explicit version |
| authority/model.py Principal, AuthorityCheck, AuthorityGrant | FROZEN_AUTHORITY_CONTRACT | Runtime permission remains separately owned; no import/invocation |
| tooling/package_trust.py TrustPolicy, NamespaceTrustRule, TrustAnchor | FROZEN_TRUST_CONTRACT | Signing/trust interpretation remains P14-owned |
| tooling/package_registry.py supplied immutable package protocol | REFERENCE_ONLY | Package availability is distinct from governance conformance; no mutation |
| agents/catalog.py ProfessionalArchetypeCatalog | REFERENCE_ONLY | Immutable exact-typed catalog pattern; archetype/agent identity not duplicated |
| quad_vector/admission.py frozen authored-module admission | REFERENCE_ONLY | Registration without binding/loading/execution; semantics remain frozen |
| P15.2 generic interchange | REUSE / REFERENCE_ONLY | Remains generic serialization owner; no new parser or transport |
| P15.6 agent, P15.9 provider/adapter identities | REFERENCE_ONLY | Admission of their domain descriptors does not authorize/create agents or authenticate providers |
| New governance policy/evidence/candidate/decision/catalog | GOVERNANCE_EXTENSION_POINT | Bounded supplied-evidence structural contracts |
| Cross-domain execution ordering/workflows | DEFER_TO_P15_11 | No dispatch or artifact movement |
| Authority/trust integration and authentication | DEFER_TO_P15_12 | Separate evidence/decisions, no conformance-to-permission conversion |

Frozen authority policy and trust policy are not domain governance policy. GovernanceDecision is a separate type with ADMISSIBLE/REJECTED/INCOMPLETE/CONFLICT outcomes, never AUTHORIZED/TRUSTED/AUTHENTICATED. No existing identity, authority, trust or registry owner is modified.

## Policy and evidence contracts

DomainGovernancePolicyIdentity is an immutable opaque validated identifier, distinct from platform/package/organization/authority/trust identities. DomainGovernancePolicy has schema `apexforge.domain-governance-policy/v1`, an explicit P14 ExactVersion, permitted SDK kinds, required evidence categories and a provenance-presence requirement.

Rules are bounded static fields. Required evidence categories are contract, review and boundary; any subset may be explicitly selected. Descriptor schema and exact P14 binding are enforced by reuse of the admitted P15.1 descriptor. Forbidden claim classes are semantic-authority, authority-grant, package-trust and provider-authentication. Conflict policy is always FAIL_CLOSED. Unknown policy schema/rules fail closed with deterministic codes. No arbitrary predicates, callbacks, executable expressions, plugin loading or general policy language exists.

GovernanceEvidence binds a category, canonical reference and exact descriptor fingerprint. Evidence is caller-supplied structural evidence, not an authenticated assertion that a human review occurred. Governance does not inspect referenced external data or authenticate its author.

DomainRegistrationCandidate binds the exact P15.1 descriptor and descriptor fingerprint, complete P14 coordinate/content identity, optional domain-specific CanonicalReference, supplied evidence, provenance and bounded claim declarations. A package name alone cannot form a candidate. Full descriptor contents and evidence are fingerprint-bound. Same name with different contract/package contents or different supplied evidence yields a different candidate fingerprint.

Malformed unsupported object structure is rejected by constructors with deterministic GovernanceError codes. Well-formed contradictory evidence is retained so evaluation can report REJECTED. Unknown claim vocabulary is a constructor error rather than arbitrary semantic extension.

## Evaluation and decisions

`evaluate(policy, candidate, catalog=None)` consumes caller-supplied evidence without mutation or hidden state. DomainGovernanceDecision retains exact policy and candidate objects; canonical records bind policy fingerprint, candidate fingerprint, descriptor fingerprint, exact implementation package and supplied evidence references.

Rules evaluate only supported domain kind, prohibited supplied claims, descriptor binding of evidence, required evidence categories and required provenance. Descriptor validity and package exactness remain frozen SDK-owned constructor guarantees. No domain-specific internal behavior is imported. All seven current SDK kinds are representable, including simulation as a generic descriptor kind.

Findings are immutable code/subject records, canonicalized by code then subject. Outcomes:
- REJECTED: disallowed kind, prohibited claim or contradictory descriptor-bound evidence.
- CONFLICT: a different existing candidate has the same registration key.
- INCOMPLETE: required evidence/provenance is absent.
- ADMISSIBLE: supplied structural evidence satisfies the explicit policy.

Precedence is REJECTED, then CONFLICT, then INCOMPLETE. Missing and contradictory findings are both retained if both occur. Finding codes include GOVERNANCE_DOMAIN_KIND_NOT_ALLOWED, GOVERNANCE_DESCRIPTOR_BINDING_INVALID, GOVERNANCE_PROHIBITED_CLAIM, GOVERNANCE_REQUIRED_EVIDENCE_MISSING, GOVERNANCE_PROVENANCE_INCOMPLETE and GOVERNANCE_REGISTRATION_CONFLICT. Constructor/admission errors include GOVERNANCE_SCHEMA_UNSUPPORTED, GOVERNANCE_POLICY_MISMATCH and GOVERNANCE_CATALOG_NOT_ADMISSIBLE. Exception prose is not canonical diagnostic identity.

Changing policy version/rules yields another fingerprint; old decisions retain their original exact policy. Changed descriptor/content/evidence requires a distinct candidate/decision. Fingerprints provide consistency, never authentication.

## Catalog, conflicts and lineage

DomainCatalogSnapshot stores one exact policy and only ADMISSIBLE decisions under that same policy. Entries retain full candidates/evidence/provenance, exact domain/descriptor/package binding and decision fingerprints. Canonical ordering is by platform identifier and contract-version text; it is deterministic ordering, not a numeric version-precedence claim.

The registration key is platform identifier plus contract version. Two different descriptors, package contents or evidence sets under the same key cannot overwrite each other. Direct conflicting catalog construction fails closed. Identical direct decisions deduplicate; `register` of an identical candidate returns the existing snapshot unchanged. Evaluation against a different policy catalog rejects policy mismatch.

`register(old, explicit_candidate)` creates a new snapshot with the exact predecessor catalog fingerprint and all prior entries. The old catalog remains immutable. Conflict decisions may be retained by callers as passive evidence but cannot enter the admitted catalog. A supplied predecessor digest on direct snapshot construction is a passive reference; only the structural register helper demonstrates preservation of actual prior entries. No supersession, withdrawal, deletion or P14 package unpublication is implemented.

Catalog presence is policy conformance only. It establishes no package trust, runtime permission, organization ownership, provider authenticity or physical safety. This catalog is not the P14 package registry.

## Integration and boundaries

P15.1 remains domain identity/descriptor/package owner. P15.2 remains generic interchange owner. Governance supplies canonical records/fingerprints and typed canonical references; no governance domain platform, competing wire format or typed JSON reconstruction is added. Future callers can bind these canonical bytes/references through existing SDK artifacts without giving them semantic authority.

P15.9 external-adapter registration cannot contact a provider or imply affiliation. Agent-domain registration cannot spawn or authorize an agent. Fabrication-domain registration cannot authorize machines or certify engineering safety. No cross-domain orchestration is implemented.

Provenance is policy -> candidate -> supplied evidence -> findings -> decision -> catalog. It does not prove real-world attribution, external authorship, authenticated review, affiliation or trust. EVIDENCE_BEFORE_ATTRIBUTION=True. CANONICAL_AIR retains semantic authority.

Package crypto remains CRYPTO_PROVIDER_UNAVAILABLE. No cryptographic governance authentication is added. Predecessor Git signing state is UNSIGNED and is separate from package crypto availability.

All production inputs are caller-supplied immutable objects. No network, filesystem discovery, environment introspection, registry crawling, credential acquisition, dynamic loading, callback execution, AIR/runtime/native/domain execution, compilation, package installation, shell or hardware access exists. Static AST audit restricts imports to dataclasses, re, the SDK and package reference/version contracts.

## Determinism and limits

Policy, registration, evidence, finding, decision and catalog fingerprints use distinct schema domains and SDK SHA-256(domain + NUL + canonical JSON). Sorted compact JSON rejects NaN, and no unconstrained numeric data or mutable arbitrary objects are accepted. Collection bounds are 4,096; SDK names are bounded to 128 characters; fingerprints are uppercase SHA-256. No wall clock, randomness, host path, process ID, locale or external state participates.

Tests build approximately 1,000 admitted registrations iteratively, reverse construction order, compare catalog fingerprints and perform exact lookup. This is determinism/scale evidence, not a performance claim.

## Validation and Patch Matrix

Focused P15.10: **24/24 PASS**.
P15.9 through P15.1 focused reruns: **28, 33, 31, 29, 29, 23, 30, 40, 30**, all PASS.
P15 aggregate: **297/297 PASS**.
P14 aggregate: **330/330 PASS**.
Native profile: **7/7 PASS**.
Authority consolidation: canonical identities, exact grant, wrong principal/capability/resource denial, authorized RuntimeEngine execution and transactional denied execution all PASS. The smoke exercises frozen authority/runtime owners; governance invokes neither.

Executed `python -X utf8 -B apexforge/p15_10_domain_governance_contract_test.py`, each predecessor focused command, P15/P14 unittest discovery, native-profile and authority-smoke commands.

Initial failure -> DOMAIN_REGISTRATION_PACKAGE_BINDING_GAP -> owning P15.10 test adapter -> frozen PackageContentIdentity uses fingerprint, not digest -> test-only patch -> exact content-revision assertion -> focused PASS -> predecessors PASS -> aggregate PASS -> frozen preservation audit -> PATCH_MATRIX=PASS. No coverage weakened, no predecessor patch. No unresolved defect found.

## Supported markers

```text
P15_BASELINE=P14_13_FREEZE
P15_10_INCOMING_CANDIDATES=27
P14_REOPENED=False
P15_10_REGISTRATION_EXACT_PACKAGE_BOUND=True
P15_10_GOVERNANCE_EVALUATION_DETERMINISTIC=True
P15_10_MISSING_EVIDENCE_DISTINCT_FROM_REJECTION=True
P15_10_CATALOG_DETERMINISTIC=True
P15_10_REGISTRATION_CONFLICT_FAILS_CLOSED=True
P15_10_DECISION_EXACT_POLICY_BOUND=True
P15_10_DECISION_EXACT_DESCRIPTOR_BOUND=True
P15_10_DECISION_EXACT_PACKAGE_CONTENT_BOUND=True
P15_10_REDEFINES_CORE_SEMANTICS=False
P15_10_GENERAL_POLICY_LANGUAGE_IMPLEMENTED=False
P15_10_GOVERNANCE_DECISION_GRANTS_AUTHORITY=False
P15_10_MUTATES_P14_REGISTRY=False
P15_10_CATALOG_PRESENCE_GRANTS_TRUST=False
P15_10_CATALOG_PRESENCE_GRANTS_AUTHORITY=False
P15_10_GOVERNANCE_INVOKES_AUTHORITY_ENGINE=False
P15_10_GOVERNANCE_GRANTS_AUTHORITY=False
P15_10_GOVERNANCE_GRANTS_PACKAGE_TRUST=False
P15_10_CRYPTOGRAPHIC_GOVERNANCE_AUTHENTICATION_IMPLEMENTED=False
P15_10_GOVERNANCE_INFERS_EXTERNAL_AFFILIATION=False
P15_10_GOVERNANCE_SPAWNS_AGENTS=False
P15_10_GOVERNANCE_AUTHORIZES_PHYSICAL_ACTUATION=False
P15_10_CROSS_DOMAIN_ORCHESTRATION_IMPLEMENTED=False
P15_10_REDEFINES_DOMAIN_PLATFORM=False
P15_10_REDEFINES_DOMAIN_INTERCHANGE=False
P15_10_EXTERNAL_ADAPTER_AUTO_DISPATCH=False
P15_10_NETWORK_ACCESS=False
P15_10_FILESYSTEM_DISCOVERY=False
P15_10_DYNAMIC_PLUGIN_LOADING_IMPLEMENTED=False
P15_10_EXECUTES_AIR=False
P15_10_EXECUTES_RUNTIME=False
P15_10_DISPATCHES_NATIVE=False
P15_10_EXECUTES_DOMAIN_CODE=False
P15_10_COMPILES=False
P15_10_INSTALLS_PACKAGES=False
P15_10_HOST_COMMAND_EXECUTION=False
P15_10_VALID_GOVERNANCE_RECORD_GRANTS_TRUST=False
P15_10_GOVERNANCE_INPUT=CALLER_SUPPLIED_EVIDENCE
CRYPTO_PROVIDER_UNAVAILABLE
EVIDENCE_BEFORE_ATTRIBUTION=True
P15_DOMAIN_GOVERNANCE_MODEL=PASS
P15_DOMAIN_GOVERNANCE_POLICY=PASS
P15_DOMAIN_GOVERNANCE_RULES=PASS
P15_DOMAIN_REGISTRATION_CANDIDATE=PASS
P15_DOMAIN_REGISTRATION_PACKAGE_BINDING=PASS
P15_DOMAIN_REGISTRATION_DESCRIPTOR_BINDING=PASS
P15_DOMAIN_GOVERNANCE_DECISION=PASS
P15_DOMAIN_GOVERNANCE_EVIDENCE_COMPLETENESS=PASS
P15_DOMAIN_GOVERNANCE_CONFLICT_HANDLING=PASS
P15_DOMAIN_GOVERNANCE_CATALOG=PASS
P15_DOMAIN_GOVERNANCE_PROVENANCE=PASS
P15_DOMAIN_GOVERNANCE_DETERMINISM=PASS
P15_DOMAIN_GOVERNANCE_TRUST_BOUNDARY=PASS
P15_DOMAIN_GOVERNANCE_AUTHORITY_BOUNDARY=PASS
P15_DOMAIN_GOVERNANCE_SECURITY_BOUNDARY=PASS
P15_9_REGRESSION=PASS
P15_8_REGRESSION=PASS
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
P14_FROZEN_PREDECESSOR_PRESERVED=True
PATCH_MATRIX=PASS
P15_10_READY_FOR_REVIEW=True
```

## Final preservation and exact Git state

Exactly 30 intended P15 candidates. All 27 incoming hashes unchanged; tracked/staged diffs empty, frozen branch/tag/HEAD unchanged, no generated residue. Nothing staged; no commit/tag/push. No P15.11/P15.12/P15.13/P15.14/P16 work.

`git status --short --untracked-files=all`:

```text
?? apexforge/p15_10_domain_governance_contract_test.py
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/p15_2_domain_interchange_contract_test.py
?? apexforge/p15_3_apexmotion_domain_contract_test.py
?? apexforge/p15_4_apexmotion_simulation_kernel_test.py
?? apexforge/p15_5_narrative_domain_contract_test.py
?? apexforge/p15_6_agent_domain_contract_test.py
?? apexforge/p15_7_parametric_domain_contract_test.py
?? apexforge/p15_8_fabrication_domain_contract_test.py
?? apexforge/p15_9_external_adapter_contract_test.py
?? apexforge/tooling/agent_domain.py
?? apexforge/tooling/apexmotion.py
?? apexforge/tooling/apexmotion_simulation.py
?? apexforge/tooling/domain_governance.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/external_adapter.py
?? apexforge/tooling/fabrication_domain.py
?? apexforge/tooling/narrative_domain.py
?? apexforge/tooling/parametric_domain.py
?? docs/p15/P15_10_DOMAIN_GOVERNANCE_CONTRACT.md
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
?? docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
?? docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
?? docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
?? docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md
?? docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md
?? docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md
?? docs/p15/P15_8_FABRICATION_DOMAIN_CONTRACT.md
?? docs/p15/P15_9_EXTERNAL_ADAPTER_CONTRACT.md
```

