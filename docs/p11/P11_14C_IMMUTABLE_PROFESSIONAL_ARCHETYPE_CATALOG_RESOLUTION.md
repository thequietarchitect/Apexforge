# P11.14C â€” Immutable Professional-Archetype Catalog and Deterministic Resolution

## Status

RED-contract slice for the first resolution layer around the frozen P11.14B
agent-domain model.

Frozen predecessor:

- P11.14B commit: `eae088afaece010acf5a43957ae7131053c77f30`
- annotated tag: `afp-p11-14b-freeze`

Primary production owners:

- `agents.catalog`
- `agents.resolution`

P11.14B `agents.model` remains byte/API frozen.

## Architectural decision

P11.14C resolves the `AgentDefinition.archetype_ids` references introduced by
P11.14B before any agent-to-narrative-character binding is introduced.

P11.14C uses an immutable deterministic catalog, not a mutable runtime registry.

Character binding is deferred to P11.14D.

## `ProfessionalArchetypeCatalog`

`agents.catalog.ProfessionalArchetypeCatalog` is a frozen dataclass with fields
exactly:

1. `archetypes: Tuple[ProfessionalArchetype, ...] = ()`

Construction rules:

- `archetypes` must be an exact tuple;
- every item must be an exact `ProfessionalArchetype`;
- authored/declaration order is preserved;
- object identity is preserved;
- duplicate `canonical_id` values are rejected;
- an empty catalog is valid.

The catalog exposes:

`resolve(canonical_id: str) -> ProfessionalArchetype`

Resolution rules:

- `canonical_id` must be an exact, non-empty, non-whitespace, already-trimmed
  string;
- lookup is by exact canonical-ID equality;
- the exact canonical object stored in the catalog is returned;
- an unknown canonical ID raises `ValueError`;
- the catalog is never mutated by lookup.

`agents.catalog.__all__` is exactly:

- `ProfessionalArchetypeCatalog`

## `AgentArchetypeResolution`

`agents.resolution.AgentArchetypeResolution` is a frozen dataclass with fields
exactly:

1. `definition: AgentDefinition`
2. `archetypes: Tuple[ProfessionalArchetype, ...]`

Validation rules:

- `definition` must be an exact `AgentDefinition`;
- `archetypes` must be an exact tuple;
- every resolved item must be an exact `ProfessionalArchetype`;
- the result length must equal `definition.archetype_ids`;
- each resolved `canonical_id` must exactly match the corresponding
  `definition.archetype_ids` item;
- order and canonical catalog-object identity are preserved.

## Resolver

`agents.resolution.resolve_agent_archetypes` has the contract:

`resolve_agent_archetypes(definition, catalog) -> AgentArchetypeResolution`

Rules:

- `definition` must be an exact `AgentDefinition`;
- `catalog` must be an exact `ProfessionalArchetypeCatalog`;
- each ID is resolved in frozen `AgentDefinition.archetype_ids` order;
- unknown IDs fail explicitly through `ValueError`;
- the returned resolution preserves the exact `AgentDefinition` object;
- the returned archetypes are the exact canonical objects stored in the catalog;
- an agent with no archetype IDs resolves to an empty tuple;
- no mutation occurs.

`agents.resolution.__all__` is exactly:

- `AgentArchetypeResolution`
- `resolve_agent_archetypes`

## Package boundary

`agents.__init__.__all__` remains empty and does not re-export P11.14C types or
functions.

## Frozen P11.14B surfaces

P11.14C must not mutate:

- `apexforge/agents/__init__.py`;
- `apexforge/agents/model.py`;
- the P11.14B smoke test;
- the P11.14B contract document.

`AgentIdentity`, `ProfessionalArchetype`, and `AgentDefinition` retain their exact
P11.14B field shapes and behavior.

## Explicit deferrals

P11.14C introduces no:

- `NarrativeIdentity` or `NarrativeCharacter` binding;
- character adapter or character-resolution model;
- planner or plan model;
- action model or executor;
- tool call or tool invocation;
- autonomous selection;
- provider/model invocation;
- runtime/session state;
- delegation;
- multi-agent coordination;
- AIR role/principal/authority reuse;
- authorization or governance resolution;
- ApexForge grammar or compiler lowering;
- project/tooling/build-artifact integration;
- incremental-cache integration;
- TAM/TAP integration;
- filesystem, subprocess, network, timer, or remote I/O.

## RED condition

Before production implementation:

- `agents.catalog` does not exist;
- `agents.resolution` does not exist.

The RED gate passes only when the first missing production module is observed for
that expected reason while all frozen P11.14B hashes remain intact.