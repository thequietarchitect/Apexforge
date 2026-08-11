# P11.6K - Canonical Narrative Prose Model

## Scope and authority

P11.6K is the smallest deterministic extension above the frozen P11.6J
predecessor at `a1683ce4f3e1fc16d8da0411fc516dd16478aef6` and tag
`afp-p11.6j-freeze`. It adds passive authored prose to the immutable narrative
source, semantic model, canonical artifact/material, and J presentation path.

The authority chain is unchanged:

```text
authored prose
  -> immutable canonical narrative model
  -> canonical artifact and session material
  -> P11.6J deterministic rendering
  -> P11.6I explicit human interaction
  -> P11.6H lifecycle and persistence
  -> P11.6G one-shot routing
  -> P11.6E diagnostics
  -> P11.6D transition semantics
```

K does not evaluate, rank, choose, transition, terminate, persist a session,
or infer an outcome.

## Model and source contract

`NarrativeScene` remains frozen and now has `title: Optional[str]` and
`body: Optional[str]`. `NarrativeDialogue` retains its exact dialogue, scene,
speaker, and participant identities and adds `text: Optional[str]`. Identity
and prose are independent values. All records remain frozen dataclasses.

The dedicated opt-in narrative syntax reuses its single existing quoted string
tokenization:

```text
scene Start {
    title "An optional title"
    body "An optional body\nwith another line"
}

dialogue Greeting {
    scene Start
    speaker Guide
    participants [Guide, Hero]
    text "Exact optional dialogue text"
}
```

Historical bare `scene Name` declarations and dialogue blocks without `text`
remain valid. Scene fields are optional in fixed `title`, then `body` order.
Dialogue `text`, when present, follows `participants`. No generic ApexForge
grammar, compiler, AIR, CLI, manifest, or editor grammar changes are made;
the existing opt-in narrative parser/lowering pipeline owns this syntax.

## Absence and canonical text

`None` is the only absence representation. Present prose must be a nonempty
exact `str`; empty strings are rejected so they cannot become a second form of
absence. Leading and trailing whitespace is authored content and is preserved.
Spaces, tabs, punctuation, quotes, backslashes, Unicode, and embedded LF are
preserved without trimming, locale handling, rewriting, or Unicode
normalization. The existing escapes `\"`, `\\`, `\n`, and `\t` supply quoted
characters, backslashes, LF, and tab. CR is rejected for prose, including the
existing `\r` escape, so canonical embedded newlines are LF. Text must be
UTF-8 encodable; no BOM or platform newline conversion is introduced by the
canonical JSON serializer.

## Artifact propagation and versioning

The writer uses `apexforge.narrative-build-artifact/v2`. Each serialized scene
has exact `identity`, `title`, and `body` members; each dialogue retains its
structural members and has exact `text`. Explicit JSON `null` is the canonical
absence representation. P11.6K loaders continue accepting strict historical
v1 records, projecting their omitted prose as `None`. No session schema or
top-level build-artifact schema changes.

The existing UTF-8, sorted-key, LF-terminated canonical JSON serializer owns
the bytes. Consequently, repeated equivalent content has identical bytes and
SHA-256. Because prose is complete authored artifact content, changing only
title, body, or dialogue text changes canonical artifact bytes and the outer
build-artifact SHA-256 while story, scene, dialogue, choice, and path identities
remain unchanged.

`NarrativeSessionMaterial` retains immutable `scene_records` and `dialogues`
loaded from the associated artifact in addition to its frozen semantic identity
inventory and executable bindings. J therefore renders without reopening a
source file, scanning a project, or invoking parsing, lowering, compilation,
or runtime execution. Mutable P11.6H session state does not contain or serialize
title, body, or dialogue text; sessions retain only their artifact fingerprint,
story, and immutable execution state.

## Rendering and compatibility

When present, J adds prose after the transition count and before facts:

```text
Title:
<exact title>
Body:
<exact body>
Dialogue:
  dialogue:<identity path>
    Speaker: character:<identity path>
    Text:
<exact dialogue text>
```

Only dialogue records whose exact `scene` equals the current session scene and
whose `text` is present are rendered. They are sorted by `(dialogue identity
kind, dialogue identity path)`. Speaker identity is displayed exactly; no
display name or quotation marks are stored or inferred. Participants remain
structural metadata. Absent prose emits no prose headings, so historical
no-prose P11.6J rendering bytes remain unchanged.

## Semantic isolation

Prose does not enter bindings or P11.6D/E/G/H inputs. It cannot affect condition
evaluation, consequence application, choice/path matching, path indices,
destination resolution, transition legality, state facts, progression, choice
history, termination, diagnostics, or persistence ordering. Strings resembling
`${fact}`, `if (...)`, `invoke Main`, `terminate`, or choice identities remain
literal text. There is no interpolation, expression parser, template engine,
macro expansion, executable markup, dialogue selection, fallback generation,
randomness, AI/LLM integration, recommendation, procedural narration, speaker
simulation, character state machine, or autonomous character behavior.

## Ownership boundary

K owns only:

- `apexforge/language/narrative_model.py`
- `apexforge/language/narrative_source.py`
- `apexforge/language/narrative_parser.py`
- `apexforge/language/narrative_lowering.py`
- `apexforge/tooling/narrative_artifact.py`
- `apexforge/tooling/narrative_execution.py`
- `apexforge/tooling/narrative_session.py`
- `apexforge/tooling/narrative_rendering.py`
- `apexforge/tooling/__init__.py`
- `apexforge/p11_6k_canonical_narrative_prose_model_smoke_test.py`
- `docs/p11/P11_6K_CANONICAL_NARRATIVE_PROSE_MODEL.md`

## Deferred work

Deferred beyond K: interpolation, variables in prose, templating, localization,
pluralization, markup/rich text/style spans, portraits, emotions, voice/audio,
dynamic dialogue, branching conversation subsystems, AI characters, NPC
simulation, procedural or recommended text, runtime descriptions, character
memory, separate conversation history, and editor, GUI, TUI, or web UI work.
