# P11.4E Structured Resolution Query and Binding Contract

## Scope and frozen baseline

P11.4E adds a pure library contract for asking a structured declaration
question of the passive P11.4D candidate index. It introduces explicit result
records for unique, zero-match, and multiple-match outcomes. It does not
integrate name resolution into normal project construction or ApexForge source
semantics.

The controlling baseline is P11.4D commit
`0d4d0f4b4c46f53456df0200446e22653e04fa87`, frozen by annotated tag
`afp-p11.4d-freeze`. The tag object is
`4707475199208aeb2ba582779994a4e92a75bb29`. P11.4D candidate records,
candidate ordering, `ProjectBuild` integration, and the two-file P11.4D
ownership boundary remain frozen and unchanged.

P11.4E is an explicit metadata operation. It parses no source, changes no
compiler behavior, and emits no diagnostic.

## Public production model

The sole P11.4E production module is `language.resolution_queries`. It exports
four frozen dataclasses and one pure function:

```text
ProjectResolutionQuery(
    kind: str,
    declaration_path: tuple[str, ...],
    module_segments: tuple[str, ...] | None = None,
)

ProjectResolvedBinding(
    query: ProjectResolutionQuery,
    candidate: ProjectResolutionCandidate,
)

ProjectUnresolvedResolution(
    query: ProjectResolutionQuery,
)

ProjectAmbiguousResolution(
    query: ProjectResolutionQuery,
    candidates: tuple[ProjectResolutionCandidate, ...],
)

resolve_project_query(index, query)
```

The exact public exports are those five names. No resolver class, registry,
cache, mutable state, alias, or dynamic export exists. Nothing is re-exported
from `language.__init__`.

## Structured query representation

`ProjectResolutionQuery` is structured metadata. It is not a dotted source
name and has no parsing operation.

`kind` is exactly `directive` or `function`. `declaration_path` normalizes to a
tuple and contains exactly one valid ApexForge identifier in P11.4E. This
single-segment rule preserves the later nesting boundary. Exact spelling and
case are retained.

`module_segments` has three distinct modes.

### Unqualified mode

```text
module_segments = None
```

An unqualified query places no legacy-or-module ownership restriction. A
candidate may match whether its qualification is legacy or module-owned.

### Exact legacy mode

```text
module_segments = ()
```

An exact legacy query matches only a candidate whose qualification has both:

```text
legacy = True
module_segments = ()
```

### Exact module mode

```text
module_segments = ("App", "Core")
```

A non-empty tuple is an exact module query. It matches only a candidate whose
qualification has both:

```text
legacy = False
module_segments == query.module_segments
```

Each module segment must be a valid ApexForge identifier. Empty internal
segments are invalid. A dotted string such as `"App.Core"` is not accepted as
one module segment or as a substitute for structured module data.

## Exact matching rules

A candidate matches only when:

```text
candidate.qualification.kind == query.kind
candidate.qualification.declaration_path == query.declaration_path
```

and the selected module mode is satisfied exactly.

Matching performs no Unicode normalization, case folding, fuzzy comparison,
alias expansion, display-name comparison, fallback lookup, or kind coercion.
`qualified_display_name` is not consulted. Same-name directive and function
candidates remain distinct because every query requires an exact kind.

The function iterates the frozen candidate tuple directly. Matching candidates
therefore retain the P11.4D canonical order and duplicate records.

## Match-count outcomes

`resolve_project_query` determines its result solely from the number of exact
matches:

```text
0 matches  -> ProjectUnresolvedResolution
1 match    -> ProjectResolvedBinding
2+ matches -> ProjectAmbiguousResolution
```

There is no other branch. Candidate order does not influence the outcome except
to present deterministic evidence.

## Binding validation

A `ProjectResolvedBinding` requires a `ProjectResolutionQuery` and a
`ProjectResolutionCandidate`. The candidate must exactly match the query under
the same kind, declaration-path, and module-mode rules used by the function.

The uniqueness guarantee belongs to `resolve_project_query`, which has the
candidate index available. Direct construction of a matching binding validates
the facts but does not inspect an external index and therefore does not claim
external uniqueness.

A nonmatching direct binding is rejected with a normal model validation
exception. No ApexForge diagnostic is produced.

## Unresolved and ambiguous results

`ProjectUnresolvedResolution` contains only its validated query. It is not an
unresolved-name diagnostic and has no source span, code, or rendered message.

`ProjectAmbiguousResolution` requires at least two matching candidates. Direct
construction normalizes the candidates through the P11.4D candidate index,
which applies the frozen canonical evidence order and retains duplicates.

An ambiguous result contains no singular candidate, winner, selected item,
ranking, or preferred result. The first candidate is never semantically
privileged. Ambiguity is an explicit result shape, not a diagnostic.

## Explicit successful-build usage

Callers may explicitly query an already successful build:

```python
outcome = resolve_project_query(
    project.resolution_candidate_index,
    ProjectResolutionQuery(
        kind="directive",
        declaration_path=("Main",),
        module_segments=("App", "Main"),
    ),
)
```

No method was added to `ProjectBuild`. `ProjectBuilder` was not modified. No
query runs automatically during parsing, compilation, module analysis,
visibility validation, linking, AIR validation, entry selection, artifact
construction, CLI operation, runtime execution, or tooling requests.

P11.4D constructs candidate metadata only for successful builds. P11.4E does
not alter that boundary and creates no partial build or failed-build query
surface.

## Duplicate-link boundary

Same-kind duplicate declarations continue to fail during the existing link
stage with `APX-LINK-001`, including same-kind declarations in different
modules. Such a failed build exposes no `ProjectBuild`, candidate index, query
outcome, or binding.

The duplicate-capable ambiguity contract applies to directly constructed
passive indexes and to any future legal candidate source. It does not bypass
or weaken the current linker collision rule.

## Generics boundary

A generic function declaration may match only through its ordinary declaration
candidate and current AIR ID, such as `function:Identity`.

P11.4E creates no candidate or binding for:

- specialization keys such as `Identity<int>`;
- lowered `__apx_spec__` function IDs;
- instantiated type arguments;
- generic-owner metadata.

Specialization keys are not valid declaration-path identifiers. A syntactically
valid query resembling a lowered synthetic name simply returns an unresolved
result because no such declaration candidate exists. Generic closure and
lowering remain unchanged.

## Compatibility invariants

Explicit querying does not mutate the index, AIR, or project. Validation proves:

- AIR remains byte-equivalent before and after querying;
- entry lookup remains flat and unchanged;
- artifact v1 bytes, schema, and fingerprint omit query and binding metadata;
- CLI version, check, run, and build behavior and output remain unchanged;
- runtime state, events, traces, authority resources, and entry execution remain
  unchanged;
- LSP definitions, references, rename, hover, completion, symbols, formatting,
  and diagnostics remain unchanged;
- VS Code packaging and language-server integration remain unchanged;
- Visual Studio bridge, diagnostics, intelligence, commands, and packaging
  fingerprints remain unchanged;
- no `APX-RESOLVE-*` diagnostic exists.

## Production boundaries

The exact P11.4E production boundary is one file:

```text
apexforge/language/resolution_queries.py
```

The frozen P11.4D ownership and construction boundary remains:

```text
apexforge/language/resolution_candidates.py
apexforge/language/project.py
```

`language.resolution_queries` is the single authorized successor consumer of
the candidate model. No other production file consumes the P11.4E query or
result records.

## Historical-test alignments

The P11.4C source guard retains its per-marker, per-file enforcement. Its exact
allowlist now recognizes the necessary `ResolutionCandidate`,
`ResolvedBinding`, and `language.resolution` occurrences in
`apexforge/language/resolution_queries.py`. Every marker remains forbidden in
every unlisted path, and unlisted forbidden markers remain rejected even in the
authorized file. The file is inspected rather than skipped.

The P11.4D smoke test still identifies
`language.resolution_candidates` and `language.project` as the two P11.4D-owned
production files. It separately identifies `language.resolution_queries` as
the one reviewed P11.4E successor consumer. Another candidate-model consumer
would fail the check.

The frozen P11.4D documentation was not modified.

## Explicit non-goals

P11.4E does not add or decide:

- ApexForge source syntax or qualified-name parsing;
- automatic project resolution;
- lexical-scope or nested-declaration traversal;
- import, export, visibility, or accessibility evidence;
- aliases;
- ranking, precedence, fallback, or winner selection;
- unresolved, ambiguous, inaccessible, or incorrect-kind diagnostics;
- diagnostic spans, codes, or related evidence;
- source-map binding;
- entry qualification;
- AIR, artifact, manifest, CLI, runtime, or tooling serialization;
- binding serialization;
- generic specialization or instantiated-owner resolution;
- mutable resolver state, registries, or caching.

## Acceptance evidence

The P11.4E smoke test proves exact exports and frozen field shapes, query and
result validation, all three module modes, exact-case matching, display-name
non-authority, all match-count outcomes, duplicate ambiguity without selection,
direct-model rejection, cross-kind separation, explicit successful-build use,
unchanged duplicates and entries, the generics boundary, AIR and artifact
invariance, CLI/runtime/tooling compatibility, exact production boundaries,
blocked network access, external temporary fixtures, and working-directory,
Git-status, and bytecode-state preservation.

The focused P11.4E through P11.4A tests must pass before the complete official
harness. With the new smoke test, expected discovery is 93 tests.

## Next proposed stage

The next proposed stage is:

```text
P11.4F Resolution Context and Visibility Evidence Contract
```

That stage may define passive context and visibility evidence needed to refine
structured matching, subject to a separate reviewed contract. P11.4E does not
implement or begin P11.4F.
