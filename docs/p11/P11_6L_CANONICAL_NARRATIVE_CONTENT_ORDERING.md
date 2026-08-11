# P11.6L - Canonical Narrative Content Ordering

## Scope and authority

P11.6L is the smallest deterministic successor to frozen P11.6K commit
`628022283b75ee97d4545bc8324da968e7fab68f` and tag
`afp-p11.6k-freeze`. It answers one presentation-only question: in what order
are multiple authored dialogue records for the current scene shown to a human?

The authority chain is:

```text
authored source order
  -> canonical narrative content order
  -> canonical artifact and session material
  -> deterministic P11.6J/K presentation
  -> P11.6I explicit human choice
  -> P11.6H lifecycle
  -> P11.6G/E/D execution
```

Content position is passive presentation data. It is not execution authority,
priority, semantic rank, or an input to path selection.

## Discovery result and canonical rule

The existing pipeline already preserves authored dialogue declaration order:

1. `NarrativeSourceStory.dialogues` is an immutable tuple.
2. The dedicated narrative parser appends each dialogue as encountered and
   constructs that tuple without sorting.
3. Lowering iterates the source tuple directly into
   `NarrativeStory.dialogues` without sorting.
4. Artifact v2 projects the semantic tuple directly into the JSON `dialogues`
   array, whose array order is canonical content.
5. The artifact loader visits that JSON array in order and constructs the
   immutable `NarrativeSessionMaterial.dialogues` tuple in the same order.

No sorting before the J/K presentation boundary destroys that order. K alone
re-sorted current-scene dialogue by identity during presentation. L removes
that identity sort. The canonical rule is therefore: filter the material tuple
to records whose exact structural scene identity equals the current session
scene and whose canonical text is present, preserving the relative order of
all surviving records.

For authored order `Start/Zeta`, `End/Elsewhere`, `Start/Alpha`, presentation
of `Start` is `Zeta`, then `Alpha`. Scene proximity never establishes
membership; exact structural scene identity does.

## Representation and fingerprinting

No `order`, `ordinal`, `sequence`, `priority`, `weight`, or `rank` field is
introduced. There is no model, source AST, parser, lowering, grammar, AIR,
compiler, artifact loader, session-material, public API, or manifest change.
The existing array/tuple position is sufficient and is now canonized as
authored presentation order.

The narrative artifact schema remains
`apexforge.narrative-build-artifact/v2`; v1 and v2 loading remain supported.
Because JSON array order is canonical authored content, identical source order
produces identical artifact bytes and SHA-256, while reordering dialogue
declarations changes those bytes and the fingerprint. Reordering does not
change story, scene, dialogue, character, choice, or path identities.

## Rendering and compatibility

P11.6J/K fixed positions remain:

```text
session header and state
optional scene title
optional scene body
authored current-scene dialogue sequence
facts
choices
```

Each rendered dialogue retains exact authored text, speaker identity, UTF-8,
LF, tabs, and leading/trailing whitespace. L performs no grouping, rewriting,
speaker sort, identity sort, text sort, summarization, or inferred ranking.
With no dialogue prose, no prose heading is emitted and historical no-prose J
rendering bytes remain unchanged.

## Semantic and interaction isolation

Dialogue tuple position does not enter executable bindings or P11.6D/E/G/H
inputs. Reordering passive dialogue cannot affect conditions, consequences,
destination resolution, transition legality, facts, progression, choice
history, termination, diagnostics, or persistence. Session serialization does
not duplicate prose or ordering state; sessions continue to retain artifact
association, story identity, and execution state.

P11.6I choice menus remain independently sorted by the frozen canonical
choice-identity/path-index rule. Choice numbering, path indices, labels,
destinations, and explicit human selection mapping are unchanged.

Determinism depends only on the authored tuple/array sequence. It has no hash,
set, filesystem-enumeration, locale, environment, clock, randomness, process,
thread, network, recommendation, scoring, AI, or LLM dependency.

## Exact ownership

P11.6L owns exactly:

- `apexforge/tooling/narrative_rendering.py`
- `apexforge/p11_6l_canonical_narrative_content_ordering_smoke_test.py`
- `docs/p11/P11_6L_CANONICAL_NARRATIVE_CONTENT_ORDERING.md`

## Deferred work

L does not add branching, choice-bearing, conditional, priority, or timed
dialogue; runtime-driven speaker turns; content groups; cutscenes; executable
content nodes; mixed-content ASTs; localization; templates; interpolation;
rich text; audio; portraits; emotions; character simulation; procedural or AI
narration; or editor GUI work.
