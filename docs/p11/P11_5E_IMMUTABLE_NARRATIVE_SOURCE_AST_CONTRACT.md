# P11.5E-B Immutable Narrative Source AST Contract

## Status

P11.5E-B is based on the annotated P11.5D freeze
`afp-p11.5d-freeze`, resolving to
`c264a2c1f1eb9e1058bc859b78da86c3dad1b28b`.

P11.5E-B owns exactly:

- `apexforge/language/narrative_source.py`
- `apexforge/p11_5e_immutable_narrative_source_ast_smoke_test.py`
- `docs/p11/P11_5E_IMMUTABLE_NARRATIVE_SOURCE_AST_CONTRACT.md`

The aligned P11.5E-A architecture audit retains separate ownership of its two
audit files.

## Purpose

P11.5E-B defines immutable source-provenance records for narrative syntax.

It adds no lexer tokens, parser behavior, semantic lowering, graph
construction, validation, diagnostics, execution, or editor integration.

Source syntax AST != narrative semantic model.

## Public API

The module exports exactly:

- `NarrativeSourceIdentifier`
- `NarrativeSourceScalar`
- `NarrativeSourceReference`
- `NarrativeSourceCharacter`
- `NarrativeSourceScene`
- `NarrativeSourceDialogue`
- `NarrativeSourceChoicePath`
- `NarrativeSourceChoice`
- `NarrativeSourcePerspective`
- `NarrativeSourceTimeline`
- `NarrativeSourceStateFact`
- `NarrativeSourceState`
- `NarrativeSourceContinuityConstraint`
- `NarrativeSourceContinuity`
- `NarrativeSourceStory`
- `NarrativeSourceDocument`

No public function is introduced.

## Source leaf records

`NarrativeSourceIdentifier` preserves exact bare identifier text and token span.

`NarrativeSourceScalar` preserves one exact source form:

- `identifier`
- `string`
- `boolean`

Boolean text is exactly `true` or `false`.

`NarrativeSourceReference` preserves an unresolved exact source name and its
expected narrative kind. Parsing and source-AST construction never resolve it.

## Declaration records

Every declaration preserves:

- declaration keyword span;
- declared-name identifier and span;
- complete declaration span;
- ordered child records and references.

Field-bearing records also preserve field-keyword spans.

Choice paths preserve label, destination, optional condition, optional
consequence, their source forms, and their spans.

## Story and document records

`NarrativeSourceStory` contains one ordered tuple for each semantic family:

1. characters
2. scenes
3. dialogues
4. choices
5. perspectives
6. timelines
7. narrative states
8. continuities

`NarrativeSourceDocument` contains exactly one story root and the complete
document span.

## Source order and duplicates

All caller tuple order and duplicate occurrences are preserved.

The source AST does not:

- sort declarations;
- deduplicate declared names;
- collapse repeated participants;
- collapse repeated paths;
- collapse repeated timeline scenes;
- collapse repeated facts;
- collapse repeated continuity requirements.

## Provenance

The existing `SourceSpan` type is reused directly.

The source AST preserves spans for:

- declaration keywords;
- field keywords;
- declared names;
- references;
- scalar values;
- choice labels;
- continuity assertions;
- complete records;
- story root;
- complete document.

Punctuation spans remain optional and are not represented in this minimal
contract.

## Exact source forms

Bare identifiers remain exact names.

Quoted-string content remains opaque exact text.

Boolean literals remain exact lowercase text.

Conditions and consequences are passive scalar source forms. P11.5E-B assigns
them no expression meaning.

## Validation boundary

Constructors validate only record shape and exact source-form invariants.

They do not decide:

- whether references resolve;
- whether declarations are duplicates;
- whether scenes are reachable;
- whether state values conflict;
- whether timelines cycle;
- whether continuity assertions contradict;
- whether perspectives conflict.

Those decisions remain outside the source AST.

## Compatibility boundary

P11.5E-B does not modify:

- source-position or source-span infrastructure;
- lexer;
- parser;
- canonical grammar;
- compiler;
- project construction;
- P11.5B semantic records;
- P11.5C graph construction;
- P11.5D passive validation;
- AIR;
- artifact v1;
- runtime;
- CLI;
- language server;
- VS Code;
- Visual Studio.

## Explicit non-goals

P11.5E-B adds:

- no parser;
- no lexer keyword registration;
- no parse diagnostics;
- no semantic lowering;
- no graph or validator calls;
- no formatter;
- no language-service behavior;
- no Visual Studio classifications;
- no execution semantics;
- no serialization.

## Acceptance contract

P11.5E-B passes when:

- the exact annotated P11.5D predecessor remains intact;
- the reviewed branch owns exactly five P11.5E paths;
- all public source-AST records are immutable;
- exact source order and duplicates remain observable;
- identifiers, strings, booleans, and unresolved references remain distinct;
- required source spans remain intact;
- no public operation exists in the source-AST module;
- all frozen narrative and operational files remain unchanged;
- running the smoke test does not mutate repository state.

## Proposed next stage

P11.5E-C may implement one opt-in narrative source parser in a new production
module against this frozen source-AST contract.

That parser must not modify the ordinary operational parser or perform semantic
lowering, graph construction, passive validation, diagnostics projection, or
runtime execution.
