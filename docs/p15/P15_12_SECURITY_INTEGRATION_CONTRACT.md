# P15.12 Security Integration, Execution Admission & Least-Privilege Guard Foundation

Review candidate only. This is pre-execution admission evidence, not execution,
a runtime permit, an authority grant, cryptographic trust or a freeze/release.

## Frozen baseline and incoming inventory

Branch: `p15-1-domain-platform-contract-sdk`.
HEAD: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Frozen predecessor: `afp-p14.13-freeze`.
P14 tag object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`.
Peeled target and branch `p14-1-package-identity-manifest`:
`0731e9c00b2858079007dbafdb0e052f497fb24c`.

Before implementation, branch/HEAD/tag/peeled target/P14 branch matched.
Exactly 33 untracked P15 candidates were present. Tracked and staged diffs were
empty. Status including ignored files showed no generated residue. These SHA-256
hashes were captured before implementation and checked again at handoff:

```text
P15_BASELINE=P14_13_FREEZE
P15_12_INCOMING_CANDIDATES=33
P14_REOPENED=False
04803D34F90ECFBA8BE742F502885A5F337EEAC9E7B38B43823F4E5656456D19  apexforge/p15_10_domain_governance_contract_test.py
9CEC9D197DFF179B4C240A7094BBE61648B28BE4D92335AE99A39D75CD26B344  apexforge/p15_11_cross_domain_orchestration_contract_test.py
0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62  apexforge/p15_1_domain_platform_contract_sdk_test.py
E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2  apexforge/p15_2_domain_interchange_contract_test.py
C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C  apexforge/p15_3_apexmotion_domain_contract_test.py
08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A  apexforge/p15_4_apexmotion_simulation_kernel_test.py
FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E  apexforge/p15_5_narrative_domain_contract_test.py
1197B2D82E28EA4B91F240946387AECE8E41FEEE788F824E021DD630F65CF5C5  apexforge/p15_6_agent_domain_contract_test.py
BF70EBF1ABD171685330F6D2800878E721B6882CDE20108447EB20E7067945A8  apexforge/p15_7_parametric_domain_contract_test.py
8C07880ACD1B05014DBD31FB6B8AD261C6E9EEFBC35D695D3EEE332EBA1612C8  apexforge/p15_8_fabrication_domain_contract_test.py
3542D42D2C6E9D6921CE709911BB060450DC811DD38E7096862ECEF508E45CAE  apexforge/p15_9_external_adapter_contract_test.py
A56E46EF274C8A9B81E0E6D8B90933B30A17996C7FB752284C891D145E312864  apexforge/tooling/agent_domain.py
571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6  apexforge/tooling/apexmotion.py
EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50  apexforge/tooling/apexmotion_simulation.py
C43F53E057AB753A8FDD0FB03E4DAA1059DE9E0810E4BB1DC19F411D9BD97E6D  apexforge/tooling/cross_domain_orchestration.py
FF18CE7F4487E38D2787CC60E024D70311171C2D373AAA347A953BA91779A9CB  apexforge/tooling/domain_governance.py
31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC  apexforge/tooling/domain_interchange.py
3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3  apexforge/tooling/domain_platform.py
16A22CA591AB15D9EC0EBEF57019AD11C1536FC7C46808D72B4237DCDCC9BFD1  apexforge/tooling/external_adapter.py
402328AC62FA4E2D767D35290842EC056ADD7D5B6C1F60F01EE1D8D8A005B829  apexforge/tooling/fabrication_domain.py
BA1284F04FC4DF4C63172E64AE8933E960C07979B1D597C7AB780253B85073DC  apexforge/tooling/narrative_domain.py
1F8E096C3CC78ED89C8452445C8456215735F4165AAC71BC2C55EADED09D3036  apexforge/tooling/parametric_domain.py
6D10D895D2D2FBD35CD551459E58929B5A1CD569602BEABB0C26986715CE6370  docs/p15/P15_10_DOMAIN_GOVERNANCE_CONTRACT.md
CDC54726E8489C2E1DB3CFE02F6CFB6CFE3EC449572D61E31C4F80CDD22883CC  docs/p15/P15_11_CROSS_DOMAIN_ORCHESTRATION_CONTRACT.md
F299D9B451A2A922A3923C0D0C015ADE712BAB627B58C275469EFFBB69CA6E2A  docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
4F726C34F77EED3BAA91716507C97EAA22A8AB62B346FCC57825D535F4A8531A  docs/p15/P15_2_DOMAIN_INTERCHANGE_CONTRACT.md
F93647E15817F40F3F0881FB322460DD4AD3F7057C6D15B004C2044167CF2BF4  docs/p15/P15_3_APEXMOTION_DOMAIN_CONTRACT.md
861DD7D3409081569B31C2537702E4DE01E57A679369FCD817A4C08395A6D59D  docs/p15/P15_4_APEXMOTION_SIMULATION_KERNEL.md
BA359C40CFE4A61D56883C2A5F075719C7E36303B23F630B76890E2AA8EEE151  docs/p15/P15_5_NARRATIVE_DOMAIN_CONTRACT.md
AD9A937754E811461595B5D8488B515D4CFCF32CFB74E74C18D76F6A35FD4769  docs/p15/P15_6_AGENT_DOMAIN_CONTRACT.md
C27D8D09E1DB62DFE751B60A4796478BA1D178545C6974A7BEAA2CE881E38EFD  docs/p15/P15_7_PARAMETRIC_DOMAIN_CONTRACT.md
8E9FA8E8EE830C3A67C1ADEFEBA28B133A8D71F3D83C91AADAECC66F8E65904D  docs/p15/P15_8_FABRICATION_DOMAIN_CONTRACT.md
C890336E3B28E6CF28A14F2719FE89E67EAF21F8A6EE44CC480686CFE2A45326  docs/p15/P15_9_EXTERNAL_ADAPTER_CONTRACT.md
```

## Frozen authority, trust and guard census

| Inspected concept/owner | Classification | Integration |
| --- | --- | --- |
| authority/model.py Principal, AuthorityCheck, AuthorityGrant | FROZEN_AUTHORITY_CONTRACT, REUSE | Canonical identity owners. Capability and resource are exact strings in AuthorityCheck, not new P15 identity classes. |
| authority/engine.py AuthorityEngine.check/allows | FROZEN_AUTHORITY_CONTRACT, REUSE | Canonical frozen read-only evaluation over explicitly supplied immutable grants. No grant construction in production. |
| authority/authority.py legacy engine; authority/validator.py declaration/role validation | REFERENCE_ONLY | Canonical runtime and consolidation evidence select authority.engine. No alternative authority matching or role resolution is introduced. |
| principal_compiler.py; air/model.py PrincipalAuthority and Principal re-export | FROZEN_AUTHORITY_CONTRACT, REFERENCE_ONLY; PrincipalAuthority REUSE | Compiler explicitly creates principal identities and named declaration metadata. P15.12 does not compile or infer identities. Frozen metadata carriers remain non-authorizing. |
| runtime/context.py and runtime/engine.py authority denial | FROZEN_RUNTIME_GUARD, REFERENCE_ONLY | Denial occurs before directive state/events/effects; return preserves state and no effects. Runtime execution is not called by P15.12. |
| runtime_directive_entry_guard_smoke_test.py and runtime directive-entry guard | FROZEN_RUNTIME_GUARD, REFERENCE_ONLY | Existing callback/lifecycle guard is an execution owner, not the P15.12 API. No callback accepted by the new gate. |
| workflow/air_runner.py, directive_engine.py, registry_linked_directive_execution_smoke_test.py | FROZEN_RUNTIME_GUARD, REFERENCE_ONLY | Linked declaration guards, principal coalescing, routing and execution remain frozen. |
| native_backend/native_execution_contract.py admit_native_profile | FROZEN_RUNTIME_GUARD, REFERENCE_ONLY | Pure bounded native-profile admission exists, but its AIR/lowering/routing semantics are not domain security admission. No native dispatch added. |
| P14 package_manifest.py coordinate/content identity/reference | FROZEN_TRUST_CONTRACT, REUSE | Exact package identity is inherited through P15.1; manifest evidence must match coordinate and content. |
| P14 package_trust.py ContentMember, SignatureEnvelope, TrustPolicy, verify_package | FROZEN_TRUST_CONTRACT, REUSE | Pure supplied-byte verification; no trust-store discovery or crypto-provider installation. |
| P14 VerificationEvidence / IntegrityResult | FROZEN_TRUST_CONTRACT, REFERENCE_ONLY | Passive result carriers are not authenticated receipts. Caller-written JSON or result status cannot establish package trust at the new gate. |
| P14 package_capabilities.py | FROZEN_AUTHORITY_CONTRACT, REFERENCE_ONLY | Structural package capability compatibility is never runtime authority. |
| P14 package_supply_chain.py evidence/report/profile | FROZEN_TRUST_CONTRACT, REFERENCE_ONLY | Structural chains and external authentication preconditions remain separate. Its final cryptographic trust is NOT_ESTABLISHED; no new supply-chain semantics. |
| P13 debug_evidence.py / trace_retention.py authority evidence and provenance scope | REFERENCE_ONLY | Retained observations are not grants; P15.12 preserves explicit CanonicalReferences without generating runtime traces. |
| P15.10 policy/candidate/decision/catalog | REUSE | Exact catalog admission is required, never reinterpreted as runtime permission. |
| P15.11 plan/node/validation | REUSE | Exact plan and node identity; the original structural validator must report VALID. No repair or graph-wide authorization. |
| SecurityAdmissionPolicy/Request/Decision and package evidence adapter | SECURITY_INTEGRATION_EXTENSION_POINT | Three new files only; scoped pre-execution conjunction over the frozen owners. |
| Workload dispatch, integration/acceptance, external authentication implementation, physical execution | DEFER_TO_P15_13 | Not begun. Existing frozen runtime checks remain necessary at any later execution boundary. |

Repository inspection found no existing generic cross-domain security gate.
Existing admission concepts are bounded native lowering/profile admission,
passive domain governance or artifact/provider-response structural checks.
None substitutes for exact principal/capability/resource authority evaluation.

## Authority integration selection

Selected mode: DIRECT_CHECK. The canonical authority.engine.AuthorityEngine is
frozen; its sorted tuple of grants is immutable. check only compares supplied
principal, capability and resource against grants, returns a Boolean and does
not mutate state, invoke a callback, access IO or execute a workload.
The frozen consolidation smoke test uses this owner and verifies denial and
transactional runtime coexistence.

P15.12 accepts only the exact AuthorityEngine class, not an arbitrary
AuthorityPolicy implementation. It calls check with the exact supplied
AuthorityCheck fields after matching them against the policy's required check
and explicit Principal. The request fingerprint binds the entire grant snapshot.
The decision reports the exact request, required/submitted check, grant snapshot
and owner-produced authority_allowed value. No second authority semantics or
fabricated authority decision is introduced.

The caller must supply the authoritative policy configuration and grant snapshot.
The gate does not authenticate their acquisition or mint permission. This mirrors
the frozen in-process authority injection contract; a decision is evidence of
evaluation over supplied inputs, not a bearer authorization token.

## Exact policy and node-scoped request

SecurityAdmissionPolicy is frozen, with canonical identifier, ExactVersion,
exact plan fingerprint, exact node fingerprint and a required frozen AuthorityCheck.
It has only bounded Boolean evidence requirements: integrity, package trust,
provenance and external-provider authentication. Governance, valid orchestration
and explicit authority are unconditional requirements and cannot be disabled.
There are no policy expressions, arbitrary callbacks, condition evaluation or
general policy language.

The policy explicitly declares which principal/capability/resource check applies
to one exact node. P15.12 neither guesses that relationship from domain/package
capability strings nor invents a new resource namespace.
The policy's exact fingerprint is bound into every request and decision.

SecurityAdmissionRequest is frozen and binds the policy, immutable P15.11 plan,
exact node object, frozen Principal, submitted frozen AuthorityCheck,
explicit immutable AuthorityEngine, optional PackageSecurityEvidence and
canonical provenance. Its canonical record retains:
plan/node fingerprints and node identifier, operation, catalog fingerprint,
governance decision fingerprint, descriptor fingerprint, implementation
coordinate/content identity, principal metadata, check, grant snapshot,
package verification inputs and provenance.

The supplied node must be an exact member of the plan, and policy plan/node
fingerprints must match. The exact governance decision must be ADMISSIBLE and
present in the exact catalog. Registered and supplied descriptors/packages must
match. P15.11 validation is consumed from its owner and must be VALID. Changes
to operation, slots, provenance, descriptor/package content, governance/catalog
or policy change admission identity. Contradictory evidence is not repaired.

## Principal, capability and resource boundaries

Principal is authority.model.Principal, not AgentIdentity, provider identity,
organization, package identity, narrative character or operating-system account.
No username, environment, host or file-author inference exists. Roles and
PrincipalAuthority names are retained as frozen metadata but never converted
into grants. Grant matching uses the canonical owner and principal.id.

Capability and resource identities are frozen AuthorityCheck strings. Required
and submitted principal/capability/resource/check identifier must match exactly.
A domain, agent, adapter or package capability cannot substitute for AuthorityCheck.

This initial profile requires nonempty exact requested resources/capabilities and
rejects wildcard request/policy fields. Identity fields are bounded printable
ASCII strings; this is a boundary input profile, not a frozen identity rewrite.
The caller declares the protected resource explicitly; the gate does not infer
whether a machine/provider-specific real-world resource exists.

Frozen existing grants may have capability "*" and resource "*" or empty string.
Those existing wildcard semantics are consumed only by AuthorityEngine.check,
unchanged. The requested protected resource remains exact. Production never
constructs an AuthorityGrant or AuthorityEngine, modifies grants, broadens a check
or creates a wildcard. No principal wildcard matching is introduced.

Changing principal, capability, resource, plan, node, descriptor, package content
or governance evidence changes the request fingerprint or causes DENIED findings.
Authority denial takes precedence over missing evidence; it never becomes a warning,
automatic retry or INCOMPLETE success.

## Package identity, integrity and cryptographic trust

PackageSecurityEvidence is a frozen adapter containing the frozen P14 manifest,
optional tuple of ContentMembers, optional SignatureEnvelope, public key and
TrustPolicy. Members are canonicalized by path and duplicates are rejected.
Member bytes are caller supplied; no files are opened. The evidence fingerprint
binds their digests, exact manifest record/metadata, signature, key fingerprint
and trust policy. Missing members (None) remain distinct from an explicit empty
tuple valid for an empty-content manifest.

Exact ImplementationPackage.from_manifest evidence must match the target
descriptor's P14 coordinate and content identity. Same coordinate with different
contents is a contradiction. The frozen P14 verify_package owns supplied-byte
integrity, signing payload, signature, signer/scope trust and acceptance states.
The new gate does not accept caller-assigned VerificationEvidence JSON as proof.

Cryptographic trust remains unavailable. A policy requiring package trust always
has SECURITY_CRYPTO_UNAVAILABLE and cannot be ADMISSIBLE. Structurally matching
keys/signatures and trusted namespace declarations still produce
CRYPTO_PROVIDER_UNAVAILABLE and accepted=False from P14.
An explicit invalid signature payload/key binding or untrusted scope is DENIED.
No VALID cryptographic signature or TRUSTED package status is fabricated.

An explicit policy may omit a cryptographic trust requirement for a structural
pre-execution check; its decision reports trust=NOT_REQUIRED and
cryptographic_trust_established=False. That is not package trust or execution.
Supplied strict P14 trust-policy requirements cannot be disabled by a weaker
P15.12 Boolean: missing signature/key/bytes remain missing, unavailable crypto
remains unavailable and incompatible scope remains denied.
Even when package bytes are missing, known signature payload/key contradictions
are denied using the frozen owner fingerprint functions.

## Evidence matrix, statuses, findings and replay

SecurityAdmissionDecision is frozen and derived only from its exact request.
Its fingerprint domain is apexforge.security-admission-decision/v1; policy and
request use distinct apexforge.security-admission-policy/v1 and
apexforge.security-admission-request/v1 domains. None reuses package, authority,
governance or orchestration identity.

The decision retains separate evidence dimensions:
plan, node, governance, orchestration, descriptor, package, authority, integrity,
trust, provenance and provider-authentication. Matrix states are SATISFIED,
NOT_REQUIRED, MISSING, UNAVAILABLE or DENIED. Required evidence is never collapsed
into a single Boolean before reporting.

Status is DENIED if any dimension is denied, INCOMPLETE if required evidence is
missing/unavailable, otherwise ADMISSIBLE. ADMISSIBLE means only that supplied
evidence satisfies the configured pre-execution gate. It does not mean execution,
operation correctness, package trust, output existence or physical authorization
outside the exact requested frozen check.

Findings are immutable code/dimension/state records, sorted deterministically.
Codes cover plan/node/governance/orchestration/descriptor/package mismatches,
principal/capability/resource/check substitution, missing or denied authority,
missing/invalid integrity/trust, unavailable crypto, missing required provenance
and missing provider authentication. Canonical identity never uses exception prose.

bind_decision compares the exact current request fingerprint with the prior
decision's request; mismatched contexts raise SECURITY_ADMISSION_REPLAY_MISMATCH.
It returns admission evidence only, including its status, never a permit.
Policy, plan, node, operation, governance, descriptor/package, principal/check,
grant snapshot, package evidence and provenance all participate in replay binding.
There is no wall-clock expiration or bearer token.

## Domain-specific and provenance boundaries

Explicit security provenance is required only when the policy says so. It is
lineage, not authentication or permission. The request retains its exact plan,
node, registration, implementation and caller references; no runtime event,
credential or authenticated attribution is manufactured.

Agent intents cannot self-authorize or auto-promote an agent into Principal.
Narrative characters/roles/causal edges and Parametric design/parameter records
cannot grant authority. Motion nodes remain structural: the simulation kernel is
not invoked. Fabrication compatibility/plan evidence cannot grant machine
authority; a protected machine operation requires its own explicit frozen
capability/resource check. No physical actuation occurs.

For External Adapter nodes, required provider authentication remains MISSING.
P15.9 supplies no authenticated-provider owner evidence, so no success carrier is
invented. A policy that does not require provider authentication reports that
dimension NOT_REQUIRED, never authenticated. Credential references are not resolved.
No tokens, API keys, credential files, trust stores or environment secrets are read.

A decision for an upstream node never authorizes a downstream node. Handoffs carry
artifact dependency/provenance only. The tested Parametric-to-Fabrication chain
requires a separate machine capability/resource check, which existing design
grants cannot satisfy. Similarly, proposing an external request is not transmission
permission. No transitive privilege propagation exists.

## Execution and static security audit

Production imports only dataclasses/hashlib, the canonical authority owner/model,
PrincipalAuthority's frozen AIR metadata owner, P15.1, P15.11, P14 trust and manifest.
No RuntimeEngine, AIR executor, native dispatcher, domain implementation, simulation,
model API, compiler, installer, credential provider or IO transport is imported/called.
Importing the AIR metadata carrier does not execute AIR.

The AST allowlist verifies exact imports, absence of dynamic import/callback/
eval/exec/pickle or IO/process/execution calls, absence of async constructs and
absence of token/permit/credential/runtime/expression fields. A direct-check
sentinel verifies exact arguments and an unchanged grant snapshot. Other sentinels
reject grant construction, governance reevaluation and artifact manufacture.
Decision records are detached projections of immutable inputs.

No network, filesystem discovery, shell/subprocess, native/domain/AIR/runtime/model
execution, simulation, compilation, package installation or machine actuation.
No runtime guard was altered or replaced. CANONICAL_AIR remains semantic authority.

## Focused validation and Patch Matrix

Initial focused run: 49/49 PASS.
Review then exposed SECURITY_TRUST_EVIDENCE_GAP: supplied signature/trust-policy
evidence could be overlooked when bytes were missing and integrity was optional.
Owner: P15.12. Frozen dependencies: P14 trust/identity, authority, P15.10 and P15.11.
Patch surface: new P15.12 module/test only.
Local contract: supplied trust requirements stay binding even if optional;
missing verification bytes stay missing, and known payload/key contradictions
remain DENIED. Added focused cases and strengthened typed finding diagnostics.
Intermediate focused run: 51/51 PASS.
Final focused run adds nonempty content/member-permutation and real digest-mismatch
evidence: 52/52 PASS. No test assertions were weakened and no failed test was hidden.

Exact final command:
`python -X utf8 -B apexforge/p15_12_security_integration_contract_test.py`.

Coverage includes immutable policy/request/decision, all exact bindings,
wrong principal/capability/resource/grants, immutable authority snapshot and exact
read-only check, wildcard requests rejected/existing grants consumed unchanged,
governance/orchestration prerequisites, incomplete versus denied precedence,
nonempty-byte integrity and substitution, crypto/scope/strict-trust boundaries,
caller-written trust status rejection, provenance requirements, domain boundaries,
handoff privilege non-propagation, replay substitutions and static audit.

The iterative scale test evaluates 1000 distinct principal-scoped admission
records, verifies ADMISSIBLE under explicitly non-cryptographic policy requirements,
checks 1000 distinct decision fingerprints, and recomputes identical fingerprints
in reverse processing order. It is determinism/scale evidence, not a benchmark.

Tests ran with host Python through the required escalation mechanism because
the sandbox Python installation was unavailable as established in P15.11.
No Python installation, Windows execution policy or security setting changed.
Read-only searches initially assumed nonexistent principal/native-admission paths;
the actual principal_compiler.py and native_backend/native_execution_contract.py
owners were found and inspected. Classification: INSPECTION_PATH_OBSERVATION;
no repository repair.

The active Autonomy Directive and explicit Patch Matrix are applied within P15.12:
FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.
No frozen authority/trust/governance/orchestration blocker or owning defect was found.

## Requested regressions

Each predecessor was run unchanged with
`python -X utf8 -B apexforge/<suite>`, in the requested descending order:

| Suite | Result |
| --- | --- |
| p15_11_cross_domain_orchestration_contract_test.py | 48/48 PASS |
| p15_10_domain_governance_contract_test.py | 24/24 PASS |
| p15_9_external_adapter_contract_test.py | 28/28 PASS |
| p15_8_fabrication_domain_contract_test.py | 33/33 PASS |
| p15_7_parametric_domain_contract_test.py | 31/31 PASS |
| p15_6_agent_domain_contract_test.py | 29/29 PASS |
| p15_5_narrative_domain_contract_test.py | 29/29 PASS |
| p15_4_apexmotion_simulation_kernel_test.py | 23/23 PASS |
| p15_3_apexmotion_domain_contract_test.py | 30/30 PASS |
| p15_2_domain_interchange_contract_test.py | 40/40 PASS |
| p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |

`python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py`:
397/397 PASS (345 incoming + 52 new).

`python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py`:
330/330 PASS.

`python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py`:
7/7 PASS.

`python -X utf8 -B apexforge/authority_consolidation_smoke_test.py`:
canonical identities and exact grant PASS;
Wrong principal/capability/resource denial: PASS;
Authorized RuntimeEngine execution: PASS;
Denied execution is transactional: PASS.
Runtime execution in this unchanged frozen smoke test is predecessor behavior;
the P15.12 module and focused suite do not trigger workload execution.

## Evidence-supported markers and distinctions

```text
P15_12_AUTHORITY_INTEGRATION_MODE=DIRECT_CHECK
P15_12_REDEFINES_CORE_SEMANTICS=False
P15_12_REDEFINES_AUTHORITY_MODEL=False
P15_12_MINTS_AUTHORITY=False
P15_12_REDEFINES_DOMAIN_GOVERNANCE=False
P15_12_REDEFINES_ORCHESTRATION=False
P15_12_REDEFINES_GOVERNANCE=False
P15_12_PRINCIPAL_INFERENCE_IMPLEMENTED=False
P15_12_AGENT_AUTO_PROMOTION_TO_PRINCIPAL=False
P15_12_CAPABILITY_ESCALATION_INFERENCE=False
P15_12_WILDCARD_AUTHORITY_FABRICATION=False
P15_12_REDEFINES_PACKAGE_TRUST=False
P15_12_CRYPTO_UNAVAILABLE_FAILS_OPEN=False
P15_12_FABRICATES_CRYPTO_TRUST=False
P15_12_PROVENANCE_GRANTS_AUTHORITY=False
P15_12_GENERAL_SECURITY_POLICY_LANGUAGE_IMPLEMENTED=False
P15_12_SECURITY_POLICY_GRANTS_AUTHORITY=False
P15_12_EXTERNAL_PROVIDER_AUTHENTICATION_FABRICATED=False
P15_12_AGENT_INTENT_GRANTS_AUTHORITY=False
P15_12_NARRATIVE_RECORD_GRANTS_AUTHORITY=False
P15_12_SIMULATION_EXECUTION_IMPLEMENTED=False
P15_12_PARAMETRIC_RECORD_GRANTS_AUTHORITY=False
P15_12_FABRICATION_PLAN_GRANTS_MACHINE_AUTHORITY=False
P15_12_PHYSICAL_ACTUATION_IMPLEMENTED=False
P15_12_CREDENTIAL_ACQUISITION_IMPLEMENTED=False
P15_12_TRANSITIVE_PRIVILEGE_ESCALATION=False
P15_12_BEARER_EXECUTION_TOKEN_IMPLEMENTED=False
P15_12_NETWORK_ACCESS=False
P15_12_FILESYSTEM_DISCOVERY=False
P15_12_DYNAMIC_PLUGIN_LOADING_IMPLEMENTED=False
P15_12_EXECUTES_AIR=False
P15_12_EXECUTES_RUNTIME=False
P15_12_DISPATCHES_NATIVE=False
P15_12_EXECUTES_DOMAIN_CODE=False
P15_12_COMPILES=False
P15_12_INSTALLS_PACKAGES=False
P15_12_HOST_COMMAND_EXECUTION=False
P15_12_RUNTIME_EXECUTION_TRIGGERED=False
P15_12_MISSING_SECURITY_EVIDENCE_FAILS_OPEN=False
P15_12_ADMISSION_NODE_SCOPED=True
P15_12_EXACT_ORCHESTRATION_BOUND=True
P15_12_REQUIRES_GOVERNANCE_ADMISSIBILITY=True
P15_12_REQUIRES_VALID_ORCHESTRATION=True
P15_12_LEAST_PRIVILEGE_RESOURCE_BINDING=True
P15_12_CONFUSED_DEPUTY_BINDINGS_EXACT=True
P15_12_AUTHORITY_DECISION_EXACT_BOUND=True
P15_12_AUTHORITY_DENIAL_FAILS_CLOSED=True
P15_12_MISSING_AUTHORITY_NOT_INFERRED=True
P15_12_SECURITY_DECISION_IMMUTABLE=True
P15_12_EXACT_PACKAGE_CONTENT_BOUND=True
P15_12_DECISION_EXACT_SECURITY_POLICY_BOUND=True
P15_12_AUTHORITY_DOES_NOT_PROPAGATE_ACROSS_HANDOFF=True
P15_12_CROSS_CONTEXT_ADMISSION_REPLAY_REJECTED=True
P15_SECURITY_INTEGRATION_MODEL=PASS
P15_SECURITY_POLICY_MODEL=PASS
P15_SECURITY_GOVERNANCE_BINDING=PASS
P15_SECURITY_ORCHESTRATION_BINDING=PASS
P15_SECURITY_NODE_BINDING=PASS
P15_SECURITY_PACKAGE_BINDING=PASS
P15_SECURITY_PRINCIPAL_BINDING=PASS
P15_SECURITY_CAPABILITY_BINDING=PASS
P15_SECURITY_RESOURCE_BINDING=PASS
P15_SECURITY_AUTHORITY_EVIDENCE=PASS
P15_SECURITY_TRUST_BOUNDARY=PASS
P15_SECURITY_PROVENANCE=PASS
P15_SECURITY_CONFUSED_DEPUTY_DEFENSE=PASS
P15_SECURITY_REPLAY_BOUNDARY=PASS
P15_SECURITY_LEAST_PRIVILEGE=PASS
P15_SECURITY_DETERMINISM=PASS
P15_SECURITY_EXECUTION_BOUNDARY=PASS
P15_SECURITY_CRYPTO_BOUNDARY=PASS
P15_SECURITY_EXTERNAL_PROVIDER_BOUNDARY=PASS
P15_SECURITY_PHYSICAL_ACTUATION_BOUNDARY=PASS
P15_SECURITY_STATIC_AUDIT=PASS
P15_11_REGRESSION=PASS
P15_10_REGRESSION=PASS
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
P15_12_READY_FOR_REVIEW=True
PATCH_MATRIX=PASS
CRYPTO_PROVIDER_UNAVAILABLE

SECURITY_ADMISSION != EXECUTION
SECURITY_ADMISSION != AUTHORITY_GRANT
SECURITY_ADMISSION != PACKAGE_TRUST
SECURITY_ADMISSION != GOVERNANCE_ADMISSION
SECURITY_ADMISSION != ORCHESTRATION_VALIDITY
GOVERNANCE_ADMISSIBLE != AUTHORIZED
GOVERNANCE_ADMISSIBLE != SECURITY_ADMITTED
VALID_ORCHESTRATION != AUTHORIZED
DECLARED_CAPABILITY != AUTHORITY
PACKAGE_INTEGRITY != PACKAGE_TRUST
PACKAGE_DIGEST_MATCH != PACKAGE_TRUST
PACKAGE_IDENTITY_MATCH != PACKAGE_TRUST
PROVENANCE != AUTHENTICATION
AGENT_INTENT != AUTHORIZATION
EXTERNAL_RESPONSE != AUTHORIZATION
FABRICATION_PLAN != MACHINE_AUTHORIZATION
FABRICATION_COMPATIBILITY != MACHINE_AUTHORIZATION
PRINCIPAL != AGENT
PRINCIPAL != PROVIDER
PRINCIPAL != PACKAGE
PRINCIPAL != ORGANIZATION
DOMAIN_CAPABILITY != AUTHORITY_CAPABILITY
PACKAGE_CAPABILITY != AUTHORITY_CAPABILITY
NODE_AUTHORIZATION != PLAN_WIDE_AUTHORIZATION
SECURITY_ADMISSIBLE != EXECUTED
SECURITY_POLICY_REQUIREMENT != AUTHORITY_GRANT
SECURITY_ADMISSION != PROVIDER_AUTHENTICATION
ARTIFACT_HANDOFF != AUTHORITY_HANDOFF
SECURITY_ADMISSION != RUNTIMEENGINE_EXECUTION
EVIDENCE_BEFORE_ATTRIBUTION=True
SEMANTIC_AUTHORITY=CANONICAL_AIR
```

## Preservation and exact Git state

Final `git status --short --untracked-files=all`:

```text
?? apexforge/p15_10_domain_governance_contract_test.py
?? apexforge/p15_11_cross_domain_orchestration_contract_test.py
?? apexforge/p15_12_security_integration_contract_test.py
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
?? apexforge/tooling/cross_domain_orchestration.py
?? apexforge/tooling/domain_governance.py
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/external_adapter.py
?? apexforge/tooling/fabrication_domain.py
?? apexforge/tooling/narrative_domain.py
?? apexforge/tooling/parametric_domain.py
?? apexforge/tooling/security_integration.py
?? docs/p15/P15_10_DOMAIN_GOVERNANCE_CONTRACT.md
?? docs/p15/P15_11_CROSS_DOMAIN_ORCHESTRATION_CONTRACT.md
?? docs/p15/P15_12_SECURITY_INTEGRATION_CONTRACT.md
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

Exactly 36 intended P15 candidates. All 33 incoming hashes remain byte-identical.
Tracked and staged diffs are empty (`git diff --exit-code` and
`git diff --cached --exit-code` return zero). Status including ignored files
shows no generated residue. Branch, HEAD, P14 branch/tag object/peeled target
remain identical to baseline.

Only security_integration.py, its focused suite and this report were added.
P15.1–P15.11, existing authority/trust contracts and every frozen
P14/P13/P12/P11/P10 tracked file are unchanged. No staging, commit, tag, push,
P15.13 acceptance, P15.14 closure/freeze, P16 or equivalent later work occurred.

Remaining work is human review of this candidate. Known limits: caller policy
configuration and authority snapshot must come from the embedding owner's trusted
in-process boundary; the gate does not authenticate their acquisition.
Provider authentication and cryptographic package trust cannot be satisfied by
the current owners. Admission does not prove engineering safety, operation
correctness, output existence or physical execution, and does not replace frozen
runtime authorization checks. No execution integration or freeze is claimed.

