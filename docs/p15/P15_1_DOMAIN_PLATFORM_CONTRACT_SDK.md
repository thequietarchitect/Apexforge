# P15.1 Domain Platform Contract & SDK Foundation

Review evidence for the generic, passive contract foundation. No domain implementation, interchange implementation or P15 freeze operation.

## Frozen predecessor and branch isolation

P14 tag: `afp-p14.13-freeze`.
P14 freeze commit/peeled tag: `0731e9c00b2858079007dbafdb0e052f497fb24c`.
P14 commit parent: `860ba9287ee237ddca0691355607c896f3ea382f`.
P14 annotated tag object: `47e4fc83b2a858ba0bbca62ed57a9a2cfafd27b3`.

Initial working tree clean, no P15 candidates and no tracked P15 slice files. Created `p15-1-domain-platform-contract-sdk` with `git switch -c p15-1-domain-platform-contract-sdk 'afp-p14.13-freeze^{}'`. HEAD initially and finally equals the exact P14 freeze commit; no P15 commit exists. P14 branch remains at the same commit; tag object and peeled target unchanged. This user-authorized slice supersedes the historical P11.4A stage text in AGENTS.md; frozen core preservation remains active.

P14 package crypto state remains `CRYPTO_PROVIDER_UNAVAILABLE`. No provider/dependency installation. Git P14 commit/tag remain UNSIGNED; this is distinct from package-signing implementation state.

## Architecture census

| Existing contract | Classification | P15.1 treatment |
|---|---|---|
| language/identities.py ProjectDeclaredIdentity | FROZEN_CORE_CONTRACT; REUSE by P14 SymbolReference | Existing current AIR directive/function identity is preserved, not prefixed with domain/platform names |
| air/model.py and verified AIR owner | FROZEN_CORE_CONTRACT | Canonical semantic authority, no AIR creation/verification/execution in this slice |
| semantic_decision/model.py, semantic lattice and narrative models | FROZEN_CORE_CONTRACT; REFERENCE_ONLY | Existing semantic meaning is not reinterpreted as SDK/domain meaning |
| authority/model.py Principal/AuthorityCheck/AuthorityGrant and engine | FROZEN_CORE_CONTRACT | Runtime authority owner, no import or invocation in SDK |
| agents/model.py AgentIdentity | FROZEN_CORE_CONTRACT; REFERENCE_ONLY | Agent identity is not generic platform identity; no new agents |
| interoperability/build_artifact.py P11 passive artifact inspection | REFERENCE_ONLY | Existing interchange remains separate; no P15.2 parser/transport added |
| native_backend/native_execution_contract.py P12 exact profile | FROZEN_CORE_CONTRACT | Existing native limits unchanged; no compile or dispatch |
| tooling/debug_inspection.py and debug_evidence.py P13 supplied evidence projections | REFERENCE_ONLY | Passive input/evidence-before-attribution precedent; debugger schema/control not reused as SDK schema |
| tooling/package_manifest.py P14 identity/reference carriers | REUSE | PackageCoordinate, PackageContentIdentity, ExactVersion, CanonicalReference and SymbolReference remain P14-owned |
| package_capabilities.py | REFERENCE_ONLY | Package capability compatibility is separate from typed DomainCapability declaration |
| package_trust.py | FROZEN_CORE_CONTRACT; REFERENCE_ONLY | Passive provenance/signature boundary; no SDK trust verdict |
| package_registry.py, publishing/cache contracts | FROZEN_CORE_CONTRACT; REFERENCE_ONLY | No discovery, publication or automatic cache mutation |
| package_artifacts.py and package_supply_chain.py | REFERENCE_ONLY | Artifact/build/AIR evidence may be referenced using existing CanonicalReference; no competing package artifact or validation algorithm |
| rich_documents/codex_adapter.py and existing projection/authoring adapters | DOMAIN_EXTENSION_POINT; REFERENCE_ONLY | Explicit owner-preserving adaptation precedent; no external integration here |
| Simulation, motion, narrative, agent, parametric, fabrication and external adapters | DEFER_TO_LATER_P15 | Kind labels only; no behavior, backend, network provider or orchestration |

There was no generic package-bound domain SDK identity to reuse. The new identity belongs exclusively to this extension-contract domain. Existing semantic models remain their owners. The SDK deliberately supports existing P14 source/AIR/artifact/build/provenance references and directive/function symbol references; it does not fabricate references for unsupported semantic identity categories.

## Platform definition, identity and package binding

A domain platform is a caller-declared extension contract describing operations, declarative capabilities, exact implementation package and dependencies. It is not compiler-core semantics, organization, package, agent or runtime authority.

`DomainPlatformIdentity` is frozen: opaque validated ID, domain kind and `apexforge.domain-platform/v1` schema. IDs use bounded lowercase ASCII segments separated by dots; no whitespace, email, endpoint, absolute path or implicit owner fields. Same spelling across identity domains is not identity equivalence.

Kinds are a closed v1 set: simulation, motion, narrative, agent, parametric, fabrication, external-adapter. Unknown kinds fail DOMAIN_KIND_INVALID. Choosing a kind executes nothing. Adding future kinds requires an explicit versioned contract change; no plug-in discovery occurs.

`ImplementationPackage` references existing P14 coordinate and exact content identity; syntax is re-admitted by P14 owners. `from_manifest` re-admits the canonical manifest then uses its existing content_identity(). It does not hash package content using a new algorithm. A manually supplied binding is a declared exact reference, not proof of member bytes, installation, trust or publication. Content verification remains P14-owned.

`DomainPlatformDescriptor` carries identity, package binding, explicit contract version, operation names, typed capability declarations, dependencies and provenance. Contract version reuses the bounded ExactVersion value representation but has separate meaning from package version or SDK schema; no version range or compatibility inference. Empty operation sets are valid inert declarations.

`DomainDependency` is an exact platform/package/contract-version reference. Duplicate platform IDs, contradictory alternatives and self-dependencies fail DOMAIN_DEPENDENCY_CONFLICT. This is a declaration set, not a resolved dependency graph; no dependency availability, transitive traversal, cycle resolution or package solving is performed.

## Requests, results and artifact references

`DomainRequest` uses `apexforge.domain-request/v1`, exact descriptor and declared operation membership. Inputs are explicit caller-supplied CanonicalReference and SymbolReference tuples, domain artifact references, requested typed capability declarations and provenance. Optional correlation is caller-supplied bounded ASCII, never generated.

Syntax-invalid or undeclared operations fail deterministically; the SDK has no operation implementation or handler registry. Requested capabilities must be members of the descriptor's declarations. Membership does not evaluate contract satisfaction or runtime permission. No mapping between P14 capability strings and domain capabilities is invented.

`DomainArtifact` uses `apexforge.domain-artifact/v1` and carries producing platform, exact implementation package, operation, exact descriptor fingerprint, raw byte digest, canonical input/symbol references and provenance. Generic kinds are analysis, plan, model, data and external-reference. SOURCE/AIR/native/package artifact kinds cannot masquerade as domain output: unsupported kinds fail DOMAIN_CORE_SEMANTIC_BOUNDARY_VIOLATION.

`from_bytes` hashes supplied bytes with SHA-256, checks declared operation membership and records descriptor identity. `verify_bytes` checks actual supplied bytes. A direct digest-only artifact construction is a reference claim until bytes are supplied for verification; reference presence is not integrity or trust proof. No bytes are acquired or retained implicitly. An external-reference artifact remains digest-bound supplied reference material, not a network endpoint adapter.

`DomainResult` uses `apexforge.domain-result/v1` and binds exact request fingerprint, platform/package/operation and canonical input references. Included outputs must match the exact descriptor fingerprint, producer package content, operation and input/symbol lineage. Same coordinate/different content and different contract revisions cannot silently substitute. Status is caller-declared COMPLETE, INCOMPLETE or FAILED; incomplete/failed require diagnostics, failed results contain no outputs. It is not an SDK execution receipt or a completeness proof for a domain-specific output contract. Domain-specific output requirements are deferred.

All result records state declaration_only=true, semantic_authority=CANONICAL_AIR, grants_authority=false and authenticates_provenance=false. The result references semantic inputs without becoming AIR or changing their meaning. The exact request fingerprint preserves input artifacts, capability declarations, correlation and context even where the result's display record projects a smaller set.

## Core, authority and participant boundaries

The production SDK imports only dataclasses/hashlib/json/re and the existing P14 manifest/reference carriers. It has no parser, type-system, AIR verification, lowering, compiler, runtime, native dispatch or AuthorityEngine invocation. Canonical AIR remains semantic authority; output records cannot select a different semantic owner.

DomainCapability is a distinct frozen declaration type. Package capability, principal capability grant, role and runtime authority remain distinct; identical strings never prove equivalence. No AuthorityGrant or permission is created. Future host authorization must be performed through existing authority owners outside this SDK.

AgentIdentity remains in the existing agent domain; even an `agent` kind label does not create an agent. Platform and package IDs do not imply organization ownership. An `external-adapter` kind is a future contract participant, not identity/semantic/organization authority. No external API integration or provider authentication exists.

## Provenance and determinism

Existing CanonicalReference and SymbolReference objects are retained unchanged. Provenance records bind references only; they do not fetch, authenticate or prove historical claims. Request → platform descriptor → exact package → declared operation → result/artifact continuity is explicit. No human/publisher/organization attribution is inferred.

All production carriers are frozen and use tuples. Unordered inputs are canonically sorted by compact canonical record JSON; exact duplicates reject rather than silently override. Operation names sort lexically. Conflicting dependency IDs reject. Independent equivalent construction, input permutations and detached record mutation yield unchanged canonical serialization/fingerprints.

Canonical JSON: sorted keys, ASCII escaping, stable compact separators, finite JSON values and UTF-8. No timestamps, filesystem paths, username, hostname, process ID, locale or random UUID participate.

Fingerprints use SHA-256(domain + NUL + canonical UTF-8 JSON), uppercase hex. Descriptor/request/result/artifact domains are respectively apexforge.domain-platform/v1, apexforge.domain-request/v1, apexforge.domain-result/v1 and apexforge.domain-artifact/v1. Identity, dependency, capability and implementation-reference fingerprints use separate descriptive domain names in the module. These are evidence identities, not replacement package/AIR/build/trust/authority identities. Raw artifact-byte digest is distinct from artifact-record fingerprint.

## Diagnostics and validation boundary

DomainContractError.code is a deterministic identifier, without exception prose or sensitive payload echo. Codes cover schema, platform/kind, package, contract version, descriptor/dependency, operation syntax/membership, capability, input/provenance, artifact digest, result package/contract/input binding, correlation and diagnostic validity.

Result diagnostics are immutable code+bounded subject records with an explicit v1 vocabulary (input/result invalid, undeclared operation, missing evidence, operation not executed). Their ordering is canonical. Unknown diagnostic codes reject. These are generic contract diagnostics, not fabricated domain behavior.

Constructors admit typed supplied objects. Canonical serialization is supplied for evidence; raw JSON parsing, transports, interchange negotiation and adapter execution are deferred to P15.2/later explicit slices. Neither parsed strings nor arbitrary host files are implicitly trusted as typed domain objects. Python-level forged objects bypassing frozen constructors are outside this bounded API contract.

## Security and deferrals

No AIR execution, RuntimeEngine, native dispatch, compiler/build, installation, domain-code dispatch, filesystem discovery, network, environment discovery, registry query, cache I/O, publication, shell/subprocess or private-key persistence. Supplied bytes remain in-memory.

Static import/call assertions and dynamic traps for authority, registry, solver, file access, process and network pass. Transitive package-manifest imports are frozen passive identity/model dependencies, not runtime invocation. Existing runtime authority smoke executes only its pre-existing test fixture outside the SDK.

No simulation, ApexMotion, narrative, agent platform, parametric design, fabrication, external adapter, governance, orchestration or security integration was added. P15.2 interchange, domain-specific semantics, capability satisfaction/authority mapping, execution hosts and P15 freeze remain deferred. No registry/cache/trust/compatibility state is inferred by SDK success.

## Patch Matrix

Initial focused suite 29/29 PASS. Review exposed DOMAIN_PLATFORM_RESULT_GAP: artifact output lacked exact descriptor fingerprint, permitting otherwise matching platform/package/operation evidence across contract revisions. Classified before patch; owning section P15.1; patch surface new module/test only; frozen dependencies P14/P11/P12/P13 unchanged. Added descriptor-fingerprint binding and negative cross-revision fixture. Focused 30/30 PASS; frozen P14 aggregate, native profile, authority smoke and preservation pass. No predecessor blocker and no failed assertions concealed.

One discovery query assumed an apexforge/debugger directory; actual frozen observation modules are tooling/debug_inspection.py and debug_evidence.py. Read-only search correction only; no frozen file patch.

```text
DOMAIN_PLATFORM_RESULT_GAP=CLOSED
PATCH_MATRIX=PASS
```

## Validation

| Command | Result |
|---|---|
| python -X utf8 -B apexforge/p15_1_domain_platform_contract_sdk_test.py | 30/30 PASS |
| python -X utf8 -B -m unittest discover -s apexforge -p p14_*_test.py | 330/330 PASS |
| python -X utf8 -B apexforge/p12_5_native_profile_contract_test.py | 7/7 PASS |
| python -X utf8 -B apexforge/authority_consolidation_smoke_test.py | PASS |

Final P14 aggregate observed 26.101s, engineering checkpoint only, no performance SLA. Earlier aggregate during review also passed 330/330; final rerun followed the binding correction. Authority smoke confirms wrong principal/capability/resource denial, authorized existing RuntimeEngine fixture execution and transactional denied execution. No inventory-sensitive historical harness was added or blindly run.

Focused coverage includes versioned schemas, identities, exact binding/content substitution, kind declarations, dependency/operation/capability membership, symbol/AIR preservation, byte integrity, provenance, correlation, cross-contract output rejection, immutable/deterministic envelopes, diagnostics, static/dynamic security and a 1,000-operation/capability/reference fixture. Scale is bounded deterministic evidence, not benchmark certification.

## Preservation and exact Git status

HEAD remains P14 freeze on isolated P15 branch. Frozen P14 branch, annotated tag and peeled target unchanged. Tracked and staged diffs empty across the entire repository, so no frozen P10/P11/P12/P13/P14 path changed. No commits, stage, tag or push during P15.1. Only the three intended candidates below; no bytecode/cache/native generated residue. No P15.2/domain-specific/freeze work.

```text
?? apexforge/p15_1_domain_platform_contract_sdk_test.py
?? apexforge/tooling/domain_platform.py
?? docs/p15/P15_1_DOMAIN_PLATFORM_CONTRACT_SDK.md
```

## Truth markers

```text
P15_BASELINE=P14_13_FREEZE
P14_REOPENED=False
P15_DOMAIN_PLATFORM_PACKAGE_BOUND=True
P15_DOMAIN_PLATFORM_REDEFINES_CORE_SEMANTICS=False
P15_UNKNOWN_DOMAIN_SCHEMA_FAILS_CLOSED=True
P15_DOMAIN_SDK_INPUT=CALLER_SUPPLIED
P15_DOMAIN_SDK_GRANTS_AUTHORITY=False
P15_DOMAIN_SDK_INVOKES_AUTHORITY_ENGINE=False
P15_DOMAIN_OPERATION_EXECUTION_IMPLEMENTED=False
P15_DOMAIN_SDK_EXECUTES_AIR=False
P15_DOMAIN_SDK_EXECUTES_RUNTIME=False
P15_DOMAIN_SDK_DISPATCHES_NATIVE=False
P15_DOMAIN_SDK_COMPILES=False
P15_DOMAIN_SDK_INSTALLS_PACKAGES=False
P15_DOMAIN_SDK_EXECUTES_DOMAIN_CODE=False
P15_DOMAIN_SDK_HOST_COMMAND_EXECUTION=False
P15_DOMAIN_SDK_NETWORK_ACCESS=False
P15_DOMAIN_SDK_FILESYSTEM_DISCOVERY=False
P15_REDEFINES_P14_PACKAGE_IDENTITY=False
P15_1_DOMAIN_IMPLEMENTATIONS_ADDED=False
P15_1_AGENTS_IMPLEMENTED=False
P15_1_EXTERNAL_ADAPTERS_IMPLEMENTED=False
CRYPTO_PROVIDER_UNAVAILABLE
P15_DOMAIN_PLATFORM_MODEL=PASS
P15_DOMAIN_PLATFORM_IDENTITY=PASS
P15_DOMAIN_PLATFORM_PACKAGE_BINDING=PASS
P15_DOMAIN_PLATFORM_SCHEMA=PASS
P15_DOMAIN_REQUEST_CONTRACT=PASS
P15_DOMAIN_RESULT_CONTRACT=PASS
P15_DOMAIN_ARTIFACT_CONTRACT=PASS
P15_DOMAIN_CAPABILITY_BOUNDARY=PASS
P15_DOMAIN_PROVENANCE=PASS
P15_DOMAIN_DETERMINISM=PASS
P15_DOMAIN_CORE_SEMANTIC_BOUNDARY=PASS
P15_DOMAIN_AUTHORITY_BOUNDARY=PASS
P15_DOMAIN_SECURITY_BOUNDARY=PASS
P14_AGGREGATE_REGRESSION=PASS
P12_NATIVE_PROFILE_REGRESSION=PASS
P15_AUTHORITY_COEXISTENCE=PASS
P14_FROZEN_PREDECESSOR_PRESERVED=True
P15_1_CANDIDATES=3
P15_1_READY_FOR_REVIEW=True
```
