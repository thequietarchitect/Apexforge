# P11.4C Resolver and Qualification Architecture Audit

## Scope and controlling architecture

P11.4C is an audit-only substage over the published P11.4A identity and
nesting architecture and the published P11.4B declared-identity metadata
index. It adds only this document and
`apexforge/p11_4c_resolver_qualification_architecture_audit_smoke_test.py`.
It does not implement a resolver or change any production behavior.

P11.4A and P11.4B control this audit. In particular:

- current AIR IDs remain flat, kind-prefixed compatibility identities;
- `ProjectDeclaredIdentity` is immutable factual metadata;
- `qualified_display_name` is a non-resolving presentation projection;
- module ownership, document reachability, direct-import visibility, AIR
  identity, entry selection, and runtime lookup are separate mechanisms;
- aliases, exports, qualified source syntax, general declaration nesting, and
  ambiguity sets do not exist; and
- generic declarations, specialization keys, and lowered targets are three
  different identity strata.

This document uses four evidence labels throughout:

- **Observed current behavior**: directly implemented and covered by current
  production code or tests.
- **Architectural inference**: a consequence of the observed implementation,
  but not a published language rule.
- **Recommended future contract**: a staged design recommendation; it is not
  active behavior.
- **Unresolved policy decision**: repository evidence does not support one
  safe choice yet.

“Resolver” below means a project-semantic process that accepts a use-site and
a requested name/kind, collects all eligible candidates, applies visibility
and qualification rules, and returns a resolved binding, ambiguity, or
deterministic failure. A kind-specific dictionary probe, display filter,
linker duplicate check, or syntax occurrence scan is not that resolver.

## Repository checkpoint

**Observed current behavior.** Before either authorized file was added:

- branch: `p11.4-identity-nesting`;
- HEAD: `4e8eb49bc639980880df1297586b1549a0c57717`;
- local remote-tracking ref `refs/remotes/origin/p11.4-identity-nesting`:
  `4e8eb49bc639980880df1297586b1549a0c57717`;
- local and remote-tracking tips matched;
- working tree and index were clean; and
- no network operation was used to verify the checkpoint.

P11.4A and P11.4B are treated as controlling published architecture. P11.3 is
the frozen module, document-graph, and declaration-ownership foundation. This
audit neither declares nor changes any milestone, freeze, tag, release, or
canonical language policy.

## Method and inspected surfaces

**Observed current behavior.** The audit read the complete P11.4A and P11.4B
documents, their executable smoke tests, `language.identities`, and
`language.project` first. It then traced:

- declaration ownership in `language.declarations` and metadata construction
  in `ProjectBuilder`;
- module header parsing, module graph construction, import edges, document
  graphs, canonical/dependency order, and visibility in `language.modules`;
- AST-to-AIR lowering and `SourceMapEntry` creation in `language.compiler`;
- global collision checks in `air.linker`;
- linked reference validation and diagnostic projection in
  `language.validation.runtime_validator` and `language.project`;
- directive and function lookup, authority resources, call frames, trace IDs,
  and event-record IDs in the runtime;
- generic declaration ownership, signature aliases, specialization keys,
  closure expansion, lowering bindings, and generated targets in
  `type_system`;
- manifest entry storage, project loading, CLI override/selection, artifact v1
  construction, and AIR serialization;
- LSP diagnostics, document/workspace symbols, hover, completion, definition,
  references, rename, formatting, server dispatch, and frozen integration
  fingerprints; and
- the Visual Studio language client and its T5.5 intelligence parity audit.

The companion smoke test uses current public behavior rather than proposed
types. It blocks sockets, creates fixtures outside the repository, compares
complete repository status and repository bytecode state before and after,
and statically verifies that no production resolver abstraction or new
identity-index consumer exists.

## Existing identity strata

### Declaration and project metadata

All identifiers in source, AIR, references, and runtime lookup are currently
case-sensitive. Module declarations alone add a case-folded uniqueness check;
module/import lookup remains exact-case. Trimming at selected API boundaries
is not case normalization.

| Representation | Creator and storage | Consumer | Case and uniqueness domain | Authority, lookup, display, serialization |
| --- | --- | --- | --- | --- |
| Source spelling | Lexer/parser AST `.name`, `.target`, and reference fields; module pre-parser header records | Compiler, syntax tooling, module graph, source maps | Exact-case; uniqueness depends on the local declaration family | Authoritative source text at its syntax boundary; participates in current short-name lookup after lowering; not a standalone serialized identity object |
| `declared_name` | `ProjectBuilder._build_declaration_metadata` copies the matching declaration `SourceMapEntry.reference` into `ProjectDeclaredIdentity` | P11.4B inspection queries only | Exact-case; not globally unique; kind and module are separate facts | Authoritative declaration spelling metadata; factual filtering only; survives only in memory, not artifact v1 |
| `current_air_id` | Compiler constructs `directive:<name>` or `function:<name>`; builder copies it into P11.4B metadata | Linker, validator, runtime, entry resolver, artifact serializer; metadata queries | Exact-case; globally unique per AIR collection under the current linker | Authoritative compatibility identity for current AIR; participates directly in lookup; serialized in artifact v1; not a final qualified declaration identity |
| `qualified_display_name` | P11.4B builder projects `<declared_name>` for legacy or `<module_name>.<declared_name>` for module mode | Exact metadata filter and human inspection only | Exact-case; duplicates across kind are retained; same-kind cross-module duplicates cannot survive linking today | Display-only and explicitly non-resolving; not source syntax, not a canonical key, not serialized |
| `module_name` | Line-oriented module pre-parser; stored in `ModuleSource`, `ModuleRecord`, `ProjectDocument`, ownership, and identity metadata | Module graph/import lookup, visibility gate, graph queries, display projection | Dotted ASCII identifier segments; declaration uniqueness uses `casefold()`, lookup uses exact text | Authoritative module ownership metadata in module mode; participates in import lookup/visibility, not declaration AIR lookup; omitted from artifact v1 |
| `source_name` | Project source normalization and `SourceText`; stored in source units, spans, module/document records, ownership, identity metadata, artifact source list | Ordering, provenance, diagnostic attribution, project loader, tools | Source-unit uniqueness is case-folded; most later queries are exact-case | Authoritative physical provenance, not a declaration namespace; artifact v1 persists canonical source paths and hashes, not declaration ownership |
| Ownership `air_id` | Builder pairs a declaration source-map entry with its per-source AIR declaration in `ProjectDeclarationOwner` | P11.3D inspection and P11.4B one-to-one construction | Exact current AIR ID; duplicate facts retained by the model | Authoritative physical/module ownership fact; no winner selection or lookup binding; in-memory only |
| Ownership record | `ProjectDeclarationOwner(kind, air_id, source_name, module_name, span)` | Ownership queries and metadata construction | Canonically ordered; exact queries; directive/function only | Factual metadata, not visibility, export, resolution, or serialization |

### Compiler, AIR, generic, entry, and runtime identities

| Representation | Creator and storage | Consumer | Case and uniqueness domain | Authority, lookup, display, serialization |
| --- | --- | --- | --- | --- |
| Source-map declaration reference | Compiler stores exact short name in `SourceMapEntry.reference` with declaration AIR ID and span | Ownership/identity collection and diagnostic attribution | Exact-case; ordered by physical source/span | Authoritative bridge to source spelling; participates in diagnostic/source filtering, not semantic winner selection; omitted from artifact v1 |
| Source-map use reference | Compiler stores directive/function call target spelling in `SourceMapEntry.reference`; sidecar ID is `invoke:...` or `function_call:...` | Module visibility and project validation diagnostic mapping | Exact-case; occurrence identity is positional | Evidence for a use site; does not store a resolved declaration; omitted from artifact v1 |
| Source-map sidecar ID | Compiler creates positional IDs for calls, locals, parameters, returns, conditionals, requirements, assignments, and emissions | Diagnostics and traceability helpers | Deterministic only within the current compilation layout | Not necessarily an AIR object ID and never a general lookup identity; omitted from artifact v1 |
| Directive declaration ID/name | Compiler creates `AIRDirective(id="directive:Name", name="Name")` | Linker, validator, entry selection, runtime, CLI authority construction, serialization | Exact-case; directive IDs globally unique | ID is current authoritative directive lookup key; name is short display/reference spelling; both serialize |
| Directive invocation target | Parser/AST and compiler preserve `DirectiveInvocation.target` as the source short string | Module visibility, validator, runtime | Exact-case; no candidate set | Lookup input. Validator/runtime accept either an existing ID or prepend `directive:`; serialized in AIR |
| Function declaration ID/name | Compiler creates `AIRFunction(id="function:Name", name="Name")` | Linker, validator, signature tables, generic closure/lowering, runtime, serialization | Exact-case; IDs and names globally unique under current validation | ID is current authoritative function key; name is the principal source/display alias; both serialize |
| Function call target | Compiler preserves `AIRCallExpression.target` as source spelling | Type checking, module visibility sidecar, validator, generic closure/lowering, runtime | Exact-case; standard library uses the same target surface with its registry | Lookup input, not a bound declaration field; serialized in AIR |
| Generic type-variable owner | Compiler creates `ApexTypeVariable.owner="function:Name"` | Type substitution, validation, encoding of open type identities, serialization | Exact-case; owner is current flat function AIR ID | Authoritative within the current generic declaration model; participates in generic identity; serialized with function metadata |
| Generic canonical specialization key | Type inference creates `GenericSpecializationKey(target, type_arguments)` and `canonical_id` such as `Identity<int>` | Instantiation table, closure dependencies, lowering, diagnostics | Exact-case target plus ordered encoded type identities; unique within one instantiation table | Authoritative only for the P9 specialization subsystem; participates in lookup/deduplication; not part of an ordinary project artifact |
| Lowered specialization name/ID | Lowerer derives `__apx_spec__Target__Types__<digest>` and `function:<generated-name>` from the specialization canonical ID | Lowered call rewriting, lowered function table, optional runtime execution of explicitly lowered AIR | Deterministic SHA-derived exact strings; collision-checked against linked function names/IDs | Authoritative only in explicit lowering output; not indexed by P11.4B; absent from ordinary `ProjectBuild` artifacts |
| Entry input name | Manifest schema 1 or CLI `--entry`; project API also accepts an argument | `_resolve_entry_directive`, CLI run/build | Trimmed, then exact-case; directive-only and project-global | Lookup input; short `Name` or current `directive:Name`; manifest persists input, artifact persists resolved ID |
| Resolved entry ID | `_resolve_entry_directive` returns `directive:Name`; stored on `ProjectBuild.entry_directive` and artifact project metadata | Runtime root selection, CLI output, authority context | Exact-case; one linked directive | Current authoritative entry binding; serialized in artifact v1 |
| Runtime directive/function index | `index_by_id` over linked AIR collections | Runtime entry, invocation, and call execution | Exact-case dictionary key; duplicate keys would overwrite, but verified linked AIR rejects them earlier | Direct flat-map lookup, not a project resolver; consumes current AIR IDs; not a separate serialized structure |
| Runtime authority resource | Compiler authority check and CLI grant use `directive:Name` | Authority engine and runtime directive execution | Exact-case current directive ID | Runtime authorization identity; serialized in AIR checks and observable in traces/diagnostics |
| Runtime event record ID | `event_record_id(directive, decision, path, index, event)` | Runtime results and traces | Exact composite runtime string | Runtime-only event identity; not a declaration lookup key or build-artifact declaration field |
| State/event/cause/path IDs | Compiler creates `state:`, `event:`, `cause:`, and `path:` IDs | Linker, validator, directive-local compiler maps, runtime | State/event/cause are globally flat after linking; paths are cause-local in nested AIR | Current member/runtime identities; serialize in artifact v1; excluded from P11.4B project declaration metadata |

### Artifact and tooling names

| Representation | Creator and storage | Consumer | Case and uniqueness domain | Authority, lookup, display, serialization |
| --- | --- | --- | --- | --- |
| Artifact v1 identity fields | Recursive AIR dataclass serialization plus resolved project entry | Build consumers and fingerprinting | Preserves exact strings already in AIR | Serialized compatibility contract: flat IDs, names, references, type owners, and entry; no module, owner, source map, candidate, or resolver metadata |
| Document symbol name | LSP syntax tree projection | Editors, workspace-symbol flattener | Exact spelling; no semantic uniqueness | Display/navigation presentation; not compiler lookup; returned over LSP only |
| Workspace symbol name/container | Recursive `.apex` scan flattens document symbols | Workspace symbol search | Query matching is case-insensitive; ordering is deterministic; duplicates are permitted | Search presentation, not project membership or binding; not serialized into build artifacts |
| LSP occurrence identity | `_Definition`/`_Occurrence` source offsets, name, and lexical namespace | Same-document definition, references, and protected rename | Exact same-document syntax identity | Authoritative only for the frozen lexical tooling feature; no cross-file/module binding and no persistence |
| Visual Studio symbol intelligence | Native client exposes the frozen T4.11 LSP methods | Visual Studio users | Same behavior as the Python language server | Presentation/client transport only; it owns no independent resolver or identity store |

**Architectural inference.** No single existing value can safely be renamed
“canonical qualified identity.” `current_air_id`, generic `canonical_id`,
`qualified_display_name`, module ownership, and LSP occurrence identity each
have different authority and compatibility boundaries.

## Current lookup-path inventory

| Surface | Current path | Classification |
| --- | --- | --- |
| Directive invocation | Parser records short `target`; compiler copies it into AIR and a source-map occurrence; module visibility prepends `directive:` and looks up one overwritten owner; validator checks ID-or-prefixed membership; runtime repeats ID-or-prefixed dictionary lookup | Compiler preservation plus direct flat-map lookup; not candidate resolution |
| Function call | Parser/compiler preserve `AIRCallExpression.target`; source type checking consults optional signature maps; source map records the use; module visibility prepends `function:`; linked validator probes ID/prefixed ID/name; generic subsystems register name/ID aliases; runtime probes ID/prefixed ID | Several kind-specific bindings and maps; no shared resolver or ambiguity set |
| Generic function call | Linked signatures are keyed by function name and ID; inference creates a key using `signature.name`; closure finds the target by short name; lowerer maps canonical specialization key to generated target | Compiler binding and specialization-table lookup after globally unique linking; not module-qualified resolution |
| Import | Header parser validates syntax/order; module graph exact-matches import module names, detects missing/cycles, and builds direct edges | A true resolver for module records only, not declarations inside modules |
| Export | No syntax, model, lookup path, or visibility set | Absent |
| Entry selection | `_resolve_entry_directive` trims input, accepts exact linked ID, otherwise prepends `directive:`; implicit entry is allowed only for exactly one directive | Small directive-only flat resolver, with no module/use-site context |
| Runtime directive execution | Linked directives are indexed by ID; root and nested invocation references accept exact ID or `directive:` prefixing | Direct runtime lookup over already-verified AIR |
| Runtime function execution | Standard library registry is checked first; linked functions then accept exact ID or `function:` prefixing | Registry dispatch plus direct linked-function lookup |
| LSP definition | Parses one document, creates syntax/lexical definitions and occurrences, resolves prior locals, member state/event uses, type parameters, and self-recursive calls | Same-document lexical resolver only; imports, directive invocations, and cross-file calls are unresolved |
| LSP references | Reuses exact T4.7 occurrence target offsets/name/namespace | Same-document occurrence projection |
| Rename | Reuses the occurrence target; permits only lexically complete local/member namespaces and rejects collisions in the same syntax index | Same-document protected edit, not project-semantic rename |
| Workspace symbols | Recursively scans `.apex` files and open overlays, calls document-symbol parsing, then ranks names/containers | Display/search scan, not a resolver |
| Visual Studio intelligence | Routes the same nine frozen language-server methods through the native host | Client transport over existing LSP behavior |

**Observed current behavior.** Same-kind duplicate declarations fail before a
supported use-site ambiguity can exist. Module visibility constructs
`definition_owner: dict[current_air_id, module_name]`; a later equal ID
overwrites an earlier owner, and the linker subsequently reports the global
collision. This is a visibility gate, not an ambiguity-capable resolver.

**Architectural inference.** Module import resolution is the only existing
project graph resolver with explicit missing/cycle diagnostics. It cannot be
reused as a declaration resolver because its nodes are modules/documents, its
edges do not encode exported declarations, and direct dependency reachability
is not declaration binding.

## Metadata versus candidate versus binding

The future model must keep five concepts separate.

| Concept | Meaning | Required contents | Must not do |
| --- | --- | --- | --- |
| Metadata record | Intrinsic fact about one declaration already recognized by the build | P11.4B identity plus P11.3D physical/module owner | Apply use-site visibility, select a winner, or carry import paths |
| Resolution candidate | One declaration eligible to enter a kind/name query before final selection | Stable link to metadata/owner; kind; declared spelling; current AIR ID; source/module; structured qualification components; declaration span | Claim that it is visible from every use site; mutate AIR; serialize into artifact v1 by default |
| Resolved binding | One use-site query paired with exactly one candidate under an explicit rule | Use span/source/module; requested kind/name/qualification; chosen candidate; visibility/import evidence; compatibility AIR target | Rewrite declaration identity, discard evidence, or use display text as authority |
| Ambiguity set | Two or more equally selectable candidates after filters and supported precedence | Query plus deterministically ordered candidates and their paths/evidence | Pick the first dictionary/source/link order candidate |
| Diagnostic evidence | Stable presentation facts derived from failure/binding analysis | Primary use/declaration span; related declaration/import spans; requested spelling/kind; ordered candidates; access reason | Become the resolver’s mutable internal state or use AIR ID as a substitute for a missing binding |

### Candidate field analysis

**Recommended future contract.** A passive candidate must expose, directly or
through referenced immutable records:

- `kind`, `declared_name`, `current_air_id`, `source_name`, `module_name`, and
  declaration `span`;
- its exact `ProjectDeclaredIdentity` and matching
  `ProjectDeclarationOwner`, or an equivalently validated one-to-one link;
- structured module segments and a declaration path, initially one segment;
- a non-authoritative display projection; and
- a deterministic intrinsic ordering key.

`qualified lookup name` should initially be represented as structured
components, not stored only as a string. The candidate can expose a formatted
display value, but formatting must not define equality.

**Architectural inference.** `visibility_origin` and `import_path` are not
intrinsic candidate fields. They depend on the use-site document/module and
the query. They belong in candidate evidence produced during collection. A
candidate visible locally can be reached through a direct import from another
source and be inaccessible from a third.

**Recommended future contract.** `generic_owner` likewise should not appear on
every ordinary function candidate as a specialization field. A generic call’s
resolved binding should reference its ordinary function declaration candidate;
a separate generic-owner binding should pair that resolved declaration with
the unchanged specialization/lowering strata.

**Unresolved policy decision.** A failed current build does not return
`ProjectBuild`, so a passive index attached only to successful builds cannot
surface colliding declaration candidates externally. P11.4D can make the
record/index duplicate-capable without changing this failure boundary. Any
later partial-build diagnostic snapshot requires separate authorization.

## Qualification representation options

| Option | Advantages | Risks and compatibility result |
| --- | --- | --- |
| Module plus declared name as separate fields | Already grounded in P11.4B; preserves exact source/module spelling; no delimiter decision; easy deterministic filtering | Insufficient alone for future nested paths, aliases, or typed equality; callers may concatenate inconsistently |
| Structured qualification object | Can hold kind, exact module segments, declaration path, and later parent components separately; equality/order need not depend on display; AIR ID can remain a compatibility field | New model/API requiring explicit validation and ordering; must not invent nesting fields as semantic facts before later work |
| Canonical qualified lookup string | Convenient dictionary/log/API key and potential future user input | Prematurely freezes separator, escaping, normalization, kind encoding, legacy representation, alias handling, and generic interaction; current `:`, `::`, `.`, and `<...>` already have other roles |
| Display-only dotted projection | Existing, deterministic, readable, byte-neutral | Can collide across kind, cannot distinguish formatting from lookup, duplicates module segment text, and is not accepted source syntax; unsuitable as authority |

**Recommended future contract.** Use exact separate fields as the source facts
and a small structured internal qualification value for candidate equality and
ordering. A suitable conceptual key is:

```text
(
    kind,
    exact module segments or an explicit legacy marker,
    exact declaration path segments,
)
```

This is an internal structure, not approved source syntax and not a serialized
replacement AIR ID. `current_air_id` remains beside it as a compatibility
target. A formatter may continue to show the P11.4B dotted display projection.

Qualification constraints:

- **Case sensitivity.** Preserve exact-case declaration and import matching.
  Do not silently extend the module declaration’s `casefold()` collision rule
  into reference lookup. A unified future module-case policy is unresolved.
- **Normalization.** Do not Unicode-normalize or case-fold source identifiers
  without a separate language-wide grammar decision.
- **Separators.** No source separator is selected. Dot is already the module
  header separator and P11.4B display formatter; colon prefixes AIR IDs;
  double-colon encodes open generic type ownership; angle brackets are generic
  syntax.
- **Module grammar.** Current modules are one or more ASCII identifier
  segments separated by dots. Store validated segments, not a reparsed display
  string.
- **Legacy headerless sources.** Preserve absent module ownership. Do not
  fabricate a module from a source path, project name, or sentinel text.
- **Cross-kind coexistence.** Keep `kind` outside the display spelling and in
  the structured key. A directive and function with the same name remain
  legal and kind-directed.
- **Cross-module coexistence.** A future structured key can distinguish equal
  same-kind names in different modules, but current linker/AIR/runtime maps
  still prohibit them. Candidate modeling must not imply executable support.
- **Nested declarations.** Reserve a tuple-shaped declaration path in the
  conceptual contract, but P11.4C/P11.4D must populate exactly one segment.
- **Aliases.** An alias is a scope binding from reference spelling to a target
  qualification. It must never rewrite the declaration’s structured identity.
- **Generic owners.** Bind a generic use to a function candidate first; do not
  derive owner identity from the dotted display or specialization text.

## Collision taxonomy

| Category | Current behavior | Future candidate-set behavior | Detection stage; legal/selectable | Required evidence |
| --- | --- | --- | --- | --- |
| Duplicate declaration | Same current kind/ID fails link `APX-LINK-001`; directive duplicates often collide first at synthetic principal | Retain every candidate fact; classify equal structured declaration keys as a definition collision | Candidate/declaration validation before executable linking; declaration should remain illegal; no use-site selection | All declaration spans, kind, exact structured key, current IDs, deterministic primary/related order |
| Cross-kind same-name declaration | Directive and function coexist because prefixes and consumers choose kind first | Separate candidate partitions by kind | Legal; selectable when the query requires a kind | Both kinds only when reporting incorrect-kind or broad tooling search |
| Same-kind cross-module declaration | Still fails global flat link `APX-LINK-001` | Distinct qualified candidates; an unqualified visible query may become ambiguous | Future declaration should be legal only after linker/AIR/runtime coexistence work; qualified selection then possible | Exact module/source/span for each candidate and visibility path from the use site |
| Same-module collision | One module maps to one source today; a second same-case/case-variant module fails `APX-MODULE-009`; one module source permits one ordinary declaration | Equal module/kind/declaration path is a collision, not ambiguity | Module/declaration collection; illegal; no winner | Module spans plus declaration spans and exact/case-folded forms |
| Import collision | Equal same-kind imports cannot reach ambiguity because declarations link-collide first | Multiple directly imported candidates with the requested short name form an ambiguity unless later explicit policy disambiguates | Use-site resolution; declarations/imports may remain legal; unqualified selection fails, explicit qualification may succeed | Use span, each import span, target declaration span, direct path |
| Transitive import collision | Transitive declarations are not visible; known references fail `APX-MODULE-008` | Only relevant if a future policy grants transitive visibility | Visibility/resolution stage; current policy keeps candidates inaccessible | Use span, direct and transitive edge chain, candidate span, reason for accessibility/inaccessibility |
| Export collision | No export syntax or model | Multiple exported candidates under a future imported surface may collide or create ambiguity | Export-set construction and/or use-site resolution; policy deferred | Export declaration/re-export spans, original declaration, import path |
| Qualified-name collision | Not representable separately from current flat duplicate | Two candidates share the same structured kind/module/path key | Candidate collection; illegal unless a later overload/signature policy explicitly permits it | Exact structured components, all declarations, no display-string-only evidence |
| Display-name collision | P11.4B can retain equal display values across kind; same-kind executable duplicates fail later | Harmless unless a UI requires disambiguating labels | Legal metadata condition; selection must ignore display equality | Kind, structured key, source/module; tooling may add container/detail labels |
| Use-site ambiguity | No supported project-semantic ambiguity result | Two or more candidates remain after kind, qualification, visibility, and supported precedence filters | Resolver stage; declarations legal; use cannot bind until disambiguated | Use span, requested spelling/kind, all ordered candidates, import/visibility evidence |
| Entry ambiguity | Multiple directives without explicit entry produce the current generic explicit-entry error; equal names cannot coexist | Legacy short entry matches more than one eligible directive | Entry-resolution stage; declarations may be legal later; short entry fails, explicit qualification may select | Manifest/CLI entry origin if available, each directive span/qualification, deterministic candidate list |
| Alias collision | Alias syntax is rejected as malformed module syntax | Two bindings introduce the same alias in one lookup scope, or alias conflicts with a local/import spelling | Alias-scope construction; legality/precedence unresolved; declaration identity remains legal | Alias declaration spans, target qualifications, conflicting local/import facts |
| Future nested-scope shadowing | No nested directive/function declarations; local value/type scope has separate frozen rules | Same short name in parent/child lexical scopes may shadow or be forbidden by namespace/kind | Future scope construction and use-site resolution; policy unresolved | Use span, lexical scope chain, shadowed/shadowing declaration spans, kind |
| Generic-owner ambiguity | Impossible because equal function names collide globally | A generic call finds multiple generic function candidates before specialization | Resolver must fail before inference/specialization; declarations may be legal when qualified | Call span, requested type arguments, candidate owners, visibility paths, no fabricated specialization key |

**Recommended future contract.** Collision legality is decided on declaration
identity; ambiguity is decided at a use site after visibility. Neither should
be represented by dictionary overwrite. Candidate ordering must never act as
selection precedence.

## Resolution-precedence questions

Repository evidence supports filters more strongly than precedence. Kind,
explicit qualification, and accessibility should constrain a candidate set;
they should not be treated as “first match wins.”

| Possible source | Evidence and safe statement | Status |
| --- | --- | --- |
| Local declaration | Same-module targets are currently visible, but a local/imported equal name cannot coexist | **Unresolved policy decision:** whether local hides an imported declaration or creates ambiguity |
| Explicit selective import | No syntax/model exists | **Unresolved policy decision** |
| Explicit module qualification | No source syntax exists; a structured API could filter exact module components | **Recommended future contract:** treat qualification as an exact constraint, not a ranking rule; whether it bypasses import accessibility is unresolved |
| Direct import | Currently grants visibility to all known directive/function declarations in that module | **Observed current behavior:** direct only; **unresolved:** whether multiple direct matches are ambiguous and whether future exports narrow the set |
| Transitive visibility | Graph reachability exists, declaration visibility does not | **Observed current behavior:** inaccessible; do not infer precedence from dependency order |
| Legacy headerless declaration | Legacy mode is project-global and has no modules/imports | **Unresolved policy decision:** legacy compatibility in mixed or migrated qualification models; current mixed mode remains illegal |
| Entry declaration | Entry is a separate directive-only project selector, not a lexical use site | **Observed current behavior:** explicit short/current ID or sole-directive fallback; no general resolution precedence |
| Future lexical parent | No legal nested directive/function declarations | **Unresolved policy decision:** lexical parent search and shadowing wait for the nesting matrix |
| Future alias | No alias syntax or scope | **Recommended future invariant:** resolve alias binding separately, then target declaration; **unresolved:** alias/local/import collision precedence |

No declaration order, dependency order, source filename order, AIR order, or
candidate canonical order is recommended as semantic precedence. Those orders
exist for determinism, not meaning.

## Diagnostic requirements

**Observed current behavior.** Existing `APX-MODULE-*`, `APX-LINK-001`,
`APX-VALIDATE-*`, parser/compiler/type diagnostics, entry error text, and
runtime diagnostics remain the baseline. P11.4C adds no diagnostic.

**Recommended future contract.** Resolver-originated diagnostics should use a
dedicated `APX-RESOLVE-*` family once an emitting resolver is authorized.
Exact numeric assignments remain unresolved. A passive P11.4D index should
emit nothing.

| Failure | Stage | Primary span | Related spans/evidence | AIR ID treatment |
| --- | --- | --- | --- | --- |
| Unresolved name | Resolve, after parsing/candidate collection | Use-site name span | Import/qualification span when distinct; optionally inaccessible near matches as structured evidence | Empty unless a compatibility reference already denotes a real bound AIR object; never synthesize from spelling |
| Ambiguous name | Resolve | Use-site name span | Every candidate declaration and relevant import/alias span in canonical candidate order | Empty because no binding exists; include candidate current AIR IDs in evidence/message only |
| Duplicate declaration | Candidate/declaration validation; preserve link baseline until migration | First declaration under deterministic declaration order | Every colliding declaration | Existing `APX-LINK-001` continues to carry current AIR ID until a separately tested migration |
| Inaccessible declaration | Resolve/visibility | Use-site span | Candidate declaration plus blocking/missing import path evidence | Candidate current AIR ID may be evidence, not a selected binding |
| Incorrect kind | Resolve | Use-site span | Same-spelling candidates of other kinds | Empty; requested and available kinds are message evidence |
| Invalid qualification | Parse or resolve depending on whether syntax is malformed or structured components are unknown | Malformed/unknown qualification component | Module/alias declaration when one partially matches | Empty unless a valid module record is referenced separately |
| Ambiguous entry | Entry resolution | Entry origin span when available; otherwise project-level | Every eligible directive declaration and qualification | Empty because no entry is bound; do not choose the first current AIR ID |
| Generic owner not found | Resolve before inference | Generic call target span | Import/qualification evidence and optional wrong-kind candidates | Empty; do not create `Target<T>` |
| Generic owner ambiguous | Resolve before inference | Generic call target span | Every generic-function declaration candidate and visibility path | Empty; no specialization/lowered ID may be generated |

Deterministic candidate ordering should be based on intrinsic semantic facts,
then physical evidence:

1. kind;
2. explicit legacy/module discriminator;
3. exact module segments;
4. exact declaration path segments;
5. source name case-folded, then exact;
6. declaration span offsets; and
7. current AIR ID as a final compatibility tie-breaker.

**Recommended future contract.** Related spans must follow candidate order,
not the order in which dictionaries, imports, source mappings, or linker units
happen to be traversed. Messages should include the requested spelling and
kind, candidate module/source labels, and the access path needed to explain
the result. Display projections may appear in messages, but structured facts
remain the authority.

**Unresolved policy decision.** `DiagnosticStage` currently has no `resolve`
literal. Adding it changes a public diagnostic model and tooling data. A later
emitting slice must decide whether to add `resolve` or temporarily classify
resolver failures under `module`/`validate`; P11.4C recommends a distinct
stage rather than overloading existing meanings.

## Generic-owner binding

**Observed current behavior.** The lifecycle is:

1. the generic declaration is one `AIRFunction` with flat ID
   `function:Identity`;
2. each `ApexTypeVariable.owner` equals that flat function ID;
3. calls retain a short/current target and optional type arguments;
4. validator and type inference resolve through name/ID signature maps;
5. `GenericSpecializationKey` uses `signature.name`, producing
   `Identity<int>`;
6. the instantiation table deduplicates by that canonical string;
7. closure expansion finds the generic AIR function by short name; and
8. lowering hashes the unchanged specialization canonical ID to create a
   deterministic synthetic function ID/name and rewrites calls to the
   generated short name.

P11.4B correctly indexes only the source generic function declaration. It
does not index specializations, closure nodes, host generics, generated
functions, or lowering bindings.

**Recommended future contract.** A qualified resolver should bind the call
target to an ordinary declared function candidate before generic inference.
A generic-owner binding sidecar should retain:

- the use-site span and requested spelling/qualification;
- the resolved declaration’s structured qualification;
- its unchanged `current_air_id`;
- the unchanged current specialization key and projection; and
- the unchanged lowered binding when current global uniqueness permits it.

For today’s globally unique functions this sidecar can preserve all current
function AIR IDs, `Identity<int>` canonical keys, SHA-derived lowered targets,
closure ordering, and diagnostics without rewriting AIR.

**Architectural inference.** Two qualified generic declarations with the same
short name cannot both use the existing global `Identity<int>` table and
lowered `__apx_spec__Identity...` name without collision. An internal table
could eventually be scoped by `(resolved owner identity, existing
specialization key)`, but the current public canonical string and lowering
digest would still collide at executable AIR.

**Unresolved policy decision.** Supporting executable coexistence of equal
short generic owners requires a versioned owner-aware specialization/lowering
contract or another stable runtime indirection. P11.4D and P11.4E must not
relax generic declaration collisions while claiming to preserve the current
lowered target identity. Resolver ownership can be added passively first;
executable coexistence is later compatibility work.

## Entry migration constraints

**Observed current behavior.** Manifest schema 1 stores one optional string.
CLI `--entry` overrides it. The project resolver accepts exact `directive:Name`
or prepends `directive:` to an exact short name. With no explicit entry,
exactly one directive is selected; multiple directives require an explicit
entry. Artifact v1 stores the resolved flat directive ID or null. CLI runtime
constructs authority grants and runtime roots from that ID.

**Recommended future contract.** A future migration should:

- keep current short and `directive:` forms working when they select exactly
  one declaration;
- accept a qualified form only after its source/API separator and module
  accessibility policy are explicitly authorized;
- report deterministic ambiguity for a legacy short form with multiple
  candidates rather than choosing by order;
- resolve to a declaration binding first, then adapt to the runtime’s
  compatibility target;
- preserve manifest/CLI override precedence; and
- version any artifact field or runtime identity change instead of silently
  changing artifact v1 bytes.

**Architectural inference.** Qualification alone does not let two equal-name
directives execute: the linker, validator, runtime index, authority resource,
trace IDs, and artifact AIR still use one flat `directive:Name`. A qualified
entry can safely map to a current ID only while that ID is globally unique.

**Unresolved policy decisions.** A manifest entry has no use-site module, so
it is unclear whether qualified/unqualified entry candidates are project-wide,
restricted to an application/root module, or governed by future exports. It
is also unresolved whether schema 1 may accept a newly parsed string form or
whether qualification requires a new manifest/artifact schema.

## Tooling implications

| Feature | Current behavior | Future resolver artifact needed | Owner |
| --- | --- | --- | --- |
| Document symbols | One-document syntax hierarchy, including parsed-only and nested syntax forms | None for basic syntax display; optional candidate/binding ID for semantic detail later | Parser/LSP remains presentation owner; project layer supplies semantics |
| Workspace symbols | Recursive file scan and syntax flattening, not manifest/project aware | Candidate index for canonical project declarations plus overlay reconciliation | Project/workspace semantic service, consumed by LSP |
| Hover | One-document syntax descriptions | Resolved binding, candidate metadata, type/generic owner, and accessibility evidence | Compiler/project resolver; LSP formats result |
| Definition | Same-document lexical occurrence graph | One resolved binding with declaration source/span; ambiguity yields no single location plus diagnostic/evidence | Project resolver owns binding; LSP maps span to URI/range |
| References | Same-document occurrences | Stable binding identity plus project-wide use-site binding index | Compiler/project semantic index; LSP queries |
| Rename | Only safe local/member lexical namespaces | Binding identity, complete project reference set, alias-versus-declaration distinction, collision simulation | Project resolver/index plus edit planner; LSP must not infer from display name |
| Completion | Syntax/lexical suggestions | Candidate collection for the current use context, with visibility/kind filters and deterministic ranking separate from semantic precedence | Project resolver supplies candidates; LSP ranks/presents |
| Diagnostics | Lexer/module-header/parser only | Resolver failures and ordered diagnostic evidence; workspace publication across affected documents | Compiler/project diagnostic owner; LSP transports |
| Visual Studio intelligence | Same frozen LSP semantics through native host | No independent model; it consumes whatever versioned LSP contract is later exposed | Python language server remains semantic endpoint |

**Recommended future contract.** The compiler/project layer must own semantic
candidates and bindings because it has canonical project membership, module
and document graphs, source maps, declaration metadata, and eventual build
diagnostics. The language server must not create a competing resolver by
combining workspace symbol names or `qualified_display_name` strings.

**Architectural inference.** Moving tooling to project semantics requires a
workspace/project snapshot service because the current server parses one open
document and workspace symbols scan arbitrary `.apex` files without loading a
manifest. Unsaved overlays, invalid documents, partial candidate sets, and
incremental invalidation are later tooling contracts, not P11.4D work.

**Unresolved policy decision.** Project-wide rename must decide whether an
alias use renames the alias binding, the target declaration, or is offered as
two explicit operations. That decision cannot be derived from current
same-document rename.

## Nesting boundary

P11.4C defines only the resolver contracts later nesting needs:

- qualification equality must be structural and able to extend from one
  declaration path segment to a tuple of segments;
- a use-site query must be able to carry a future lexical scope/parent chain;
- candidates must retain source/owner spans independently of display text;
- aliases must remain bindings, not declaration identity rewrites; and
- ambiguity evidence must support candidates at different lexical depths.

P11.4C does not define nesting syntax, legal parent/child declaration pairs,
capture, lexical traversal, shadowing precedence, multiple declarations per
module source, or nested AIR/runtime ownership. P11.4D should populate exactly
one declaration-path segment and no parent field.

`extend` and `converge` are also outside this audit. Later work must decide
whether they create declarations, contributions to one declaration, composite
identities, or reference bindings. The resolver can require candidates and
origin evidence without choosing those semantics now.

The boundary is therefore:

- P11.4C: vocabulary, structured candidate/binding/evidence contracts, risks,
  and staging;
- future naming/nesting matrix: legal declarations, parents, scopes, and
  shadowing;
- future composite identity work: stable equality for authorized multi-part
  declarations;
- future alias work: scope bindings and collision/rename rules; and
- future `extend`/`converge` work: contribution and ownership semantics.

## Compatibility invariants

Every future resolver slice must explicitly preserve or version these facts:

1. P11.4B metadata remains immutable, factual, and non-resolving.
2. `qualified_display_name` never becomes lookup authority by implication.
3. Current directive/function and member AIR IDs remain exact until an
   explicitly versioned migration.
4. Same-name cross-kind declarations remain legal and kind-directed.
5. Existing same-kind duplicate phase, code, primary/related ordering, and AIR
   ID remain the baseline until a tested compatibility change.
6. Distinct-module same-kind declarations continue to collide until linker,
   validator, runtime, generic, artifact, entry, and tooling coexistence are
   authorized together as needed.
7. Module name case-folded uniqueness and exact import lookup remain exact;
   no silent normalization is introduced.
8. Direct imports grant the current narrow visibility; transitive reachability
   does not grant visibility; exports remain absent.
9. Legacy headerless project-global behavior remains exact and does not gain a
   fabricated module identity.
10. Generic declaration IDs, type-variable owners, canonical specialization
    keys, closure, lowering targets, and ordinary-build exclusion remain exact.
11. Entry strings, CLI override rules, authority resources, runtime roots, and
    artifact v1 resolved entry remain exact.
12. Runtime lookup, traces, diagnostics, and event-record identities remain
    module-unaware until separately migrated.
13. Manifest schema 1 and artifact v1 field sets/bytes/fingerprints gain no
    candidate or resolver metadata implicitly.
14. LSP and Visual Studio retain their frozen syntax/same-document behavior
    until a dedicated tooling slice consumes project resolver artifacts.
15. Determinism is explicit: candidate order supports stable results but never
    acts as semantic winner selection.

## Explicit non-goals

P11.4C does not add or change:

- lexer, parser, grammar, qualification syntax, module syntax, or aliases;
- compiler binding, source maps, AIR models/IDs, linker, validator, or runtime;
- `ProjectBuild`, `ProjectIdentityIndex`, `ProjectDeclaredIdentity`, ownership,
  module/document graphs, imports, exports, visibility, or entry selection;
- duplicate/collision acceptance, ambiguity diagnostics, or diagnostic stages;
- generic inference, specialization, closure, lowering, or indexing;
- manifests, artifact schemas, serialization, CLI commands/output, or runtime
  authority;
- language-server, VS Code, or Visual Studio behavior;
- nested declaration syntax, lexical parent traversal, composite identity,
  `extend`, or `converge`; or
- P11.4D implementation, P11.5 work, commits, tags, releases, or remote state.

## Recommended implementation sequence

The sequence proposed for evaluation is directionally sound, but executable
same-name coexistence and entry migration are more tightly coupled to AIR and
runtime identity than the labels alone suggest.

1. **P11.4D Passive Resolver Candidate Index.** Add immutable, deterministic
   candidate facts over successful P11.4B declarations. Use structured
   qualification components; no source syntax, query winner, visibility
   result, diagnostic, AIR rewrite, or tooling consumer.
2. **P11.4E Structured Resolution Query and Binding Contract.** Define a
   project API accepting structured queries/use-site context and producing
   candidate evidence, one binding, or an ambiguity object. Initially run only
   over currently successful globally unique builds and do not change compiler
   diagnostics or AIR.
3. **P11.4F Qualified Use-Site Integration and Collision Migration Plan.** Only
   after the query contract is stable, authorize any source qualification,
   compiler binding, emitted resolver diagnostics, and linker/AIR/runtime
   coexistence needed by that syntax. Generic owner-aware executable identity
   must be explicit here or in a dedicated preceding slice.
4. **P11.4G Entry Qualification Migration.** Preserve legacy unique entries,
   define ambiguous entry diagnostics and project-root visibility, and version
   manifest/artifact/runtime effects as required. Do not precede executable
   directive coexistence.
5. **P11.4H Naming and Nesting Matrix.** Specify legal declaration parents,
   scope traversal, shadowing, composite paths, source cardinality, and tooling
   effects before adding nested declarations.
6. **P11.4I Aliases, `extend`, and `converge` Identity Contracts.** Add
   reference-only alias bindings and separately define contribution/composite
   semantics using the established structured identity and evidence model.

**Architectural inference.** Combining P11.4E and P11.4F would risk treating
an API/display key as source syntax and simultaneously changing diagnostics,
AIR, runtime, and tools. Separating passive/query layers from executable
integration keeps the first stages reviewable and reversible.

## Acceptance evidence

The executable record is
`apexforge/p11_4c_resolver_qualification_architecture_audit_smoke_test.py`.
It directly proves:

- the exact frozen P11.4B public fields, immutability, and absence of resolving
  fields;
- display-name metadata filtering without entry lookup authority;
- unchanged flat directive/function AIR IDs and same-name cross-kind behavior;
- unchanged legacy and cross-module same-kind `APX-LINK-001` failure phase,
  identity, primary span, and related span;
- accepted direct/transitive/legacy visibility and absent export behavior;
- exact short/current-ID entry behavior and rejection of dotted/colon forms;
- unchanged generic declaration owner, `Identity<int>` key, closure, lowered
  synthetic ID, and exclusion from P11.4B metadata;
- unchanged runtime directive lookup and authority resource behavior;
- byte-identical artifact v1 before/after metadata inspection, unchanged
  manifest schema, and exact CLI check/run/build output boundaries;
- unchanged LSP cross-file/import non-resolution, callable rename protection,
  frozen integration hash, and Visual Studio intelligence hash;
- exactly the existing `language.identities` and `language.project` production
  consumption boundary, with no new resolver abstraction;
- blocked network access, external context-managed fixtures, working-directory
  preservation, repository-status preservation, and repository-bytecode
  before/after preservation.

Validation is required with UTF-8 mode and bytecode writes disabled. The
focused P11.4C, P11.4B, and P11.4A tests must pass before the complete official
harness. The expected complete discovery count is 91 smoke tests.

## Recommended P11.4D scope

The exact next substage should be **P11.4D Passive Resolver Candidate Index**.
It should remain metadata-only and smaller than a resolver.

Recommended authorized production boundary:

- add one `language` module containing frozen candidate/index records and a
  structured internal qualification value;
- modify `language.project` only to construct the candidate index beside the
  existing ownership and identity metadata and append it to `ProjectBuild`
  with an empty default and `compare=False`.

Recommended candidate contents:

```text
ProjectResolutionCandidate(
    identity: ProjectDeclaredIdentity,
    owner: ProjectDeclarationOwner,
    qualification: ProjectQualification,
)

ProjectQualification(
    kind: str,
    module_segments: tuple[str, ...],
    declaration_path: tuple[str, ...],
    legacy: bool,
)

ProjectResolutionCandidateIndex(candidates=())
```

This shape is a recommendation for the P11.4D design review, not an API
implemented or canonized by P11.4C. Validation must require the identity and
owner to describe the same kind/current AIR ID/source/module/span.
`declaration_path` must contain exactly the one current declared name;
`module_segments` must be the exact validated module segments or empty only
for legacy; `legacy` must distinguish absence from an empty/synthetic module.

P11.4D queries should be factual selectors only: by source, module components,
kind/declared name, structured qualification, and current AIR ID. They must
return every match in canonical order. They must not accept a source-level
qualified string, inspect imports, compute visibility, carry import paths,
select a winner, create a binding/ambiguity, emit a diagnostic, alter link
collisions, bind generics, select entries, serialize, execute, or feed tooling.

P11.4D should add one focused smoke test and one stage document. It should not
modify any P11.4A/P11.4B record except if a historical wrapper requires the
same narrowly justified additive-field compatibility alignment already used
by P11.4B. No grammar, compiler, AIR, linker, validator, runtime, module,
visibility, entry, CLI, artifact, manifest, LSP, VS Code, or Visual Studio file
belongs in that slice.

The remaining limitation must be explicit: because canonical builds still
fail on same-kind duplicates, the public candidate index will initially exist
only for successful builds. Its record/index constructors can retain duplicate
facts, but no partial failed-build result or executable ambiguity behavior is
authorized.
