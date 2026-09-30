# P12.6-3 — Immutable Metadata Sidecar Identity and Association Foundation

Implementation scope: immutable values and fail-closed structural/provenance validation only. Executed validation supports readiness for human review; evidence and retained invocation failures are recorded below. P12.6-4 has not started.

Baseline: HEAD = afp-p12.5-execution-freeze^{commit} = 6e71a1afae36c3b4984e949c707d3e6fae6cc269. P12.4, reconstruction P12.5 and execution P12.5 tag objects/commits match the P12.6-1/2 records. The controlling documents are preserved byte-for-byte; their SHA-256 values at entry are:

- P12.6-1: 496eee7b666586074869b69c27e91363f9d141692c35b460341581eda38fb1b5
- P12.6-2: 357a76cd34524bb35290bbb9b1dc4aaf5a3a1214c267c781fe67e25369f5d353

## Contract and implementation

New compiler/tooling-owned module: apexforge/tooling/debug_metadata.py. No import/re-export is added to an existing owner. Existing consumers do not automatically load or activate metadata. This opt-in foundation does not change AIR, VerifiedAIRProgram, RegistryExecutionPlan, NativeProfileAdmission, native receipts, result schemas, compiler code, admission or emission.

Frozen SourceIdentity holds a portable project-relative slash-separated logical name and uppercase SHA-256 of exact governed UTF-8 bytes. Its construction takes no filesystem root, cwd, physical path, timestamp, random ID or environment. It rejects drive/absolute/UNC/backslash/traversal/dot/empty/control-character identities rather than normalizing them. Names retain spelling; duplicate names under casefold are rejected within a sidecar. UTF-8 content is not normalized for BOM, Unicode, newline or whitespace. A logical name's governance is the caller's responsibility: a relative name alone cannot prove that a caller did not choose a temporary/random label. Source content must be supplied again at validation; stale bytes are rejected. Existing SourcePosition/SourceSpan/SourceText provide character-offset/line/column consistency, including Unicode, CRLF and empty EOF spans.

StateLocator identifies a state-initialization occurrence and exact state ID. AssignmentLocator identifies directive occurrence/ID, decision reference occurrence/ID, path occurrence/ID and assignment occurrence. AIRMetadataIdentity binds either locator to the exact canonical AIR transport fingerprint through the existing build_verified_air_lowering_input delegate. No independent AIR serialization/hash, object identity or source-name resolver is introduced. Exact canonical references are checked for uniqueness/existence and indices for bounds. Alternative path identities can be structurally referred to, but no path is selected or admitted by this metadata layer.

OperationReference carries explicit ordinal and AIRMetadataIdentity; operation_id is a domain-separated af-meta-op SHA-256 derived solely from those values. Repeated equal assignments have distinct occurrence locators. Equivalent AIR/structure/order yields identical operation identities. Different AIR revisions yield different references; identities are not promised stable across arbitrary edits. Operation IDs contain no source paths, generated symbols, host state or execution instructions.

MetadataSidecar retains frozen source identities, existing SourceMap evidence, AIR digest and ordered operation references. EvidenceReference is an optional explicit producer-supplied occurrence reference (operation ID, source occurrence, existing SourceMap entry occurrence). It validates reference integrity only: no source→AIR bridge is derived, inferred or authenticated by matching values or entry order. The source-map wire representation, producer correspondence algorithm, generated-source ranges and native mapping implementation remain undecided in this gate. A supplied relationship is an assertion by its compiler/tooling producer, not proof manufactured by metadata.

Sources must be in deterministic logical-name order; evidence references must be in deterministic tuple order. Existing SourceMap ordering and multiplicity are retained. Operations must have contiguous explicit ordinals, unique operation IDs and unique structural identities. An external required-operation tuple is mandatory when validating: a partial or reordered sidecar cannot claim that expected coverage. The tuple is supplied by the producer/provenance authority; metadata does not discover an execution schedule or infer required coverage. An empty required tuple explicitly requests no operation coverage, not full-program coverage.

MetadataAssociation is separate from RegistryExecutionPlan. It binds sidecar digest, canonical AIR digest, existing routing digest, exact entry and sorted owner-program content digests. Association construction uses the existing plan-binding delegate and validates exact entry existence. Validation reconstructs expected provenance from caller-governed current inputs and rejects mismatches rather than repairing metadata. Owner hashes supplement the existing routing digest without rewriting its established preimage. Associations are local provenance checks, not signatures, an independent AIR verifier or native admission tickets.

All model containers require exact immutable tuples/value classes. In-memory canonical tuple preimages and canonical JSON hashing are used only to test/fingerprint identities. There is no file writer, reader, persistent source-map format or serialized artifact requirement. Fingerprints are domain/schema separated and include governed source hashes, logical names, coordinates, exact compiler entry fields/occurrences, AIR references, operation order, explicit evidence references and association provenance as applicable. Whole-source bytes remain governed by their content hash; source bytes are not embedded in the sidecar.

Machine paths and controls are rejected in source identities and compiler evidence fields where applicable. No environment, process ID, time, ticket, temp root, tool installation path, raw log or random generator is accessed. Exact AIR IDs retain canonical semantic spelling; they are not renamed or treated as filesystem paths. No user-facing presentation category or arbitrary producer field is added.

## Compatibility and no-second-semantics boundary

Metadata only observes canonically verified AIR supplied by an existing owner. It does not resolve source identifiers, infer types, evaluate expressions, choose causal alternatives, execute authority policy, interpret operators, reorder actions or create semantic events. Digesting canonical transport is not executing semantics. The external required-operation sequence preserves producer-specified occurrence order; the sidecar never sorts it into a new schedule.

Neither compiler-produced CausalPath.actions nor any other AIR field is assigned/replaced by implementation code. The focused preservation test compiles a real source with repeated assignments, captures nonempty actions and canonical AIR bytes, validates metadata/plan association, and checks the same actions object and unchanged canonical AIR transport. It then requires existing native admission to continue rejecting that compiler program. The action-population/native-admission incompatibility remains a separate limitation, not solved or waived here.

Native-operation references are mapping identities only. This module does not import native profile admission or execution, construct an admitted program, emit C, rename C symbols, enable PDBs, instrument traces, invoke TAM adapters or create a substitute TAM. Existing TAM and runtime trace ownership remains untouched. No source→native/address correspondence or end-to-end source-mapped native execution is claimed.

## Focused validation and test policy

New test: apexforge/p12_6_3_metadata_identity_association_test.py. Coverage includes equivalent input identities; repeated construction fingerprints; content changes; canonical AIR changes and reordering; repeated operations; source evidence multiplicity; stale source/AIR; absent or ambiguous canonical locators; invalid/bool/negative indices; duplicate/missing operation references; malformed character spans; unsupported inference requests; mismatched sidecar/routing/entry/owner associations; absolute/host-path contamination; frozen values; real compiler actions preservation; static import/call audit and executable traps against compiler/verifier/runtime/process invocation during metadata validation.

Commands executed from repository root with the exact interpreter recorded below:

- Python -B apexforge/p12_6_3_metadata_identity_association_test.py
- Python -B apexforge/p12_5_native_profile_contract_test.py
- Python -B -m unittest discover -s apexforge -p p12_5_native_execution_acceptance_test.py -v

The last command imports the existing acceptance suite without executing its __main__ evidence writer, preserving frozen RCV-54 JSON. It ran after the focused foundation and profile contracts passed. No full historical regression harness is planned unless a relevant failure requires it.

Interpreter discovery attempts: py reports no installed Pythons; py -3.9 reports Python 3.9 not found; python/python3 are absent from PATH. The standard shell helper also fails initialization, so repository reads/writes/Git checks use the Node tool. The user has been asked for the available runner. No test is recorded as passing solely from static inspection.

## Remaining gate

Focused tests and relevant P12.5 execution checks passed. No code correction was necessary. Invocation/environment failures are retained below; no frozen assertion was weakened. Diagnostics currently fail closed with ValueError/TypeError/UTF-8 decode errors; no canonical language diagnostic or runtime result is rewritten.

Recommend P12.6-4 — Source→AIR Sidecar Representation and Native Operation Mapping Contract/Implementation Review as the first gate authorized to decide actual producer correspondence representation and native-operation mapping implementation. It must retain P12.5 admission and classify the compiler actions mismatch separately. Persistent serialization, native integration, coverage/authenticity of producer bridges and retention policy need their own explicitly scoped decisions. PDBs, debugger protocols, breakpoints/stepping/stack/variable inspection, DAP, P12.7 and P13 remain excluded.

New files in this gate: tooling/debug_metadata.py, p12_6_3_metadata_identity_association_test.py, and this document. Earlier P12.6 documents are unchanged; no staging, commit, tag or push is authorized or performed.

## Historical session status (before interpreter authorization)

No tests executed. P12.6-3 terminal evidence remains PENDING_TEST_EXECUTION; no gate-completion claim is made. The source/action/native compatibility checks must run before PASS markers can be issued.

Exact Git status --short --untracked-files=all:

```text
?? apexforge/p12_6_3_metadata_identity_association_test.py
?? apexforge/tooling/debug_metadata.py
?? docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
?? docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md
?? docs/p12/P12_6_3_IMMUTABLE_METADATA_IDENTITY_ASSOCIATION_FOUNDATION.md
```

HEAD/tag objects/peeled commits and P12.6-1/2 hashes were checked unchanged. Tracked and staged diffs are empty.

## Executed validation evidence

Exact interpreter: `C:\Users\corte\AppData\Local\Programs\Python\Python39\python.exe`. `--version` returned `Python 3.9.13` (exit 0). Every Python validation command in this resumption used that interpreter with `-B`; no launcher or substitute interpreter ran the tests.

| Command arguments | Passed | Failures | Errors | Exit |
| --- | ---: | ---: | ---: | ---: |
| -B apexforge/p12_6_3_metadata_identity_association_test.py | 8 | 0 | 0 | 0 |
| -B apexforge/p12_5_native_profile_contract_test.py | 7 | 0 | 0 | 0 |
| -B -m unittest discover -s apexforge -p p12_5_native_execution_acceptance_test.py -v | 20 | 0 | 0 | 0 |

Current resumption total: 35 passed test executions, comprising 28 unique tests (8 metadata, 7 profile, 13 native). Discovery repeats the 7 imported profile tests. The pre-interruption metadata/profile runs also passed 8/7 respectively; they are not included in the current 35 count. No full historical suite ran. Native discovery avoided the frozen acceptance JSON writer, and no tracked file changed. Temporary native builds were cleaned by the existing suite.

### Failure classifications retained

- TEST_INVOCATION_DEFECT: the initial direct Node invocation over-escaped interpreter path separators. Correcting invocation spelling changed no implementation.
- ENVIRONMENTAL_BLOCKER: corrected direct invocation could not launch under the sandbox; stat of the explicitly authorized path reported EPERM. Standard sandbox shell setup also failed with helper_unknown_error. Approved elevated execution of the exact interpreter resolved access and confirmed Python 3.9.13.
- No executable test failures occurred. No IMPLEMENTATION_DEFECT, TEST_FIXTURE_DEFECT, HISTORICAL_CONTRACT_BLOCKER, GOVERNANCE_CONFLICT or UNSUPPORTED_TARGET was established.

### Compatibility and audit evidence

The executed real-compiler fixture test retained the exact nonempty actions tuple and byte-identical canonical AIR transport after metadata construction/association validation. It then required NativeExecutionError from existing native admission. Metadata did not remove, rewrite, suppress or normalize actions. The separate P12.5 profile suite retained nonempty-actions rejection and the broader supported/rejected admission matrix.

The executed metadata no-second-semantics test performed a static import/call audit and trapped compiler, verifier, runtime and subprocess invocation during metadata validation. Identity/association checks passed without activating those owners. Metadata remains opt-in in the compiler/tooling layer and does not change native execution.

Real native acceptance passed canonical-runtime final-state comparison, ordered overwrite/source checks, signed-I64 minimum/maximum and Unicode/maximum-profile cases, exact receipt/input/output provenance, changed-input rejection, artifact substitution/issuance checks, locking, failure handling and no-fallback assertions. Repeated native image bytes, receipts, raw outputs and canonical results were identical (P12_5_NATIVE_REPEATED_IMAGE_RECEIPT_OUTPUT_RESULT=PASS). This establishes compatibility for the existing bounded profile and inspected test cases, not whole-language equivalence.

Direct inspection confirmed no tracked AIR schema, plan schema, native profile, compiler action, receipt/result or emitter change. Existing options retain /Od and /Brepro; no PDB/debug switches were added. P12.6-1/2 hashes match the preserved hashes above. All three tag objects/peeled commits and ancestry match the baseline table in P12.6-1/2; HEAD remains 6e71a1afae36c3b4984e949c707d3e6fae6cc269.

### Review evidence markers

```text
P12_6_METADATA_OWNER=COMPILER_TOOLING_SIDECAR
P12_6_SOURCE_IDENTITY=PASS
P12_6_AIR_METADATA_IDENTITY=PASS
P12_6_OPERATION_IDENTITY=PASS
P12_6_ASSOCIATION_VALIDATION=PASS
P12_6_METADATA_DETERMINISM=PASS
P12_6_STALE_METADATA_FAILS_CLOSED=True
P12_6_METADATA_DOES_NOT_CHANGE_CAUSAL_ACTIONS=True
P12_6_NO_SECOND_SEMANTIC_IMPLEMENTATION=True
P12_6_AIR_SCHEMA_CHANGED=False
P12_6_NATIVE_PROFILE_EXPANDED=False
P12_6_PDB_ENABLED=False
P12_6_3_READY_FOR_REVIEW=True
```

Readiness is for human review only; it does not declare a milestone complete, frozen or released. P12.6-4 remains recommended but has not begun. No staging, commit, tag or push occurred.

Final exact Git status --short --untracked-files=all:

```text
?? apexforge/p12_6_3_metadata_identity_association_test.py
?? apexforge/tooling/debug_metadata.py
?? docs/p12/P12_6_1_DEBUG_METADATA_CAPABILITY_CENSUS.md
?? docs/p12/P12_6_2_BOUNDED_DEBUG_METADATA_SCOPE_AND_COMPATIBILITY_REVIEW.md
?? docs/p12/P12_6_3_IMMUTABLE_METADATA_IDENTITY_ASSOCIATION_FOUNDATION.md
```
