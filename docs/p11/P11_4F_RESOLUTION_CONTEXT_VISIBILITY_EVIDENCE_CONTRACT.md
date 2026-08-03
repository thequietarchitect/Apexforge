# P11.4F Resolution Context and Visibility Evidence Contract

## Scope and frozen baseline

P11.4F adds a passive, explicit library contract for recording use-site context
and factual relationships between that context and candidates already matched by
the frozen P11.4E structured-query operation.

The controlling baseline is:

- branch: `p11.4-identity-nesting`;
- P11.4E commit: `4f0554cd020a5dc0f0a84afbeaac46b9814353cb`;
- annotated freeze: `afp-p11.4e-freeze`;
- tag object: `1474d53906da6e0a264dc1f101cf1203851cf530`.

The P11.4E freeze and all preceding freezes remain immutable. P11.4F does not
change the P11.4D candidate model or the P11.4E matching and outcome model.

## Passive factual-only purpose

The stage records caller-supplied context and derives four exact facts for each
candidate that already matches a structured query:

- whether the candidate has the same exact physical source name;
- whether a non-legacy candidate has the same exact non-empty module tuple;
- whether a non-legacy candidate's exact module tuple appears in the supplied
  imported-module facts;
- whether the candidate is legacy/headerless.

These facts are evidence, not policy. The contract does not determine whether a
candidate is visible or accessible, filter candidates, rank evidence, establish
precedence, choose a winner, or emit a diagnostic.

## Production boundary

P11.4F has exactly one production file:

```text
apexforge/language/resolution_context.py
```

It is an explicit library module. Nothing is re-exported through
`language.__init__`, and no project, compiler, runtime, CLI, artifact, or tooling
path invokes it automatically.

Its exact public exports are:

```python
__all__ = (
    "ProjectResolutionContext",
    "ProjectVisibilityEvidence",
    "collect_project_visibility_evidence",
)
```

There is no resolver class, policy class, scope graph, module registry, mutable
resolver state, cache, alias, dynamic export, or runtime class renaming.

## Public immutable records

### `ProjectResolutionContext`

```python
@dataclass(frozen=True)
class ProjectResolutionContext:
    source_name: str
    module_segments: tuple[str, ...]
    imported_modules: tuple[tuple[str, ...], ...] = ()
```

This record contains only facts explicitly supplied by its caller. It is not
derived from a document graph, source map, module analysis, import graph, entry,
compiler, runtime, or tooling request.

### `ProjectVisibilityEvidence`

```python
@dataclass(frozen=True)
class ProjectVisibilityEvidence:
    query: ProjectResolutionQuery
    context: ProjectResolutionContext
    candidate: ProjectResolutionCandidate
    same_source: bool
    same_module: bool
    imported_module: bool
    legacy_candidate: bool
```

The record retains the frozen P11.4E query and P11.4D candidate objects. It does
not copy their fields into a competing representation. Its four booleans must be
real `bool` values and must exactly equal the derived facts described below.

The record has no `visible`, `accessible`, `selected`, `winner`, `rank`,
`priority`, or `precedence` field.

## Resolution-context representation

### Source name

`source_name` is a non-empty string with no NUL character. Its spelling and case
are preserved exactly. P11.4F performs no path normalization, case folding,
filesystem lookup, or existence check.

The name is a factual physical-source identifier supplied by the caller.

### Legacy context

```python
module_segments == ()
```

The empty tuple represents a legacy/headerless use site. It does not imply that
legacy declarations are globally visible.

### Module-owned context

A non-empty tuple represents a module-owned use site:

```python
("App", "Main")
```

Every segment must be a valid ApexForge identifier. Strings and bytes are not
accepted as segment iterables. Empty segments, non-string segments, dotted
combined segments such as `"App.Main"`, and invalid identifiers are rejected.

P11.4F does not parse a dotted source string or add source-level module syntax.
Exact case and spelling are retained.

## Imported-module normalization

`imported_modules` normalizes to:

```python
tuple[tuple[str, ...], ...]
```

Every imported module path is non-empty and contains only valid ApexForge
identifier segments. The normalized module paths are sorted by exact tuple
ordering. Exact duplicates are retained.

For example:

```text
("Zeta",)
("Alpha", "Core")
("Zeta",)
```

normalizes to:

```text
(("Alpha", "Core"), ("Zeta",), ("Zeta",))
```

This ordering is deterministic evidence presentation only. Duplicate imports do
not create duplicate candidate evidence. P11.4F does not collapse imports,
expand aliases, resolve re-exports, inspect a graph or filesystem, infer implicit
imports, or reject an imported module equal to the current module.

## Exact evidence derivation

For a query-matching candidate, `same_source` is exactly:

```python
candidate.identity.source_name == context.source_name
```

No filesystem canonicalization participates. The frozen candidate invariant
already requires its identity and owner source names to agree.

`legacy_candidate` is exactly:

```python
candidate.qualification.legacy
```

It is a candidate fact and does not imply visibility.

`same_module` is true only when all of these facts hold:

- the context module tuple is non-empty;
- the candidate is not legacy;
- the candidate qualification's module tuple exactly equals the context module
  tuple.

Consequently, a legacy context never produces same-module evidence, and a
legacy candidate never has `same_module=True`.

`imported_module` is true only when:

- the candidate is not legacy; and
- its exact qualification module tuple occurs in `context.imported_modules`.

Membership is exact-case and exact-segment. Duplicate import facts do not
multiply evidence records.

`same_module` and `imported_module` may both be true when the caller explicitly
includes its current module in the imported-module facts. The overlap is retained
without rejection, ranking, or precedence.

## Candidate and query agreement

Every evidence record must contain exactly a `ProjectResolutionQuery`, a
`ProjectResolutionContext`, and a `ProjectResolutionCandidate`. The candidate
must match the query under the frozen P11.4E operation.

P11.4F reuses `resolve_project_query` for this check. It does not copy,
reinterpret, or weaken P11.4E matching rules. Therefore kind, declaration path,
and the three module-query modes retain their frozen exact-case behavior.

Direct evidence construction validates factual consistency only. It does not
claim that the candidate is visible, accessible, or unique in some external
index. Malformed direct construction raises `TypeError` or `ValueError`, not an
ApexForge diagnostic.

## Collection function

```python
def collect_project_visibility_evidence(
    index: ProjectResolutionCandidateIndex,
    query: ProjectResolutionQuery,
    context: ProjectResolutionContext,
) -> tuple[ProjectVisibilityEvidence, ...]:
    ...
```

The function validates its three arguments and invokes the frozen P11.4E query
operation. It flattens the outcome as follows:

```text
unresolved outcome -> no candidates -> ()
resolved binding   -> one candidate  -> one evidence record
ambiguous outcome  -> all candidates -> all evidence records
```

It returns one evidence record for every matching candidate. It preserves the
P11.4D canonical candidate order and retains duplicate candidate records as
duplicate evidence records.

The first ambiguous candidate is never treated as a winner. The function does
not collapse duplicates, rank evidence, filter by any evidence flag, convert
evidence to accessibility or visibility, return a resolved binding, or emit a
diagnostic.

## Explicit-only successful-build usage

The contract may be invoked explicitly after a successful project build:

```python
evidence = collect_project_visibility_evidence(
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
query, or any outcome record. No context is automatically constructed. No
evidence is collected during parsing, compilation, module analysis, linking,
validation, entry resolution, artifact construction, CLI operation, execution,
or tooling requests.

## Duplicate and cross-kind boundaries

Same-kind duplicate declarations continue to fail during linking with
`APX-LINK-001`. A failed build exposes no `ProjectBuild`, candidate index,
structured query result, context, or evidence. Evidence cannot bypass that
collision boundary.

Same-name directive and function declarations remain legal and separate because
the frozen query requires an exact declaration kind.

## Generic boundary

A generic declaration participates only through its ordinary declared function
candidate. P11.4F creates no context or evidence for specialization keys,
lowered synthetic functions, `__apx_spec__` IDs, instantiated type arguments,
or generic-owner records.

Generic closure collection, canonical specialization keys, lowered target IDs,
and lowering behavior remain unchanged.

## Compatibility invariants

Evidence collection is observational. Before and after explicit collection:

- AIR is byte-equivalent;
- artifact v1 bytes and fingerprints are unchanged;
- entry resolution is unchanged;
- compiler, linker, and validator behavior is unchanged;
- CLI version, check, run, and build behavior is unchanged;
- runtime state, events, traces, authority resources, and execution are
  unchanged;
- LSP behavior is unchanged;
- VS Code behavior is unchanged;
- Visual Studio behavior is unchanged;
- no `APX-RESOLVE-*` diagnostic exists.

## Ownership and successor boundaries

P11.4D remains owned by exactly:

```text
apexforge/language/resolution_candidates.py
apexforge/language/project.py
```

Its reviewed successor consumers are:

```text
apexforge/language/resolution_queries.py
apexforge/language/resolution_context.py
```

P11.4E remains owned by exactly:

```text
apexforge/language/resolution_queries.py
```

Its only P11.4F successor consumer is:

```text
apexforge/language/resolution_context.py
```

The complete candidate-model production set is exactly the two P11.4D owners
plus those two reviewed successor consumers. P11.4F does not modify
`language.project`, `language.resolution_candidates`, or
`language.resolution_queries`.

## Historical-test alignments

The P11.4C source guard retains its exact per-path, per-marker allowlist. It adds
only the marker pairs necessarily present in
`apexforge/language/resolution_context.py`; the file remains fully scanned, and
all unapproved markers remain forbidden.

The P11.4D boundary check continues to distinguish its two original ownership
files from reviewed successor consumers. It recognizes only the frozen P11.4E
query module and the new P11.4F context module.

The P11.4E boundary check continues to identify its single ownership file and
now recognizes only the P11.4F context module as its successor consumer. It also
checks the exact four-file candidate-model set and rejects automatic integration
in `ProjectBuild` or `ProjectBuilder`.

No frozen P11.4D or P11.4E documentation is modified.

## Explicit non-goals

P11.4F does not add or change:

- ApexForge, qualified-name, use-site, module, import, or export syntax;
- aliases, wildcard imports, re-export behavior, lexical scope, nested
  declarations, or scope traversal;
- visibility policy or accessibility policy;
- candidate filtering, ranking, precedence, fallback, or winner selection;
- resolver, unresolved, ambiguity, or inaccessible diagnostics;
- resolution source spans;
- binding, context, or evidence serialization;
- AIR, artifact v1, manifests, compiler output, linker behavior, validator
  behavior, or entry resolution;
- runtime, CLI, LSP, VS Code, or Visual Studio behavior;
- generic closure or lowering.

The terms “visibility evidence” describe factual inputs for a future policy;
they do not claim visibility.

## Acceptance evidence

The P11.4F smoke test proves the exact public model, context validation,
deterministic imported-module normalization, duplicate retention, all four flag
derivations, frozen query-mode reuse, zero/unique/ambiguous flattening, canonical
order, direct validation, no policy fields, explicit successful-build use,
duplicate-link and generic boundaries, AIR and artifact invariance, compatibility
with CLI/runtime/tooling, exact production ownership, no diagnostics, no network
access, external temporary fixtures, and preservation of working directory, Git
status, and repository bytecode state.

The unchanged official harness remains the full regression authority.

## Next proposed stage

The next proposed stage is:

```text
P11.4G  Visibility Policy and Contextual Candidate Filtering Contract
```

P11.4F does not implement or begin P11.4G.
