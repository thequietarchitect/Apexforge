# P12.6-2 — Bounded Debug-Metadata Scope and Compatibility Review

Status: PASS for this documentation-only scope and compatibility review. This is a proposed ownership contract for human review, not implementation approval, a milestone completion declaration, or a release. Canonical AIR remains semantic authority. No production or test code is changed.

## Checkpoint and primary evidence

HEAD = afp-p12.5-execution-freeze^{commit} = 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

Initial status contained only docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md. That census is the primary evidence and remains byte-for-byte unchanged (SHA-256 496eee7b666586074869b69c27e91363f9d141692c35b460341581eda38fb1b5). The session's explicit P12.6-2 request governs scope despite the stale current-stage section in AGENTS.md.

| Freeze | Tag object | Commit |
| --- | --- | --- |
| afp-p12.4-freeze | 7c475986ed3ed1d58cc30148603fbfe8b09529ee | 13f7646f1052746f54f906076d66d29117ee2718 |
| afp-p12.5-freeze | 9e2d7a4f57a10e0499d788f8584ace477f624b07 | 542be090e193b3d931d27c08e16de3efd961a01e |
| afp-p12.5-execution-freeze | 6ad3d33601a576c2b42e2fde16cd98c2c61980fd | 6e71a1afae36c3b4984e949c707d3e6fae6cc269 |

The original P12.5 freeze is the reconstruction checkpoint; the execution freeze is the current baseline. Both tag objects and all peeled commits match P12.6-1 and were rechecked at the end. All three commits are ancestors of HEAD. No tag was created or moved.

Preserved census findings: locations already survive tokens, AST, compiler SourceMap and project sidecars; VerifiedAIRProgram and RegistryExecutionPlan do not carry that sidecar; native receipts/evidence already bind AIR, routing, generated C, toolchain, executable image, output and result fingerprints across their respective layers; no source→native location map or PDB contract exists; TAM has actual source/token/declaration/ownership/resolution/type/authority/narrative adapters; runtime traces are separate; native results contain neither TAM nor runtime trace records; physical source/span and decision/path identity are lost at later seams. Proposed records below do not describe existing implemented fields.

## Proposed ownership contract

Adopt:

existing portable source identity + compiler SourceMap
→ compiler/tooling-owned deterministic metadata sidecar
→ exact AIR content and structural identity references
→ external execution-plan provenance association
→ bounded native operation/generated-source mapping
→ separate artifact/result provenance association.

| Layer | Owner and responsibility | Boundary |
| --- | --- | --- |
| Source snapshot, tokens/AST | Existing loader/source/lexer/parser owners | Supply source bytes/text and existing spans; metadata does not parse or reinterpret syntax |
| SourceMap and source→AIR evidence | Existing compiler/project owners | Authoritative producer of correspondence; preserve kinds, references and all observed relationships |
| Deterministic metadata sidecar | Compiler/tooling boundary adjacent to CompiledSource/ProjectBuild, separate from frozen dataclasses | Own source snapshot references and typed AIR/source correspondences; expose immutable evidence, not semantics |
| Canonical AIR and verification | Existing AIR/compiler/verifier | Continue owning semantics and validity; no span, path, metadata ID or debug flag added to AIR |
| Plan provenance association | External companion to existing execution-plan binding | Reference sidecar digest, AIR digest, routing digest, entry and owner-content references; plan remains routing owner |
| Native operation mapping | Native lowering/emission owner | Record structural correspondence for already-admitted operations in exact emitted order; no source interpretation |
| Artifact/result provenance | External companion to existing native artifact/evidence | Bind metadata/mapping digests to existing receipt, image and result/output fingerprints; no runtime event synthesis |
| TAM / runtime traces | Their existing owners | Optional references to observed records only; no ownership transfer or automatic execution |

Use a sidecar as metadata owner; a provenance envelope carries only binding/reference evidence. Lowering metadata owns only AIR-operation→generated-source correspondence and references the source sidecar. Neither a provenance receipt, TAM map, registry plan nor AIR itself is an alternative owner for compiler source correspondence. Existing compiler/project and loader ownership provides the narrowest coherent location; do not introduce a parallel parser or compiler.

## 1. Source identity and span reuse

Reuse language.source.SourcePosition, SourceSpan and SourceText unchanged: one-based line/column, zero-based Python character offset, named end-exclusive spans. Preserve EOF/empty spans and optional absence. LSP UTF-16 conversion remains a presentation operation owned by language_server/diagnostics.py; byte offsets are not substituted for character offsets.

For portable file-backed metadata, use the manifest's validated project-relative slash-separated source name and exact original UTF-8 byte SHA-256, with an explicit file-source kind/encoding policy. This follows tooling/project_manifest.py and project_loader.py: reject absolute/drive/UNC paths, traversal, empty/dot segments and casefold-colliding project source names; retain canonical spelling rather than lowercasing identity. Physical resolved paths/root belong only to local lookup. A portable source key is scoped by its sidecar/project source-set identity, not globally by basename. Different paths with identical bytes remain distinct source units.

For in-memory inputs, use an explicit logical source label and exact supplied text encoded as UTF-8, identified as an in-memory snapshot. Do not claim those bytes were read from disk. Missing snapshots/spans are explicitly unavailable; do not fabricate names or locations. Do not strip an absolute path to its basename, since that silently merges identities. If existing SourceSpan.source_name is nonportable, the source owner must provide an explicit unambiguous name association to a portable snapshot, or the export must report unavailable/reject it. Do not silently rewrite frozen spans or TAM IDs.

Do not normalize newlines, Unicode, BOMs, whitespace or case inside source content. Verify the snapshot text used for spans corresponds to its declared bytes/encoding, and positions are consistent with that text. Character offsets alone cannot authenticate the source revision. Keep raw bytes out of the sidecar when a digest/reference suffices; source retention is a separate caller responsibility.

## 2. SourceMap→AIR association and minimum metadata identity

Bind every source sidecar to the exact canonical AIR transport fingerprint already produced by VerifiedAIRLoweringInput, retaining its established canonical serialization and hash rules. Sidecar identity includes its own schema/policy version and source-content evidence; it is not an AIR semantic identity. The same AIR content can legitimately have multiple source sidecars (different comments, source arrangements or revisions); one AIR digest is not a unique source-map lookup key.

Minimum AIR reference: exact AIR program fingerprint plus typed structural locator. Use an existing canonical node ID where available, scoped by owning collection/parent, and a tuple of collection/occurrence indices where nodes lack unique IDs. Preserve exact IDs, kinds and parent relationships; no display-name, alias, casefold lookup or string concatenation may replace the locator. Occurrence indices distinguish equal repeated assignments. Identity is deterministic for the exact AIR revision, not stable across arbitrary edits. A typed tuple avoids delimiter collisions and accommodates Unicode IDs without making them C identifiers.

For a store in the bounded profile, the locator identifies the program, entry directive, occurrence in its causal_decisions tuple, referenced decision, sole admitted path, and assignment ordinal within that path. State initialization uses the program/state occurrence and exact state ID. Existing references can be checked for exact structural consistency against canonically verified, already-admitted AIR; metadata must not select among candidates or perform source-name resolution. Scope duplicate local path IDs by their decision and program. Output encoding/OS calls are backend infrastructure, not invented ApexForge operations.

Preserve SourceMapEntry.air_id/kind/reference and original entry occurrence as compiler evidence. Declaration entries may refer directly to real AIR IDs. Synthetic assignment/call/local IDs are compiler-side identities, not automatically AIR node IDs. The compiler/project owner must supply or validate explicit structural correspondence; the metadata layer cannot infer it by matching literal values, sorting spans, zipping entries to AIR assignments, first-match lookup, or reparsing source. Preserve one-to-many relationships, duplicates and distinct equal operations. Missing, contradictory or ambiguous evidence is an explicit unmapped/invalid mapping, never a guessed span.

No AIR schema extension or new semantic IDs are required: existing canonical IDs plus revision-scoped structural occurrence locators suffice. Exact wire encoding, serializer APIs and module names are intentionally deferred to the next contract/foundation gate.

## 3. Plan references without plan ownership

Do not add fields to RegistryExecutionPlan or VerifiedAIRProgram. The native contract's exact dataclass inventory would reject unreviewed schema changes. Associate metadata through an external companion to RegistryExecutionPlanBinding, keyed by verified AIR digest, existing routing digest, exact entry, sidecar digest and explicit owner-program fingerprints where relevant. The companion may retain read-only references, but neither owns nor reconstructs source metadata.

The current routing fingerprint includes sorted owner keys, not a digest of every owner program. Preserve it exactly. The bounded profile additionally checks sole-owner transport equality, so its owner AIR reference can reuse that validated content digest. Multi-owner composition, transformed AIR, generic lowering and relinking need explicit correspondence from their existing owning transformations before source metadata can follow them. Do not claim that equal IDs alone carry locations through those transformations. Such extensions are outside the first bounded gate.

## 4. Bounded AIR→native mapping and compatibility gap

Use explicit ApexForge metadata operation IDs derived from the structural locators as the primary mapping anchor. Record decision/path/assignment occurrence and ordered store ordinal before identity is reduced to (state index, literal). State ID plus literal is insufficient: repeated and overwritten stores remain distinct. Preserve initialization operations separately. Do not change NativeProfileAdmission's existing schema in the first gate; any future mapping companion observes it and must show one-to-one agreement with the admitted relocation/store sequence without computing final state.

During a separately authorized emitter integration, record operation-ID→generated program.c range as each existing line is emitted, bound to the exact generated-source hash and emitter/mapping policy version. This is a generated-source map, not a machine-address map. Retain s0/s1 identifiers and existing emitted bytes/options; do not inject #line directives, extra runtime calls or rename variables to encode source identities. Identifiers and compiler symbols can disappear, collide, be decorated or change with toolchain choices, so neither is the authoritative anchor. No instruction/RVA relationship is asserted without actual future compiler/linker evidence.

**Live gap:** compiler.py:1347–1380 fills both path.assignments and path.actions. native_execution_contract.py:132–134 requires actions to be empty; the focused native tests construct assignment-only AIR and explicitly reject nonempty actions. Thus ordinary compiler-produced assignment paths are not automatically admitted by this native profile. Metadata cannot erase actions, authority checks or other rejected constructs, normalize them into acceptable AIR, or broaden admission. Source→native operation coverage remains unavailable for this route until a separately named compatibility gate owned by the compiler/canonical lowering/profile authorities provides tested evidence. This review does not authorize that gate or disguise it as metadata infrastructure. Hand-authored admitted AIR can have deterministic operation metadata with source locations explicitly unavailable; attaching a source fixture by assertion is not authentic correspondence.

Consequently the full chain is an ownership contract, not a claim that this baseline already supports end-to-end source-mapped native execution. Preserve P12.5 rejection behavior, exact ordering, no-second-semantics protections and all assertions.

## 5. Native artifact/result association and PDB decision

Keep frozen P12.5 receipts, receipt fingerprints, CanonicalExecutionResult.input_fingerprint and result schemas unchanged. A separate versioned provenance association may bind the source-sidecar digest, plan-association digest and native-mapping digest to the existing receipt fingerprint, generated-source hash and whole-image hash. A result association references that artifact association plus existing canonical result and raw-output fingerprints. An association must validate all links rather than overwrite a frozen fingerprint with a metadata digest. It is provenance evidence, not a signature or transferable issuance ticket.

Do not claim a store executed merely because it has an emitted range or final state value. Native results currently carry neither TAM nor runtime traces; this review adds no trace execution contract. execute_native's temporary cleanup means persistence/retention would require later explicit caller-owned artifact handling, not embedding machine paths in identity.

**PDB/debug-symbol decision: not used or required in the bounded P12.6 contract.** No /Zi, /Z7, /DEBUG, /Fd, PDB generation, symbol extraction, flag changes or debugger behavior is authorized. /Od is not a debug mapping contract. Historical .debug$S/.chks64 observations prove that some COFF metadata exists, not that ApexForge spans are mapped.

If a future separately authorized review considers compiler debug metadata, require same-path and relocated-build characterization, logical-path remapping/path-leak scanning, exact toolchain/options binding, documented GUID/age/timestamp/path behavior, and separation of auxiliary debug-container identity from semantic/source identity. Whole artifact digests must still cover actual bytes; do not remove nondeterministic PE fields or sections from frozen image/DLL hashes to obtain reproducibility. P12.4D's object policy and P12.4G-C's whole-DLL policy remain intact. Compiler metadata may supplement a proven mapping later, never replace explicit ApexForge identity or justify weakening reproducibility.

## 6. TAM retention and runtime-trace boundaries

Retain and reference existing TAM adapters: trace_map_from_source_map, trace_map_from_token_evidence, trace_map_from_declaration_identity_indexes, trace_map_from_resolution_observation, trace_map_from_type_evidence, trace_map_from_authority_evidence and trace_map_from_narrative_evidence, together with their existing TraceIdentity/TraceRecord/TraceMap and explicit composition behavior. Do not duplicate adapters, create a substitute TAM, reinterpret missing records or automatically run semantic owners to populate evidence.

TAM is a view of existing evidence, not the source-map owner, a complete execution graph or a semantic decision engine. Existing source-span TAM IDs lack content hashes and are index/name dependent; keep their definitions and link them to a source snapshot through external provenance when available. Do not rewrite those IDs to satisfy portable metadata policy. A malformed/nonportable/unbound record cannot be silently relabeled portable.

Core RuntimeEngine TraceStep(kind, message, facts), narrative trace events and semantic-decision provenance remain separate owner products. Metadata may reference actually supplied evidence; it does not translate generated C into runtime events or merge runtime records into TAM. Existing TAP projection/adapters remain diagnostic-only, read-only, user-controlled and non-activating. Compiler TAM does not replace Concordat TAM-v3.

| Evidence fields | Classification |
| --- | --- |
| AIR IDs, typed locators, actual decision/path references, type/authority identities supplied by owners | Semantic identity references; metadata assigns no semantic meaning beyond owner evidence |
| Portable source key/content hash/span, sidecar/map digest, AIR/routing/receipt/image/output/result digests, TAM IDs and explicit edges | Provenance/correspondence identity within their stated schema and scope |
| Producer/owner/representation/schema labels | Deterministic interpretation contract, not host information |
| Trace kind, owner-provided facts, messages and provenance strings | Owner evidence; not automatically identity-safe or environmental-safe. Preserve original records; only explicitly governed typed references enter new metadata fingerprints |
| Host path, temp directory, PID, wall time, tool discovery location, raw logs | Environmental telemetry; exclude from portable deterministic metadata |

TAM fields named provenance are free-form tuples, so their name alone does not make them canonical fingerprint inputs. Existing runtime/TAM fingerprint or identity rules are not modified. Do not hash arbitrary rendered messages or logs as new identity.

## 7. Determinism and fingerprint exclusions

Deterministic metadata inputs must include: schema and identity/encoding/mapping policy versions; exact portable source names/kinds and original byte hashes; explicit unavailable/coverage states; observed spans and SourceMap kinds/references/occurrences; exact AIR transport digest and typed locators; validated parent/owner content references; governed deterministic ordering and actual relationship multiplicity. Reference external TAM identities only when present and within their recorded snapshot context. Source text changes must change source-content provenance even if AIR semantics do not change.

Plan associations additionally include sidecar digest, existing AIR/routing fingerprints, exact entry and necessary owner-program hashes. Native mappings additionally include profile, operation IDs in existing execution order, generated-source name/ranges/hash, and mapping/emitter policy version. Artifact/result associations include mapping/sidecar references and the existing receipt/image/result/output fingerprints. Reuse existing SHA-256/canonical AIR rules; do not invent a rival AIR hash or silently combine these distinct digest domains.

Toolchain binary hashes, fixed governed options and target/profile remain native build-provenance inputs, not source semantic identity. Metadata/source identity should survive moving the project or changing an unrelated host; native build identity legitimately changes when actual toolchain/code bytes change. Existing P12.5 receipt rules remain unchanged.

Exclude from new portable deterministic fingerprints: machine-specific absolute paths, workspace/install/temp roots, discovery paths and PATH/environment dumps, usernames/machine names, timestamps/mtime/wall-clock duration, process/thread IDs, memory/object addresses, random ticket/UUID values, build-directory spelling, locale-dependent formatting, raw compiler logs, nondeterministic traversal order, auxiliary PDB GUID/age/path telemetry and arbitrary presentation strings. Never include secrets. Sort set-like metadata deterministically under declared rules, but never sort or deduplicate executable operations or observed trace sequences. Whole file byte hashes still include every byte, even when an embedded field is environmental; exclusions are about field-level metadata inputs, not permission to redact hashed artifacts.

## 8. Explicit no-second-semantic-implementation review

| Forbidden behavior | Contract result |
| --- | --- |
| Resolve names | Only exact already-owned AIR IDs/locators and explicit source associations; ambiguous correspondence is a gap |
| Infer types | Reference existing type evidence; no native metadata inference |
| Evaluate expressions | Observe admitted literals/operations; no constant folding or final-state computation |
| Choose causal paths | Reference the sole path after existing admission; alternative paths remain rejected |
| Perform authority decisions | Reference supplied authority evidence; admission and canonical authority owners remain unchanged |
| Reinterpret operators | Preserve existing admitted set_int contract; no operator table/translation policy added |
| Reorder execution | Preserve directive decision order and path assignment occurrence, including overwritten stores |
| Fabricate semantic events | Generated ranges/provenance are static evidence, never synthetic runtime/TAM events |

Result: PASS for the proposed observational contract. Structural validation and digest comparison are allowed; invoking canonical verification/admission stays with existing owners. Any source/compiler/profile mismatch, missing operation bridge, unknown transformation or need for one of the forbidden behaviors is classified as an architectural gap and fails closed for that mapping. Metadata availability does not activate execution and metadata absence does not broaden or invalidate otherwise valid canonical language semantics. Explicit metadata validation may fail its own gate without rewriting semantic results.

## 9. Exact P12.6-3 gate recommendation

Recommend P12.6-3 — Deterministic Metadata Sidecar Identity and Association Foundation, only after explicit authorization of this proposed contract.

Bound the first implementation to immutable source-snapshot references, reused spans/SourceMap evidence, AIR structural reference validation and an external metadata/plan association. Document the versioned canonical encoding/fingerprint contract and add focused model/association validation tests. Source-map serialization and persistent sidecar fingerprint generation remain for a later named slice; P12.6-3 does not implement a source-map serializer. No compiler/parser/AIR/plan schema change, native emitter/admission change, receipt/result change or debug flags belong in that first slice.

Required focused acceptance: relocated-root identity stability; CRLF/Unicode/EOF offsets; source-content changes with equal AIR; missing snapshots/spans; absolute/traversal/collision rejection; repeated identical stores with distinct locators; stale/mismatched AIR, owner and routing associations; preservation of SourceMap multiplicity and TAM IDs; unchanged native exact-field/admission/rejection contract; no semantic-owner/process dependency introduced by metadata. Reject ambiguous source→operation bridges rather than claiming coverage. Run focused checks before any broader regression required by the actual patch.

Source→native serializer/emitter/provenance integration must be a subsequent explicitly named gate with independently validated operation correspondence. The compiler actions/admission mismatch requires its own compatibility decision; it cannot be folded into P12.6-3. Address mapping, PDB, debugger protocol, breakpoints, stepping, stacks/variables, DAP, P12.7 equivalence and P13 remain excluded. The review establishes ownership and compatibility boundaries; it does not authorize implementation in this session.

## Evidence, verification and remaining limitations

Primary evidence: unchanged P12.6-1 census. Live targeted reads in this session:

- AGENTS.md
- apexforge/air/model.py
- apexforge/language/compiler.py
- apexforge/language/project.py
- apexforge/language/source.py
- apexforge/native_backend/execution_plan_binding.py
- apexforge/native_backend/lowering_input.py
- apexforge/native_backend/native_execution.py
- apexforge/native_backend/native_execution_contract.py
- apexforge/native_backend/result.py
- apexforge/p12_5_native_execution_acceptance_test.py
- apexforge/p12_5_native_profile_contract_test.py
- apexforge/runtime/diagnostics.py
- apexforge/tam/model.py
- apexforge/tam/production.py
- apexforge/tap_check/projection.py
- apexforge/tooling/build_artifact.py
- apexforge/tooling/project_loader.py
- apexforge/tooling/project_manifest.py
- apexforge/workflow/air_runner.py
- docs/p12/P12_4D_COFF_REPRODUCIBILITY_PROVENANCE_POLICY.md
- docs/p12/P12_4G_C_DLL_REPRODUCIBILITY_POLICY.md

Focused native contract/acceptance assertions were inspected, including nonempty-actions rejection, ordered overwrites and Unicode IDs. Git checkpoint, exact tag-object/commit comparisons, ancestry, initial/final worktree inventory, and preservation of census bytes were validated. No tests, builds, native execution or full regression harness ran: this patch is documentation only. The shell helper could not initialize; direct Node filesystem/Git inspection provided the evidence. No production regression pass or new binary/PDB characterization is claimed.

New file: this review only. No frozen file, test assertion, diagnostic behavior, manifest/CLI protocol or receipt/result schema changed. Remaining work: human contract review; authorized foundation gate; producer-owned operation bridge; separately reviewed compiler/native compatibility if end-to-end source execution is wanted. Missing source evidence, revision-scoped operation identities, process-local artifact issuance and absent address mapping remain explicit limitations.

Final git status --short --untracked-files=all:

```text
?? docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
?? docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md
```

Tracked and staged diffs are empty. HEAD and all three recorded freeze references are unchanged. Nothing was staged, committed, tagged or pushed.

P12_6_METADATA_SCOPE_REVIEW=PASS

P12_6_IMPLEMENTATION_STARTED=False
