# P11.14A â€” Agent, Character, and Professional-Archetype Declaration-Model Architecture Audit

## Status

Architecture-audit-only slice. No production model, grammar, compiler, runtime,
tooling, project, package, cache, TAP/TAM, or autonomous behavior is introduced
by P11.14A.

Frozen predecessor:

- P11.13F commit: `32a440e46dd903fe91b115f6e36ec2fca45d3026`
- annotated tag: `afp-p11-13f-freeze`

Roadmap owner:

- P11.14 â€” Agents, characters, and professional archetypes.

## Audit conclusion

P11.14 requires a new canonical agent-domain owner. Existing narrative character
and AIR role owners are semantically distinct and remain frozen.

The successor minimal model is expected to begin under `agents.model`, but P11.14A
does not create that production package.

## Canonical boundary decisions

### 1. Agent is a new domain

`Agent` must not be implemented by renaming, subclassing, or extending
`NarrativeCharacter`, `AIRRole`, `AIRPrincipal`, or a runtime/session type.

The repository currently has no canonical production Agent, AgentDefinition,
AgentPlanner, AgentAction, AgentRuntime, ToolCall, ProfessionalArchetype, or
MultiAgent model. P11.14 therefore receives a clean namespace and a new owner.

### 2. NarrativeCharacter remains narrative-owned

`language.narrative_model.NarrativeCharacter` remains the canonical narrative
character identity and keeps its frozen shape.

P11.14 does not add fields to NarrativeCharacter and does not reinterpret
narrative character identity as autonomous execution state.

A later agent model may define an explicit reference/binding to a canonical
character representation, but the relationship must be owned by the agent
domain rather than by `language.narrative_model`.

### 3. Professional archetype is not an AIR role

AIR role semantics are authorization-bearing: roles carry authority references,
participate in authority resolution, and are stored by `RoleRegistry`.

A professional archetype is descriptive/classificatory. It must not implicitly
grant roles, authorities, capabilities, permissions, or execution rights.

P11.14A therefore rejects direct reuse of `AIRRole` or `RoleRegistry` as the
professional-archetype model.

### 4. Declaration is not permission

The existence of an agent, character association, or professional archetype
grants no authority.

P11.14A introduces no principal binding, role resolution, authority inheritance,
capability grant, trust decision, permission evaluation, or governance policy.

Future authorization integration must be explicit and owned by the existing
authorization/governance boundaries.

### 5. P11.14A is non-executing

P11.14A defines no:

- planner or planning algorithm;
- action execution;
- tool call or tool invocation;
- model/provider invocation;
- autonomous selection;
- delegation;
- multi-agent coordination;
- runtime/session lifecycle;
- workflow execution;
- narrative transition;
- filesystem, subprocess, timer, network, or remote I/O.

### 6. No language grammar in P11.14A

No `agent`, `archetype`, or related ApexForge source keyword is added in this
slice. Lexer, parser, compiler, AIR serialization, language-server behavior,
Visual Studio syntax, and VS Code syntax remain frozen.

The minimal immutable domain model must exist and stabilize before source syntax
is considered.

### 7. Frozen predecessor owners are reference-only

P11.14A must not mutate:

- `language.narrative_model`;
- `air.model` or AIR role/principal semantics;
- `role.registry`;
- `authorization`;
- `governance`;
- `runtime`;
- `workflow`;
- `tooling.cli`;
- `tooling.build_artifact`;
- project manifest/loader/project-kind surfaces;
- `rich_documents`;
- incremental cache;
- TAM or TAP;
- P11.13 package integration.

## Answers to the architecture-audit questions

1. **New Agent owner?** Yes. Agent requires a new canonical domain owner rather
   than overloading NarrativeCharacter.
2. **Professional archetype relation to role?** Distinct descriptive model.
   It does not reuse or compose AIR role authority semantics in P11.14A.
3. **Identity/authority references?** Declaration alone grants none. Authority,
   roles, capabilities, and permissions are explicitly outside this slice.
4. **Purely declarative/immutable?** Yes. P11.14A is architecture-only and the
   successor minimal model must begin immutable and non-executing.
5. **Minimum grammar?** None in P11.14A.
6. **Deferred behavior?** Planning, actions, tools, runtime, sessions,
   delegation, autonomy, provider/model invocation, and multi-agent behavior.
7. **Reference-only owners?** Narrative, AIR role/principal, authorization,
   governance, runtime, workflow, tooling, project/package, cache, TAM/TAP.

## Successor direction

P11.14B should define the smallest immutable agent-domain model necessary to
represent agent identity and professional-archetype classification without
execution or permission semantics.

P11.14B must audit exact field shapes before production and should avoid
prematurely defining planning, action, tool, runtime, or multi-agent contracts.