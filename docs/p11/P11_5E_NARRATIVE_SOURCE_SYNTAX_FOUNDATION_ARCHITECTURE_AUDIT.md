# P11.5E Narrative Source Syntax Foundation Architecture Audit

## Status

P11.5D is the frozen validation predecessor. Its annotated freeze tag is
`afp-p11.5d-freeze`, resolving to
`c264a2c1f1eb9e1058bc859b78da86c3dad1b28b`.

The original P11.5E-A audit established the boundary before production source
records existed. The **reviewed P11.5E-B successor** now implements that
boundary through one passive production module. The lexer, parser, compiler,
project pipeline, language server, and Visual Studio extension remain unchanged.

P11.5E-A owns exactly:

- `apexforge/p11_5e_narrative_source_syntax_foundation_architecture_audit_smoke_test.py`
- `docs/p11/P11_5E_NARRATIVE_SOURCE_SYNTAX_FOUNDATION_ARCHITECTURE_AUDIT.md`

## Purpose

P11.5B through P11.5D established passive narrative semantic records,
deterministic graph construction, and passive graph validation.

Those layers contain no accepted ApexForge source syntax and no source
provenance for narrative declarations or references.

P11.5E defines the source-facing boundary needed before narrative parsing,
semantic lowering, diagnostics, language-service behavior, or Visual Studio
integration can be implemented safely.

The first implementation must use one opt-in narrative source document and one
story root. It must not alter the ordinary operational ApexForge parser.

## Layer separations

The following separations are mandatory:

- source syntax AST != narrative semantic model;
- parsing != semantic lowering;
- semantic lowering != graph construction;
- graph construction != validation;
- passive validation classification != source diagnostic;
- source formatting != semantic normalization;
- editor coloring != parser acceptance;
- parser acceptance != runtime execution.

P11.5B records remain span-free immutable semantic values. Source provenance
belongs to a separate source AST rather than being retrofitted into frozen
semantic records.

## Proposed source vocabulary

The proposed source vocabulary is:

- `story`
- `character`
- `scene`
- `dialogue`
- `choice`
- `path`
- `perspective`
- `timeline`
- `narrative_state`
- `continuity`

Supporting field vocabulary is proposed as:

- `scene`
- `speaker`
- `participants`
- `destination`
- `condition`
- `consequence`
- `viewpoint`
- `scenes`
- `fact`
- `require`

These words are architectural vocabulary only in P11.5E-A. They are not added
to the frozen lexer keyword table or parser dispatch.

## Proposed source shape

The canonical design target is structurally equivalent to:

```apex
story ExperimentalContinuity {
    character Ada
    character Borin

    scene Arrival
    scene Archive

    dialogue Warning {
        scene Arrival
        speaker Ada
        participants [Borin, UndeclaredWitness]
    }

    choice ArchiveDecision {
        scene Archive

        path "Enter the hidden chamber" {
            destination UndeclaredHiddenChamber
            condition door_open
            consequence secret_revealed
        }
    }

    perspective AdaView {
        viewpoint Ada
    }

    timeline MainTimeline {
        scenes [Arrival, Archive]
    }

    narrative_state KnownFacts {
        fact Ada.trusts_borin = true
    }

    continuity IdentityLaw {
        require Ada: "Ada remembers the archive."
    }
}
```

P11.5E-A does not make this source executable or parser-recognized.

The first parser-facing implementation is limited to one complete story root
per opt-in narrative source document. Multiple story roots, interleaving with
ordinary operational declarations, module imports, exports, and project-wide
linking remain deferred.

## Source provenance contract

The existing `SourceSpan` system remains canonical.

A future narrative source AST must preserve:

- the complete document span;
- the complete story span;
- each declaration span;
- each block span;
- each declared-name span;
- each field-keyword span;
- each reference span;
- each list-item span;
- each scalar-value span;
- each choice-label span;
- each continuity-assertion span.

Every declared name carries a source span.

Every reference carries a source span.

Every scalar value carries a source span.

The source AST may retain punctuation spans when needed for precise recovery or
formatting, but punctuation spans are not semantic identities.

## Ordering and duplicate policy

The source AST must preserve source order and duplicates.

It must not:

- sort declarations;
- deduplicate characters or scenes;
- collapse repeated participants;
- collapse repeated paths;
- collapse repeated timeline scenes;
- collapse repeated state facts;
- collapse repeated continuity requirements;
- normalize distinct spellings into one identity.

Duplicate declarations and repeated relations remain source evidence for later
semantic lowering and passive validation.

## Scalar and reference policy

Bare identifiers remain exact names.

Quoted strings remain opaque text.

Boolean literals lower to exact text, preserving `true` or `false` for the
current P11.5B narrative-state value model.

P11.5E-A assigns no expression semantics to:

- choice conditions;
- choice consequences;
- state values;
- continuity assertions.

A future source AST may represent identifier, string, and boolean scalar forms
distinctly while preserving their exact source text and spans.

References are source-level names. They are not resolved during parsing.

Parsing must not classify a reference as declared, missing, reachable, or
contradictory.

## Error and recovery boundary

P11.5E-A defines no diagnostics.

A future narrative parser may use existing parse-stage `BuildDiagnostic` and
`SourceSpan` infrastructure, but diagnostic codes, messages, recovery points,
and related spans remain deferred until the source AST contract is frozen.

The initial source parser should fail deterministically rather than silently
repairing malformed input.

## Compatibility boundary

P11.5E-A makes:

- no lexer changes;
- no parser changes;
- no compiler integration;
- no project integration;
- no module-system integration;
- no semantic lowering;
- no graph-construction integration;
- no validation integration;
- no AIR changes;
- no artifact changes;
- no runtime changes;
- no CLI changes;
- no diagnostics;
- no language-server integration;
- no VS Code integration;
- no Visual Studio integration.

Existing operational `.apex` syntax and behavior remain unchanged.

## Explicit non-goals

P11.5E-A adds:

- no production source AST;
- no production parser;
- no keyword registration;
- no grammar export changes;
- no canonical EBNF changes;
- no parse diagnostics;
- no semantic lowering;
- no automatic graph construction;
- no automatic validation;
- no source diagnostic projection;
- no formatter support;
- no completion;
- no outline symbols;
- no hover;
- no definition, references, or rename;
- no syntax-color registration;
- no execution semantics.

## Acceptance contract

P11.5E-A passes when:

- the exact annotated P11.5D predecessor remains intact;
- only the two audit-owned files are added;
- source AST and semantic-layer separations are explicit;
- the narrative vocabulary and one-story document boundary are explicit;
- source provenance requirements are explicit;
- source ordering and duplicate retention are explicit;
- scalar and unresolved-reference policy are explicit;
- no production narrative source declarations exist;
- lexer, parser, compiler, project, narrative, AIR, runtime, and CLI files
  remain byte-for-byte unchanged;
- running the audit does not mutate repository state.

## Reviewed production boundary

P11.5E-B introduces one passive production module:

`apexforge/language/narrative_source.py`

It contains immutable source identifiers, scalars, unresolved references,
declaration records, one story root, and one source document. It preserves
exact spans, source order, and duplicates without parser behavior.

## Proposed next stage

P11.5E-C may implement an opt-in narrative source parser against the frozen
P11.5E-B source-AST contract. The ordinary operational parser remains unchanged.
