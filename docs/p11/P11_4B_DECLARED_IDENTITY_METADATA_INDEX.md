# P11.4B Declared Identity Metadata Index

## Scope and controlling architecture

P11.4B implements the metadata-only recommendation from
`P11_4A_IDENTITY_NESTING_ARCHITECTURE_AUDIT.md`. It adds a deterministic,
read-only description of successful project declarations that the compiler
already recognizes. It does not introduce a naming subsystem and does not
change the accepted P11.3 module, document-graph, ownership, visibility,
linking, validation, or execution contracts.

The implementation changes only `language.identities` and the project-build
integration in `language.project`. The lexer, parser, compiler lowering,
linker, validator, AIR model, artifact serializer, manifest, CLI, runtime,
language server, VS Code integration, and Visual Studio integration are not
modified.

## Exact public metadata model

`language.identities` exports exactly two frozen dataclasses:

```text
ProjectDeclaredIdentity(
    kind: str,
    declared_name: str,
    current_air_id: str,
    source_name: str,
    module_name: Optional[str],
    qualified_display_name: str,
    span: SourceSpan,
)

ProjectIdentityIndex(
    identities: tuple[ProjectDeclaredIdentity, ...] = (),
)
```

The field order is part of the P11.4B contract. The fields mean:

| Field | Exact meaning |
| --- | --- |
| `kind` | The existing successful project declaration family. It is exactly `directive` or `function`. |
| `declared_name` | Exact identifier spelling from the matching declaration `SourceMapEntry.reference`. |
| `current_air_id` | The existing AIR value, exactly `directive:<declared_name>` or `function:<declared_name>`. It is a compatibility reference, not a new canonical identity. |
| `source_name` | Exact physical source-unit name already used by the build and span. |
| `module_name` | Exact validated module spelling in module mode, or `None` in legacy mode. |
| `qualified_display_name` | Non-resolving presentation metadata: the declared name in legacy mode, or `<module_name>.<declared_name>` in module mode. |
| `span` | Existing source span of the declaration entry. It must belong to `source_name`. |

Constructor validation rejects unsupported kinds, invalid declared
identifiers, a `current_air_id` that differs from the existing kind/name AIR
ID, blank sources, invalid module names, a display projection inconsistent
with the other fields, non-`SourceSpan` values, and source/span mismatches.
Validation does not normalize or rewrite a supplied AIR ID.

There is deliberately no `canonical_id`, alias, namespace, owner identity,
parent identity, visibility, scope, export, entry, collision result,
specialization, or resolver field.

## Creation and storage

`ProjectBuilder._build_declaration_metadata` creates ownership and identity
metadata together while each per-source `CompiledSource`, its `SourceMap`, and
the exact source-to-module mapping are available. It does not reparse source
and does not reconstruct declaration provenance from flattened linked AIR.

For each source, the builder first obtains the existing directive and function
AIR IDs from that source's compiled `AIRProgram`. A source-map entry contributes
metadata only when its kind is `directive` or `function` and its AIR ID exists
in the matching compiled collection. The existing source-map reference
supplies `declared_name`; the source map supplies the span; and the current
module graph supplies the optional exact module name.

Each successful `ProjectDeclarationOwner` therefore has one corresponding
`ProjectDeclaredIdentity`. A compiler injected into `ProjectBuilder` that
returns a bare `AIRProgram` has no source map, so neither ownership nor identity
metadata is fabricated.

The completed `ProjectIdentityIndex` is returned on `ProjectBuild.identity_index`.
That field is appended after `declaration_ownership`, has an empty default
factory, and has `compare=False`. Existing positional construction remains
valid, manual builds receive an empty index by default, and project equality
does not acquire metadata sensitivity.

Failed builds do not expose a partial `ProjectBuild` or partial index.

## Supported declaration families

The index contains only successful top-level project declarations:

- ordinary directives;
- ordinary functions; and
- generic function declarations, represented once as their existing
  `function:<name>` declaration.

P11.2B headerless sequential directives each receive a record with
`module_name=None`. Module-mode declarations retain the exact module spelling.

The index does not contain parsed-only workflows, authorities, principals, or
roles. It also does not promote states, events, causes, paths, requirements,
parameters, local bindings, type parameters, invocations, calls, conditionals,
synthetic principals, or synthetic authority checks into project declarations.
Generic specialization keys, specialization-closure nodes, host generics,
lowered synthetic functions, and lowering bindings are excluded.

## Deterministic ordering

`ProjectIdentityIndex` converts its input to a tuple and sorts every record by:

1. `current_air_id`;
2. `source_name.casefold()`;
3. exact `source_name`;
4. span start offset;
5. span end offset;
6. `kind`;
7. whether `module_name` is non-`None`, with legacy first;
8. exact module name, using an empty string only as the `None` sort proxy;
9. exact `declared_name`; and
10. exact `qualified_display_name`.

This extends the P11.3D ownership order without changing it. Input mapping
order, module dependency traversal, and repeated collection do not change the
index result. Equal AIR IDs and equal display projections remain separate
records; no dictionary overwrite or winner selection occurs.

## Read-only inspection

The index exposes these exact-case queries:

```text
for_source(source_name)
for_module(module_name)
find_all(kind, declared_name)
find_current_air_id(current_air_id)
find_qualified_display_name(qualified_display_name)
```

Every query returns a tuple in canonical index order. Unknown valid values
return `()`. Non-string inputs raise `TypeError`, blank strings raise
`ValueError`, and the `kind` argument must be exactly `directive` or
`function`. Queries do not trim nonblank values.

Both dataclasses are frozen, and collection storage and query results are
tuples. Consumers can inspect records but cannot mutate the index through its
public model.

## Identity-preservation guarantee

`current_air_id` copies the already-created AIR ID bit for bit. The record
constructor requires it to be the current kind/name ID and never generates a
qualified, normalized, prefixed, hashed, or replacement value. The builder
does not write metadata back to AIR.

Consequently:

- linked directive and function IDs remain globally flat and module-unaware;
- member, principal, authority-check, and source-map sidecar IDs remain exact;
- generic declarations remain `function:<name>`;
- generic keys remain forms such as `Identity<int>`;
- lowered generic targets retain their established deterministic synthetic
  IDs;
- short and canonical entry handling remains exact;
- runtime lookups, traces, and diagnostics retain existing IDs; and
- artifact v1 serializes the same AIR and contains no identity-index field.

Focused tests compare identity records directly with AIR, source-map, and
ownership values; verify exact generic and duplicate diagnostic IDs; and
compare AIR projections and artifact bytes before and after metadata queries.

## Explicitly absent metadata

P11.4B does not fabricate facts that the current compiler does not establish.
In particular, these values are absent rather than inferred:

- aliases and alias targets;
- resolvable qualified names;
- canonical replacement IDs;
- namespaces;
- declaration parents;
- declaration or lexical scopes;
- nested declaration relationships;
- exports, re-exports, or visibility decisions;
- ambiguity candidate sets or collision winners;
- composite declaration identities;
- generic specialization ownership; and
- entry eligibility or entry selection results.

`qualified_display_name` is the one presentation projection authorized by
P11.4A. It is not source syntax, not an alias, not a lookup key, not a
namespace, not an AIR ID, and not evidence that two same-name declarations can
coexist.

## Index boundary versus resolver boundary

The metadata index answers factual filtering questions over declarations that
already survived the existing build pipeline. It does not answer semantic
questions such as which declaration a reference denotes, which imports make a
candidate visible, whether a spelling is ambiguous, which duplicate wins, or
which directive is an entry.

In particular, `find_qualified_display_name` is an exact metadata filter. Its
name does not make the display value resolvable. Multiple matches are returned
unchanged and in deterministic order. The index never invokes the linker,
visibility validator, entry resolver, compiler, or runtime.

A future resolver may consume immutable identity, ownership, document, and
module facts. It must not mutate this index or reinterpret display text as a
canonical declaration identity.

## Boundary to later naming and nesting stages

P11.4B adds no syntax and does not relax the current globally flat AIR/linker
collision model. Qualified references, qualified entries, aliases,
namespaces, duplicate adjudication, ambiguity diagnostics, and same-name
coexistence remain later naming work.

There is no `parent_identity` because successful directives and functions
cannot currently nest. Directive members remain their existing structural AIR
forms with inconsistent global/cause-local identity boundaries. Adding a
parent relation, treating a module header as syntax nesting, or promoting
members would require a separately authorized grammar, scope, diagnostic,
AIR, runtime, and tooling contract.

## Behavioral non-effects and non-goals

P11.4B does not change lexing, parsing, diagnostics, compilation, linking,
validation, generic inference, specialization, closure, lowering, dispatch,
module-source cardinality, P11.2B behavior, entry selection, artifact schema,
manifest schema, CLI commands or output, runtime behavior, LSP behavior, VS
Code behavior, or Visual Studio behavior.

It adds no cache, incremental compiler, package behavior, resolver, registry,
parallel symbol table, placeholder alias support, placeholder nesting support,
or placeholder implementation for a later roadmap stage.

## Test coverage

`apexforge/p11_4b_declared_identity_metadata_smoke_test.py` is independently
runnable with UTF-8 mode and bytecode writes disabled. Its structural and
behavioral assertions cover:

- exact public exports, dataclass fields, constructor validation, frozen
  records, tuple storage, ordering, query validation, exact-case matching, and
  duplicate/display-collision retention;
- deterministic legacy, module, reversed-input, and repeated collection;
- directives, functions, generic declarations, nested-member exclusion, and
  one-to-one correspondence with declaration ownership;
- exact AIR IDs, AIR serialization before/after queries, bare-AIR compiler
  behavior, manual `ProjectBuild` compatibility, and empty defaults;
- generic inference, specialization closure, lowering, and exclusion of
  specialization/lowered identities;
- unchanged duplicate-link diagnostics, direct/transitive/legacy visibility,
  P11.2B and module-source boundaries, entry selection, and runtime execution;
- artifact v1 byte/fingerprint stability, manifest schema 1, exact CLI output,
  language-server and Visual Studio frozen fingerprints, and absence of index
  consumption from those tooling paths; and
- external context-managed temporary fixtures, repository-status and
  working-directory preservation, and blocked socket creation.

The complete regression harness remains the compatibility authority beyond
this focused slice.

## Historical regression-contract alignment

P11.4B corrected two historical smoke-test wrapper assumptions without
relaxing their production contracts. The P11.3D test had required
`declaration_ownership` to remain the final `ProjectBuild` field. That
terminal-position check prevented any later additive metadata even though the
P11.3D contract is the established relative order, defaults, `compare=False`
behavior, and positional/equality compatibility of `document_graph` and
`declaration_ownership`. The corrected assertion verifies those properties,
including construction through the full pre-P11.4B positional field set,
while allowing later metadata fields to follow.

The published P11.4A audit smoke test had also required an initially clean
tracked tree and index. That publication-gate assumption could not run against
legitimate downstream changes. Its regression invariant now captures complete
Git status and repository bytecode state before executing the audit checks and
requires exact equality afterward. Working-directory and network guards remain
in place. The test therefore continues to detect tracked, staged, untracked,
or bytecode mutation caused by its own execution without rejecting pre-existing
authorized work.

No historical parser, compiler, AIR, linker, diagnostic, module, entry,
artifact, runtime, CLI, language-server, or Visual Studio behavior was relaxed.
Both historical smoke tests remain discovered and executed by the complete
regression harness.

## Known limitations and remaining risk

The index exists only after a successful build, so duplicate declarations are
representable by the public collection model but not returned from a failed
canonical build. Same-kind declarations remain unable to coexist even when
their modules differ. Module-name uniqueness remains case-folded while module
lookup remains exact-case. Display projections can collide and must not be
used as resolver keys. Parsed-only forms and nested members remain outside the
successful project declaration set. Artifact v1 and tooling intentionally
cannot inspect the index.

The builder depends on the canonical compiler invariant that a recognized
declaration source-map entry carries the exact declared name in `reference`.
An injected compiler returning bare AIR remains supported with an empty index;
an injected `CompiledSource` that fabricates inconsistent declaration
source-map facts is rejected by the metadata constructor rather than silently
inventing a name.

## Recommended next substage

P11.4C should be a narrowly scoped, audit-first resolver contract over the
immutable identity, ownership, document, and module facts. It should specify
candidate sets, exact case behavior, qualification representation, collision
versus use-site ambiguity, deterministic diagnostic ordering, generic-owner
binding, entry migration constraints, and tooling implications before any
syntax or AIR migration is authorized.

P11.4C should not begin by changing AIR IDs, artifact v1, runtime lookup,
aliases, namespace grammar, declaration nesting, export policy, CLI behavior,
or language-server behavior. Those changes require explicit later slices and
tested migration contracts.
