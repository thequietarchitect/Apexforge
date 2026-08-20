# P11-SRC-E - Source Diagnostics and Invalid-Form Rejection

## Status

Source/bridge validation slice following `afp-p11-src-d-freeze`.

P11-SRC-E adds deterministic validation for authored semantic-decision structure and for the integrity of the D bridge. It does not execute or reproduce P11.10 semantic validation.

## Public surface

`apexforge/language/semantic_decision_source_validation.py` exports:

- `SemanticDecisionSourceValidationError`
- `validate_semantic_decision_source_bridge`

The validator accepts one exact `LoweredSemanticDecisionDocument` and returns the exact same object on success.

It performs no transformation.

## Rejection matrix

P11-SRC-E rejects the following source/bridge-invalid states:

1. duplicate decision identities in one semantic-decision document;
2. a decision with no candidates;
3. duplicate candidate identities inside one decision;
4. convergence candidate references present without a convergence policy;
5. a convergence policy present without any convergence candidate references;
6. a convergence candidate object that is not one of the exact candidate objects owned by the decision;
7. incompatibility evidence whose left or right endpoint is not one of the exact candidate objects owned by the decision.

These are source-namespace and bridge-integrity conditions. They are not admissibility, convergence-result, or Paradox Elevation decisions.

## Intentional non-rejections

P11-SRC-E intentionally does not reject or reinterpret:

- an extension/unsupported P11.10 convergence policy identity;
- duplicate authored convergence references;
- explicit-order parameter shapes that P11.10 may later resolve as unresolved;
- self-incompatibility evidence;
- duplicate or incomplete incompatibility evidence;
- a Paradox Elevation request that later proves ineligible;
- absence of condition evidence;
- indeterminate admissibility;
- insufficient admissible convergence cardinality;
- unsupported policy semantics;
- unresolved convergence;
- incomplete information-loss evidence.

Those conditions belong to the already-frozen P11.10 semantic stages or to later evidence supply.

In particular, the frozen P11.10 policy layer deliberately converts malformed/unsupported/insufficient operative convergence inputs into deterministic unresolved results rather than source-syntax failures. E preserves that contract.

## Diagnostic contract

Failures raise `SemanticDecisionSourceValidationError` carrying a canonical `BuildDiagnostic` with:

- severity `error`;
- code `APX-SEMANTIC-DECISION-SOURCE-VALIDATION`;
- stage `compile`;
- the relevant source/bridge span.

Validation is deterministic and reports the first failure in document/source traversal order.

## Exact candidate ownership

D binds authored candidate references to exact frozen P11.10 `CandidateAlternative` objects.

E verifies that convergence and incompatibility relationships continue to point into the exact candidate object set owned by their decision.

This is a bridge-integrity check. It does not compare payload meaning, calculate compatibility, establish admissibility, rank candidates, or infer source references.

## Frozen subsystem boundary

P11-SRC-E does not call or reproduce:

- `evaluate_advanced_condition`;
- `construct_semantic_convergence_set`;
- `apply_semantic_convergence_policy`;
- `assess_paradox_elevation`;
- `elevate_paradox_assessment`;
- `validate_semantic_convergence_resolution`;
- `validate_paradox_elevation_assessment`;
- `validate_elevated_semantic_state`;
- downstream projection;
- reporting;
- runtime execution.

The frozen `apexforge/semantic_decision` package remains unchanged.

## Predecessor compatibility

Unlike the earlier B/C boundary issue, the P11-SRC-D smoke test does not require the future validation module to remain absent. Therefore the D smoke test remains directly runnable as a predecessor regression after E is added.

E additionally checks its own durable D chain by reparsing and relowering source before validation.

## Next slice

P11-SRC-F will consume parser, lowering, and E validation together to provide real `.apex` compile/analysis acceptance for semantic-decision source while preserving the ordinary AIR and narrative source paths.