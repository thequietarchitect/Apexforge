"""P11.8D deterministic Parametric Semantic Lattice construction and indexing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .model import ParametricSemanticLattice
from .records import (
    SemanticLatticeRelationship,
    SemanticLatticeSubjectReference,
)


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{field} must be an exact str")
    if not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty and trimmed")
    return value


@dataclass(frozen=True)
class SemanticLatticeSnapshot:
    """Immutable deterministic composition of lattice metadata and canonical records."""

    lattice: ParametricSemanticLattice
    subjects: Tuple[SemanticLatticeSubjectReference, ...] = ()
    relationships: Tuple[SemanticLatticeRelationship, ...] = ()

    def __post_init__(self) -> None:
        if type(self.lattice) is not ParametricSemanticLattice:
            raise TypeError("lattice must be an exact ParametricSemanticLattice")
        if type(self.subjects) is not tuple:
            raise TypeError("subjects must be an exact tuple")
        if any(type(item) is not SemanticLatticeSubjectReference for item in self.subjects):
            raise TypeError(
                "subjects must contain exact SemanticLatticeSubjectReference values"
            )
        if type(self.relationships) is not tuple:
            raise TypeError("relationships must be an exact tuple")
        if any(type(item) is not SemanticLatticeRelationship for item in self.relationships):
            raise TypeError(
                "relationships must contain exact SemanticLatticeRelationship values"
            )
        if len(set(self.subjects)) != len(self.subjects):
            raise ValueError("duplicate semantic lattice subject reference")
        available = set(self.subjects)
        for relationship in self.relationships:
            if relationship.source not in available or relationship.target not in available:
                raise ValueError(
                    "semantic lattice relationship endpoints must be present in subjects"
                )


def construct_semantic_lattice_snapshot(
    lattice: ParametricSemanticLattice,
    *,
    subjects: Tuple[SemanticLatticeSubjectReference, ...] = (),
    relationships: Tuple[SemanticLatticeRelationship, ...] = (),
) -> SemanticLatticeSnapshot:
    """Construct one immutable snapshot without sorting, ranking, or executing inputs."""

    return SemanticLatticeSnapshot(
        lattice=lattice,
        subjects=subjects,
        relationships=relationships,
    )


def subjects_for_domain(
    snapshot: SemanticLatticeSnapshot,
    source_domain: str,
) -> Tuple[SemanticLatticeSubjectReference, ...]:
    selected = _text(source_domain, "source_domain")
    return tuple(
        subject for subject in snapshot.subjects if subject.source_domain == selected
    )


def subjects_for_kind(
    snapshot: SemanticLatticeSnapshot,
    source_kind: str,
) -> Tuple[SemanticLatticeSubjectReference, ...]:
    selected = _text(source_kind, "source_kind")
    return tuple(subject for subject in snapshot.subjects if subject.source_kind == selected)


def subjects_for_identity(
    snapshot: SemanticLatticeSnapshot,
    source_identity: Tuple[str, ...],
) -> Tuple[SemanticLatticeSubjectReference, ...]:
    if type(source_identity) is not tuple or not source_identity:
        raise TypeError("source_identity must be a non-empty exact tuple")
    for index, item in enumerate(source_identity):
        _text(item, f"source_identity[{index}]")
    return tuple(
        subject
        for subject in snapshot.subjects
        if subject.source_identity == source_identity
    )


def relationships_for_relation(
    snapshot: SemanticLatticeSnapshot,
    relation: str,
) -> Tuple[SemanticLatticeRelationship, ...]:
    selected = _text(relation, "relation")
    return tuple(
        relationship
        for relationship in snapshot.relationships
        if relationship.relation == selected
    )


def relationships_from_subject(
    snapshot: SemanticLatticeSnapshot,
    subject: SemanticLatticeSubjectReference,
) -> Tuple[SemanticLatticeRelationship, ...]:
    if type(subject) is not SemanticLatticeSubjectReference:
        raise TypeError("subject must be an exact SemanticLatticeSubjectReference")
    return tuple(
        relationship
        for relationship in snapshot.relationships
        if relationship.source == subject
    )


def relationships_to_subject(
    snapshot: SemanticLatticeSnapshot,
    subject: SemanticLatticeSubjectReference,
) -> Tuple[SemanticLatticeRelationship, ...]:
    if type(subject) is not SemanticLatticeSubjectReference:
        raise TypeError("subject must be an exact SemanticLatticeSubjectReference")
    return tuple(
        relationship
        for relationship in snapshot.relationships
        if relationship.target == subject
    )


__all__ = (
    "SemanticLatticeSnapshot",
    "construct_semantic_lattice_snapshot",
    "subjects_for_domain",
    "subjects_for_kind",
    "subjects_for_identity",
    "relationships_for_relation",
    "relationships_from_subject",
    "relationships_to_subject",
)
