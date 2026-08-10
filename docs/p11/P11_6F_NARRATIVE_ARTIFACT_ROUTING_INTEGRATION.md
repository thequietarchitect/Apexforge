# P11.6F — Narrative Artifact, Routing, and Integration Boundary

## Status

P11.6F is the first narrative stage allowed to cross into ApexForge's existing
build-artifact surface. It packages already compiled narrative semantics and
P11.6C executable bindings; it does not create a second narrative compiler or
runtime.

The controlling predecessor is the annotated P11.6E freeze:

- tag: `afp-p11.6e-freeze`
- commit: `ba038346e04bb1733a43c522eda8dffe54709f0d`

## Artifact representation

`tooling/narrative_artifact.py` defines the immutable
`NarrativeBuildArtifact`. Its canonical material is:

- the source name;
- the exact P11.5 `NarrativeStory` semantic object;
- the exact P11.6C `NarrativeExecutableBindingSet` object.

The story and binding objects are referenced, not reconstructed into parallel
runtime records. Their JSON projection uses the deterministic schema
`apexforge.narrative-build-artifact/v1`; family and path ordering is preserved
from the frozen tuples and mapping keys are canonicalized by the existing
build-artifact JSON serializer.

No `NarrativeExecutionState`, `NarrativeExecutionResult`, transition result,
trace, diagnostic, termination state, timestamp, random identifier, or runtime
progression is stored. Initial scene selection and choice selection remain
runtime caller concerns.

## Routing and compatibility

`route_narrative_build_material(...)` accepts only the exact compiled
`NarrativeSourceAnalysis` and exact P11.6C binding set. The binding story must
match the semantic story identity. This is semantic-output authority: no
filename or arbitrary-text heuristic activates the route.

The existing `CanonicalBuildArtifact` has one optional
`narrative_artifact` association. `construct_build_artifact(...)` defaults it
to `None`, preserving the historical non-narrative payload, bytes, fingerprint,
constructor behavior, project metadata, AIR serialization, and CLI behavior.
When explicitly supplied, the narrative projection is added under the
`narrative` key and is included in the existing canonical fingerprint. The
existing `ProjectBuild` contract is unchanged because it owns linked AIR and
does not contain narrative compilation material.

The public `tooling` package exports the new artifact and routing symbols.
The CLI and manifest are unchanged: schema-1 manifests remain authoritative
for existing AIR projects, and `apexforge build` does not infer narrative
content or execute narrative runtime behavior.

Absent narrative material therefore follows the existing path and produces a
normal AIR artifact. Malformed material fails at the exact type/identity
boundary; malformed narrative source continues to fail through the existing
P11.5 parser/analysis diagnostics.

## Frozen execution boundaries

- P11.6B remains the owner of immutable execution/result record shapes.
- P11.6C remains the owner of descriptive-to-executable bindings.
- P11.6D remains the sole scene/choice transition authority.
- P11.6E remains the owner of trace, diagnostics, and explicit termination.
- P11.6F only packages and routes build material.

There is no automatic choice, no initial-scene inference, no graph-shape
termination, no AIR runtime reuse, and no mutation of frozen narrative
semantic or runtime objects.

## Deferred boundary

P11.6F deliberately does not add a user-facing narrative run command,
interactive loop, input prompting, save/load state, editor integration, or
runtime orchestration. A successor such as P11.6G or later may own project
recognition and user-facing execution routing if those concerns are approved
as a separate slice.
