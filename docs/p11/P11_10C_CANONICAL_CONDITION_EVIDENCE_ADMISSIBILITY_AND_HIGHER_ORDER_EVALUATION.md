# P11.10C - Canonical Condition Evidence, Admissibility, and Higher-Order Evaluation

## Status

P11.10C is an additive production slice based exactly on `afp-p11.10b-freeze`.

It adds explicit immutable condition evidence, a canonical admissibility-state taxonomy, immutable advanced-condition evaluation results, and one deterministic pure evaluator. It does not modify the frozen P11.10B model.

## Ownership

P11.10C owns canonical condition evidence, admissibility state, and deterministic higher-order evaluation over explicit P11.10B `AdvancedCondition` records.

P11.10C does not own semantic convergence-set construction, convergence policy, candidate selection, candidate composition, ranking, Paradox Elevation eligibility, elevated semantic-state construction, downstream lowering, reporting, tooling, or runtime execution.

## Frozen P11.10B boundary

`apexforge/semantic_decision/model.py` remains byte-for-byte frozen from `afp-p11.10b-freeze`.

The B public record shapes and core semantic outcome taxonomy remain unchanged.

C extends the package additively through `apexforge.semantic_decision.evaluation` and additive package exports.

## ConditionEvidence

`ConditionEvidence` has exact fields:

- `condition`
- `result`
- `facts`
- `provenance`

`condition` must be an exact `AdvancedCondition`.

`result` is an explicit exact `bool` or `None`. It is supplied by the caller as already-canonical evidence. C does not obtain it by executing AIR, runtime, narrative, authority, governance, Quad-Vector, AETHER-AIR, or backend machinery.

`facts` is an exact tuple of exact `(key, value)` tuples. Keys are non-empty trimmed strings. Values are immutable scalar values or recursively immutable tuples.

`provenance` is an exact tuple of non-empty trimmed strings.

C preserves evidence facts and provenance as supplied. Facts are explanatory evidence and are not interpreted as hidden executable predicates.

## AdmissibilityState

`AdmissibilityState` has exact field `canonical_id`.

The core taxonomy is exactly, and in this order:

1. `admissible`
2. `inadmissible`
3. `indeterminate`

The record accepts open state identifiers structurally. Later validation/extension contracts own closed-membership and extension rules.

## AdvancedConditionEvaluation

`AdvancedConditionEvaluation` has exact fields:

- `condition`
- `evidence`
- `state_id`
- `provenance`

The evaluation preserves the exact supplied `AdvancedCondition` object and exact evidence objects in caller order.

The record is passive. Direct construction does not prove that `state_id` was produced by the canonical evaluator.

## Canonical evaluation rule

`evaluate_advanced_condition(condition, *, evidence=())` accepts only an exact B `AdvancedCondition` and an exact tuple of exact `ConditionEvidence` records.

Every evidence record must reference the exact same `AdvancedCondition` object supplied to the evaluator. Equal-but-distinct condition objects are rejected.

Evaluation is deterministic and intentionally conservative:

- no evidence -> `indeterminate`;
- if any explicit evidence result is `None` -> `indeterminate`;
- all explicit results `True` -> `admissible`;
- all explicit results `False` -> `inadmissible`;
- mixed `True` and `False` -> `indeterminate`.

The evaluator does not sort, deduplicate, rank, weight, or otherwise establish precedence among evidence records.

The evaluator does not interpret `AdvancedCondition.condition_kind`, `AdvancedCondition.payload`, evidence fact keys, evidence fact values, provenance ordering, P11.8 priority metadata, P11.9 encounter order, authority state, or Quad-Vector lane ordering as hidden precedence.

## Provenance

Canonical evaluation provenance is deterministic concatenation in this order:

1. `AdvancedCondition.provenance`;
2. each evidence record's provenance in caller encounter order.

No provenance item is synthesized, sorted, deduplicated, or converted into semantic priority.

## Ordinary conditional execution exclusion

Existing AIR/runtime `when`/`otherwise` evaluation and narrative predicate evaluation remain authoritative in their existing owners.

C does not call runtime expression evaluators, execute AIR expressions, evaluate narrative predicates, inspect runtime state, mutate runtime state, invoke effects, execute transitions, or call authority/governance engines.

Higher-order evaluation in C means deterministic classification over explicit already-canonical evidence, not execution of predecessor conditions.

## Candidate and convergence exclusion

C does not accept a `CandidateAlternative` argument and does not return a `CandidateAlternative` or `SemanticOutcome`.

C does not discover, filter, select, compose, rank, converge, or elevate candidate alternatives.

Mixed evidence is `indeterminate`; it is not Paradox Elevation and does not create a `paradox.elevation_candidate` outcome.

P11.10D owns semantic convergence-set construction and explicit convergence-policy boundaries.

P11.10E owns deterministic convergence selection, composition, and ranking.

P11.10F owns Paradox Elevation eligibility and immutable elevated semantic-state contracts.

## Validation and extension boundary

P11.10C performs only structural constructor checks and the explicit evaluator input-identity rule required for deterministic evaluation.

Duplicate evidence, duplicate facts, repeated provenance, custom admissibility identifiers, and broader semantic closure remain later validation/extension concerns unless explicitly forbidden by this C contract.

## Public surface

P11.10C adds exactly:

- `ConditionEvidence`
- `AdmissibilityState`
- `CORE_ADMISSIBILITY_STATES`
- `AdvancedConditionEvaluation`
- `evaluate_advanced_condition`

The package public surface becomes the frozen five B symbols followed by these five C symbols.

## Acceptance

P11.10C is accepted only when:

1. the branch descends from `afp-p11.10b-freeze`;
2. frozen P11.10B `model.py` remains unchanged;
3. predecessor AETHER-AIR, AIR/language/runtime/narrative, Quad-Vector, semantic-lattice, authority, and governance production surfaces remain unchanged;
4. the package exposes the exact reviewed ten-symbol public surface;
5. C record field shapes and core three-state taxonomy match this contract;
6. evidence requires explicit `bool`/`None` results and exact immutable structures;
7. evaluation preserves exact condition/evidence object identity and caller order;
8. the canonical five-case evaluation rule is deterministic;
9. provenance aggregation is exact and encounter-order preserving;
10. no ordinary conditional execution, candidate selection, convergence, ranking, SemanticOutcome construction, or Paradox Elevation enters C;
11. frozen P11.10B and isolated P11.10A regressions remain green;
12. the C smoke leaves repository status unchanged.

## Next stage

After P11.10C freezes, P11.10D may introduce semantic convergence-set construction and explicit convergence-policy records over explicit B candidates and canonical C evaluation products.

P11.10D must not yet perform convergence selection, composition, ranking, or Paradox Elevation.
