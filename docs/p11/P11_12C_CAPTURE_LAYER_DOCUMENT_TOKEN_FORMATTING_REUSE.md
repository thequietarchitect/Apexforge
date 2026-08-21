# P11.12C â€” Capture-Layer Document, Token, and Formatting Reuse

## Purpose

P11.12C binds the P11.12B immutable cache model to the existing Capture-layer
owners:

- loaded project documents;
- lexer tokens;
- document formatting.

C introduces explicit reuse through an optional single `CacheEntry`.

C does not yet introduce a general cache store, persistence, project-builder
integration, dependency invalidation, TAP observation, semantic evaluation, or
runtime execution.

## Predecessor

P11.12C begins from:

`afp-p11-12b-freeze`

at:

`2de18a85bc2243a9006d1ca87e511f19b84832ac`

The exact B files and hashes remain unchanged.

The top-level `incremental_cache.__all__` B surface also remains unchanged.
C is provided through the explicit module:

`incremental_cache.capture`

## Corrected source-content boundary

The P11.12C read-only audit found an important preexisting loader contract.

`tooling.project_loader.load_project` performs:

1. exact `read_bytes()`;
2. UTF-8 decoding;
3. universal-newline normalization:
   - CRLF â†’ LF;
   - CR â†’ LF;
4. construction of `LoadedProjectSource` with both:
   - normalized `source`;
   - exact `source_bytes`.

Therefore `source_bytes.decode("utf-8")` is not required to equal `source`.

This is intentional and predates P11.12.

The Capture layer preserves both identities instead of collapsing them.

## Raw document identity

A document Capture identity uses:

- layer: `capture`;
- kind: `document`;
- owner: `tooling.project_loader`;
- subject: manifest-relative source name;
- input fingerprint: SHA-256 of exact `source_bytes`;
- configuration fingerprint: SHA-256 of empty canonical bytes.

The cached value is the exact `LoadedProjectSource` reference.

A matching cached document is reused only when the current
`LoadedProjectSource` value equals the cached value. This prevents reuse from
leaking a stale absolute `path` when identical relative content is loaded from
another project root.

Changing only CRLF/LF representation changes the raw-document identity.

## Token identity

Token Capture identity uses:

- layer: `capture`;
- kind: `tokens`;
- owner: `language.lexer`;
- subject: `LoadedProjectSource.name`;
- input fingerprint: SHA-256 of normalized `source` encoded as UTF-8;
- configuration fingerprint: canonical JSON containing
  `inter_directive_line_comments`.

`source_name` is represented by the identity subject rather than duplicated
inside configuration.

This matters because lexer token spans contain source provenance.

Two files that differ only by CRLF versus LF can therefore have:

- different document cache keys;
- identical token cache keys,

provided their manifest-relative source name and lexer configuration are the
same.

That is safe because the lexer receives the normalized source text.

## Token artifact fingerprint

The token artifact fingerprint is SHA-256 over deterministic canonical JSON of
the exact frozen `Token` dataclasses and their nested span data.

The cache does not reinterpret token meaning.

On an exact valid hit, the lexer is not invoked.

A matching identity with an invalid token value or mismatching artifact
fingerprint is treated as unusable and the tokens are reproduced by the
canonical lexer.

## Formatting identity

Formatting Capture identity uses:

- layer: `capture`;
- kind: `formatting`;
- owner: `language_server.formatting`;
- subject: formatter URI;
- input fingerprint: SHA-256 of the exact text argument encoded as UTF-8;
- configuration fingerprint containing:
  - canonical formatter fingerprint;
  - provided `tabSize`, when present;
  - provided `insertSpaces`, when present.

The URI is the subject and is not duplicated into configuration.

Unknown client option keys are not included by C because the frozen formatter
contract identifies client indentation through `tabSize` and `insertSpaces`.
If the formatter contract changes, its fingerprint changes and therefore the
Capture identity changes.

C does not claim that URI currently changes formatted text for every document.
It remains the formatting subject so any URI-sensitive future contract does not
alias unrelated documents.

## Immutable formatting value

The existing formatter returns:

`tuple[dict[str, object], ...]`

The outer tuple is immutable but nested dictionaries are mutable.

P11.12A explicitly prohibited treating that nested structure as deeply
immutable merely because the outer container is a tuple.

C therefore freezes the JSON-safe formatting edit structure recursively with
explicit immutable container tags:

- mapping â†’ tagged tuple containing sorted key/value pairs;
- list/tuple â†’ tagged tuple containing ordered frozen elements;
- scalar â†’ unchanged scalar.

The explicit tags make empty mappings and empty sequences unambiguous. This is
required because a valid idempotent formatter result can be the empty edit
tuple.

The resulting `CacheEntry.value` contains no mutable list or dictionary.

`formatting_edits_from_capture(...)` validates the artifact fingerprint and
rehydrates the canonical `tuple[dict, ...]` owner result for downstream use.

This does not transfer formatting ownership to the cache.

## Explicit reuse boundary

Each Capture operation accepts:

`cached: Optional[CacheEntry] = None`

This is intentionally not a store.

When the supplied entry has the exact expected identity and passes
artifact-integrity validation, the same `CacheEntry` object is returned.

On a miss, mismatch, invalid value, or corrupt artifact fingerprint, the
canonical owner is invoked and a new entry is returned.

C emits no hit/miss observation object yet.

That observation authority belongs to the later invalidation/reuse slice.

## Public Capture surface

`incremental_cache.capture` exports exactly seven operations:

- `document_capture_identity`;
- `capture_document`;
- `token_capture_identity`;
- `capture_tokens`;
- `formatting_capture_identity`;
- `capture_formatting`;
- `formatting_edits_from_capture`.

The B top-level package surface remains untouched.

## No general store

P11.12C adds no:

- dictionary-backed project cache;
- LRU;
- global singleton;
- disk store;
- SQLite;
- pickle;
- cache directory;
- TTL;
- timestamp validity;
- background warmup.

General lookup/storage and dependency invalidation remain later P11.12 work.

## No ProjectBuilder integration

`ProjectBuilder`, `build_project`, compiler owners, runtime owners, and tooling
CLI routes remain unchanged.

P11.12C proves Capture reuse independently before any build path consumes it.

## Determinism and corruption behavior

A Capture entry is reusable only when:

- identity matches exactly;
- the expected value shape is valid;
- its artifact fingerprint matches the cached value.

A corrupt or structurally incompatible cached entry is not reused.

This keeps cache presence from changing owner semantics.

## Real-project acceptance

C tests the existing P11.1B two-source fixture.

For each real loaded source it proves:

- raw document capture;
- token capture;
- formatting capture;
- exact repeated document reuse;
- exact repeated token reuse;
- exact repeated formatting reuse.

## P11.12D handoff

P11.12D may now bind the Resonance layer to existing immutable owner products.

The Capture layer provides the lower-level content identities that can become
ordered dependencies of:

- AST;
- module/document graph;
- project semantic indexes;
- compiler sidecars;
- TAM;
- narrative graph;
- Quad-Vector products;
- semantic lattice products.

D must continue the same rule:

the cache records reuse identity; the original owner retains semantic
authority.

## Closure condition

P11.12C is complete when:

- P11.12B freeze ancestry and hashes remain exact;
- B top-level public surface remains unchanged;
- exact-byte document identity is proven;
- normalized-text token identity is proven;
- newline-equivalent token reuse is proven;
- lexer configuration participates in identity;
- formatting contract/options participate in identity;
- formatting nested mappings are frozen;
- formatting edits round-trip exactly;
- exact cache hits avoid owner invocation;
- corrupt entries are rejected from reuse;
- real-project Capture reuse passes;
- no general store or persistence exists;
- predecessor semantic owners remain unchanged.