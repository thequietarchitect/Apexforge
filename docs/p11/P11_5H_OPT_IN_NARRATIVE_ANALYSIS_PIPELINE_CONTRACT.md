# P11.5H-B Opt-In Narrative Analysis Pipeline Contract

## Status

P11.5H-B is based on the annotated P11.5G freeze
`afp-p11.5g-freeze`, resolving to:

`6afe6a3a8e3842a27bbaba99aaef379485a31c5b`

The reviewed candidate owns exactly five files:

1. `apexforge/language/narrative_analysis.py`
2. `apexforge/p11_5h_opt_in_narrative_analysis_pipeline_architecture_audit_smoke_test.py`
3. `apexforge/p11_5h_opt_in_narrative_analysis_pipeline_smoke_test.py`
4. `docs/p11/P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_ARCHITECTURE_AUDIT.md`
5. `docs/p11/P11_5H_OPT_IN_NARRATIVE_ANALYSIS_PIPELINE_CONTRACT.md`

## Purpose

P11.5H-B adds an explicit opt-in composition API for:

`parse -> lower -> graph -> validate`

Composition != integration.

## Public API

`apexforge/language/narrative_analysis.py` exports exactly:

- `NarrativeSourceAnalysis`
- `analyze_narrative_source`

## Result record

`NarrativeSourceAnalysis` is an immutable dataclass containing exactly:

- `source_document: NarrativeSourceDocument`
- `semantic_story: NarrativeStory`
- `semantic_graph: NarrativeSemanticGraph`
- `validation_report: NarrativeValidationReport`

The constructor requires exact product types.

The semantic story identity must agree with the source story name, graph story
identity, and validation-report story identity.

## Entry point

```python
def analyze_narrative_source(
    source: str,
    *,
    source_name: str = "<memory>",
) -> NarrativeSourceAnalysis:
    ...
```

The function stores the exact result of every frozen stage without flattening,
copying, replacing, or reinterpreting that product.

## Stage order

The pipeline always executes:

1. `parse_narrative_source`
2. `lower_narrative_source`
3. `build_narrative_semantic_graph`
4. `validate_narrative_semantic_graph`

A failed stage prevents every later stage from running.

## Error propagation

`NarrativeSourceParseError` propagates unchanged.

`NarrativeSemanticLoweringError` propagates unchanged.

P11.5H-B adds no wrapper exception, pipeline-specific diagnostic, aggregation,
classification conversion, or suppression.

## Passive findings

Validation findings remain passive.

A successful analysis may contain any number of validation findings, including
duplicate declarations, referenced-only identities, conflicting state values,
temporal cycles, repeated relations, continuity clusters, and perspective
clusters.

Those findings are returned in `validation_report`; they do not cause the
pipeline to fail.

## Provenance and evidence

The source document retains source spans and source-form scalar evidence.

The semantic story retains lowered identities, duplicates, unresolved
references, and scalar text.

The graph retains ordered semantic evidence.

The validation report retains ordered passive findings.

The immutable result keeps all four layers available together.

## Determinism

Identical source text and source name produce value-equal analysis results.

All order and duplicate-preservation guarantees remain owned by the frozen
individual stages.

## Compatibility boundary

P11.5H-B changes no frozen stage implementation and adds no:

- compiler integration
- project integration
- AIR integration
- artifact integration
- runtime integration
- CLI integration
- language-server integration
- VS Code integration
- Visual Studio integration
- ordinary parser or lexer integration

## Non-goals

P11.5H-B does not add project discovery, multi-source analysis, name
resolution, diagnostic conversion, execution, serialization, formatting, or
editor commands.

## Acceptance contract

P11.5H-B passes when:

- the annotated P11.5G freeze remains authoritative
- exactly five reviewed files are owned
- the analysis module exposes exactly two public names
- the result stores four exact immutable stage products
- stage order is deterministic
- stage failures propagate unchanged and short-circuit later work
- passive findings remain successful outputs
- all frozen narrative and operational surfaces remain unchanged
- tests do not mutate repository state
