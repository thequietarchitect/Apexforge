# P11-SRC-A — Semantic Decision Source Architecture Audit

## Status

Audit-only architecture slice.

Predecessor: `afp-p11.10i-freeze` / `41b71a30c88ae70125daae158ca398f9efdb5de1`.

P11-SRC-A introduces no production parser, source-AST, lowering, AIR, runtime, or semantic-decision behavior.

## Finding

P11.10 already owns the semantic meaning of advanced conditions, candidate alternatives, admissibility, convergence policies, convergence resolution, Paradox Elevation, validation, projection, and reporting.

The ordinary ApexForge source pipeline remains AIR-centered:

`source -> Parser/SourceUnitNode -> compiler -> AIRProgram -> ProjectBuild`

`SourceUnitNode` currently owns function, directive, workflow, authority, principal, and role declarations. `ProjectBuild` owns AIR/verified-AIR plus project, module, source-map, identity, and resolution metadata.

P11.5/P11.6 establish the correct precedent for a non-AIR semantic source family:

`narrative source -> narrative source AST -> narrative lowering -> NarrativeStory -> optional narrative build artifact`

P11-SRC will follow the same ownership principle rather than forcing semantic decisions into AIR or duplicating P11.10 semantics.

## Locked ownership boundary

P11-SRC owns only:

- author-facing semantic-decision source representation;
- immutable semantic-decision source AST;
- source recognition and parsing;
- source diagnostics;
- deterministic lowering/adaptation into frozen P11.10 objects;
- later project/tooling exposure where explicitly proven necessary.

P11.10 continues to own:

- `AdvancedCondition`;
- `CandidateAlternative`;
- admissibility evaluation;
- convergence policies and sets;
- convergence resolution;
- Paradox Elevation eligibility and elevation;
- semantic-decision validation;
- downstream projection and reporting.

The ordinary AIR compiler and `ProjectBuild` are unchanged by P11-SRC-A.

## Proposed structural words

The following words are unclaimed by the current lexer and are reserved as P11-SRC design candidates, not yet production keywords:

`decision`, `candidate`, `converge`, `using`, `incompatible`, `paradox`, `elevate`

Existing `when`, `requires`, `and`, `or`, `not`, `true`, and `false` should be reused where their existing language semantics are appropriate.

## Required flow

`.apex semantic-decision source -> P11-SRC source AST -> P11-SRC lowering -> frozen semantic_decision objects -> P11.10 evaluation/convergence/paradox/validation`

P11-SRC must not create a second implementation of convergence, admissibility, Paradox Elevation, or semantic validation.

## Non-goals

P11-SRC-A does not:

- add keywords to the lexer;
- extend `SourceUnitNode`;
- modify `compile_source`;
- modify `ProjectBuild`;
- create semantic-decision production files;
- add runtime mutation;
- alter any P11.10 frozen contract.

## Next slice

P11-SRC-B will begin with a deliberate red test proving that the immutable semantic-decision source AST module and its required public source-node contracts do not yet exist. Only after that red gate will the source-AST production implementation be added.
