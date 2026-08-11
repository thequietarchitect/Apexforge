# P11.6G — User-Facing Narrative Execution Routing

## Scope and predecessor

P11.6G exposes one deterministic, non-interactive narrative transition through
the existing ApexForge CLI/public tooling architecture. Its frozen predecessor
is annotated tag `afp-p11.6f-freeze` at commit
`6963c606d408131be4f76adf3f2ecdf077ab4447`.

The route is invocation policy only. It does not compile narrative source,
create condition/consequence semantics, resolve transitions, generate trace or
diagnostics, infer termination, or own a session lifecycle.

## Public command

The single command is:

```text
apexforge narrative BUILD_ARTIFACT --request REQUEST_JSON
```

`BUILD_ARTIFACT` must be canonical `apexforge.build-artifact/v1` JSON whose
fingerprint verifies and whose `narrative` member is the frozen P11.6F
`apexforge.narrative-build-artifact/v1` projection. A historical AIR-only
artifact deterministically reports unavailable narrative material. The route
does not inspect source filenames, extensions, or raw text and does not rerun
the P11.5 compiler to bypass artifact authority.

The existing `run` command remains AIR-only. Existing `build` behavior is
unchanged and never executes a narrative merely because a build was requested.

## Explicit request representation

The request schema is `apexforge.narrative-execution-request/v1`. Every request
must provide all four top-level fields:

```json
{
  "choice": {"kind": "choice", "path": ["Decide"]},
  "path_index": 0,
  "schema": "apexforge.narrative-execution-request/v1",
  "state": {
    "choice_history": [],
    "current_scene": {"kind": "scene", "path": ["Start"]},
    "facts": [],
    "progression": [{"kind": "scene", "path": ["Start"]}],
    "story": {"kind": "story", "path": ["Story"]},
    "termination": {"reason": null, "status": "active"}
  }
}
```

State requires explicit story and current-scene identities, facts, non-empty
progression ending at the current scene, complete choice history, and complete
termination state. Choice identity and non-negative exact integer path index
are also mandatory. Missing or malformed fields are rejected; no initial scene,
choice, path, story, or progression is inferred. This is a one-shot request
document, not a save/checkpoint lifecycle.

## Artifact and authority routing

`tooling/narrative_execution.py` verifies the existing canonical build JSON and
fingerprint, validates that P11.6F semantic choice-path projection and P11.6C
executable path projection agree, and rehydrates the exact frozen P11.6C record
types. It neither reconstructs a competing `NarrativeBuildArtifact` nor binds
descriptive condition/consequence strings.

One request delegates exactly once to:

```text
runtime.narrative_observability.execute_narrative_choice(...)
```

That P11.6E boundary continues to delegate transition resolution, fail-closed
condition evaluation, consequence application, and immutable state movement to
P11.6D. The CLI does not import or call the P11.6D transition function.

## Deterministic result and failures

Results use `apexforge.narrative-execution-result/v1` and the existing canonical
sorted, two-space, UTF-8 JSON serializer. The output contains `ok`, complete
initial and final state, P11.6E diagnostics, ordered P11.6E trace, and selected
choice evidence. It contains no timestamp, random identifier, absolute path, or
Python representation.

P11.6E transition failures use exit code 30 and retain their narrative-specific
diagnostics and trace in the structured result. They include story mismatch,
exact choice/path failures, fail-closed unsatisfied conditions, and attempts
from already-terminated state. Failed transitions preserve the original state.

Pre-execution routing failures use exit code 50 and stable classifications:

- `APX-NARRATIVE-100`: invalid request;
- `APX-NARRATIVE-110`: unavailable build artifact;
- `APX-NARRATIVE-111`: malformed/noncanonical build artifact;
- `APX-NARRATIVE-112`: unavailable P11.6F narrative material;
- `APX-NARRATIVE-120`: malformed explicit execution state.

Argparse retains exit code 2 for invalid CLI shape.

## Preserved and deferred boundaries

P11.6G changes neither `ProjectBuild`, P11.6F artifact structures, manifest
schema, canonical AIR build output, nor historical AIR `run`. Runtime state
remains separate from immutable build material.

P11.6H or later owns interactive/repeated execution, choice menus, prompts,
automatic initial-state or scene creation, save/load and persistent campaigns,
explicit termination command routing, editor/debugger integration, and
long-running sessions. P11.6G performs at most one explicitly requested choice
transition and never terminates from graph shape or absence of choices.
