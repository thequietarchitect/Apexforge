# P11.12B â€” Minimal Immutable Incremental-Cache Model

## Purpose

P11.12B introduces the smallest production model required to express the
three-layer P11.12 cache without integrating caching into any existing owner.

B defines:

- the cache schema version;
- the canonical layer identifiers;
- exact SHA-256 fingerprints;
- structured cache identities;
- ordered dependency references;
- immutable cache entries;
- deterministic identity-key derivation.

B performs no lookup, storage, persistence, compilation, semantic evaluation,
project building, invalidation traversal, or runtime execution.

## Predecessor

P11.12B begins from:

`afp-p11-12a-freeze`

at the exact P11.12A architecture-audit commit.

The A audit remains the ownership and correctness authority for P11.12.

## Package

The new production package is:

`apexforge/incremental_cache`

Its B public surface contains exactly nine symbols:

- `CACHE_SCHEMA_VERSION`;
- `CACHE_LAYER_IDS`;
- `CACHE_FINGERPRINT_ALGORITHM`;
- `CacheFingerprint`;
- `CacheDependency`;
- `CacheIdentity`;
- `CacheEntry`;
- `cache_fingerprint`;
- `cache_identity_key`.

No existing compiler, project, runtime, tooling, semantic, TAM, or TAP package
is modified by B.

## Schema and layers

The cache schema is:

`CACHE_SCHEMA_VERSION = 1`

The canonical ordered layer tuple is:

`("capture", "resonance", "stability")`

Layer order follows the P11.12 roadmap and is data, not execution authority.

## Fingerprints

`CacheFingerprint` is a frozen dataclass containing:

- `algorithm`;
- `value`.

B supports only the canonical algorithm:

`sha256`

The value is exactly 64 lowercase hexadecimal characters.

`cache_fingerprint(payload: bytes)` fingerprints exact bytes.

It rejects text and other implicit encodings. Owners or later integration
layers must explicitly produce the exact canonical bytes whose identity they
intend to fingerprint.

This preserves the P11.12A rule that exact source bytes are the Capture anchor
while permitting higher layers to fingerprint their own canonical
representations.

## Structured identity

`CacheIdentity` is a frozen dataclass containing:

- `schema_version`;
- `layer_id`;
- `artifact_kind`;
- `owner`;
- `subject`;
- `input_fingerprint`;
- `configuration_fingerprint`;
- ordered `dependencies`.

This directly implements the A finding that a bare source hash is insufficient
for higher-layer validity.

The semantic owner field records who produced the value. It does not transfer
that ownership to the cache.

The subject is canonical owner-defined identity text. B does not normalize,
resolve, or infer subjects.

## Configuration identity

Every cache identity contains a `configuration_fingerprint`.

If an owner has no output-affecting configuration, later integration may use
the SHA-256 fingerprint of an explicitly defined empty canonical byte
representation.

B does not guess which configuration fields belong to each owner.

That mapping is introduced by the layer-specific integration slices.

## Dependencies

`CacheDependency` is a frozen pair of:

- upstream `cache_key`;
- upstream artifact `fingerprint`.

Dependencies are an exact tuple.

Their order is preserved and contributes to the derived cache key.

Duplicate upstream cache keys are rejected because one structured identity
should not represent the same dependency twice ambiguously.

The dependency object deliberately refers to canonical keys and fingerprints
rather than embedding recursive cache identities.

## Canonical cache key

`cache_identity_key(identity)` serializes only the structured identity fields
to deterministic compact UTF-8 JSON with sorted mapping keys and then returns
lowercase SHA-256 hex.

The dependency array remains ordered.

Therefore changing any of the following naturally changes the key:

- schema;
- layer;
- artifact kind;
- owner;
- subject;
- input fingerprint;
- configuration fingerprint;
- dependency identity;
- dependency artifact fingerprint;
- dependency order.

No timestamp, mtime, process state, random value, or memory address
participates.

## Entry wrapper

`CacheEntry` is frozen and contains:

- `identity`;
- `artifact_fingerprint`;
- `value`.

The `cache_key` property derives the key from `identity`.

The entry preserves the exact owner-produced `value` reference.

B deliberately does not deep-copy, serialize, or reinterpret that value.

The frozen wrapper prevents cache metadata rebinding, but the semantic
immutability of the owner value remains the owner's contract.

Layer-specific slices must only admit values through explicit integration
contracts. This is especially relevant to formatting output, whose nested
mapping values are not automatically deep-frozen merely because an outer tuple
exists.

## No operational cache yet

P11.12B does not provide:

- cache store;
- cache lookup;
- cache hit/miss;
- eviction;
- invalidation traversal;
- disk persistence;
- file format;
- project-builder integration;
- CLI integration;
- background cache warming;
- semantic reconstruction;
- runtime execution.

Those are intentionally outside the minimal model.

## No persistence

No `pickle`, SQLite, shelve, temporary-file, or filesystem persistence is
introduced.

The B model is pure in-memory data and deterministic key computation.

Persistence may only be considered after cached and uncached semantic
equivalence is established.

## No time-based correctness

B has no timestamp or TTL fields.

A stale semantic product becomes invalid when a content/configuration/dependency
identity changes.

Storage reclamation is separate from semantic validity.

## Ownership boundary

The cache owns:

- cache identity metadata;
- cache artifact fingerprints;
- dependency key metadata;
- later reuse observations.

It does not own:

- lexer tokens;
- parser AST;
- module/document graphs;
- compiler products;
- declaration/identity/resolution indexes;
- TAM;
- narrative semantics;
- Quad-Vector semantics;
- semantic lattice;
- AIR verification;
- execution-plan semantics;
- runtime/session state.

## A-stage compatibility

P11.12A's absence assertion for dedicated cache production is a stage-boundary
proof.

Once B exists, downstream slices protect A through:

- `afp-p11-12a-freeze`;
- frozen A artifact hashes;
- durable ownership rules.

They must not rerun A's obsolete "cache production absent" assertion as a
forward regression.

## P11.12C handoff

P11.12C may build the Capture layer on top of this model.

Its first responsibility is to bind explicit cache identities to existing
Capture owners:

- `LoadedProjectSource` exact bytes;
- exact source SHA-256;
- lexer `Token` tuples;
- formatting output under the formatter contract and options.

C must still leave parser/compiler/project semantics untouched.

## Closure condition

P11.12B is complete when:

- P11.12A freeze ancestry is exact;
- the A audit hashes remain exact;
- the nine-symbol public cache surface is exact;
- all four model dataclasses are frozen;
- fingerprinting is exact-bytes SHA-256;
- structured identity is deterministic;
- ordered dependencies affect identity;
- duplicate dependency keys are rejected;
- owner payload references are preserved;
- no operational cache or persistence exists;
- predecessor semantic owners remain unchanged.