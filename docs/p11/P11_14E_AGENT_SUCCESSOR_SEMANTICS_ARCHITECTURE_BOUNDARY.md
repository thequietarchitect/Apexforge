# P11.14E â€” Agent Successor Semantics Architecture Boundary

## Status

Architecture-only, non-production boundary slice following frozen P11.14D.

Frozen predecessor:

- P11.14D commit: `12915a4082f709c0a398a1c110438451616139c3`
- annotated tag: `afp-p11-14d-freeze`

P11.14E introduces no production agent type.

## Frozen P11.14 chain

The predecessor chain remains:

1. P11.14B â€” minimal immutable agent identity, professional archetype, and agent
   definition declarations;
2. P11.14C â€” immutable professional-archetype catalog and deterministic
   archetype resolution;
3. P11.14D â€” passive `AgentDefinition` / `NarrativeCharacter` binding.

All predecessor field shapes, exports, behavior, and bytes remain frozen.

## Decision 1 â€” `capability` is not agent descriptive vocabulary

ApexForge already uses `capability` as authority- and authorization-bearing
vocabulary.

Existing owners resolve, require, check, and authorize capabilities before
execution. The language also exposes `capability` as authority syntax.

Therefore P11.14 must not introduce descriptive types such as:

- `AgentCapability`;
- `AgentCapabilityDescriptor`;
- `AgentCapabilityProfile`;
- `capability_ids` on `AgentDefinition`.

An agent declaration does not gain authority, permissions, execution rights, or
authorization merely because it has a professional archetype or narrative
character binding.

## Decision 2 â€” `policy` is also not agent descriptive vocabulary

`policy` already has multiple operative semantic owners in ApexForge, including
authority-policy and semantic-decision convergence-policy behavior.

P11.14E therefore introduces no `AgentPolicy`, `AgentPolicyDescriptor`, or
`AgentPolicyProfile`.

## Decision 3 â€” no speculative skill / competency / trait ontology

The architecture audit found no existing production contract or consumer that
requires a new agent `skill`, `competency`, or `trait` ontology.

`ProfessionalArchetype` already supplies the currently required descriptive
professional classification.

P11.14E therefore does not invent:

- `AgentSkill`;
- `AgentCompetency`;
- `AgentTrait`;
- skill/competency/trait catalogs;
- descriptive proficiency levels;
- scoring/ranking semantics.

A future slice may introduce such vocabulary only when a concrete consumer and
semantic boundary require it.

## Decision 4 â€” binding multiplicity remains deferred

`AgentCharacterBinding` continues to represent one explicit pair.

P11.14E introduces no:

- `AgentBindingSet`;
- binding registry;
- binding catalog;
- binding resolver;
- global one-to-one, one-to-many, or many-to-many rule.

Multiplicity becomes a production concern only when a concrete consumer requires
collection semantics.

## Decision 5 â€” operative agent semantics remain deferred

The repository currently has no canonical agent-domain owner for planning,
actions, tools, runtime, sessions, delegation, or multi-agent coordination.

P11.14E does not claim those namespaces.

No production types or functions named like the following enter this slice:

- `AgentPlan`;
- `AgentPlanner`;
- `AgentAction`;
- `AgentExecutor`;
- `AgentRuntime`;
- `AgentSession`;
- `AgentTool`;
- `ToolCall`;
- `ToolInvocation`;
- `MultiAgent`;
- `Delegation`.

## Decision 6 â€” next successor boundary

P11.14F should begin with a read-only architecture audit for the first operative
agent contract.

That audit must decide the separation among:

- intent / goal declaration;
- plan representation;
- action representation;
- tool-request representation;
- authorization checking;
- execution/runtime state.

No one of those concepts should be implemented until ownership and dependency
direction are explicit.

In particular:

- planning must not grant authority;
- action description must not execute effects;
- tool-request description must not invoke providers;
- authorization remains owned by existing authority/authorization subsystems;
- runtime/session mutation remains outside passive declaration models.

## Package boundary

`agents.__init__.__all__` remains empty.

No P11.14E production module is added.

## Integration boundary

P11.14E adds no integration with:

- AIR;
- authority;
- authorization;
- roles;
- governance;
- runtime;
- workflow;
- tooling;
- rich documents;
- cache;
- TAM;
- TAP;
- grammar or compiler lowering;
- project/build artifacts;
- provider/model invocation;
- filesystem, subprocess, network, or remote I/O.

## Freeze contract

P11.14E freezes an architectural negative space:

1. capability remains authority/authorization vocabulary;
2. policy is not repurposed as descriptive agent metadata;
3. professional archetype remains the only agent professional-classification
   primitive presently required;
4. speculative skill/competency/trait types are deferred;
5. binding multiplicity remains deferred;
6. planner/action/tool/runtime semantics remain deferred;
7. P11.14F begins by auditing the first operative agent semantic boundary;
8. no production file changes occur in P11.14E.