# P11.10G - Validation, Collision, Closure, Provenance, and Extension Contracts

## Status

P11.10G is an additive validation slice based exactly on `afp-p11.10f-freeze`.

It validates the complete frozen P11.10B-F semantic-decision product family without modifying or replacing B-F semantic ownership. It introduces layered immutable receipts for ordinary semantic convergence, Paradox Elevation assessment, and elevated semantic state.

## Ownership

P11.10G owns:

- cross-record structural validation over frozen B-F products;
- collision and exact-object closure checks;
- provenance integrity and deterministic lineage checks;
- extension-identifier declaration, collision, and closure;
- E policy/result consistency validation;
- F assessment/result consistency validation;
- elevated semantic-state closure validation;
- passive immutable validation receipts.

P11.10G does not evaluate new condition semantics, construct convergence sets, define new convergence policies, select/rank/compose candidates, invent Paradox Elevation eligibility, execute runtime behavior, grant authority, resolve governance conflict, recompute Quad-Vector results, transform AETHER-AIR, lower backend state, report, or mutate source products.

## Layered validation receipts

P11.10G follows the layered receipt precedent used by the frozen P11.8 and P11.9 validation systems.

It exports:

- `SemanticDecisionValidationReceipt`
- `ParadoxElevationValidationReceipt`
- `ElevatedSemanticStateValidationReceipt`
- `validate_semantic_convergence_resolution`
- `validate_paradox_elevation_assessment`
- `validate_elevated_semantic_state`

A Paradox validation receipt preserves the exact ordinary semantic-decision receipt it depends on.

An elevated-state validation receipt preserves the exact Paradox assessment receipt it depends on.

G does not flatten the complete B-F graph into one monolithic receipt.

## SemanticDecisionValidationReceipt

Exact fields:

- `resolution`
- `extension_admissibility_state_ids`
- `extension_outcome_kind_ids`
- `extension_policy_ids`
- `provenance`
- `checks`

The receipt preserves the exact validated `SemanticConvergenceResolution`.

Extension identifier tuples preserve caller declaration order.

Receipt provenance is the exact validated E resolution provenance.

Receipts are passive observations and never become execution or semantic precedence.

## Extension identifier contract

The ordinary validator accepts keyword-only declaration tuples:

- `extension_admissibility_state_ids`
- `extension_outcome_kind_ids`
- `extension_policy_ids`

Each must be an exact tuple of unique, non-empty, trimmed strings.

An extension identifier may not collide with its corresponding frozen core taxonomy.

The core taxonomies remain:

Admissibility:
- `admissible`
- `inadmissible`
- `indeterminate`

Outcome:
- `selected`
- `composed`
- `unresolved`
- `paradox.elevation_candidate`

Operative E policy:
- `select.explicit-order`
- `compose.all-admissible`
- `rank.explicit-order`

Declaring an extension does not grant executable or operative semantics.

An extension convergence policy remains subject to frozen E behavior. Under frozen E, an unsupported policy resolves deterministically to `unresolved`; G validates that result rather than inventing extension execution.

A declared extension outcome kind does not authorize a manually fabricated E result that disagrees with frozen E policy application.

## Condition and evidence closure

Every `ConditionEvidence` reachable through a validated resolution must reference the exact `AdvancedCondition` held by its `AdvancedConditionEvaluation`.

Within one evidence record, fact keys must be unique.

Duplicate evidence coordinates inside one evaluation are rejected. A coordinate is the exact `(result, facts, provenance)` content under the already-closed exact condition.

Every evaluation state identifier must be either a frozen core admissibility identifier or an explicitly declared extension identifier.

For a frozen core state identifier, the stored state must agree with the frozen P11.10C evaluator over the exact stored condition and evidence.

G does not interpret extension-state semantics.

## Candidate collision and convergence closure

Candidate identities within one `SemanticConvergenceSet.candidates` tuple must be unique.

The same exact `EvaluatedCandidate` object may not appear twice.

Each evaluated candidate's condition/evidence chain must pass G validation.

`SemanticConvergenceSet.members` must be exactly the existing candidate bindings whose evaluation `state_id == "admissible"`, in candidate encounter order.

G does not reinterpret custom extension states as admissible.

The convergence-set provenance must equal the frozen D aggregation:

1. policy provenance;
2. for each candidate binding in encounter order:
   - candidate provenance;
   - evaluation provenance.

## Policy integrity

Policy IDs must be core or explicitly declared extension IDs.

Policy parameter keys must be unique.

G does not interpret a declared extension policy beyond the semantics already supplied by frozen E.

## Ranking and outcome closure

Every ranked candidate must be one of the exact D convergence members.

A ranking may not repeat a candidate or rank.

A non-empty ranking must use consecutive ranks beginning at 1.

Every outcome alternative must be one of the exact D convergence-member candidate objects.

An outcome may not repeat the same exact candidate.

Outcome kind IDs must be core or explicitly declared extension IDs.

## Policy/result consistency

G recomputes the expected frozen E resolution from the exact supplied `SemanticConvergenceSet` by calling `apply_semantic_convergence_policy`.

The validated resolution must agree with frozen E on:

- rank values;
- exact ranked candidate objects;
- outcome kind;
- exact outcome alternative objects;
- outcome payload;
- outcome provenance;
- resolution provenance.

This is validation only. G does not acquire E's policy ownership.

A zero- or one-member convergence set may therefore validate when frozen E correctly produces its deterministic unresolved fallback.

G rejects a zero/one-member product only when its claimed E result disagrees with frozen E semantics.

## Provenance integrity

Every local provenance tuple validated by G remains exact, immutable, encounter ordered, and free of duplicate entries.

C evaluation provenance must equal condition provenance plus evidence provenance in encounter order.

D convergence-set provenance must equal the frozen D aggregation.

E resolution and outcome provenance must agree with frozen E.

G never sorts, deduplicates, fabricates, ranks, or interprets provenance.

## ParadoxElevationValidationReceipt

Exact fields:

- `assessment`
- `resolution_receipt`
- `provenance`
- `checks`

`validate_paradox_elevation_assessment` first validates the exact E resolution contained by `assessment.evidence`.

It then validates the explicit F incompatibility-evidence graph.

Every incompatibility endpoint must be one of the exact E outcome alternatives.

Self-pairs are rejected.

Duplicate unordered incompatibility pairs are rejected.

All Paradox evidence provenance must pass provenance integrity.

Finally, G calls frozen `assess_paradox_elevation` over the exact supplied evidence and requires the stored assessment to agree with F on:

- `eligible`;
- presence or absence of candidate outcome;
- candidate outcome kind;
- exact candidate outcome alternatives;
- candidate outcome payload;
- candidate outcome provenance;
- assessment provenance.

G does not change an ineligible assessment into an eligible assessment.

A structurally valid ineligible F assessment remains a valid product.

## ElevatedSemanticStateValidationReceipt

Exact fields:

- `state`
- `assessment_receipt`
- `provenance`
- `checks`

`validate_elevated_semantic_state` first validates the exact assessment referenced by the state.

The assessment must be eligible.

G calls frozen `elevate_paradox_assessment` and requires the state to preserve the exact expected participating alternatives and provenance.

G does not create a new elevated state during validation and does not reinterpret eligibility.

## Validation check names

The ordinary receipt records these completed checks in exact order:

1. `extension-identifier-collision`
2. `condition-evidence-closure`
3. `condition-evidence-collision`
4. `admissibility-state-closure`
5. `candidate-identity-collision`
6. `convergence-membership-closure`
7. `policy-parameter-collision`
8. `policy-extension-closure`
9. `ranking-closure`
10. `outcome-alternative-closure`
11. `outcome-extension-closure`
12. `policy-result-consistency`
13. `provenance-integrity`

The Paradox receipt records:

1. `resolution-validation`
2. `paradox-endpoint-closure`
3. `paradox-pair-collision`
4. `paradox-assessment-consistency`
5. `paradox-provenance-integrity`

The elevated-state receipt records:

1. `assessment-validation`
2. `elevated-eligibility`
3. `elevated-alternative-closure`
4. `elevated-provenance-integrity`

## Later ownership

P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability over validated P11.10 products.

P11.10I owns final P11.10 integration and freeze.

## P11.10G acceptance

P11.10G is accepted only when:

1. the branch descends exactly from frozen P11.10F;
2. frozen P11.10B/C/D/E/F production modules remain unchanged;
3. the semantic-decision package gains exactly six G public symbols;
4. three layered immutable receipt shapes are frozen exactly;
5. core and extension identifier collisions/closure are validated without granting extension semantics;
6. C condition/evidence closure, fact/evidence collision, core-state consistency, and provenance lineage are validated;
7. candidate identity collision and exact D membership closure are validated;
8. policy parameter collision, ranking closure, outcome closure, and E policy/result consistency are validated;
9. zero/one-member deterministic unresolved E products may validate when they agree with frozen E;
10. Paradox endpoint/pair closure and exact F assessment consistency are validated without inventing eligibility;
11. elevated-state eligibility, alternative closure, and provenance are validated without recreating elevation semantics;
12. receipts preserve exact predecessor objects and remain passive;
13. no runtime, authority/governance, causal, Quad-Vector, AETHER-AIR transformation, backend, reporting, or tooling behavior enters G;
14. only the intended additive G artifacts are present.

## Next stage

After P11.10G freezes, P11.10H may add deterministic downstream compatibility, reporting, tooling visibility, and traceability over validated receipts.

P11.10H must consume validated products without re-running or altering B-G semantic ownership.
