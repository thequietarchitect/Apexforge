# P11.16A â€” Final Verification Architecture Boundary

## Status

Architecture-only.

P11.16A freezes the verification methodology for the final P11 validation
sequence. It changes no production file and does not yet run the broad
historical regression matrix.

Predecessor:

- terminal P11.15I freeze commit:
  `12f1e568bec83f5d74c661e042f7bcef25f0b5b9`
- annotated predecessor tag:
  `afp-p11-15i-freeze`

## Discovery baseline

The independent P11.16 discovery audit established:

- **150** P11 tags;
- **150/150** tags are ancestors of the terminal P11.15I baseline;
- **116** annotated P11 tags;
- **34** historical lightweight P11 tags;
- **178** P11 smoke tests;
- **146** P11 documents;
- numbered P11 smoke-test phases **1 through 15**;
- **9** SRC-family smoke tests;
- **12** TAM-family smoke tests;
- **305** production Python files, all parse successfully;
- `examples/P11Validation` is currently absent;
- 35 smoke tests reference `P11Validation`;
- 40 smoke tests reference `tempfile`;
- 122 smoke tests reference `subprocess`;
- 5 smoke tests reference Visual Studio;
- 1 smoke test references VSCode.

Historical lightweight tags are retained as history. P11.16 does not rewrite
or re-tag earlier freezes merely to make historical tag style uniform.

## Final-verification principle

P11.16 must not treat every old smoke test as if it were a current semantic
contract.

ApexForge has legitimate later frozen stages that supersede earlier exact file
hashes, exact owner snapshots, and historical environment assumptions. At the
same time, current durable semantics remain binding.

Therefore every P11 regression entry must be classified before broad
execution.

## Verification classes

### 1. `DURABLE_CURRENT`

A test or assertion belongs here when its behavior remains a current semantic
contract at the terminal P11 baseline.

Rules:

- must execute against current HEAD;
- failure blocks P11.16 completion;
- do not weaken the test merely to get green;
- do not reinterpret the semantic owner boundary;
- production repairs are allowed only when the current frozen architecture
  actually violates its durable contract.

### 2. `HISTORICAL_EXACT_FREEZE`

A test or assertion belongs here when it pins an exact historical hash,
historical owner snapshot, historical branch state, or a byte identity that was
legitimately superseded by a later frozen stage.

Rules:

- retain historical test bytes;
- classify the precise supersession reason;
- verify replacement/follow-on freeze ancestry and evidence;
- never mutate current production merely to recreate an obsolete exact hash;
- historical failure is not silently ignoredâ€”it is resolved by explicit
  historical evidence.

### 3. `ENVIRONMENT_FIXTURE_BOUND`

A test belongs here when success depends on a historical fixture or execution
environment not inherently part of the current repository state.

Known example:

```text
examples/P11Validation
```

The directory is currently absent, while 35 historical smoke tests reference
it.

Rules:

- record the exact dependency;
- if prior canonical fixture bytes/evidence exist, P11.16 may reconstruct the
  fixture temporarily for regression execution;
- temporary reconstruction must not become a permanent repository restoration
  merely to make tests green;
- unclassified environment errors block verification until understood.

### 4. `EXTERNAL_TOOLCHAIN_BOUND`

A test belongs here when it requires a separately resolved external toolchain,
IDE integration environment, or subprocess behavior.

Examples include:

- Visual Studio;
- VSCode;
- PowerShell/subprocess integration;
- environment-sensitive packaged-entry behavior.

Rules:

- record the required toolchain/environment;
- execute when the required toolchain is available;
- toolchain unavailability must never be reported as a false pass;
- do not mutate production to simulate an unavailable external toolchain.

## Required matrix coverage

P11.16 must account for **all 178 P11 smoke tests**.

Coverage includes:

1. numbered P11.1 through P11.15 smoke tests;
2. the complete SRC family;
3. the complete TAM family;
4. tooling / CLI / editor compatibility;
5. repository regression surfaces:
   - `apexforge/tests`;
   - `apexforge/regression_harness.py`;
   - `apexforge/tooling/performance_baseline.py`;
6. semantic owner-boundary sentinels.

No smoke test may disappear from the matrix merely because it is awkward,
historical, or environment-sensitive.

## Current SRC family

The final-verification matrix must include:

- `p11_src_a_semantic_decision_source_architecture_audit_smoke_test.py`
- `p11_src_b_immutable_semantic_decision_source_ast_smoke_test.py`
- `p11_src_c_deterministic_semantic_decision_source_parser_smoke_test.py`
- `p11_src_d_semantic_decision_lowering_smoke_test.py`
- `p11_src_e_semantic_decision_source_validation_smoke_test.py`
- `p11_src_f_real_apex_compile_analysis_acceptance_smoke_test.py`
- `p11_src_g_powershell_tooling_compatibility_smoke_test.py`
- `p11_src_g_semantic_decision_project_lsp_compatibility_smoke_test.py`
- `p11_src_h_final_integration_regression_freeze_smoke_test.py`

## Current TAM family

The final-verification matrix must include:

- `p11_tam_a_architecture_traceability_ownership_audit_smoke_test.py`
- `p11_tam_b_minimal_immutable_trace_model_smoke_test.py`
- `p11_tam_c_deterministic_trace_production_foundation_smoke_test.py`
- `p11_tam_d_declaration_identity_ownership_trace_production_smoke_test.py`
- `p11_tam_e_reference_scope_resolution_evidence_trace_production_smoke_test.py`
- `p11_tam_f_type_evidence_trace_production_smoke_test.py`
- `p11_tam_g_authority_evidence_trace_production_smoke_test.py`
- `p11_tam_h_narrative_evidence_trace_production_smoke_test.py`
- `p11_tam_i_token_evidence_trace_production_smoke_test.py`
- `p11_tam_j_final_integration_architecture_audit_smoke_test.py`
- `p11_tam_k_deterministic_whole_map_composition_smoke_test.py`
- `p11_tam_l_final_integration_regression_freeze_smoke_test.py`

## Final-verification ordering

P11.16A freezes this successor sequence:

### P11.16B â€” Matrix Classification and Manifest

Create a deterministic manifest representing all 178 P11 smoke tests, their
verification class, execution requirements, owner/freeze evidence, and
historical/environment notes.

P11.16B is classification/evidence work, not production mutation.

### P11.16C â€” Durable Semantic Execution

Execute the current durable semantic matrix and owner-boundary sentinels.

Any durable failure is blocking.

### P11.16D â€” Historical / Environment / Toolchain Resolution

Resolve historical exact-freeze, missing-fixture, subprocess, IDE, and
environment-sensitive entries with explicit evidence.

No silent skips and no false passes.

### P11.16E â€” Repository-Wide Final Verification

Run the final combined verification surface including repository regression
surfaces, compile/parse checks, tooling compatibility, and no-mutation checks.

### P11.16F â€” Final Freeze

Freeze final P11 verification only after the matrix is fully accounted for and
the repository is clean.

## Production policy

P11.16A introduces no production change.

P11.16 as a verification phase should remain non-production unless final
verification discovers a real current semantic regression. Such a regression
must be repaired under the already-frozen architectural owner, not by
weakening verification.

## Non-goals

P11.16A does not:

- run all 178 smoke tests blindly;
- repair historical exact hashes;
- restore `examples/P11Validation` permanently;
- rewrite lightweight historical tags;
- invent new P11 functionality;
- reopen P11.15 interoperability;
- begin P12 native backend work.

## Successor

The next stage after freezing P11.16A is:

**P11.16B â€” Matrix Classification and Manifest**.