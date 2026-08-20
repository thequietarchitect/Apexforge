# P11-SRC-D - Semantic Decision Source Lowering

## Status

Production lowering/adaptation slice following `afp-p11-src-c-freeze`.

P11-SRC-D translates the immutable P11-SRC-B/C source representation into passive inputs owned by the already-frozen P11.10 semantic-decision subsystem. It does not execute P11.10 evaluation, convergence, Paradox Elevation, validation, projection, or runtime behavior.

## Public lowering surface

`apexforge/language/semantic_decision_lowering.py` exports:

- `LoweredSemanticDecisionCandidate`
- `LoweredSemanticDecisionDeclaration`
- `LoweredSemanticDecisionDocument`
- `SemanticDecisionSourceLoweringError`
- `lower_semantic_decision_source`

The three lowered records are immutable bridge aggregates. They preserve source grouping and exact source spans while carrying exact P11.10-owned passive objects.

## P11.10 object reuse

SRC-D directly constructs the existing frozen P11.10 types:

- `CandidateAlternative`
- `AdvancedCondition`
- `ConvergencePolicy`
- `ParadoxIncompatibilityEvidence`

SRC-D does not define substitutes for these objects.

P11.10 deliberately leaves `AdvancedCondition.condition_kind` open and gives condition kinds no executable meaning at the passive model layer. SRC-D therefore records authored condition forms as:

- `source.identifier`
- `source.string`
- `source.boolean`
- `source.expression`

The authored scalar text is stored as the `AdvancedCondition.payload`. No condition is evaluated by lowering.

## Candidate lowering

Each authored candidate becomes one exact P11.10 `CandidateAlternative`.

A candidate with an authored `when` clause also receives one passive `AdvancedCondition` in its bridge record.

A candidate without `when` has `condition is None`. SRC-D does not invent an unconditional-admissibility evaluation.

## Source reference binding

`incompatible` and `converge` source references are resolved against candidates declared in the same source decision.

A reference must resolve to exactly one candidate. Unknown or ambiguous source references raise `SemanticDecisionSourceLoweringError`.

This is source binding required to construct object identity relationships. It is not P11.10 convergence, collision, or closure validation.

## Convergence policy adaptation

An authored convergence policy becomes the existing P11.10 `ConvergencePolicy`.

For the frozen P11.10 policies:

- `select.explicit-order`
- `rank.explicit-order`

SRC-D maps the authored convergence candidate order to the exact P11.10 parameter shape:

`(("order", (<candidate identities in authored order>)),)`

This is required by the frozen P11.10 explicit-order contract.

For `compose.all-admissible`, SRC-D supplies no policy parameters because the frozen P11.10 composition contract rejects parameters. The bridge separately preserves the authored convergence candidate tuple and its encounter order.

Unsupported/extension policy identities remain representable as passive P11.10 `ConvergencePolicy` values with no invented parameters. SRC-D does not decide their semantics.

## Incompatibility lowering

Each explicit source statement:

`incompatible LEFT, RIGHT`

becomes one P11.10 `ParadoxIncompatibilityEvidence` whose endpoints are the exact resolved `CandidateAlternative` objects and whose `materially_incompatible` value is `True`.

This does not infer incompatibility from payloads or identity spelling. The source statement itself is the explicit authored incompatibility assertion.

SRC-D does not check whether incompatibility evidence is complete for a later Paradox Elevation assessment. That remains P11.10 ownership.

## Paradox Elevation source preservation

The presence of `paradox elevate` is preserved as `paradox_requested=True`.

Its optional `when` and `requires` clauses are lowered only to passive `AdvancedCondition` records.

SRC-D does not convert `requires information_loss` into `ParadoxElevationEvidence.reduction_requires_information_loss=True`. The authored requirement is not itself proof that reduction actually requires information loss.

A later analysis/execution adapter must supply explicit evidence and an existing `SemanticConvergenceResolution` before P11.10 may construct `ParadoxElevationEvidence` and assess eligibility.

## Provenance

Each P11.10 object created by SRC-D receives deterministic provenance derived from the corresponding source span.

Bridge aggregates also retain exact `SourceSpan` values.

Provenance is trace evidence only. It is not admissibility, precedence, compatibility, truth, or authority.

## Diagnostic contract

Unrepresentable source-to-P11.10 bridge states raise `SemanticDecisionSourceLoweringError` with:

- severity `error`
- code `APX-SEMANTIC-DECISION-LOWERING`
- stage `compile`
- the exact relevant source span

SRC-D currently diagnoses unknown/ambiguous candidate references and P11.10-unrepresentable empty/whitespace policy identity text.

## Predecessor compatibility

The frozen P11-SRC-C smoke test intentionally asserts that semantic-decision lowering does not yet exist, so that absence assertion is a C stage-boundary proof rather than a forward-compatible D regression.

P11-SRC-D leaves the frozen C test unchanged and directly re-verifies C's durable parser capabilities: source recognition, deterministic repeat parsing, decision ordering, candidate ordering, convergence-reference ordering, and immutable source structure.

## Deliberate non-ownership

P11-SRC-D does not call or reproduce:

- `evaluate_advanced_condition`
- `construct_semantic_convergence_set`
- `apply_semantic_convergence_policy`
- `assess_paradox_elevation`
- `elevate_paradox_assessment`
- semantic-decision validation
- downstream projection
- reporting
- runtime execution

It also does not modify the frozen `apexforge/semantic_decision` package.

## Next slice

P11-SRC-E will begin from the P11-SRC-D freeze and own source diagnostics plus invalid-form rejection at the source bridge boundary. It must consume the D bridge contract and must not acquire P11.10 semantic execution authority.