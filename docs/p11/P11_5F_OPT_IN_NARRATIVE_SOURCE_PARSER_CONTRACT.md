# P11.5F-B Opt-In Narrative Source Parser Contract

## Status

P11.5F-B is based on the annotated P11.5E freeze
`afp-p11.5e-freeze`, resolving to:

`eba9a27a34563a8df5f77b796c82b032ab2b0485`

The reviewed P11.5F candidate owns exactly five files:

1. `apexforge/language/narrative_parser.py`
2. `apexforge/p11_5f_opt_in_narrative_source_parser_architecture_audit_smoke_test.py`
3. `apexforge/p11_5f_opt_in_narrative_source_parser_smoke_test.py`
4. `docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_ARCHITECTURE_AUDIT.md`
5. `docs/p11/P11_5F_OPT_IN_NARRATIVE_SOURCE_PARSER_CONTRACT.md`

## Purpose

P11.5F-B implements one dedicated, explicit parser that converts narrative
source text into the immutable P11.5E source AST.

Opt-in parser != ordinary operational parser.

## Public API

`apexforge/language/narrative_parser.py` exports exactly:

- `NarrativeSourceParseError`
- `parse_narrative_source`

The entry point accepts one source string and optional source name and returns
one exact `NarrativeSourceDocument`.

## Private scanner

The module owns a private scanner for identifiers, quoted strings, lowercase
booleans, punctuation, and end of source.

Supported string escapes are `\"`, `\\`, `\n`, `\r`, and `\t`.

Narrative keywords remain contextual identifier text. The ordinary lexer token
inventory is unchanged.

## Accepted grammar

One document contains exactly one story root.

The parser accepts character and scene declarations, dialogue blocks, choice
blocks with one or more paths, perspective blocks, timeline blocks,
narrative-state blocks, and continuity blocks.

Dialogue field order is `scene`, `speaker`, `participants`.

Choice field order is `scene` followed by one or more `path` blocks.

Choice-path field order is `destination`, optional `condition`, optional
`consequence`.

Perspective contains `viewpoint`. Timeline contains a non-empty `scenes` list.
Narrative state contains zero or more `fact` declarations. Continuity contains
zero or more `require` declarations.

## Source AST construction

Parsing creates only exact P11.5E `NarrativeSource*` records.

The parser preserves exact names, scalar forms, expected reference kinds,
source order, duplicate evidence, and complete source provenance.

References are not resolved during parsing.

## Syntax diagnostics

Every syntax failure raises `NarrativeSourceParseError` carrying one exact
`BuildDiagnostic` with severity `error`, stage `parse`, code
`APX-NARRATIVE-SYNTAX`, a precise source span, and a deterministic message.

The parser reports the first deterministic syntax failure and performs no
recovery.

## Separation boundary

P11.5F-B performs parsing only.

It does not resolve names, lower into P11.5B semantic records, construct the
P11.5C graph, call P11.5D validation, project semantic findings, select choice
paths, execute timelines, mutate runtime state, or render prose.

## Frozen compatibility

P11.5F-B makes no changes to the frozen narrative source AST, source and
diagnostic infrastructure, ordinary lexer and parser, compiler, project
system, semantic model, graph builder, validator, AIR, artifact v1, runtime,
CLI, language server, VS Code, or Visual Studio.

## Acceptance contract

P11.5F-B passes when the P11.5E freeze remains authoritative, exactly five
reviewed files are owned, complete valid narrative source parses
deterministically, source order and duplicate evidence remain observable,
source spans are exact, malformed source yields deterministic syntax
diagnostics, frozen operational files remain unchanged, and tests do not
mutate repository state.
