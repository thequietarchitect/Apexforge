# P11.5H-A Opt-In Narrative Analysis Pipeline Architecture Audit

## Status

P11.5G is the frozen lowering predecessor.

The controlling annotated tag is `afp-p11.5g-freeze`, resolving to:

`6afe6a3a8e3842a27bbaba99aaef379485a31c5b`

The original audit established the composition boundary. The reviewed P11.5H-B
successor now implements it through one dedicated production module.

## Core composition

`parse -> lower -> graph -> validate`

Composition != integration.

## Production boundary

P11.5H-B adds one dedicated production module:

`apexforge/language/narrative_analysis.py`

It publicly exports exactly:

- `NarrativeSourceAnalysis`
- `analyze_narrative_source`

## Result contract

`NarrativeSourceAnalysis` is an immutable result record.

It stores exact stage products:

- `source_document`
- `semantic_story`
- `semantic_graph`
- `validation_report`

Exact product types and common story identity are enforced.

## Stage behavior

Deterministic stage order is:

1. parse
2. lower
3. graph
4. validate

`NarrativeSourceParseError propagates unchanged`.

`NarrativeSemanticLoweringError propagates unchanged`.

A failed stage prevents later stages from running.

There is no pipeline-specific diagnostic.

Validation findings remain passive and are returned as successful output.

## Compatibility boundary

No changes to language/narrative_parser.py.

No changes to language/narrative_lowering.py.

No changes to language/narrative_graph.py.

No changes to language/narrative_validation.py.

There is:

- no compiler integration
- no project integration
- no AIR or artifact integration
- no runtime integration
- no CLI integration
- no language-server integration
- no VS Code integration
- no Visual Studio integration

## Acceptance contract

The reviewed P11.5H-A/P11.5H-B candidate passes when:

- the annotated P11.5G freeze remains authoritative
- exactly five reviewed files are owned
- one dedicated analysis module exposes exactly two public names
- the immutable result retains four exact stage products
- deterministic stage order is preserved
- stage failures propagate unchanged and short-circuit
- validation findings remain passive
- frozen narrative and operational surfaces remain unchanged
- tests do not mutate repository state
