# P11.10F - Paradox Elevation Eligibility and Immutable Elevated Semantic State

## Status

P11.10F is an additive semantic-decision slice based exactly on `afp-p11.10e-freeze`.

It introduces explicit pairwise semantic-incompatibility evidence, explicit Paradox Elevation evidence, immutable eligibility assessment, immutable elevated semantic state, and two deterministic functions. It does not modify frozen P11.10B/C/D/E production implementations.

## Ownership

P11.10F owns:

- explicit semantic incompatibility evidence used only for Paradox Elevation;
- explicit evidence that ordinary reduction would require semantically relevant information loss;
- deterministic Paradox Elevation eligibility;
- construction of `paradox.elevation_candidate` only after positive eligibility;
- immutable elevated semantic-state construction over positively eligible assessments.

P11.10F does not own ordinary convergence selection/composition/ranking, broad validation/collision/closure/extension policy, runtime execution, authority/governance conflict resolution, causal-path selection, Quad-Vector resolution, AETHER-AIR transformation, backend lowering, reporting, or tooling.

Paradox Elevation is not ordinary branch selection, error handling, averaging, conflict suppression, or automatic winner selection.

## ParadoxIncompatibilityEvidence

`ParadoxIncompatibilityEvidence` has exact fields:

- `left`
- `right`
- `materially_incompatible`
- `provenance`

Both endpoints must be exact P11.10B `CandidateAlternative` objects.

`materially_incompatible` is an exact bool.

The evidence record is explicit semantic evidence. F does not inspect candidate payloads, provenance text, identity spelling, P11.8 priority metadata, P11.9 coordinates, authority state, causal weight, or any other predecessor field to infer incompatibility.

F semantic incompatibility is not Concordat/governance policy-conflict evidence and does not call governance conflict classification.

## ParadoxElevationEvidence

`ParadoxElevationEvidence` has exact fields:

- `resolution`
- `incompatibilities`
- `reduction_requires_information_loss`
- `provenance`

`resolution` must be an exact P11.10E `SemanticConvergenceResolution`.

`incompatibilities` is an exact tuple of exact `ParadoxIncompatibilityEvidence` records.

`reduction_requires_information_loss` is an exact bool supplied explicitly by the caller. F does not infer information loss by inspecting candidate payloads.

## Eligible unresolved ordinary convergence

An E outcome being `unresolved` is necessary but not sufficient for Paradox Elevation.

The frozen F core accepts only a successful ordinary `rank.explicit-order` E resolution as an unresolved convergence product eligible for further Paradox assessment. This distinguishes a legitimate unresolved ranked convergence from E's deterministic unresolved fallback for malformed parameters, unsupported policies, ambiguous identities, or insufficient cardinality.

For F eligibility:

1. the E outcome kind must be `unresolved`;
2. the unresolved outcome must preserve at least two exact candidate alternatives;
3. those alternatives must be the exact admissible D convergence members in the same trace order;
4. all participating D member evaluations must remain `admissible`;
5. the E policy must be `rank.explicit-order`;
6. E must have produced a complete consecutive ranking over every participating alternative exactly once;
7. the caller must explicitly state that reduction requires semantically relevant information loss;
8. complete pairwise material-incompatibility evidence must cover every unordered pair of participating alternatives exactly once;
9. every covered pair must explicitly state `materially_incompatible == True`.

No other unresolved E result becomes eligible merely because it is unresolved.

Future policy extensions may broaden this boundary only through later explicit contracts and validation.

## Complete incompatibility relation

For alternatives `A`, `B`, and `C`, eligibility requires explicit evidence for all three unordered pairs:

- `A` with `B`;
- `A` with `C`;
- `B` with `C`.

Evidence orientation is non-semantic: `A,B` and `B,A` represent the same unordered pair for coverage.

Missing pair evidence, duplicate pair evidence, self-pair evidence, endpoints outside the participating alternatives, or any pair explicitly marked not materially incompatible makes the assessment ineligible.

F does not silently elevate a paradoxical subset. The supplied unresolved participating set itself must establish complete material incompatibility.

Broad validation diagnostics and extension semantics remain P11.10G ownership.

## Information-loss boundary

`reduction_requires_information_loss` is whole-resolution evidence rather than pairwise evidence.

It means that reducing the participating unresolved ordinary convergence to a single ordinary result would discard semantically relevant information.

The flag must be explicitly `True` for eligibility.

F does not compute, score, estimate, or infer semantic information loss.

## ParadoxElevationAssessment

`ParadoxElevationAssessment` has exact fields:

- `evidence`
- `eligible`
- `candidate_outcome`
- `provenance`

For an ineligible assessment:

- `eligible == False`;
- `candidate_outcome is None`.

For an eligible assessment:

- `eligible == True`;
- `candidate_outcome` is an exact B `SemanticOutcome`;
- `candidate_outcome.kind_id == "paradox.elevation_candidate"`;
- its alternatives are the exact unresolved participating candidate objects.

The B taxonomy value `paradox.elevation_candidate` therefore gains operative meaning only through a positive F assessment. A manually constructed B outcome with that kind does not prove eligibility.

## Provenance

Assessment provenance is aggregated without sorting or deduplication in this exact order:

1. E resolution provenance;
2. `ParadoxElevationEvidence.provenance`;
3. each incompatibility-evidence provenance tuple in supplied evidence encounter order.

The eligible candidate outcome preserves that exact assessment provenance.

Provenance is trace evidence only. It is not compatibility, precedence, truth, or authority.

## ElevatedSemanticState

`ElevatedSemanticState` has exact fields:

- `assessment`
- `alternatives`
- `provenance`

`elevate_paradox_assessment` accepts only an exact positively eligible `ParadoxElevationAssessment` carrying a `paradox.elevation_candidate` outcome.

The elevated state preserves:

- the exact assessment object;
- the exact participating candidate objects;
- the assessment provenance.

Elevation does not select, rank, average, merge, execute, authorize, mutate, or lower the alternatives.

The contradiction or incompatibility becomes represented immutable semantic state rather than being discarded.

## Ordinary unresolved results that are not Paradox Elevation

The following do not establish eligibility by themselves:

- unsupported E policy;
- malformed or incomplete explicit order;
- ambiguous candidate identities;
- insufficient convergence cardinality;
- mixed or indeterminate C evidence;
- missing incompatibility evidence;
- candidate payloads that appear contradictory;
- governance or authority conflict;
- a manually constructed `paradox.elevation_candidate` B outcome.

Paradox Elevation requires the complete positive F evidence contract.

## Later ownership

P11.10G owns validation, collision, closure, provenance validation, extension validation, policy/result consistency validation, and downstream structural validity.

P11.10H owns downstream compatibility, reporting, tooling visibility, and traceability.

P11.10I owns final integration and freeze.

## P11.10F acceptance

P11.10F is accepted only when:

1. the branch descends exactly from frozen P11.10E;
2. frozen P11.10B/C/D/E production files remain unchanged;
3. the semantic-decision package gains exactly the six F public symbols;
4. all F records have the exact frozen field shapes;
5. eligibility requires an exact unresolved successful ranked E resolution rather than any unresolved fallback;
6. eligibility requires at least two exact admissible D members;
7. complete pairwise material-incompatibility evidence covers every participating pair exactly once;
8. explicit whole-resolution information-loss evidence is required;
9. ineligible evidence never creates a `paradox.elevation_candidate`;
10. eligible assessment preserves exact candidate identity and deterministic provenance;
11. elevated state can be constructed only from an eligible assessment and preserves all participating alternatives;
12. F does not inspect payloads, reuse governance conflict classification, select winners, average, execute, grant authority, resolve Quad-Vector state, transform AETHER-AIR, lower backend state, report, or mutate runtime state;
13. only the intended additive F artifacts are present.

## Next stage

After P11.10F freezes, P11.10G may validate the complete P11.10 semantic-decision product family for collision, closure, provenance, extension identifiers, policy/result consistency, and downstream structural validity.

P11.10G must validate existing F semantics without inventing new Paradox Elevation eligibility.
