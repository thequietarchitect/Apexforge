# P11.10D - Semantic Convergence-Set Construction and Explicit Policy Boundary

## Status

P11.10D is an additive semantic-decision slice based exactly on `afp-p11.10c-freeze`.

It introduces immutable convergence-policy, evaluated-candidate, and semantic-convergence-set records plus one deterministic constructor. It does not modify the frozen P11.10B model or P11.10C evaluation implementation.

## Ownership

P11.10D owns:

- explicit passive convergence-policy records;
- explicit binding of one `CandidateAlternative` to one canonical `AdvancedConditionEvaluation`;
- deterministic convergence-set construction from caller-supplied evaluated candidates;
- preservation of the complete evaluated-candidate trace;
- derivation of the admissible convergence-member subset;
- deterministic provenance aggregation.

P11.10D does not own convergence selection, composition, ranking, compatibility scoring, precedence inference, Paradox Elevation eligibility, elevated state construction, runtime execution, authority/governance decisions, Quad-Vector resultant resolution, AETHER-AIR transformation, backend lowering, reporting, or tooling.

## ConvergencePolicy

`ConvergencePolicy` has exact fields:

- `identity`
- `parameters`
- `provenance`

`identity` is an open, non-empty, trimmed string. D does not define a closed convergence-policy taxonomy and does not interpret the policy identifier.

`parameters` is an exact tuple of exact `(key, value)` tuples. Keys are non-empty trimmed strings. Values are immutable scalar or recursively immutable tuple values.

`provenance` is an exact tuple of non-empty trimmed strings.

A policy record is descriptive input to later P11.10 semantics. Merely supplying a policy does not select, rank, compose, or prefer any candidate.

## EvaluatedCandidate

`EvaluatedCandidate` has exact fields:

- `candidate`
- `evaluation`

`candidate` must be an exact P11.10B `CandidateAlternative`.

`evaluation` must be an exact P11.10C `AdvancedConditionEvaluation`.

D preserves both exact predecessor objects. It does not reevaluate the condition, discover a candidate, infer a condition-to-candidate relation, or copy either predecessor.

## SemanticConvergenceSet

`SemanticConvergenceSet` has exact fields:

- `policy`
- `candidates`
- `members`
- `provenance`

`policy` is the exact supplied `ConvergencePolicy`.

`candidates` is the exact caller-supplied tuple of `EvaluatedCandidate` objects and preserves encounter order.

`members` contains, in encounter order, the exact candidate bindings whose canonical evaluation has `state_id == "admissible"`.

The complete `candidates` tuple is preserved even when a candidate is inadmissible or indeterminate. D therefore keeps the full evaluated-candidate trace while exposing the admissible subset used by later convergence semantics.

D does not sort, rank, score, deduplicate, resolve, select, compose, or reinterpret candidates.

## Construction rule

`construct_semantic_convergence_set(candidates, *, policy)` is deterministic over explicit canonical inputs.

For each supplied `EvaluatedCandidate`:

- `admissible` -> retained in `members`;
- every other structural state identifier -> not retained in `members`.

D does not invoke the P11.10C evaluator and does not validate whether a custom `state_id` is a canonical extension. Those are separate ownership concerns.

A zero-member or one-member `SemanticConvergenceSet` is structurally permitted in D. The P11.10 architecture defines ordinary semantic convergence as examining two or more admissible alternatives, but later validation/closure owns rejecting products that are not semantically valid for a downstream convergence operation.

Duplicate candidates, duplicate evaluations, duplicate provenance, duplicate parameter keys, convergence-set cardinality, extension identifiers, and broader semantic closure remain later validation concerns unless explicitly forbidden by this D contract.

## Provenance

Constructor provenance is aggregated without sorting or deduplication in this exact order:

1. `policy.provenance`;
2. for each `EvaluatedCandidate` in encounter order:
   - `candidate.provenance`;
   - `evaluation.provenance`.

Encounter order is trace order only. It is never convergence precedence.

## Explicit-policy boundary

A convergence policy must be supplied explicitly.

D does not infer policy identity or precedence from:

- candidate encounter order;
- candidate provenance order;
- evaluation evidence order;
- P11.8 priority metadata;
- P11.9 AETHER-AIR encounter order, reporting coordinates, consumer labels, or operation labels;
- authority or governance state;
- Quad-Vector lane order or resultant data;
- causal `max_weight` policy.

Existing causal policy semantics remain owned by the causal subsystem and are not imported as P11.10 convergence policy.

## No operative convergence semantics

P11.10D introduces no public function for candidate selection, composition, ranking, winner resolution, compatibility scoring, policy execution, Paradox Elevation eligibility/construction, runtime execution, state mutation, backend lowering, reporting, or tooling integration.

`construct_semantic_convergence_set` only constructs the explicit policy-bound convergence input set.

## Later ownership

P11.10E owns deterministic convergence selection, composition, and ranking under explicit P11.10-owned policy.

P11.10F owns Paradox Elevation eligibility and immutable elevated semantic-state contracts.

P11.10G owns validation, collision, closure, provenance validation, extension validation, and downstream structural validity.

P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability.

P11.10I owns final integration and freeze.

## P11.10D acceptance

P11.10D is accepted only when:

1. the branch descends exactly from frozen P11.10C;
2. frozen P11.10B and P11.10C production files remain unchanged;
3. the semantic-decision package gains exactly the four D public symbols;
4. D records have the exact frozen field shapes;
5. exact B/C predecessor object identity is preserved;
6. policy identity is explicit, open, passive, and never interpreted by D;
7. the constructor preserves the complete candidate tuple and derives only the admissible-member subset;
8. encounter order and deterministic provenance are preserved without implying precedence;
9. zero/one-member structures remain constructible and later validation ownership is preserved;
10. no selection, composition, ranking, Paradox Elevation, runtime, causal-policy reuse, backend, reporting, or tooling behavior enters D;
11. only the intended additive D artifacts are present.

## Next stage

After P11.10D freezes, P11.10E may introduce deterministic convergence selection, composition, and ranking under explicit P11.10-owned policy.

P11.10E must not silently infer precedence from D encounter order or provenance.
