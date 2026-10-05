# P15.13 Platform Integration, End-to-End Acceptance & Release-Candidate Evidence

This is integration acceptance evidence, not an executor, authority grant,
package trust decision, release or freeze. Human review remains authoritative.

## Incoming frozen baseline

Branch: `p15-1-domain-platform-contract-sdk`.
HEAD: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
P14 predecessor: `afp-p14.13-freeze`.
Tag object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`.
Peeled target and `p14-1-package-identity-manifest`:
`0731e9c00b2858079007dbafdb0e052f497fb24c`.

Before implementation, all refs matched; exactly 36 incoming candidates were
present; tracked and staged diffs were empty; status including ignored files
contained no generated residue. The incoming SHA-256 census is:

```text
P15_BASELINE=P14_13_FREEZE
P15_13_INCOMING_CANDIDATES=36
P14_REOPENED=False
04803D34F90ECFBA8BE742F502885A5F337EEAC9E7B38B43823F4E5656456D19  apexforge/p15_10_domain_governance_contract_test.py
9CEC9D197DFF179B4C240A7094BBE61648B28BE4D92335AE99A39D75CD26B344  apexforge/p15_11_cross_domain_orchestration_contract_test.py
42104FF4B0E008A971DA3590640A12E4F99159C658792743D622AB49281BA462  apexforge/p15_12_security_integration_contract_test.py
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
B5CFDE03BF60322F66C5C90C5A8B467B8720531F02632D018B6C804401C4F173  apexforge/tooling/security_integration.py
6D10D895D2D2FBD35CD551459E58929B5A1CD569602BEABB0C26986715CE6370  docs/p15/P15_10_DOMAIN_GOVERNANCE_CONTRACT.md
CDC54726E8489C2E1DB3CFE02F6CFB6CFE3EC449572D61E31C4F80CDD22883CC  docs/p15/P15_11_CROSS_DOMAIN_ORCHESTRATION_CONTRACT.md
E47E5836F7CEDD9A8B42E2A86384368E34036C04A5D0B70404208948C195401D  docs/p15/P15_12_SECURITY_INTEGRATION_CONTRACT.md
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

## Ownership census

| Concern | Existing owner | Classification / P15.13 use |
| --- | --- | --- |
| Domain identity, descriptor, implementation binding, capabilities, artifacts | P15.1 domain_platform.py | OWNED_BY_EXISTING_P15_SLICE; exact immutable carriers reused. |
| Generic interchange | P15.2 domain_interchange.py | OWNED_BY_EXISTING_P15_SLICE; existing descriptor/artifact/request round trips only. |
| Motion entity/frame/state/trajectory | P15.3 apexmotion.py | OWNED_BY_EXISTING_P15_SLICE; caller state and artifact/reference preserved. |
| Simulation specification, steps, deterministic evolution and trace | P15.4 apexmotion_simulation.py | OWNED_BY_EXISTING_P15_SLICE; explicit zero-step trace consumed; no evolution in new integration code. |
| Narrative semantics and domain structure | Frozen P11 language/narrative_model.py and narrative_graph.py; P15.5 narrative_domain.py | REFERENCE_ONLY for P11 semantics; OWNED_BY_EXISTING_P15_SLICE for passive domain snapshot. |
| Agent identity, session and action intents | Frozen agents/model.py; P15.6 agent_domain.py | REFERENCE_ONLY for AgentIdentity; OWNED_BY_EXISTING_P15_SLICE for context/ledger/intent carriers. |
| Parametric design, parameters and variant | P15.7 parametric_domain.py | OWNED_BY_EXISTING_P15_SLICE; existing structural variant reused. |
| Fabrication input, plan and compatibility | P15.8 fabrication_domain.py | OWNED_BY_EXISTING_P15_SLICE; supplied part evidence and exact variant association, no physical work. |
| Adapter/provider/request/response | P15.9 external_adapter.py | OWNED_BY_EXISTING_P15_SLICE; offline caller request/reported response only. |
| Governance admission and catalog | P15.10 domain_governance.py | OWNED_BY_EXISTING_P15_SLICE; fixtures call its public evaluation; collector consumes exact decisions. |
| Structural orchestration and topological planning | P15.11 cross_domain_orchestration.py | OWNED_BY_EXISTING_P15_SLICE; exact plan/node/handoff references and structural validation. |
| Node-scoped security admission | P15.12 security_integration.py | OWNED_BY_EXISTING_P15_SLICE; request/decision/status/replay bindings consumed through owner. |
| Runtime principal/capability/resource authority | Frozen authority/model.py and authority/engine.py | REFERENCE_ONLY; new production module has no authority import or direct check. |
| Package identity/integrity/trust | Frozen P14 package_manifest.py and package_trust.py | REFERENCE_ONLY; exact P15.1 implementation binding and P15.12 package evidence path. |
| Canonical AIR / semantic authority | Frozen air model/verifier/compiler contracts | REFERENCE_ONLY; CANONICAL_AIR is unchanged. |
| Scenario, observations, expected admissions and acceptance result | P15.13 platform_acceptance.py | INTEGRATION_ACCEPTANCE_ONLY; no second domain, governance, authority or security model. |
| Closure/freeze/release | P15.14 and later | DEFER_TO_P15_14; no work begun. |

No new KINDS entry, semantic identity, domain operation, conversion, security
rule language, runtime guard or execution lifecycle is added.

## Minimal integration evidence model

AcceptanceEvidence is a frozen caller-supplied PASS/FAIL observation for one of
the twelve owning layers or eleven boundary areas, with an exact frozen
CanonicalReference. It does not run a suite or authenticate a claim.

AdmissionExpectation holds a caller case identifier, exact P15.12 request and
decision, and expected ADMISSIBLE/DENIED/INCOMPLETE status. It snapshots the
owner-produced request/decision fingerprints, status and public bind_decision
outcome once. Those private fields are derived, frozen and not constructor inputs.
This avoids repeat admission during record projection; no security semantics
are recomputed by P15.13. A changed case is reconstructed through the same owner.

PlatformAcceptanceScenario binds a caller identifier, exact P15.11 plan,
exact P15.1 implementation-package baseline, admissions, existing artifacts,
domain-record references, layer/boundary observations and provenance.
Tuples are bounded at 4096 records and canonically ordered; duplicates and
conflicting matrix rows are rejected. There are no display/path/clock/random IDs.

PlatformAcceptanceResult is an immutable derived evidence assessment. It checks
baseline/package/artifact/reference continuity, owner plan validity, exact
admission context, owner replay binding, expected status and matrix/node coverage.
It reports PASS, FAIL or INCOMPLETE with sorted structured findings.
PASS may mean an expected DENIED/INCOMPLETE admission was correctly observed.
It never means a security gate admitted every node or that a workflow ran.

Findings include ACCEPTANCE_EVIDENCE_MISSING, ACCEPTANCE_OBSERVATION_FAILED,
ACCEPTANCE_PACKAGE_BASELINE_MISMATCH, ACCEPTANCE_ORCHESTRATION_NOT_VALID,
ACCEPTANCE_ARTIFACT_BINDING_MISMATCH, ACCEPTANCE_INITIAL_ARTIFACT_MISSING,
ACCEPTANCE_ADMISSION_CONTEXT_MISMATCH, ACCEPTANCE_ADMISSION_REPLAY_MISMATCH,
ACCEPTANCE_ADMISSION_UNEXPECTED and ACCEPTANCE_NODE_EVIDENCE_MISSING.
Missing evidence yields INCOMPLETE; contradictory/failed observations yield FAIL
and take precedence. Exception prose is not canonical finding identity.

The acceptance matrix is caller evidence supported by focused cross-owner
assertions and the separately rerun owner suites. The collector is not a proof
authenticator, suite runner or release gate.

## End-to-end scenarios and exact continuity

The main deterministic DAG has six nodes:
Parametric -> Fabrication -> Agent -> External Adapter,
with Narrative -> Agent and Motion -> Agent dependencies.
Every node holds an exact P15.10 catalog decision, exact P15.1 descriptor,
exact P14 implementation identity, declared operation and explicit slots.
Every protected planned operation has its own explicit P15.12 request/policy.

The Parametric variant is an existing P15.7 owner record. FabricationInput
retains that exact variant fingerprint alongside explicit caller part bytes.
AgentTask retains exact FabricationPlan, NarrativeSnapshot and SimulationTrace
references; a caller-declared Agent intent is explicitly retained in the offline
ExternalRequest. ExternalResponse is supplied reported evidence bound to its exact
request/provider/correlation; admit_response performs only the P15.9 structural check.

These records are independently supplied passive descriptions. They are not
outputs of executing the planned nodes. Generic model-kind handoffs are explicitly
declared using P15.11's supported structural contract. They do not adapt a
Parametric record into geometry, a Fabrication model into a machine command,
a narrative into fact, or an intent into transmission. Operation-specific slot
semantics are not invented where current descriptors declare only operations.

Caller-supplied initial artifacts bind the Parametric, Narrative and Motion
input slots. Other outputs remain OutputSlot declarations without byte digests.
Scenario artifacts retain complete originating platform, implementation,
operation, descriptor fingerprint, semantic references, symbols and provenance.
No generic integrated-artifact identity replaces an origin domain.

Continuity assertions cover:
P14 content identity -> P15.1 descriptor -> owner domain record/artifact ->
P15.10 candidate/decision/catalog -> P15.11 node/plan ->
P15.12 policy/request/decision. Source provenance scopes and exact domain
references survive the chain without becoming authorship or authentication.

A same-coordinate content substitution is rejected by the acceptance baseline
and P15.12 package owner binding. A legitimate content revision changes exact
descriptor/domain-record/candidate/decision/catalog/node/plan/request/decision
fingerprints. Rebinding the new policy/evidence creates a new decision; old
admission replay fails. Similar-name descriptor revision, different admissible
governance candidate/catalog, changed node/operation/handoff/plan all prevent
reuse of prior admissions.

## Interchange and domain boundaries

P15.2 round trips every supported descriptor and existing SDK artifact, including
domain-specific record artifacts and an SDK DomainRequest. Exact object,
fingerprint, identity, package, descriptor and references are preserved.
Raw domain records, orchestration, security and acceptance objects are not forced
through unsupported P15.2 wire kinds; no new top-level wire format is added.

MotionState remains caller-supplied motion evidence, not measured physical truth.
The P15.4 owner validates an explicit zero-step SimulationTrace with no computed
states. New integration code never calls simulate or evolve; sentinels enforce
this. P15.4's actual evolution is covered by its unchanged focused regression,
not reimplemented by P15.13. Simulated record status is not a workflow receipt.

NarrativeSnapshot/events remain NARRATIVE_DECLARATION and external_fact_verified=False.
Narrative-origin initial artifact and AgentTask reference remain exact.

Agent identity remains the frozen AgentIdentity; session/context/intents retain
P15.6 ownership. It is not a Principal or narrative character. Caller ledger
entries and selected intent metadata do not select actions or run an agent.

ParametricVariant retains geometry_generated=False and engineering_safety_proven=False.
FabricationPlan remains NOT_PERFORMED and grants_authority=False. A VALID declared
FabricationValidation proves compatibility only, never engineering safety or
machine authorization. No physical-object identity is manufactured.

ExternalRequest remains execution_permission=False. The reported ExternalResponse
remains EXTERNALLY_SUPPLIED and authenticated=False. Provider identity supplies
no organization-affiliation relation; no Organization identity/type is invented
where the inspected owners provide none. No credentials, environment secrets,
certificates or trust stores are read; no transport/model/provider/machine API
is invoked.

## Admission, authority, trust and denial acceptance

P15.12's reviewed mode remains DIRECT_CHECK. Test fixtures provide explicit
frozen in-process authority snapshots through the existing P15.12 path; no
production AuthorityEngine/AuthorityGrant construction or direct check exists.
The same explicitly supplied review capability/resource may be required by
multiple node-specific policies, but every node gets its own exact evaluation.
Nothing propagates authority through handoffs.

Five main cases expect structural ADMISSIBLE under explicitly non-cryptographic
test policies. The External Adapter expects INCOMPLETE because required provider
authentication is unavailable. These expected outcomes can produce acceptance
PASS without inventing provider authentication or permission to dispatch.

Governance ADMISSIBLE plus a VALID plan remains INCOMPLETE when authority evidence
is missing. Wrong-principal, wrong-capability and wrong-resource grant snapshots
produce P15.12 DENIED without changing governance/catalog/plan or executing.
An expected-denial integration case records acceptance PASS only because that
fail-closed outcome was the expected contract behavior.

Required package trust stays INCOMPLETE with SECURITY_CRYPTO_UNAVAILABLE.
Digest/content equality never becomes cryptographic package trust. P15.13
does not call a trust verifier independently or reinterpret P14 states.
P15.12 remains the package security evidence integration point.
CRYPTO_PROVIDER_UNAVAILABLE is preserved.

The collector's output explicitly states NOT_PERFORMED, grants_authority=False,
grants_trust=False, freeze_performed=False and CANONICAL_AIR.
No RuntimeEngine/native/domain/model/simulation/provider/machine workload is called.

## Identity-separation and boundary matrix

| Separation / boundary | Integration evidence |
| --- | --- |
| Agent != Principal; Narrative character != Agent | Exact owner types/identities remain distinct; no promotion/inference. |
| Provider != Organization | No affiliation relation or organization field is introduced by provider identity. |
| Parametric variant != Fabrication plan | Exact typed association retains the variant; no identity merge or geometry. |
| Fabrication plan != Physical object | Declarative plan/compatibility only; no physical-object carrier or actuation. |
| Governance decision != Authority decision | Catalog admission remains insufficient without P15.12 authority evidence. |
| Security decision != Execution result | Immutable admission evidence, NOT_PERFORMED, no execution result/token. |
| Semantic authority | CANONICAL_AIR unchanged. |
| Package trust | Explicit policy boundary; required crypto unavailable; no trust minted. |
| Runtime authority | Owner evaluation only via P15.12; no handoff privilege propagation. |
| Engineering safety / physical actuation | Existing false/non-executing owner flags retained. |
| External facts | Narrative declaration and externally reported response remain unverified. |
| Network / credentials / models | Offline references only; no IO acquisition, dispatch or model call. |

The eleven boundary observations are separate from the twelve-layer acceptance
matrix. Their references identify the owner evidence that the focused assertions
inspect. They are not authority, authentication or safety certifications.

## Determinism, scale and static audit

Independent complete scenarios and reversed node/edge/admission/artifact/reference/
observation construction orders produce identical scenario records/fingerprints,
plan fingerprints, admission evidence, result findings and result fingerprints.
No clock, random UUID, hostname, current directory, process ID, environment or
network state participates.

The scale case retains 128 planned nodes, 127 explicit DAG edges and 128 separately
node-scoped admission records over one deterministic plan. Iterative P15.11 order,
matrix acceptance and reverse admission-order fingerprint equality are checked.
This is substantial structural composition evidence, not a benchmark or execution.

The production AST allowlist permits only dataclasses, P15.1, P15.11, P15.12 and
the frozen CanonicalReference owner. No subprocess/socket/http/requests/SDK/device/
dynamic-import dependency, direct authority check, eval/exec/pickle, IO, compiler,
installer, callback or async worker is present. Class census includes only
acceptance evidence/expectation/scenario/result/error carriers.
Dynamic sentinels reject simulate/evolve, governance reevaluation, grant factory
invocation and artifact manufacture during acceptance; immutable projection also
does not reevaluate P15.12 admission.

## Patch Matrix and validation ledger

Initial focused run: 29 cases, 28 fixture errors. Classification:
PLATFORM_PROVENANCE_CONTINUITY_GAP, owning P15.13 test adapter.
Cause: positional tuple recomposition duplicated a canonically ordered provenance
reference; P15.12 correctly rejected it. Smallest patch passes the exact node
provenance tuple directly. Inspection also classified
PLATFORM_INTERCHANGE_INTEGRATION_GAP: the envelope adapter needed P15.2's schema
field rather than an unsupported SCHEMA attribute. Test adapter corrected only.
No owner assertion, security requirement or predecessor file was changed.
Corrected focused run: 29/29 PASS.

The substantial case exposed repeated derivation of immutable admission references.
Classification: PLATFORM_INTEGRATION_MODEL_GAP, owner P15.13 evidence projection.
Patch surface: new module/test only. Freeze owner-produced fingerprints/status/
public replay outcome once in AdmissionExpectation, with non-init private fields.
The same 128 nodes, 127 edges and 128 cases/assertions remain; no scale reduction
or assertion weakening. Added full package-revision continuity and no-repeat-
admission projection assertions.

Patch routing:
FAILURE -> CLASSIFICATION -> OWNING SECTION -> FROZEN DEPENDENCIES ->
PATCH SURFACE -> LOCAL CONTRACT -> SECTION REGRESSION -> DEPENDENCY REGRESSION ->
CROSS-SECTION REGRESSION -> AGGREGATE REGRESSION -> PRESERVATION AUDIT -> PATCH_MATRIX.

Final focused P15.13 validation: **31/31 PASS**. All predecessor focused
commands used `python -X utf8 -B apexforge/<owning focused suite>`, in
P15.12 through P15.1 order; all passed unchanged.

## Deterministic acceptance and predecessor matrix

The matrix observations are caller-supplied, immutable evidence references.
They are not authenticated test receipts; this report separately records the
actual executed suites. All twelve owning layers are represented.

| Owner | Integrated evidence | Focused regression |
| --- | --- | --- |
| P15.1 | Exact SDK descriptors/artifacts | 30/30 PASS |
| P15.2 | Supported descriptor/artifact/request round trips | 40/40 PASS |
| P15.3 | Motion-origin record | 30/30 PASS |
| P15.4 | Explicit zero-step SimulationTrace | 23/23 PASS |
| P15.5 | NarrativeSnapshot origin | 29/29 PASS |
| P15.6 | AgentTask/ledger/intent identity | 29/29 PASS |
| P15.7 | Exact structural ParametricVariant | 31/31 PASS |
| P15.8 | Declarative FabricationInput/Plan | 33/33 PASS |
| P15.9 | Offline ExternalRequest/Response | 28/28 PASS |
| P15.10 | Exact governed registrations/catalog | 24/24 PASS |
| P15.11 | Six-node DAG, handoffs and initial evidence | 48/48 PASS |
| P15.12 | Node-scoped admission and denial/incomplete cases | 52/52 PASS |

Frozen checks completed: P14 **330/330 PASS**, native profile **7/7 PASS**.
Authority consolidation: canonical identities, exact grant, wrong
principal/capability/resource denial, authorized RuntimeEngine execution and
transactional denied execution all PASS. RuntimeEngine execution here belongs
only to the unchanged frozen smoke test; P15.13 does not execute workloads.

## Preservation audit

All 36 incoming SHA-256 hashes match the incoming census. There are exactly
39 intended untracked candidates: the incoming 36 plus the three P15.13 files.
Tracked and staged diffs are empty. Status including ignored files has no
generated residue. Branch, HEAD, P14 tag object, peeled target and P14 branch
remain exactly as recorded above. Frozen predecessors and P15.1–P15.12,
including authority and package-trust owners, are unchanged.

Exact Git status:

```text
?? apexforge/p15_10_domain_governance_contract_test.py
?? apexforge/p15_11_cross_domain_orchestration_contract_test.py
?? apexforge/p15_12_security_integration_contract_test.py
?? apexforge/p15_13_platform_integration_acceptance_test.py
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
?? apexforge/tooling/platform_acceptance.py
?? apexforge/tooling/security_integration.py
?? docs/p15/P15_10_DOMAIN_GOVERNANCE_CONTRACT.md
?? docs/p15/P15_11_CROSS_DOMAIN_ORCHESTRATION_CONTRACT.md
?? docs/p15/P15_12_SECURITY_INTEGRATION_CONTRACT.md
?? docs/p15/P15_13_PLATFORM_INTEGRATION_ACCEPTANCE.md
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

No staging, commit, tag, push, freeze or P15.14 implementation occurred.
No workflow/domain execution, external network, credential acquisition,
provider/model dispatch or physical actuation occurred in P15.13.
The acceptance result describes structural observations, including expected
security denial/incompleteness; it grants no authority or trust. Provider
authentication and cryptographic trust remain unavailable where required.
Human review remains authoritative.

P15 aggregate: **428/428 PASS** using
`python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py`.
Frozen aggregate used the same discovery form with `p14_*_test.py`;
native and authority checks used their requested unchanged focused scripts.
No failures remain after the classified P15.13 adapter/projection corrections.

## Evidence-supported markers

```text
P15_13_REDEFINES_CORE_SEMANTICS=False
P15_13_DUPLICATE_SEMANTIC_OWNERSHIP=False
P15_13_NEW_DOMAIN_KIND_ADDED=False
P15_13_REDEFINES_SECURITY_ADMISSION=False
P15_13_REDEFINES_AUTHORITY=False
P15_13_MINTS_AUTHORITY=False
P15_13_REDEFINES_PACKAGE_TRUST=False
P15_13_FABRICATES_TRUST=False
P15_13_REDEFINES_DOMAIN_INTERCHANGE=False
P15_13_MOTION_RECORD_PROVES_PHYSICAL_TRUTH=False
P15_13_REDEFINES_SIMULATION=False
P15_13_NARRATIVE_RECORD_EXTERNAL_FACT=False
P15_13_REDEFINES_AGENT_IDENTITY=False
P15_13_AGENT_AUTO_EXECUTION=False
P15_13_AGENT_AUTO_PRINCIPAL_PROMOTION=False
P15_13_PARAMETRIC_VARIANT_GEOMETRY_GENERATED=False
P15_13_FABRICATION_EXECUTION=False
P15_13_PHYSICAL_ACTUATION=False
P15_13_EXTERNAL_ADAPTER_DISPATCH=False
P15_13_NETWORK_ACCESS=False
P15_13_PROVIDER_AUTHENTICATION_FABRICATED=False
P15_13_AUTOMATIC_SEMANTIC_CONVERSION=False
P15_13_INTEGRATED_RUNTIME_IMPLEMENTED=False
P15_13_FREEZE_PERFORMED=False
P15_13_EXACT_IDENTITY_CONTINUITY=True
P15_13_EXACT_DESCRIPTOR_CONTINUITY=True
P15_13_EXACT_GOVERNANCE_CONTINUITY=True
P15_13_EXACT_ORCHESTRATION_CONTINUITY=True
P15_13_PROVENANCE_CONTINUITY=True
P15_13_NARRATIVE_ORIGIN_PRESERVED=True
P15_13_GOVERNANCE_PLUS_ORCHESTRATION_NOT_AUTHORITY=True
P15_13_SECURITY_ADMISSION_DOES_NOT_EXECUTE=True
P15_13_AUTHORITY_DENIAL_END_TO_END_FAILS_CLOSED=True
P15_13_PACKAGE_SUBSTITUTION_REJECTED=True
P15_13_DESCRIPTOR_SUBSTITUTION_REJECTED=True
P15_13_GOVERNANCE_SUBSTITUTION_REJECTED=True
P15_13_CROSS_NODE_ADMISSION_REPLAY_REJECTED=True
P15_13_ARTIFACT_ORIGIN_PRESERVED=True
P15_13_IDENTITY_DOMAINS_REMAIN_DISTINCT=True
P15_13_ACCEPTANCE_MATRIX_COMPLETE=True
P15_13_INTEGRATION_DETERMINISTIC=True
P15_13_ACCEPTANCE_RESULT_IS_NOT_EXECUTION_RESULT=True
P15_13_STATIC_SECURITY_AUDIT=PASS
P15_PLATFORM_INTEGRATION_MODEL=PASS
P15_PLATFORM_OWNERSHIP_MAP=PASS
P15_PLATFORM_IDENTITY_CONTINUITY=PASS
P15_PLATFORM_DESCRIPTOR_CONTINUITY=PASS
P15_PLATFORM_GOVERNANCE_CONTINUITY=PASS
P15_PLATFORM_ORCHESTRATION_CONTINUITY=PASS
P15_PLATFORM_SECURITY_CONTINUITY=PASS
P15_PLATFORM_PROVENANCE_CONTINUITY=PASS
P15_PLATFORM_INTERCHANGE_INTEGRATION=PASS
P15_PLATFORM_DOMAIN_BOUNDARIES=PASS
P15_PLATFORM_PACKAGE_SUBSTITUTION_DEFENSE=PASS
P15_PLATFORM_DESCRIPTOR_SUBSTITUTION_DEFENSE=PASS
P15_PLATFORM_GOVERNANCE_SUBSTITUTION_DEFENSE=PASS
P15_PLATFORM_ADMISSION_REPLAY_DEFENSE=PASS
P15_PLATFORM_IDENTITY_SEPARATION=PASS
P15_PLATFORM_EXECUTION_BOUNDARY=PASS
P15_PLATFORM_TRUST_BOUNDARY=PASS
P15_PLATFORM_AUTHORITY_BOUNDARY=PASS
P15_PLATFORM_DETERMINISM=PASS
P15_PLATFORM_STATIC_SECURITY=PASS
P15_PLATFORM_ACCEPTANCE_MATRIX=PASS
P15_12_REGRESSION=PASS
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
PATCH_MATRIX=PASS
CRYPTO_PROVIDER_UNAVAILABLE
READY_FOR_P15_14_CLOSURE_REVIEW=True
P15_13_READY_FOR_REVIEW=True
```

Readiness is for human review only. No closure/freeze work has begun.

```text
INTEGRATION_ACCEPTANCE != EXECUTION
INTEGRATION_ACCEPTANCE != AUTHORITY
INTEGRATION_ACCEPTANCE != PACKAGE_TRUST
INTEGRATION_ACCEPTANCE != RELEASE
INTEGRATION_ACCEPTANCE != FREEZE
END_TO_END_PLAN != END_TO_END_RUN
ADMITTED_NODE != EXECUTED_NODE
EXTERNAL_RESPONSE != VERIFIED_EXTERNAL_TRUTH
FABRICATION_PLAN != PHYSICAL_FABRICATION
AGENT_RECORD != HUMAN_IDENTITY
NARRATIVE_RECORD != REAL_WORLD_FACT
PARAMETRIC_VARIANT != GENERATED_GEOMETRY
SIMULATION_STATE != PHYSICAL_WORLD_STATE
SEMANTIC_AUTHORITY=CANONICAL_AIR
```
