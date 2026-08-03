# P11.3B Canonical Project Document-Graph Foundation

## Scope and accepted baseline

P11.3B adds an immutable physical-document graph beside the existing
`ModuleGraph`. It implements the graph foundation recommended by the accepted
P11.3A audit at commit `697e3b2` on the required P11.3B starting commit
`04caf24`. The frozen P11.2 baseline remains
`6b82f797bfd74b01047928638c7cf2538f689485` under
`afp-p11.2-freeze`.

This slice projects already parsed and validated project data. It does not
replace module parsing, module validation, compilation, linking, validation,
entry selection, runtime execution, artifacts, manifests, CLI behavior, or
language-server behavior.

## Public model and invariants

`language.modules` exports these frozen dataclasses:

- `ProjectDocument`
- `ResolvedImportEdge`
- `ProjectDocumentGraph`

It also exports `build_project_document_graph`. `ProjectBuilder` calls that
function only after `parse_module_source` and `build_module_graph` have
succeeded. The builder does not parse source text again.

Every graph has these invariants:

- `documents` contains every physical project source exactly once.
- Physical source names are unique under the same case-folded rule already
  enforced by `ProjectBuilder`.
- `canonical_order` and `dependency_order` each contain every document once.
- A graph is entirely legacy or entirely explicit-module mode.
- Every explicit import has exactly one resolved edge.
- Every dependency edge precedes its importer in module dependency order.
- All collections are tuples and all graph records are frozen dataclasses.

An empty `ProjectDocumentGraph()` is the compatibility default for manually
constructed `ProjectBuild` values. Successful `ProjectBuilder` output always
contains the derived graph for its complete source set.

## Document records

`ProjectDocument` contains:

- `source_name`: the exact normalized physical `SourceUnit.name`;
- `module_name`: the exact case-preserved module spelling, or `None`;
- `module_span`: the existing module-name `SourceSpan`, or `None`;
- `imports`: the existing ordered tuple of `ModuleImport` declarations.

The graph does not copy, normalize, case-fold, or reorder module and import
spellings. Each `ModuleImport` retains its existing exact name and import-name
span. Module and import spans must belong to the document's physical source.

## Resolved import edges

`ResolvedImportEdge` contains:

- `importer_source_name`;
- `imported_module_name` with its original case-preserved spelling;
- `target_source_name`;
- `import_span`, which is the original import-name span.

`ProjectDocumentGraph.resolved_import_edges` is ordered first by canonical
physical importer source and then by import declaration order within that
source. Legacy graphs contain no edges. Module graphs contain one edge for
every already validated import; unresolved edges are not represented because
the existing `APX-MODULE-006` boundary fails the build first.

## Canonical physical source order

`canonical_source_order()` returns physical source names ordered by
`(source_name.casefold(), source_name)`. It exactly reproduces
`ProjectBuild.source_units` order and the existing canonical project source
order. It is independent of module dependency order.

## Dependency-first source order

`dependency_first_source_order()` returns physical source names in build
dependency order. In explicit module mode it exactly projects
`ModuleGraph.source_order()`, including the existing module-name lexical
tie-breaking. In legacy mode it equals canonical physical source order.

## Direct dependency semantics

`direct_document_dependencies(source_name)` returns target
`ProjectDocument` records in the requesting document's import declaration
order. It does not sort those records by module name or dependency order.

This query reports graph reachability only. It does not perform declaration
lookup and does not change direct-import-only directive or function
visibility.

## Transitive dependency semantics

`transitive_document_dependencies(source_name)` computes the unique reachable
document set and filters that set through the graph's complete
dependency-first source order. Therefore:

- each reachable document occurs once;
- every reachable dependency precedes its importer;
- the requesting document is excluded;
- unrelated documents are excluded;
- the result is deterministic under source mapping insertion-order changes.

Transitive document dependency remains distinct from declaration visibility.
A root document that imports a middle document does not gain access to a leaf
directive or function merely because the middle document imports the leaf.

## Lookup and invalid queries

`find(source_name)` performs exact-case physical-source lookup after trimming
outer whitespace. It returns `None` for an unknown source. Both dependency
queries return an empty tuple for an unknown source. A non-string source query
raises `TypeError`; an empty or whitespace-only query raises `ValueError`.
Case variants are not aliases.

## Legacy projection

In a headerless project, the document graph contains one `ProjectDocument`
for every physical source. Every record has `module_name=None`,
`module_span=None`, and no imports. The graph has no resolved edges, and its
dependency order equals canonical source order.

The existing `ModuleGraph()` remains empty and `ModuleGraph.is_legacy` remains
true. P11.2B headerless multi-directive parsing remains enabled for legacy
compilation only.

## Module-mode projection

In explicit module mode, every physical source becomes one document and every
document retains the matching validated `ModuleRecord` name, span, and import
tuple. Resolved edges use exact-case module lookup already completed by
`build_module_graph`. Dependency order comes directly from
`ModuleGraph.source_order()`.

Module sources remain limited to one ordinary top-level declaration. The
document graph does not enable P11.2B directive sequences in module mode.

## ProjectBuild integration

`ProjectBuild.document_graph` exposes the derived graph. The new field is
appended after all existing positional fields, so existing positional
construction through `entry_directive` continues to work. Because the graph
is a projection of already represented build inputs and module data, it is
excluded from `ProjectBuild` dataclass equality comparisons; existing build
equality semantics remain based on the pre-P11.3B fields.

The default for direct manual construction is an empty immutable document
graph. `ProjectBuilder.build` supplies the complete derived graph.

## Frozen compatibility guarantees

P11.3B does not change:

- `ModuleGraph.is_legacy`, `modules`, `order`, `source_order()`,
  `direct_imports()`, equality, or ordering;
- parser grammar, header masking, spans, or single-node parser behavior;
- compiler behavior, AIR identities, SourceMap behavior, linking, validation,
  or runtime authority;
- direct-versus-transitive directive/function visibility;
- generic closure or lowering;
- short/canonical entry selection and ambiguity behavior;
- CLI `check`, `run`, or `build` output;
- manifest schema 1;
- artifact v1 schema, bytes, source order, hashes, or fingerprint;
- language-server syntax-only and same-document behavior.

Accessing the document graph has no compilation, execution, serialization, or
artifact side effect.

## Diagnostics preservation

The document graph is constructed only after the existing module graph has
validated mixed mode, uniqueness, missing imports, and cycles. It introduces
no production diagnostic and reuses `APX-MODULE-001` through
`APX-MODULE-009` unchanged where reachable, including stage, message category,
primary span, related spans, and `air_id` behavior.

The module-declaration-after-import branch that is preempted by
`APX-MODULE-002` remains preempted. P11.3B does not expose or repair that
currently unreachable `APX-MODULE-003` branch.

## Explicit non-goals

This slice adds no export syntax or model, implicit exports, visibility rules,
public/private declarations, re-exports, export lists, import aliases,
namespaces, qualified identities, qualified source references, qualified
entry syntax, nested declarations, multiple declarations in module sources,
P11.4 identity work, AIR fields, artifact fields, manifest fields, CLI
commands, cross-file language-server resolution/rename, workspace graph,
runtime-authority change, production diagnostic change, or P11.3C behavior.

## Known limitations

- Module uniqueness remains case-folded while import resolution remains exact
  case.
- Documents model physical ownership and dependency reachability only; they do
  not contain declaration, reference, export, or visibility nodes.
- Dependency queries are forward-only. No reverse-dependency API is included.
- Language-server workspace state does not consume this graph.
- Manual `ProjectBuild` construction receives the empty compatibility default
  unless a caller explicitly supplies a graph.
- Legacy documents have no invented module identity and therefore no import
  relationships.

## Acceptance checklist

- [x] Every legacy and module physical source has one immutable document.
- [x] Exact module/import spellings and existing spans are retained.
- [x] Every validated import has one immutable resolved edge.
- [x] Canonical and dependency-first source orders are separately exposed.
- [x] Direct dependencies preserve import declaration order.
- [x] Transitive dependencies are unique, deterministic, requester-excluding,
  and dependency-first.
- [x] Legacy graphs contain no module names or import edges.
- [x] Module graphs are projected without changing `ModuleGraph` behavior.
- [x] `ProjectBuild.document_graph` preserves existing positional slots and
  equality behavior.
- [x] Existing module diagnostics and the unreachable branch boundary remain
  unchanged.
- [x] P11.2B remains legacy-only; module sources remain single-declaration.
- [x] Visibility, generics, entry selection, CLI, artifact v1, and LSP
  boundaries remain unchanged.
- [x] No export, alias, namespace, qualification, AIR, artifact, or LSP overlay
  model is present.

## Test record

The focused executable record is
`apexforge/p11_3b_project_document_graph_smoke_test.py`. It covers legacy and
module projection, reversed mapping order, records and spans, resolved edges,
all order/query surfaces, invalid queries, immutability, ModuleGraph values,
reachable module diagnostics, the unreachable diagnostic branch boundary,
P11.2B asymmetry, direct-only visibility, generic closure/lowering, entry
selection, exact CLI output, artifact v1 byte/fingerprint stability,
language-server non-integration, network isolation, and temporary-fixture
cleanup.

Validation is run with UTF-8 mode and bytecode writes disabled. The executing
agent reports the focused test matrix and complete regression-harness count
rather than embedding a permanent harness count in this contract.
