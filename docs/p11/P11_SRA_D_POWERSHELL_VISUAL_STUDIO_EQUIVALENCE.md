# P11 Supplemental Release Acceptance D - PowerShell / Visual Studio Equivalence

Status: **FROZEN**

Baseline: SRA-C freeze `34ae66b6c2fb8fefa4bfeae9661ec1eac4d6dd84` / `afp-p11-sra-c-visual-studio-experimental-acceptance-freeze`.

## Scope
SRA-D validates PowerShell <-> Visual Studio behavioral and semantic equivalence where the two products expose the same operation. It does not require feature parity and does not add editor features merely to make the surfaces symmetrical.

The governing model is:

```text
CLI CAPABILITY SET != VISUAL STUDIO CAPABILITY SET

SHARED_OPERATION(PS) == SHARED_OPERATION(VS)

CLI-ONLY CANONICAL SEMANTICS
  POWER_SHELL_CANONICAL_RESULT = PASS
  VS_COMPETING_IMPLEMENTATION  = ABSENT / PASS
  DIRECT_VS_RESULT_COMPARISON  = NOT_APPLICABLE_TO_CURRENT_SURFACE
```

The IDE must never become a second semantics implementation. The canonical Visual Studio entry point remains `.sln`; `.slnx` is not qualified by this acceptance.

## Acceptance ledger
| Gate | Result |
| --- | --- |
| D0 successor/control point | PASS |
| D1 fixture/capability/owner census | PASS |
| D2 live environment identity | PASS |
| D3 CLI/LSP diagnostics equivalence | PASS |
| D4 declaration/resolution equivalence | PASS |
| D5 broader semantic/result equivalence | PASS |
| D5A semantic-decision bridge | PASS |
| D5B narrative | PASS |
| D5C convergence / Paradox | PASS |
| D5D TAM | PASS |
| D6 negative/divergence | PASS |
| D7 restart/determinism | PASS |
| D8A governance/control point | PASS |
| D8 final regression | PASS |

Freeze authorization is **true**. D8 final regression and governance review are closed.

## Shared-surface equivalence
Diagnostics: valid source is accepted by CLI and produces zero LSP diagnostics; malformed source produces canonical `APX-PARSE-003` equivalently and deterministically.

Definition/resolution: `directive:Observer` resolves canonically to `src/observer.apex` and projects to the same editor declaration. Missing/hidden targets remain unresolved and project to no editor location. Multiple visible candidates remain ambiguous and project to no editor location. The editor does not select a hidden winner.

Fresh-process repetition reproduced the positive, unresolved, ambiguous, and diagnostic acceptance snapshots deterministically.

## CLI-only canonical semantics
Semantic-decision, narrative, convergence/Paradox, and TAM current semantics passed their canonical PowerShell-side acceptance. Visual Studio contains no competing implementation for these CLI-only semantic surfaces; direct Visual Studio result comparison is therefore not applicable to the current surface.

## Historical blockers and governance classifications
Historical packaging/path/branch/fixture contracts are retained as historical classifications rather than reclassified as current semantic regressions. `examples/P11Validation` is not to be permanently or approximately reconstructed merely to green a historical test.

## Carried review item
SRA-C3A workflow `invoke Main` definition resolution remains `REVIEW_REQUIRED`; a current regression has not been established. The item is carried explicitly rather than silently converted to PASS.

## Future-scope boundary
SRA-E optimization acceptance remains queued. P12 is not entered. Polyplane expansion and the Observation, Governance, Simulation, Optimization, Distribution, Temporal, and Knowledge planes remain deferred post-release work and must not enter SRA-D.

## SRA-D freeze
Annotated freeze tag: `afp-p11-sra-d-powershell-visual-studio-equivalence-freeze`.

No production semantic mutation was introduced by SRA-D. The SRA-D freeze is **authorized** after final D8 regression and governance review passed.
