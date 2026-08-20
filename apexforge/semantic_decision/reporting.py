"""P11.10H deterministic observational reporting for semantic-decision projections."""

from __future__ import annotations

from typing import Any, Tuple

from .projection import SemanticDecisionDownstreamProjection as _SemanticDecisionDownstreamProjection
from .validation import (
    ElevatedSemanticStateValidationReceipt as _ElevatedSemanticStateValidationReceipt,
    ParadoxElevationValidationReceipt as _ParadoxElevationValidationReceipt,
    SemanticDecisionValidationReceipt as _SemanticDecisionValidationReceipt,
)


_REPORT_HEADING = "APEXFORGE SEMANTIC DECISION DOWNSTREAM PROJECTION REPORT"
_REPORT_END = "END SEMANTIC DECISION DOWNSTREAM PROJECTION REPORT"


def _render_value(value: Any) -> str:
    return repr(value)


def _append_values(lines: list, heading: str, values: Tuple[Any, ...]) -> None:
    lines.append(heading)
    if not values:
        lines.append("<none>")
        return
    for index, value in enumerate(values, 1):
        lines.append(f"{index}. {_render_value(value)}")


def _candidate_identities(values: tuple) -> tuple:
    return tuple(item.identity for item in values)


def _append_resolution_receipt(
    lines: list,
    receipt: _SemanticDecisionValidationReceipt,
) -> None:
    resolution = receipt.resolution
    convergence_set = resolution.convergence_set

    lines.append("VALIDATION TYPE")
    lines.append("semantic-decision-resolution")
    lines.append("POLICY")
    lines.append(convergence_set.policy.identity)
    lines.append("POLICY PARAMETERS")
    lines.append(_render_value(convergence_set.policy.parameters))

    lines.append("CANDIDATES")
    if not convergence_set.candidates:
        lines.append("<none>")
    else:
        for index, binding in enumerate(convergence_set.candidates, 1):
            lines.append(
                f"{index}. identity={_render_value(binding.candidate.identity)}; "
                f"state={_render_value(binding.evaluation.state_id)}"
            )

    _append_values(
        lines,
        "MEMBERS",
        _candidate_identities(
            tuple(item.candidate for item in convergence_set.members)
        ),
    )

    lines.append("RANKING")
    if not resolution.ranking:
        lines.append("<none>")
    else:
        for ranked in resolution.ranking:
            lines.append(
                f"{ranked.rank}. {_render_value(ranked.candidate.identity)}"
            )

    lines.append("OUTCOME KIND")
    lines.append(resolution.outcome.kind_id)
    _append_values(
        lines,
        "OUTCOME ALTERNATIVES",
        _candidate_identities(resolution.outcome.alternatives),
    )
    lines.append("OUTCOME PAYLOAD")
    lines.append(_render_value(resolution.outcome.payload))

    _append_values(
        lines,
        "EXTENSION ADMISSIBILITY STATES",
        receipt.extension_admissibility_state_ids,
    )
    _append_values(
        lines,
        "EXTENSION OUTCOME KINDS",
        receipt.extension_outcome_kind_ids,
    )
    _append_values(
        lines,
        "EXTENSION POLICIES",
        receipt.extension_policy_ids,
    )
    _append_values(lines, "VALIDATION PROVENANCE", receipt.provenance)
    _append_values(lines, "VALIDATION CHECKS", receipt.checks)


def _append_paradox_receipt(
    lines: list,
    receipt: _ParadoxElevationValidationReceipt,
) -> None:
    assessment = receipt.assessment
    evidence = assessment.evidence

    lines.append("VALIDATION TYPE")
    lines.append("paradox-elevation-assessment")
    lines.append("PARADOX ELIGIBLE")
    lines.append("true" if assessment.eligible else "false")
    lines.append("REDUCTION REQUIRES INFORMATION LOSS")
    lines.append(
        "true" if evidence.reduction_requires_information_loss else "false"
    )

    lines.append("INCOMPATIBILITY EVIDENCE")
    if not evidence.incompatibilities:
        lines.append("<none>")
    else:
        for index, item in enumerate(evidence.incompatibilities, 1):
            lines.append(
                f"{index}. left={_render_value(item.left.identity)}; "
                f"right={_render_value(item.right.identity)}; "
                f"materially_incompatible="
                f"{'true' if item.materially_incompatible else 'false'}"
            )

    lines.append("PARADOX CANDIDATE OUTCOME")
    if assessment.candidate_outcome is None:
        lines.append("<none>")
    else:
        lines.append(assessment.candidate_outcome.kind_id)
        _append_values(
            lines,
            "PARADOX CANDIDATE ALTERNATIVES",
            _candidate_identities(assessment.candidate_outcome.alternatives),
        )

    _append_values(lines, "PARADOX PROVENANCE", receipt.provenance)
    _append_values(lines, "PARADOX VALIDATION CHECKS", receipt.checks)
    lines.append("RESOLUTION RECEIPT")
    _append_resolution_receipt(lines, receipt.resolution_receipt)


def _append_elevated_receipt(
    lines: list,
    receipt: _ElevatedSemanticStateValidationReceipt,
) -> None:
    state = receipt.state
    lines.append("VALIDATION TYPE")
    lines.append("elevated-semantic-state")
    _append_values(
        lines,
        "ELEVATED ALTERNATIVES",
        _candidate_identities(state.alternatives),
    )
    _append_values(lines, "ELEVATED PROVENANCE", receipt.provenance)
    _append_values(lines, "ELEVATED VALIDATION CHECKS", receipt.checks)
    lines.append("ASSESSMENT RECEIPT")
    _append_paradox_receipt(lines, receipt.assessment_receipt)


def render_semantic_decision_downstream_projection_report(
    projection: _SemanticDecisionDownstreamProjection,
) -> str:
    """Render one exact H projection without revalidation or semantic recomputation."""

    if type(projection) is not _SemanticDecisionDownstreamProjection:
        raise TypeError(
            "render_semantic_decision_downstream_projection_report requires an exact "
            "SemanticDecisionDownstreamProjection"
        )

    lines = [
        _REPORT_HEADING,
        "CONSUMER",
        projection.consumer,
    ]
    _append_values(lines, "PROJECTION PROVENANCE", projection.provenance)

    validation = projection.validation
    if type(validation) is _SemanticDecisionValidationReceipt:
        _append_resolution_receipt(lines, validation)
    elif type(validation) is _ParadoxElevationValidationReceipt:
        _append_paradox_receipt(lines, validation)
    elif type(validation) is _ElevatedSemanticStateValidationReceipt:
        _append_elevated_receipt(lines, validation)
    else:
        raise TypeError(
            "projection validation is not an exact frozen P11.10G receipt"
        )

    lines.append(_REPORT_END)
    return "\n".join(lines)


__all__ = ("render_semantic_decision_downstream_projection_report",)
