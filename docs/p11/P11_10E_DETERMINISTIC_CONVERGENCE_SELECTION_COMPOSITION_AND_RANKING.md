# P11.10E - Deterministic Convergence Selection, Composition, and Ranking

## Status

P11.10E is an additive semantic-decision slice based exactly on `afp-p11.10d-freeze`.

It introduces the first P11.10-owned operative convergence-policy vocabulary, immutable ranking/resolution records, and one deterministic policy application function. It does not modify frozen P11.10B, P11.10C, or P11.10D production implementations.

## Ownership

P11.10E owns deterministic convergence selection, composition, and ranking under explicit P11.10-owned policy.

P11.10E does not own Paradox Elevation eligibility or elevated-state construction, broad validation/collision/closure/extension policy, runtime execution, authority/governance decisions, causal-path selection, Quad-Vector resolution, AETHER-AIR transformation, backend lowering, reporting, or tooling.

## Core operative policy identifiers

`CORE_CONVERGENCE_POLICY_IDS` is the exact tuple:

1. `select.explicit-order`
2. `compose.all-admissible`
3. `rank.explicit-order`

These are the first policy identifiers with operative P11.10 semantics.

P11.10D remains open to arbitrary passive `ConvergencePolicy.identity` values. E does not close the D structural vocabulary. An unsupported policy identity simply has no E-owned ordinary convergence semantics and therefore produces an unresolved E result.

E does not import or reinterpret causal `max_weight`, P11.8 passive priority metadata, P11.9 encounter order, provenance order, authority state, Quad-Vector lane order, lexical candidate identity, or any other predecessor metadata as hidden precedence.

## RankedCandidate

`RankedCandidate` has exact fields:

- `candidate`
- `rank`

`candidate` must be an exact P11.10B `CandidateAlternative`.

`rank` must be an exact positive integer.

Direct record construction does not validate ranking-set uniqueness or closure; P11.10G owns broad collision and closure validation.

## SemanticConvergenceResolution

`SemanticConvergenceResolution` has exact fields:

- `convergence_set`
- `ranking`
- `outcome`
- `provenance`

`convergence_set` is the exact supplied P11.10D `SemanticConvergenceSet`.

`ranking` is an exact tuple of exact `RankedCandidate` values.

`outcome` is an exact P11.10B `SemanticOutcome`.

`provenance` preserves the convergence-set provenance without sorting or deduplication.

The resolution record is immutable. It does not execute the selected or composed candidate.

## Explicit-order policy parameter

Both `select.explicit-order` and `rank.explicit-order` require the policy parameters to have exactly this structural form:

`(("order", (<candidate identity>, ...)),)`

The order tuple must:

- contain exact non-empty trimmed strings;
- identify every admissible D member exactly once;
- contain no duplicate identities;
- contain no unknown identities;
- be unambiguous with respect to the admissible D member identities.

The explicit order tuple is the sole E-owned precedence input for these policies.

D candidate encounter order remains trace order and is not precedence.

When the explicit-order parameter is absent, malformed, incomplete, contains duplicates, contains unknown identities, or cannot uniquely identify the admissible members, E returns an unresolved result rather than inventing a tie-breaker.

## select.explicit-order

For two or more admissible D members under a valid explicit order:

- E creates a `RankedCandidate` tuple in the supplied explicit order;
- ranks are consecutive positive integers beginning at 1;
- E creates a `SemanticOutcome` with `kind_id == "selected"`;
- the outcome contains exactly the rank-1 canonical candidate.

Changing D encounter order alone must not change the ranking or selected candidate when the explicit policy order is unchanged.

## compose.all-admissible

For two or more admissible D members, `compose.all-admissible` requires no policy parameters.

E creates:

- an empty ranking tuple;
- a `SemanticOutcome` with `kind_id == "composed"`;
- all admissible D member candidates in preserved D member encounter order.

That preserved order is representational composition order only. It is not ranking or precedence.

If parameters are supplied to this core policy, E returns unresolved rather than silently ignoring them.

E does not perform compatibility scoring in this slice. Formal compatibility and closure remain later validation concerns.

## rank.explicit-order

For two or more admissible D members under a valid explicit order:

- E creates the complete explicit `RankedCandidate` tuple;
- E does not select a winner;
- E creates a `SemanticOutcome` with `kind_id == "unresolved"`;
- the unresolved outcome preserves the admissible member alternatives in D encounter order.

Ranking is therefore inspectable semantic precedence without being implicit selection.

## Unresolved behavior

E returns a deterministic unresolved resolution when:

- fewer than two admissible convergence members are present;
- a core policy cannot interpret its required parameter shape;
- an explicit order is incomplete, duplicated, unknown, or ambiguous;
- `compose.all-admissible` receives unexpected parameters;
- the policy identity is unsupported by E.

An unresolved E result has:

- `ranking == ()`, except a successful `rank.explicit-order` result, which intentionally preserves its explicit ranking;
- `outcome.kind_id == "unresolved"`;
- `outcome.alternatives` equal to the admissible D member candidates in D encounter order;
- provenance equal to the D convergence-set provenance.

E does not turn unresolved ordinary convergence into `paradox.elevation_candidate`. P11.10F alone owns Paradox Elevation eligibility and elevated-state construction.

## Determinism and provenance

Equivalent canonical D inputs under the same explicit E policy produce equivalent rankings and outcomes.

E preserves exact canonical candidate object identities.

Resolution and outcome provenance preserve the exact D convergence-set provenance tuple. E does not sort, deduplicate, fabricate, or reinterpret provenance.

## Excluded precedence sources

The following are never E precedence unless a later explicit P11.10 policy contract independently gives them semantics:

- D candidate encounter order;
- evidence or provenance order;
- P11.8 priority metadata;
- P11.9 encounter/reporting coordinates;
- authority or governance state;
- Quad-Vector lane order/resultants;
- causal `max_weight`;
- lexical candidate identity;
- Python object identity.

The three E core policies introduced here use only their explicitly frozen semantics.

## Later ownership

P11.10F owns Paradox Elevation eligibility and immutable elevated semantic-state contracts.

P11.10G owns validation, collision, closure, provenance validation, extension validation, policy/result consistency validation, and downstream structural validity.

P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability.

P11.10I owns final integration and freeze.

## P11.10E acceptance

P11.10E is accepted only when:

1. the branch descends exactly from frozen P11.10D;
2. frozen P11.10B/C/D production files remain unchanged;
3. the semantic-decision package gains exactly the four E public symbols;
4. the exact three-policy core operative vocabulary is frozen;
5. E records and function signature have the exact frozen shapes;
6. explicit-order selection is deterministic and independent of D encounter order;
7. all-admissible composition preserves admissible members without ranking them;
8. explicit-order ranking establishes inspectable precedence without selecting a winner;
9. unsupported, malformed, ambiguous, or insufficient convergence inputs become unresolved without hidden tie-breakers;
10. exact canonical candidate identity and D provenance are preserved;
11. no Paradox Elevation, runtime, causal-policy reuse, P11.8 priority execution, authority/governance decision, Quad-Vector resolution, backend, reporting, or tooling behavior enters E;
12. only the intended additive E artifacts are present.

## Next stage

After P11.10E freezes, P11.10F may introduce Paradox Elevation eligibility and immutable elevated semantic-state contracts over explicit unresolved ordinary convergence products.

P11.10F must not reinterpret every unresolved E result as Paradox Elevation automatically.
