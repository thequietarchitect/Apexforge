# P11.5I-B Narrative Analysis Result Reporting Contract

## Status

P11.5I-B is based on the annotated P11.5H freeze
`afp-p11.5h-freeze`, resolving to:

`f9af32adb5cf56a5d78f6bcd59ed4ecc70c933c1`

The reviewed candidate owns exactly five files:

1. `apexforge/tools/narrative_report.py`
2. `apexforge/p11_5i_narrative_analysis_result_reporting_architecture_audit_smoke_test.py`
3. `apexforge/p11_5i_narrative_analysis_result_reporting_smoke_test.py`
4. `docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_ARCHITECTURE_AUDIT.md`
5. `docs/p11/P11_5I_NARRATIVE_ANALYSIS_RESULT_REPORTING_CONTRACT.md`

## Purpose

P11.5I-B adds one deterministic human-readable projection over one already
completed `NarrativeSourceAnalysis`.

Reporting != serialization.

Reporting != execution.

## Public API

`apexforge/tools/narrative_report.py` exports exactly:

- `render_narrative_analysis_report`

The function requires one exact `NarrativeSourceAnalysis` and returns one exact
`str`.

## Canonical sections

The report renders these sections in fixed order:

1. `ApexForge Narrative Analysis Report`
2. `SOURCE SUMMARY`
3. `SEMANTIC SUMMARY`
4. `GRAPH NODES`
5. `GRAPH EDGES`
6. `VALIDATION FINDINGS`

The output has no trailing whitespace and no trailing newline.

## Source summary

The source section reports:

- source name
- story name
- story start location
- counts for every source declaration family

The report does not reconstruct source text or source-form quoting.

## Semantic summary

The semantic section reports the canonical story identity and every declaration
family in frozen tuple order.

Duplicate declarations remain duplicated.

Empty families use `(none)`.

## Identity display

Every identity is rendered as:

`<kind>:<path>`

Path segments are joined by `.` without case conversion, alias resolution, or
qualification.

## Graph projection

Nodes are rendered in exact graph-node order with either `declared` or
`referenced-only`.

Edges are rendered in exact graph-edge order with:

- relation
- source identity
- target identity
- every ordered evidence key/value pair

No traversal, sorting, merging, or deduplication occurs.

## Validation projection

Findings are rendered in exact report order with:

- classification
- ordered identities
- node indexes
- edge indexes
- ordered evidence key/value pairs

Empty collections use `(none)`.

Validation findings remain passive and are not converted to diagnostics,
exceptions, warnings, or exit codes.

## Determinism and mutation

Value-equal analyses produce byte-identical reports.

Rendering performs no re-analysis and does not mutate any source, semantic,
graph, validation, or analysis product.

## Failure contract

Any value whose exact type is not `NarrativeSourceAnalysis` raises `TypeError`.

No reporting-specific exception or diagnostic is added.

## Compatibility boundary

P11.5I-B changes no frozen narrative module and adds no:

- serialization
- deserialization
- file writing
- CLI integration
- compiler integration
- project integration
- AIR integration
- artifact integration
- runtime integration
- language-server integration
- VS Code integration
- Visual Studio integration
- syntax highlighting

## Acceptance contract

P11.5I-B passes when:

- the annotated P11.5H freeze remains authoritative
- exactly five reviewed files are owned
- the reporter exposes exactly one public function
- the canonical empty report matches exactly
- source, semantic, graph, and validation order is preserved
- duplicate and referenced-only evidence remains visible
- node indexes, edge indexes, and ordered evidence are rendered
- rendering is deterministic and mutation-free
- all frozen narrative and operational surfaces remain unchanged
- tests do not mutate repository state
