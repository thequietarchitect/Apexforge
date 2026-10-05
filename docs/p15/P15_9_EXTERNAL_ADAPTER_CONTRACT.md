# P15.9 External Adapter Contract — Review Evidence

P15.9 provides offline typed provider/adapter/request/response contracts. This is review evidence, not a release or freeze. No live transport, provider SDK, credential acquisition, model invocation, CAD/slicer/device dispatch, or later P15 milestone was implemented.

## Baseline and preservation

Branch: `p15-1-domain-platform-contract-sdk`. HEAD and frozen P14 branch: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
P14 annotated tag `afp-p14.13-freeze` object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`; peeled target: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
Incoming inventory was exactly 24 files. Tracked and staged diffs were empty; no generated residue was found. All incoming SHA-256 values below remain unchanged. Tracked diff emptiness also preserves P10–P14, frozen agent/authority and P11 narrative sources. No history/ref mutation was performed. Package crypto remains `CRYPTO_PROVIDER_UNAVAILABLE`; predecessor Git signing remains UNSIGNED, a separate matter.

| Incoming path | SHA-256 |
|---|---|
| apexforge/p15_1_domain_platform_contract_sdk_test.py | 0BA43486943D5C627F4E087ABECBE0B84C80492E124ECC72BD2BED351A255F62 |
| apexforge/p15_2_domain_interchange_contract_test.py | E88276DD0F3846A7C77BC412C547F728B19B134F9E8BD4FD0AE0089AFAB3B5D2 |
| apexforge/p15_3_apexmotion_domain_contract_test.py | C67BB50BED81970E568F3F0D25F5D5A067C5A7605D2AD72651FAB0575BBE9F3C |
| apexforge/p15_4_apexmotion_simulation_kernel_test.py | 08B76C272D00C9940F22F93CA88BE35C4FE0D84CF365B323B4E8EA579139AA8A |
| apexforge/p15_5_narrative_domain_contract_test.py | FA0521428CE6DDDE6BE0055EAEDA6E8C13C8ED5130AB4CCE2BC3F9374C49DD6E |
| apexforge/p15_6_agent_domain_contract_test.py | 1197B2D82E28EA4B91F240946387AECE8E41FEEE788F824E021DD630F65CF5C5 |
| apexforge/p15_7_parametric_domain_contract_test.py | BF70EBF1ABD171685330F6D2800878E721B6882CDE20108447EB20E7067945A8 |
| apexforge/p15_8_fabrication_domain_contract_test.py | 8C07880ACD1B05014DBD31FB6B8AD261C6E9EEFBC35D695D3EEE332EBA1612C8 |
| apexforge/tooling/agent_domain.py | A56E46EF274C8A9B81E0E6D8B90933B30A17996C7FB752284C891D145E312864 |
| apexforge/tooling/apexmotion.py | 571645F0974A7D883A30C2FAE2B0E6BD6E08EB20CFA064DD4F0294E7F2B466B6 |
| apexforge/tooling/apexmotion_simulation.py | EBF4EC35362A12D12031E8E3A08ADC1DF98420604E2315854DA8FB16A1891D50 |
| apexforge/tooling/domain_interchange.py | 31A57D37FAE3932A6D5A465369B907BABF761E70AFF7682503EAD40FABA19CEC |
| apexforge/tooling/domain_platform.py | 3826AD16F29D08A7628A89938A123ED6E62AF262F73277CFEEA7F285880CD2A3 |
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

## Architecture census and ownership

- REUSE: P15.1 immutable platform, exact P14 implementation package, domain capability, domain artifact; P14 canonical provenance references and exact version types.
- REUSE: P15.2 generic artifact interchange and strict parser. P15.9 does not define another top-level interchange protocol.
- FROZEN_EXTERNAL_CONTRACT / REFERENCE_ONLY: `rich_documents/codex_adapter.py` binds supplied advisory proposals to frozen document/block lineage; `semantic_lattice/adapters.py` preserves source-owned identities; `quad_vector/authoring/adapter.py` validates neutral human/tool/advisory declarations without implementation loading. None is an external-provider identity or transport owner.
- FROZEN_AUTHORITY_CONTRACT: existing authority/principal/role/capability contracts remain external to this module. The authority smoke exercises these unchanged owners.
- REFERENCE_ONLY: native execution and editor/LSP subprocess wrappers are controlled historical execution seams, not permission for external adapter dispatch.
- REFERENCE_ONLY: P15.6 agent identity/session/action-intent, P15.7 CAD references, P15.8 fabrication evidence. No conversion or automatic dispatch is added.
- ADAPTER_EXTENSION_POINT: typed provider, adapter, operation, credential reference, request and supplied response records.
- DEFER_TO_LIVE_TRANSPORT / EXTERNAL_ENVIRONMENT_DEPENDENCY: historical integrations requiring external executable, network, credentials or hardware were not activated or tested live.
- DEFER_TO_P15_10: governance, authorization integration and orchestration.

## Contract

Platform `apexforge.external-adapter`, kind `external-adapter`, SDK version 1.0.0 declares only `external.request.describe` and `external.response.describe`. The P15.1 descriptor retains coordinate and exact package content identity.

ExternalProviderIdentity and ExternalAdapterIdentity are separate frozen opaque identifier types. Identifiers follow the bounded SDK name syntax (128 characters); email/path/display names are not substituted for identity. No organization, human, model, agent, principal, ownership or affiliation relation is inferred. No provider-name field or affiliation proof is introduced.

ExternalAdapterDescriptor binds adapter/provider identities, exact SDK platform/package and contract version, explicitly declared ExternalOperations, domain capability requirements, credential-reference kinds and provenance. Schemas are separate `apexforge.external-adapter/v1`, `apexforge.external-request/v1`, `apexforge.external-response/v1`. Unknown schema/operation fails closed. Operation idempotency is an explicit Boolean declaration, never inferred from operation names.

CredentialReference contains an opaque ID, bounded reference kind, provider and declared scopes. It has no credential-value slot; it never retrieves, validates or logs a secret. Scope declarations are not authorization. When a descriptor declares credential kinds, a matching reference is required. Identifiers are caller-supplied references, not a vault or secret storage API.

ExternalRequest binds the exact adapter descriptor fingerprint, adapter/provider/package, declared operation, explicit correlation ID, canonical input references, exact declared capability requirements, optional credential reference and opaque payload, plus provenance. Requirements grant no permission. Constructor/admission/retry helpers perform structural validation only. Inputs may retain canonical AIR/semantic references without interpretation.

ExternalResponse retains the exact request and fingerprint, correlation and provider, reported status, output references, bounded diagnostic codes, optional opaque payload and provenance. Statuses are REPORTED_SUCCESS, REPORTED_FAILURE, REPORTED_REJECTED and REPORTED_PENDING. Admission rejects cross-provider/correlation/request/revision substitution. A caller can supply a new self-consistent record; hashes provide consistency, not authenticity. Authentication remains unimplemented.

ExternalPayload binds an uppercase SHA-256 digest and optionally caller-supplied exact bytes. Supplied bytes must match the digest and are limited to 1 MiB. Bytes are opaque and never parsed, executed, expanded into local paths or converted into arbitrary objects. Reference/declaration collections are bounded to 4,096, exact-typed, canonically sorted; conflicting operations and duplicate references are rejected. Diagnostics use a closed code set.

No raw provider JSON parser or provider-specific external artifact locator is implemented. Typed constructors admit supported fields and reject unsupported constructor fields; generic P15.2 JSON parsing remains responsible for its own strict schema/unknown-field/duplicate-key validation. Provider-specific bytes remain outside ApexForge semantic authority. Future typed payload parsing and authenticated/live transports require later explicit work.

`admit_response` is the offline reference admission seam, supplied only typed caller evidence. `retry_request` returns the unchanged request, retaining exact identity without transmission, delay or a timed retry policy. Correlation is explicit; no random or wall-clock identity is generated. No transport callback or dynamic plugin loader exists.

`domain_artifact` wraps descriptor/request/response canonical bytes as P15.1 external-reference artifacts under the exact platform/package with provenance. P15.2 serializes/reconstructs these generic artifacts; consumers separately retain supplied payload bytes. P15.9 does not reconstruct its typed records from JSON. Generic DomainRequest/DomainResult can carry those artifacts through existing SDK contracts; no new SDK model is forked.

## Evidence and boundaries

Fingerprints inherit deterministic sorted-key compact JSON and SHA-256 over distinct schema domains plus NUL and canonical bytes. Descriptor, request, response, opaque-payload and SDK artifact identities remain distinct. Unordered declarations/references canonicalize; correlation and operation changes bind new request identity. No timestamps, environment variables, endpoint, secret, host path, random value, DNS or machine state affects records.

Provenance binds supplied references to provider/adapter/request/response lineage. It establishes no authenticated authorship, external truth, external completion, provider affiliation, organization ownership, package trust or authorization. EVIDENCE_BEFORE_ATTRIBUTION=True. CANONICAL_AIR remains semantic authority. Agent != provider != model; narrative characters remain separate; fabrication plans and CAD references are not external commands.

Static AST audit confirms only dataclasses/hashlib/re/SDK/package-contract imports, no eval/exec/open/dynamic import/network/process/authority/runtime dependencies, no asynchronous/background loops or secret retrieval/logging. Production inputs are caller-supplied immutable records or bytes. No arbitrary callbacks or plugin discovery.

## Validation and Patch Matrix

Focused P15.9: **28/28 PASS**, including approximately 1,000 request/response records repeated deterministically. Exact revisions, package binding, schemas, operations, capabilities, credential references, response substitution, reported statuses, immutable models, payload integrity/bounds, provenance, generic artifact interchange, retry identity and static security are covered.

P15.8–P15.1 focused reruns: **33, 31, 29, 29, 23, 30, 40, 30**, all PASS.
P15 aggregate: **273/273 PASS**.
P14 aggregate: **330/330 PASS**.
P12 native profile: **7/7 PASS**.
Authority consolidation: canonical identities, exact grant, wrong principal/capability/resource denial, authorized RuntimeEngine execution and transactional denied execution all PASS. This smoke invokes the frozen runtime; the P15.9 module does not.

Commands: `python -X utf8 -B apexforge/p15_9_external_adapter_contract_test.py`, each predecessor focused command, `python -X utf8 -B -m unittest discover -s apexforge -p p15_*_test.py`, corresponding P14 aggregate, native-profile and authority-smoke commands.

Initial test failure -> EXTERNAL_ADAPTER_MODEL_GAP -> owning P15.9 focused assertion -> frozen P15.1 byte-verification contract -> test-only patch -> assert exact digest after verify_bytes (which returns None and raises on mismatch) -> focused PASS -> predecessor focused PASS -> both aggregates PASS -> preservation hashes/diffs/ref audit -> PATCH_MATRIX=PASS. No assertions were weakened and no predecessor changed. No unresolved defect found.

## Supported markers

```text
P15_BASELINE=P14_13_FREEZE
P15_9_INCOMING_CANDIDATES=24
P14_REOPENED=False
P15_9_EXTERNAL_ADAPTER_USES_P15_DOMAIN_PLATFORM=True
P15_9_ADAPTER_PACKAGE_BOUND=True
P15_9_EXTERNAL_RESPONSE_REQUEST_BOUND=True
P15_9_EXTERNAL_RESPONSE_IS_SUPPLIED_EVIDENCE=True
P15_9_UNKNOWN_EXTERNAL_SCHEMA_FAILS_CLOSED=True
P15_9_REDEFINES_CORE_SEMANTICS=False
P15_9_PROVIDER_NAME_PROVES_AFFILIATION=False
P15_9_EXTERNAL_PROVIDER_AFFILIATION_INFERRED=False
P15_9_CREDENTIAL_VALUES_STORED=False
P15_9_CREDENTIAL_VALUES_LOGGED=False
P15_9_EXTERNAL_REQUEST_EXECUTES=False
P15_9_EXTERNAL_RESPONSE_AUTHENTICATION_IMPLEMENTED=False
P15_9_LIVE_NETWORK_TRANSPORT_IMPLEMENTED=False
P15_9_TRANSPORT_IS_SEMANTIC_OWNER=False
P15_9_IDEMPOTENCY_INFERRED_FROM_OPERATION_NAME=False
P15_9_AUTOMATIC_RETRY_EXECUTION_IMPLEMENTED=False
P15_9_AGENT_INTENT_AUTO_DISPATCH=False
P15_9_FABRICATION_AUTO_DISPATCH=False
P15_9_CAD_AUTO_DISPATCH=False
P15_9_EXTERNAL_BYTES_EXECUTED=False
P15_9_EXTERNAL_ADAPTER_GRANTS_AUTHORITY=False
P15_9_EXTERNAL_ADAPTER_INVOKES_AUTHORITY_ENGINE=False
P15_9_VALID_EXTERNAL_RECORD_GRANTS_TRUST=False
P15_9_NETWORK_ACCESS=False
P15_9_FILESYSTEM_DISCOVERY=False
P15_9_DYNAMIC_PLUGIN_LOADING_IMPLEMENTED=False
P15_9_HOST_COMMAND_EXECUTION=False
P15_9_EXECUTES_AIR=False
P15_9_EXECUTES_RUNTIME=False
P15_9_DISPATCHES_NATIVE=False
P15_9_COMPILES=False
P15_9_INSTALLS_PACKAGES=False
P15_9_EXECUTES_EXTERNAL_CODE=False
P15_9_SECRET_ACQUISITION_IMPLEMENTED=False
CRYPTO_PROVIDER_UNAVAILABLE
EVIDENCE_BEFORE_ATTRIBUTION=True
P15_EXTERNAL_ADAPTER_PLATFORM_MODEL=PASS
P15_EXTERNAL_PROVIDER_IDENTITY=PASS
P15_EXTERNAL_ADAPTER_IDENTITY=PASS
P15_EXTERNAL_ADAPTER_PACKAGE_BINDING=PASS
P15_EXTERNAL_OPERATION_MODEL=PASS
P15_EXTERNAL_REQUEST_MODEL=PASS
P15_EXTERNAL_RESPONSE_MODEL=PASS
P15_EXTERNAL_CORRELATION_BINDING=PASS
P15_EXTERNAL_CREDENTIAL_REFERENCE_BOUNDARY=PASS
P15_EXTERNAL_AGENT_PROVIDER_BOUNDARY=PASS
P15_EXTERNAL_AFFILIATION_BOUNDARY=PASS
P15_EXTERNAL_PROVENANCE=PASS
P15_EXTERNAL_DETERMINISM=PASS
P15_EXTERNAL_TRUST_BOUNDARY=PASS
P15_EXTERNAL_AUTHORITY_BOUNDARY=PASS
P15_EXTERNAL_SECURITY_BOUNDARY=PASS
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
P15_9_READY_FOR_REVIEW=True
```

## Final repository state

Exactly 27 intended P15 candidates; nothing staged. HEAD, P14 branch/tag object/peeled target unchanged. Tracked and staged diffs empty. No generated residue. No commit, tag or push; no P15.10 or freeze work.

Exact `git status --short --untracked-files=all`:

```text
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
?? apexforge/tooling/domain_interchange.py
?? apexforge/tooling/domain_platform.py
?? apexforge/tooling/external_adapter.py
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
?? docs/p15/P15_9_EXTERNAL_ADAPTER_CONTRACT.md
```

