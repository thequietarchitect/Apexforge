"""Deterministic human-readable reports for narrative source analyses."""

from __future__ import annotations

from typing import Iterable

from language.narrative_analysis import NarrativeSourceAnalysis
from language.narrative_model import NarrativeIdentity


__all__ = ("render_narrative_analysis_report",)


def _identity_text(identity: NarrativeIdentity) -> str:
    return f"{identity.kind}:{'.'.join(identity.path)}"


def _identity_list(
    identities: Iterable[NarrativeIdentity],
) -> str:
    rendered = tuple(_identity_text(identity) for identity in identities)
    if not rendered:
        return "(none)"
    return ", ".join(rendered)


def _index_list(indexes: Iterable[int]) -> str:
    rendered = tuple(str(index) for index in indexes)
    if not rendered:
        return "(none)"
    return ", ".join(rendered)


def _evidence_text(
    evidence: Iterable[tuple[str, str]],
) -> str:
    rendered = tuple(
        f"{key}={value}"
        for key, value in evidence
    )
    if not rendered:
        return "(none)"
    return "; ".join(rendered)


def _append_semantic_family(
    lines: list[str],
    label: str,
    records: tuple[object, ...],
) -> None:
    identities = tuple(record.identity for record in records)
    lines.append(
        f"  {label} ({len(identities)}): "
        f"{_identity_list(identities)}"
    )


def render_narrative_analysis_report(
    analysis: NarrativeSourceAnalysis,
) -> str:
    """Render one exact analysis without re-analysis or mutation."""

    if type(analysis) is not NarrativeSourceAnalysis:
        raise TypeError(
            "render_narrative_analysis_report requires an exact "
            "NarrativeSourceAnalysis."
        )

    source_story = analysis.source_document.story
    semantic_story = analysis.semantic_story
    graph = analysis.semantic_graph
    validation = analysis.validation_report

    lines: list[str] = [
        "ApexForge Narrative Analysis Report",
        "",
        "SOURCE SUMMARY",
        f"  source: {analysis.source_document.span.source_name}",
        f"  story: {source_story.name.text}",
        f"  start: {source_story.span.render_start()}",
        f"  characters: {len(source_story.characters)}",
        f"  scenes: {len(source_story.scenes)}",
        f"  dialogues: {len(source_story.dialogues)}",
        f"  choices: {len(source_story.choices)}",
        f"  perspectives: {len(source_story.perspectives)}",
        f"  timelines: {len(source_story.timelines)}",
        f"  narrative-states: {len(source_story.states)}",
        f"  continuities: {len(source_story.continuities)}",
        "",
        "SEMANTIC SUMMARY",
        f"  story: {_identity_text(semantic_story.identity)}",
    ]

    _append_semantic_family(
        lines,
        "characters",
        semantic_story.characters,
    )
    _append_semantic_family(
        lines,
        "scenes",
        semantic_story.scenes,
    )
    _append_semantic_family(
        lines,
        "dialogues",
        semantic_story.dialogues,
    )
    _append_semantic_family(
        lines,
        "choices",
        semantic_story.choices,
    )
    _append_semantic_family(
        lines,
        "perspectives",
        semantic_story.perspectives,
    )
    _append_semantic_family(
        lines,
        "timelines",
        semantic_story.timelines,
    )
    _append_semantic_family(
        lines,
        "narrative-states",
        semantic_story.states,
    )
    _append_semantic_family(
        lines,
        "continuities",
        semantic_story.continuities,
    )

    lines.extend(("", "GRAPH NODES"))
    if graph.nodes:
        for index, node in enumerate(graph.nodes):
            state = "declared" if node.declared else "referenced-only"
            lines.append(
                f"  {index}: {_identity_text(node.identity)} [{state}]"
            )
    else:
        lines.append("  (none)")

    lines.extend(("", "GRAPH EDGES"))
    if graph.edges:
        for index, edge in enumerate(graph.edges):
            lines.append(
                f"  {index}: {edge.relation} "
                f"{_identity_text(edge.source)} -> "
                f"{_identity_text(edge.target)}"
            )
            lines.append(
                f"    evidence: {_evidence_text(edge.evidence)}"
            )
    else:
        lines.append("  (none)")

    lines.extend(("", "VALIDATION FINDINGS"))
    if validation.findings:
        for index, finding in enumerate(validation.findings):
            lines.append(f"  {index}: {finding.classification}")
            lines.append(
                f"    identities: "
                f"{_identity_list(finding.identities)}"
            )
            lines.append(
                f"    node-indexes: "
                f"{_index_list(finding.node_indexes)}"
            )
            lines.append(
                f"    edge-indexes: "
                f"{_index_list(finding.edge_indexes)}"
            )
            lines.append(
                f"    evidence: "
                f"{_evidence_text(finding.evidence)}"
            )
    else:
        lines.append("  (none)")

    return "\n".join(lines)
