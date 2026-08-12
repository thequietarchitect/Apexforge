"""P11.8F semantic-lattice validation, collision, provenance, and extension contracts.

P11.8D remains authoritative for snapshot structural construction: exact canonical
types, duplicate exact subjects, and relationship endpoint closure.  This module
adds passive validation over an already-constructed snapshot and never executes,
ranks, resolves, grants, imports, or mutates semantic state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .authoring import (
    SemanticLatticeAuthoringProposal,
    SemanticLatticeAuthoringSource,
    adapt_codex_semantic_lattice_proposal,
    adapt_semantic_lattice_authoring_proposal,
)
from .construction import SemanticLatticeSnapshot
from .model import CORE_SEMANTIC_LATTICE_AXES
from .records import SemanticLatticeEvidence


def _exact_tuple(value: object, *, owner: str) -> tuple:
    if type(value) is not tuple:
        raise TypeError(f"{owner} must be an exact tuple")
    return value


def _subject_coordinate(subject: object) -> Tuple[str, Tuple[str, ...]]:
    return (subject.source_domain, subject.source_identity)


def _relationship_coordinate(relationship: object) -> tuple:
    return (relationship.source, relationship.relation, relationship.target)


def _evidence_coordinate(evidence: SemanticLatticeEvidence) -> tuple:
    return (evidence.kind, evidence.facts, evidence.provenance)


@dataclass(frozen=True)
class SemanticLatticeValidationReceipt:
    """Immutable passive receipt for one validated canonical snapshot."""

    snapshot: SemanticLatticeSnapshot
    extension_axis_ids: Tuple[str, ...]
    provenance: Tuple[str, ...]
    checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.snapshot) is not SemanticLatticeSnapshot:
            raise TypeError("snapshot must be an exact SemanticLatticeSnapshot")
        for name, value in (
            ("extension_axis_ids", self.extension_axis_ids),
            ("provenance", self.provenance),
            ("checks", self.checks),
        ):
            _exact_tuple(value, owner=name)
            if any(type(item) is not str or not item.strip() for item in value):
                raise ValueError(f"{name} entries must be non-empty strings")


@dataclass(frozen=True)
class SemanticLatticeAuthoringValidationReceipt:
    """Validation receipt preserving neutral authoring provenance."""

    proposal: SemanticLatticeAuthoringProposal
    snapshot_receipt: SemanticLatticeValidationReceipt

    def __post_init__(self) -> None:
        if type(self.proposal) is not SemanticLatticeAuthoringProposal:
            raise TypeError("proposal must be an exact SemanticLatticeAuthoringProposal")
        if type(self.snapshot_receipt) is not SemanticLatticeValidationReceipt:
            raise TypeError(
                "snapshot_receipt must be an exact SemanticLatticeValidationReceipt"
            )


def validate_semantic_lattice_snapshot(
    snapshot: SemanticLatticeSnapshot,
) -> SemanticLatticeValidationReceipt:
    """Validate passive cross-record, provenance, and extension invariants.

    The input must already be a P11.8D snapshot.  This function deliberately does
    not recreate D's exact-subject or endpoint-closure checks.
    """

    if type(snapshot) is not SemanticLatticeSnapshot:
        raise TypeError("snapshot must be an exact SemanticLatticeSnapshot")

    axis_ids = tuple(axis.canonical_id for axis in snapshot.lattice.axes)
    if len(set(axis_ids)) != len(axis_ids):
        raise ValueError("duplicate semantic lattice axis canonical_id")

    declared_axes = set(axis_ids)
    parameter_coordinates = set()
    for parameter in snapshot.lattice.parameters:
        if parameter.axis_id not in declared_axes:
            raise ValueError(
                "semantic lattice parameter axis_id must reference a declared axis"
            )
        coordinate = (parameter.axis_id, parameter.key)
        if coordinate in parameter_coordinates:
            raise ValueError("duplicate semantic lattice parameter coordinate")
        parameter_coordinates.add(coordinate)

    source_identity_kinds = {}
    for subject in snapshot.subjects:
        coordinate = _subject_coordinate(subject)
        previous_kind = source_identity_kinds.get(coordinate)
        if previous_kind is not None and previous_kind != subject.source_kind:
            raise ValueError(
                "source-owned semantic identity collides across subject kinds"
            )
        source_identity_kinds[coordinate] = subject.source_kind

    relationship_coordinates = set()
    provenance = []
    for relationship in snapshot.relationships:
        coordinate = _relationship_coordinate(relationship)
        if coordinate in relationship_coordinates:
            raise ValueError("duplicate semantic lattice relationship coordinate")
        relationship_coordinates.add(coordinate)

        evidence_coordinates = set()
        for evidence in relationship.evidence:
            evidence_coordinate = _evidence_coordinate(evidence)
            if evidence_coordinate in evidence_coordinates:
                raise ValueError(
                    "duplicate semantic lattice evidence coordinate in relationship"
                )
            evidence_coordinates.add(evidence_coordinate)
            if len(set(evidence.provenance)) != len(evidence.provenance):
                raise ValueError(
                    "semantic lattice evidence provenance contains duplicate entries"
                )
            provenance.extend(evidence.provenance)

    core_ids = tuple(axis.canonical_id for axis in CORE_SEMANTIC_LATTICE_AXES)
    core_id_set = set(core_ids)
    if any(core_id not in declared_axes for core_id in core_ids):
        raise ValueError("semantic lattice snapshot omits a canonical core axis")
    extension_axis_ids = tuple(
        axis_id for axis_id in axis_ids if axis_id not in core_id_set
    )

    checks = (
        "axis-coordinate-integrity",
        "parameter-axis-closure",
        "parameter-coordinate-collision",
        "source-identity-kind-collision",
        "relationship-coordinate-collision",
        "evidence-coordinate-collision",
        "provenance-integrity",
        "extension-axis-preservation",
    )
    return SemanticLatticeValidationReceipt(
        snapshot=snapshot,
        extension_axis_ids=extension_axis_ids,
        provenance=tuple(provenance),
        checks=checks,
    )


def validate_semantic_lattice_authoring_proposal(
    proposal: SemanticLatticeAuthoringProposal,
) -> SemanticLatticeAuthoringValidationReceipt:
    """Validate a neutral authoring proposal through the ordinary P11.8E/D path."""

    if type(proposal) is not SemanticLatticeAuthoringProposal:
        raise TypeError("proposal must be an exact SemanticLatticeAuthoringProposal")
    snapshot = adapt_semantic_lattice_authoring_proposal(proposal)
    return SemanticLatticeAuthoringValidationReceipt(
        proposal=proposal,
        snapshot_receipt=validate_semantic_lattice_snapshot(snapshot),
    )


def validate_codex_semantic_lattice_proposal(
    proposal: SemanticLatticeAuthoringProposal,
) -> SemanticLatticeAuthoringValidationReceipt:
    """Validate Codex only as the frozen P11.8E advisory provider."""

    if type(proposal) is not SemanticLatticeAuthoringProposal:
        raise TypeError("proposal must be an exact SemanticLatticeAuthoringProposal")
    if proposal.source is not SemanticLatticeAuthoringSource.ADVISORY:
        raise ValueError("Codex validation requires advisory authoring source")
    if proposal.provider_identity != "codex":
        raise ValueError("Codex validation requires provider_identity 'codex'")
    snapshot = adapt_codex_semantic_lattice_proposal(proposal)
    return SemanticLatticeAuthoringValidationReceipt(
        proposal=proposal,
        snapshot_receipt=validate_semantic_lattice_snapshot(snapshot),
    )


__all__ = (
    "SemanticLatticeAuthoringValidationReceipt",
    "SemanticLatticeValidationReceipt",
    "validate_codex_semantic_lattice_proposal",
    "validate_semantic_lattice_authoring_proposal",
    "validate_semantic_lattice_snapshot",
)
