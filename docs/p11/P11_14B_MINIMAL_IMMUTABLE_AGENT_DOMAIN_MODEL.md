# P11.14B â€” Minimal Immutable Agent-Domain Model

## Status

RED-contract slice for the first production model in P11.14.

Frozen predecessor:

- P11.14A commit: `b7ac9468441749a8237517ca0dcb38acd0bbbbae`
- annotated tag: `afp-p11-14a-freeze`

Primary production owner:

- `agents.model`

No language, AIR, execution, authorization, tooling, project, package, cache,
TAM, or TAP integration belongs to P11.14B.

## Canonical model

P11.14B introduces exactly three model types.

### `AgentIdentity`

Frozen dataclass fields exactly:

1. `canonical_id: str`

Validation:

- exact `str`;
- non-empty;
- non-whitespace;
- already trimmed.

No kind/path hierarchy is frozen in this slice.

### `ProfessionalArchetype`

Frozen dataclass fields exactly:

1. `canonical_id: str`

Validation is identical to `AgentIdentity.canonical_id`.

A professional archetype is descriptive/classificatory only. It grants no AIR
role, authority, capability, permission, principal binding, or execution right.

No display label, prose description, skill map, authority set, or role link is
frozen in P11.14B.

### `AgentDefinition`

Frozen dataclass fields exactly:

1. `identity: AgentIdentity`
2. `archetype_ids: Tuple[str, ...] = ()`

Validation:

- `identity` must be an exact `AgentIdentity`;
- `archetype_ids` must be an exact tuple;
- each item must be an exact `str`, non-empty, non-whitespace, and already
  trimmed;
- declaration order is preserved;
- duplicate archetype IDs are rejected;
- the empty tuple is valid.

`AgentDefinition` stores archetype identity references rather than embedded
`ProfessionalArchetype` objects. Resolution belongs to a later P11.14 slice.

## Package surface

P11.14B creates:

- `agents.model`;
- `agents.__init__`.

`agents.model.__all__` is exactly:

- `AgentIdentity`
- `ProfessionalArchetype`
- `AgentDefinition`

`agents.__init__.__all__` remains empty. The first model is module-local until a
later integration slice explicitly promotes package exports.

## Explicit deferrals

P11.14B introduces no:

- `NarrativeIdentity` or `NarrativeCharacter` binding;
- character adapter;
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
- ApexForge grammar;
- lexer/parser/compiler lowering;
- AIR serialization;
- project kind;
- project manifest or loader field;
- build artifact schema;
- CLI routing;
- rich-document projection;
- incremental cache integration;
- TAM/TAP integration;
- remote I/O.

## Ownership rule

The only production files allowed to change in P11.14B are:

- `apexforge/agents/__init__.py`
- `apexforge/agents/model.py`

All frozen predecessor owners remain byte-identical.

## RED condition

Before implementation, importing `agents.model` must fail because the production
agent package does not exist at the P11.14A freeze.

The RED gate passes only when that absence is observed while the contract and
predecessor boundaries remain valid.