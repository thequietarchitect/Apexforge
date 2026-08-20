# P11.10H - Downstream Compatibility, Reporting, Tooling Visibility, and Traceability

## Status

P11.10H is an additive downstream-observation slice based exactly on `afp-p11.10g-freeze`.

It consumes exact frozen P11.10G validation receipts. It does not revalidate, recompute, alter, select, rank, compose, elevate, execute, authorize, lower, or mutate semantic-decision products.

## Ownership

P11.10H owns:

- one immutable downstream projection over exact G validation receipts;
- explicit downstream consumer labeling;
- projection provenance;
- deterministic human-readable reporting;
- passive tooling visibility and traceability.

P11.10H does not own B-F semantic decisions, G validation, runtime execution, authority/governance decisions, causal selection, Quad-Vector resolution, AETHER-AIR transformation, backend lowering, CLI command routing, IDE mutation, or final P11.10 integration.

## Canonical public surface

P11.10H adds exactly:

- `SemanticDecisionDownstreamProjection`
- `project_validated_semantic_decision`
- `render_semantic_decision_downstream_projection_report`

## One discriminated downstream projection

P11.10H follows the frozen P11.9 downstream projection precedent.

`SemanticDecisionDownstreamProjection` has exact fields:

- `validation`
- `consumer`
- `provenance`

`validation` must be exactly one of:

- `SemanticDecisionValidationReceipt`
- `ParadoxElevationValidationReceipt`
- `ElevatedSemanticStateValidationReceipt`

The exact receipt type is the downstream discriminator.

H does not flatten G's layered receipt graph. A Paradox receipt still preserves its exact ordinary resolution receipt. An elevated-state receipt still preserves its exact Paradox receipt and nested ordinary resolution receipt.

## Projection construction

`project_validated_semantic_decision` accepts one exact G receipt plus keyword-only:

- `consumer`
- `provenance`

`consumer` must be an exact non-empty trimmed string.

`provenance` must be an exact tuple of non-empty trimmed strings.

The projection preserves the exact validation receipt object, exact consumer text, and exact projection-provenance tuple supplied by the caller.

Projection provenance is downstream trace metadata only. It is not merged into or substituted for G validation provenance.

The projection constructor performs no G validation and calls no B-G semantic function.

## Consumer boundary

`consumer` is an observational downstream label.

A consumer label does not:

- establish convergence precedence;
- select a candidate;
- grant authority;
- route runtime execution;
- establish backend lowering;
- alter Paradox Elevation;
- modify validation;
- mutate a canonical object.

Changing only the consumer label must not change the exact validation receipt or any semantic content.

## Deterministic report

`render_semantic_decision_downstream_projection_report` accepts only an exact `SemanticDecisionDownstreamProjection` and returns one exact `str` with no trailing newline.

The report includes:

- consumer;
- projection provenance;
- the exact validation-receipt family;
- ordinary semantic-decision policy, candidates, admissibility states, members, ranking, outcome, extension identifiers, validation provenance, and checks;
- Paradox eligibility, information-loss evidence flag, incompatibility evidence, candidate outcome, Paradox provenance, and checks when a Paradox receipt is present;
- elevated alternatives, elevated provenance, and elevated validation checks when an elevated-state receipt is present;
- nested receipt lineage for Paradox and elevated-state reports.

The report is deterministic for equivalent immutable input.

## No revalidation or reprojection during reporting

Reporting consumes the already-created H projection.

It does not call:

- `validate_semantic_convergence_resolution`
- `validate_paradox_elevation_assessment`
- `validate_elevated_semantic_state`
- `evaluate_advanced_condition`
- `construct_semantic_convergence_set`
- `apply_semantic_convergence_policy`
- `assess_paradox_elevation`
- `elevate_paradox_assessment`
- `project_validated_semantic_decision`

The reporter only observes the exact projection and its preserved G receipt graph.

## Downstream compatibility

H accepts all three frozen G receipt families through one projection type.

This provides a stable compatibility boundary for later tools without forcing downstream consumers to reconstruct semantic-decision state or depend directly on B-F constructors.

Unknown objects, raw semantic resolutions, raw Paradox assessments, and raw elevated states are not accepted by the H projection constructor.

A reporter does not accept a raw G receipt directly; the explicit H projection boundary is required.

## Tooling visibility

P11.10H provides public deterministic projection and reporting surfaces that CLI, editor, diagnostics, external tooling, tests, or future integrations may consume.

This slice does not modify existing CLI, LSP, VS Code, Visual Studio, runtime-report, or narrative-report owners.

Tooling visibility is observational availability, not automatic integration or command registration.

## Traceability

The report preserves G receipt nesting:

ordinary:
`SemanticDecisionValidationReceipt`

Paradox:
`ParadoxElevationValidationReceipt -> SemanticDecisionValidationReceipt`

elevated:
`ElevatedSemanticStateValidationReceipt -> ParadoxElevationValidationReceipt -> SemanticDecisionValidationReceipt`

The report also preserves candidate identities, states, extension declarations, checks, receipt provenance, incompatibility relations, and elevated alternatives in deterministic encounter order.

Report order is representational only. It is not semantic precedence.

## P11.10H acceptance

P11.10H is accepted only when:

1. the branch descends exactly from frozen P11.10G;
2. frozen P11.10B-G production modules remain unchanged;
3. the semantic-decision package gains exactly three H public symbols;
4. the projection has exact fields `validation`, `consumer`, `provenance`;
5. the projection accepts only exact frozen G receipt types;
6. the projection preserves exact receipt identity and caller-supplied consumer/provenance;
7. consumer/projection provenance remain observational metadata;
8. one deterministic reporter handles all three G receipt families;
9. Paradox and elevated reports preserve nested receipt lineage;
10. reporting is pure observation with no validation, reprojection, semantic recomputation, execution, authority, backend, or mutation;
11. no historical CLI/editor/runtime/reporting owner is modified;
12. only the intended additive H artifacts are present.

## Next stage

After P11.10H freezes, P11.10I owns final integration, regression, and freeze.

P11.10I should verify the complete A-H ownership chain and integrated B-H identity/traceability lineage without adding new semantic behavior.
