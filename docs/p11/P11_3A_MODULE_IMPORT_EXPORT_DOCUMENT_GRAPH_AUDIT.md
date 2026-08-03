# P11.3A Module, Import, Export, and Document-Graph Architecture Audit

## Audit status and scope

This document records the implementation present on branch
`p11.3-modules-imports` at `736626cb79dfcdf3ea79d3274ba6a0c755c32e1e`.
The frozen P11.2 baseline is
`6b82f797bfd74b01047928638c7cf2538f689485` under
`afp-p11.2-freeze`. Commits `fa5836d` and `b6f9277` are ancestors of the
audited branch.

P11.3A is audit-only. This document and its companion smoke test do not change
production code, define export semantics, create a document graph, or begin
P11.3B. The repository owner retains authority over the recommended next
slice.

For this audit, **export** means an ApexForge language-level declaration and
visibility mechanism. Python package re-exports, grammar-export utilities, AIR
serialization, and files under `apexforge/exports` are unrelated. **Document
graph** means a project-level graph that represents every physical source
document and its language relationships. It does not mean the existing
workflow graph, `SourceMap`, manifest source list, or `ModuleGraph` alone.

Implementation and tests inspected include:

- `apexforge/language/modules.py`, `project.py`, `parser.py`, and `compiler.py`;
- `apexforge/air/linker.py` and the runtime validator;
- `apexforge/tooling/project_loader.py`, `project_manifest.py`,
  `build_artifact.py`, and `cli.py`;
- the module, source-grammar, project-builder, P11.2A, and P11.2B smoke tests;
- linker, diagnostics, generic, CLI, artifact, and P10-T4 language-server
  tests and implementation;
- definition, hover, formatting, document/workspace symbols, references,
  rename, completion, diagnostics, integration, and server surfaces.

## Existing implemented behavior

### Parser and module-header contract

Module and import headers are parsed before the ordinary lexer/parser by
`parse_module_source`. They are not AST declarations. The observable syntax is
line-oriented and case-sensitive:

```text
module-name ::= identifier ("." identifier)*
identifier  ::= [A-Za-z_][A-Za-z0-9_]*
module-line ::= horizontal-space* "module" horizontal-space+ module-name
                horizontal-space* ";"? horizontal-space* newline?
import-line ::= horizontal-space* "import" horizontal-space+ module-name
                horizontal-space* ";"? horizontal-space* newline?
```

Leading blank lines and blank lines between headers are accepted. A module
line may be indented. At most one module declaration is accepted, imports
require a preceding module declaration, and all headers must occur before the
ordinary top-level body. Lowercase `module` and `import` are the only header
keywords. Comments are not header trivia: a comment starts the body, so a
later module/import-looking line is late and invalid.

The optional semicolon is discarded. Names are stripped and validated but are
not lowercased, case-folded, path-normalized, or resolved relative to the
source filename. Thus `App.Core` remains `App.Core`. The physical source name
is stripped; it does not derive the module name.

Each recognized header line is replaced with spaces while retaining every
CR/LF character. `masked_source` therefore has the same length, offsets,
lines, columns, and line-ending layout as the original source. Module and
import spans cover only the name, excluding keyword, indentation, optional
semicolon, and newline.

Imports are stored in declaration order. Exact duplicate spellings in one
source fail during header parsing. A spelling that differs only by case is not
an exact duplicate; it proceeds to graph construction and normally fails as a
missing exact-case module.

The ordinary parser still returns exactly one top-level node from
`parse(source)`. It recognizes function, directive, workflow, authority,
principal, and role declarations. Module/import headers reach that parser only
as same-length whitespace.

### Legacy mode, module mode, and P11.2B

`build_module_graph` selects one project-wide mode:

| Input shape | Current mode and result |
| --- | --- |
| No source declares a module | Legacy mode; `ModuleGraph()` is empty and `is_legacy` is true. |
| Every source declares a module | Module mode; graph validation and dependency ordering apply. |
| At least one source declares a module and at least one does not | The whole build fails with `APX-MODULE-005`; there is no per-file mixed mode. |

P11.2B remains intentionally asymmetric. In legacy mode,
`allow_headerless_multi_directive=True`, so one physical headerless source may
contain a sequence of directives. In module mode the builder passes
`allow_headerless_multi_directive=False`; every module source remains limited
to one ordinary top-level declaration. A second directive in the same module
source fails at parse stage exactly like a second function or a mixed second
declaration.

Language-server analyzers call the single-node `parse` entry directly. They do
not call the P11.2B headerless directive-sequence parser. Consequently the
compiler/CLI accepts P11.2B headerless multi-directive files while current LSP
syntax features still treat the second directive as invalid. This is existing
tooling asymmetry, not a new contract.

### Module graph, uniqueness, and ordering

`ModuleGraph` contains only explicit module projects:

- `modules` is a tuple of `ModuleRecord(name, source_name, span, imports)`
  sorted by `(module_name.casefold(), module_name)`;
- `order` contains each module exactly once in deterministic dependency-first
  topological order;
- `direct_imports(name)` returns the stored direct imports in source order;
- `source_order()` projects graph order to physical source names;
- legacy projects have no module or document records in this object.

Module declaration uniqueness is case-insensitive by `casefold()`. `App.Core`
and `app.core` conflict with `APX-MODULE-009`. Import lookup, `find`, and graph
edges are nevertheless exact-case: importing `app.core` does not find a
declared `App.Core`. This uniqueness/lookup asymmetry is current behavior.

Missing imports are rejected before cycle detection. A self-import resolves
to its own module and is reported as the one-edge cycle `name -> name`; there
is no dedicated self-import diagnostic. Cycles are found by deterministic DFS
over case-folded/name-sorted module names and dependencies. The reported path
starts from that deterministic traversal, the first cycle edge is primary,
and remaining edge spans are related spans.

Topological ordering uses dependency count plus a heap keyed by
`(name.casefold(), name)`. All direct and transitive dependencies precede an
importer. When more than one module is ready, lexical module-name order is the
tie-breaker. Import declaration order does not change that tie-breaking.

There are three distinct deterministic orders:

| Surface | Order |
| --- | --- |
| `ProjectBuild.source_units` and loaded manifest sources | Canonical physical source path/name order, `(casefold, original)`. |
| `ModuleGraph.modules` | Canonical module-name order, `(casefold, original)`. |
| Module compilation, AIR link input, linked directive/function order | Dependency-first `ModuleGraph.order`. |

Legacy compilation/link order remains canonical physical source-name order.

### Resolution and visibility

Compiled declaration identities are global and not module-qualified. Examples
are `directive:Worker`, `function:Identity`, `state:count`, `event:done`,
`cause:flow`, `principal:Worker`, and `auth:Worker`. Import declarations do not
create namespaces, aliases, canonical qualified identities, or rewritten AIR
references.

After every module source is compiled, `validate_module_visibility` builds a
global owner table for linked directive and function IDs. It then examines
source-map entries of only two kinds:

| Reference | Current cross-module behavior |
| --- | --- |
| Directive invocation | A known directive in the same module or a directly imported module is accepted. A known directive in any other module fails with `APX-MODULE-008`. The AIR target remains its short spelling. |
| Function call, including generic calls | A known function in the same module or a directly imported module is accepted. A known function in any other module fails with `APX-MODULE-008`. The AIR target remains short; explicit type arguments remain call metadata. |

Transitive imports affect dependency/build order but do not confer visibility.
Importing `middle`, where `middle` imports `leaf`, does not permit a call from
the first module to a declaration owned by `leaf`. There is therefore no
implicit re-export behavior.

Imports do have a narrow semantic effect beyond ordering: they gate known
cross-module directive invocations and function calls. They do not implement
general declaration lookup. The owner table is populated from all compiled
modules by global short AIR ID, and imports merely authorize an already-known
owner. Undefined targets have no owner, bypass module visibility, and later
fail runtime validation (`APX-VALIDATE-002` for directives and
`APX-VALIDATE-003` for functions).

Current declaration/reference behavior by family is:

| Family | Imported and non-imported module behavior |
| --- | --- |
| Directive | Project-supported. Definitions are global short IDs. Invocation visibility is same-module plus direct imports only. Duplicate IDs fail linking. |
| Function | Project-supported. Definitions are global short IDs. Call visibility is same-module plus direct imports only. Duplicate IDs fail linking. |
| Generic function | Same direct-import gate as a non-generic function. Linked specialization collection/lowering operates on the complete linked AIR and retains IDs such as `Identity<int>`; modules do not qualify them. |
| State | Compiled from a directive-local state-name map. Source syntax does not resolve another module's state. Linked state IDs are still globally flat, so same-name definitions collide regardless of imports. |
| Event | Compiled from a directive-local event-name map. Source syntax does not resolve another module's event. Linked event IDs are globally flat and collide regardless of imports. |
| Cause | Owned syntactically by one directive, but AIR cause IDs are globally short and duplicate causes collide regardless of imports. There is no cross-cause import lookup. |
| Path | Nested under a cause and not import-resolved. Repeated path IDs can exist in different causes under the established AIR shape. |
| Principal | A supported directive synthesizes `principal:DirectiveName`. Source `principal` declarations parse but the main compiler rejects them with `APX-COMPILE-007`; imports cannot make them project declarations. |
| Authority | Directive-attached authority values enter AIR without module visibility analysis. Top-level authority declarations parse but the main compiler rejects them with `APX-COMPILE-007`. |
| Role | Standalone compilation lowers a role to `AIRRole`, but `ProjectBuilder` requires `AIRProgram` and reports fallback `APX-COMPILE-999`; imports do not change this boundary. |
| Workflow | Parses, but the main compiler rejects `WorkflowNode` with `APX-COMPILE-007`. The separate legacy workflow engine is outside the module project pipeline. |

Source references for directive/function targets are short identifiers.
Canonical AIR-prefixed forms are accepted only at APIs that explicitly handle
them, notably project entry selection (`Main` or `directive:Main`). ApexForge
source does not accept module-qualified declaration references such as
`app.main.Main`, and entry selection does not resolve that spelling. There is
no ambiguity object or overload resolution: duplicate same-kind global short
definitions fail with `APX-LINK-001`. Identical short names in different
kind-prefix namespaces, such as a function and directive both named `Same`,
can coexist.

### Export status

No ApexForge language export semantics are implemented.

- `export` is not a module header, lexer keyword, parser production, AST node,
  compiler input, AIR declaration, manifest field, artifact field, or LSP
  semantic feature.
- There is no explicit export syntax or export list.
- There is no `public`/`private` declaration visibility.
- There are no implicit export records.
- There are no re-exports. Direct-import-only visibility specifically rejects
  transitive access.
- There is no aliasing or qualified export identity.

All project-supported directives and functions are present in one globally
linked AIR program, and every such declaration in a directly imported module
is eligible for the narrow call/invocation gate. That fact is an artifact of
global linking plus direct-import validation; it must not be described as an
implemented implicit-export model. In P11.3 terminology, exports remain a
roadmap requirement only.

### Document-graph status

The only language dependency graph is `ModuleGraph`. It is not a complete
document graph:

- it has one module record per explicit-module source and an import edge list;
- it maps module names to physical source names and supplies dependency order;
- it is empty in legacy mode, even though legacy projects have physical
  documents and declarations;
- it has no document identity independent of module identity;
- it contains no declaration nodes, ownership index, references, export
  edges, visibility results, unresolved edges, reverse dependencies, or
  language-server overlay state;
- it is not serialized into AIR or artifact v1.

Other nearby structures are not document graphs. `ProjectManifest.sources` is
an ordered file inventory. `SourceMap` maps AIR/source-reference entries to
spans but does not model documents or dependencies. `AIRProgramLinker` merges
ordered global declarations but stores no module edge or ownership metadata.
Workspace symbols recursively scan `.apex` files and flatten per-document
syntax symbols without building, resolving imports, or consulting the
manifest/module graph.

### CLI, manifest, and artifact behavior

`apexforge check`, `run`, and `build` load the canonical manifest source
snapshot and call the same `build_project` pipeline used by direct API callers.
They therefore accept valid module projects and expose the same module
diagnostics through the check failure boundary. No module-specific CLI command
or option exists.

Manifest schema 1 has only `schema`, `name`, `sources`, and optional `entry`.
Sources are normalized to slash-separated safe relative paths and sorted by
`(casefold, original)`. The entry remains a global directive reference. It may
be short or `directive:`-canonical but cannot name a module or select an export.
With no configured entry, exactly one linked directive is the fallback;
multiple directives are ambiguous even when they reside in distinct modules.

Public `run` grants invocation authority only to the selected entry directive.
Module imports do not grant downstream runtime authority. A valid imported
invocation can therefore build successfully and still receive the established
runtime denial unless the execution context supplies the callee grant.

Build artifact schema remains `apexforge.build-artifact/v1` with top-level
`schema`, `project`, `air`, and `fingerprint` fields:

- `project.sources` remains canonical manifest/path order, not module graph
  order;
- each source hash is SHA-256 over the exact loaded bytes, before universal
  newline normalization used for compilation;
- `air` is the complete linked program, so its directive/function sequence in
  module mode follows dependency-first link input;
- the fingerprint is SHA-256 over canonical UTF-8 JSON containing only
  `schema`, `project`, and `air`; the fingerprint record is added afterward;
- there is no module name, import edge, export, source-to-module map, or
  document graph field.

Thus two useful but different orders coexist inside one artifact: manifest
source metadata is path-ordered, while linked AIR declarations can be
dependency-ordered.

### Language-server behavior

The language server recognizes module/import headers syntactically in each
open document by calling `parse_module_source` and parsing `masked_source`.
It does not load a project, resolve a manifest, build `ModuleGraph`, link AIR,
or validate missing imports, cycles, mixed mode, or cross-module visibility.

| Surface | Current behavior |
| --- | --- |
| Diagnostics | Reports header lexer/parser diagnostics for one document. A syntactically valid but missing import produces no LSP diagnostic. |
| Completion | Includes `module` and `import` keyword completions and syntax descriptions; it has no module-name index. |
| Document symbols | An explicit module is the root symbol; imports and the single top-level declaration are children. Headerless sources expose the declaration directly. |
| Workspace symbols | Recursively scans `.apex` files, indexes module and supported declaration symbols, and honors open overlays. It does not resolve relationships or require a manifest. Import child symbols are not independent indexed declarations. |
| Hover | Provides syntax-level module and direct-import hover text plus ordinary declaration/member hovers. |
| Formatting | Reprints a module line followed by imports in source order, removes optional semicolons, inserts one blank line, and formats the one parsed declaration. |
| Definition | Defines the current document's module declaration to itself. Import names are not indexed as resolvable references; cross-file/import definition is deferred. |
| References | Uses the same-document occurrence graph. A module declaration has only its local occurrence; import resolution and cross-file references are deferred. |
| Rename | Module, callable, directive, workflow, authority, capability, role, and principal namespaces are protected. File/module and cross-file rename are deferred. Import names are not resolved rename targets. |

## Existing diagnostics

All module diagnostics have severity `error` and stage `module`. `ModuleError`
and `ProjectBuildError` sort diagnostics by canonical diagnostic sort key.

| Code | Trigger and message category | Primary span | Related spans |
| --- | --- | --- | --- |
| `APX-MODULE-001` | Malformed module/import-looking header, or a header after the body began. | Entire offending line excluding newline. | None. |
| `APX-MODULE-002` | A second module declaration. Because this check precedes the later ordering branch, `module; import; module` is observably `002`, not `003`. | Second module name. | First module-name span. |
| `APX-MODULE-003` | Import before any module declaration. | Import name. | None. |
| `APX-MODULE-004` | Exact duplicate import in one source. | Later import name. | First equal import-name span. |
| `APX-MODULE-005` | Headerless source while any other source activates module mode. One diagnostic is created for each headerless source. | Zero-width span at offset 0 in that physical source. | None. |
| `APX-MODULE-006` | Imported name has no exact-case module declaration. | Import-name span. | None. |
| `APX-MODULE-007` | Deterministically selected import cycle, including self-import. | First import edge in the reported cycle path. | Remaining edge spans in path order. |
| `APX-MODULE-008` | Known directive/function owner is neither the caller's module nor a direct import. | Invocation or function-call source-map span. | None; `air_id` is the source reference entry ID. |
| `APX-MODULE-009` | Module name duplicates an earlier declaration under `casefold()`. | Later module-name span in canonical source processing order. | Earlier module-name span. |

Related project diagnostics that define the current boundary are:

- a second declaration in a module source: parse stage, normally
  `APX-PARSE-001`, at the second top-level token;
- duplicate global AIR declarations across modules: link stage,
  `APX-LINK-001`, primary first definition, remaining source definitions as
  related spans, canonical global `air_id`;
- undefined directive/function targets: validate stage,
  `APX-VALIDATE-002`/`APX-VALIDATE-003`, mapped to call sites through
  `SourceMap`;
- workflow, authority, and principal top-level project sources: compile stage,
  `APX-COMPILE-007`, declaration span;
- a role project source: compile-stage fallback `APX-COMPILE-999`, zero-width
  start-of-source span, because standalone lowering returned `AIRRole` instead
  of `AIRProgram`.

There are no diagnostics dedicated to self-import, transitive visibility,
ambiguous imported declarations, qualified names, exports, or document-graph
consistency.

## Frozen compatibility requirements

Any later P11.3 production slice must preserve the following unless the owner
explicitly authorizes and tests a compatibility change:

1. P10 and P11.2 frozen behavior, diagnostics, source spans, deterministic AIR,
   CLI contracts, artifact v1, and language-server T4 contracts.
2. Header masking must remain offset/line/column preserving.
3. Headerless all-legacy projects must continue to build without module
   declarations.
4. P11.2B headerless multi-directive source units must remain accepted in
   legacy mode in physical source order.
5. Module sources must remain one declaration per physical source until a
   separately reviewed change authorizes otherwise.
6. Mixed legacy/module projects must fail rather than silently infer module
   identities.
7. Existing dependency-first module build order and deterministic lexical
   tie-breaking must remain stable.
8. Current short and canonical entry forms, one-directive fallback, and
   multi-directive ambiguity must remain stable.
9. Imports must not broaden runtime authority.
10. Artifact v1 source hashes must remain hashes of exact loaded bytes, and no
    new artifact fields may appear without a versioned artifact decision.
11. The compiler/runtime core must remain deterministic and independent of AI
    services; validation and authority boundaries must not be bypassed.

## Missing or partial behavior

The current implementation is sufficient for dependency ordering and a narrow
direct-call gate, but it does not yet fulfill the roadmap phrase “Modules,
Imports, Exports, and Document Graph.” Missing or partial areas are:

- no export grammar, AST, semantic model, AIR projection, diagnostics, or LSP
  support;
- no public/private visibility, export list, re-export, or alias behavior;
- no canonical module-qualified declaration identity or namespace;
- no general resolver shared by all declaration families;
- no explicit ambiguous-reference result because global duplicates fail first;
- no document graph that represents legacy and module documents uniformly;
- no declaration ownership or reference edges persisted after module
  visibility validation;
- no reverse-dependency or transitive-reachability API;
- no graph serialization or tooling query surface;
- no project-aware LSP import diagnostics, definition, references, or rename;
- no module-aware entry syntax;
- only functions and directives are canonical project declaration families;
- module sources cannot use P11.2B multi-directive units;
- source metadata order and AIR order are deterministic but intentionally
  different and not explicitly related in artifact v1.

## Architectural risks

1. **Case semantics are split.** Module uniqueness is case-folded while import
   lookup is exact. Users can receive “duplicate declaration” for two case
   variants but “missing import” when using the wrong variant.
2. **Global short IDs erase ownership.** Module ownership is reconstructed from
   per-source compiled AIR and then discarded. Future exports or qualification
   cannot be layered safely by treating current IDs as already namespaced.
3. **Visibility is a post-compile special case.** Only source-map directive and
   function reference kinds are checked. New reference kinds could become
   globally visible accidentally unless every producer is wired manually.
4. **Known and unknown targets fail at different stages.** A known but
   non-imported target is a module error; an unknown target bypasses module
   visibility and becomes a validation error.
5. **Duplicate globals can distort owner inference.** The temporary owner table
   is keyed by global ID before the linker reports duplicates. Although
   deterministic, it is not an ambiguity-capable symbol table.
6. **`ModuleGraph` omits legacy documents.** Extending it in place as a full
   document graph could silently change `is_legacy`, defaults, equality, and
   downstream assumptions.
7. **Build and tooling see different graphs.** Workspace symbols scan files
   independently; LSP diagnostics do not see manifest membership or import
   edges; P11.2B build and LSP parsing also differ.
8. **Order domains can be confused.** Manifest source order, module record
   order, graph order, and linked AIR order are all deterministic but serve
   different contracts.
9. **Export work is cross-layer by nature.** Adding an `export` keyword would
   touch frozen grammar/lexer/parser/LSP surfaces before a visibility and
   identity model exists. Starting with syntax would prematurely lock design.
10. **One unreachable diagnostic branch exists.** The implementation contains
    a “module declaration must precede imports” `APX-MODULE-003` branch, but a
    second module after an import is caught first as `APX-MODULE-002`.

## P11.3 non-goals

P11.3A does not implement, and the recommended immediate slice should not
silently introduce:

- export syntax, implicit exports, public/private rules, re-exports, or export
  lists;
- import aliases, namespaces, qualified source references, or qualified
  declaration identities;
- multiple declarations in module sources or nested declarations;
- P11.4 identity redesign;
- workflow/authority/principal/role promotion into the canonical project
  compiler;
- new artifact fields or a new artifact schema;
- new CLI commands or module-aware entry spelling;
- cross-file LSP resolution/rename;
- runtime authority changes;
- grammar, compiler, AIR, runtime, CLI, and tooling redesign in one slice.

## Proposed P11.3B slice

The smallest coherent production slice supported by this evidence is a
**canonical project document-graph foundation that projects existing behavior
without changing it**.

The slice should introduce an immutable document graph alongside, not as a
reinterpretation of, `ModuleGraph`. It should represent every canonical
`SourceUnit` exactly once in both legacy and module projects. Each record should
contain the physical source name, optional module name and module-name span,
and the existing ordered import declarations. Resolved module-mode edges
should point to target document records while retaining import spans. The graph
should expose separately named canonical source order, dependency order,
direct dependencies, and transitive dependencies. In legacy mode it should
contain document records and no import edges, while preserving the current
empty `ModuleGraph` compatibility projection.

`ProjectBuilder` may expose this graph on `ProjectBuild`, but compilation,
visibility, linking, validation, entry selection, CLI output, artifact v1, and
language-server behavior should remain unchanged in this first slice. Existing
module diagnostics should be reused exactly rather than replaced. No export
field should be added yet; the document graph supplies stable physical and
dependency ownership on which a later, separately reviewed export model can be
designed.

This recommendation intentionally does not complete all of P11.3. It sequences
the missing graph foundation before export syntax and qualified identity, which
currently lack a safe ownership model.

## Exact P11.3B acceptance checklist

The recommended slice is acceptable only if all items below are demonstrated:

- [ ] Repository branch/baseline/freeze/ancestry preconditions are verified
  before edits, and unrelated changes are absent.
- [ ] A documented immutable `ProjectDocumentGraph` (name subject to owner
  approval) represents every input source exactly once.
- [ ] Legacy documents are represented without inventing module names or
  changing `ModuleGraph.is_legacy`.
- [ ] Explicit module documents retain exact module/import spellings and
  existing source spans.
- [ ] Every resolved import edge maps one importer document to one target
  document and retains the import-name span.
- [ ] Direct dependency queries preserve import declaration order.
- [ ] Transitive dependency queries are deterministic, cycle-free after current
  validation, and explicitly distinct from visibility.
- [ ] Canonical physical source order and dependency-first module order are
  separately named and reproduce current results exactly.
- [ ] Existing `APX-MODULE-001` through `APX-MODULE-009` observable stage, code,
  message category, primary span, related spans, and `air_id` behavior remain
  unchanged.
- [ ] Exact-case import lookup and case-folded uniqueness remain unchanged in
  this slice, with the risk documented rather than silently “fixed.”
- [ ] Direct-only directive/function visibility remains unchanged; transitive
  imports do not become visible and undefined targets retain validate-stage
  diagnostics.
- [ ] P11.2B headerless multi-directive compatibility remains enabled only in
  legacy mode; module sources remain one declaration each.
- [ ] Generic call closure/lowering, entry selection, linked AIR order, runtime
  authority, CLI `check`/`run`/`build`, and artifact fingerprints remain
  byte/semantic compatible as applicable.
- [ ] Artifact v1 gains no fields and manifest schema 1 gains no fields.
- [ ] No export, alias, namespace, qualification, identity redesign, new CLI
  command, or cross-file LSP feature is included.
- [ ] Focused parser/graph/diagnostic/project tests pass before the complete
  regression harness.
- [ ] The complete harness reports its actual discovered test count and passes
  without hidden or weakened coverage.
- [ ] Changed files, tests, failures, risks, limitations, and final repository
  state are reported; no milestone is declared complete, frozen, or released.

## P11.3A audit acceptance record

The companion
`apexforge/p11_3a_module_architecture_audit_smoke_test.py` freezes the observed
parser, graph, visibility, generic, entry, CLI, artifact, language-server, and
isolation behavior described here. Final test counts and repository status are
reported by the executing agent rather than embedded as a permanent claim in
this audit document.
