# P11.5G-A Narrative Semantic Lowering Architecture Audit

## Status

P11.5F is the frozen parser predecessor.

The controlling annotated tag is `afp-p11.5f-freeze`, resolving to:

`f24bd96217fb541f105e3bb1f1564f4c593e5111`

The original P11.5G-A audit established the lowering boundary before production
implementation. The reviewed P11.5G-B successor now implements that boundary
through one dedicated production module.

## Core separations

Source AST != semantic model.

Semantic lowering != graph construction.

The lowerer accepts one existing source document. No parser invocation occurs.

## Production boundary

P11.5G-B adds one dedicated production module:

`apexforge/language/narrative_lowering.py`

It publicly exports exactly:

- `NarrativeSemanticLoweringError`
- `lower_narrative_source`

## Identity mapping

Declared names become single-segment identity paths.

Reference expected kind becomes identity kind.

Reference name text becomes the sole identity-path segment.

No name resolution occurs.

## Record mapping

Every source declaration maps one-for-one to the corresponding semantic record.

Source order and duplicates are preserved for declarations, participants,
choice paths, timeline scenes, state facts, continuity constraints, and
continuity subjects.

## Scalar mapping

Scalar text is preserved when representable by the semantic model.

Scalar source-form kind is not preserved because the semantic model stores
plain strings. Identifier, quoted-string, and boolean distinctions remain in
the source AST.

## Provenance

Source spans remain in the source AST.

The semantic model receives no invented provenance fields.

## Lowering failures

Unrepresentable empty or surrounding-whitespace scalar values raise
`NarrativeSemanticLoweringError`.

The error carries one canonical `BuildDiagnostic` using code
`APX-NARRATIVE-LOWERING`, stage `compile`, and the exact scalar span.

The first deterministic lowering failure is reported in source traversal order.

## Compatibility boundary

No changes to language/narrative_source.py.

No changes to language/narrative_model.py.

No changes to language/narrative_parser.py.

There is:

- no parser invocation
- no graph construction
- no narrative validation
- no compiler integration
- no project integration
- no AIR or artifact integration
- no runtime integration
- no CLI integration
- no language-server integration
- no VS Code integration
- no Visual Studio integration

The frozen source, parser, semantic, graph, validation, and operational surfaces
remain byte-identical to P11.5F.

## Acceptance contract

The reviewed P11.5G-A/P11.5G-B candidate passes when:

- the annotated P11.5F freeze remains authoritative
- exactly five reviewed files are owned
- one dedicated lowerer exposes exactly two public names
- identities use single-segment identity paths
- unresolved references remain passive semantic identities
- source order and duplicates remain observable
- scalar evidence loss is explicit
- representability diagnostics are precise and deterministic
- frozen predecessor surfaces remain unchanged
- tests do not mutate repository state
