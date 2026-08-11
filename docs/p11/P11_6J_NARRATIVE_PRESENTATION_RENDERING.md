# P11.6J — Narrative Presentation and Rendering

## Scope and authority

P11.6J is the smallest deterministic human-facing rendering layer above the
frozen P11.6I interaction shell at annotated tag `afp-p11.6i-freeze`, commit
`a2c5f8b1ce3f5e9f50632a8a7cdfd3a311e51587`. It projects canonical structural
narrative material plus one immutable P11.6H session into presentation data
and stable text. It does not interpret narrative meaning or own input,
transition, termination, persistence, or lifecycle behavior.

The authority chain remains:

```text
canonical narrative material + immutable session
  -> P11.6J deterministic presentation/rendering
  -> P11.6I human input and exact menu mapping
  -> P11.6H session lifecycle and atomic persistence
  -> P11.6G one-shot execution routing
  -> P11.6E diagnostics and explicit termination
  -> P11.6D transition authority
```

## Public rendering API

`tooling.narrative_rendering` exports:

- `narrative_session_presentation(material, session)` for the immutable
  structured projection;
- `render_narrative_presentation(presentation)` for stable text formatting;
- `render_narrative_session(material, session)` as the composed convenience
  API;
- frozen `NarrativeSessionPresentation`, `NarrativeFactPresentation`, and
  `NarrativeChoicePresentation` records.

The projection fails closed on wrong exact input types, artifact-fingerprint
mismatch, story mismatch, or a current scene absent from the associated
material. Rendering neither repairs nor substitutes invalid data.

## Deterministic projection and ordering

The model contains exact story and scene identities, termination status and
optional reason, successful transition count, normalized facts, and current
structural paths. It contains no clock, locale, terminal, environment,
filesystem, random, network, process, or user-derived data.

Facts are explicitly ordered by:

```text
(subject identity kind, subject identity path, fact name, fact value)
```

Only binding paths whose exact `source_scene` equals the current session scene
are projected. Active-session paths preserve P11.6I's frozen ordering:

```text
(choice identity kind, choice identity path, zero-based path index)
```

One-based menu numbers are assigned after that sort. Every entry retains the
exact choice identity and zero-based path index, exact canonical path label,
and exact destination scene identity. P11.6I converts those displayed records
to its existing `NarrativeSessionStepRequest` objects; J never parses or
consumes the user's selection.

## Exact text format

Text uses literal LF delimiters, always ends in one LF, and has no ANSI or
width-sensitive formatting:

```text
ApexForge narrative session
Story: <identity>
Scene: <identity>
Status: <active-or-terminated>
Termination reason: <reason>       # present only when canonical state has one
Transitions: <choice-history-count>
Facts:
  <subject-identity>:<name>=<value> # or (none)
Choices:
  <number>. <choice-identity> path[<index>] <JSON string label> -> <scene>
```

A terminated presentation uses `Choices:` followed by
`(session terminated)`. An active scene with no structural paths uses
`(none)`. Neither shape implies or performs termination.

Identity text is the exact kind, a colon, and the canonical path segments
joined by `/`. Choice labels use deterministic JSON string escaping with
Unicode preserved. Fact names and values are reproduced without
interpretation.

## Canonical text and absent fields

At this frozen artifact/session boundary, `NarrativeScene` carries only an
identity. `NarrativeDialogue` carries identities for itself, its scene,
speaker, and participants, but no dialogue text. `NarrativeSessionMaterial`
does not carry scene titles, bodies, descriptions, or dialogue records.

The sole available presentation prose is the exact canonical choice-path
label already present in executable structural binding material. J renders
that label exactly. It does not invent scene titles, descriptions, dialogue,
speaker text, emotion, meaning, destination narration, recommendations, or
any other prose. Richer prose requires a later, explicitly versioned schema
slice and is not inferred here.

## No semantic evaluation

Structural visibility is exact current-scene membership only. J never reads a
path condition or consequence, tests satisfiability, ranks paths, marks them
allowed or blocked, previews effects, selects a fallback, infers termination,
or calls P11.6D. A condition-unsatisfied path remains visible; after explicit
selection, the frozen H/G/E/D authority chain alone decides legality and
returns diagnostics.

## P11.6I/J responsibility split

J creates and formats the immutable current-state presentation. I retains the
injected streams, prompt, complete input grammar, invalid-input retry,
one-based selection lookup, exact choice/path request, H step and termination
delegation, semantic-failure reporting, atomic H persistence ordering,
quit/EOF behavior, and loop exit rules.

On successful H step or termination, I persists the immutable returned session
before J renders it. On semantic failure, J has no fallback behavior. For an
already-terminated session, J renders the received state and I exits without
consuming input or retrying termination.

## Compatibility and exclusions

`apexforge narrative-session interact BUILD SESSION` and all historical
arguments, exit codes, prompts, messages, and rendered state/menu bytes remain
compatible. `tooling/cli.py`, manifests, artifact schemas, grammar, compiler,
AIR, runtime, language-server/editor integrations, and protected fixtures are
unchanged.

J performs no input, output-stream ownership, file read/write, atomic session
write, transition, termination, condition evaluation, consequence application,
AIR execution, autonomous selection, threading, subprocess, timer, network,
environment, terminal-width, or filesystem operation.

Deferred work includes new prose schema fields, character simulation, AI or
autonomous dialogue, recommendations and previews, procedural narration,
localization, styling/themes/ANSI, TUI/GUI/web/editor UI, save slots,
campaigns, rewind/checkpoints, multiplayer/networking, voice/audio, animation,
timers, and background processing.
