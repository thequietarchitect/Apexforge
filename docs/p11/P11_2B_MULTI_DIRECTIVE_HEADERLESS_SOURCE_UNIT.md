# P11.2B Multi-Directive Headerless Source Unit

## Status, scope, and authority

This document records the implementation candidate for the P11.2B production
slice. It does not declare the slice accepted, frozen, canonized, released, or
complete; repository ownership and final review remain human responsibilities.

P11.2B introduces one controlled compatibility extension: a headerless legacy
physical `.apex` source may contain two or more complete sequential declarations
using the existing `directive` syntax. It adds no separator, modifier, alias,
export, nesting form, grouping form, keyword, generic directive, or new
declaration family.

The frozen P10 baseline is commit `38a3778`. P11.1 is frozen at commit
`5ba048a` under tag `afp-p11.1-freeze`. P11.2A is accepted at commit
`b6f9277`. The continuity revision preceding implementation is `3eb07a1` on
branch `p11.2-multi-declaration`.

## Non-goals

This slice does not add multiple functions, workflows, authorities, principals,
or roles to one source. It does not accept a mixed directive/function source or
any other mixed declaration family. It adds no nested directives, modules,
imports, exports, aliases, namespaces, qualification, overloads, declaration
modifiers, packages, cache behavior, artifact execution, or runtime mode.

Nested declaration identity redesign has not begun. P11.2C, P11.3
modules/imports, P11.4 identity work, and all later roadmap work have not begun.

## Exact grammar compatibility extension

The historical P10 ordinary source rule remains:

```text
P10_OrdinarySource = HeaderSection? Declaration EOF
```

P11.2B adds a separate narrow alternative rather than redefining `Declaration`
as a general list:

```text
P11_2B_Source = HeaderlessDirectiveSequence | P10_OrdinarySource
HeaderlessDirectiveSequence = DirectiveDeclaration
                              InterDirectiveTrivia DirectiveDeclaration
                              (InterDirectiveTrivia DirectiveDeclaration)* EOF
InterDirectiveTrivia = (Whitespace | LineComment)+
LineComment = "//" LineCharacter* LineEnd
```

The compatibility overlay is recorded in `language.grammar` separately from
the frozen P10 EBNF and P10 fingerprint. The historical generated P10 grammar
exports and conformance corpus remain unchanged and reviewed as the base
grammar; P11.2B coverage verifies the overlay directly.

Whitespace remains ordinary lexer whitespace. Because the frozen P10 lexer had
no general comment syntax, P11.2B recognizes `//` line comments through an
opt-in lexer path only when parsing inter-directive trivia. Such comments are
accepted only between complete directives. Leading, trailing, headered,
intra-directive, function, and general-source comments remain unsupported. No
block-comment syntax is introduced.

The intentional source-unit asymmetry is therefore:

- ordinary single-declaration sources remain unchanged;
- module/import-header sources remain limited to one declaration;
- a headerless legacy source may additionally contain sequential directives;
- functions and mixed declaration lists remain unsupported.

## Parser and source-unit representation

The existing public `parse(source)` entry retains its exact single-node return
shape and still consumes `EOF` after one ordinary declaration. Existing callers
therefore see no container or API change.

P11.2B adds the narrowly named
`parse_headerless_directive_source_unit(source)`. It returns a tuple of the
original `DirectiveNode` objects in physical source order. It creates no general
source-unit AST and exposes no future declaration syntax. Every node and nested
reference retains its original source name, offsets, line/column positions, and
full declaration span. The parser loop has no recovery and preserves first-error
behavior.

## Compiler and AIR flow

`compile_source_with_map` parses the directive tuple and lowers every node
independently through the existing directive compiler contract. It composes
those results into one existing `AIRProgram` by concatenating existing AIR
collections in source order. No AIR declaration type or field is added.

Each directive receives zero-based local `order` from its physical position.
The project linker still orders each unit by local order and assigns contiguous
project-global order. The compiler preserves `directive:Name`,
`principal:Name`, `auth:Name`, `state:Name`, `event:Name`, `cause:Name`, and
cause-local `path:Name` exactly. Invocation objects retain short source
references; linked validation/runtime continue resolving short and canonical
references after all declarations are linked.

Project module analysis remains the mode authority. `ProjectBuilder` enables
the compatibility path only for a fully legacy/headerless graph and explicitly
disables it in module mode after header masking. Modules and imports remain
unchanged and a headered source retains one declaration.

## Ordering and split-source equivalence

For valid directives A then B, one headerless source containing A then B
produces the same linked semantic AIR as adjacent legacy source units containing
A and B in that same project order. Equivalence includes directive identities
and order; principals and authority checks; states, events, causes, paths,
requirements, references; linked validation; entry resolution; and runtime
behavior.

The canonical artifact AIR member is equal. A source-metadata-free projection
containing canonical AIR has the same deterministic SHA-256 fingerprint.

Physical provenance legitimately differs. Source-unit names, source lists,
exact source hashes, source-map filenames and locations, artifact source
records, and consequently complete P11.1C artifact fingerprints may differ.
P11.2B does not erase those differences to force byte identity.

## Duplicate, collision, and identity behavior

The composed program reaches the existing linker. A same-source duplicate is
rejected at link stage with `APX-LINK-001`; source-map matches provide the first
declaration span and later related span. The first collision may remain the
synthetic `principal:Name`, so tests do not canonize incidental owner wording.

Cross-source duplicates retain the same path. State, event, and cause IDs remain
flat program-global identities, so same-kind reuse across directives collides.
Cross-kind short-name reuse remains accepted because prefixes differ. Path
uniqueness remains cause-local: `path:Name` may repeat in distinct causes.

No nested identity redesign, owner qualification, namespace, alias, export, or
overload behavior is introduced.

## Forward references

All contained directives are lowered before linked validation. A directive may
invoke a later or earlier directive in the same source. Undefined invocation
targets retain `APX-VALIDATE-002` and the invocation source span.

## Entry selection, authority, and runtime

| Condition | Result |
| --- | --- |
| One linked directive and no entry | Existing implicit canonical fallback |
| Multiple directives and no entry | Ambiguous for run/resolve; build may record `null` |
| Explicit short `Name` | Resolves to `directive:Name` |
| Explicit `directive:Name` | Resolves directly |
| Undefined explicit/manifest entry | Existing entry error |

Public `run` still grants only selected-entry invocation. A downstream
directive independently checks authority and is denied with `RUN001` without
its grant; transactional rollback remains. No root, wildcard, cross-directive,
or inferred grant and no runtime execution mode is added.

## CLI, artifact, and P11.1 preservation

Public `apexforge check`, `run`, and `build` accept the new source shape through
the existing project pipeline. `project`, `new`, and `--version` are unchanged.
Build remains non-executing and artifact execution remains unsupported.

The artifact schema remains exactly `apexforge.build-artifact/v1` with
`schema`, `project`, `air`, and `fingerprint`. No field is added. Exact source
hashing, canonical UTF-8 JSON, fingerprint boundary, atomic replacement,
failure preservation, temporary cleanup, public output, and exit codes remain
the frozen P11.1 contracts.

## Diagnostics

Tests assert stage, code, source/span, canonical collision identity, and related
locations rather than new full-message wording:

| Case | Stable boundary |
| --- | --- |
| Malformed second expression | parse / `APX-PARSE-004`, second declaration |
| Nested directive | parse / `APX-PARSE-003`, nested keyword |
| Same-source duplicate | link / `APX-LINK-001`, collision ID and related span |
| Undefined invocation | validate / `APX-VALIDATE-002`, call site |
| Mixed directive/function | parse / `APX-PARSE-001`, second keyword |
| Headered multiple directives | parse / `APX-PARSE-001`, second keyword |
| Invalid trailing token | parse / `APX-PARSE-001`, trailing token |

## Compatibility matrix

| Source shape | P11.2B behavior |
| --- | --- |
| One headerless directive | Accepted with unchanged AIR/parser shape |
| Two or more headerless directives | Accepted in physical order |
| Inter-directive whitespace and `//` comments | Accepted |
| One headerless function | Unchanged |
| Multiple functions | Rejected |
| Directive/function mix | Rejected |
| Multiple workflows/authorities/principals/roles | Rejected |
| Nested directive | Rejected |
| Headered source with multiple directives | Rejected |
| Module sources with one declaration each | Unchanged |
| Generic directive | Unsupported |

## Changed production surfaces

- `apexforge/language/lexer.py`: opt-in inter-directive comment token.
- `apexforge/language/parser.py`: directive-only source-unit parser.
- `apexforge/language/compiler.py`: existing directive lowering composition.
- `apexforge/language/project.py`: legacy enablement/module disablement.
- `apexforge/language/grammar.py`: separate compatibility grammar notes.

AIR model, linker, serialization, runtime engine, CLI, project loader, artifact
writer, manifest schema, and module/import semantics are unchanged.

## Test and document surfaces

- `apexforge/p11_2b_multi_directive_source_unit_smoke_test.py` adds focused
  production coverage.
- `apexforge/p11_2a_declaration_model_audit_smoke_test.py` changes only the
  historical two-directive rejection expectation required by P11.2B; function
  and mixed-family rejections remain.
- This document records the implementation/review contract.

No accepted P11.1 fixture is modified.

## Known limitations

- This is directive-only, not a general declaration list.
- Only `//` comments between complete directives are recognized; there is no
  general/block-comment feature.
- Parser recovery remains out of scope.
- Flat state/event/cause identities and synthetic-principal wording remain.
- Source maps remain build metadata and are not added to artifact v1.
- AIR deserialization/artifact execution remain unsupported.
- Modules/imports retain one declaration per physical source.
- Functions and mixed declaration lists remain unsupported.

## Exact acceptance checklist

- [ ] Human review confirms the change is limited to P11.2B.
- [ ] Two/three sequential headerless directives compile in source order.
- [ ] Whitespace and `//` comments between declarations are accepted.
- [ ] Forward/reverse same-source invocations resolve after linking.
- [ ] Single-directive parser shape, AIR, IDs, spans, and runtime remain compatible.
- [ ] One-source and adjacent split-source semantic AIR are equal.
- [ ] Physical-source provenance differences are retained/documented.
- [ ] Same/cross-source duplicates retain source-aware link rejection.
- [ ] Flat state/event/cause and cause-local path behavior is preserved.
- [ ] Fallback, ambiguity, and short/canonical entries pass.
- [ ] Entry-only authority and downstream denial pass.
- [ ] Public check/run/non-executing build pass.
- [ ] Artifact v1 schema, hashing, fingerprint, and atomic write pass.
- [ ] All required invalid-source diagnostics pass.
- [ ] Grammar export/conformance and frozen P10 syntax tests pass unchanged.
- [ ] P11.2A and P11.1A through P11.1D gates pass.
- [ ] Generic function coverage proves functions were not broadened/broken.
- [ ] Complete regression passes with `PYTHONUTF8=1`.
- [ ] No accepted fixture, temporary project, generated residue, bytecode,
      commit, tag, merge, push, freeze, or release is produced.
- [ ] P11.2C, P11.3, identity redesign, and later work were not implemented.
