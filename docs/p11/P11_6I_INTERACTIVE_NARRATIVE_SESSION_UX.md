# P11.6I — Interactive Narrative Session UX

## Scope and authority

P11.6I adds the smallest deterministic human-driven shell above the frozen
P11.6H session lifecycle at annotated tag `afp-p11.6h-freeze`, commit
`c3557f817bf4c46d579d4dfc2498e620c7967e0a`.

The shell loads one existing canonical build artifact and one existing P11.6H
session. It does not create sessions, infer starting scenes, execute AIR,
evaluate narrative conditions, apply consequences, select choices or paths,
infer termination, or implement persistence. The authority chain remains:

```text
human menu selection
  -> P11.6I exact menu mapping
  -> P11.6H session lifecycle
  -> P11.6G one-shot routing
  -> P11.6E diagnostics and termination
  -> P11.6D transition authority
```

## Command and input grammar

The added command is:

```text
apexforge narrative-session interact BUILD SESSION
```

`SESSION` is both the session loaded at entry and the file atomically replaced
after each successful P11.6H operation. The core function accepts injected
text input and output streams, so it has no dependency on a terminal, ANSI
support, console width, timing, or global `input()`/`print()`.

At each active prompt, the complete input grammar is:

- a positive ASCII decimal menu number: request exactly that displayed path;
- `terminate`: explicitly request the frozen P11.6E `explicit_outcome`
  termination through P11.6H;
- `quit`: close the shell without changing narrative termination;
- EOF: close the shell without changing narrative termination.

Input is trimmed but is not fuzzy-matched. Blank input, aliases, non-ASCII
numbers, non-numeric text, zero, negative values, and out-of-range numbers are
rejected with a deterministic message. They perform no lifecycle call and no
write. There is no default menu entry.

## Deterministic presentation and mapping

Each presentation shows the exact story identity, current scene identity,
termination status and reason when present, transition count, and normalized
facts. Active sessions then show only executable binding paths whose structural
`source_scene` equals the current session scene.

Paths are explicitly sorted by the tuple:

```text
(choice identity kind, choice identity path, path index)
```

Menu numbering begins at one after that sort. Every immutable menu item retains
the exact choice identity and exact zero-based path index used to construct its
P11.6H `NarrativeSessionStepRequest`, together with the structural label and
destination displayed to the user. The menu does not inspect a condition or
claim that any structural path is satisfiable. It does not traverse unrelated
scenes or rank, recommend, hide, or choose entries.

No available paths is displayed as `(none)` and still waits for `terminate`,
`quit`, EOF, or invalid explicit input. Graph shape never implies termination.

## Step, failure, and persistence behavior

A valid menu number causes exactly one `step_narrative_session(...)` call. The
frozen H/G/E/D chain decides success, condition satisfaction, transition
legality, consequences, diagnostics, trace, and evidence.

On success, the returned immutable next session is passed once to
`write_narrative_session_atomic(...)`. Only after that call returns is the next
session adopted and presented. The next prompt therefore cannot expose an
unpersisted state.

On any semantic failure, the current session object and persisted session file
remain unchanged. The complete canonical P11.6H step-result JSON, including the
authoritative P11.6E diagnostic/result information, is displayed. The shell
does not try a different path. It waits for another explicit input only after
reporting that failure.

If persistence raises `NarrativeSessionOutputError`, interaction stops. The
unpersisted next session is never adopted, displayed, retried, or used for a
later transition. P11.6H's atomic writer retains responsibility for preserving
the prior file.

## Quit, EOF, termination, and terminated sessions

`quit` and EOF return the latest successfully persisted state without another
step, termination request, or write. Neither changes narrative status.

`terminate` constructs the sole frozen termination reason,
`explicit_outcome`, and calls `terminate_narrative_session(...)` exactly once.
The returned immutable state is atomically persisted through the H writer,
then displayed, and interaction exits without accepting later input.

An already-terminated session is displayed deterministically and immediately
closed. No input is consumed, no transition or termination operation is
called, and no write occurs. A terminated session is never revived.

## Compatibility and exclusions

The historical `run`, `build`, P11.6G `narrative`, and P11.6H `create`, `step`,
and `terminate` parsers and execution paths are unchanged. P11.6H production,
P11.6B–G runtime modules, ProjectBuild, manifests, compiler, grammar, AIR,
editors, and protected validation fixtures are outside P11.6I ownership.

There is no random choice, scoring, recommendation, AI/LLM decision, automatic
fallback, automatic progression, background thread, daemon, sleep, filesystem
scan, network operation, or AIR `RuntimeEngine` narrative execution.
