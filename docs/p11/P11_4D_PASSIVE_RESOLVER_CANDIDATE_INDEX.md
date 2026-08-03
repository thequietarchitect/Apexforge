# P11.4D Passive Resolver Candidate Index

## Scope and frozen baseline

P11.4D adds passive metadata for declarations that have already crossed the
existing successful-project-build boundary. It does not add a resolver and it
does not change the meaning of any ApexForge program.

The controlling baseline is P11.4C at commit
`cdbff8de0b3df95c1b9cc2ee2d440d147252ddaf`, frozen by the annotated tag
`afp-p11.4c-freeze`. P11.4A remains the controlling identity and nesting
architecture audit, P11.4B remains the declared-identity metadata contract,
and P11.4C remains the resolver and qualification architecture audit.

This stage is metadata-only. It records factual candidate inputs that a later
resolver may consume, but it performs no use-site lookup, visibility analysis,
binding, ambiguity classification, semantic ranking, or winner selection.

## Public immutable records

The public model is defined in `language.resolution_candidates` by three
ordinary frozen dataclasses.

```text
ProjectQualification(
    kind: str,
    module_segments: tuple[str, ...],
    declaration_path: tuple[str, ...],
    legacy: bool,
)

ProjectResolutionCandidate(
    identity: ProjectDeclaredIdentity,
    owner: ProjectDeclarationOwner,
    qualification: ProjectQualification,
)

ProjectResolutionCandidateIndex(
    candidates: tuple[ProjectResolutionCandidate, ...] = (),
)
```

All three records are immutable. Sequence inputs are normalized to tuples, and
the index stores a canonical tuple. The candidate retains the exact P11.4B
`ProjectDeclaredIdentity` and P11.3D `ProjectDeclarationOwner` objects; it does
not copy their fields into a third parallel identity record.

The new module exports these three names directly. No re-export was added to
`language.__init__`.

## Qualification representation

`ProjectQualification` is a structured metadata value, not a qualified source
string. P11.4D neither creates nor accepts a dotted or otherwise delimited
source-level lookup name.

The present qualification rules are exact:

- `kind` is either `directive` or `function`;
- `declaration_path` contains exactly one ApexForge identifier;
- that one segment equals the candidate identity's exact `declared_name`;
- spelling and case are preserved;
- no Unicode normalization or case folding participates in semantic equality.

A legacy declaration has all of the following facts:

```text
legacy = True
module_segments = ()
owner.module_name is None
identity.module_name is None
```

A module-owned declaration has all of the following facts:

```text
legacy = False
module_segments = tuple(owner.module_name.split("."))
owner.module_name == identity.module_name
module_segments contains no empty segment
```

`qualified_display_name` remains a non-resolving P11.4B display projection. It
is not consulted when constructing qualification, comparing qualifications,
or filtering candidates.

## Candidate fact agreement

A `ProjectResolutionCandidate` is valid only when its existing identity and
owner records agree on every declaration fact:

- declaration kind;
- current AIR ID and owner AIR ID;
- physical source name;
- module name, including exact `None` for legacy ownership;
- declaration span.

Its qualification must then agree with both records. Candidate construction
rejects a mismatched kind, AIR ID, source, module, span, declaration path,
module path, or legacy discriminator. This consistency check emits no compiler
diagnostic; malformed direct model construction raises a normal model
validation exception.

## Candidate-index construction

`ProjectBuilder` first preserves the existing sequence:

1. normalize sources;
2. analyze modules and build the document graph;
3. compile source units;
4. collect the existing ownership and identity metadata;
5. validate module visibility;
6. link AIR programs;
7. validate the linked program;
8. select the existing optional entry directive.

Only after these steps succeed does it pair each P11.4B identity with its exact
P11.3D owner and construct the candidate index. `ProjectBuild` receives exactly
one candidate per successful declared identity.

The index is appended to `ProjectBuild` as:

```text
resolution_candidate_index: ProjectResolutionCandidateIndex
```

It has an empty default and `compare=False`, preserving prior positional
construction and equality behavior. A custom compiler that supplies no
declaration source-map metadata receives empty ownership, identity, and
candidate indexes rather than fabricated facts.

Failed builds expose no `ProjectBuild`, so they expose no candidate index.
P11.4D does not add a partial-build result.

## Canonical deterministic ordering

The index sorts candidates by the following complete key:

1. exact kind;
2. explicit legacy/module discriminator, with legacy facts first;
3. exact `module_segments` tuple;
4. exact `declaration_path` tuple;
5. physical source name case-folded;
6. physical source name exact;
7. declaration-span start offset;
8. declaration-span end offset;
9. current AIR ID as the final compatibility tie-breaker.

This is evidence ordering only. Earlier position never means greater semantic
priority, stronger visibility, accessibility, precedence, or selection.

## Factual all-match filters

The index exposes only minimal read-only inspection:

- exact kind plus declared-name filtering;
- exact current-AIR-ID filtering;
- exact structured-qualification filtering.

Each filter returns a tuple containing every matching candidate in canonical
order. Matching is exact-case. A missing value returns an empty tuple. No
filter collapses a result to one candidate or treats the first item as a
semantic winner.

## Duplicate retention and collision boundary

The public index constructor deliberately retains duplicate candidate records.
This establishes that the passive representation is structurally capable of
carrying duplicate evidence in a future stage.

Duplicate retention does not implement ambiguity. It creates no ambiguity
object, diagnostic, precedence rule, or resolution outcome.

Ordinary project construction retains the existing linker boundary. Same-kind
duplicate declarations, including same-kind declarations in different
modules, still fail during linking with `APX-LINK-001`. Because those builds do
not succeed, they do not expose a candidate index. Same-name cross-kind
directive and function declarations retain their existing legal coexistence
and appear as separate candidate facts.

## Compatibility results

P11.4D leaves all executable and serialized contracts unchanged:

- entry lookup remains flat and unqualified;
- AIR declaration names and IDs are unchanged;
- candidate inspection does not mutate AIR;
- generic declarations appear as ordinary function candidates;
- canonical specialization keys and lowered synthetic IDs remain excluded;
- specialization closure and deterministic lowering are unchanged;
- artifact v1 bytes, schema, and fingerprints omit candidate metadata;
- CLI version, check, run, and build behavior and output remain unchanged;
- runtime lookup, authority resources, state, events, and traces are unchanged;
- LSP definition, references, rename, hover, completion, symbols, formatting,
  and diagnostics retain their frozen behavior;
- VS Code packaging and language-server integration remain unchanged;
- Visual Studio bridge, diagnostics, intelligence, commands, and packaging
  fingerprints remain unchanged.

P11.4D emits no `APX-RESOLVE-*` diagnostic and adds no diagnostic stage.

## Exact production boundary

Only two production files participate in P11.4D:

```text
apexforge/language/resolution_candidates.py
apexforge/language/project.py
```

The first owns the passive model. The second constructs it after successful
build completion and stores it on `ProjectBuild`. No compiler, linker,
validator, runtime, artifact, manifest, CLI, language-server, VS Code, or
Visual Studio production file consumes the candidate index.

## Historical-test alignments

Two published smoke tests received narrow successor-stage alignments.

The P11.4B smoke test previously required `identity_index` to be the final
`ProjectBuild` field. It now verifies the actual P11.4B invariant: the existing
positional fields remain unchanged, and `document_graph`,
`declaration_ownership`, and `identity_index` remain consecutive and ordered,
with `identity_index.compare` still false. It does not test the P11.4D field.

The P11.4C smoke test retains its complete forbidden-marker scan. An exact
per-file marker allowlist permits only the P11.4D names in
`language.resolution_candidates` and their construction in `language.project`.
All other files and all unlisted forbidden markers continue to fail the audit.
The test therefore records the two-file successor production boundary without
authorizing a resolver or any downstream consumer.

Neither alignment changes production behavior or weakens the frozen P11.4B or
P11.4C architectural invariant it was designed to prove.

## Explicit non-goals

P11.4D does not implement or decide:

- name resolution or use-site lookup;
- resolved bindings;
- candidate selection or a winner;
- semantic ranking or precedence;
- visibility or accessibility;
- import-path or visibility-origin evidence;
- ambiguity sets or ambiguity diagnostics;
- unresolved, inaccessible, incorrect-kind, or qualification diagnostics;
- source qualification syntax or parsing;
- aliases;
- nested declaration syntax or lexical traversal;
- extend or converge semantics;
- generic-owner candidate fields;
- generic specialization candidates;
- entry qualification or entry migration;
- AIR, manifest, artifact, CLI, runtime, or tooling schema changes.

The terms `candidate` and `canonical order` in this stage describe passive
facts and deterministic evidence presentation only.

## Acceptance evidence

The P11.4D smoke test proves:

- exact frozen public dataclass fields;
- qualification and fact-consistency rejection;
- legacy and module-owned construction;
- one-to-one identity/owner/candidate correspondence;
- cross-kind separation;
- the complete deterministic ordering key under shuffled input;
- all-match tuple filters;
- duplicate retention without selection;
- unchanged link failures and entries;
- generic declaration inclusion and synthetic-ID exclusion;
- byte-identical AIR and artifact v1 behavior;
- unchanged CLI, runtime, LSP, VS Code, and Visual Studio contracts;
- the exact two-file production boundary;
- blocked network access, external temporary fixtures, working-directory
  preservation, Git-status preservation, and bytecode-state preservation.

The focused P11.4D, P11.4C, P11.4B, and P11.4A tests must pass before the
complete official harness. With the new smoke test, expected discovery is 92
tests.

## Next proposed stage

The next proposed stage is:

```text
P11.4E Structured Resolution Query and Binding Contract
```

That stage may define a structured use-site query and resolved-binding result
against the passive candidates, subject to a separate reviewed contract. It
must decide unresolved policy questions before adding semantic selection.
P11.4D does not implement or begin P11.4E.
