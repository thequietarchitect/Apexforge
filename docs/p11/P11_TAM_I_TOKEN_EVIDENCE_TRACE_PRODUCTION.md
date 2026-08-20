# P11-TAM-I â€” Token Evidence Trace Production

## Purpose

P11-TAM-I adds deterministic TAM projection for the canonical public
`language.lexer.Token` evidence surface.

This closes the final dedicated trace domain in the ten-domain Compiler TAM
taxonomy.

The slice is observational. TAM-I does not invoke the lexer, tokenize source,
parse source, reconstruct source, classify editor text, or perform semantic
execution.

## Predecessor

P11-TAM-I begins from:

`afp-p11-tam-h-freeze`
â†’ `cdd23d15a9cb699e11c2e82278371652a4439f8d`

P11-TAM-B through P11-TAM-H remain predecessor capabilities.

## Canonical token owner

The ordinary ApexForge lexer publicly exports:

`Token(kind: str, value: str, span: Optional[SourceSpan] = None)`

with exact dataclass fields:

- `kind`;
- `value`;
- `span`.

`language.parser` consumes this public `Token` type directly.

Therefore the canonical TAM token evidence owner is
`language.lexer.Token`.

## Excluded token-like representations

P11-TAM-I does not absorb every object whose name contains "token".

In particular:

- `language.narrative_parser._Token` is parser-private;
- `language.semantic_decision_parser._Token` is parser-private;
- language-server completion `_Token` values are editor/completion internals;
- Visual Studio `SyntaxToken` values are editor-classification records.

Those are distinct owner-specific representations and are not duplicated into
the core TAM token domain.

## Production API

P11-TAM-I introduces:

- `trace_record_from_token_evidence(token, token_index=...)`;
- `trace_map_from_token_evidence(tokens)`.

The map producer requires an exact tuple of exact
`language.lexer.Token` values and preserves lexical input order.

## Token-domain mapping

Every record uses the existing canonical TAM `token` domain.

For each token:

- `producer="language.lexer"`;
- `owner="language.lexer"`;
- `representation="token"`.

## Token identity preservation

A lexical token has no AIR-style or declaration-style canonical identity.

TAM therefore does not fabricate `TraceRecord.canonical_identity`.

The deterministic TAM-local `TraceIdentity` preserves:

- caller-provided token index;
- exact token `kind`;
- exact token `value`;
- explicit source-span presence/absence;
- source name and start/end line/column when a span exists.

The token index preserves the caller's lexical ordering context. The source
location ensures identical kind/value tokens at distinct positions remain
distinct observations even when projected at the same explicit index.

## Source-span boundary

When `Token.span` is a real `SourceSpan`, TAM stores that exact object in
`TraceRecord.source_span`; it does not rebuild or normalize the span.

When `Token.span is None`, TAM records `source_span=None` and fabricates no
location.

EOF is ordinary lexer evidence and remains observable with its zero-width
source span.

## Forbidden behavior

`tam.production` must not invoke or acquire ownership of:

- `lex`;
- `scan_string`;
- lexer keyword/punctuation inventories;
- lexer errors;
- ordinary parser execution;
- narrative parser execution;
- semantic-decision parser execution;
- source reconstruction;
- editor completion scanners;
- Visual Studio/VS Code syntax classification.

Therefore:

- `LEXING_EXECUTION=NONE`;
- `TOKENIZATION_EXECUTION=NONE`;
- `PARSING_EXECUTION=NONE`;
- `SOURCE_RECONSTRUCTION=NONE`;
- `CLI_LSP_INTEGRATION=NONE`;
- `SEMANTIC_EXECUTION=NONE`.

## Fixture rule

The P11-TAM-I smoke test may call the frozen ordinary `lex` function only to
obtain real already-produced `Token` values for the test fixture.

That fixture execution does not occur in `tam.production` and grants TAM no
lexer ownership beyond observing the resulting token records.

## Completion condition

P11-TAM-I is complete when:

- TAM-H freeze ancestry is proven;
- the canonical public `Token(kind, value, span)` contract is preserved;
- real lexer-produced tokens are consumed;
- kind, value, exact source span, EOF, and token order are preserved;
- span-less tokens fabricate no source location;
- no canonical identity, provenance, or TAM graph link is fabricated;
- parser-private and editor token representations remain distinct owners;
- no lexing, tokenization, parsing, source reconstruction, editor
  classification, CLI/LSP integration, or semantic execution occurs in TAM
  production;
- frozen lexer/source/parser/editor and prior TAM owners remain unchanged;
- TAM predecessor and SRC durable regressions remain green.

After P11-TAM-I, all ten canonical TAM domains have dedicated production
coverage and the next step is TAM integration/final freeze.