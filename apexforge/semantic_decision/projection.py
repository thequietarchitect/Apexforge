"""P11.10H passive downstream projection over exact P11.10G validation receipts."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass
from typing import Tuple, Union

from .validation import (
    ElevatedSemanticStateValidationReceipt as _ElevatedSemanticStateValidationReceipt,
    ParadoxElevationValidationReceipt as _ParadoxElevationValidationReceipt,
    SemanticDecisionValidationReceipt as _SemanticDecisionValidationReceipt,
)


_ValidationReceipt = Union[
    _SemanticDecisionValidationReceipt,
    _ParadoxElevationValidationReceipt,
    _ElevatedSemanticStateValidationReceipt,
]

_SUPPORTED_RECEIPT_TYPES = (
    _SemanticDecisionValidationReceipt,
    _ParadoxElevationValidationReceipt,
    _ElevatedSemanticStateValidationReceipt,
)


def _text(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")


def _provenance(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    for index, item in enumerate(value):
        _text(item, f"{field}[{index}]")


def _receipt(value: object, field: str) -> None:
    if type(value) not in _SUPPORTED_RECEIPT_TYPES:
        raise TypeError(
            f"{field} must be an exact P11.10G semantic-decision validation receipt"
        )


@_dataclass(frozen=True)
class SemanticDecisionDownstreamProjection:
    """Immutable read-only projection preserving one exact G validation receipt."""

    validation: _ValidationReceipt
    consumer: str
    provenance: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _receipt(self.validation, "SemanticDecisionDownstreamProjection.validation")
        _text(self.consumer, "SemanticDecisionDownstreamProjection.consumer")
        _provenance(
            self.provenance,
            "SemanticDecisionDownstreamProjection.provenance",
        )


def project_validated_semantic_decision(
    validation: _ValidationReceipt,
    *,
    consumer: str,
    provenance: Tuple[str, ...] = (),
) -> SemanticDecisionDownstreamProjection:
    """Project one exact validated product without revalidation or semantic action."""

    _receipt(validation, "validation")
    _text(consumer, "consumer")
    _provenance(provenance, "provenance")
    return SemanticDecisionDownstreamProjection(
        validation=validation,
        consumer=consumer,
        provenance=provenance,
    )


__all__ = (
    "SemanticDecisionDownstreamProjection",
    "project_validated_semantic_decision",
)
