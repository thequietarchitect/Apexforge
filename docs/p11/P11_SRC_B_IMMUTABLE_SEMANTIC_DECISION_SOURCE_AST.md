# P11-SRC-B - Immutable Semantic Decision Source AST

## Status

Production source-model slice following `afp-p11-src-a-freeze`.

P11-SRC-B introduces only immutable, source-provenance-preserving AST records for authored semantic-decision syntax. It does not add lexical recognition, parsing, semantic lowering, convergence execution, Paradox Elevation execution, AIR ownership, project-build ownership, or runtime mutation.

## Production surface

`apexforge/language/semantic_decision_source.py` owns:

- `SemanticDecisionSourceIdentifier`
- `SemanticDecisionSourceScalar`
- `SemanticDecisionSourceCandidate`
- `SemanticDecisionSourceIncompatibility`
- `SemanticDecisionSourceConvergence`
- `SemanticDecisionSourceParadoxElevation`
- `SemanticDecisionSourceDeclaration`
- `SemanticDecisionSourceDocument`

All records are frozen dataclasses and preserve `SourceSpan` provenance.

## Source-model rules

Identifiers are exact, non-empty, trimmed source text.

Source scalars preserve one of four passive forms:

- `identifier`
- `string`
- `boolean`
- `expression`

`expression` stores authored expression text only. P11-SRC-B does not interpret, evaluate, normalize, or lower the expression.

Candidate `when` spans and conditions must appear together.

A convergence record preserves an authored policy reference plus an exact tuple representing candidate order. P11-SRC-B does not verify that the policy is a canonical P11.10 policy or that candidate references resolve.

Paradox Elevation source records preserve the authored `paradox` / `elevate` spans and optional `when` / `requires` source pairs. They do not assess eligibility or elevate any semantic state.

Declaration records aggregate candidates, incompatibility assertions, optional convergence, and optional Paradox Elevation source material. Reference resolution and cross-record semantic consistency remain outside this slice.

A semantic-decision source document contains one or more decision declarations.

## Ownership boundary

P11-SRC-B owns source structure only.

P11.10 remains the sole owner of:

- `AdvancedCondition`
- `CandidateAlternative`
- condition evaluation and admissibility
- convergence policies, sets, and resolution
- incompatibility evidence semantics
- Paradox Elevation assessment and elevation
- semantic validation
- downstream projection and reporting

The ordinary AIR parser/compiler, `SourceUnitNode`, `ProjectBuild`, narrative pipeline, and runtime are unchanged.

## Deliberate exclusions

P11-SRC-B does not:

- add `decision`, `candidate`, `converge`, `using`, `incompatible`, `paradox`, or `elevate` to the lexer;
- add a semantic-decision parser;
- add semantic-decision lowering;
- modify frozen P11.10 code;
- resolve candidate names;
- validate canonical convergence policy IDs;
- evaluate conditions;
- construct P11.10 semantic objects;
- modify build artifacts;
- add runtime behavior.

## Next slice

P11-SRC-C will begin from the P11-SRC-B freeze and introduce source recognition plus deterministic parsing into these immutable records. Parser behavior must preserve the source spans and ordering established here without acquiring P11.10 semantic authority.