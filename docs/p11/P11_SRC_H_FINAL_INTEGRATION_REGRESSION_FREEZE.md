# P11-SRC-H â€” Final Integration Regression and Source-Surface Bridge Freeze

## Purpose

P11-SRC-H closes the Semantic Decision Source-Surface Bridge track by proving
that the frozen A-through-G slices compose as one deterministic user-facing
capability without introducing new semantic ownership.

H is an integration/freeze slice. It does not add parser, lowering,
validation, convergence, Paradox Elevation, runtime, or P11.10 behavior.

## Frozen predecessor chain

The final integration proof requires these exact frozen slices, in ancestry
order:

- P11-SRC-A â€” architecture and grammar ownership audit
- P11-SRC-B â€” immutable semantic-decision source AST
- P11-SRC-C â€” dedicated source parser
- P11-SRC-D â€” one-way lowering into frozen P11.10 objects
- P11-SRC-E â€” source/bridge validation and deterministic diagnostics
- P11-SRC-F â€” real `.apex` parse/lower/validate analysis composition
- P11-SRC-G â€” project classification, PowerShell/CLI check routing,
  multi-source project composition, and document-local LSP diagnostics

The G freeze is the immediate predecessor for H.

## Integrated source path

The frozen source bridge is:

`.apex source`
â†’ P11-SRC-C parser
â†’ P11-SRC-D lowering
â†’ P11-SRC-E source/bridge validation
â†’ P11-SRC-F analysis
â†’ P11-SRC-G project composition
â†’ PowerShell/CLI `check` and LSP diagnostics

The lowered objects remain the exact P11.10 semantic-decision objects.
P11-SRC does not define a competing convergence or Paradox semantic system.

## Capability census

The final SRC track contains seven frozen predecessor slices (A through G)
and nine production touchpoints:

1. `language/semantic_decision_source.py`
2. `language/semantic_decision_parser.py`
3. `language/semantic_decision_lowering.py`
4. `language/semantic_decision_source_validation.py`
5. `language/semantic_decision_analysis.py`
6. `language/semantic_decision_project_analysis.py`
7. `tooling/project_loader.py`
8. `tooling/cli.py`
9. `language_server/diagnostics.py`

H itself adds only the final integration smoke test and this document.

## Final acceptance matrix

H proves:

- exact A-through-G freeze tag targets and ancestry;
- real `.apex` semantic-decision file acceptance;
- deterministic parse/lower/validate/analyze composition;
- exact P11.10 candidate and convergence-policy object reuse;
- manifest-ordered multi-source project composition;
- deterministic rejection of cross-source duplicate decision identities;
- real repository CLI-wrapper acceptance;
- deterministic CLI behavior;
- CLI/LSP semantic-decision diagnostic-code equivalence;
- deterministic document-local LSP diagnostics;
- AIR source-family isolation;
- narrative source-family isolation;
- no condition evaluation;
- no convergence construction/resolution;
- no Paradox assessment/elevation;
- no P11.10 validation ownership;
- no runtime execution.

## Boundary after freeze

After P11-SRC-H freezes, the Semantic Decision Source-Surface Bridge is closed.

The next corrective bridge is P11-TAM â€” Compiler Token Analysis Map
Foundation. TAM consumes and records canonical compiler/source provenance; it
must not reconstruct or replace the frozen semantic-decision behavior
established by P11.10 and P11-SRC.