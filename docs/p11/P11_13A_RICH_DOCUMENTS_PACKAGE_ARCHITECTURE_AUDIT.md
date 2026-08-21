# P11.13A â€” Rich Documents and Package Architecture Audit

## Purpose

P11.13A is the audit-only entry slice for:

`P11.13 â€” Rich Documents and Package Architecture`

It begins from the frozen P11.12H three-layer incremental-cache checkpoint and
introduces no P11.13 production owner.

The slice exists to freeze the current ownership boundaries before P11.13B
creates the first immutable rich-document/package-tier model.

## Predecessor

P11.13A begins from:

`afp-p11-12h-freeze`

at:

`278e8716d666bc663bc9570f2b367958d2abba83`

The P11.12 predecessor remains immutable.

## Canonical P11.13 requirements

P11.13 requires:

- `.apexdoc`;
- executable document blocks;
- semantic tables;
- diagrams;
- world bibles;
- character sheets;
- simulation descriptions;
- package tiers:
  - `core`;
  - `standard`;
  - `domain`;
  - `experimental`.

P11.13-C is reserved for the specialized Experimental Codex Adapter.

That adapter is optional/advisory and must never become required for
deterministic compilation.

## Stage-boundary finding: no `.apexdoc` production yet

The current production tree contains no `.apexdoc` literal and no dedicated
source-family owner for `.apexdoc`.

The current project manifest remains:

- `name`;
- `sources`;
- `entry`;
- `schema`.

`LoadedProject` remains:

- `root`;
- `manifest_path`;
- `manifest`;
- `sources`;
- `project_kind`.

P11.13A therefore does not modify project-loader or manifest semantics.

Manifest integration is deferred until the rich-document model/parser contract
is frozen.

## Stage-boundary finding: no rich-document/package-tier owner

The audit found no current production owner matching:

- rich document;
- semantic table;
- semantic diagram;
- world bible;
- character sheet;
- simulation description;
- package descriptor;
- package tier.

P11.13B may therefore introduce dedicated immutable owners without conflicting
with an existing canonical implementation.

This absence is a stage-boundary fact.

Later P11.13 slices must not rerun the whole A smoke after these intentionally
absent owners are added.

They should verify A through its freeze tag, hashes, and durable architecture
decisions instead.

## Existing narrative ownership

The codebase already has extensive narrative semantics.

Canonical narrative model owners include:

- `NarrativeCharacter`;
- `NarrativeScene`;
- `NarrativeContinuity`;
- `NarrativeStory`;

under:

`language.narrative_model`

The audit also found the established parser, semantic graph, validation,
project-analysis, source-document, runtime-binding, execution, transition, and
observability families.

P11.13 must not create a second character/story/scene/continuity semantic
system.

## World-bible and character-sheet architecture

A world bible is a rich-document projection over existing narrative semantics.

It may organize or annotate canonical narrative identities, characters, scenes,
continuity, timelines, and related metadata.

It does not become a competing narrative semantic owner.

A character sheet follows the same rule.

It may project and structure canonical character/narrative identity data but
must not redefine `NarrativeCharacter` meaning.

## Simulation-description architecture

A simulation description is structured rich-document metadata.

It must remain deterministic and side-effect free in the model/parser slices.

Its structure should be reusable by later P11.15 interoperability/ApexMotion
work without starting P11.15 early.

## `.apexdoc` role

`.apexdoc` is a document container/source family, not a second Apex language.

An `.apexdoc` document can contain executable Apex blocks and non-executable
semantic-document blocks.

Executable blocks must delegate to the canonical Apex compiler.

P11.13 may extract, map, and compose those blocks; it may not invent alternate
Apex execution semantics.

## Executable-block lineage

Every executable block must retain deterministic lineage:

document â†’ block â†’ extracted Apex source â†’ canonical compiler/transformation

That lineage must remain suitable for TAM traceability.

Non-executable blocks have no runtime effect merely because they occur in an
`.apexdoc` document.

## Semantic tables

Semantic tables are deterministic structured semantic metadata.

Ordering must be canonical.

The table model must not silently execute expressions or introduce authority
decisions.

## Diagrams

Semantic diagrams are structured semantic graph/diagram metadata.

Rendering is secondary.

The canonical product should describe deterministic nodes/edges/relations;
visual rendering may consume that structure later.

## Package architecture

P11.13 introduces package architecture, not the future package manager.

The immutable package tiers are:

1. `core`
2. `standard`
3. `domain`
4. `experimental`

Tier classification is metadata/visibility architecture.

It does not grant semantic authority.

### Core

The `core` tier identifies language/runtime intrinsic contracts.

### Standard

The `standard` tier identifies canonical standard-library packages.

The existing P10 standard-library owner remains authoritative.

### Domain

The `domain` tier identifies deterministic domain-specific extensions.

### Experimental

The `experimental` tier identifies explicitly opt-in deterministic or advisory
extensions.

Experimental status never permits weaker correctness.

## Import and visibility ownership

Package-tier import behavior must reuse the existing canonical
module/import/visibility owners.

P11.13 must not introduce a second import resolver merely for package tiers.

## P14 boundary

The audit found no current production owner for:

- lockfiles;
- remote package registry;
- dependency solver;
- package signing;
- remote package restoration/fetch.

Those belong to the later P14 Package Manager and Registry phase.

P11.13 must not absorb that future scope.

## Existing Codex surface

The audit found existing Codex-related semantic-lattice production:

- `semantic_lattice.authoring.adapt_codex_semantic_lattice_proposal`;
- `semantic_lattice.validation.validate_codex_semantic_lattice_proposal`.

Therefore P11.13-C should adapt the existing Codex semantic-lattice proposal
surface rather than invent a competing Codex semantics owner.

The P11.13-C adapter remains:

- specialized;
- experimental;
- optional;
- advisory where applicable;
- non-required for deterministic compilation.

## CLI boundary

Current CLI `build`, `check`, and `run` all retain optional ProjectBuilder
injection seams.

P11.13A does not modify them.

CLI integration is deferred until deterministic `.apexdoc` parsing/building is
implemented.

## P11.12 cache boundary

P11.12 now provides Capture, Resonance, Stability, operational cache, and
ProjectBuilder integration.

P11.13A does not immediately cache rich-document products because those owners
do not yet exist.

Once canonical rich-document products are frozen, later P11.13 slices may reuse
P11.12 Capture/Resonance infrastructure.

## TAP boundary

P11.13A gives TAP no new ownership.

Rich-document parsing, package classification, or Codex adaptation must not
turn TAP into a semantic authority.

## Runtime boundary

P11.13A executes no runtime behavior.

Early P11.13 model/parser slices must remain deterministic and non-executing.

## Engineering decomposition

P11.13-C is reserved canonically.

The engineering sequence is:

- **P11.13A** â€” architecture/ownership/source-family/package-tier audit;
- **P11.13B** â€” minimal immutable rich-document + package-tier model;
- **P11.13-C** â€” Experimental Codex Adapter; optional/advisory only;
- **P11.13D** â€” `.apexdoc` parser, executable-block extraction, source mapping;
- **P11.13E** â€” semantic tables/diagrams and
  world-bible/character-sheet/simulation projections;
- **P11.13F** â€” project/package-tier integration,
  deterministic build/artifact/CLI;
- **P11.13G** â€” cache/TAM/tooling integration and deterministic equivalence;
- **P11.13H** â€” regression/capability census/final P11.13 freeze.

The decomposition is an engineering plan constrained by the canonical P11.13
roadmap and the reserved P11.13-C specialized adapter.

## P11.13B handoff

B should introduce the smallest immutable production vocabulary needed to make
the later parser/integration slices type-safe.

It should define structure, identity, block kinds, package-tier classification,
and package descriptors without:

- parsing `.apexdoc`;
- compiling executable blocks;
- mutating ProjectManifest;
- changing CLI behavior;
- executing runtime code;
- adding remote package management;
- duplicating narrative semantics;
- making Codex mandatory.

## Closure condition

P11.13A is complete when:

- P11.12H freeze ancestry and H hashes remain exact;
- the repository contains exactly two A audit artifacts;
- `.apexdoc` is still absent from production;
- no rich-document/package-tier production owner exists yet;
- existing narrative owners are explicitly recognized;
- existing Codex authoring/validation owners are explicitly recognized;
- package-manager/registry functionality remains deferred to P14;
- CLI/project-manifest integration remains deferred;
- package tier IDs are fixed as
  `core, standard, domain, experimental`;
- predecessor production and docs are unchanged.