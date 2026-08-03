# P11.4A Identity and Nesting Architecture Audit

## Scope and frozen baseline

This is an audit-only record of the implementation on branch
`p11.4-identity-nesting` at required starting commit `bf779d7` (`Advance P11.4
to identity and nesting audit`). P11.3 is frozen at
`05d836a58722b5fbb42ef2958f2e58d2df472d03` under
`afp-p11.3-freeze`; P11.2 and P11.1 remain frozen at `6b82f79` and `5ba048a`.

The only additions in this slice are this document and
`apexforge/p11_4a_identity_nesting_architecture_audit_smoke_test.py`. No
production file is changed. This audit does not implement or canonize a P11.4B
model, qualified identity, alias, namespace, export, visibility rule, nested
declaration, diagnostic, entry spelling, artifact field, CLI feature, or
tooling behavior.

The audit uses these terms precisely:

- a *declaration* is a source construct named by the parser;
- a *successful project declaration* is a declaration that becomes part of a
  successful canonical `ProjectBuild`;
- an *AIR ID* is the current string stored on an AIR value;
- a *sidecar ID* is a `SourceMapEntry.air_id` that may not exist in AIR;
- *canonical* describes an implementation's current canonical key, not a
  decision that the key is the final P11.4 identity design;
- *collision* means two definitions occupy one current key;
- *ambiguity* means two distinct valid candidates are visible for one
  reference. The current implementation represents collisions but cannot
  reach a supported same-kind imported ambiguity set.

## Audit method

The audit read the P11 continuity pulse; P11.2A/P11.2B and P11.3A through
P11.3D accepted records; their executable smoke tests; lexer, parser, source,
compiler, project, module, diagnostic, AIR, linker, validator, runtime,
manifest, CLI, artifact, generic, language-server, VS Code, and Visual Studio
surfaces; and the relevant P7 through P11 regression records.

The companion smoke test is a current-behavior test, not a proposed-feature
test. It composes accepted P11.2/P11.3 helpers and adds direct probes for exact
ID formats, all unsupported declaration nestings, legal member/control-flow
nesting, lexical scopes, generic key/lowering identity, entry case behavior,
LSP fingerprints, Visual Studio parity, network isolation, external temporary
fixtures, working-directory preservation, repository-status preservation, and
absence of tracked/staged changes.

Assumptions and unresolved boundaries:

1. `canonical AIR ID` below means the key currently enforced by linking or
   runtime lookup. It does not imply module qualification.
2. Parsed-only workflow, authority, principal, and role forms are inventory
   facts, not supported project declarations.
3. A display qualification such as `App.Core.Main` can be useful metadata but
   is not source syntax and must not be treated as resolvable without a later
   resolver contract.
4. No current evidence supports a parent declaration identity for successful
   project declarations because nested directive/function declarations are
   illegal. Nested members have inconsistent AIR containment and should not be
   promoted silently.
5. Export policy remains deferred. Existing direct-import permission is not an
   implicit export set.

## Current declaration inventory

### Ordinary top-level forms

The lexer/parser recognizes exactly six ordinary top-level declaration
keywords. `parse()` returns one AST node and then requires EOF. P11.2B adds a
legacy-only tuple of sequential directives without adding a declaration kind.

| Form and source shape | AST and compilation | Successful `ProjectBuild`, AIR, identity | Ownership, duplicates, entry/runtime/artifact | Language server |
| --- | --- | --- | --- | --- |
| `directive Name { ... }` | `DirectiveNode`; fully compiled | Yes. `AIRDirective(id="directive:Name", name="Name")` plus synthetic principal/check and flattened member AIR | One `ProjectDeclarationOwner`; optional module metadata. Global same-ID collision. Only entry-eligible family. Runtime behavior and artifact AIR present. | Top-level symbol with member children; syntax hover/completion/formatting; same-document occurrence behavior; no semantic cross-file resolution. |
| `function Name(...) { ... }` | `FunctionNode`; fully compiled | Yes. `AIRFunction(id="function:Name", name="Name")` | One owner. Global same-ID collision. Not an entry. Pure-function runtime and artifact AIR present. | Function symbol with type-parameter, parameter, and local children; same-document lexical intelligence only. |
| `function Name<T...>(...) { ... }` | The same `FunctionNode`, with `TypeParameterNode` values | Yes. Declaration remains `function:Name`; generic metadata is attached to `AIRFunction` | One function owner only. Specializations and lowered targets are not owners or entries. Source-generic AIR is serialized by ordinary build. | Displayed as a function with type-parameter children; no module-aware generic resolution. |
| `workflow Name { invoke Target... }` | `WorkflowNode`; main compiler emits `APX-COMPILE-007` | No canonical project AIR | No owner, module visibility, link duplicate, entry, runtime, CLI artifact, or project identity. A separate legacy engine is outside the project pipeline. | Syntax symbol/hover/formatting exist. Declaration rename and semantic target resolution are protected/deferred. |
| `authority Name extends Parent? { capability ... }` | `AuthorityNode`; main compiler emits `APX-COMPILE-007` | No canonical project AIR | No owner or project identity. Separate legacy helper is outside the pipeline. Directive member `authority Name` is only a reference. | Syntax symbol with capability children; semantic resolution is absent. |
| `principal Name { authority/role ... }` | `PrincipalNode`; main compiler emits `APX-COMPILE-007` | No canonical project AIR | No owner or project identity. It is distinct from a compiled directive's synthetic principal. | Syntax symbol with reference children; semantic resolution is absent. |
| `role Name { authority ... }` | `RoleNode`; compiler returns standalone `AIRRole`, then `ProjectBuilder` emits `APX-COMPILE-999` because the result is not `AIRProgram` | No successful project declaration. Standalone `AIRRole.name` is unprefixed; its source map uses `role:Name`. | No project owner, linked identity, entry, runtime, or artifact from source. | Syntax symbol with authority-reference children; workspace-visible rename is protected. |

There is no `IdentityNode`, identity keyword, or separate identity declaration
family. `Identity` in generic tests is an ordinary function name. A generic
function is not a seventh top-level declaration kind.

### Nested and lexical forms

| Source form | Legal owner | AST / AIR or sidecar representation | Identity and project status |
| --- | --- | --- | --- |
| State | Directive | `StateNode` / `StateDefinition` | `state:Name`; directive-local source lookup but globally flat link identity; not a project declaration owner. |
| Event | Directive | `EventNode` / `EventDefinition` | `event:Name`; directive-local source lookup, globally flat link identity; not an owner. |
| Cause | Directive | `CauseNode` / `CausalDecision` | `cause:Name`; syntactically directive-owned, globally flat link identity; not an owner. |
| Path | Cause | `PathNode` / `CausalPath` nested in a decision | `path:Name`; uniqueness is checked within one cause, so the same ID may occur in separate causes; not an owner. |
| Value parameter | Function header | `ParameterNode` / `AIRParameter` | Lexical name; sidecar `parameter:Function:index`; not a global declaration. |
| Local binding | Function body/branch | `LetNode` / `AIRLocalBinding` | Lexical name; positional sidecar `local:Function:scope`; not global. |
| Generic type parameter | Function header | `TypeParameterNode` / `ApexTypeVariable` | Name plus owner `function:Function`; sidecar `type_parameter:Function:index`. |
| Generic specialization | Inferred or explicit call | `GenericSpecializationKey` / `GenericSpecialization` | Compile-time key `Target<Type,...>`; not a source declaration or ownership record. |
| Lowered generic target | Explicit lowering result | Generated `AIRFunction` and `LoweredSpecializationBinding` | Synthetic `function:__apx_spec__...`; absent from an ordinary `ProjectBuild` and its artifact unless a separate caller serializes lowered output. |
| Requirement | Directive | `RequirementNode` / `DirectiveRequirement` | Sidecar `requirement:Directive:index`; AIR value contains capability/principal, not that ID. |
| Directive authority reference | Directive | `DirectiveAuthorityNode` / `DirectiveAuthority(name)` | Name-keyed link value, not `auth:Name`; duplicate falls through `APX-LINK-999`. |
| Invocation/call | Path action/expression | `InvokeActionNode` / `DirectiveInvocation`; `CallExpressionNode` / `AIRCallExpression` | References, not declarations. Sidecars are `invoke:scope:index` and `function_call:scope:index`. |
| `when`/`otherwise` | Function body or path action stream | Function/path conditional nodes and AIR conditionals | Structural control flow and lexical branch scope, not declaration identity. |

States, events, causes, paths, parameters, locals, and type parameters must not
be described as independent top-level project declarations.

## Current identity-layer inventory

All source identifiers and current AIR/reference matching are case-sensitive.
Module declarations are unique under `casefold()` but module/import lookup is
exact-case. No normalization joins those two rules.

| Category | Status, creator, and exact shape | Unique/module-aware/persisted/addressable/resolution role |
| --- | --- | --- |
| Declared identity | Partial. AST `.name` for six top-level forms and nested named forms; exact source spelling. | Not globally unique by itself; not module-aware. Only directive/function declarations survive the project pipeline. User-addressable where grammar/API permits. |
| Source spelling | Present in AST names/references, `SourceMapEntry.reference`, AIR `.name`, and module records. | Exact-case; retained in memory and often AIR/artifact. Not a separate identity object. |
| Display identity | Partial/conflated. AIR `.name`, `Principal.display_name`, LSP symbol names, CLI entry text, and trace facts display short names or current IDs. | No canonical display model; not reliably unique or module-aware. |
| Canonical identity | Partial and overloaded. Current AIR strings (`directive:`, `function:`, member prefixes), generic `canonical_id`, standard-library IDs. | Link keys are globally flat; specialization keys are separate compile-time keys. Module-unaware. Some serialize into artifact v1. |
| Short identity | Present as declaration `.name`, call/invoke target, and entry short spelling. | Exact-case, unqualified, user-addressable, kind-selected by each resolver. Not globally unique across kinds. |
| Module identity | Present in `ModuleSource`, `ModuleRecord`, `ModuleGraph`, `ProjectDocument`, and ownership metadata. Shape is dotted identifier segments such as `App.Core`. | Declaration uniqueness is case-folded; lookup exact-case. In-memory only; absent from artifact v1 AIR and entry. |
| Module-qualified identity | Absent. | No grammar, resolver, AIR, entry, artifact, or tooling semantic form. |
| Alias identity | Absent. | `import ... as ...` is malformed module syntax. No alias binding or alias-aware lookup. |
| Namespace identity | Absent. | `namespace` is an ordinary identifier and fails as a top-level declaration. |
| Composite identity | Partial, nonuniform. Generic keys use `Target<Type,...>`; open type arguments use `owner::name`; event-record IDs concatenate runtime components; sidecar scopes concatenate components. | These are internal/runtime keys, not a general declaration identity or source qualification scheme. |
| Ownership identity | Present as `ProjectDeclarationOwner(kind, air_id, source_name, module_name, span)`. | Exact-case immutable metadata for directives/functions only. Duplicates retained. Not used for resolution and not serialized. |
| Source-map identity | Present as `SourceMapEntry(air_id, span, kind, reference)`. | Deterministic in-memory sidecar; many IDs are synthetic/positional. Used to attribute diagnostics and module reference checks; omitted from artifact v1. |
| Linked AIR identity | Present on AIR `id` fields and name-keyed authority/role values. | Global and module-unaware. Linker uniqueness is per collection/kind, except paths remain nested within causes. Serialized by `air_to_dict`. |
| Runtime identity | Present. Directives/functions use linked IDs; frames retain function ID/name; runtime events compose directive/decision/path/index/event; trace facts carry current IDs. | Module-unaware and externally observable in traces/diagnostics. |
| Entry identity | Present. `Name` becomes `directive:Name`; already canonical `directive:Name` is accepted. | Exact-case, directive-only, globally unqualified. Manifest and CLI override are user-addressable; artifact stores resolved canonical entry. |
| Generic declaration identity | Present as `function:Name`; each `ApexTypeVariable.owner` equals that ID. | Global, module-unaware, serialized in function/type metadata. |
| Generic specialization identity | Present as `GenericSpecializationKey.canonical_id`, e.g. `Identity<int>`. | Exact-case target string plus ordered type identities; canonical within a specialization table, module-unaware, not an ordinary project artifact field. |
| Lowered target identity | Present only after explicit lowering: `function:__apx_spec__Target__Types__<10 hex>` and the corresponding unprefixed function name. | Deterministic/synthetic, collision-checked against linked function names/IDs, module-unaware, runtime dispatch target of lowered AIR. |
| Principal identity | Partial. Compiled directives synthesize `principal:Directive`; source principal declarations do not enter the project. | Global and serialized; used by authority/runtime. Source-map kind `principal` points at the directive span. |
| Authority-check identity | Present for compiled directives as `auth:Directive`. | Global, serialized, and referenced from `AIRDirective.authority_checks`; not a source authority declaration identity. |
| State identity | `state:Name`. | Globally flat after linking, though source actions resolve from the containing directive's complete state map. Serialized and runtime-relevant. |
| Event identity | `event:Name`. | Same split as state. Serialized and runtime-relevant. |
| Cause identity | `cause:Name`. | Globally flat; referenced by its containing directive. Serialized and runtime-relevant. |
| Path identity | `path:Name`. | Cause-local validation and nested storage; repeated IDs across causes are possible. Serialized and runtime-relevant. |

The major conflations are: current AIR ID versus final canonical declaration
identity; short name versus display name; module ownership versus visibility;
and source-map sidecar ID versus real AIR identity. Generic specialization's
`canonical_id` is canonical only within the P9 generic subsystem.

## Exact canonical ID inventory

| ID or spelling | User-declared/synthetic and boundary | Module-qualified? | Artifact v1 |
| --- | --- | --- | --- |
| `directive:<name>` | User declaration lowered to global linked AIR | No | Yes, including resolved entry when selected |
| `function:<name>` | User function/generic declaration; global linked AIR | No | Yes |
| `principal:<directive-name>` | Synthetic per compiled directive | No | Yes |
| `auth:<directive-name>` | Synthetic authority check per directive | No | Yes |
| `state:<name>` | User nested member; directive-local source map, global link key | No | Yes |
| `event:<name>` | User nested member; directive-local source map, global link key | No | Yes |
| `cause:<name>` | User nested member; global link key | No | Yes |
| `path:<name>` | User nested member; cause-local nested key | No | Yes |
| `requirement:<directive>:<index>` | Synthetic source-map-only position | No | No; requirement values serialize without this sidecar ID |
| `parameter:<function>:<index>` | Synthetic source-map-only position | No | No ID; parameter name/type serialize |
| `type_parameter:<function>:<index>` | Synthetic source-map-only position | No | No sidecar ID; type-variable name/owner serialize |
| `local:<function>:<scope>` | Synthetic lexical source-map position | No | No ID; local name/expression serialize |
| `function_when:`, `return:`, `function_call:` | Synthetic positional source-map IDs | No | No |
| `invoke:`, `assignment:`, `emit:`, `when:` | Synthetic path/action sidecar IDs | No | No |
| `role:<name>` | Source-map sidecar for standalone role lowering; `AIRRole.name` itself is unprefixed | No | No successful project artifact |
| `Identity<int>` | Generic specialization key and display string | No | Omitted from ordinary project artifact; exists in explicit closure/lowering result |
| `function:__apx_spec__Identity__int__<digest>` | Synthetic lowered concrete AIR function; digest is first 10 SHA-256 hex characters of specialization canonical ID | No | Not in ordinary build artifact; serializable only if a caller explicitly serializes lowered AIR |
| `Name` / `directive:Name` | Short and canonical entry inputs | No | Artifact stores resolved `directive:Name`, or null under established build rules |
| `<directive>:<decision>:<path>:event:<index>:<event>` | Synthetic runtime event-record composite ID | No | Runtime only, not build artifact |

No delimiter here is a reserved general qualification grammar. In particular,
`<...>` is already generic call/type-argument syntax, `::` already appears in
open generic type-variable encoding, and `:` is heavily used by AIR and
sidecar IDs. A future qualified-name syntax cannot be chosen by string
concatenation alone.

## Ownership-index interaction

P11.3D's exact public surface remains:

```text
ProjectDeclarationOwner(
    kind,
    air_id,
    source_name,
    module_name,
    span,
)
ProjectDeclarationOwnership(declarations=())
```

Both dataclasses are frozen. Kinds are exactly `directive` and `function`.
AIR IDs must be current unqualified `directive:<identifier>` or
`function:<identifier>` strings. Source and optional module spellings are
stored exactly; the span must belong to the source.

Canonical owner order is:

1. `air_id`;
2. `source_name.casefold()`;
3. exact `source_name`;
4. span start offset;
5. span end offset;
6. kind;
7. whether module is non-`None`, with legacy first; and
8. exact module name, using empty string only as the sort proxy for `None`.

`for_source`, `for_module`, and `find_all` use exact-case queries and return
tuples in collection order. Equal AIR IDs are retained as separate owners;
there is no winner. Legacy owners have `module_name=None`; explicit modules
retain exact validated spelling. P11.2B contributes every directive from its
one physical source. A generic function contributes one function owner;
specializations and lowered targets contribute none.

The index exists only on a successful `ProjectBuild`. Failed duplicate builds
expose no partial build. Manual `ProjectBuild` construction receives the empty
default. An injected compiler returning a bare `AIRProgram` supplies no source
map, so the builder deliberately fabricates no owner/span.

P11.3D solves immutable physical/module ownership for successful directive and
function declarations, deterministic ordering, exact spans, duplicate-fact
retention in the public model, and a stable metadata boundary beside the
document/module graphs. It intentionally does not:

- qualify or rewrite an AIR ID;
- alter reference resolution or linker order;
- grant visibility or exports;
- resolve ambiguity or collisions;
- create aliases or namespaces;
- change entry selection or runtime authority;
- add/reorder diagnostics;
- enter manifest or artifact v1;
- change CLI output, language-server behavior, or Visual Studio behavior; or
- represent nested members, generic instantiations, or lowered targets.

## Module and import interaction

`ModuleGraph` owns only `modules` and dependency-first `order`.
`ProjectDocumentGraph` owns physical documents, resolved import edges,
canonical physical order, and dependency order. The ownership index is a
separate projection. Module ownership, document reachability, narrow module
visibility, and AIR identity are four distinct mechanisms.

| Question | Current behavior |
| --- | --- |
| Module-name uniqueness | Case-folded: `App.Core` conflicts with `app.core` using `APX-MODULE-009`. |
| Import lookup | Exact-case: importing `app.core` does not find `App.Core`; `APX-MODULE-006`. |
| Same-module access | Known directive invocations/function calls are permitted. |
| Direct import | Grants the narrow known-target invocation/call gate for all supported declarations in that module; this is not an export set. |
| Transitive dependency | Affects graph/build order only; no declaration visibility. Known use fails `APX-MODULE-008`. |
| Legacy mode | Module graph is empty; directive/function lookup remains project-global. |
| Same short name in distinct modules | Same-kind declarations still share one global AIR ID and fail `APX-LINK-001`. |
| Cross-kind equal name | Accepted because `directive:` and `function:` are separate keys. |
| Module-qualified reference/entry | Unsupported. Dot-qualified references currently fail lexically; dotted/`::` entries are undefined. |
| Alias/import alias | Unsupported; alias-looking header is `APX-MODULE-001`. |
| Namespace | Unsupported top-level identifier. |
| Export/re-export/visibility modifier | Absent. `export`, `public`, and `private` are ordinary identifiers and fail in declaration positions. |

`validate_module_visibility` reconstructs a temporary dictionary from global
directive/function IDs to one module. A later duplicate overwrites an earlier
owner before the linker rejects the collision. This dictionary is therefore
not an ambiguity-capable resolver and must not become the P11.4 identity
index.

## Duplicate and collision matrix

All deterministic multi-source primary/related selection uses canonical
source-map order: case-folded source name, exact source name, offsets, then
entry fields. Ownership retains only directive/function definition facts.

| Case | Result and diagnostic | Span / ordering / identity cause | Ownership fact |
| --- | --- | --- | --- |
| Duplicate directives | Reject at link, `APX-LINK-001`; currently the first collision is normally `principal:Name` because principals merge before directives | First canonical directive span primary, later span(s) related; global synthetic principal and then directive IDs collide | Both directive owners can be represented by the collection, but failed build returns no index |
| Duplicate functions | Reject at link, `APX-LINK-001`, `air_id=function:Name` | First definition primary, later related; global flat function ID | Both facts representable; no successful build |
| Directive/function same short name | Accept | Prefix namespaces differ; resolvers select kind first | Two owners with distinct kinds/IDs |
| Duplicate state | Reject at link, `APX-LINK-001`, `state:Name` | First member span primary, later related; globally flat despite directive-local source lookup | Not retained by P11.3D |
| Duplicate event | Reject at link, `APX-LINK-001`, `event:Name` | Same as state | Not retained |
| Duplicate cause | Reject at link, `APX-LINK-001`, `cause:Name` | Same as state | Not retained |
| Same state/event/cause/path short spelling | Accept across kinds | Prefix and nested collection separate them | Nested members not retained |
| Duplicate path in one cause | Reject in validation with fallback `APX-VALIDATE-999`; empty `air_id`, no source/related span | Cause-local nested ID collision; diagnostic mapping is weak | Not retained |
| Same `path:Name` in separate causes | Accept | Paths remain nested; no global path linker table | Not retained |
| Same supported name in separate modules | Reject at link as the same global ID | Module owner is not part of identity | Duplicate owners are representable before failure |
| Equal generic declaration names/signatures | Reject as duplicate `function:Name`; no overload set | Type-parameter names/signature do not change declaration identity | Duplicate function owners representable |
| Equal specialization keys from repeated calls | Deduplicated in canonical specialization table | Same `Target<Type,...>` key; equal projection is one record, conflicting projection raises generic conflict | Specializations excluded |
| Same generated lowering target | Deterministically the same binding for same specialization; generated collision with an existing function is `APX-LOWER-003` | SHA-derived synthetic name plus occupied-name/ID check | Excluded |
| Module-name case collision | Reject in module stage, `APX-MODULE-009` | Later canonical source's module-name span primary, earlier related | No build/index |
| Import case mismatch | Reject `APX-MODULE-006` | Import-name span primary, exact lookup | No build/index |
| Ambiguous direct imports | Not currently reachable as a supported ambiguity | Same-kind equal declarations collide globally first; temporary owner map has one value | Index can retain facts but no resolver consumes them |
| Directive authority duplicate | Reject at link fallback `APX-LINK-999`, key is unprefixed authority name | Current mapping has no source span/related spans | Not retained |
| Duplicate function parameter | Compile `APX-COMPILE-008` | Function declaration span, `air_id=function:Name`; exact-case | No successful owner |
| Duplicate/parameter-shadowing local | Compile `APX-COMPILE-009` / `010` | Function span, `air_id=function:Name`; sequential lexical namespace | No successful owner |
| Forward local reference | Validate `APX-VALIDATE-006` | Function declaration mapped as primary, `air_id=function:Name` | No successful owner |
| Duplicate generic type parameter | Parse `APX-PARSE-009` | Later type-parameter token primary; no related spans/air_id | No owner |
| Built-in type shadow by generic parameter | Parse `APX-PARSE-010` | Type-parameter token primary | No owner |

Current collision is caused by globally flat IDs, not by module visibility.
Current ambiguity is absent because colliding candidates cannot coexist. A
future resolver must preserve the distinction: a definition collision and a
use-site ambiguity are not interchangeable diagnostics.

## Ambiguity analysis

The implementation has no ambiguity result object, overload set, candidate
list, alias expansion, or namespace lookup. Resolver surfaces choose a kind
before lookup and accept one short/canonical string. Two different kinds with
one spelling are therefore not ambiguous. Two same-kind declarations cannot
coexist because linking fails. Two imported same-kind declarations likewise
cannot reach a use-site ambiguity.

After a future identity layer permits two qualified declarations, an
unqualified use with both visible should be a use-site ambiguity with the use
span primary and all candidates/import paths related in deterministic
qualified-identity/source order. P11.4A does not assign a code or implement
that behavior.

## Generic identity lifecycle

1. The parser creates one `FunctionNode` named `Identity` and
   `ApexTypeVariable(name="T", owner="function:Identity")`.
2. Compiler source-map IDs are `function:Identity`,
   `type_parameter:Identity:0`, and `parameter:Identity:0`. AIR stores the
   function ID and owned variable.
3. Calls retain a short target (`Identity`) plus optional explicit type
   arguments. Inference and explicit arguments both create a
   `GenericSpecializationKey(target="Identity", type_arguments=(int,))`.
4. The key's current canonical/display string is `Identity<int>`. An open
   type-variable argument is encoded as `<owner>::<name>` inside the angle
   brackets.
5. `GenericInstantiationTable` deduplicates equal closed keys and orders by
   canonical ID. A conflicting projection for one key is an error.
6. `GenericSpecializationManifest` adds deterministic caller/callee closure
   edges; closure remains module-unaware because targets are short/global.
7. Explicit lowering maps the canonical specialization to a stable binding:
   `function:__apx_spec__Identity__int__<digest>` and the same unprefixed
   function name, where digest is the first ten SHA-256 hex characters of
   `Identity<int>`.
8. Original generic declarations remain in lowered AIR for traceability.
   Generated concrete functions have no type parameters; rewritten call sites
   dispatch to the generated unprefixed target name through ordinary runtime
   frames.
9. Ordinary `ProjectBuilder` validates generic calls but does not replace its
   program with lowered AIR. Artifact v1 therefore contains source-generic AIR
   and no specialization table/binding unless an external caller deliberately
   serializes a separate lowered program.

Generic declaration ID is a linked declaration identity. Specialization ID is
a compile-time key and display form. Lowered function ID is a synthetic runtime
target. These categories must remain separate. All are case-sensitive and
module-unaware. A module-aware design must derive specializations from the
resolved generic declaration identity; prepending module text to the current
`Target<Type>` string is insufficient.

Angle brackets are already generic syntax. A future qualification spelling
must not be confused with specializations. The frozen P9/P10 burden includes
short call targets, exact `Identity<int>` canonical IDs, deterministic closure,
SHA-based lowered names, original-generic traceability, host-generic leaves,
ordinary P7 call-frame execution, and artifact v1's current source-generic
AIR.

## Nesting inventory

| Relationship | Grammar/parser/project result | Scope, span, identity, and classification |
| --- | --- | --- |
| Directive inside directive | Rejected, parse `APX-PARSE-003` at nested keyword | No scope/identity; unsupported boundary |
| Function inside function | Rejected, parse `APX-PARSE-007` | No closure/nested identity; unsupported |
| Function inside directive | Rejected, `APX-PARSE-003` | Unsupported |
| Directive inside function | Rejected, `APX-PARSE-007` | Unsupported |
| Workflow inside workflow | Rejected, `APX-PARSE-001` expecting `invoke` | Unsupported; top-level workflow is parsed-only |
| Authority inside authority | Rejected, `APX-PARSE-001` expecting `capability` | Unsupported; `authority Name` in a directive is a reference, not nesting |
| Principal inside principal | Rejected, `APX-PARSE-003` | Unsupported |
| Role inside role | Rejected, `APX-PARSE-001` expecting `authority` | Unsupported |
| State inside directive | Accepted structural member; exact member span | Directive-local source lookup; `state:Name` globally linked; frozen feature |
| Event inside directive | Accepted structural member | Directive-local lookup; `event:Name` globally linked; frozen feature |
| Cause inside directive | Accepted structural member | `cause:Name` global link key; frozen feature |
| Path inside cause | Accepted structural member | `path:Name` cause-local validation/nested AIR; frozen feature |
| `when`/`otherwise` inside path | Accepted ordered actions | Lexical action tree, synthetic sidecar scopes, no declaration identity |
| Nested path `when`/`otherwise` | Accepted recursively; depth protected by validation/runtime | Structural control flow, not declaration nesting |
| Local bindings in functions/branches | Accepted | Ordered lexical scope; branch locals do not escape; sidecar positional IDs |
| Nested function `when`/`otherwise` | Accepted recursively; maximum depth 64 | Each branch receives the incoming visible-name set; sibling branches may reuse a new name |
| Generic declaration inside declaration | A generic function is top-level only; nested function form is rejected | Type parameters belong only to the containing top-level function |
| Module/import header inside declaration | Rejected in module pre-parser with `APX-MODULE-001` | Headers are physical-source metadata, not declarations or nested namespaces |
| Sequential top-level legacy directives | Accepted only through P11.2B headerless compatibility | Source sequence, not structural nesting; each directive keeps global ID and one owner/span |
| Multiple declarations in module source | Rejected after first declaration, normally `APX-PARSE-001` | One ordinary top-level declaration per module source remains frozen |

There is no general source-unit AST, declaration block, namespace declaration,
or nested declaration parent link.

## Scope and shadowing inventory

| Layer | Order/forward/shadow/case behavior | Identity and diagnostics |
| --- | --- | --- |
| Project | Source units sort by `(casefold, exact)`; linking sees complete programs, so cross-source calls/invocations can be forward or reverse in legacy mode | Global AIR ID tables; duplicate link diagnostics. Scope and identity are partly conflated here. |
| Module | Dependency-first compile/link order; known calls/invocations require same module or direct import | Temporary ID-to-owner gate, not a namespace/resolver. Exact module lookup after case-folded uniqueness. |
| Source | Physical provenance and ordinary one-root boundary; legacy-only directive sequence | Source name is ownership evidence, not a declaration namespace. |
| Directive | Compiler first builds complete state/event maps, so later member references work | Exact-case member lookup, but state/event/cause identities are globally flat. No local shadow rule across member kinds because prefixes differ. |
| Function | Parameters visible initially; local declarations become visible sequentially; linked function calls resolve after linking | Function ID is global; lexical namespace is a separate set. No local function declarations. |
| Parameter | Entire function body | Duplicate exact name is `APX-COMPILE-008`; case variants are distinct. |
| Local binding | Visible only after its declaration in its statement stream | Duplicate or parameter shadow is forbidden (`009`/`010`); forward use becomes `APX-VALIDATE-006` or an earlier type error. |
| Conditional branch | Inherits enclosing visible names; branch additions do not escape. Sibling branches can reuse one new name | Validator/runtime copy/extend immutable binding sets/frames. Branch scope is not encoded in a declaration identity. |
| Generic type parameter | Function signature/body type-annotation scope | `ApexTypeVariable.owner=function:Name`; duplicate and built-in shadow rejected in parse. Value and type namespaces are distinct mechanisms. |
| State/event member lookup | Containing directive's complete maps | Forward use works; imported/module lookup does not apply. IDs later collide globally. |
| Cause/path | Structural containment; no general source reference lookup | Cause global ID, path cause-local ID. This inconsistency is a P11.4 pressure point. |
| Linked program | Complete directive/function indexes accept short or current canonical references where the API supports them | Module ownership has already been erased from AIR. |
| Runtime call frame | Exact parameter/local names in immutable frame; frame stack uses function ID and rejects duplicate binding/recursion | Runtime scope consumes linked IDs but is not the same structure as declaration identity. |

Scope and identity are not represented by one consistent mechanism. Project
and linker tables conflate identity with global uniqueness; directive member
maps provide local resolution despite global IDs; function lexical scopes are
sets/frames; module visibility is a separate pre-link gate.

## Entry identity

| Input | Result |
| --- | --- |
| Short `Main` | Exact-case lookup of `directive:Main` |
| Canonical `directive:Main` | Accepted directly when defined |
| Manifest entry | Same string normalization and project resolver |
| CLI `--entry` | Overrides manifest and uses the same resolver |
| No entry, exactly one directive | Implicit canonical fallback |
| No entry, multiple directives | `resolve_entry`/run error; non-executing build may record null |
| No entry, zero directives | Entry error using current compatibility wording |
| Module-qualified/aliased entry | Unsupported/undefined |
| Function entry | Undefined because resolver always selects the directive family |
| Case mismatch | Undefined |
| Duplicate directive entry | Build fails at link before entry selection, usually on synthetic principal collision |

Entry strings are externally frozen in manifest schema 1, CLI behavior,
artifact project metadata, runtime authority grants, diagnostics, and user
scripts. A future qualified identity cannot silently reinterpret a dotted
short name, make an existing short entry ambiguous without a migration rule,
or require export status before export/qualification contracts exist.

## Diagnostics

`BuildDiagnostic` preserves severity, stage, code, primary span, related spans,
`air_id`, and a canonical sort key. P11.4A adds none.

`APX-LINK-001` remains the source-aware same-ID authority. The companion smoke
test verifies function/member collision identities and accepted P11.2/P11.3
span behavior. Generic/local/parser diagnostics remain at their current stages.

`APX-MODULE-001` through `APX-MODULE-009` remain exact:

- `001`: malformed/late header line;
- `002`: second module, with first module related;
- `003`: import before module;
- `004`: exact duplicate import;
- `005`: headerless source in mixed mode;
- `006`: missing exact-case module;
- `007`: deterministic cycle;
- `008`: known non-directly-visible directive/function reference;
- `009`: case-folded duplicate module.

The separate module-after-import `APX-MODULE-003` implementation branch
remains preempted by the earlier `APX-MODULE-002` second-module check. This
audit neither exposes nor repairs it.

## Manifest and CLI compatibility

Manifest schema 1 still accepts only `schema`, `name`, `sources`, and optional
`entry`. Sources are safe normalized relative paths sorted by
`(casefold, exact)`. Entry is a nonblank string with no semantic qualification
parsing at manifest load.

`check`, `run`, and `build` all call the canonical project pipeline. Success
output contains project/source count, resolved entry/runtime diagnostic count,
or artifact schema/fingerprint as established; it does not expose module,
ownership, identity-index, specialization, export, or namespace metadata.
Imports do not broaden runtime authority. P11.4A changes no command, flag,
exit code, output, or error rendering.

## Artifact v1 compatibility

Artifact v1 top-level fields remain exactly `schema`, `project`, `air`, and
`fingerprint`. `project` contains name, canonical source list and exact-byte
SHA-256 hashes, source count, and resolved canonical directive entry or null.
`air` is recursive dataclass serialization of the linked `AIRProgram`.

The fingerprint is SHA-256 over canonical UTF-8 JSON containing `schema`,
`project`, and `air`; the fingerprint record is added afterward. Ownership,
module/document graphs, source map, aliases, exports, qualified identities,
specialization tables, and identity metadata are omitted. Querying P11.3D
metadata does not change bytes or fingerprint.

Externally frozen identity forms in v1 are current serialized AIR IDs,
short-name fields/references, generic type-variable owner strings, and the
resolved `directive:` entry. Source-map positional IDs, declaration ownership,
module identity, closure keys, and lowering bindings remain internal to the
current build flow. Replacing serialized AIR IDs requires a versioned artifact
decision; metadata-only in-memory work does not.

## Runtime identity and trace behavior

Runtime lookup indexes linked AIR by existing IDs. Directive entry/invocation
accepts short or `directive:` references. Function lookup similarly recognizes
short/current function references. Call frames store `function_id`,
`function_name`, exact parameter/local bindings, and stack depth.

Trace facts and runtime diagnostics expose current IDs: directive start/finish,
authority checks, invocation caller/target, state/path/event facts, function
call/local/return frames, and standard-library canonical IDs. `Diagnostic.node_id`
uses current runtime node identities. Runtime event IDs are composite strings
built from directive, decision, path, event index, and event ID. None is
module-aware. A migration that rewrites AIR IDs would therefore affect runtime
traces and diagnostics even if execution semantics stayed constant.

## Language-server behavior

The language server parses one open document through `parse_module_source` and
the ordinary one-node parser. It does not use `ProjectBuilder`, manifest,
module/document graphs, declaration ownership, linker, validator, generic
closure, or runtime.

| Feature | Current semantic boundary |
| --- | --- |
| Syntax diagnostics | Module-header + lexer + parser only; no missing import, collision, visibility, or project diagnostics. P11.2B second directive remains an LSP parse error. |
| Document symbols | Hierarchical syntax tree: optional module root, imports and one top-level declaration, plus nested members/parameters/locals. Parsed-only families are displayed. |
| Workspace symbols | Deterministic recursive `.apex` scan with open-document overlays; flattens selected syntax symbols. No manifest membership, linking, or semantic identity. |
| Hover | Syntax descriptions in one document, including module/import text. |
| Completion | Context-aware syntax/lexical suggestions; no module-name/project index or inferred semantic candidates. |
| Definition | Same-document syntax/lexical occurrence graph; module self-definition only; imports/cross-file declarations unresolved. |
| References | Same-document occurrences sharing the definition graph's lexical identity. |
| Rename | Only lexically complete local/member namespaces. Modules, imports, callables, directives, workflows, authorities, capabilities, roles, and principals are protected. |
| Formatting | One valid ordinary parsed declaration plus module/import headers; invalid syntax gets no edits. |
| Qualified names/aliases/nested declarations | No behavior beyond existing lexical/parser rejection. |

Workspace symbols index multiple files but do not resolve relationships.
Definition, references, rename, hover, completion, formatting, diagnostics, and
document symbols operate on one document. Open overlays affect document state
and workspace symbol scanning, not semantic project resolution.

## Visual Studio behavior

Visual Studio hosts the same frozen T4.11 Python language server. Its T5.5
intelligence contract exposes document symbols, hover, completion, definition,
references, prepare/rename, workspace symbols, and formatting without modifying
server semantics. Diagnostics and full-document synchronization pass through
the same LSP. Native classification recognizes the existing keyword/module
surface only.

The audit verifies the frozen T4.11 integration fingerprint
`c2fff74134a40bd335e1c04123127d4cc87df7aa2ed3accc5133d93da9066897`
and Visual Studio T5.5 fingerprint
`65f6ab0565276a59b1a71814acb0023da161a38661605b788e5f8b1e2753f82a`.
Visual Studio does not consume declaration ownership and gains no identity,
alias, qualification, export, or nesting behavior in this slice.

## Candidate identity models

### Comparison matrix

| Candidate | Frozen compatibility; AIR/linker/validator | Generics and entry | Diagnostics/source maps; artifact/runtime/CLI | Tooling, determinism, case/collision | Migration, aliases/nesting, display risk |
| --- | --- | --- | --- | --- | --- |
| 1. Preserve flat AIR IDs; external qualification index | High for P10/P11.1-P11.3. AIR/linker unchanged, so same-kind declarations still cannot coexist. | Can map declarations but cannot safely derive two equal-short generic specializations or qualified entries while link collisions remain. | Metadata can be in-memory and byte-neutral. Existing diagnostics stay, but ambiguity cannot be represented in executable AIR. | Deterministic exact-case index is feasible; LSP could later consume it. Case split remains. | Easy first step and alias lookup scaffold, weak final nesting/collision model. High risk that display qualification is mistaken for canonical identity. |
| 2. Replace AIR IDs with fully module-qualified strings | Low immediate compatibility. Touches AIR dataclasses, linker, validator, references, runtime, serialization, entries, tests. | Requires module-aware generic keys/lowering and entry migration. Legacy synthetic module decision required. | Changes artifact v1 bytes/fingerprint and runtime traces; broad diagnostic `air_id` churn and CLI entry effects. | Enables coexistence/ambiguity after resolver work; requires delimiter/escaping/case contract and project-aware tooling. | Hard migration; helps modules but not lexical parents by itself. Strong risk of conflating storage, lookup, and display strings. |
| 3. Structured identity object separating declared/qualified/canonical/display | Strong long-term separation; immediate use inside AIR would be breaking, metadata-only use can be compatible. | Can derive specializations/entries from resolved declaration identity without using display text. | Can retain current AIR ID as compatibility field; source maps can carry structure later. Artifact/runtime unchanged only if object remains sidecar. | Best explicit case/ordering/ambiguity model and tooling API. | Moderate staged migration; supports aliases/parents cleanly. Lowest display/canonical conflation, but premature fields can canonize unsupported nesting. |
| 4. Composite strings with escaping/normalization | Medium/low. Strings fit current APIs but demand global delimiter and rewrite rules. | Collides conceptually with `:`, `::`, `<...>`, and generated IDs; entries require parsing. | Likely changes serialized IDs/traces; diagnostics need reversible decoding. | Determinism possible only with explicit escaping, Unicode/case rules, and kind tags. | Superficially easy, actually high migration and ambiguity risk. Aliases should not rewrite identities. Highest display/canonical conflation risk. |
| 5. Source/module ownership plus resolver-generated canonical identity | High if resolver output begins as metadata and current AIR IDs remain. Linker can migrate later. | Resolver can bind generic declaration first, then derive specialization; entry can remain unaffected initially. | Source spans/owners are already available. Artifact/runtime/CLI remain stable while generated IDs are sidecar-only. | Deterministic candidates/order/case can be explicit; enables future ambiguity without overwriting owners. | Moderate and well staged; aliases can be bindings, parents later. Some risk if generated canonical strings are exposed before grammar decisions. |
| 6. Namespace scopes with local short names and global qualified names | Low now: requires grammar/scope/resolver and likely AIR/link changes. | Clean generic and entry model after qualification rules exist. | New diagnostics and tooling mandatory; artifact/runtime migration likely if qualified names serialize. | Strong coexistence and ambiguity semantics; namespace/module case policy must be unified. | Powerful for future nesting/aliases, but far broader than P11.4B. Display/canonical distinction still necessary. |
| 7. Aliases as reference-only bindings, never declaration identity | High as a rule, but unusable alone because alias syntax/resolver is absent. AIR declaration IDs need not change. | Correctly preserves generic owner/specialization and entry declaration identity; aliased entry policy can be separately chosen. | Can keep artifacts/traces stable if aliases disappear after resolution; diagnostics need alias and target spans. | Deterministic alias scope/collision rules needed; tooling must rename binding separately from declaration. | Essential future invariant and compatible with models 3/5/8. Does not solve canonical identity or nesting alone. Low conflation risk. |
| 8. Hybrid immutable structured metadata while preserving current AIR IDs | Highest near-term compatibility. Add sidecar identity records/index; AIR/linker/validator untouched. | Record only generic declaration now; specializations/lowering remain existing systems; entries unchanged. | No diagnostic, source-map, artifact v1, runtime, trace, or CLI change. | Deterministic exact-case queries and duplicate retention; tooling unchanged until authorized. Does not yet relax collisions. | Smallest migration and foundation for resolver/aliases/parents later. Low risk if fields clearly call AIR IDs `current_air_id` and display names non-resolving. |

### Findings by candidate

1. An external qualification index is viable only as a factual index. It
   cannot claim to solve same-name coexistence while the linker still rejects
   equal AIR IDs.
2. Immediate fully qualified AIR IDs solve the visible collision symptom but
   cross every frozen serialization/runtime/tooling boundary. They also leave
   local lexical ownership and display separation underspecified.
3. Structured identities are the sound destination because case, kind,
   declared spelling, canonical storage, display, ownership, alias binding,
   and parent relationships are different facts. P11.4B should not inject the
   object into AIR yet.
4. Composite strings are inappropriate as the first foundation. Current
   syntax/IDs already occupy common delimiters, and escaping would become an
   externally frozen language contract prematurely.
5. Resolver-generated canonical identity is a strong second-stage direction
   after immutable declared-identity facts exist. A resolver should consume,
   not overwrite, ownership/document/module data.
6. Namespace scopes can support the roadmap but require grammar and tooling,
   so they are not the smallest coherent next stage.
7. Aliases should always be reference-scope bindings. They must never rename a
   declaration, generic owner, runtime ID, or artifact identity.
8. The hybrid metadata model best fits the frozen baseline and creates the
   minimum trustworthy input for model 5. It is recommended below with no AIR
   or resolver behavior.

## Candidate nesting models

| Candidate | Parser/AIR/source-map/diagnostic cost | Runtime/generics/tooling/ambiguity | Compatibility and conclusion |
| --- | --- | --- | --- |
| 1. Keep top-level declarations; nested members only | None. Preserves current AST/AIR/source maps and diagnostics. | Current inconsistent member IDs remain; tooling already displays hierarchy. | Highest compatibility; baseline to preserve during metadata work. |
| 2. Nested functions in functions | New grammar, closure capture and lexical parent semantics, AIR/runtime call-frame changes, source-map parent identity, recursion/shadow diagnostics. | Generic owner identity, captures, definition/reference/rename, overload/ambiguity rules all change. | Too broad; not supported by evidence for P11.4B. |
| 3. Functions inside directives | Grammar and AST ownership plus decision whether functions are lexical, directive members, or runtime-owned; AIR/linker changes likely. | Generic specialization must include resolved parent; calls and module visibility/tooling change. | Broad and semantically ambiguous; defer. |
| 4. Directives inside modules as structural namespace members while one physical top-level declaration remains | Modules are already headers/metadata, not AST containers. Could be modeled as ownership qualification without grammar change. | No runtime parent needed, but same-name coexistence still needs resolver/link migration; tooling needs project awareness. | Useful conceptual model for qualified ownership, but do not call it syntax nesting. |
| 5. Explicit namespace declarations | New keyword/grammar, multiple/nested declarations, resolver, source maps, diagnostics, formatting/symbol navigation. | Enables qualification/aliases; raises namespace/module interaction and runtime non-ownership questions. | Later-stage design, not P11.4B. |
| 6. Declaration blocks with multiple named declarations | General source-unit AST/parser/compiler ordering and module-source cardinality change. | Link/source maps/tooling must preserve mixed order; ambiguity grows. | Conflicts with frozen one-declaration module boundary; defer. |
| 7. Nesting as identity qualification only, not runtime ownership | Can represent module/parent path metadata without changing execution if no syntax is added. | Generics can derive from resolved parent identity later; tools can display hierarchy. Risk of pretending current members are project declarations. | Promising principle, but parent links should wait until an authorized declaration relation exists. |
| 8. Structured lexical scopes with explicit parent identity links | Best long-term representation for real nested declarations; requires scope tree, parent lifetime, shadow/forward rules, source-map links, diagnostics. | Supports captures, generics, tooling, and deterministic ambiguity when specified. | Correct destination for nesting, but premature now. Metadata record should omit parent until syntax/model exists. |

The smallest current nesting decision is preservation: module ownership may be
recorded as declaration metadata, but no source or runtime nesting is added.
`parent_identity` should remain absent in P11.4B. Adding it now would either be
always `None` or tempt callers to promote states/events/causes/paths into the
successful project declaration set despite their inconsistent AIR scopes.

## Compatibility comparison

| Model | P10/P11 frozen safety | Same-name future | Generic correctness | Entry/artifact/runtime safety now | Tooling foundation | Recommended now |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Flat AIR + external index | High | Low | Medium-low | High | Medium | No, incomplete alone |
| Fully qualified AIR strings | Low | High | Medium after migration | Low | Medium | No |
| Structured identity everywhere | Low immediately / high staged | High | High | Low immediately | High | No immediate AIR adoption |
| Escaped composite strings | Low-medium | High | Medium | Low | Medium | No |
| Ownership + resolver canonicalization | High staged | High | High | High if sidecar first | High | Later resolver stage |
| Namespace scopes | Low | High | High | Low | High | No |
| Reference-only aliases | High as invariant | Neutral | High | High | High | Adopt as future invariant, not a slice |
| Hybrid immutable metadata/current AIR IDs | Highest | Foundation only | High preservation | Highest | High future value | Yes |

## Recommended P11.4B boundary

### Exact stage name

**P11.4B Declared Identity Metadata Index**.

This name is deliberately narrower than "canonical qualified identity". The
slice records declared identity facts and one non-resolving display projection;
it does not decide the final canonical resolver key.

### Exact public model

Add `language.identities` with two frozen dataclasses, exported from that
module only:

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

Field order above is exact. Both records and tuple storage must be immutable.
Kinds remain exactly `directive` and `function`. `declared_name` is the exact
source spelling recovered from the matching declaration source-map reference.
`current_air_id` is exactly the current `directive:<name>` or
`function:<name>` value and is explicitly not renamed `canonical_id`.

`qualified_display_name` is metadata only:

- legacy: `<declared_name>`;
- module mode: `<exact-module-name>.<declared_name>`.

The field is not a source spelling, lookup key, alias, namespace, AIR ID,
entry, or visibility result. Dotted module names are already validated
identifier segments, so this presentation is deterministic without inventing
escaping. Kind remains separate, allowing a directive and function to share a
display string.

No `parent_identity` field is included. Current successful project
declarations have no legal declaration parent. Parent identity belongs in the
later slice that authorizes a specific nesting relation and tests its grammar,
scope, diagnostics, AIR, and tooling consequences.

### Ordering and query behavior

Canonical index order must extend the accepted P11.3D order without changing
it:

1. `current_air_id`;
2. `source_name.casefold()`;
3. exact `source_name`;
4. span start offset;
5. span end offset;
6. kind;
7. whether module is non-`None`, legacy first;
8. exact module name or empty sort proxy;
9. exact `declared_name`; and
10. exact `qualified_display_name`.

Expose read-only exact-case queries returning tuples in index order:

```text
for_source(source_name)
for_module(module_name)
find_all(kind, declared_name)
find_current_air_id(current_air_id)
find_qualified_display_name(qualified_display_name)
```

Unknown valid queries return `()`. Non-string inputs raise `TypeError`; blank
strings raise `ValueError`. `kind` must be exactly `directive` or `function`.
Queries do not trim nonblank values, resolve references, choose winners, grant
visibility, select entries, compile, execute, or serialize.

### Integration and duplicate representation

Append `identity_index` to `ProjectBuild` after `declaration_ownership`, with
`default_factory=ProjectIdentityIndex` and `compare=False`. This preserves all
existing positional fields/equality and gives manual builds an empty default.

`ProjectBuilder` constructs the index beside ownership while per-source
`CompiledSource`, source-map references, and exact module mapping are still
available. It must not reparse text or derive source ownership from flattened
linked AIR. Every successful ownership record has exactly one corresponding
identity record.

Equal current AIR IDs and equal display names remain multiple records. The
index never overwrites, rejects, resolves, or selects one. Existing duplicates
still reach the linker and retain `APX-LINK-001`; a failed build returns no
partial `ProjectBuild`.

Legacy records have `module_name=None` and short display name. Module records
retain exact validated spelling. Generic source functions contribute one
`function` identity. Specializations, closure nodes, host generics, and
lowered targets do not enter the index.

### Non-effects

P11.4B must have no effect on entry selection, diagnostics, source-map shape,
module/document graph shape, visibility, linker/validator behavior, AIR IDs,
generic keys/lowering, runtime identity/traces, authority, manifest schema 1,
CLI output, artifact v1 bytes/fingerprint, language-server behavior, VS Code,
or Visual Studio.

### Proposed file boundary

Authorized production files for the proposed future slice:

- add `apexforge/language/identities.py`;
- modify `apexforge/language/project.py` only.

Authorized future test/document files:

- add `apexforge/p11_4b_declared_identity_metadata_smoke_test.py`;
- add `docs/p11/P11_4B_DECLARED_IDENTITY_METADATA_INDEX.md`.

No other production, test, governance, or accepted P11.3 file should change in
that slice without separate owner authorization.

### Explicit P11.4B non-goals

No grammar/lexer/parser change; parent identity; nested declaration; multiple
module declarations; qualified source reference or entry; alias syntax or
binding; namespace; export/re-export/visibility; resolver; ambiguity
diagnostic; collision relaxation; AIR field/ID rewrite; linker/validator
change; generic specialization/lowering identity change; artifact/manifest
field; CLI behavior; runtime/trace behavior; language-server/VS Code/Visual
Studio behavior; workflow/authority/principal/role promotion; member promotion;
P11.4C implementation; P11.5 or later work.

### P11.4B acceptance checklist

- [ ] Exact two frozen public dataclasses and field order are implemented.
- [ ] Exact constructor validation rejects invalid kind/name/current AIR ID,
      source/module/display shape, span type, and source mismatch.
- [ ] Every successful directive/function owner maps one-to-one to a declared
      identity record with exact source spelling.
- [ ] Legacy and exact module display projections are deterministic and
      explicitly non-resolving.
- [ ] Canonical ordering is stable under reversed mapping/dependency order.
- [ ] Exact-case queries return tuples; duplicates/display collisions are
      retained without overwrite.
- [ ] Generic declarations have one record; specializations/lowered targets
      have none.
- [ ] No parent field or nested member promotion exists.
- [ ] Manual `ProjectBuild` positional/equality compatibility is preserved.
- [ ] Existing ownership, module, and document graph shapes remain unchanged.
- [ ] `APX-LINK-001`, `APX-MODULE-001` through `009`, and the preempted branch
      remain exact.
- [ ] Direct/transitive/legacy visibility and short/canonical entries remain
      exact.
- [ ] Manifest, CLI, artifact v1 bytes/fingerprint, runtime, LSP, VS Code, and
      Visual Studio remain exact.
- [ ] Focused tests precede the complete harness; actual discovery/pass count
      and repository status are reported.

## Explicit P11.4A non-goals

P11.4A makes no production change and does not implement the recommendation.
It adds no qualified identity, aliases, namespaces, nesting, declaration
blocks, exports, visibility, ambiguity resolution, diagnostic, AIR schema,
artifact schema, entry syntax, manifest field, CLI feature, runtime behavior,
tooling behavior, or later roadmap work. It does not declare any milestone
complete, frozen, canonized, or released.

## Known limitations

1. Same-kind declaration IDs remain globally flat even with distinct modules.
2. State/event/cause source lookup is directive-local while linked IDs are
   global; path identity follows a different cause-local rule.
3. Ownership and the proposed identity metadata cover only successful
   directives/functions, not every parsed declaration or nested member.
4. Failed builds expose no partial ownership/identity index.
5. The module visibility owner dictionary overwrites duplicate keys before the
   linker reports them and cannot represent ambiguity.
6. Case-folded module uniqueness and exact-case import lookup remain split.
7. Source-map IDs mix real AIR IDs and positional sidecar IDs.
8. Artifact serialization is one-way for parts of the current AIR model;
   artifact execution/full AIR round-trip is not supported.
9. Ordinary project builds do not store generic closure/lowering output.
10. LSP diagnostics and most intelligence are one-document syntax/lexical
    views; workspace symbols are multi-file but nonsemantic.
11. P11.2B build acceptance and ordinary LSP one-node parsing remain
    intentionally asymmetric.
12. Duplicate paths and directive authorities still use weak `999` diagnostic
    mappings without full source attribution.

## P11.4A acceptance checklist

- [x] Repository branch, HEAD, clean areas, freeze tag, ancestry, stage markers,
      and local-origin equality were verified before editing.
- [x] Governance and accepted P11.2/P11.3 architecture were read first.
- [x] Exact parser and successful-project declaration inventories are recorded.
- [x] Identity layers and exact current IDs are classified without promoting
      parsed-only or nested forms.
- [x] Ownership, module, visibility, collision, ambiguity, generic, nesting,
      scope, entry, diagnostic, CLI, artifact, runtime, LSP, and Visual Studio
      boundaries are recorded and executable.
- [x] Eight identity candidates and eight nesting candidates are compared.
- [x] One metadata-first P11.4B boundary is recommended with exact model,
      ordering, queries, files, non-effects, non-goals, and checklist.
- [x] Only the two authorized P11.4A files are added; no existing file changes.
- [x] Focused validation and complete regression result are recorded below.

## Test record

The executable record is
`apexforge/p11_4a_identity_nesting_architecture_audit_smoke_test.py`. It covers
the 33 required audit areas by direct assertions and reuse of accepted
P11.2/P11.3 helpers. It makes no network call, uses only context-managed
external temporary fixtures, restores/preserves the working directory, checks
repository status before/after, and rejects tracked/staged changes.

Validation uses `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, and `py -3 -B`.

- P11.4A focused smoke: PASS.
- Required focused compatibility matrix: 57/57 scripts passed.
- Complete regression harness: discovered 89 smoke tests; 89/89 passed.
- Final repository shape after validation: exactly the two authorized P11.4A
  files are untracked; no existing, tracked, or staged file is changed.
