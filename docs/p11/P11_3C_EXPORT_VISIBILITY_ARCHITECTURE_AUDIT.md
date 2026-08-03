# P11.3C Export and Visibility Architecture Audit

## Scope and accepted baseline

This audit records the implementation on branch `p11.3-modules-imports` at
`a8ae42856de8acda0e909d4b9bb4c5efdef83b89` (`Advance P11.3 to export
visibility audit`). The accepted P11.3B implementation is `3811b21`, the
accepted P11.3A audit is `697e3b2`, and the frozen P11.2 baseline is
`6b82f797bfd74b01047928638c7cf2538f689485` under
`afp-p11.2-freeze`. Commits `6b82f79`, `fa5836d`, and `b6f9277` are ancestors
of the audited HEAD.

P11.3C is audit-only. Its two additions are this document and
`apexforge/p11_3c_export_visibility_architecture_audit_smoke_test.py`. No
production file, grammar, compiler, AIR model, runtime, CLI, artifact,
manifest, diagnostic, or language-server implementation is changed. This
audit does not implement or canonize P11.3D.

In this document, *visibility* means whether one source declaration reference
is permitted to target a declaration owned by another source/module. *Export*
means a language-level declaration of a module's externally visible surface.
Python re-exports, grammar-export tooling, workflow trace exports, and the
`apexforge/exports` data directory are unrelated.

Two terms require care:

- `identity` is not a current top-level source declaration. `Identity` is often
  used as a sample function name, while generic type identities are type-system
  values.
- a *generic declaration* is a `FunctionNode` with type parameters, not a
  seventh top-level declaration kind.

## Existing declaration inventory

### Top-level declarations

The ordinary parser accepts exactly the six spellings in
`TOP_LEVEL_DECLARATIONS`. It returns exactly one ordinary top-level node. The
P11.2B compatibility parser additionally accepts two or more sequential
headerless directives in legacy mode only; it does not add another declaration
kind.

| Kind | Parser node | Main project lowering and linked AIR | Ownership and duplicate rule |
| --- | --- | --- | --- |
| Directive | `DirectiveNode` | Supported. Produces one `AIRDirective` plus a synthetic `Principal`, `AuthorityCheck`, states, events, causal decisions/paths, requirements, and directive-authority values in an `AIRProgram`. | Syntactically owned by its physical source and optional module; linked identity is global `directive:Name`. Same global IDs fail at link, sometimes after a synthetic nested ID collides first. |
| Function | `FunctionNode` | Supported. Produces one `AIRFunction` in an `AIRProgram`; it links, validates, and executes as a pure function. | Source/module ownership is recoverable from the per-source compiled artifact and source map. Linked identity is global `function:Name`; duplicates fail with `APX-LINK-001`. |
| Generic function | `FunctionNode` with `TypeParameterNode` values | Supported through the ordinary function lowering. `AIRFunction.type_parameters` contains owned `ApexTypeVariable` values. Inference, specialization collection, closure, and lowering occur over linked AIR. | The declaration remains `function:Name`; each type variable owner is `function:Name`; a specialization uses an unqualified identity such as `Identity<int>`. It has the same duplicate and visibility rules as its function. |
| Workflow | `WorkflowNode` | Parsed, but the main compiler rejects it with `APX-COMPILE-007`. The separate legacy workflow engine is not the project module pipeline. | No canonical project AIR declaration, module owner map, import visibility, link duplicate rule, or entry behavior exists. |
| Authority | `AuthorityNode` | Parsed, but the main compiler rejects it with `APX-COMPILE-007`. A separate legacy helper lowers to an authority grant outside the project pipeline. | No canonical project declaration ownership or module visibility exists. Directive-attached authority references are a different nested form. |
| Principal | `PrincipalNode` | Parsed, but the main compiler rejects it with `APX-COMPILE-007`. A standalone helper is outside compiler dispatch. | No canonical project declaration ownership or module visibility exists. A compiled directive's synthetic `principal:DirectiveName` is a different AIR value. |
| Role | `RoleNode` | `compile_node_with_map` produces a standalone `AIRRole`, not `AIRProgram`; `ProjectBuilder` rejects that result through `APX-COMPILE-999`. | It has a standalone source-map entry and unprefixed `AIRRole.name`, but no successful project link, module visibility, or entry behavior. |
| Identity | No node or production | Not a source declaration. | Not applicable. |

### Top-level module, cross-source, entry, and language-server matrix

| Kind | Current module awareness and cross-source visibility | Direct import required | Transitive import grants access | Entry candidate | Language-server treatment |
| --- | --- | --- | --- | --- | --- |
| Directive | Successful module declarations are globally linked. Only invocation references are checked for same-module or direct-import ownership. | Yes for a known directive in another module; no in legacy/headerless mode. | No. | Yes, by short `Name` or canonical `directive:Name`. | Syntax diagnostics, symbols, hover, and same-document declaration occurrence; directive invocation definition is not cross-file resolved and directive rename is protected. |
| Function | Successful module declarations are globally linked. Only call references are checked for same-module or direct-import ownership. | Yes for a known function in another module; no in legacy/headerless mode. | No. | No. | Syntax/symbol/hover and lexical same-document behavior; cross-file calls are not resolved and callable rename is protected. |
| Generic function | Same module gate as an ordinary function. Specialization closure scans the complete linked program after that gate. | Yes when the generic owner is in another module. | No. | No. | Displayed as a function with type-parameter children; no module-aware generic resolution. |
| Workflow | Module header parsing occurs before the compile rejection, but there is no project declaration to expose. | Not applicable. | No. | No. | Parsed and shown by syntax features; workflow declaration rename is protected and invocation targets are not resolved. |
| Authority | Module header parsing occurs before the compile rejection, but there is no project declaration to expose. | Not applicable. | No. | No. | Parsed and shown by syntax features; authority/capability resolution and rename remain protected or deferred. |
| Principal | Module header parsing occurs before the compile rejection, but there is no project declaration to expose. | Not applicable. | No. | No. | Parsed and shown by syntax features; principal/role/authority resolution and declaration rename are deferred. |
| Role | Module header parsing occurs, then the non-`AIRProgram` result is rejected. | Not applicable. | No. | No. | Parsed and shown by syntax features; role declaration rename and authority-reference resolution are deferred. |

### Nested declarations and references

| Family | Parser/AIR representation | Current ownership, visibility, and duplicates |
| --- | --- | --- |
| Type parameter | `TypeParameterNode` / `ApexTypeVariable`; projected to `AIRFunction.type_parameters` | Owned by global short `function:Name`. It is lexical, not imported independently. Parser rejects duplicate type-parameter names. |
| Value parameter and local binding | `ParameterNode`/`LetNode`; `AIRParameter`/`AIRLocalBinding` | Function lexical scope only; never an import/export candidate. Compiler and validator enforce duplicate/shadow rules. |
| State | `StateNode`; global `StateDefinition(id="state:Name")` | Source actions resolve through the containing directive's local state-name map. Imports cannot expose a state reference, but equal linked state IDs collide globally with `APX-LINK-001`. |
| Event | `EventNode`; global `EventDefinition(id="event:Name")` | Emits resolve through the containing directive's local event-name map. Imports cannot expose an event reference, but equal linked event IDs collide globally. |
| Cause | `CauseNode`; global `CausalDecision(id="cause:Name")` | Syntactically belongs to a directive. There is no source lookup across causes/modules; equal linked IDs collide globally. |
| Path | `PathNode`; `CausalPath(id="path:Name")` nested in a cause | No import lookup. Equal path IDs in one cause fail validation; equal IDs in different causes can coexist under the current nested AIR shape. |
| Directive authority and requirement | `DirectiveAuthorityNode` / `RequirementNode`; `DirectiveAuthority` / `DirectiveRequirement` | Attached to the containing directive. Authority values are name-keyed by the linker; duplicate behavior can fall through unsourced `APX-LINK-999`. Requirements are appended and repeated values are accepted. |
| Capability | `CapabilityNode` inside `AuthorityNode` | Parsed only because the containing top-level authority does not enter the project AIR pipeline. |
| Role/principal references | `RoleAuthorityNode`, `PrincipalRoleNode`, `PrincipalAuthorityNode` | Containing top-level form is not a successful project declaration; no import visibility exists. |
| Directive invocation | `InvokeActionNode`; `DirectiveInvocation`; source-map kind `directive_invocation` | This is a reference, not a declaration. It is the only directive reference family checked by module visibility. |
| Function call | `CallExpressionNode`; `AIRCallExpression`; source-map kind `function_call` | This is a reference, not a declaration. Calls, including explicit/inferred generic calls, are the only function reference family checked by module visibility. |

No nested functions, directives, workflows, authorities, principals, or roles
are accepted. Module sources remain limited to one ordinary top-level
declaration.

## Existing ownership model

Ownership exists in several temporary or partial forms; no persistent semantic
declaration-ownership graph exists.

| Structure | Owns now | Must not be reinterpreted as |
| --- | --- | --- |
| `SourceUnit` | Canonical physical source name and source text. | A module, declaration, or export record. |
| `ModuleSource` | Parsed optional module name/span, ordered direct imports, and offset-preserving masked source. | A parsed top-level declaration or semantic export set. |
| `ModuleRecord` | One validated explicit module's name, physical source, module span, and imports. | A declaration namespace or export owner. |
| `ModuleGraph` | Explicit-module dependency records and dependency-first module order; empty in legacy mode. | A document graph, declaration graph, visibility result, or namespace. |
| `ProjectDocument` | Physical source identity plus projected optional module/import header data. | A declaration/export/reference node. |
| `ProjectDocumentGraph` | Every physical document, resolved import edges, physical order, and dependency order. | Declaration lookup or visibility. Direct/transitive queries report reachability only. |
| Per-source `CompiledSource` | One independently compiled `AIRProgram` and source map. | A persistent project owner index; the builder discards its source grouping after linking. |
| AIR declarations | Global short IDs and runtime/validation data. | Module-qualified identity or authoritative source ownership. |
| `AIRProgramLinker` tables | Temporary same-kind uniqueness sets while merging ordered global declarations. | Import/export lookup or an ambiguity-capable symbol table. |
| `validate_module_visibility` owner map | Temporary `directive:`/`function:` ID to module mapping reconstructed from per-module compiled artifacts. | A stable public ownership model. Duplicate IDs overwrite an earlier owner before the linker rejects the duplicate. |
| Merged `SourceMap` | Sorted declaration/reference-to-span evidence across sources. | A document dependency graph or canonical export set. |

Future canonical export metadata should not be owned exclusively by any current
graph or AIR structure. Source-written export intent, if syntax is eventually
chosen, belongs with the source-facing parse result that owns its span:
`ModuleSource` for a header/section list, or the top-level declaration AST for
a modifier. The validated semantic export set should be owned by a separate
immutable declaration-ownership/export index keyed by source/module and future
qualified declaration identity. `ModuleRecord`, `ModuleGraph`, and
`ProjectDocumentGraph` should only project or consume relationships. AIR,
linker tables, CLI, artifacts, and language-server indexes should consume the
validated result only when their own versioned contracts require it.

## Existing visibility behavior

`validate_module_visibility` runs after every source has compiled and before
the project AIR programs are linked. In explicit module mode it:

1. walks modules in dependency-first `ModuleGraph.order`;
2. builds one global short-ID owner dictionary from each compiled program's
   directives and functions;
3. walks sorted source-map entries in each module;
4. checks only `directive_invocation` and `function_call` entries; and
5. permits a known owner only when it is the current module or one of
   `ModuleGraph.direct_imports(current)`.

An unknown target has no owner, bypasses this module check, and later fails
linked validation as `APX-VALIDATE-002` (directive) or `APX-VALIDATE-003`
(function). A known but non-visible target fails earlier as `APX-MODULE-008`.
This stage difference is observable.

Local declarations are usable inside their own module. Direct imports grant
the narrow invocation/call permission for every currently supported directive
or function in the imported module because no export filter exists. This is a
consequence of global discovery plus an owner gate, not an implicit export
set.

Legacy/headerless projects skip `validate_module_visibility`; their supported
directives and functions retain project-wide global lookup. Module mode remains
direct-import-only. Imports do not grant runtime authority: public `run` grants
only the selected entry directive's invocation capability.

## Existing export status

There is no ApexForge export system:

- no `export` header keyword, lexer keyword, parser production, AST node, or
  declaration;
- no implicit export set or default-public/default-private rule;
- no `public` or `private` visibility modifier;
- no export list, export-all form, or wildcard;
- no re-export, including no transitive implicit re-export;
- no import alias;
- no namespace model;
- no module-qualified declaration identity or reference spelling;
- no module-qualified entry spelling;
- no export or visibility AIR field;
- no manifest export field;
- no artifact v1 export metadata; and
- no language-server export/private awareness.

`export`, `public`, and `private` currently lex as ordinary identifiers. Used
where a declaration/modifier would appear, they produce ordinary parse
diagnostics rather than recognized export-feature diagnostics. They may still
be used where an identifier is grammatically permitted, which is adjacent
behavior and not a visibility feature.

## Import and direct/transitive visibility behavior

- Importing module `B` grants a source in `A` access to known directive and
  function targets owned by `B`.
- If `B` imports `C`, `A` does not gain access to `C`. The transitive document
  query can return `C`, but using a known `C` target still produces
  `APX-MODULE-008`.
- There is no named-import form; a direct import gates all supported callable
  declarations because no export subset exists.
- A future re-export must require a direct import by the re-exporting module;
  otherwise it would manufacture authority over a declaration with no direct
  dependency edge or source span.
- Transitive imports should never grant visibility by themselves. Any future
  propagation should require an explicit re-export edge.
- Module lookup is exact-case, while module declaration uniqueness is
  case-folded. Export lookup cannot safely choose a new case rule without an
  explicit compatibility decision. The least surprising continuation is exact
  case after exact module resolution, with case-folded duplicate detection.

## Generic and entry-point behavior

Generic declaration ownership follows the unqualified function identity.
`ApexTypeVariable.owner` is `function:Name`; source-map type-parameter IDs are
`type_parameter:Name:index`; explicit and inferred calls retain short targets;
specializations use values such as `Identity<int>`; lowering generates
deterministic concrete function IDs. None contains a source or module identity.

Only linked directives can be selected as entries. The accepted forms are
`Name` and `directive:Name`. With no configured entry, exactly one linked
directive is selected; zero or multiple directives fail at run/entry
resolution, while a non-executing build can record a null entry in the
multiple-directive case. `module.Name`, `module::Name`, and similar spellings
are undefined.

An eventual private/export rule must explicitly decide whether an entry must be
exported. That decision should not be encoded while entry identity is global
and unqualified.

## Identity and naming constraints

Current AIR and reference identities are insufficient for a general export
resolver:

1. Same-kind declarations with the same short name in different modules have
   the same AIR ID and fail with `APX-LINK-001`; they cannot coexist as two
   candidates.
2. Two directly imported modules therefore cannot currently contribute a
   supported ambiguity set for one short name. The project fails as a global
   duplicate even if the declaration is never referenced.
3. The pre-link owner dictionary has one value per short ID. A later duplicate
   overwrites an earlier owner, so it is unsuitable as an ambiguity model.
4. A directive and function with the same short name can coexist only because
   their kind prefixes differ.
5. States, events, and causes remain globally flat even though source lookup is
   directive-local. Exporting them would expose identities that do not encode
   their containing directive.
6. Generic specializations encode type arguments but not module ownership.
7. Entry directives are globally short.

Metadata can safely precede P11.4 when it only records physical source,
optional module, declaration kind, current canonical short AIR ID, and source
span without changing lookup. Default/private enforcement for already unique
directives/functions is technically possible before P11.4, but it would lock
entry, collision, and migration semantics onto an owner map that cannot
represent ambiguity. General export enforcement, same-short-name coexistence,
qualified lookup, imported ambiguity, aliases, re-exports, nested declarations,
flat nested-ID repair, and module-qualified entries require P11.4 identity work
first.

## Candidate export models

No candidate is selected merely because another language uses it. All models
must preserve deterministic source spans, canonical ordering, current module
source limits, and the P11.4 identity direction.

### A. Explicit export list in a module header or declaration section

- **Grammar and spans:** a header form fits the current pre-parser but expands
  its line grammar and masking diagnostics; a declaration section belongs in
  the ordinary parser. Each listed name needs its own exact span.
- **Source shape:** redundant but workable with one declaration per module
  source; naturally extends to multiple declarations later.
- **P11.4/direct imports/duplicates:** it can list short names initially, but
  qualified identity is required for stable resolution and ambiguity. Import
  visibility remains direct plus the listed subset. Duplicate linker behavior
  cannot be relaxed before P11.4.
- **Diagnostics:** unknown export, duplicate list item, non-local export,
  unsupported declaration kind, and private-entry diagnostics need primary
  item spans plus declaration-related spans.
- **CLI/artifact/LSP:** compilation can consume a list without changing CLI
  success text or artifact v1 if metadata is not serialized. Formatting,
  symbols, hover, navigation, references, and rename must understand the list
  once syntax is accepted.
- **Migration/determinism:** requiring a list would break every existing module
  project; treating absence as compatibility-public postpones that break.
  Preserve declaration order for source presentation but canonicalize semantic
  sets by future qualified identity.

### B. Per-declaration `public` or `export` modifier

- **Grammar and spans:** touches the frozen lexer/parser and every declaration
  production; the modifier and declaration each need owned spans.
- **Source shape:** concise for one declaration per source and compatible with
  future multi-declaration sources.
- **P11.4/direct imports/duplicates:** it marks the owner cleanly but does not
  solve short-ID collision or imported ambiguity. Direct import remains
  required. Link duplicates still preempt visibility until identities change.
- **Diagnostics:** duplicate/conflicting modifiers, unsupported kinds,
  non-exported use, private entry, and visibility diagnostics are required.
- **CLI/artifact/LSP:** artifact v1 can remain unchanged only while visibility
  metadata is compile-time-only. Every syntax-oriented LSP surface must change.
- **Migration/determinism:** explicit-export-by-modifier is breaking if absence
  means private; absence-as-current-public reduces migration risk. Canonical
  order follows declaration identity rather than modifier order.

### C. Default-public declarations with optional `private`

- **Grammar and spans:** requires a `private` modifier production and span but
  no positive export declaration.
- **Source shape:** minimal in one-declaration sources and extends to multiple
  declarations.
- **P11.4/direct imports/duplicates:** best preserves current direct-import
  access but would create a real implicit export set, which does not exist now.
  It does not solve global duplicates or ambiguity.
- **Diagnostics:** private cross-module use and private-entry diagnostics are
  central; conflicting modifiers remain possible if public is later added.
- **CLI/artifact/LSP:** compilation-only enforcement could leave CLI/artifact
  bytes unchanged. LSP must display and enforce private boundaries.
- **Migration/determinism:** lowest behavior migration risk for existing module
  projects, but highest risk of prematurely making broad public API the default.

### D. Default-private declarations with explicit export

- **Grammar and spans:** requires either model A or B's syntax and span model.
- **Source shape:** explicit and future-proof, though verbose when every
  one-declaration module is intended as a library surface.
- **P11.4/direct imports/duplicates:** aligns with a narrow API surface but does
  not itself create qualified identity. Direct import remains necessary.
- **Diagnostics:** non-exported use, missing/duplicate export, unsupported
  export kind, and private entry need stable diagnostics.
- **CLI/artifact/LSP:** same compile-only artifact possibility and broad LSP
  syntax/semantic impact as A/B.
- **Migration/determinism:** maximally breaking if applied immediately because
  all existing module declarations become inaccessible. A compatibility epoch
  or explicit migration is required.

### E. Export-all or wildcard forms

- **Grammar and spans:** adds wildcard punctuation/keyword parsing and a span
  for the wildcard or source module.
- **Source shape:** compact now and later, but obscures API review as declaration
  counts grow.
- **P11.4/direct imports/duplicates:** expands every collision and imported
  ambiguity risk. It should not precede qualified identities. Direct import is
  still required by consumers.
- **Diagnostics:** unsupported wildcard target, collision expansion, and
  ambiguity diagnostics require deterministic expansion and related spans.
- **CLI/artifact/LSP:** tooling needs expansion previews and workspace-aware
  references. Serialized export surfaces would require a new artifact schema.
- **Migration/determinism:** easy migration but high accidental-API risk.
  Expansion must sort by canonical qualified identity, never filesystem order.

### F. Re-export of directly imported declarations

- **Grammar and spans:** needs syntax that owns both the direct import/re-export
  relationship and the selected declaration or wildcard span.
- **Source shape:** useful only once modules can expose a stable API facade;
  future multiple declarations increase its value.
- **P11.4/direct imports/duplicates:** requires a direct import and stable
  qualified declaration identity. It cannot be modeled safely by copying a
  global short ID. Imported equal short names require qualification or a
  deterministic ambiguity error.
- **Diagnostics:** missing direct import, non-exported upstream declaration,
  re-export cycle, duplicate re-export, collision, and ambiguity diagnostics
  need both re-export and upstream related spans.
- **CLI/artifact/LSP:** project-aware definition/references/rename and export
  graph traversal become necessary. A distributable artifact export surface
  requires a schema version change.
- **Migration/determinism:** opt-in and non-breaking, but semantically the most
  dependent on P11.4. Re-export closure and cycle traversal require canonical
  qualified ordering.

## Candidate visibility models

The deterministic baseline for any later enforcement should be evaluated as:

- local declarations are always visible in their owning module;
- legacy/headerless projects retain existing global visibility unless a
  separately authorized migration changes them;
- module-mode projects remain same-module plus direct-import-only;
- importing a module exposes its validated export set, not arbitrary transitive
  dependencies;
- transitive access exists only through an explicit re-export edge;
- a re-export requires a direct import;
- module lookup remains exact-case after case-folded uniqueness checks;
- generic ownership follows its function declaration and future qualified
  identity; specializations derive from that owner;
- parsed but non-lowered declaration forms cannot participate in a successful
  project export set and should receive a declaration/export diagnostic only
  after their project lowering is intentionally supported; and
- dependency graph reachability is never itself visibility.

For two directly imported modules exporting the same short name, import-time
rejection is simpler but rejects unused imports and makes import order appear
semantic. A use-site ambiguity diagnostic is more precise and preserves unused
imports, but it requires the resolver to retain both qualified candidates.
Therefore use-site ambiguity is the better eventual model, with the primary
span on the use and related spans on each exported declaration/import path;
it cannot be implemented while same-kind global duplicates fail first.

## Re-export analysis

There is currently no re-export. Direct import of a module neither records an
export edge nor propagates its imports. A safe future re-export requires:

1. a direct import edge owned by the re-exporting source;
2. an upstream declaration that is itself exported;
3. stable qualified declaration identity;
4. a distinct re-export edge rather than copied ownership;
5. cycle detection independent from the already acyclic module-import graph,
   because export selections can create their own graph; and
6. deterministic closure ordered by qualified identity with source-order spans
   retained for diagnostics and formatting.

These requirements place actual re-export behavior after P11.4.

## Ambiguity and collision analysis

Collision is a definition problem: two declarations occupy the same current
global kind-prefixed ID. It produces `APX-LINK-001`. Ambiguity is a lookup
problem: more than one valid, distinct declaration is visible for one source
spelling. The current implementation can represent collision but not ambiguity.

An export system must not rename a collision into an ambiguity while AIR IDs
remain equal. Conversely, after P11.4 permits two qualified declarations, a
short use with both in scope should not be mislabeled as a duplicate. Local
shadowing is also undefined today; no new rule should be inferred from Python
or another language. P11.4 must decide whether local declarations shadow
imports or whether equal visible short names require qualification.

## Diagnostic-stage and span analysis

All existing `APX-MODULE` diagnostics are severity `error`, stage `module`, and
deterministically sorted by `BuildDiagnostic.sort_key()`.

| Code | Existing contract that must remain unchanged |
| --- | --- |
| `APX-MODULE-001` | Malformed/late module or import-looking line; primary is the offending line excluding newline. |
| `APX-MODULE-002` | Second module declaration; primary is the later name, related span is the first name. |
| `APX-MODULE-003` | Import before a module; primary is the import name. A separate module-after-import branch exists but is preempted by `002`. |
| `APX-MODULE-004` | Exact duplicate import; later name primary, first equal name related. |
| `APX-MODULE-005` | Headerless source in mixed mode; zero-width start-of-source primary for each affected source. |
| `APX-MODULE-006` | Missing exact-case imported module; import-name primary. |
| `APX-MODULE-007` | Deterministic cycle; first selected import edge primary and remaining path edges related. |
| `APX-MODULE-008` | Known non-directly-visible directive/function use; call/invocation primary, no related spans, source-reference `air_id`. |
| `APX-MODULE-009` | Case-folded duplicate module; later module-name primary and earlier declaration related. |

The unreachable module-after-import `APX-MODULE-003` branch does not consume a
new number and must not be repaired or exposed as part of export work.
`APX-MODULE-001` through `009` need not be renumbered: later export diagnostics
can use a new stable family such as `APX-EXPORT-*`, or append new module codes
without changing existing values. Exact numbers must be chosen in the stage
that implements them, not by this audit.

Recommended stage ownership for future diagnostics:

- malformed export syntax: lex/parse or module-header parse, matching the
  selected grammar owner;
- duplicate/unknown/non-local export and missing direct import for re-export:
  module/export semantic stage;
- duplicate qualified definitions: link stage;
- a use with multiple distinct visible candidates: resolution/link stage;
- use of a known non-exported declaration: module/export visibility stage;
- private or non-exported entry: entry stage, after a qualified entry contract;
- malformed hand-authored AIR export data: validation stage only if a future
  AIR schema actually contains it.

Unknown/duplicate export diagnostics should use the export item span as primary
and the local declaration or prior export as related. Non-visible uses should
use the reference span as primary and the declaration/export/import spans as
related. `air_id` should remain the source reference sidecar ID for use-site
errors; declaration/export-definition errors should use the canonical
declaration identity once P11.4 defines it. Ordering must use the existing
canonical diagnostic sort key, with related candidates additionally ordered by
future qualified identity and source span.

## CLI and manifest compatibility

The CLI `check`, `run`, and `build` commands all use the same manifest snapshot
and `build_project` pipeline. There is no export command or flag. Successful
output does not mention modules or visibility. `run` entry selection remains
short/canonical directive based and grants authority only to that entry.

Manifest schema 1 permits only `schema`, `name`, `sources`, and optional
`entry`. A metadata-only in-memory ownership/export foundation can remain
compilation-only without changing the manifest, check output, run output,
build output, source order, source hashes, or entry spelling. The manifest
first needs a versioned change only if it must select a module-qualified entry,
declare package/public surface policy, or refer to exported declarations as
distribution metadata.

## Artifact v1 compatibility

Artifact v1 has exactly `schema`, `project`, `air`, and `fingerprint` at the top
level. `project.sources` is canonical manifest/path order with SHA-256 over
exact loaded bytes. Linked AIR order is dependency-first in module mode. The
fingerprint hashes canonical JSON containing `schema`, `project`, and `air`
before the fingerprint record is added.

There is no export, visibility, module qualification, module graph, document
graph, or declaration-owner field. Reading the document graph does not change
artifact bytes or fingerprint. A compile-time-only ownership/export check can
leave artifact v1 byte-identical. The first required artifact change is when a
consumer must discover or link against an exported surface without the source
project, when AIR identities become module-qualified in serialized AIR, or
when re-export/package metadata must be distributed. That requires an explicit
new artifact schema; it must not silently add fields to v1.

## Language-server impact

The language server independently parses one open document through
`parse_module_source` and the ordinary parser. It does not load the manifest,
build `ModuleGraph`/`ProjectDocumentGraph`, link AIR, or validate imports.

| Surface | Current behavior | Future export/private requirement |
| --- | --- | --- |
| Syntax diagnostics | Header lexer/parser diagnostics only; a missing import is silent. Export-looking text is an ordinary parse error. | Parse export syntax and publish its syntax diagnostics; project semantic diagnostics need workspace/project state. |
| Formatting | Reprints module/import headers and one declaration. Invalid source receives no edits. | Preserve export syntax, source-order presentation, modifiers/lists, and idempotence. |
| Document symbols | Module root with import/declaration children; headerless declaration root. | Represent export declarations/modifiers and private/public detail without inventing resolution. |
| Hover | Syntax descriptions for modules/imports and declarations/members. | Show declared/effective visibility and re-export target from validated project state. |
| Definition | Same-document syntax/lexical graph; module declaration self-defines; imports are unresolved. | Resolve imports, exported uses, re-exports, and qualified identities across files. |
| References | Same-document occurrences only. | Include cross-file import/export/re-export/use references with stable identity. |
| Rename | Lexically complete locals/members only; modules and workspace-visible declaration families are protected. | Rename qualified declarations, export list items, imports, re-exports, and uses atomically; reject visibility collisions. |
| Workspace symbols | Recursively scans `.apex` files and flattens syntax symbols, honoring open overlays; no manifest or resolution. | Filter/annotate exports/private declarations only after a project-aware index exists; retain deterministic paths and overlay handling. |
| Imports | Completion/hover/symbol syntax only; no module-name index or cross-file definition. | Complete/resolve module names, then expose only validated exports. |
| Ambiguity diagnostics | None. | Emit use-site ambiguity with all candidate declaration/import spans after qualified identities exist. |
| Cross-file resolution | Deferred. | Consume the canonical declaration ownership/export index rather than independently rebuilding semantics. |

Accepting export syntax without updating diagnostics, formatting, document
symbols, hover, and the frozen integration fingerprints would create another
build/LSP asymmetry. Therefore the recommended P11.3D avoids syntax.

## ProjectDocumentGraph boundary

P11.3B remains a physical-document/dependency graph:

- it contains `ProjectDocument` records and `ResolvedImportEdge` edges only;
- it contains no declaration, export, reference, visibility, namespace,
  qualification, AIR, artifact, or language-server nodes;
- `ModuleGraph` retains only `modules` and dependency-first `order`;
- graph access does not compile, link, execute, serialize, or change artifact
  v1 bytes/fingerprint;
- direct and transitive dependency queries do not define declaration
  visibility;
- legacy projection contains every physical document with no invented module
  name or edges while `ModuleGraph()` remains empty; and
- manually constructed `ProjectBuild` values retain the empty
  `ProjectDocumentGraph()` compatibility default and pre-P11.3B equality.

Declaration/export data should be held beside this graph and reference physical
documents by canonical source name. Extending `ProjectDocumentGraph` with
semantic nodes would collapse the boundary P11.3B intentionally established.

## Frozen compatibility requirements

Any later P11.3 slice must preserve, unless a separately authorized and tested
compatibility change says otherwise:

1. the P10 and P11.2 frozen grammar, diagnostics, compiler/runtime behavior,
   authority boundaries, CLI, artifacts, and language-server contracts;
2. exact offset/line/column-preserving module-header masking;
3. headerless legacy projects and P11.2B multi-directive source order;
4. one ordinary declaration per module source;
5. mixed-mode failure, exact-case import lookup, and case-folded module/source
   uniqueness;
6. dependency-first module compilation/link order and canonical lexical
   tie-breaking;
7. direct-only directive/function module visibility and legacy global
   behavior;
8. unknown-reference validation staging;
9. short/canonical entry forms and fallback behavior;
10. global duplicate `APX-LINK-001` behavior until identity work explicitly
    changes it;
11. generic inference, specialization closure, and lowering;
12. no import-derived runtime authority;
13. manifest schema 1 and artifact v1 bytes, source order, hashes, and
    fingerprint; and
14. `APX-MODULE-001` through `009`, including the preempted branch boundary.

## Architectural risks

1. **Temporary owner overwrite.** The visibility dictionary cannot represent
   multiple same-short-name candidates and can select the last duplicate before
   linking rejects it.
2. **Global short identities.** Module ownership disappears from AIR, nested
   state/event/cause IDs, generic specializations, and entries.
3. **Special-case visibility.** New reference kinds are globally visible unless
   explicitly added to the two-kind source-map check.
4. **Stage split.** Known invisible and unknown targets fail at different
   stages, complicating future export diagnostics.
5. **Case split.** Case-folded uniqueness and exact-case lookup can produce
   apparently inconsistent user results.
6. **Parsed/non-lowered forms.** Syntax and language-server features advertise
   declaration families that cannot enter a project export set.
7. **Entry exposure.** A private/export rule can silently make an existing
   manifest entry invalid unless sequencing is explicit.
8. **Graph boundary erosion.** Putting declarations into the document graph
   would mix physical reachability with semantic visibility.
9. **Artifact drift.** Serializing compile-time metadata into artifact v1 would
   change bytes and fingerprints even when runtime behavior is unchanged.
10. **Build/LSP divergence.** Adding syntax without project-aware tooling would
    make accepted build behavior partially invisible or uneditable in the LSP.

## P11.3 non-goals

P11.3C implements none of the following, and the recommendation does not
silently include them:

- production-code changes;
- an export keyword, public/private modifier, export list, wildcard, or
  re-export;
- aliases, namespaces, qualified identities/references/entries, or P11.4;
- multiple declarations in module sources or nested declarations;
- new AIR, manifest, artifact, CLI, language-server, runtime-authority, or
  diagnostic behavior;
- promotion of workflow, authority, principal, or role source forms into the
  canonical project compiler; or
- implementation of P11.3D or any later stage.

## Recommended P11.3D slice

**Proposed stage name:** P11.3D Canonical Declaration Ownership Index.

The smallest coherent production step is a metadata-only ownership foundation
for later exports, not export syntax and not visibility enforcement. It can
safely precede P11.4 because it records current facts without changing identity
or lookup.

### Exact public model additions

Add a new production module `apexforge/language/declarations.py` containing:

- frozen `ProjectDeclarationOwner(kind, air_id, source_name, module_name,
  span)`, where `kind` is exactly `directive` or `function` in this slice,
  `air_id` is the current canonical short ID, `module_name` is optional for
  legacy mode, and `span` is the existing top-level source-map span; and
- frozen `ProjectDeclarationOwnership(declarations=())`, with deterministic
  canonical declaration order and read-only queries `for_source(source_name)`,
  `for_module(module_name)`, and `find_all(air_id)`.

The plural `find_all` is deliberate: the metadata model must retain duplicate
owners long enough for the existing linker to report them rather than
overwriting one owner. Constructor validation should require one source span,
exact source/module spellings, recognized project declaration kinds, and
canonical current IDs. Canonical order should be `(air_id, source span)` with
case-folded/original source-name components included in the span key.

Append `declaration_ownership` to `ProjectBuild` after `document_graph`, with an
empty factory default and `compare=False`, preserving all existing positional
construction and equality. Successful builds populate it from each per-source
`CompiledSource` before the artifacts lose their physical grouping. Legacy
records use `module_name=None`; module records use the already validated exact
module spelling.

Do **not** add `exported`, `public`, `private`, export-set, or reference-edge
fields in P11.3D. That avoids disguising today's direct-import gate as an
implicit export policy. A later post-P11.4 slice can add a distinct validated
export index keyed by qualified declaration identity.

### Exact production files likely to change

- Add `apexforge/language/declarations.py`.
- Modify `apexforge/language/project.py` only to construct/expose the immutable
  ownership index while per-source artifacts and module mapping are available.

No change is authorized by this audit; these are the proposed P11.3D files for
owner review. `modules.py`, `grammar.py`, `lexer.py`, `parser.py`, `compiler.py`,
AIR, linker, validator, manifest, CLI, artifact, runtime, and language-server
files should remain unchanged in that slice.

### Parser, compatibility, and diagnostics behavior

P11.3D should add no grammar/parser behavior. `export`, `public`, and `private`
remain ordinary identifiers and invalid as declaration modifiers. Compilation,
linking, validation, entry selection, execution, direct/transitive visibility,
legacy behavior, source order, AIR order, CLI output, manifest schema 1,
artifact v1 bytes/fingerprint, and language-server behavior remain exact.

No diagnostic should be added. Existing duplicate declarations still reach
the linker and produce the existing `APX-LINK-001` with unchanged primary and
related spans. Existing `APX-MODULE-001` through `009`, including the preempted
branch, remain unchanged. The ownership index is not consumed by visibility in
the same slice, so it cannot reorder or restage errors.

### Exact tests

Add one focused P11.3D smoke test that verifies:

1. legacy and module directives/functions have exact owner records and spans;
2. generic functions remain kind `function` and retain current type-parameter
   ownership;
3. reversed source mapping order produces identical canonical ownership;
4. equal short IDs from different sources are both retained by `find_all`
   before the existing deterministic link error is reported;
5. non-lowered top-level forms retain their existing compile failures and do
   not create successful ownership records;
6. `SourceUnit`, `ModuleSource`, `ModuleRecord`, `ModuleGraph`,
   `ProjectDocument`, and `ProjectDocumentGraph` shapes are unchanged;
7. manual `ProjectBuild` construction receives the empty compatibility default;
8. direct/transitive/legacy visibility, generics, and entry selection are
   unchanged;
9. CLI `check`/`run`/`build` output and artifact v1 bytes/fingerprint are
   unchanged;
10. language-server behavior and frozen fingerprints are unchanged; and
11. focused tests precede the complete regression harness, with actual
    discovery count reported.

### Explicit P11.3D non-goals

No export syntax or metadata, visibility enforcement, resolver replacement,
qualified identity, ambiguity behavior, collision relaxation, re-export,
alias, namespace, entry change, nested declaration, multiple module
declarations, parsed-form promotion, AIR/schema change, diagnostic, CLI,
artifact, manifest, language-server, runtime, or authority change.

P11.3D can safely precede P11.4 only with this metadata-only boundary. Actual
export enforcement should be postponed until P11.4 supplies qualified
declaration identity and an ambiguity-capable resolver.

## Exact P11.3D acceptance checklist

- [ ] Repository branch, HEAD, cleanliness, freeze tag, ancestry, and stage
  guardrails are verified before edits.
- [ ] Only the separately authorized P11.3D files are changed.
- [ ] Every successfully compiled directive/function has one immutable owner
  record with exact source/module spelling and declaration span.
- [ ] Legacy ownership records contain no invented module identity.
- [ ] Duplicate current short IDs are representable as multiple owner records;
  the existing linker remains the diagnostic authority.
- [ ] Canonical ownership ordering is deterministic under mapping insertion
  reversal.
- [ ] No export/visibility/reference nodes enter `ProjectDocumentGraph` or
  `ModuleGraph`.
- [ ] `ProjectBuild` positional construction/equality compatibility and empty
  manual default are preserved.
- [ ] No grammar, lexer, parser, compiler, AIR, linker, validator, runtime,
  manifest, CLI, artifact, or language-server production file changes.
- [ ] No export policy, implicit export set, syntax, enforcement, re-export,
  alias, namespace, qualification, ambiguity, or P11.4 behavior appears.
- [ ] Existing module/link/validate/entry diagnostics and spans remain exact.
- [ ] Direct-import-only module behavior, legacy global visibility, generics,
  entry selection, CLI output, and artifact v1 bytes remain exact.
- [ ] Focused validation and the full harness pass; actual counts and final
  repository status are reported without declaring a milestone frozen or
  complete.

## Test record

The executable audit record is
`apexforge/p11_3c_export_visibility_architecture_audit_smoke_test.py`. It is
read-only with respect to production files and covers:

- absent export/public/private syntax and the exact parser declaration
  inventory;
- supported, partial, and rejected lowering boundaries;
- source-map ownership evidence and global short nested IDs;
- direct directive/function imports, transitive rejection, and legacy global
  visibility;
- same-kind `APX-LINK-001` collision rather than a supported ambiguity set;
- generic declaration ownership, inferred specialization, closure, and
  lowering;
- short/canonical entries and rejected module-qualified spellings;
- exact `ProjectDocumentGraph`/`ModuleGraph` fields and compatibility default;
- reachable `APX-MODULE-001` through `009` behavior and the preempted
  module-after-import branch;
- exact CLI check/run behavior, stable build output boundary, artifact v1
  bytes/fingerprint/field exclusions;
- syntax-oriented and same-document language-server behavior;
- external, network-free, deterministic temporary fixtures removed by their
  context manager; and
- unchanged `git status --porcelain=v2 --untracked-files=all` before and after
  the smoke test body.

Validation uses UTF-8 mode, `PYTHONDONTWRITEBYTECODE=1`, and `py -3 -B`. The
executing agent reports the focused matrix, failures, complete regression
discovery count, and final repository status rather than embedding a permanent
harness-count claim in this audit.
