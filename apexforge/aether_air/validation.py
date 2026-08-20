"""P11.9F passive AETHER-AIR validation, collision, closure, and extension contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .construction import AetherAirSnapshot
from .model import AetherBehaviorKind, CORE_AETHER_BEHAVIOR_KINDS
from .transformation import AetherAirTransformation


def _text_tuple(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    for index, item in enumerate(value):
        if type(item) is not str:
            raise TypeError(f"{field}[{index}] must be an exact str")
        if not item or item != item.strip():
            raise ValueError(f"{field}[{index}] must be non-empty and trimmed")


def _contains_equal(values: object, candidate: object) -> bool:
    return any(item == candidate for item in values)


def _contains_identity(values: object, candidate: object) -> bool:
    return any(item is candidate for item in values)


def _has_duplicate(values: object) -> bool:
    seen = []
    for value in values:
        if _contains_equal(seen, value):
            return True
        seen.append(value)
    return False


def _extension_kind_ids(
    extension_kinds: Tuple[AetherBehaviorKind, ...],
) -> Tuple[str, ...]:
    if type(extension_kinds) is not tuple:
        raise TypeError("extension_kinds must be an exact tuple")

    ids = []
    core_ids = tuple(kind.canonical_id for kind in CORE_AETHER_BEHAVIOR_KINDS)

    for item in extension_kinds:
        if type(item) is not AetherBehaviorKind:
            raise TypeError(
                "extension_kinds must contain exact AetherBehaviorKind values"
)
        if item.canonical_id in core_ids:
            raise ValueError("AETHER-AIR extension kind collides with a core behavior kind")
        if item.canonical_id in ids:
            raise ValueError("duplicate AETHER-AIR extension kind declaration")
        ids.append(item.canonical_id)

    return tuple(ids)


@dataclass(frozen=True)
class AetherAirValidationReceipt:
    """Immutable passive receipt for one validated AETHER-AIR snapshot."""

    snapshot: AetherAirSnapshot
    extension_kind_ids: Tuple[str, ...] = ()
    provenance: Tuple[str, ...] = ()
    checks: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.snapshot) is not AetherAirSnapshot:
            raise TypeError("snapshot must be an exact AetherAirSnapshot")
        _text_tuple(self.extension_kind_ids, "extension_kind_ids")
        _text_tuple(self.provenance, "provenance")
        _text_tuple(self.checks, "checks")


@dataclass(frozen=True)
class AetherAirTransformationValidationReceipt:
    """Immutable passive receipt for one validated AETHER-AIR transformation."""

    transformation: AetherAirTransformation
    source_receipt: AetherAirValidationReceipt
    result_receipt: AetherAirValidationReceipt
    checks: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.transformation) is not AetherAirTransformation:
            raise TypeError(
                "transformation must be an exact AetherAirTransformation"
)
        if type(self.source_receipt) is not AetherAirValidationReceipt:
            raise TypeError(
                "source_receipt must be an exact AetherAirValidationReceipt"
)
        if type(self.result_receipt) is not AetherAirValidationReceipt:
            raise TypeError(
                "result_receipt must be an exact AetherAirValidationReceipt"
)
        _text_tuple(self.checks, "checks")


def validate_aether_air_snapshot(
    snapshot: AetherAirSnapshot,
    *,
    extension_kinds: Tuple[AetherBehaviorKind, ...] = (),
) -> AetherAirValidationReceipt:
    """Validate passive structural integrity without resolving semantic outcomes."""

    if type(snapshot) is not AetherAirSnapshot:
        raise TypeError("snapshot must be an exact AetherAirSnapshot")

    declared_extension_ids = _extension_kind_ids(extension_kinds)
    core_kind_ids = tuple(
        kind.canonical_id for kind in CORE_AETHER_BEHAVIOR_KINDS
)

    behaviors = snapshot.representation.behaviors
    traces = snapshot.traces

    if _has_duplicate(behaviors):
        raise ValueError("duplicate AETHER-AIR behavior intent")

    for behavior in behaviors:
        if (
            behavior.kind_id not in core_kind_ids
            and behavior.kind_id not in declared_extension_ids
):
            raise ValueError("undeclared AETHER-AIR extension behavior kind")

    if _has_duplicate(traces):
        raise ValueError("duplicate AETHER-AIR intent trace")

    predecessor_kinds = []
    provenance = []

    for trace in traces:
        if not _contains_identity(behaviors, trace.intent):
            raise ValueError(
                "AETHER-AIR trace intent is not closed over exact representation behavior objects"
)

        predecessor_coordinate = (
            trace.predecessor.source_domain,
            trace.predecessor.source_identity,
        )
        existing_kind = None
        for coordinate, source_kind in predecessor_kinds:
            if coordinate == predecessor_coordinate:
                existing_kind = source_kind
                break

        if (
            existing_kind is not None
            and existing_kind != trace.predecessor.source_kind
):
            raise ValueError(
                "AETHER-AIR predecessor identity collision across source kinds"
)

        if existing_kind is None:
            predecessor_kinds.append(
                (predecessor_coordinate, trace.predecessor.source_kind)
)

        if _has_duplicate(trace.evidence):
            raise ValueError(
                "duplicate AETHER-AIR evidence coordinate in intent trace"
)

        for evidence in trace.evidence:
            if _has_duplicate(evidence.provenance):
                raise ValueError(
                    "AETHER-AIR evidence provenance contains duplicate entries"
)
            provenance.extend(evidence.provenance)

    return AetherAirValidationReceipt(
        snapshot=snapshot,
        extension_kind_ids=declared_extension_ids,
        provenance=tuple(provenance),
        checks=(
            "behavior-intent-collision",
            "intent-trace-collision",
            "trace-intent-closure",
            "predecessor-identity-kind-collision",
            "trace-evidence-collision",
            "evidence-provenance-integrity",
            "extension-kind-collision",
            "extension-kind-closure",
        ),
    )


def validate_aether_air_transformation(
    transformation: AetherAirTransformation,
    *,
    extension_kinds: Tuple[AetherBehaviorKind, ...] = (),
) -> AetherAirTransformationValidationReceipt:
    """Validate source/result structural integrity without selecting outcomes."""

    if type(transformation) is not AetherAirTransformation:
        raise TypeError(
            "transformation must be an exact AetherAirTransformation"
)

    source_receipt = validate_aether_air_snapshot(
        transformation.source,
        extension_kinds=extension_kinds,
    )
    result_receipt = validate_aether_air_snapshot(
        transformation.result,
        extension_kinds=extension_kinds,
    )

    if _has_duplicate(transformation.provenance):
        raise ValueError(
            "AETHER-AIR transformation provenance contains duplicate entries"
)

    if transformation.operation == "normalization":
        if (
            transformation.source.representation
            != transformation.result.representation
            or transformation.source.traces
            != transformation.result.traces
        ):
            raise ValueError(
                "AETHER-AIR normalization source/result canonical content disagrees"
)

    return AetherAirTransformationValidationReceipt(
        transformation=transformation,
        source_receipt=source_receipt,
        result_receipt=result_receipt,
        checks=(
            "source-validation",
            "result-validation",
            "transformation-provenance-integrity",
            "normalization-source-result-consistency",
        ),
    )


__all__ = (
    "AetherAirValidationReceipt",
    "AetherAirTransformationValidationReceipt",
    "validate_aether_air_snapshot",
    "validate_aether_air_transformation",
)
