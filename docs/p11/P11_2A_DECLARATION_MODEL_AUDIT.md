# P11.2A Declaration Model Audit and Compatibility Contract

## Scope and non-goals

P11.2A records the declaration behavior that exists before P11.2 work. It adds
one current-behavior smoke test and this audit. It does not change production
grammar, parser, compiler, AIR, linker, validation, serialization, project,
manifest, CLI, authority, runtime, or tooling behavior.

This slice does not add declaration syntax or semantics. It does not begin
P11.2B, modules/imports work for P11.3, identity expansion for P11.4,
storytelling semantics, Compiler TAM, Quad-Vector work, AETHER-AIR 2.0, TAP
Check, caching, packages, agents, ApexMotion, native compilation, or any later
roadmap slice.

The audit uses `declaration` for a named source construct. A keyword's presence
in the lexer or frozen grammar does not imply that the canonical project
pipeline lowers, links, validates, serializes, or executes that construct.

## Frozen baseline

P11.1 is frozen at commit `5ba048a` under tag `afp-p11.1-freeze`. The current
working revision inspected for this audit contains that commit as an ancestor.
P10's frozen grammar contract remains important here: it explicitly defines
`ApexForgeSource = HeaderSection? Declaration EOF` and states that a source
unit contains one ordinary top-level declaration.

P11.2A preserves the complete P11.1 public surface:

- `apexforge project`
- `apexforge check`
- `apexforge run`
- `apexforge build`
- `apexforge new`
- `apexforge --version`
- the P11.1A observational performance baseline
- the `apexforge.build-artifact/v1` schema and fingerprint rules
- P11.1 execution, entry, authority, and non-execution boundaries

## Inspected implementation surfaces

The audit inspected every required starting surface:

- `pyproject.toml`
- `apexforge/language/parser.py`
- `apexforge/language/compiler.py`
- `apexforge/language/project.py`
- `apexforge/language/diagnostics.py`
- `apexforge/air/model.py`
- `apexforge/air/serialization.py`
- `apexforge/tooling/project_loader.py`
- `apexforge/tooling/project_manifest.py`
- `apexforge/tooling/cli.py`
- `apexforge/runtime/engine.py`
- `apexforge/regression_harness.py`

Repository search then identified and the audit inspected these directly
relevant implementation surfaces:

- frozen source grammar, export, conformance, lexer, source spans, and module
  header analysis in `language/grammar.py`, `grammar_export.py`,
  `grammar_conformance.py`, `lexer.py`, `source.py`, and `modules.py`
- AIR function models, linking, and verification in `air/functions.py`,
  `air/linker.py`, and `air/verify.py`
- semantic and runtime validation in
  `language/validation/semantic_validator.py` and `runtime_validator.py`
- generic constraints, inference, specialization closure, lowering, and freeze
  audit in `type_system/constraints.py`, `generics.py`, `inference.py`,
  `specialization.py`, `closure.py`, `lowering.py`, and `freeze.py`
- standalone legacy/partial lowering or execution in `role_compiler.py`,
  `principal_compiler.py`, `authority/compiler.py`, and
  `workflow/workflow_engine.py`
- build-artifact construction in `tooling/build_artifact.py`

The inspected current-behavior coverage included parser and compiler smoke
tests; project builder and P7 project integration; AIR linking; function
frontend, linking, validation, and runtime; P8 typed compilation; P9 generic
declaration, inference, explicit arguments, constraints, specialization,
closure, lowering, and integration; source diagnostics; module/import legacy
coverage; grammar conformance; and all P11.1A through P11.1D gates.

## Complete current top-level declaration inventory

All six forms below are public in the frozen P10 source grammar. Their
downstream support differs materially.

| Form | Accepted source syntax | AST | Canonical project support | Status |
| --- | --- | --- | --- | --- |
| Function | `function Name<T : constraint>? (parameters) : ReturnType? { let/when/otherwise/return }`; at least one return is required | `FunctionNode` | Lowers to one `AIRFunction` in an `AIRProgram`, links across sources, validates and executes as a pure function, and participates in generic closure/lowering | Public; supported across source units |
| Directive | `directive Name { state/event/authority/requires/cause... }` | `DirectiveNode` | Lowers to one `AIRDirective` plus its principal, authority check, states, events, causal decisions, paths, requirements, and references; links, validates, serializes, and executes | Public; supported across source units |
| Workflow | `workflow Name { invoke Target... }` | `WorkflowNode` | Main compiler rejects with `APX-COMPILE-007`; no AIR program declaration or project linker support. A separate legacy engine consumes the AST directly | Public parse syntax; parsed but not lowered or linked |
| Authority | `authority Name extends Parent? { capability Name... }` | `AuthorityNode` | Main compiler rejects with `APX-COMPILE-007`; no canonical project AIR mapping. A separate legacy compiler is outside the project pipeline | Public parse syntax; parsed but not lowered or linked |
| Principal | `principal Name { authority Name | role Name... }` | `PrincipalNode` | Main compiler rejects with `APX-COMPILE-007`; no canonical project AIR mapping. A standalone legacy helper is outside compiler dispatch | Public parse syntax; parsed but not lowered or linked |
| Role | `role Name { authority Name... }` | `RoleNode` | Main compiler dispatch lowers it to standalone `AIRRole`, not `AIRProgram`; `ProjectBuilder` therefore rejects it as a project source | Public parse syntax; partially lowered, not project-linked |

No source can contain two entries from this table. After parsing one node,
`parse()` consumes `EOF`; a second top-level keyword is rejected with the parse
category `APX-PARSE-001`.

### Nested declaration inventory

| Construct | Legal containment | AST | Lowered representation and identity | Duplicate behavior |
| --- | --- | --- | --- | --- |
| Type parameter | Function header only | `TypeParameterNode` / `ApexTypeVariable` | `AIRFunction.type_parameters`; owner `function:Name`; source-map ID `type_parameter:Name:index` | Duplicate names rejected by parser with `APX-PARSE-009`; built-in type shadowing and unknown constraints are also rejected |
| Value parameter | Function header only | `ParameterNode` | `AIRParameter`; source-map ID `parameter:Name:index`; not a program-global symbol | Duplicate names rejected by compiler with `APX-COMPILE-008` |
| Local binding | Function statement or conditional block | `LetNode` | `AIRLocalBinding`; lexical runtime binding, not a program-global symbol | Leading duplicates use `APX-COMPILE-009`; full lexical duplicate/shadow checks also occur during linked validation |
| State | Directive only | `StateNode` | `StateDefinition`, `state:ShortName` | Duplicate global IDs fail linking with `APX-LINK-001`, including duplicates in one directive or different directives |
| Event | Directive only | `EventNode` | `EventDefinition`, `event:ShortName` | Duplicate global IDs fail linking with `APX-LINK-001` |
| Cause | Directive only | `CauseNode` | `CausalDecision`, `cause:ShortName` | Duplicate global IDs fail linking with `APX-LINK-001` |
| Path | Cause only | `PathNode` | `CausalPath`, `path:ShortName` | Duplicate path IDs within one cause fail validation; the current diagnostic is generic `APX-VALIDATE-999`. The same path ID in different causes is accepted |
| Directive authority reference | Directive only | `DirectiveAuthorityNode` | `DirectiveAuthority(name=...)` in `AIRProgram.authorities`; name-keyed by linker | Duplicate names fail linking, currently through generic `APX-LINK-999` without a source span |
| Requirement | Directive only | `RequirementNode` | `DirectiveRequirement`; source-map ID `requirement:Directive:index`; serialized in AIR | Repeated identical requirements are currently accepted; this is not promoted to a permanent contract |
| Capability | Authority only | `CapabilityNode` | No canonical project AIR mapping from source | Parser accepts repeats; project compilation stops at the unsupported authority node |
| Workflow invocation | Workflow only | `WorkflowInvokeNode` | No AIR project mapping; legacy workflow engine iterates AST references | Repeated invocations are actions, not duplicate declarations |
| Role authority reference | Role only | `RoleAuthorityNode` | `AIRRoleAuthority(name=...)` in standalone `AIRRole` | Standalone lowering preserves repeats; project linking is unavailable |
| Principal role/authority reference | Principal only | `PrincipalRoleNode` / `PrincipalAuthorityNode` | No canonical project mapping from source | Parser accepts repeats; main compiler rejects the containing principal |

States, events, causes, and paths may reuse the same short spelling inside one
directive because their canonical prefixes differ. Function and directive
names may likewise share a short spelling across sources. These are current
cross-kind behaviors, not a general alias or namespace facility.

## Scope and containment matrix

| Declaration family | Top level | Function local | Directive local | Cause local | Path local | Other |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Function | Yes, exactly one declaration per source | No nested functions | No | No | No | Type parameters, parameters, and lexical `let` bindings belong to the function |
| Directive | Yes, exactly one declaration per source | No | No nested directives | No | No | States, events, causes, authority references, and requirements belong to the directive syntax |
| Workflow | Yes, exactly one declaration per source | No | No | No | No | Workflow invocations belong to a workflow |
| Authority | Yes, exactly one declaration per source | No | `authority Name` is only a reference member, not a nested authority declaration | No | No | Capabilities belong to a top-level authority AST |
| Principal | Yes, exactly one declaration per source | No | No | No | No | Role and authority references belong to a principal |
| Role | Yes, exactly one declaration per source | No | No | No | No | Authority references belong to a role |
| State/event/cause | No | No | Yes | No | No | A cause contains paths |
| Path | No | No | No | Yes | No | A path contains actions; actions are not declarations |

Placing a top-level keyword inside a function, directive, cause, or path is
rejected at the grammar point for that container. There is no parser recovery:
parsing stops at the first lex/parse error and returns one structured
diagnostic.

## Parser-to-AIR mapping

| Parser node | Compiler/lowering output | AIR collection | Runtime relevance |
| --- | --- | --- | --- |
| `DirectiveNode` | One directive plus synthetic principal and authority check; flattened states, events, causes, paths, requirements, and references | `directives`, `principals`, `authority_checks`, `states`, `events`, `causal_decisions`, `requirements`, `authorities` | Entry execution, authority check, causal decision/path actions, state/event changes, and directive invocation |
| `FunctionNode` | One `AIRFunction` with ordered body, parameters, return/type metadata, and type parameters | `functions` | Pure expression calls through linked function resolution |
| `RoleNode` | Standalone `AIRRole` only | None in the canonical project path | No canonical project runtime relevance from source |
| `WorkflowNode` | None in main compiler | None | Separate legacy AST workflow engine only |
| `AuthorityNode` | None in main compiler | None | Separate legacy helper only; not project runtime input |
| `PrincipalNode` | None in main compiler | None | Separate legacy helper only; not project runtime input |

`air_to_dict` recursively serializes all dataclass fields, including linked
functions, roles, requirements, and generic metadata, while preserving tuple
order as JSON array order. This is the path used by P11.1C build artifacts.
`air_from_dict` reconstructs only the older core directive-oriented subset and
does not restore functions, roles, authorities, requirements, or generic
metadata. Therefore current public artifact serialization is one-way; a full
AIR round trip and artifact execution are not supported.

## Symbols and identity

| Source concept | Current canonical declaration identity or key | Reference behavior |
| --- | --- | --- |
| Directive | `directive:Name` | Project entries accept `Name` or `directive:Name`; `invoke Name` is stored as the short source reference and resolved against both forms |
| Synthetic directive principal | `principal:DirectiveName` | Used by directive and public-run authority boundaries |
| Synthetic directive authority check | `auth:DirectiveName` | Referenced by the lowered directive |
| Function | `function:Name` | Calls retain their source target spelling; linked validation/runtime accept short or canonical function references |
| State | `state:Name` | Plain and canonical state lookup are accepted; identity is not directive-scoped |
| Event | `event:Name` | Emit lowering resolves the directive-local spelling to this ID |
| Cause | `cause:Name` | Referenced from its lowered directive; identity is not directive-scoped |
| Path | `path:Name` | Stored inside its cause; identical IDs may exist in different causes |
| Requirement | `requirement:Directive:index` in the source map only | AIR requirement has capability and optional principal, not this ID |
| Function parameter | `parameter:Function:index` in the source map only | Lexical name in the AIR function |
| Function type parameter | `type_parameter:Function:index` in the source map; variable owner `function:Function` | Generic signature and call inference use the owned type variable |
| Generic specialization | `Function<Type,...>` such as `Identity<int>` | Closure records are deterministic compile-time identities; lowering maps each linked specialization to a generated concrete `function:` identity |
| Role/authority | Current standalone/link keys are unprefixed `name` values | Not available as canonical project declarations from the corresponding source forms |

Canonical prefixes separate current function/directive and state/event/cause
cross-kind names. They do not scope nested declarations by their containing
directive or cause. No alias, export identity, module-qualified declaration
identity, overload set, or general declaration symbol graph exists.

## One-source and multi-source compatibility

| Scenario | One source | Multiple sources | Classification |
| --- | --- | --- | --- |
| Multiple directives | Rejected after the first declaration with `APX-PARSE-001` | Supported when every linked global ID is unique | One-source rejection is intentional frozen grammar; cross-source support is established |
| Multiple functions | Rejected after the first declaration with `APX-PARSE-001` | Supported, including forward calls | Same classification |
| Mixed functions and directives | Rejected after the first declaration with `APX-PARSE-001`, in either order | Supported; each kind has an independent canonical prefix and order sequence | Cross-source behavior supported, previously weakly covered |
| Multiple workflows | Rejected as multiple declarations before downstream concerns | Each source parses, but every workflow is rejected by main compiler | Parsed, not lowered/linked |
| Multiple authorities | Same | Same | Parsed, not lowered/linked |
| Multiple principals | Same | Same | Parsed, not lowered/linked |
| Multiple roles | Same | Standalone lowering produces non-`AIRProgram` units, which the project builder rejects | Partially supported only outside projects |
| Generic functions and users | Rejected if concatenated into one source | Supported across sources; linked specialization collection and lowering cross the source boundary | Supported |

There is no existing multi-declaration one-source representation against which
multi-source AIR can be equivalent. The current compatibility statement is
instead exact: one declaration per source succeeds where that declaration
family is supported, and concatenating the same declarations into one source
is rejected. P11.2A tests both sides without inventing equivalence.

Optional `module`/`import` lines are a frozen pre-parser header facility. They
are masked without shifting offsets, after which the ordinary parser still
receives exactly one declaration. In legacy mode, source filename order drives
compilation. In existing module mode, dependency order drives compilation and
direct imports constrain directive/function visibility. This audit records
that inherited behavior only; it does not begin P11.3.

## Ordering and determinism

1. `ProjectManifest` normalizes declared relative paths and sorts them by
   `(casefolded path, original path)`. It does not retain the authored JSON
   array order. `LoadedProject.sources` must exactly preserve this canonical
   manifest order.
2. `ProjectBuilder` likewise sorts legacy mapping or iterable source units by
   `(casefolded source name, source name)`. Mapping insertion order therefore
   cannot affect linked AIR.
3. Existing module mode uses deterministic topological dependency order with
   casefolded lexical tie-breaking.
4. The linker processes programs in that selected unit order. Within each
   unit, directives and functions are sorted by local `order` then canonical
   ID. It then assigns independent contiguous global `order` values to each
   declaration kind.
5. AIR stores declaration kinds in separate tuples. It therefore preserves
   deterministic order within each kind, not a mixed function/directive source
   interleaving.
6. Generic specialization tables and lowering use canonical deterministic
   order and deduplicate repeated equivalent specialization records.
7. `SourceMap` entries and build diagnostics use deterministic source-aware
   sort keys. P11.1C canonical JSON sorts object keys while preserving AIR
   array order.

The P11.2A smoke test repeats a build with reversed mapping insertion order and
requires identical `air_to_dict` output. It also exercises a temporary manifest
whose authored list is reversed and verifies canonical manifest order through
loading and linking.

## Duplicate and collision behavior

- A second top-level declaration in one source is a parse-cardinality error,
  not a duplicate-name analysis.
- Duplicate cross-source function IDs fail linking with `APX-LINK-001`, with
  the first canonical source span and later spans as related locations.
- Duplicate directive names also fail linking. Because directive lowering
  creates `principal:Name` before directives are merged, the first reported
  colliding owner may be the synthetic principal rather than the directive.
  The rejection is reliable; the owner wording is not promoted as a contract.
- State, event, and cause identities are flat across the entire linked program.
  Two otherwise distinct directives cannot currently reuse one of those
  same-kind short names.
- Path uniqueness is checked within each cause, not across the linked program.
- Function/directive and state/event/cause identical short names are accepted
  because their canonical prefixes differ. Resolution remains kind-specific.
- Duplicate function parameters, generic type parameters, and lexical locals
  are rejected at their existing parser/compiler/validator boundaries.
- Repeated requirements are currently accepted. Repeated directive authority
  names fail through a generic link diagnostic. Neither incidental outcome is
  declared a permanent public design.
- No overload resolution exists. Same-kind top-level names are duplicates,
  regardless of parameter or generic signature differences.

## Forward references and cross-declaration resolution

- A directive may refer to states and events declared later in the same
  directive because lowering constructs the complete directive-local maps
  before lowering actions.
- Directive invocations resolve after programs are linked. Forward and reverse
  cross-source references therefore behave the same in legacy projects;
  existing module mode additionally requires direct visibility.
- Function calls are recorded during compilation and validated against the
  complete linked function index. Calls to a function in a later canonical
  source work. The same applies to a directive expression calling a linked
  function.
- Undefined directive calls use `APX-VALIDATE-002`; undefined function calls
  use `APX-VALIDATE-003`; arity failures use `APX-VALIDATE-004`; recursive
  function cycles use `APX-VALIDATE-005` where the existing mapper recognizes
  the failure.
- Cross-kind short names do not create ambiguous call resolution because each
  resolver selects its declaration family before applying the canonical
  prefix.
- Top-level within-source forward references are inapplicable: a source has no
  second top-level declaration.

## Generic compatibility

Generic declarations apply only to functions. Type parameters have owned
identity, optional current constraints, and may appear in parameter and return
annotations. Calls support inference and explicit type arguments.

After source compilation and AIR linking, the specialization collector scans
the complete linked program, including calls in other functions and directive
expressions. A generic declaration and its user may therefore reside in
different source units and in either filename/dependency order. Closed records
use identities such as `Identity<int>`, are deduplicated deterministically, and
may then be materialized by the existing generic lowerer. Unused generic
declarations do not create specializations.

`ProjectBuilder` validates linked generic calls but does not itself replace the
project's source-generic AIR with the result of `lower_linked_generics`.
Generic lowering remains its existing explicit boundary. There are no generic
directives, workflows, authorities, principals, roles, states, events, causes,
or paths.

## Diagnostics and source attribution

- Lexer, parser, compiler, module, link, and recognized linked-validation
  failures carry `BuildDiagnostic` values with stable stages and codes.
- Source spans retain the provided source-unit name. Module header masking
  preserves exact offsets.
- Same-file invalid nesting is reported at the unexpected nested keyword. The
  focused audit uses `APX-PARSE-003` and checks the source name without freezing
  the full message.
- Cross-file duplicate definitions use `APX-LINK-001`; the primary span is the
  first deterministic source-map match and later definitions are related
  spans.
- Cross-file undefined function resolution uses the call-site source span and
  `APX-VALIDATE-003`, even when other linked files are present.
- Parser recovery is not implemented. One source parse stops at the first
  error, and project construction stops without a partial `ProjectBuild`.
- Some validation/link failures not recognized by `language.project`'s current
  mapping fall back to `APX-LINK-999` or `APX-VALIDATE-999` and may lack a
  source span. Duplicate path IDs and directive authority references expose
  this weak boundary.
- The source map is build-time metadata and is not part of the P11.1C AIR
  artifact schema.

## Entry-selection interaction

Only linked directives are entry candidates.

| Linked directive count and selection | Current behavior |
| --- | --- |
| Explicit short `Name` | Resolves to `directive:Name` when defined |
| Explicit canonical `directive:Name` | Resolves directly when defined |
| Exactly one directive, no explicit/manifest entry | `ProjectBuild.resolve_entry` returns that directive's canonical ID |
| Multiple directives, no explicit/manifest entry | `run`/`ProjectBuild.resolve_entry` fails with `ProjectEntryPointError`; `build` preserves P11.1C behavior and records null when no entry is selected |
| Zero directives, no entry | Fails with `ProjectEntryPointError`; its current message says “multi-directive” and is incidental wording |
| Undefined explicit or manifest entry | Fails with `ProjectEntryPointError` |

Functions, roles, workflows, authorities, and principals never participate in
entry fallback. P11.2A does not expose `RuntimeEngine.execute`'s compatibility
all-directive path through the public CLI.

## Classification summary

### Supported and already covered

- one directive per source and multiple directives across sources
- one function per source and multiple linked functions across sources
- cross-source directive invocation and function calls
- deterministic legacy filename order and existing module dependency order
- canonical directive/function entry and call resolution
- same-kind duplicate rejection across files
- function generic declarations, constraints, closed specialization records,
  linked closure, and deterministic lowering
- one-directive fallback and multi-directive entry ambiguity

### Supported but weakly covered before P11.2A

- a mixed linked program containing both directives and functions without
  relying on module fixtures
- identical function/directive short names in one linked program
- the explicit contrast between rejected one-source concatenation and accepted
  split-source declarations
- canonical manifest sorting carried through declaration link order
- generic declaration/use split across canonical source order in a focused
  declaration audit

The P11.2A smoke test strengthens only these current-behavior observations.

### Partially supported

- role source parses and lowers to standalone `AIRRole`, but cannot enter the
  canonical `AIRProgram` project pipeline
- AIR JSON writing covers the current dataclass model, while `air_from_dict`
  reconstructs only the older directive subset
- nested identities appear canonical but have inconsistent containment scope:
  state/event/cause are program-global while path is cause-local in validation

### Parsed but not fully lowered or linked

- workflow
- authority
- principal

### Rejected intentionally

- more than one ordinary top-level declaration in a source under the frozen
  P10 grammar
- declarations nested in an illegal container
- same-kind linked canonical duplicates
- invalid function lexical duplicates, generic parameter duplicates,
  constraints, call arity, unresolved calls, and recursive cycles
- ambiguous or undefined project entries

### Rejected incidentally or with weak diagnostics

- a role source in a project is rejected because compiler output is `AIRRole`
  where `ProjectBuilder` requires `AIRProgram`
- duplicate directive authority names use generic link fallback diagnostics
- duplicate path IDs use generic validation fallback diagnostics
- zero-directive entry failure reuses multi-directive message wording
- distinct directives collide when they reuse flat state, event, or cause IDs;
  the deterministic rejection is real, but P11.2A does not canonize flat
  containment as the final P11 identity design

### Not implemented

- a source-unit AST containing multiple ordinary declarations
- within-source mixed declaration order and inter-declaration source-unit
  lowering
- generic declaration families other than functions
- overloads, aliases, exports, or a general declaration/symbol graph
- module-qualified declaration identity
- full source-aware mappings for every linker/validator failure
- full AIR/build-artifact deserialization or artifact execution

## Current architectural risks

1. The parser's single-root contract is the immediate compilation-unit
   bottleneck: the linker is multi-declaration-capable only because each source
   contributes one supported declaration.
2. Six public grammar families but only two canonical project families create
   a parse/compile capability mismatch; role adds a third incompatible partial
   shape.
3. Flat state/event/cause IDs prevent otherwise independent directives from
   reusing common member names. Path scoping differs, so the apparent prefix
   scheme does not encode one consistent containment model.
4. Directive duplicate diagnostics may identify a synthetic principal first,
   and some nested duplicate failures fall back to unsourced `999` categories.
5. Repeated requirements are accepted without an explicit duplicate policy.
6. Linked validation deliberately completes some resolution that isolated
   compilation cannot. Any future declaration container must retain that
   staged boundary rather than introducing order-dependent compile behavior.
7. Public serialization is intentionally one-way. Treating `air_from_dict` as
   a full declaration round trip would lose current declarations and metadata.
8. AIR separates declaration kinds into tuples, so it has no representation of
   mixed source declaration order.

These are audit findings, not production changes or permanent language-design
decisions.

## Exact first implementation gap selected for P11.2B

Proposed name: **P11.2B Multi-Directive Headerless Source Unit**.

This is the smallest coherent gap because directive AIR, linking, validation,
runtime behavior, entries, diagnostics, and deterministic ordering already
exist across source units. The missing boundary is only a source-unit container
that can carry more than one existing directive declaration.

The proposed narrow acceptance boundary is:

1. Accept two or more sequential uses of the existing directive syntax in one
   headerless, legacy-mode source unit. Add no declaration separator, modifier,
   alias, nesting form, or new keyword.
2. Introduce the smallest parser/source-unit representation needed to retain
   directive nodes and spans in source order. Preserve the existing return and
   behavior for a source containing exactly one directive unless a separately
   reviewed compatibility adapter is required.
3. Lower each contained directive through the existing directive lowering
   contract into one linkable AIR program. Preserve every existing canonical
   identity, action/reference rule, and source span.
4. Assign deterministic local directive order from source order; preserve the
   existing project source order and linker global renumbering.
5. Make the one-source result equivalent to the same directives split into
   adjacent headerless sources under the same declaration order, except for
   source-unit/source-map provenance.
6. Reject same-source canonical duplicates through a stable, source-aware
   duplicate category without weakening cross-source duplicate checks.
7. Preserve one-directive fallback, multi-directive ambiguity, explicit short
   and canonical entries, public run authority, and P11.1 build artifacts.
8. Keep functions, roles, workflows, authorities, principals, module/import
   headers, nested identity redesign, and every other declaration family out
   of this slice.

This boundary improves multi-declaration coherence without combining unrelated
families, inventing syntax, entering P11.3 modules/imports, or attempting P11.4
identity expansion. It is independently testable with parser, compiler,
linker, validation, entry, artifact, and source-diagnostic cases.

P11.2B has not begun. P11.3 and all later roadmap work have not begun.

## P11.2A repository-integrity contract

The only intended P11.2A files are:

- `apexforge/p11_2a_declaration_model_audit_smoke_test.py`
- `docs/p11/P11_2A_DECLARATION_MODEL_AUDIT.md`

No production file or accepted P11.1 fixture is changed. The smoke test uses a
temporary project that is removed by `TemporaryDirectory`, makes no network
call, uses no AI service, and creates no repository output. P11.2A creates no
commit, tag, merge, push, freeze, or release.
