# P11.3D Canonical Declaration Ownership Index

## Scope and accepted baseline

P11.3D adds an immutable, in-memory ownership index for the two declaration
families that successfully enter the canonical project AIR pipeline:
directives and functions. It implements the metadata-only foundation
recommended by the accepted P11.3C export and visibility architecture audit at
commit `40a5d21`, starting from required HEAD `37db47b` on branch
`p11.3-modules-imports`.

The accepted P11.3B implementation is `3811b21`, the accepted P11.3A audit is
`697e3b2`, and the frozen P11.2 baseline is
`6b82f797bfd74b01047928638c7cf2538f689485` under tag
`afp-p11.2-freeze`.

This slice records facts already produced by successful per-source compilation.
It does not change grammar, parsing, AIR, linking, validation, runtime, entry
selection, manifests, CLI behavior, artifacts, language-server behavior, or
Visual Studio integration.

## Public model

`language.declarations` exports exactly:

- `ProjectDeclarationOwner`
- `ProjectDeclarationOwnership`

Both are frozen dataclasses. The module is used directly; no package initializer
is changed to re-export the names.

## ProjectDeclarationOwner invariants

`ProjectDeclarationOwner` has fields in this exact order:

1. `kind: str`
2. `air_id: str`
3. `source_name: str`
4. `module_name: Optional[str]`
5. `span: SourceSpan`

The record enforces these invariants:

- `kind` is exactly `directive` or `function`.
- A directive ID has the current canonical short form
  `directive:<identifier>`.
- A function ID has the current canonical short form
  `function:<identifier>`.
- The short identifier uses the current ASCII source identifier shape and is
  neither module-qualified nor specialized.
- `source_name` is a nonblank string.
- `module_name` is either `None` or a nonblank string.
- `span` is a `SourceSpan` and `span.source_name` exactly equals
  `source_name`.
- Source and module names are stored exactly as supplied. Construction does not
  trim, case-fold, path-normalize, qualify, or otherwise rewrite them.

The record has no export, public/private, visibility, alias, namespace,
qualified-identity, reference-edge, AIR-schema, artifact, or runtime field.

## ProjectDeclarationOwnership invariants

`ProjectDeclarationOwnership` has one field:

```text
declarations: tuple[ProjectDeclarationOwner, ...] = ()
```

Construction converts the input collection to a tuple, rejects any non-owner
element, and sorts all owners into canonical order. Equal `air_id` values are
allowed and retained as distinct records. The collection does not build a
single-value dictionary, overwrite owners, resolve declarations, select a
winner, infer visibility, or reject ambiguity.

The frozen record plus its tuple storage make the collection immutable.

## Canonical ordering

Owners are ordered by this exact key:

1. `air_id`
2. `source_name.casefold()`
3. exact `source_name`
4. `span.start.offset`
5. `span.end.offset`
6. `kind`
7. whether `module_name` is non-`None` (`None` sorts first)
8. exact `module_name`, using the empty string only as the sort representation
   for `None`

The final two components are deterministic tie-breakers only. Stored source and
module spellings are never rewritten. This order is independent of source
mapping insertion order, module dependency order, compilation order, linked AIR
order, and filesystem enumeration order.

## Query semantics

The collection exposes three read-only queries:

- `for_source(source_name)`
- `for_module(module_name)`
- `find_all(air_id)`

Each returns a tuple of owners in canonical collection order. Matching is exact
and case-sensitive. A valid but unknown string returns `()`. A non-string value
raises `TypeError`; an empty or whitespace-only string raises `ValueError`.
Queries do not trim a nonblank query, mutate the collection, compile, link,
resolve, validate, grant visibility, select an entry, execute, or serialize.

Legacy records are discoverable through `for_source` and `find_all`.
`for_module` does not invent a module identity for them.

## Legacy projection

In a headerless legacy project, `ProjectBuilder` examines every per-source
`CompiledSource` while its physical grouping still exists. Each source-map entry
whose kind is `directive` or `function` and whose ID belongs to the matching
per-source AIR declaration becomes one owner.

This includes every directive in a P11.2B multi-directive physical source and
ordinary legacy function declarations. Every legacy owner has
`module_name=None`. Exact physical source names and existing top-level
declaration spans are retained.

States, events, causes, paths, principals, authority checks, requirements,
actions, calls, and runtime records remain outside the ownership index.

## Module-mode projection

In explicit module mode, the same per-source compiled/source-map evidence is
combined with the already validated `ModuleRecord.source_name ->
ModuleRecord.name` mapping. The exact case-preserved module spelling becomes the
owner's `module_name`.

The index does not reparse source text and does not derive ownership from the
final flattened AIR order. Module dependency order may differ from canonical
owner order without changing either contract.

One ordinary top-level declaration per module source remains the parser/project
boundary. The ownership index does not enable multiple module declarations.

## Generic declaration handling

A generic source function produces exactly one owner of kind `function` for its
current declaration ID, such as `function:Identity`. Its existing type
parameters retain their `function:Identity` owner in the type system.

Inferred or explicit specializations such as `Identity<int>`, specialization
closure entries, and generated/lowered concrete targets do not become project
declaration owners. Generic inference, closure, specialization, and lowering
remain unchanged.

## Duplicate-owner retention

`ProjectDeclarationOwnership` deliberately retains multiple records with the
same `air_id`. It is an ownership projection, not a uniqueness table or
resolver. This avoids the overwrite behavior of the temporary module-visibility
owner dictionary and preserves enough metadata for future identity work.

Actual duplicate projects still proceed to `AIRProgramLinker`. The linker
remains the sole duplicate-diagnostic authority and continues to emit the
existing `APX-LINK-001` stage, code, message, primary span, related spans,
`air_id`, and deterministic ordering. The index does not reject, resolve,
preempt, restage, or reorder duplicates.

## ProjectBuild integration

`ProjectBuild` appends this field after `document_graph`:

```text
declaration_ownership: ProjectDeclarationOwnership
```

It uses `default_factory=ProjectDeclarationOwnership` and `compare=False`.
Every pre-existing positional field retains its slot. Existing manual
positional construction that omits this field receives an empty immutable
compatibility default. Equality remains based on the fields that preceded the
P11.3B document graph and P11.3D ownership projection.

Canonical `ProjectBuilder.build` output supplies the populated projection after
all sources compile and before visibility validation and linking discard the
per-source grouping.

## ModuleGraph boundary

`ModuleGraph` remains exactly `modules` plus dependency-first `order`. It gains
no declaration, export, visibility, reference, namespace, qualification, or
ownership field. Its legacy empty representation, `is_legacy`, lookup,
direct-import query, source order, equality, and deterministic ordering remain
unchanged.

## ProjectDocumentGraph boundary

`ProjectDocumentGraph` remains a physical-document and dependency graph. Its
records, resolved import edges, canonical physical source order,
dependency-first order, and dependency queries remain unchanged.

The declaration ownership index is a separate `ProjectBuild` projection.
Document dependencies do not become declaration edges, export edges, reference
edges, or visibility results. Direct and transitive document queries do not
grant declaration access.

## Linker and diagnostics preservation

P11.3D adds no diagnostic and changes no diagnostic stage. It preserves:

- reachable `APX-MODULE-001` through `APX-MODULE-009` behavior;
- the preempted module-after-import `APX-MODULE-003` branch;
- `APX-LINK-001` duplicate authority and spans;
- parse, compile, validation, and entry diagnostics;
- diagnostic severity, code, message, primary span, related spans, `air_id`,
  and canonical ordering.

No linker, validator, parser, compiler, diagnostic, or AIR production file is
changed by this slice.

## Visibility non-enforcement

The ownership index is not consumed by `validate_module_visibility`. Existing
module behavior remains same-module plus direct-import-only for known directive
invocations and function calls. A transitive dependency does not grant access.
Legacy supported declarations remain project-wide visible.

Queries can return an owner that is not visible from a given source because a
query reports metadata only. Querying an owner never grants access, selects a
candidate, resolves ambiguity, or changes runtime authority.

There is no implicit export set. Existing direct-import access is not described
or stored as export policy.

## CLI and manifest compatibility

Manifest schema 1 remains unchanged. Source lists and entry spelling remain
unchanged. CLI `check`, `run`, and `build` consume the same project pipeline and
produce their established output without mentioning declaration ownership,
exports, visibility, modules, or qualification.

Short and canonical directive entry spellings remain supported. Module-qualified
entries remain unsupported. Imports do not broaden runtime authority.

## Artifact v1 compatibility

Artifact v1 retains exactly `schema`, `project`, `air`, and `fingerprint` at its
top level. The ownership index is not passed to AIR serialization or artifact
construction. It adds no declaration-owner, export, visibility, module,
qualification, module-graph, or document-graph field.

Artifact source order, exact-byte source hashes, linked AIR order, canonical
JSON, bytes, and SHA-256 fingerprint remain unchanged. Accessing any ownership
query has no artifact side effect.

## Language-server non-integration

The language server and Visual Studio integration do not import or consume the
ownership index. Syntax diagnostics, formatting, document symbols, hover,
same-document definition/references/rename, workspace symbols, and Visual
Studio diagnostics remain at their existing boundaries.

There is no export awareness, project ownership lookup, cross-file declaration
resolution, reference discovery, rename, or module-qualified navigation in this
slice.

## Frozen compatibility guarantees

P11.3D preserves:

- frozen P10 and P11.2 grammar, compiler, runtime, authority, diagnostic, CLI,
  artifact, and tooling behavior;
- exact module-header masking and source spans;
- legacy source ordering and P11.2B multi-directive support;
- one ordinary declaration per module source;
- exact-case import resolution and case-folded source/module uniqueness;
- dependency-first module compilation and linked AIR order;
- current short, globally unqualified AIR identities;
- direct-only module visibility and legacy global visibility;
- generic declaration, inference, specialization, closure, and lowering;
- linker and validator authority;
- short/canonical entry selection;
- manifest schema 1, artifact v1, CLI output, language-server behavior, and
  Visual Studio integration.

## Explicit non-goals

P11.3D adds no export keyword, public/private modifier, export list, implicit
export set, wildcard export, re-export, alias, namespace, qualified identity,
qualified reference, qualified entry, visibility enforcement, ambiguity
resolution, local-shadowing rule, declaration-reference graph, reverse
dependency graph, nested declaration, multiple declarations in module sources,
new AIR field, artifact field, manifest field, CLI feature, language-server
feature, Visual Studio feature, runtime behavior, authority behavior, validator
behavior, linker behavior, diagnostic, P11.4 identity work, P11.3E behavior, or
later roadmap work.

Workflow, authority, principal, role, identity, state, event, cause, path,
generic specialization, lowered target, principal check, authority check, and
runtime records are not promoted into ownership kinds.

## Known limitations

- Identities remain globally short, so same-kind declarations with equal names
  still collide at link time even when they have different module owners.
- The index reports ownership but cannot represent qualified identity,
  imported ambiguity, aliases, exports, re-exports, or visibility decisions.
- Module uniqueness remains case-folded while module import lookup remains
  exact-case.
- Manual `ProjectBuild` construction receives the empty compatibility default.
- The injectable `ProjectBuilder` compatibility adapter accepts a bare
  `AIRProgram`; when an injected compiler supplies no `SourceMap`, no physical
  span exists and the builder does not fabricate or reparse ownership records.
- Failed builds expose no partial `ProjectBuild`, including builds that reach
  the linker with duplicate owners.
- Language-server workspace state does not consume project ownership metadata.

## Acceptance checklist

- [x] Public owner and collection records are frozen and have the exact fields.
- [x] Constructor invariants reject invalid kinds, IDs, names, spans, and source
  mismatches.
- [x] Canonical order is deterministic under reversed mapping insertion order.
- [x] Equal AIR IDs remain representable and queryable without overwrite.
- [x] Legacy directives, P11.2B directive sequences, and functions are projected
  with `module_name=None`.
- [x] Module owners retain exact validated module and physical source spelling.
- [x] Existing top-level source-map spans are reused without reparsing.
- [x] Generic functions have one declaration owner and no specialization owner.
- [x] `ProjectBuild` field order, positional defaults, and equality compatibility
  are preserved.
- [x] `ModuleGraph` and `ProjectDocumentGraph` shapes remain unchanged.
- [x] Linker duplicate authority, diagnostics, visibility, entries, CLI,
  manifest, artifact v1, and language-server boundaries remain unchanged.
- [x] No export, visibility, alias, namespace, qualification, AIR, artifact,
  tooling, runtime, or later-stage behavior is introduced.

## Test record

The focused executable record is
`apexforge/p11_3d_canonical_declaration_ownership_smoke_test.py`. It covers
public shape and exports, immutability, constructor rejection, duplicate
retention, exact queries, canonical ordering, legacy and module projection,
P11.2B multi-directive sources, nested-member exclusions, reversed mappings,
generic declaration ownership and lowering boundaries, `ProjectBuild`
compatibility, graph shapes, visibility and entry boundaries, reachable module
diagnostics plus the preempted branch, unchanged `APX-LINK-001`, exact CLI
output, artifact byte/fingerprint stability before and after queries,
language-server and Visual Studio non-consumption, external deterministic
temporary fixtures, network prohibition, working-directory preservation, and
unchanged repository status.

Validation uses UTF-8 mode, `PYTHONDONTWRITEBYTECODE=1`, and `py -3 -B`. The
executing agent reports the focused matrix, failures, actual full-harness
discovery count, and final repository status rather than embedding a permanent
harness count in this contract.
