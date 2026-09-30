# P12.6-4 Deterministic Source/AIR/Native Mapping — Review Evidence

Status: ready for human review; no milestone freeze or release declaration.

## Ownership and bounded contract

Canonical AIR remains semantic authority. Compiler/tooling owns immutable observational sidecars. RegistryExecutionPlan remains routing/entry authority. Native admission and lowering remain the unchanged P12.5 bounded profile apexforge.native.win-x64.i64-literal-state-set/v1. No AIR schema changes, PDB/debug flags, debugger protocol, TAM redesign, runtime trace redesign, or profile expansion.

The compiler producer records exact existing SourceMapEntry evidence at state and top-level assignment construction. The opt-in compile_source_with_operation_evidence API returns canonical CompiledSource plus an immutable ledger. It reuses the ordinary compilation path. SourceAIRMapping consumes that ledger, verifies exact canonical AIR transport, and links unique existing SourceMap entries to P12.6-3 typed structural identities and operation IDs. Missing physical spans are explicitly UNMAPPED; missing or ambiguous producer correspondence rejects. Correspondence is never reconstructed from names, literals, types, or causal semantics.

Source identities remain project-relative logical names plus exact governed byte fingerprints and existing character spans. AIR identities remain exact canonical AIR fingerprint, typed structural locator and deterministic occurrence ordinal. Operation ordering is states followed by existing directive/decision/path assignment order; repeated assignments have distinct identities. No Python object identity participates.

Supported source correspondence is a single original, unlinked/untransformed directive, states and top-level path assignments. Nested source evidence is retained in SourceMap but unsupported nested operations receive no invented locator. Other declarations retain location evidence rather than inferred operation correspondence. The producer ledger is trusted local compiler evidence, not a cryptographically authenticated arbitrary external claim.

## Synthetic policy

Source-backed entries retain their exact spans. Compiler-generated principal/authority objects have no owned physical span in mapping lineage; their existing legacy SourceMap positions are referenced only as originating directive evidence. AIRProgram is a generated container and MetadataSidecar is metadata-only. Missing origins remain absent. Existing SourceMap evidence is not rewritten.

## Native correspondence and provenance

The native emitter returns optional side-channel character offsets for each existing state initializer and admitted store. Region ends exclude the newline. Generated C bytes do not change; no comments or markers are added. GeneratedRegion binds operation identity, admitted order and canonical program.c span. NativeSourceMapping binds schema/version, sidecar fingerprint, source correspondence fingerprint (or explicit UNMAPPED_SOURCE), plan association, profile and exact generated-source content fingerprint. Canonical JSON is only a fingerprint preimage; no public persistence/load format is introduced.

Mapping validation reconstructs deterministic observations using the unchanged admission owner and rejects substituted source/AIR/routing/profile/generated-C/regions. MappedNativeArtifact associates the map externally with the existing receipt and executable image fingerprints; canonical artifacts, receipts, dispatch and results are not redesigned. Host paths, build directories, clocks, random data and environmental telemetry do not enter mapping fingerprints. Mapping ends at generated C, not machine addresses.

There is deliberately no claim of an executable ordinary compiler-source-to-native chain: compiler-produced nonempty CausalPath.actions and authority surface still fail bounded admission. Source-to-AIR works on real compiler output; AIR-to-C works on admitted P12.5 fixtures whose absent physical source correspondence is explicit. Metadata does not confer executability.

## Executed validation

Every Python command used C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe (Python 3.9.13), with -B.

- p12_6_4_source_native_mapping_test.py: 11/11 PASS.
- p12_6_3_metadata_identity_association_test.py: 8/8 PASS.
- p12_5_native_profile_contract_test.py: 7/7 PASS.
- unittest discovery of p12_5_native_execution_acceptance_test.py: 20/20 PASS (includes seven imported profile tests).
- source_diagnostics_smoke_test.py: PASS, all seven reported checks.
- p7_function_conditional_smoke_test.py: PASS, all seven reported checks.

No executed test failures; no defect-driven implementation corrections. The interrupted regression batch during server recovery produced no counted result and was rerun. The full historical suite was not run.

Focused negatives cover stale source/AIR/generated C, absent/duplicate producer or operation correspondence, ambiguous SourceMap evidence, overlapping/empty/out-of-range generated regions, wrong AIR locator/native profile/routing association, substituted artifact mapping/receipt binding, path contamination, and requests to infer absent correspondence. Each rejects.

Repeated source construction and emission produce identical SourceMap evidence, operation references, generated bytes/regions, canonical map preimages and fingerprints. The original emitter loaded from the execution-freeze Git reference produces exactly the same C bytes. Live mapped builds retain the same executable image, receipt, output and result as the frozen-emitter fixture and canonical execution oracle. Repeated mapped builds retain image/receipt/output/result determinism.

Compiler ordinary versus observed output equality, interleaved/nested action coverage and explicit action snapshots prove CausalPath.actions are preserved. Native admission continues rejecting nonempty compiler-produced actions. Static mapping audits forbid resolver/type/evaluator/authority/semantic execution calls; dependency traps prove source-map validation does not invoke those engines. Observers record producer structure; they do not resolve, infer, evaluate, choose paths, enforce policy, reinterpret operators, reorder actions or fabricate decisions.

## Checkpoint and next review

HEAD and afp-p12.5-execution-freeze commit: 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

Unchanged freeze references (tag object / commit):

- afp-p12.4-freeze: 7c475986ed3ed1d58cc30148603fbfe8b09529ee / 13f7646f1052746f54f906076d66d29117ee2718.
- afp-p12.5-freeze: 9e2d7a4f57a10e0499d788f8584ace477f624b07 / 542be090e193b3d931d27c08e16de3efd961a01e.
- afp-p12.5-execution-freeze: 6ad3d33601a576c2b42e2fde16cd98c2c61980fd / 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

Recommended P12.6-5: Mapping Provenance and Trace-Retention Contract Review. Review how existing TAM observational evidence and separately owned runtime traces can reference these mappings at artifact/result boundaries; define missing/unsupported retention explicitly. Preserve bounded admission and source coverage limits. Do not assume ordinary compiler output is native-admitted. No PDB, address maps, debugger protocol, semantic expansion or equivalence milestone is implied. P12.6-5 has not begun.

P12_6_SOURCE_TO_AIR_MAPPING=PASS
P12_6_AIR_TO_NATIVE_MAPPING=PASS
P12_6_GENERATED_REGION_IDENTITY=PASS
P12_6_MAPPING_PROVENANCE=PASS
P12_6_MAPPING_DETERMINISM=PASS
P12_6_STALE_MAPPING_FAILS_CLOSED=True
P12_6_MAPPING_SEMANTICALLY_OBSERVATIONAL=True
P12_6_EXECUTION_SEMANTICS_UNCHANGED=True
P12_6_METADATA_DOES_NOT_CHANGE_CAUSAL_ACTIONS=True
P12_6_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_6_NATIVE_PROFILE_EXPANDED=False
P12_6_PDB_ENABLED=False
P12_6_4_READY_FOR_REVIEW=True
