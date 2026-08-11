# P11.6H — Narrative Session and State Lifecycle

## Scope and predecessor

P11.6H adds deterministic persistence and explicit lifecycle operations above
the frozen P11.6G one-shot route. Its exact predecessor is annotated tag
`afp-p11.6g-freeze` at commit
`401990113b539ef4aee5213cdc8d444c49160643`.

The stage owns one tooling module, `tooling/narrative_session.py`, plus narrow
CLI and public-export wiring. P11.6B through P11.6G production structures are
unchanged.

## Immutable session record

The session schema is `apexforge.narrative-session/v1`. It contains only:

- the schema;
- the canonical build-artifact SHA-256 algorithm and fingerprint;
- the exact story identity;
- the current immutable P11.6B `NarrativeExecutionState`.

The story member must equal the execution state's story. There is no session
identifier, timestamp, UUID, machine path, Python representation, UI state,
or duplicated story/binding material. The fingerprint binds the session to
the complete canonical P11.6F-capable build artifact, not merely to a story
name or filesystem location.

Loading requires valid UTF-8, duplicate-free JSON, exact fields and identity
kinds, the supported schema, canonical existing JSON formatting, and valid
P11.6B state invariants. Artifact-relative use additionally verifies the
artifact fingerprint and story; declared scenes, facts, progression, and
choice history must be possible for the validated artifact and its exact
P11.6C binding paths. Malformed state is rejected rather than repaired.

Session serialization reuses P11.1C `canonical_json_bytes`: UTF-8, sorted
mapping keys, two-space indentation, and a final newline. Session files are
written through a temporary sibling, flushed and synchronized, then atomically
replaced. An unsuccessful write preserves an existing output file.

## Explicit creation

Creation uses request schema
`apexforge.narrative-session-create-request/v1` with exact `story`,
`start_scene`, and `facts` members. Story and scene are full narrative
identities. The starting scene must be declared by that exact artifact story;
it is never inferred from order, graph roots, incoming edges, filenames,
manifests, or naming conventions.

The initial state has the requested scene as its sole progression entry, no
choice history, supplied normalized facts, and active termination. Creation
never inspects graph shape and never infers a terminal outcome.

## One explicit step

The step request schema is
`apexforge.narrative-session-step-request/v1` and requires one exact choice
identity and one non-negative exact integer path index. After artifact/session
association validation, P11.6H constructs the frozen P11.6G
`NarrativeExecutionRequest` and calls `execute_narrative_request(...)` exactly
once. P11.6G delegates to P11.6E `execute_narrative_choice(...)`, which retains
P11.6D as the sole transition authority.

The step result schema is
`apexforge.narrative-session-step-result/v1`. Its `execution` member is the
unchanged complete P11.6G result projection: success, initial/final states,
P11.6E diagnostics, trace, and choice evidence. Its `session` member contains
the new immutable session only on success. A P11.6E failure produces no next
session and does not write or replace the requested output path. This includes
fail-closed unsatisfied conditions and `NARRATIVE_EXECUTION_TERMINATED`.

## Explicit termination

The termination request schema is
`apexforge.narrative-session-terminate-request/v1`. Its explicit `reason` is
passed to frozen P11.6E `terminate_narrative(...)`; the supported frozen value
is `explicit_outcome`. Success creates a new immutable session with the
terminated state. Re-termination remains a deterministic P11.6E error exposed
as the narrow P11.6H termination failure. Scene shape, outgoing choices, path
satisfiability, and destination naming never terminate a session.

## CLI and deterministic failures

P11.6G remains exactly:

```text
apexforge narrative BUILD_ARTIFACT --request REQUEST_JSON
```

P11.6H adds a separate namespace. Each invocation performs at most one action:

```text
apexforge narrative-session create BUILD --request CREATE_JSON --output SESSION
apexforge narrative-session step BUILD SESSION --request STEP_JSON --output NEXT_SESSION
apexforge narrative-session terminate BUILD SESSION \
  --request TERMINATE_JSON --output TERMINATED_SESSION
```

All output paths are explicit. There is no stdin choice input, prompt, menu,
loop, current-session scan, hidden state, campaign folder, or autosave policy.
Normal lifecycle routing failures use exit code 51 and stable codes:

| Code | Classification |
| --- | --- |
| `APX-NARRATIVE-200` | invalid explicit lifecycle request |
| `APX-NARRATIVE-210` | unavailable session file |
| `APX-NARRATIVE-211` | malformed or noncanonical session |
| `APX-NARRATIVE-220` | unavailable build artifact |
| `APX-NARRATIVE-221` | malformed build artifact |
| `APX-NARRATIVE-222` | unavailable narrative build material |
| `APX-NARRATIVE-230` | artifact/session fingerprint mismatch |
| `APX-NARRATIVE-231` | story mismatch |
| `APX-NARRATIVE-232` | invalid explicit starting scene |
| `APX-NARRATIVE-233` | malformed explicit initial facts |
| `APX-NARRATIVE-240` | explicit termination failure |
| `APX-NARRATIVE-250` | atomic session output failure |

P11.6E transition failures retain exit code 30 and their complete structured
diagnostic/trace result. They are not rewritten as H routing errors.

## Preserved and deferred boundaries

Historical AIR `run`, historical `build`, P11.6G `narrative`, `ProjectBuild`,
manifests, grammar, compiler, AIR, runtime contracts, and P11.6F/G production
structures remain unchanged. Build artifacts contain no session or runtime
state.

P11.6I or later retains interactive loops, repeated prompting, automatic
choice/path/scene selection, menus, automatic progression, campaigns,
profiles, autosaves, checkpoints, editor/debugger integration, background
services, long-running sessions, and richer human-readable narrative UX.
