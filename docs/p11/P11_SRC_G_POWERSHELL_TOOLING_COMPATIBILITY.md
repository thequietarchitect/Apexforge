# P11-SRC-G - PowerShell and Tooling Compatibility

## Current candidate

This candidate connects the frozen P11-SRC-F semantic-decision analysis surface
to `apexforge check`.

It does not make the ordinary AIR compiler own semantic-decision syntax.

## Project classification

`tooling.project_loader` recognizes three project kinds:

- `air`
- `narrative`
- `semantic_decision`

The live predecessor already classifies a project as narrative when the project
contains at least one source and every declared source is recognized as
narrative.

G mirrors that established all-source rule for semantic-decision documents.

Classification order is:

1. all sources narrative -> `narrative`;
2. otherwise, all sources semantic-decision -> `semantic_decision`;
3. every other project -> `air`.

This preserves mixed-source projects at the existing AIR boundary.

Malformed text beginning with the exact `decision` source form remains
semantic-decision-classified so its semantic-decision parser owns diagnostics.

## `apexforge check`

Narrative behavior is unchanged.

For a semantic-decision project, `_run_check` analyzes each loaded source in
canonical manifest/source order through the frozen
`analyze_semantic_decision_source` API.

AIR projects retain the existing `ProjectBuilder` path.

All failures continue through the existing `CLIProjectCheckError` boundary and
therefore retain `EXIT_CHECK = 20`.

Successful checks retain the generic output:

`ApexForge check passed: NAME (N source(s)).`

## PowerShell/process acceptance

The focused smoke test exercises:

- in-process `tooling.cli.main(("check", project))`;
- a multi-source semantic-decision project;
- malformed semantic-decision diagnostics;
- ordinary AIR through an injected ProjectBuilder;
- narrative source-family preservation;
- mixed-source AIR fallback;
- the repository `apexforge_cli.py check PROJECT` wrapper in a child process.

The child-process wrapper is the process boundary used from PowerShell.

## Semantic boundary

G delegates all semantic-decision source work to frozen P11-SRC-F.

G performs no condition evaluation, convergence construction or resolution,
Paradox assessment/elevation, P11.10 validation, projection, or runtime
execution.

## Deliberately unchanged in this candidate

No changes are made to:

- `language.compiler`;
- `language.project`;
- shared AIR lexer/parser behavior;
- narrative production modules;
- frozen P11-SRC-B through F modules;
- frozen P11.10;
- runtime execution;
- build artifact formats.

Language-server/editor compatibility remains a separate G gate before freeze.

## Project-wide semantic-decision analysis

The PowerShell/tooling gate exposed one project-level gap: independent
per-source analysis allowed two files to declare the same semantic-decision
identity.

G therefore adds `language.semantic_decision_project_analysis` as a thin,
manifest-ordered composition layer over the frozen P11-SRC-F analysis API.

It does not merge or reinterpret P11.10 semantic objects. It preserves the
exact per-source F analysis products and adds only cross-source decision
identity uniqueness.

A duplicate project identity raises the source-aware
`APX-SEMANTIC-DECISION-PROJECT` diagnostic at link stage. The second
declaration is the primary span and the first declaration is retained as a
related span.

## Language-server diagnostics compatibility

`language_server.diagnostics.analyze_document` now recognizes
semantic-decision documents and delegates them to the frozen P11-SRC-F
analysis entry point before the existing AIR/module fallback.

This makes valid semantic-decision documents diagnostic-clean in the LSP and
maps malformed semantic-decision source through the existing
`diagnostics_from_exception` and `diagnostic_to_lsp` path.

No new LSP capability is advertised. Hover, completion, definition,
references, rename, symbols, formatting, and workspace indexing retain their
existing ownership. G adds semantic-decision diagnostics compatibility only.

Cross-file semantic-decision identity validation remains a project/CLI
responsibility because the current diagnostics entry point is document-local
and the frozen language-server contract does not expose a semantic project
workspace composition seam.

## Final G boundary

P11-SRC-G now owns:

- project-kind recognition for semantic-decision source families;
- PowerShell/CLI `check` routing;
- manifest-ordered semantic-decision project analysis;
- deterministic cross-source decision identity rejection; and
- document-local LSP semantic-decision diagnostics.

It still does not own AIR compilation, runtime execution, convergence
resolution, condition evaluation, Paradox assessment/elevation, P11.10
validation, or semantic projection.
