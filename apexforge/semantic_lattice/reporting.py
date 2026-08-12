"""P11.8G deterministic read-only semantic-lattice reporting projections.

Reporting consumes frozen P11.8F validation receipts. It does not validate,
construct, execute, resolve, rank, authorize, import, load, or mutate semantic
state. Existing runtime and narrative reporting surfaces remain separate.
"""

from __future__ import annotations

import json
from typing import Any, Tuple

from .validation import (
    SemanticLatticeAuthoringValidationReceipt,
    SemanticLatticeValidationReceipt,
)


REPORT_HEADING = "APEXFORGE SEMANTIC LATTICE REPORT"
REPORT_END = "END SEMANTIC LATTICE REPORT"
AUTHORING_REPORT_HEADING = "APEXFORGE SEMANTIC LATTICE AUTHORING REPORT"
AUTHORING_REPORT_END = "END SEMANTIC LATTICE AUTHORING REPORT"


def _render_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _identity_text(subject: object) -> str:
    return (
        f"{subject.source_domain}:{subject.source_kind}:"
        f"{_render_value(subject.source_identity)}"
    )


def _render_evidence(evidence: object) -> str:
    return (
        f"kind={evidence.kind}; "
        f"facts={_render_value(evidence.facts)}; "
        f"provenance={_render_value(evidence.provenance)}"
    )


def _append_section(lines: list[str], heading: str, values: Tuple[str, ...]) -> None:
    lines.append(heading)
    if not values:
        lines.append("<none>")
        return
    lines.extend(f"{index}. {value}" for index, value in enumerate(values, 1))


def render_semantic_lattice_validation_report(
    receipt: SemanticLatticeValidationReceipt,
) -> str:
    """Render one exact validated lattice receipt without revalidation or mutation."""

    if type(receipt) is not SemanticLatticeValidationReceipt:
        raise TypeError(
            "render_semantic_lattice_validation_report requires an exact "
            "SemanticLatticeValidationReceipt"
        )

    snapshot = receipt.snapshot
    lines = [REPORT_HEADING]

    _append_section(
        lines,
        "AXES",
        tuple(axis.canonical_id for axis in snapshot.lattice.axes),
    )
    _append_section(
        lines,
        "PARAMETERS",
        tuple(
            f"axis={parameter.axis_id}; key={parameter.key}; "
            f"value={_render_value(parameter.value)}"
            for parameter in snapshot.lattice.parameters
        ),
    )
    _append_section(
        lines,
        "SUBJECTS",
        tuple(_identity_text(subject) for subject in snapshot.subjects),
    )

    relationships = []
    for relationship in snapshot.relationships:
        evidence = tuple(_render_evidence(item) for item in relationship.evidence)
        relationships.append(
            f"source={_identity_text(relationship.source)}; "
            f"relation={relationship.relation}; "
            f"target={_identity_text(relationship.target)}; "
            f"evidence={_render_value(evidence)}"
        )
    _append_section(lines, "RELATIONSHIPS", tuple(relationships))
    _append_section(lines, "EXTENSION AXES", receipt.extension_axis_ids)
    _append_section(lines, "PROVENANCE", receipt.provenance)
    _append_section(lines, "CHECKS", receipt.checks)
    lines.append(REPORT_END)
    return "\n".join(lines)


def render_semantic_lattice_authoring_validation_report(
    receipt: SemanticLatticeAuthoringValidationReceipt,
) -> str:
    """Render authoring provenance plus the ordinary validated lattice report."""

    if type(receipt) is not SemanticLatticeAuthoringValidationReceipt:
        raise TypeError(
            "render_semantic_lattice_authoring_validation_report requires an exact "
            "SemanticLatticeAuthoringValidationReceipt"
        )

    proposal = receipt.proposal
    lines = [
        AUTHORING_REPORT_HEADING,
        f"source={proposal.source.value}",
        f"author_identity={proposal.author_identity}",
        f"provider_identity={proposal.provider_identity}",
        render_semantic_lattice_validation_report(receipt.snapshot_receipt),
        AUTHORING_REPORT_END,
    ]
    return "\n".join(lines)


__all__ = (
    "AUTHORING_REPORT_END",
    "AUTHORING_REPORT_HEADING",
    "REPORT_END",
    "REPORT_HEADING",
    "render_semantic_lattice_authoring_validation_report",
    "render_semantic_lattice_validation_report",
)
