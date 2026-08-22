# P11.14D â€” Agent / Narrative-Character Binding

## Status

RED-contract slice for the first explicit cross-domain binding between the frozen
P11.14 agent declaration domain and the frozen narrative-character domain.

Frozen predecessor:

- P11.14C commit: `99dc17eb8225b2a07ed552293471747afc770903`
- annotated tag: `afp-p11-14c-freeze`

Primary production owner:

- `agents.character_binding`

All P11.14B/P11.14C agent-domain owners remain byte/API frozen.

The frozen narrative model remains byte/API frozen.

## Architectural decision

P11.14D introduces one passive immutable record:

`AgentCharacterBinding`

with fields exactly:

1. `definition: AgentDefinition`
2. `character: NarrativeCharacter`

The binding references the full canonical objects rather than copying or reducing
them to `AgentIdentity` or `NarrativeIdentity`.

Rationale:

- `AgentDefinition` is the canonical passive declaration and already preserves its
  exact `AgentIdentity`;
- `NarrativeCharacter` is the canonical narrative-domain character object and
  already validates that its `NarrativeIdentity.kind` is `"character"`;
- the binding therefore does not duplicate identity-kind validation;
- preserving both full objects keeps their frozen domain semantics intact.

## Validation

`AgentCharacterBinding` is a frozen dataclass.

Construction requires:

- `definition` to be an exact `AgentDefinition`;
- `character` to be an exact `NarrativeCharacter`.

No normalization, copying, re-resolution, or reconstruction occurs.

The exact supplied objects are preserved:

- `binding.definition is definition`;
- `binding.character is character`.

## Multiplicity boundary

Each `AgentCharacterBinding` record represents exactly one agent-definition /
narrative-character pair.

P11.14D introduces no registry, collection, catalog, resolver, or global uniqueness
rule. Cross-record multiplicity and uniqueness semantics are deferred.

## Archetype-resolution orthogonality

`AgentCharacterBinding` accepts a frozen `AgentDefinition` directly whether or
not the caller has separately produced an `AgentArchetypeResolution`.

P11.14D does not import or require `agents.catalog` or `agents.resolution`.

## Narrative ownership

Character-kind validation remains exclusively owned by
`language.narrative_model.NarrativeCharacter`.

P11.14D does not inspect or revalidate `NarrativeIdentity.kind` or path contents.

## Module export boundary

`agents.character_binding.__all__` is exactly:

- `AgentCharacterBinding`

`agents.__init__.__all__` remains empty and does not re-export the binding.

## Dependency boundary

Production may import only:

- Python standard-library dataclass support;
- `AgentDefinition` from `agents.model`;
- `NarrativeCharacter` from `language.narrative_model`.

P11.14D imports no:

- `agents.catalog`;
- `agents.resolution`;
- runtime narrative binding;
- AIR;
- role;
- authority;
- authorization;
- governance;
- workflow;
- tooling;
- rich-document projection;
- cache;
- TAM;
- TAP.

## Explicit deferrals

P11.14D introduces no:

- agent or character registry;
- binding catalog;
- binding resolver;
- global one-to-one or many-to-many enforcement;
- planner or planning state;
- action model or executor;
- tool call or invocation;
- autonomous selection;
- model/provider invocation;
- runtime/session state;
- delegation;
- multi-agent coordination;
- authority or permission semantics;
- grammar/compiler lowering;
- project/build-artifact integration;
- filesystem, subprocess, network, timer, or remote I/O.

## RED condition

Before production implementation, `agents.character_binding` does not exist.

The RED gate passes only when import fails for that expected missing module while
all frozen predecessor and cross-domain owner hashes remain intact.