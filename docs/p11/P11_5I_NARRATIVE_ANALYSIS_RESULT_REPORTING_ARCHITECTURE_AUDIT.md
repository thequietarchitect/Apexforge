# P11.5I-A Narrative Analysis Result Reporting Architecture Audit

## Status

P11.5H is the frozen analysis-pipeline predecessor.

The controlling annotated tag is `afp-p11.5h-freeze`, resolving to:

`f9af32adb5cf56a5d78f6bcd59ed4ecc70c933c1`

The original audit established the reporting boundary. The reviewed P11.5I-B
successor now implements it through one dedicated production module.

## Core boundary

Reporting != serialization.

Reporting != execution.

## Production boundary

P11.5I-B adds one dedicated production module:

`apexforge/tools/narrative_report.py`

It publicly exports exactly:

- `render_narrative_analysis_report`

The function accepts one exact NarrativeSourceAnalysis and returns one
deterministic human-readable report.

## Canonical projection

The report renders, in fixed order:

1. source summary
2. semantic summary
3. graph nodes
4. graph edges
5. validation findings

Source order, graph order, and finding order are preserved.

Identity display uses `<kind>:<path>`.

Canonical empty markers use `(none)`.

Graph edge evidence and validation identity, node-index, edge-index, and
evidence tuples are rendered in stored order.

## Purity

There is no re-analysis.

There is no mutation.

There is no diagnostic conversion.

The reporter does not parse, lower, build, validate, execute, serialize, write
files, or query the environment.

## Compatibility boundary

No changes to language/narrative_analysis.py.

No changes to language/narrative_validation.py.

There is:

- no serialization
- no CLI integration
- no compiler integration
- no project integration
- no AIR or artifact integration
- no runtime integration
- no language-server integration
- no VS Code integration
- no Visual Studio integration

## Acceptance contract

The reviewed P11.5I-A/P11.5I-B candidate passes when:

- the annotated P11.5H freeze remains authoritative
- exactly five reviewed files are owned
- one pure reporting function is exposed
- the deterministic human-readable report has fixed sections
- source, semantic, graph, and validation order is preserved
- identity display, ordered evidence, and canonical empty markers are stable
- rendering performs no mutation or re-analysis
- frozen narrative and operational surfaces remain unchanged
- tests do not mutate repository state
