"""P11.9H deterministic read-only AETHER-AIR downstream projection reporting."""

from __future__ import annotations

import json
from typing import Any, Tuple

from .projection import AetherAirDownstreamProjection
from .validation import (
    AetherAirTransformationValidationReceipt,
    AetherAirValidationReceipt,
)


REPORT_HEADING = "APEXFORGE AETHER-AIR DOWNSTREAM PROJECTION REPORT"
REPORT_END = "END AETHER-AIR DOWNSTREAM PROJECTION REPORT"


def _render_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def _append_section(
    lines: list[str],
    heading: str,
    values: Tuple[str, ...],
) -> None:
    lines.append(heading)
    if not values:
        lines.append("<none>")
        return
    lines.extend(f"{index}. {value}" for index, value in enumerate(values, 1))


def _behavior_text(behavior: object) -> str:
    parameters = tuple(
        (parameter.key, parameter.value)
        for parameter in behavior.parameters
    )
    return (
        f"kind={behavior.kind_id}; "
        f"intent={_render_value(behavior.intent)}; "
        f"parameters={_render_value(parameters)}"
)


def _evidence_text(evidence: object) -> str:
    return (
        f"kind={evidence.kind}; "
        f"facts={_render_value(evidence.facts)}; "
        f"provenance={_render_value(evidence.provenance)}"
)


def _intent_index(snapshot: object, intent: object) -> int:
    return next(
        (
            index
            for index, behavior in enumerate(
                snapshot.representation.behaviors,
                1,
            )
            if behavior is intent
        ),
        0,
    )


def _append_traces(lines: list[str], snapshot: object) -> None:
    lines.append("TRACES")
    if not snapshot.traces:
        lines.append("<none>")
        return
    for trace_index, trace in enumerate(snapshot.traces, 1):
        predecessor = trace.predecessor
        lines.append(
            f"{trace_index}. "
            f"predecessor={predecessor.source_domain}:"
            f"{predecessor.source_kind}:"
            f"{_render_value(predecessor.source_identity)}; "
            f"intent_index={_intent_index(snapshot, trace.intent)}"
)
        for evidence_index, evidence in enumerate(trace.evidence, 1):
            lines.append(
                f"  evidence {evidence_index}. {_evidence_text(evidence)}"
)


def _append_snapshot_validation(
    lines: list[str],
    receipt: AetherAirValidationReceipt,
) -> None:
    snapshot = receipt.snapshot
    _append_section(
        lines,
        "BEHAVIORS",
        tuple(
            _behavior_text(behavior)
            for behavior in snapshot.representation.behaviors
        ),
    )
    _append_traces(lines, snapshot)
    _append_section(lines, "EXTENSION KINDS", receipt.extension_kind_ids)
    _append_section(lines, "VALIDATION PROVENANCE", receipt.provenance)
    _append_section(lines, "CHECKS", receipt.checks)


def _append_transformation_validation(
    lines: list[str],
    receipt: AetherAirTransformationValidationReceipt,
) -> None:
    transformation = receipt.transformation
    lines.extend((
        "TRANSFORMATION",
        f"operation={transformation.operation}",
    ))
    _append_section(
        lines,
        "TRANSFORMATION PROVENANCE",
        transformation.provenance,
    )
    lines.append("SOURCE SNAPSHOT")
    _append_snapshot_validation(lines, receipt.source_receipt)
    lines.append("RESULT SNAPSHOT")
    _append_snapshot_validation(lines, receipt.result_receipt)
    _append_section(lines, "TRANSFORMATION CHECKS", receipt.checks)


def render_aether_air_downstream_projection_report(
    projection: AetherAirDownstreamProjection,
) -> str:
    """Render one exact frozen downstream projection without semantic action."""

    if type(projection) is not AetherAirDownstreamProjection:
        raise TypeError(
            "render_aether_air_downstream_projection_report requires an exact "
            "AetherAirDownstreamProjection"
)

    lines = [
        REPORT_HEADING,
        "CONSUMER",
        projection.consumer,
    ]
    _append_section(
        lines,
        "PROJECTION PROVENANCE",
        projection.provenance,
    )

    validation = projection.validation
    lines.append("VALIDATION")
    if type(validation) is AetherAirValidationReceipt:
        lines.append("snapshot")
        _append_snapshot_validation(lines, validation)
    elif type(validation) is AetherAirTransformationValidationReceipt:
        lines.append("transformation")
        _append_transformation_validation(lines, validation)
    else:
        raise TypeError(
            "projection validation is not an exact frozen P11.9F receipt"
)

    lines.append(REPORT_END)
    return "\n".join(lines)


__all__ = ("render_aether_air_downstream_projection_report",)
