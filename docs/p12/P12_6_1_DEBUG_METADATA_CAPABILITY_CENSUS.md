# P12.6-1 — Debug Metadata Capability Census

Scope: read-only inspection of the P12.5 execution freeze; one documentation artifact only. No source-map design, implementation, compiler flags, PDB behavior, P12.7, or P13 work. The explicit session request supersedes the stale current-stage text in AGENTS.md for this census only. Findings describe the inspected representations, not whole-language native support.

## Exact checkpoint and freeze references

HEAD = afp-p12.5-execution-freeze^{commit} = 6e71a1afae36c3b4984e949c707d3e6fae6cc269.
Initial Git status --short was empty. All three peeled commits are ancestors of HEAD.

| Tag | Annotated tag object | Peeled commit |
| --- | --- | --- |
| afp-p12.4-freeze | 7c475986ed3ed1d58cc30148603fbfe8b09529ee | 13f7646f1052746f54f906076d66d29117ee2718 |
| afp-p12.5-freeze | 9e2d7a4f57a10e0499d788f8584ace477f624b07 | 542be090e193b3d931d27c08e16de3efd961a01e |
| afp-p12.5-execution-freeze | 6ad3d33601a576c2b42e2fde16cd98c2c61980fd | 6e71a1afae36c3b4984e949c707d3e6fae6cc269 |

P12.4 and original P12.5 tag objects and commits match the frozen RCV-52 evidence. The execution tag points to the exact user-specified checkpoint; its object is recorded here and checked unchanged at session end. There is no earlier independent execution-tag-object value supplied in the request, so that object's historical immutability beyond this session is not independently asserted.

## Existing source and span mechanisms

- language/source.py: frozen SourcePosition uses one-based lines/columns and zero-based Python character offsets. SourceSpan is named and end-exclusive; SourceText maps offsets deterministically. Names are caller-supplied strings, not content identities. These are not byte offsets or LSP UTF-16 columns.
- language/lexer.py and parser.py: tokens and AST expression, declaration, action, parameter, type-annotation, and source-unit nodes have optional spans. AST spans use compare=False. Missing spans remain possible for hand-constructed nodes. Module header masking preserves offsets, lines, and columns (modules.py).
- compiler.py already contains SourceMapEntry(air_id, span, kind, reference), sorted SourceMap lookup/merge, and CompiledSource(program, source_map). This census does not introduce or redesign that existing source map. Declaration entries include directive, state, event, causal decision/path, function, authority, principal, role, workflow, and requirement evidence. Action/call/local/return entries use scope/index-based sidecar IDs; they must not all be assumed to name independent canonical AIR nodes.
- project.py: ProjectBuild retains source units, program, verified program, SourceMap, module/document graphs, declaration ownership, and identity/resolution metadata. A custom compiler returning bare AIR receives an empty SourceMap. SourceUnit stores name and source text without a content hash.
- declarations.py and identities.py retain physical source name, module name, declaration span, and AIR identity for directives/functions. Qualified display names are passive metadata; current IDs remain directive:<declared-name> / function:<declared-name> rather than module-qualified identities.
- tooling/build_artifact.py separately records loaded source paths and SHA-256 of source bytes, entry, canonical AIR, and a canonical artifact fingerprint. Its ordinary AIR artifact payload does not serialize ProjectBuild.source_map or TAM records. This source-byte identity is separate from the native receipt's generated-C hash.

## Existing AIR identities and diagnostic locations

AIRProgram contains semantic records and references, not source spans or source maps. Directives, states, events, functions, principals, decisions and paths have canonical string IDs; assignments refer to state IDs and do not carry their own source-side action ID. compiler.py produces scoped/indexed identities; air/ids.py also derives event-record identity from directive, decision, path, index and event. Canonical serialization preserves semantic IDs and content, without compiler sidecars.

VerifiedAIRProgram contains only program. VerificationResult diagnostics are separate and require_verified wraps the same program; no source metadata is added. VerifiedAIRLoweringInput keeps the wrapper, canonical AIR JSON and uppercase SHA-256 transport fingerprint. Its source_owner is a Python representation-owner label, not a source filename.

RegistryExecutionPlan contains program, entry_directive and directive_owners (casefolded lookup keys to owning AIRProgram). It has semantic ownership/routing, not physical source ownership. RegistryExecutionPlanBinding checks canonical transport equality and fingerprints AIR content, entry and sorted owner IDs. This general routing digest does not independently hash every owner's content; bounded native admission additionally checks the sole owner's exact canonical transport. TargetNeutralLoweringProduct retains the binding and fingerprints its canonical product.

BuildDiagnostic has optional primary span, related_spans and air_id. Project link/validation errors use source-map lookup to recover locations. Core runtime/verifier Diagnostic has severity/code/message/node_id without a span. LSP diagnostics explicitly convert character offsets to zero-based UTF-16 positions using supplied source text. NativeExecutionError has code/detail only; it does not recover ApexForge source locations.

GenericSpecializationKey identifies a function plus exact type arguments using canonical type encoding, with immutable specialization/table records. These are compile-time identities, not native symbol locations; the current native profile rejects functions and generic execution.

## Existing native provenance, generated source and debug evidence

Actual production profile: apexforge.native.win-x64.i64-literal-state-set/v1. NativeProfileAdmission retains AIR/routing fingerprints, exact entry, ordered state_ids, literal initializers, and ordered stores as (state index, literal). Decision/path/assignment identities are not retained per store. They participate in the whole AIR fingerprint but cannot be recovered from the emitted stores alone.

native_execution.py emits program.c with volatile s0, s1, ... variables, ordered assignments, emit, and apexforge_entry. No AIR names enter C identifiers. Generated lines are deterministic for admission values/order, but there is no generated-line-to-ApexForge-span or address-to-AIR relationship record, nor #line directive.

NativeArtifact contains image path, canonical receipt JSON, receipt fingerprint and a process-local issuance ticket. The receipt binds profile, AIR, routing, entry, sole owner AIR, state IDs, generated-C hash, compiler/linker/companion-DLL/kernel32.lib hashes, fixed options and whole-image hash. Build paths/timestamps are excluded. It does not include original source hashes/spans, per-store identity, native address ranges, symbol inventory, object hash, or a PDB record. execute_native removes temporary build products; build_native can retain them in a caller-provided directory.

Existing compiler options include /Od and /Brepro at compile/link boundaries, with fixed entry and no C runtime. There is no /Zi, /Z7, /DEBUG or /Fd option in this production command. This is command inspection, not a fresh binary-section/PDB characterization. Absence of those switches does not establish absence of all COFF metadata.

Frozen P12.4D policy explicitly documents observed .debug$S and .chks64 object-container variance, stable executable sections and .drectve, source/ABI/toolchain/flags/section/object hashes. Those historical metadata sections are not an ApexForge source mapping. P12.4G-C separately governs whole-DLL reproducibility. The lifecycle DLL exports only apexforge_release_handle and apexforge_release_buffer per the .def/header; it is a separate artifact from the bounded program.exe execution path.

Dispatch re-admits, verifies receipt issuance and generated source/input identity, and locks/hash-checks the image. Raw output is ordered little-endian I64 bytes without names. _decode restores original state IDs from admission. CanonicalExecutionResult.input_fingerprint is the receipt fingerprint; its own fingerprint combines input, status and payload fingerprint. NativeExecutionEvidence adds receipt JSON and raw-output fingerprint. No source locations, instruction addresses, TAM map, or semantic execution trace are carried.

## Actual TAM and semantic trace structures

Compiler TAM is real code: tam/model.py defines immutable TraceIdentity, TraceDomain, TraceRecord and TraceMap, with optional source_span/canonical_identity, provenance and upstream/downstream IDs. Domains are source, token, declaration, reference, scope, type, authority, narrative, ownership and transformation. TraceMap preserves supplied order and checks unique IDs; it does not infer edges or require referenced records to exist.

tam/production.py has explicit adapters for existing SourceMap entries, declaration/ownership indexes, resolution queries/contexts/candidates/outcomes, type evidence, authority evidence, narrative semantic evidence and lexer tokens. SHA-256 TAM-local IDs derive from explicit evidence keys and indexes. Source-span keys include name and both positions, but no source-content hash; source-map entry IDs include index, AIR ID and span. Thus deterministic within these inputs does not imply edit-stable or content-addressed source identity.

SourceMap projection actually creates source-to-transformation links and retains AIR IDs/spans. Other evidence adapters project their owner values; no universal complete execution graph is implied. compose_trace_maps explicitly concatenates supplied records. A repository search for adapter calls outside tests found definitions/re-exports, not automatic compiler/project/native pipeline attachment. ProjectBuild, VerifiedAIRProgram, RegistryExecutionPlan, native admission/receipt/result have no TraceMap field.

Core runtime Trace/TraceStep are a separate kind/message/Fact structure produced by RuntimeEngine (directive, authority, state delta, event, invocation, condition and function evidence). Diagnostic.node_id and facts can retain semantic IDs; TraceStep has neither SourceSpan nor TAM TraceIdentity. tools/trace_export.py exports those runtime records, not a TAM map. NarrativeExecutionResult separately carries ordered NarrativeExecutionTraceEvent(kind, message, string facts), diagnostics, state and choice identities. Semantic-decision model values have identities/provenance tuples; that does not make them a native execution trace.

TAP audit_trace_map is diagnostic-only observational projection: exact transformation/source-map-entry and authority-check/grant signatures map to reporting categories. Other TAM records are omitted rather than inferred as semantic changes or runtime events. Separate TAP adapters observe already-produced runtime, convergence, narrative, generic-lowering and directive results. None establishes source-to-native address mapping. Compiler TAM remains distinct from Concordat TAM-v3; TAP remains user-controlled and non-activating.

## Identity survival across the requested chain

| Boundary | Survives | Currently absent or lost |
| --- | --- | --- |
| source → AST/parser | caller source name, token/node spans, declared names; offset-preserving module masking | persistent source content identity in these nodes; spans optional |
| AST/parser → canonical AIR | semantic declaration/reference IDs and semantics | spans/action-sidecar IDs are external in CompiledSource.SourceMap, not in AIR |
| canonical AIR → VerifiedAIRProgram | full AIR graph/IDs | no automatic source-map, project identity or trace attachment |
| VerifiedAIRProgram → RegistryExecutionPlan | program IDs, exact entry, semantic owner programs | physical source/module/span sidecars; plan is separately built and then bound, not derived from a source-carrying wrapper |
| RegistryExecutionPlan → native profile | AIR/routing fingerprints, entry/state IDs and ordered store relocation | decision/path/assignment identity per store; source spans/TAM |
| native profile → native artifact | receipt provenance/state list, generated C and image identity | AIR names in C symbols; source spans/line/address mappings; per-store metadata |
| native artifact → execution result | validated receipt fingerprint, restored state IDs, values, output/result digests | executed store/path history, source location and semantic/TAM traces |

## Verification, limitations and recommended P12.6-2 gate

Performed Git checkpoint/tag/ancestry checks, static field and emitter inspection, repository call-site/debug-switch searches, and inspection of focused TAM/native test assertions. No test suite, compiler build, native dispatch or expensive regression stack was run: no behavior changed and the census claims are representation/command facts. Existing historical acceptance records are not presented as new live results. The shell helper failed to initialize twice; the repository inspection used Node's filesystem and direct Git invocation afterward. A debug-pattern search returned no matches (Git exit 1); this is an absence result, not a passing test.

Changed files: this document only. Production, tests, CLI, AIR, runtime and native flags remain untouched. Main limitations: optional/partial compiler spans; sidecar-only action IDs; loss of source content binding and physical ownership at execution seams; no per-store identity in admission; no source/native symbol/address relationship; no native semantic trace; transient artifacts and process-local issuance. No claim of wider native support or fresh PDB/PE characterization.

Recommended P12.6-2 next gate: human review of this census and agreement on a bounded debug-metadata contract scope for the existing native profile. Before any design/implementation, decide which existing identities and source-content evidence must be preserved, distinguish semantic identity from debug/build-container identity, and identify focused compatibility/admission/reproducibility checks required by any future contract. Treat optional spans, synthetic action IDs and exact native schema closure as explicit review questions. This recommendation is a gate proposal only; it specifies no new source-map format, API, flags, PDB behavior or implementation.

## Files inspected

Full text or selected relevant sections were read from these files (repository searches also examined matching tracked lines):

- AGENTS.md
- apexforge/aether_air/model.py
- apexforge/air/functions.py
- apexforge/air/ids.py
- apexforge/air/model.py
- apexforge/air/serialization.py
- apexforge/interoperability/build_artifact.py
- apexforge/language/build.py
- apexforge/language/compiler.py
- apexforge/language/declarations.py
- apexforge/language/diagnostics.py
- apexforge/language/identities.py
- apexforge/language/lexer.py
- apexforge/language/modules.py
- apexforge/language/parser.py
- apexforge/language/project.py
- apexforge/language/source.py
- apexforge/language_server/diagnostics.py
- apexforge/native_backend/execution_plan_binding.py
- apexforge/native_backend/lowering_input.py
- apexforge/native_backend/native_execution.py
- apexforge/native_backend/native_execution_contract.py
- apexforge/native_backend/result.py
- apexforge/native_backend/target_neutral_lowering.py
- apexforge/p11_tam_c_deterministic_trace_production_foundation_smoke_test.py
- apexforge/p11_tam_i_token_evidence_trace_production_smoke_test.py
- apexforge/p12_5_native_execution_acceptance_test.py
- apexforge/p12_5_native_profile_contract_test.py
- apexforge/p12_5_rcv_52_native_execution_dispatch_capability_census.json
- apexforge/p12_5_rcv_54_native_execution_acceptance.md
- apexforge/p12_5_rcv_55_execution_completion_review.md
- apexforge/runtime/diagnostics.py
- apexforge/runtime/engine.py
- apexforge/runtime/narrative_execution.py
- apexforge/semantic_decision/model.py
- apexforge/tam/integration.py
- apexforge/tam/model.py
- apexforge/tam/production.py
- apexforge/tap_check/adapters.py
- apexforge/tap_check/aggregation.py
- apexforge/tap_check/projection.py
- apexforge/tooling/build_artifact.py
- apexforge/tools/trace_export.py
- apexforge/trace_viewer.py
- apexforge/type_system/specialization.py
- apexforge/workflow/air_runner.py
- docs/p11/P11_11C_TRACE_MAP_OBSERVATIONAL_AUDIT_PROJECTION.md
- docs/p12/P12_4B_WIN_X64_MSVC_COFF_TOOLCHAIN_OBJECT_PROFILE.md
- docs/p12/P12_4D_COFF_REPRODUCIBILITY_PROVENANCE_POLICY.md
- docs/p12/P12_4G_C_DLL_REPRODUCIBILITY_POLICY.md
- runtimes/native/include/apexforge_native.h
- runtimes/native/link/apexforge_native.def

## Exact final Git status

Expected and verified after writing this artifact, using git status --short --untracked-files=all:

```text
?? docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
```

No staging, commit, tag or push operation was performed. HEAD and all recorded tag objects/peeled commits were rechecked after writing.

P12_6_CAPABILITY_CENSUS_COMPLETE=True

P12_6_IMPLEMENTATION_STARTED=False
