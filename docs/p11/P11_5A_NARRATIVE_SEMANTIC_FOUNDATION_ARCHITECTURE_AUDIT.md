# P11.5A Narrative Semantic Foundation Architecture Audit

## Scope and controlling frozen baseline

P11.5A is an architecture-audit-only stage. It establishes the minimum
conceptual foundation for narrative semantics before syntax, semantic records,
graphs, diagnostics, serialization, compiler integration, or runtime behavior
are designed or implemented.

The controlling predecessor is P11.4H at commit
`c6570766703d00bba4e1aff7d712a0d271c9ecc1`. Its immutable annotated freeze is
`afp-p11.4h-freeze`, whose tag object is
`e8f8ed425f0ef265bdc9842b8abc5ecd96b2c78a`. P11.4H remains the frozen
predecessor. P11.5A is the first P11.5 stage.

The exact roadmap title is:

```text
P11.5  Rich Storytelling Semantic Foundation
```

P11.5A owns exactly this document and its architecture-audit smoke test. It
adds or changes no production file and changes no existing test or document.

## Why P11.5 follows identity and contextual resolution

P11.4 established deterministic declaration facts, structured qualification,
explicit query outcomes, contextual evidence, visibility filtering, and
outcome classification. Narrative structures need those stable distinctions
before they can refer to story-owned identities or relate declarations across
sources and modules. P11.5 therefore builds conceptually on identity and
contextual resolution rather than inventing a separate naming system.

That continuity does not integrate narrative semantics into P11.4 production
code. P11.5 must coexist with the operational ApexForge language rather than
replace its directive, function, module, compiler, runtime, or tooling model.

## Audit classification

Statements in this document have one of four roles:

- **Observed baseline:** behavior or structure already frozen by P11.4H.
- **Required architecture:** a conceptual responsibility established for the
  future P11.5 program.
- **Deferred design:** an implementation choice deliberately left open.
- **Non-goal:** work explicitly excluded from P11.5A.

No conceptual noun below is a frozen Python class, field, source keyword,
serialized key, node identifier, edge identifier, or diagnostic code.

## Minimum narrative semantic model

The minimum coherent vocabulary is story, character, scene, dialogue, choice,
perspective, timeline, narrative state, and continuity. These structures are
semantic input and are not decorative text. Their eventual deterministic
representation is called the Narrative Semantic Graph.

### Story

**Required architecture:** A story is the eventual narrative semantic root or
ownership boundary. It must organize narrative identities, scenes, choices,
state, time, and continuity without implying a source syntax, production
record, serialization container, or runtime entry point.

A story boundary supplies a place in which relations can be interpreted. It
does not mean that the story owns the existing runtime, replaces a project, or
becomes generated prose.

### Character

**Required architecture:** A character is an eventual narrative identity that
may participate in scenes, dialogue, knowledge, choices, and narrative-state
transitions. Four concepts must remain distinct:

- character identity: which narrative participant is referenced;
- character state: story-relevant facts currently attributed to that identity;
- character knowledge: information revealed or available to that identity;
- character participation: the identity's relation to a scene, dialogue, or
  choice.

Identity must not be inferred from mutable state, and compiler knowledge must
not automatically become character knowledge.

### Scene

**Required architecture:** A scene is an eventual narrative unit with
containment, ordering, dependency, perspective, dialogue, and state-transition
relations. Scene identity is separate from scene execution and from rendered
prose. Ordering states semantic temporal or narrative constraints; it is not a
runtime scheduler.

Dependencies may determine whether a scene is structurally reachable or
semantically consistent. P11.5A neither executes scenes nor freezes dependency
field names.

### Dialogue

**Required architecture:** Dialogue carries semantic participation rather than
existing only as plain string storage. Its future representation needs enough
meaning to associate:

- a speaker;
- one or more intended participants or listeners;
- scene membership;
- eligibility or dependency conditions;
- possible narrative consequences.

These are conceptual requirements, not field names. Text rendering, dialogue
generation, audio, voice, and runtime delivery remain outside this audit.

### Choice

**Required architecture:** A choice represents narrative branching and
reachability. It must eventually distinguish the choice identity, available
paths, path conditions, branch destinations or consequences, and reachability.

Choice branching is not automatic branch selection. The semantic model may
describe alternatives and consistency without choosing a winner or executing
a branch.

### Perspective

**Required architecture:** Perspective identifies the viewpoint through which
narrative information is observed or available. It is distinct from global
compiler truth and from omniscient analysis facts. A future analysis may use
perspective to reason about knowledge or revelation, but P11.5A defines no
viewpoint filter or accessibility policy.

### Timeline

**Required architecture:** Timeline semantics support deterministic temporal
ordering and temporal constraints. Impossible timelines are semantic
consistency failures rather than scheduling accidents.

P11.5A defines no time syntax, clock, calendar, duration algebra, scheduler,
wall-clock binding, or runtime execution model. The final canonical temporal
ordering algorithm remains deferred.

### Narrative state

**Required architecture:** Narrative semantic state represents story-relevant
facts and changes used to understand characters, scenes, choices, knowledge,
and continuity. It does not replace or extend the existing ApexForge runtime
execution state in P11.5A.

Narrative state may eventually describe semantic transitions even when no
runtime executes them. Runtime state remains the operational execution record.
No existing runtime-state record is modified.

### Continuity

**Required architecture:** Continuity is the invariant layer across identities,
scenes, knowledge, dependencies, choices, state, perspective, and timeline. It
is broader than temporal ordering. A narrative can be temporally ordered yet
inconsistent because identity, knowledge, participation, dependency, or state
facts contradict one another.

Continuity validation is not narrative generation. P11.5A creates neither a
continuity validator nor diagnostics.

## Narrative Semantic Graph purpose

The Narrative Semantic Graph is the eventual deterministic semantic
representation of narrative source structures. It must be derived from
semantic source structures rather than generated prose. It must be capable of
expressing these architectural relation families:

- narrative containment;
- identity participation;
- temporal ordering;
- scene dependency;
- dialogue participation;
- knowledge and revelation;
- choice branching and reachability;
- narrative-state transition;
- perspective;
- continuity constraints.

The graph is architectural only in P11.5A. No graph object is created. This
audit does not freeze Python class names, field names, constructors, enums,
serialized keys, artifact schemas, graph node IDs, graph edge IDs, or
diagnostic codes.

The graph is also not a substitute for existing compiler representations. AIR
continues to represent the frozen operational compilation boundary, while
artifact v1 continues to serialize its existing build contract.

## Roadmap validation responsibilities

The future semantic foundation must support deterministic detection or
classification of all eight roadmap responsibilities:

1. impossible timelines;
2. characters knowing unrevealed information;
3. broken scene dependencies;
4. contradictory identities;
5. missing dialogue participants;
6. unreachable choices;
7. unresolved narrative references;
8. accidental continuity changes.

P11.5A records these responsibilities without selecting algorithms, stages,
diagnostic codes, messages, spans, or recovery behavior. A later contract must
decide how evidence is represented before any diagnostic surface is added.

## Required semantic separations

The following boundaries are controlling:

```text
story structure != rendered prose
character identity != character state
character knowledge != compiler knowledge
scene ordering != runtime scheduling
dialogue semantics != plain string storage
choice branching != automatic branch selection
perspective != global truth
timeline != wall-clock execution
narrative state != runtime state
continuity validation != narrative generation
Narrative Semantic Graph != AIR
Narrative Semantic Graph != artifact v1
```

These separations prevent a later implementation from collapsing semantic
facts into presentation, execution, compiler omniscience, or serialization.

## Deterministic graph requirements

The eventual narrative model must preserve ApexForge determinism:

- identical narrative semantic input must produce identical graph ordering;
- identity must not depend on object addresses;
- graph ordering must not depend on hash-table iteration;
- source ordering and canonical identity rules must be explicit;
- duplicate or contradictory narrative identities require deterministic
  treatment;
- continuity analysis must not silently choose among contradictory
  interpretations;
- hidden ranking and probabilistic resolution are prohibited.

Canonical ordering is a future design question. P11.5A does not choose whether
source order, identity order, relation-family order, or another structured key
forms the final algorithm. It requires only that the choice become explicit,
stable, and non-semantic where used for evidence presentation.

## Compatibility with operational ApexForge

**Observed baseline:** P11.4H provides an explicit contextual resolution API
over successfully built declaration candidates. P11.5A does not consume or
change that API.

**Compatibility invariant:** Project construction, candidate resolution, AIR,
artifact bytes and fingerprints, compiler behavior, linker behavior, validator
behavior, entry resolution, runtime execution, CLI behavior, LSP, VS Code, and
Visual Studio remain unchanged. Existing diagnostics remain unchanged.

Narrative semantics must eventually interoperate with the operational language
through reviewed contracts. They must not replace directives, functions,
module identity, runtime state, or existing authority behavior.

## Exact P11.5A ownership and acceptance evidence

P11.5A owns exactly:

```text
apexforge/p11_5a_narrative_semantic_foundation_architecture_audit_smoke_test.py
docs/p11/P11_5A_NARRATIVE_SEMANTIC_FOUNDATION_ARCHITECTURE_AUDIT.md
```

There are no production changes. There are no modifications to existing tests
or documentation. The executable audit verifies:

- the exact P11.4H commit, tag, and annotated-tag object;
- the nine-term vocabulary and Narrative Semantic Graph purpose;
- every validation responsibility and semantic separation;
- deterministic graph constraints;
- absence of storytelling lexer keywords and grammar declarations;
- absence of narrative production declarations, graph objects, diagnostic
  codes, and automatic project integration;
- the exact two-file ownership boundary;
- accepted P11.4H compatibility for project, resolution, AIR, artifacts,
  compiler, linker, validator, entry, runtime, CLI, LSP, VS Code, and Visual
  Studio;
- no network access, repository mutation, bytecode mutation, or in-repository
  temporary fixture.

## Explicit non-goals

P11.5A does not introduce or change:

- storytelling source syntax or parser keywords;
- grammar productions or AST records;
- semantic-model records;
- graph classes, builders, validators, nodes, edges, or identifiers;
- continuity diagnostics or narrative diagnostic codes;
- text, prose, story, or dialogue generation;
- AI story generation;
- runtime scene execution or branch execution;
- game-engine behavior or visual rendering;
- ApexMotion integration;
- audio, voice, or network behavior;
- AIR or artifact v1;
- manifests, compiler, linker, validator, or entry resolution;
- runtime state or execution;
- CLI, LSP, VS Code, Visual Studio, or standard-library behavior.

Architectural example names such as `NarrativeSemanticGraph`,
`StoryDeclaration`, `CharacterDeclaration`, `SceneDeclaration`,
`DialogueDeclaration`, `ChoiceDeclaration`, `ContinuityValidator`, and
`NarrativeDiagnostic` are not production declarations and are not reserved by
this audit.

## Deferred design decisions

P11.5A deliberately leaves unresolved:

- narrative source syntax and grammar;
- production type and field names;
- ownership integration with projects, modules, and declarations;
- canonical narrative identity and graph ordering algorithms;
- graph storage and traversal APIs;
- knowledge, time, state, dependency, and reachability formalisms;
- validation stages and diagnostic evidence;
- AIR, artifact, runtime, CLI, and tooling integration;
- serialization and schema versioning.

Deferring these questions prevents architecture-audit terminology from becoming
an accidental production contract.

## Proposed next stage

```text
P11.5B  Minimal Narrative Semantic Model Contract
```

P11.5B is proposed only. P11.5A does not define its production API, fields,
files, syntax, or implementation, and does not begin P11.5B.
