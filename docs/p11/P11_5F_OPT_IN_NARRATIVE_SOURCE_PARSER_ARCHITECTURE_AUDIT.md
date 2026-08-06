# P11.5F-A Opt-In Narrative Source Parser Architecture Audit

## Status

P11.5E is the frozen source-AST predecessor.

The controlling annotated tag is `afp-p11.5e-freeze`, resolving to:

`eba9a27a34563a8df5f77b796c82b032ab2b0485`

The original P11.5F-A audit established the parser boundary before production
implementation. The reviewed P11.5F-B successor now implements that boundary
through one dedicated production module.

## Core separation

Opt-in parser != ordinary operational parser.

No changes to language/lexer.py.

No changes to language/parser.py.

The parser is invoked only through an explicit narrative API. Ordinary
compilation, project loading, runtime execution, diagnostics, formatting, and
editor behavior remain unchanged.

## Production boundary

P11.5F-B adds one dedicated production module:

`apexforge/language/narrative_parser.py`

It publicly exports exactly:

- `NarrativeSourceParseError`
- `parse_narrative_source`

All scanner tokens, scanner helpers, parser state, and grammar helpers remain
private.

## Scanner and grammar

The module owns one private narrative scanner.

The scanner recognizes identifiers, quoted strings, lowercase booleans,
braces, brackets, commas, colons, dots, equals signs, and end of source.

Contextual narrative keywords are recognized from exact identifier text. The
ordinary lexer is not imported or changed.

One source document contains exactly one story root.

The grammar supports characters, scenes, dialogues, choices and paths,
perspectives, timelines, narrative states and facts, and continuity
requirements.

Field order is fixed in this minimal parser contract.

## References and provenance

The parser records unresolved references and their expected kinds.

It preserves source order and duplicates.

Every produced record retains canonical `SourceText` and `SourceSpan`
provenance for document, story, keywords, names, fields, references, scalars,
labels, assertions, and complete blocks.

## Syntax failure contract

`NarrativeSourceParseError` contains one canonical `BuildDiagnostic`.

The diagnostic uses stage `parse`, code `APX-NARRATIVE-SYNTAX`, a precise
source span, and a deterministic message.

The parser reports the first deterministic syntax failure.

## Parsing boundary

Parsing creates only `NarrativeSource*` records.

No semantic lowering.

No graph construction.

No narrative validation.

The parser does not resolve names, infer contradictions, select paths, execute
timelines, mutate state, or render prose.

## Compatibility boundary

P11.5F has:

- no compiler integration;
- no project integration;
- no AIR integration;
- no artifact integration;
- no runtime integration;
- no CLI integration;
- no language-server integration;
- no VS Code integration;
- no Visual Studio integration.

The ordinary lexer, parser, compiler, project system, runtime, and editor
tooling remain byte-identical to the P11.5E freeze.

## Acceptance contract

The reviewed P11.5F-A/P11.5F-B candidate passes when:

- the annotated P11.5E freeze remains authoritative;
- exactly five reviewed files are owned;
- one dedicated parser module exposes exactly two public names;
- valid source parses into the immutable source AST;
- source order and duplicates are preserved;
- unresolved references remain passive evidence;
- syntax failure behavior is deterministic;
- frozen operational files remain unchanged;
- tests do not mutate repository state.
