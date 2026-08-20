# P11-SRC-F - Real .apex Compile/Analysis Acceptance

## Status

Integrated semantic-decision source-analysis slice following
`afp-p11-src-e-freeze`.

P11-SRC-F composes the already-frozen semantic-decision source stages into one
opt-in front-end analysis API and proves that source read from a real `.apex`
file traverses the complete source bridge:

`source text -> parse -> lower -> source/bridge validation`

The output is a validated passive P11.10 bridge. This slice does not compile
semantic-decision source to AIR and does not execute semantic-decision policy.

## Why F is opt-in

The existing ordinary compiler remains AIR-owned. `compile_source_with_map`
parses an ordinary source unit and returns `CompiledSource`; `compile_source`
returns its AIR program.

The established narrative precedent is different: narrative source analysis is
an explicitly opt-in composition API. It parses, lowers, constructs its graph,
validates, and returns one immutable analysis result without modifying the
ordinary compiler.

P11-SRC-F follows that precedent. Tooling/CLI dispatch belongs to P11-SRC-G.
Final cross-surface integration belongs to P11-SRC-H.

## Public surface

`apexforge/language/semantic_decision_analysis.py` exports exactly:

- `SemanticDecisionSourceAnalysis`
- `analyze_semantic_decision_source`

`SemanticDecisionSourceAnalysis` is immutable and contains:

- `source_document`: the exact P11-SRC-B/C source document;
- `semantic_bridge`: the exact P11-SRC-D bridge after successful P11-SRC-E
  validation.

Its invariant requires the source and bridge decision identities to agree in
source order and their document spans to agree.

## Fixed analysis order

`analyze_semantic_decision_source` performs exactly:

1. `parse_semantic_decision_source`;
2. `lower_semantic_decision_source`;
3. `validate_semantic_decision_source_bridge`;
4. construction of `SemanticDecisionSourceAnalysis`.

The E validator must return the exact bridge object. F does not introduce a
second transformed or copied validated representation.

## Real `.apex` acceptance

The F acceptance test writes semantic-decision source to a temporary file with
the `.apex` suffix, reads the file as UTF-8 source text, and analyzes it with
the real file path supplied as `source_name`.

The test proves:

- semantic-decision document recognition;
- preservation of `.apex` source-name provenance;
- deterministic repeat analysis;
- source decision ordering;
- candidate ordering;
- passive condition lowering;
- explicit-order policy adaptation;
- explicit incompatibility object reuse;
- exact equivalence with directly running C -> D -> E.

The temporary file is outside repository state and leaves no fixture residue.

## Diagnostic propagation

F does not wrap or replace predecessor diagnostics.

Malformed syntax propagates the existing parser diagnostic.

Unrepresentable source binding propagates the existing lowering diagnostic.

Source/bridge invalidity propagates the existing E validation diagnostic.

The original diagnostic stage and source span remain observable.

## Source-family isolation

The semantic-decision source recognizer remains opt-in and recognizes only
documents whose leading source form is `decision`.

Narrative `story` source remains narrative-owned.

Ordinary directive/function/workflow/authority/principal/role source remains
owned by the ordinary parser/compiler path.

F makes no change to `language.compiler`, `language.project`,
`language.narrative_analysis`, or the shared lexer.

## Deliberate non-ownership

P11-SRC-F does not call or reproduce:

- `evaluate_advanced_condition`;
- `construct_semantic_convergence_set`;
- `apply_semantic_convergence_policy`;
- `assess_paradox_elevation`;
- `elevate_paradox_assessment`;
- P11.10 validation;
- projection/reporting;
- runtime execution.

It also adds no CLI, PowerShell command, language-server, VS Code, or
Visual Studio integration.

## Meaning of "compile/analysis acceptance"

For this source-bridge phase, compile/analysis acceptance means that a real
`.apex` source file can be accepted by the front-end semantic-decision path and
lowered to a validated passive semantic bridge with compile-stage diagnostics
where appropriate.

It does not mean AIR lowering or native/backend compilation.

## Next slice

P11-SRC-G will integrate this frozen analysis API with user-facing tooling and
PowerShell `.apex` acceptance while preserving ordinary AIR and narrative
routing.