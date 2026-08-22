# P11.16B â€” Final Verification Matrix Classification

## Status

Classification / manifest stage only. No production file is modified.

P11.16B classifies the exact **178 pre-P11.16 P11 smoke tests** captured at
terminal P11.15I commit:

`12f1e568bec83f5d74c661e042f7bcef25f0b5b9`

The governing P11.16A architecture freeze is:

`56286b04905a063988d325c5e699c268cdc835a4`

## Matrix arithmetic

- numbered P11.1-P11.15 tests: **157**
- SRC tests: **9**
- TAM tests: **12**
- total: **178**

## Primary-class counts

- `DURABLE_CURRENT`: **54**
- `HISTORICAL_EXACT_FREEZE`: **78**
- `ENVIRONMENT_FIXTURE_BOUND`: **30**
- `EXTERNAL_TOOLCHAIN_BOUND`: **16**

Every entry has exactly one primary class.

## Orthogonal risk/evidence flags

Primary classification does not erase other execution facts. Each manifest
entry separately records:

- `requires_p11validation`
- `uses_tempfile`
- `uses_subprocess`
- `explicit_visual_studio`
- `explicit_vscode`
- `explicit_powershell_toolchain`
- `exact_hash_evidence`
- `git_evidence`
- `freeze_evidence`

Generic `subprocess` use does **not** by itself imply external-toolchain
classification.

## Classification precedence

1. `EXTERNAL_TOOLCHAIN_BOUND`
2. `ENVIRONMENT_FIXTURE_BOUND`
3. `HISTORICAL_EXACT_FREEZE`
4. `DURABLE_CURRENT`

Explicit external-toolchain identity means Visual Studio, VSCode, or the named
PowerShell tooling-compatibility test.

Any test that requires `examples/P11Validation` is primarily
`ENVIRONMENT_FIXTURE_BOUND`.

A test is primarily `HISTORICAL_EXACT_FREEZE` when static source evidence shows
freeze/frozen evidence plus exact-hash or Git evidence, or exact-hash evidence
plus Git evidence.

Tests without stronger non-durable evidence are `DURABLE_CURRENT`.

## Execution routing

- `DURABLE_CURRENT` -> **P11.16C**
- all other primary classes -> **P11.16D**

## Risk census

```text
exact_hash_evidence=103
explicit_powershell_toolchain=1
explicit_visual_studio=15
explicit_vscode=5
freeze_evidence=161
git_evidence=118
requires_p11validation=35
uses_subprocess=122
uses_tempfile=40
```

## Canonical manifest

Machine-readable manifest:

`docs/p11/P11_16B_FINAL_VERIFICATION_MATRIX_MANIFEST.json`

For every row it records path, family, phase, primary class, reason codes,
execution stage, baseline source SHA256, baseline Git blob OID, and orthogonal
risk/evidence flags.

## Non-goals

P11.16B does not execute the matrix, mutate production, weaken historical
tests, permanently restore `examples/P11Validation`, or begin P12.

## Successor

**P11.16C â€” Durable Semantic Execution**
