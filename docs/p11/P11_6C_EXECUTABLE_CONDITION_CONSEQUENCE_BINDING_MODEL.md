# P11.6C — Executable Condition/Consequence Binding Model

## Status

P11.6C binds descriptive execution text; it does not execute it.

The controlling predecessor is the frozen P11.6B checkpoint:

- tag: `afp-p11.6b-freeze`
- commit: `b339791715670ad752d3a82e315b1f9334b1e55a`

P11.6B remains unchanged.

## Source semantic boundary

P11.5 remains frozen.

`NarrativeChoicePath.condition` and `NarrativeChoicePath.consequence` remain
optional descriptive strings. P11.6C does not alter their source syntax,
parser, lowering, graph, validation, or semantic model.

The binding layer consumes those exact strings and maps them to explicit
narrative-specific executable representations supplied by the caller.

Exact-text binding is intentional. P11.6C does not guess meaning from prose,
case-fold text, tokenize prose into expressions, or silently reinterpret
descriptive language.

## Why AIR expressions are not reused

AIR expressions are not reused.

The existing AIR expression hierarchy is verified and runtime-evaluable.
Existing AIR state assignments and conditional actions belong to the AIR
runtime execution model.

Narrative execution remains separate, so P11.6C introduces a minimal
narrative-specific binding vocabulary.

## NarrativeFactPredicate

`NarrativeFactPredicate` is an explicit future-evaluable condition record:

- narrative subject;
- fact name;
- operator: `equals` or `not_equals`;
- expected string value.

P11.6C validates this structure but does not evaluate it.

## NarrativeFactAssignment

`NarrativeFactAssignment` is an explicit future-applicable consequence record:

- narrative subject;
- fact name;
- replacement string value.

It represents setting one current narrative fact slot. P11.6C does not apply
the assignment.

## Binding registries

`NarrativeConditionBinding` maps one exact descriptive condition string to one
`NarrativeFactPredicate`.

`NarrativeConsequenceBinding` maps one exact descriptive consequence string to
one or more ordered `NarrativeFactAssignment` records.

Duplicate source-text keys are rejected. Consequence bindings also reject
duplicate fact slots within one consequence.

## Choice-path binding

`bind_narrative_story(...)` walks frozen `NarrativeStory.choices` and every
choice-path tuple in existing order.

For each path it creates `NarrativeExecutableChoicePath`, preserving choice
identity, source scene, path index, label, destination, original condition text,
bound predicate, original consequence text, and ordered assignments.

The frozen semantic story is never mutated.

## Missing and unbound semantics

Missing condition means ungated.

Present but unbound condition text is rejected.

A missing consequence means no consequence assignments.

Present but unbound consequence text is rejected.

`NarrativeBindingError` is raised for present descriptive text without an
explicit exact-text binding. Unknown condition prose therefore cannot silently
become truthy.

## Determinism

Binding is deterministic because choice order, path order, path indices,
exact-text lookup, and assignment order are preserved, while duplicate registry
keys are rejected. All public binding records are frozen.

## Stage boundaries

No condition evaluation.

No consequence application.

No scene transition.

No choice selection.

No initial-scene resolution.

No state mutation.

No runtime trace emission.

No runtime diagnostics.

No termination policy.

No AIR lowering.

No `ProjectBuild` integration.

No build-artifact schema.

No manifest change.

No CLI routing.

No editor integration.

## Successor stages

P11.6D may consume these bindings to implement deterministic scene/choice
transition mechanics.

P11.6E remains responsible for trace, runtime diagnostics, and termination.

P11.6F and later stages remain responsible for artifacts and public routing.
