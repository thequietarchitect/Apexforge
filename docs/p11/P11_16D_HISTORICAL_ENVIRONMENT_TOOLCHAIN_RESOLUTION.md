# P11.16D â€” Historical / Environment / Toolchain Resolution

## Status

P11.16D resolves the **130 non-durable** rows that remain after the frozen
P11.16C correction overlay. This stage is verification/evidence only and
introduces no production change.

Baseline:

- P11.16C freeze: `715d41c733674b1b8681b0d3eb27b9143181bce7`
- P11.16C tag: `afp-p11-16c-freeze`

## Corrected matrix

- `DURABLE_CURRENT`: **48** â€” completed in P11.16C
- `HISTORICAL_EXACT_FREEZE`: **82**
- `ENVIRONMENT_FIXTURE_BOUND`: **32**
- `EXTERNAL_TOOLCHAIN_BOUND`: **16**
- total: **178**
- P11.16D non-durable surface: **130**

## Historical resolution

All **82 historical rows** have an exact test-blob match on a reachable
**annotated P11 freeze tag**.

- exact annotated anchors: **82**
- lightweight-only anchors: **0**
- unanchored historical rows: **0**

## Environment resolution

The two packaged-entry rows are environment-bound. Their direct CLI paths
succeed while the historical packaged `tooling.cli:main` subprocess is unable
to import `tooling` from that execution environment.

`examples/P11Validation` is required by **35 rows**:

- 30 `ENVIRONMENT_FIXTURE_BOUND`
- 5 `EXTERNAL_TOOLCHAIN_BOUND`

The fixture is absent from the worktree and could not be recovered from
current Git refs, reflog-reachable history, or unreachable/dangling commits.

Its canonical resolution is:

`HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE`

P11.16D does **not** fabricate or restore that fixture.

## External toolchain resolution

Windows PowerShell, Visual Studio Code, Visual Studio, `devenv.exe`, and
MSBuild are installed and resolvable.

Two external rows execute successfully under the current environment:
`p11_3d_canonical_declaration_ownership_smoke_test.py` and
`p11_src_g_powershell_tooling_compatibility_smoke_test.py`.

The eight P11.4 Visual Studio rows reach the T5.2 source-integrity audit. The
five guarded C# classification files have canonical committed Git blobs that
match the exact expected T5.2 hashes. Their current working-tree byte
difference is line-ending representation only; LF normalization reproduces
the canonical hashes.

The five external P11.5 rows also depend on the canonically unavailable
`P11Validation` fixture.

TAM-I retains external-toolchain classification while its stage-relative
current mismatch is resolved through exact annotated historical freeze
evidence.

## Canonical resolution codes

- `EXACT_ANNOTATED_FREEZE_BLOB_ANCHOR`: **82**
- `PACKAGED_ENTRY_ENVIRONMENT_BOUND`: **2**
- `P11VALIDATION_HISTORICALLY_REQUIRED_CANONICALLY_UNAVAILABLE`: **30**
- `TOOLCHAIN_AVAILABLE_CURRENT_PASS`: **2**
- `VISUAL_STUDIO_AVAILABLE_CANONICAL_SOURCE_VALID_WORKTREE_LINE_ENDING_BOUND`: **8**
- `TOOLCHAIN_AVAILABLE_P11VALIDATION_CANONICALLY_UNAVAILABLE`: **5**
- `TOOLCHAINS_AVAILABLE_HISTORICAL_EXACT_FREEZE_SUPERSESSION`: **1**

Total: **130**

## Mutation boundary

- production mutation: **none**
- permanent fixture restoration: **none**
- frozen P11.16B manifest mutation: **none**
- frozen P11.16C correction mutation: **none**

## Successor

**P11.16E â€” Repository-Wide Final Verification**
