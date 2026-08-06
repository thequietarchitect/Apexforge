# P11.5G-B Narrative Semantic Lowering Contract

## Status

P11.5G-B is based on the annotated P11.5F freeze
`afp-p11.5f-freeze`, resolving to:

`f24bd96217fb541f105e3bb1f1564f4c593e5111`

The reviewed P11.5G candidate owns exactly five files:

1. `apexforge/language/narrative_lowering.py`
2. `apexforge/p11_5g_narrative_semantic_lowering_architecture_audit_smoke_test.py`
3. `apexforge/p11_5g_narrative_semantic_lowering_smoke_test.py`
4. `docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_ARCHITECTURE_AUDIT.md`
5. `docs/p11/P11_5G_NARRATIVE_SEMANTIC_LOWERING_CONTRACT.md`

## Purpose

P11.5G-B implements one deterministic, one-way conversion from the immutable
P11.5E source AST to the immutable P11.5B semantic model.

Source AST != semantic model.

Semantic lowering != graph construction.

## Public API

`apexforge/language/narrative_lowering.py` exports exactly:

- `NarrativeSemanticLoweringError`
- `lower_narrative_source`

The entry point is:

```python
def lower_narrative_source(
    document: NarrativeSourceDocument,
) -> NarrativeStory:
    ...
```

The function requires one exact `NarrativeSourceDocument` and returns one exact
`NarrativeStory`.

## Identity mapping

Declared names become single-segment identity paths.

Declaration family determines semantic identity kind.

References remain unresolved. Their `expected_kind` becomes semantic identity
kind, and exact reference name text becomes the sole path segment.

No symbol table, declaration lookup, namespace qualification, or identity
canonicalization is performed.

## Record mapping

Every source declaration maps one-for-one to its corresponding semantic record.

The source document wrapper is consumed. Its story becomes the returned
semantic story.

All declaration tuples, nested tuples, and duplicate occurrences retain exact
source order.

## Scalars

Scalar text is preserved exactly when representable by the frozen semantic
model.

The semantic model stores plain strings and therefore does not preserve whether
a value originated as an identifier, quoted string, or boolean token.

That source-form evidence remains available in the original source AST.

## Representability diagnostics

The frozen semantic model requires non-empty trimmed strings for choice labels,
optional choice condition and consequence values, state-fact values, and
continuity assertions.

An unrepresentable value raises `NarrativeSemanticLoweringError` carrying one
exact `BuildDiagnostic`:

- severity: `error`
- stage: `compile`
- code: `APX-NARRATIVE-LOWERING`
- span: the exact source scalar
- message: deterministic field-specific representability failure

Only the first failure in deterministic traversal order is reported.

## Provenance

Semantic records do not gain source-span fields.

All spans remain in the immutable source AST. Callers that need provenance must
retain the original `NarrativeSourceDocument` alongside the lowered
`NarrativeStory`.

## Traversal order

Lowering follows semantic constructor order:

1. characters
2. scenes
3. dialogues
4. choices and paths
5. perspectives
6. timelines
7. states and facts
8. continuities and constraints

Nested tuple order is preserved exactly.

## Passive evidence

The lowerer preserves without deciding:

- duplicate declarations
- duplicate references
- unresolved references
- conflicting state values
- repeated continuity assertions
- repeated perspectives
- temporal cycles encoded by scene order

Those remain inputs for later graph construction and passive validation.

## Frozen compatibility

P11.5G-B makes no changes to:

- narrative source records
- narrative parser
- narrative semantic records
- narrative graph construction
- narrative validation
- ordinary lexer and parser
- compiler
- project construction
- AIR
- artifact v1
- runtime
- CLI
- language server
- VS Code
- Visual Studio

## Non-goals

P11.5G-B adds no parsing, name resolution, graph construction, validation,
diagnostic projection from validation, execution, serialization, formatting,
or editor integration.

## Acceptance contract

P11.5G-B passes when:

- the annotated P11.5F freeze remains authoritative
- exactly five reviewed files are owned
- the lowerer exposes exactly two public names
- valid source records lower deterministically
- identities use exact single-segment paths
- source order, duplicates, and unresolved references remain observable
- representability failures are precise and deterministic
- source records and all frozen operational surfaces remain unchanged
- lowering tests do not mutate repository state
