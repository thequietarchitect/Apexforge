# P11.4G Visibility Policy and Contextual Candidate Filtering Contract

## Scope and frozen baseline

P11.4G defines one fixed visibility policy over the passive factual evidence
frozen by P11.4F. It also provides an explicit operation that retains every
query-matching candidate visible under that policy.

The controlling baseline is:

- branch: `p11.4-identity-nesting`;
- P11.4F commit: `866c3fe7001f3dc0748c209cd31a0c67c9721599`;
- annotated freeze: `afp-p11.4f-freeze`;
- tag object: `9a0dff150fa07bf7f8d996b473204bddf87cd95f`.

The P11.4F freeze and every earlier freeze remain immutable. P11.4G changes
neither P11.4D candidates, P11.4E query matching, nor P11.4F evidence derivation.

## Fixed non-configurable policy

P11.4G answers only which fixed visibility bases apply to one valid evidence
record and which matching candidates remain after that policy is applied. It has
no configuration switches, weights, scores, priorities, or fallback order.

The stage does not choose among visible candidates. It does not classify a
filtered tuple as unresolved, resolved, or ambiguous, and it creates no binding
or diagnostic.

## Sole production module

P11.4G has exactly one production file:

```text
apexforge/language/resolution_visibility.py
```

Nothing is re-exported through `language.__init__`. The exact public exports are:

```python
__all__ = (
    "ProjectVisibilityDecision",
    "evaluate_project_visibility",
    "filter_project_visible_candidates",
)
```

There is no resolver class, configurable policy class, accessibility policy,
scope graph, module registry, mutable state, cache, ranking mechanism, alias,
dynamic export, or runtime class renaming.

## Public immutable decision

```python
@dataclass(frozen=True)
class ProjectVisibilityDecision:
    evidence: ProjectVisibilityEvidence
    visible: bool
    visibility_basis: tuple[str, ...]
```

The decision retains the exact P11.4F evidence object. It does not reconstruct
the query, context, candidate, or evidence facts. `visible` is an actual `bool`.
`visibility_basis` is an immutable normalized tuple containing every and only
applicable basis token.

The decision has no field named `accessible`, `selected`, `winner`, `rank`,
`priority`, `precedence`, `score`, or `weight`.

## Frozen basis vocabulary

The complete basis vocabulary is:

```text
same_source
same_module
imported_module
legacy_context
```

The canonical presentation order is exactly:

```python
(
    "same_source",
    "same_module",
    "imported_module",
    "legacy_context",
)
```

Only applicable tokens are retained. The canonical order is private production
data and is not exposed as a public constant. It is deterministic presentation
only and creates no ranking, precedence, fallback, or winner selection.

## Same-source visibility

The `same_source` basis is included exactly when `evidence.same_source` is true.
P11.4G does not reinterpret the P11.4F source fact, so exact source-name spelling
and case remain authoritative without filesystem normalization. This basis
applies to legacy and module-owned candidates.

## Same-module visibility

The `same_module` basis is included exactly when `evidence.same_module` is true.
The P11.4F fact already requires a non-empty context module, a non-legacy
candidate, and exact module-segment equality. P11.4G does not broaden it.

## Imported-module visibility

The `imported_module` basis is included exactly when
`evidence.imported_module` is true. Duplicate import facts still yield one
Boolean fact and therefore one token.

P11.4G does not inspect document graphs, expand aliases, infer imports, follow
re-exports, or inspect the filesystem.

## Legacy-context visibility

The `legacy_context` basis is included exactly when both facts hold:

```python
evidence.legacy_candidate
evidence.context.module_segments == ()
```

This makes a legacy/headerless candidate visible from a legacy/headerless use
site. It does not make legacy declarations globally visible from module-owned
contexts. A remote legacy candidate in a module context has no `legacy_context`
basis and is visible only when another basis applies, such as exact same source.

The exact legacy query mode does not itself grant visibility. Query matching and
visibility policy remain separate operations.

## Overlapping bases

Every applicable basis is retained. Evidence with same-source, same-module, and
imported-module facts produces:

```python
(
    "same_source",
    "same_module",
    "imported_module",
)
```

A same-source legacy candidate in a legacy context may produce:

```python
(
    "same_source",
    "legacy_context",
)
```

Neither example creates ranking or precedence. No token suppresses another.

## Final visibility value

Visibility is exactly:

```python
visible == bool(visibility_basis)
```

An unrelated record with no basis is not visible. Any record with one or more
valid bases is visible. There is no fallback rule.

## Exact decision validation

Direct construction validates that:

- `evidence` is exactly `ProjectVisibilityEvidence`;
- `visible` is an actual `bool`, not an integer substitute;
- a basis iterable normalizes to a tuple;
- strings and bytes are rejected as basis iterables;
- every item is an exact string in the frozen vocabulary;
- no token is duplicated;
- tokens use canonical presentation order;
- the tuple exactly equals the bases derived from the evidence;
- `visible` exactly equals `bool(visibility_basis)`.

A caller therefore cannot mark unrelated evidence visible, mark qualifying
evidence invisible, omit or add a basis, reorder or duplicate tokens, or invent
a token. Invalid direct construction raises `TypeError` or `ValueError`, not an
ApexForge diagnostic.

## Visibility evaluation

```python
def evaluate_project_visibility(
    evidence: ProjectVisibilityEvidence,
) -> ProjectVisibilityDecision:
    ...
```

The function requires exactly a P11.4F evidence record, derives every basis in
canonical order, derives visibility from the non-empty tuple, and returns a
validated immutable decision.

It does not mutate evidence, reconstruct metadata, call the filesystem, inspect
a graph, rank bases, select a candidate, or emit a diagnostic.

## Explicit contextual filtering

```python
def filter_project_visible_candidates(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> tuple[ProjectResolutionCandidate, ...]:
    ...
```

The function validates its arguments and invokes the frozen P11.4F evidence
collector. Every evidence record is evaluated under the fixed policy. Its
candidate is retained exactly when the decision is visible.

The result rules are:

```text
zero query matches          -> ()
matches but zero visible    -> ()
one visible candidate       -> one-candidate tuple
multiple visible candidates -> all visible candidates
```

The result is always a tuple of `ProjectResolutionCandidate` objects.

## Ordering and duplicate retention

Filtering preserves the frozen P11.4D canonical candidate order by iterating the
P11.4F evidence tuple without reordering. Duplicate visible candidates remain
duplicate tuple elements. Invisible candidates are omitted without changing the
relative order of retained candidates.

Filtering never sorts by basis, prefers one basis, selects the first candidate,
or deduplicates candidates.

## Frozen query-mode reuse

P11.4G inherits P11.4E matching through the P11.4F collector.

- An unqualified query may initially match legacy and module-owned candidates;
  policy is then applied to every match.
- An exact legacy query initially matches only legacy candidates, which still
  require same-source or legacy-context evidence.
- An exact module query initially matches only that exact module, whose
  candidates still require same-source, same-module, or imported-module evidence.

Kind, declaration path, module segments, spelling, and case retain exact frozen
matching semantics.

## No outcome classification

Filtering may reduce a P11.4E ambiguous match set to zero, one, or multiple
visible candidates. These remain plain tuple lengths. P11.4G does not convert:

- an empty tuple to `ProjectUnresolvedResolution`;
- a one-candidate tuple to `ProjectResolvedBinding`;
- a multiple-candidate tuple to `ProjectAmbiguousResolution`.

A one-candidate tuple is not a winner or binding. No P11.4E outcome record or
resolution diagnostic is returned.

## Explicit-only successful-build usage

The function may be called explicitly after a successful build:

```python
visible_candidates = filter_project_visible_candidates(
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

No method is added to `ProjectBuild`, `ProjectBuilder`, the candidate index, the
query, context, evidence, or any P11.4E result record. No context, evidence,
decision, or filtered tuple is constructed automatically during parsing,
compilation, module analysis, linking, validation, entry resolution, artifact
construction, CLI operation, execution, or tooling.

## Duplicate and cross-kind boundaries

Same-kind duplicates continue to fail during linking with `APX-LINK-001`.
Failed builds expose no project, index, query result, context, evidence, decision,
or filtered tuple. Filtering cannot bypass the linker collision boundary.

Same-name declarations of different kinds remain legal and separate because the
frozen query requires an exact kind. Filtering never combines kinds.

## Generic boundary

A generic declaration participates only through its ordinary declared function
candidate. P11.4G creates no decisions or filtered candidates for specialization
keys, lowered synthetic functions, `__apx_spec__` IDs, instantiated type
arguments, or generic-owner records. Generic closure and lowering are unchanged.

## Compatibility invariants

Visibility evaluation and filtering are observational. They do not change:

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

P11.4G is owned by exactly:

```text
apexforge/language/resolution_visibility.py
```

P11.4F remains owned by `apexforge/language/resolution_context.py`, whose only
P11.4G successor consumer is the visibility module.

P11.4E remains owned by `apexforge/language/resolution_queries.py`; its reviewed
successors are the context and visibility modules.

P11.4D remains owned by exactly:

```text
apexforge/language/resolution_candidates.py
apexforge/language/project.py
```

Its reviewed successors are the query, context, and visibility modules. The
complete candidate-model production set is exactly these five files.

## Historical-test alignments

The P11.4C source guard retains its exact per-file, per-marker allowlist. It adds
only the `ResolutionCandidate` and `language.resolution` pairs required by the
new module. `ProjectResolver` and resolver diagnostics remain forbidden.

The P11.4D boundary preserves its two original ownership files and adds only the
visibility module to reviewed successor consumers.

The P11.4E boundary preserves its single ownership file, recognizes only the
context and visibility modules as successors, checks the exact five-file set,
and rejects automatic integration in `ProjectBuild` or `ProjectBuilder`.

The P11.4F boundary preserves the context module as its sole ownership file and
recognizes only the visibility module as its P11.4G successor. It retains exact
P11.4E and P11.4D ownership assertions.

Frozen P11.4D, P11.4E, and P11.4F documentation is unchanged.

## Explicit non-goals

P11.4G does not add or change:

- ApexForge, qualified-name, use-site, module, import, or export syntax;
- aliases, wildcard imports, re-exports, lexical scope, nesting, or traversal;
- configurable visibility or accessibility policy;
- ranking, precedence, scores, weights, fallback, or winner selection;
- binding creation or contextual outcome classification;
- resolver, unresolved, ambiguity, or inaccessible diagnostics;
- resolution spans or decision/context/evidence serialization;
- AIR, artifact v1, manifests, compiler, linker, validator, or entry behavior;
- runtime, CLI, LSP, VS Code, or Visual Studio behavior;
- generic closure or lowering.

## Acceptance evidence

The P11.4G smoke test proves the exact public model, fixed private vocabulary,
canonical order, every required basis derivation, overlap without precedence,
strict validation, evidence immutability, zero/one/many filtering, query-mode
reuse, canonical ordering, duplicates, no outcome classification, explicit
successful-build use, duplicate-link and generic boundaries, AIR and artifact
invariance, CLI/runtime/tooling compatibility, exact ownership, no diagnostics,
no network access, isolated fixtures, and Git/bytecode preservation.

The unchanged official harness remains the complete regression authority.

## Next proposed stage

The next proposed stage is:

```text
P11.4H  Contextual Resolution Outcome Classification Contract
```

P11.4G does not implement or begin P11.4H.
