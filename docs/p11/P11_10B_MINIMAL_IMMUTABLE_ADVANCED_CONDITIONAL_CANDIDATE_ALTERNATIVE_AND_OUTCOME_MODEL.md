# P11.10B - Minimal Immutable Advanced-Conditional, Candidate-Alternative, and Outcome Model

## Status

P11.10B is the first production slice of the P11.10 semantic-decision layer.

It is based exactly on `afp-p11.10a-freeze` and introduces only passive immutable data vocabulary. It does not evaluate conditions, determine admissibility, construct convergence sets, select or rank alternatives, establish convergence policy, determine Paradox Elevation eligibility, validate semantic closure, report results, lower outcomes, or execute runtime behavior.

## Package ownership

P11.10B introduces the top-level production package `apexforge.semantic_decision`.

The package is the umbrella semantic-decision namespace for P11.10. The package name does not imply that B itself performs decisions.

P11.10B initially owns only `AdvancedCondition`, `CandidateAlternative`, `SemanticOutcomeKind`, `SemanticOutcome`, and `CORE_SEMANTIC_OUTCOME_KINDS`.

No other public production symbol is introduced by B.

## Frozen predecessor boundary

`afp-p11.10a-freeze` is the exact predecessor.

P11.10B does not modify the frozen P11.9 AETHER-AIR package, existing AIR/language/runtime/narrative ordinary conditional owners, Quad-Vector synchronization or resultant resolution, Parametric Semantic Lattice ownership, authority/governance ownership, backend behavior, serialization, CLI, editor, or tooling behavior.

P11.10B is additive only.

## AdvancedCondition

`AdvancedCondition` is a passive immutable higher-order semantic condition description with exact fields `identity`, `condition_kind`, `payload`, and `provenance`.

`identity` and `condition_kind` are exact non-empty trimmed strings. `payload` is caller-supplied immutable data restricted to immutable scalar values or recursively immutable tuples. `provenance` is an exact tuple of non-empty trimmed strings.

`condition_kind` is intentionally open in P11.10B. B defines no closed condition-kind registry and gives no condition kind executable meaning.

An `AdvancedCondition` does not evaluate itself, execute AIR expressions, inspect runtime state, invoke narrative predicates, call authority engines, or determine admissibility.

## CandidateAlternative

`CandidateAlternative` is a passive immutable semantic possibility with exact fields `identity`, `payload`, and `provenance`.

B does not discover, resolve, rank, deduplicate, or reinterpret candidate identity. Encounter order and provenance are preserved but do not become semantic precedence.

B does not attach admissibility, truth, ranking, selection, compatibility, or elevation meaning merely because a candidate exists.

## SemanticOutcomeKind

`SemanticOutcomeKind` is a passive immutable descriptor with exact field `canonical_id`.

The B core taxonomy is exactly, and in this order:

1. `selected`
2. `composed`
3. `unresolved`
4. `paradox.elevation_candidate`

The taxonomy names outcome categories only. B does not contain the logic that makes any outcome valid.

`paradox.elevation_candidate` is not an elevated semantic state and does not prove Paradox Elevation eligibility. P11.10F owns eligibility and immutable elevated-state contracts.

## SemanticOutcome

`SemanticOutcome` is a passive immutable envelope with exact fields `kind_id`, `alternatives`, `payload`, and `provenance`.

`alternatives` is an exact tuple containing exact `CandidateAlternative` objects. B preserves the supplied objects and caller order.

B intentionally does not enforce semantic cardinality, uniqueness, taxonomy membership, admissibility, compatibility, selection correctness, composition correctness, unresolved-result correctness, or Paradox Elevation eligibility.

A structurally valid B record can still be semantically invalid under later P11.10 contracts. B does not reject an empty `selected` outcome, duplicate alternatives, or an extension `kind_id`.

Those are not B defects. They preserve the data-first ownership boundary.

## Immutability

All four public record classes are frozen dataclasses. Tuple containers are exact tuples.

Payload values accept only exact immutable scalar values (`str`, `int`, `float`, `bool`, `None`) and recursively immutable tuples. Lists, dictionaries, sets, mutable custom objects, and arbitrary objects are rejected.

`SemanticOutcome.alternatives` preserves exact supplied candidate object identities.

## Non-operative boundary

P11.10B introduces no public function for condition evaluation, truth computation, admissibility determination, candidate discovery/filtering, convergence-set construction, convergence policy/execution, selection, composition, ranking, conflict resolution, Paradox Elevation eligibility/construction, runtime execution, state mutation, authority/governance decisions, AETHER-AIR transformation, Quad-Vector recomputation, backend lowering/generation, serialization, reporting, or CLI/editor/tooling integration.

B is data vocabulary only.

## Later-slice ownership

P11.10C owns canonical condition evidence, admissibility, and deterministic higher-order evaluation contracts.

P11.10D owns semantic convergence-set construction and the explicit convergence-policy boundary.

P11.10E owns deterministic convergence selection, composition, and ranking under explicit P11.10-owned policy.

P11.10F owns Paradox Elevation eligibility and immutable elevated semantic-state contracts.

P11.10G owns validation, collision, closure, provenance, and extension contracts.

P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability.

P11.10I owns final integration regression and freeze.

## P11.10B acceptance

P11.10B is accepted only when:

1. the branch descends exactly from `afp-p11.10a-freeze`;
2. predecessor production surfaces remain unchanged;
3. `apexforge.semantic_decision` exposes exactly the five B public symbols;
4. all four B record classes are frozen dataclasses with exact reviewed field shapes;
5. the core outcome taxonomy contains exactly the four reviewed identifiers in canonical order;
6. condition kinds remain passive open identifiers without evaluation semantics;
7. payload and provenance boundaries are structurally immutable;
8. `SemanticOutcome` preserves exact supplied candidate objects and encounter order;
9. B does not enforce later-owned admissibility, cardinality, collision, selection, convergence, ranking, or elevation eligibility semantics;
10. no operative evaluation, convergence, ranking, Paradox Elevation, runtime, backend, serialization, reporting, or tooling behavior enters the package;
11. the frozen P11.10A architecture regression remains green in its canonical isolated checkout;
12. the B smoke leaves repository status unchanged.

## Next stage

After P11.10B freezes, P11.10C may introduce canonical condition evidence, admissibility state, and deterministic higher-order evaluation contracts over explicit B records.

P11.10C must not yet perform semantic convergence selection/ranking or Paradox Elevation.