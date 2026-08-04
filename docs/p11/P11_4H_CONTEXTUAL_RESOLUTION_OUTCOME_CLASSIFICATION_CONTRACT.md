# P11.4H Contextual Resolution Outcome Classification Contract

## Scope and frozen baseline

P11.4H is the closing stage of P11.4. It classifies the candidate tuple retained
by the frozen P11.4G visibility policy through the frozen P11.4E resolution
outcome operation.

The controlling baseline is:

- branch: `p11.4-identity-nesting`;
- P11.4G commit: `a316c006623ab8f48009a3c86d09af7f517ad9ee`;
- annotated freeze: `afp-p11.4g-freeze`;
- tag object: `b8dbe9d28a376e55ae973a0af2ba00815295acb9`.

The P11.4G freeze and all earlier freezes remain immutable. P11.4H changes no
candidate discovery, query matching, context facts, evidence derivation,
visibility policy, ordering, or frozen outcome model.

## Closing-stage purpose

P11.4H performs one count-based classification:

```text
zero visible candidates     -> ProjectUnresolvedResolution
one visible candidate       -> ProjectResolvedBinding
multiple visible candidates -> ProjectAmbiguousResolution
```

This is classification over the final visible tuple. It is not a new resolver
architecture, candidate-selection mechanism, or policy layer.

## Sole production module

P11.4H has exactly one production file:

```text
apexforge/language/resolution_outcomes.py
```

Nothing is re-exported through `language.__init__`.

The exact public API is:

```python
__all__ = (
    "resolve_project_contextual_query",
)
```

The module defines no public class, dataclass, outcome record, type alias,
constant, configurable classifier, resolver, policy, diagnostic, mutable state,
cache, alias, or dynamic export.

## Exact public function

```python
def resolve_project_contextual_query(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> (
    ProjectUnresolvedResolution
    | ProjectResolvedBinding
    | ProjectAmbiguousResolution
):
    ...
```

The function requires exact instances of `ProjectResolutionCandidateIndex`,
`ProjectResolutionQuery`, and `ProjectResolutionContext`. Invalid arguments raise
`TypeError` before filtering. No ApexForge diagnostic is emitted.

## Mandatory frozen-operation reuse

The architecture is exactly:

```python
visible_candidates = filter_project_visible_candidates(
    index,
    query,
    context,
)

visible_index = ProjectResolutionCandidateIndex(
    visible_candidates,
)

return resolve_project_query(
    visible_index,
    query,
)
```

P11.4H invokes the frozen P11.4G filter once, constructs one candidate index from
exactly the filtered tuple, and invokes the frozen P11.4E classifier once with
the exact caller-supplied query.

It does not copy or reimplement P11.4E matching, P11.4E classification, P11.4F
evidence derivation, P11.4G visibility, candidate ordering, duplicate handling,
or outcome validation.

## No direct outcome construction

`resolve_project_query` remains the sole constructor-facing classification
authority. The P11.4H module does not directly instantiate:

```text
ProjectUnresolvedResolution
ProjectResolvedBinding
ProjectAmbiguousResolution
```

These names appear only as frozen imported result types and in the function's
return annotation.

## Zero-visible classification

An empty filtered tuple produces the exact frozen
`ProjectUnresolvedResolution` record.

This covers both:

- a query that originally matched no candidates; and
- a query that matched candidates but whose candidates were all filtered out.

P11.4H intentionally does not distinguish those causes. The unresolved result
contains only its frozen query field. It acquires no reason, inaccessible state,
hidden-candidate count, rejected candidates, evidence, decisions, diagnostics,
or source spans.

## One-visible classification

A one-candidate filtered tuple produces the exact frozen
`ProjectResolvedBinding` for that candidate.

The visible candidate may have qualified through same-source, same-module,
imported-module, legacy-context, or overlapping P11.4G bases. Those facts are not
copied into the binding and do not change its structure.

A raw ambiguous query may become resolved when filtering retains exactly one
candidate. This is classification by final tuple count, not winner selection.

## Multiple-visible classification

A filtered tuple containing two or more candidates produces the exact frozen
`ProjectAmbiguousResolution` containing every visible candidate.

P11.4H does not select the first candidate, rank by visibility, prefer any basis,
deduplicate equal candidates, or reduce ambiguity through precedence.

The ambiguous outcome tuple is exactly the canonical tuple in the filtered
candidate index.

## Raw ambiguity reduction

P11.4G filtering may transform an initially ambiguous P11.4E query match set in
three ways:

```text
all candidates hidden       -> unresolved
exactly one candidate kept  -> resolved binding
multiple candidates kept    -> ambiguous
```

P11.4H observes only the final tuple. It does not report the raw match count,
hidden candidates, visibility evidence, or policy decisions.

## Canonical ordering

P11.4G preserves P11.4D canonical candidate order. P11.4H constructs the frozen
candidate index from that exact tuple, so the order remains canonical when passed
to `resolve_project_query`.

Invisible candidates do not alter the retained candidates' relative order. No
contextual rank or visibility precedence is introduced.

## Duplicate retention

Duplicate candidate entries remain distinct through filtering, intermediate
index construction, and classification:

```text
()                     -> unresolved
(candidate,)           -> resolved
(candidate, candidate) -> ambiguous
```

Two equal or identical candidate objects are still two entries. They are not
collapsed before P11.4E classification. A duplicate-visible ambiguity retains
both entries.

## Exact query preservation

The caller-supplied `ProjectResolutionQuery` object remains authoritative through
the complete operation:

```text
index + exact query + context
        |
P11.4G filtering with the same query
        |
filtered index + the same query
        |
frozen P11.4E outcome
```

P11.4H does not reconstruct, normalize, weaken, broaden, or replace the query.
Declaration kind, declaration path, module mode, legacy qualification, module
qualification, exact spelling, and exact case retain frozen P11.4E semantics.

## Query-mode behavior

An unqualified query retains frozen matching before P11.4G applies visibility.

An exact legacy query retains exact legacy matching, followed by same-source or
legacy-context visibility and then count classification.

An exact module query retains exact module matching, followed by P11.4G
visibility and count classification. Exact qualification does not bypass
visibility.

Exact kind separation remains intact. Same-name directives and functions do not
mix.

## Frozen outcome identity

P11.4H returns only:

```text
ProjectUnresolvedResolution
ProjectResolvedBinding
ProjectAmbiguousResolution
```

It introduces no contextual, visible, classification, binding, or inaccessible
outcome class.

Frozen outcomes acquire no field for context, evidence, visibility decision,
visibility basis, accessibility, selection, rank, precedence, score, weight,
reason, hidden candidates, diagnostic, or source span.

## Explicit-only successful-build usage

The function may be called explicitly after a successful build:

```python
outcome = resolve_project_contextual_query(
    project.resolution_candidate_index,
    ProjectResolutionQuery(
        kind="directive",
        declaration_path=("Main",),
    ),
    ProjectResolutionContext(
        source_name="src/main.apex",
        module_segments=("App", "Main"),
        imported_modules=(("Lib", "Core"),),
    ),
)
```

No method is added to `ProjectBuild`, `ProjectBuilder`, the candidate index,
query, context, evidence, visibility decision, or frozen outcome records.

Contextual resolution is not invoked automatically during parsing, compilation,
module analysis, linking, validation, entry resolution, artifact construction,
CLI operation, execution, LSP requests, VS Code operations, or Visual Studio
operations.

## Duplicate-link boundary

Same-kind duplicate declarations continue to fail during linking with
`APX-LINK-001`. A failed build exposes no project, candidate index, query result,
context, evidence, visibility decision, filtered tuple, or contextual outcome.

P11.4H cannot bypass the existing linker collision boundary.

## Cross-kind boundary

Same-name declarations of different kinds remain legal and distinct. Frozen
exact-kind query matching occurs before visibility filtering and classification.

## Generic boundary

A generic declaration participates only through its ordinary declared function
candidate. Specialization keys, lowered synthetic functions, `__apx_spec__`
identifiers, instantiated type arguments, and generic-owner records do not gain
contextual outcomes.

Synthetic specialization queries remain unresolved. Generic closure, canonical
specialization keys, lowering, and generated target IDs remain unchanged.

## Compatibility invariants

Contextual classification is observational. It does not change:

- AIR or serialized AIR bytes;
- artifact v1 bytes or fingerprints;
- manifests or entry resolution;
- compiler, linker, or validator behavior;
- CLI version, check, run, or build behavior;
- runtime state, events, traces, authority resources, or execution;
- LSP, VS Code, or Visual Studio behavior;
- existing diagnostics.

No `APX-RESOLVE-*` diagnostic exists.

## Production ownership boundaries

P11.4H is owned by exactly:

```text
apexforge/language/resolution_outcomes.py
```

P11.4G remains owned by exactly
`apexforge/language/resolution_visibility.py`. Its only P11.4H successor consumer
is the outcome module.

P11.4F remains owned by exactly
`apexforge/language/resolution_context.py`. Its reviewed consumers are the
visibility and outcome modules.

P11.4E remains owned by exactly
`apexforge/language/resolution_queries.py`. Its reviewed consumers are the
context, visibility, and outcome modules.

P11.4D remains owned by exactly:

```text
apexforge/language/resolution_candidates.py
apexforge/language/project.py
```

Its reviewed consumers are the query, context, visibility, and outcome modules.
The complete candidate-model production set is exactly these six files.

## Historical-test alignments

The P11.4C guard retains its exact per-file, per-marker allowlist. It authorizes
only the candidate, frozen binding, and `language.resolution` markers necessarily
present in the outcome module. `ProjectResolver` and resolver diagnostics remain
forbidden.

The P11.4D boundary preserves its two ownership files and adds only the outcome
module to reviewed consumers.

The P11.4E boundary preserves its single ownership file, adds only the outcome
module to reviewed consumers, checks the six-file candidate-model set, and
rejects automatic project integration.

The P11.4F boundary preserves its single ownership file and recognizes only the
visibility and outcome modules as reviewed consumers.

The P11.4G boundary preserves the visibility module as its sole ownership file
and recognizes only the outcome module as its P11.4H successor.

Frozen P11.4D, P11.4E, P11.4F, and P11.4G documentation is unchanged.

## Explicit non-goals

P11.4H does not add or change:

- ApexForge, qualified-name, use-site, module, import, or export syntax;
- aliases, wildcard imports, re-exports, lexical scope, nesting, or traversal;
- candidate discovery, query matching, context, evidence, or visibility policy;
- accessibility, ranking, precedence, scores, weights, fallback, or selection;
- candidate deduplication, unresolved reasons, inaccessible outcomes, or hidden
  candidate reporting;
- diagnostics, resolution source spans, or serialization;
- AIR, artifact v1, manifests, compiler, linker, validator, or entry behavior;
- runtime, CLI, LSP, VS Code, or Visual Studio behavior;
- generic closure or lowering.

## Acceptance evidence

The P11.4H smoke test proves the exact one-function API, no new records or public
aliases, exact input validation, mandatory operation reuse and call counts, exact
object preservation, no direct outcome construction, zero/one/multiple
classification, raw ambiguity reduction, canonical order, duplicate-visible
ambiguity, query-mode reuse, frozen outcome fields, successful-build explicit
usage, duplicate-link and generic boundaries, AIR and artifact invariance,
CLI/runtime/tooling compatibility, exact ownership, no diagnostics, no network
access, isolated fixtures, and Git/bytecode preservation.

The unchanged official harness remains the full regression authority.

## Next roadmap milestone

The next roadmap milestone is:

```text
P11.5
```

P11.4H does not define, implement, or begin P11.5.
